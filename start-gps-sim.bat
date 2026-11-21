@echo off
setlocal EnableDelayedExpansion

:: ============================================
:: Auto-elevate to Administrator (для usbipd)
:: ============================================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrator privileges...
    if "%~1"=="" (
        powershell -Command "Start-Process -FilePath '%~f0' -WorkingDirectory '%~dp0' -Verb RunAs"
    ) else (
        powershell -Command "Start-Process -FilePath '%~f0' -ArgumentList '%~1' -WorkingDirectory '%~dp0' -Verb RunAs"
    )
    exit /b
)

:: ============================================
:: Configuration
:: ============================================
set "WSL_DISTRO=Ubuntu"
set "HACKRF_VID_PID=1d50:6089"
set "ZEDF9P_VID_PID=1546:01a9"
set "IMAGE_NAME=gps-simulator:local"

:: ============================================
:: Parse mode: rf or tx (default tx)
:: ============================================
set "RUN_MODE=tx"
if /i "%~1"=="rf" set "RUN_MODE=rf"
echo ============================================
echo  GPS SIM AUTO  ^| Mode: %RUN_MODE%
echo ============================================
echo.

:: ============================================
:: [0/6] Resolve project directory
:: ============================================
echo [0/6] Resolving project directory...
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
echo       Windows path: %PROJECT_DIR%

if not exist "%PROJECT_DIR%\docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found in %PROJECT_DIR%
    pause
    exit /b 1
)

for /f "usebackq delims=" %%i in (`wsl -d %WSL_DISTRO% -- wslpath -u "%PROJECT_DIR%"`) do set "WSL_PATH=%%i"
if "%WSL_PATH%"=="" (
    echo [ERROR] Failed to convert path to WSL format.
    pause
    exit /b 1
)
echo       WSL path:     %WSL_PATH%

:: ============================================
:: [1/6] Ensure docker/podman is available
:: ============================================
echo.
echo [1/6] Checking container runtime...
where docker >nul 2>&1
if errorlevel 1 (
    echo       docker not found. Creating docker.bat wrapper for podman...
    set "WRAPPER_DIR=%USERPROFILE%\bin"
    if not exist "!WRAPPER_DIR!" mkdir "!WRAPPER_DIR!"
    (
        echo @echo off
        echo podman %%*
    ) > "!WRAPPER_DIR!\docker.bat"
    set "PATH=!WRAPPER_DIR!;!PATH!"
    where docker >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Neither docker nor podman found.
        echo         Install Podman Desktop or Docker Desktop.
        pause
        exit /b 1
    )
    echo       Wrapper created at !WRAPPER_DIR!\docker.bat
)
echo       Container runtime OK.

:: ============================================
:: [2/6] Build image if missing
:: ============================================
echo.
echo [2/6] Checking image %IMAGE_NAME%...
docker image inspect %IMAGE_NAME% >nul 2>&1
if errorlevel 1 (
    echo       Image not found. Building...
    cd /d "%PROJECT_DIR%"
    docker compose build
    if errorlevel 1 (
        echo [ERROR] docker compose build failed.
        pause
        exit /b 1
    )
    echo       Image built.
) else (
    echo       Image already exists.
)

:: ============================================
:: [3/6] Find + attach HackRF
:: ============================================
echo.
echo [3/6] Searching for HackRF (VID:PID = %HACKRF_VID_PID%)...
set "BUSID="
for /f "tokens=1" %%i in ('usbipd list ^| findstr /i "%HACKRF_VID_PID%"') do set "BUSID=%%i"

if "!BUSID!"=="" (
    echo [ERROR] HackRF not found. Check USB connection.
    pause
    exit /b 1
)
echo       Found BUSID: !BUSID!

usbipd bind --busid !BUSID! >nul 2>&1
echo       Bind done or already bound.

start /b "" usbipd attach --wsl --auto-attach --busid !BUSID! >nul 2>&1
echo       Attach started in background. Waiting for device...
timeout /t 5 /nobreak >nul

:: ============================================
:: [4/6] Verify HackRF visibility inside WSL
:: ============================================
echo.
echo [4/6] Verifying HackRF visibility inside WSL...
set "LSUSB_OUT="
for /f "usebackq delims=" %%i in (`wsl -d %WSL_DISTRO% -- bash -c "lsusb | grep -i '%HACKRF_VID_PID%'"`) do set "LSUSB_OUT=%%i"

if "!LSUSB_OUT!"=="" (
    echo [ERROR] HackRF not visible in WSL.
    pause
    exit /b 1
)
echo       !LSUSB_OUT!
echo       HackRF visible in WSL.

:: ============================================
:: [5/6] Attach ZED-F9P only if --rf
:: ============================================
echo.
if /i "%RUN_MODE%"=="rf" (
    echo [5/6] RF mode: searching for ZED-F9P ^(VID:PID = %ZEDF9P_VID_PID%^)...
    set "ZED_BUSID="
    for /f "tokens=1" %%i in ('usbipd list ^| findstr /i "%ZEDF9P_VID_PID%"') do set "ZED_BUSID=%%i"

    if "!ZED_BUSID!"=="" (
        echo [ERROR] ZED-F9P not found. Check USB connection.
        echo         If your receiver has a different VID:PID, edit ZEDF9P_VID_PID in this .bat.
        pause
        exit /b 1
    )
    echo       Found ZED-F9P BUSID: !ZED_BUSID!

    usbipd bind --busid !ZED_BUSID! >nul 2>&1
    echo       Bind done or already bound.

    start /b "" usbipd attach --wsl --auto-attach --busid !ZED_BUSID! >nul 2>&1
    echo       Attach started in background. Waiting for /dev/ttyACM*...
    timeout /t 5 /nobreak >nul

    set "TTYACM_OUT="
    for /f "usebackq delims=" %%i in (`wsl -d %WSL_DISTRO% -- bash -c "ls -l /dev/ttyACM* 2>/dev/null"`) do set "TTYACM_OUT=%%i"

    if "!TTYACM_OUT!"=="" (
        echo [ERROR] /dev/ttyACM* not visible in WSL.
        echo         Check usbipd attach for ZED-F9P.
        pause
        exit /b 1
    )
    echo       !TTYACM_OUT!
    echo       ZED-F9P serial port visible in WSL.
) else (
    echo [5/6] TX mode: skipping ZED-F9P attach ^(not needed for --tx^).
)

:: ============================================
:: [6/6] Run
:: ============================================
echo.
cd /d "%PROJECT_DIR%"
if /i "%RUN_MODE%"=="rf" (
    echo [6/6] Starting full run ^(checks + IQ + RF probe^)...
    docker compose --profile hardware run --rm gps-simulator-hardware --mode hardware --generate --rf
) else (
    echo [6/6] Starting full run ^(checks + IQ + TX^)...
    docker compose --profile hardware run --rm gps-simulator-hardware --mode hardware --generate --tx
)

set "EXITCODE=%errorlevel%"
echo.
echo [DEBUG] docker compose exit code: %EXITCODE%
echo Done. Press any key to exit...
pause >nul