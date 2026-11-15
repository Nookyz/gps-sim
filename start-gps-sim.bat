@echo off
setlocal EnableDelayedExpansion

:: ============================================
:: Auto-elevate to Administrator
:: ============================================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: ============================================
:: Configuration
:: ============================================
set "WSL_DISTRO=Ubuntu"
set "HACKRF_VID_PID=1d50:6089"

:: ============================================
:: [0/5] Resolve project directory
:: ============================================
echo [0/5] Resolving project directory...
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
echo       Windows path: %PROJECT_DIR%

if not exist "%PROJECT_DIR%\docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found in %PROJECT_DIR%
    echo         Place this .bat file in the project root.
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
:: [1/5] Find HackRF
:: ============================================
echo.
echo [1/5] Searching for HackRF (VID:PID = %HACKRF_VID_PID%)...
set "BUSID="
for /f "tokens=1" %%i in ('usbipd list ^| findstr /i "%HACKRF_VID_PID%"') do set "BUSID=%%i"

if "!BUSID!"=="" (
    echo [ERROR] HackRF not found. Check USB connection.
    pause
    exit /b 1
)
echo       Found BUSID: !BUSID!

:: ============================================
:: [2/5] Bind device
:: ============================================
echo.
echo [2/5] Binding device (bind)...
usbipd bind --busid !BUSID! >nul 2>&1
echo       Bind done or already bound.

:: ============================================
:: [3/5] Attach to WSL with auto-reconnect
:: ============================================
echo.
echo [3/5] Attaching to WSL with auto-reconnect...
usbipd attach --wsl --auto-attach --busid !BUSID!
if errorlevel 1 (
    echo [ERROR] Attach failed.
    pause
    exit /b 1
)

:: ============================================
:: [4/5] Verify device visibility inside WSL
:: ============================================
echo.
echo [4/5] Verifying device visibility inside WSL...
wsl -d %WSL_DISTRO% -- bash -c "lsusb | grep -i '1d50:6089' || echo '[WARN] HackRF not visible in WSL yet'"

:: ============================================
:: [5/5] Full run: checks + generate IQ + RF probe
:: ============================================
echo.
echo [5/5] Starting full run in Docker (checks + IQ + RF probe)...
wsl -d %WSL_DISTRO% -- bash -c "cd '%WSL_PATH%' && docker compose --profile hardware run --rm gps-simulator-hardware --mode hardware --generate --tx"

echo.
echo Done. Press any key to exit...
pause >nul