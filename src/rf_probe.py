import subprocess
import time

from .config import GPS_SDR_DIR, GPS_SDR_OUTPUT


def _start_hackrf_transfer(command):
    """Запускает hackrf_transfer в фоне и проверяет, что он не упал сразу."""
    print("\n[RF] Starting hackrf_transfer in background...")
    print(f"[RF] {' '.join(map(str, command))}")
    process = subprocess.Popen(
        command,
        cwd=GPS_SDR_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Дать время на инициализацию передатчика
    time.sleep(2)
    if process.poll() is not None:
        try:
            out, _ = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            out = "(no output)"
        print(f"[RF][ERROR] hackrf_transfer exited immediately:\n{out}")
        return None
    print("[RF] hackrf_transfer is running.")
    return process


def _enable_ubx_messages(ser):
    """
    Явно включает NAV-SAT и NAV-STATUS на USB-порту.
    Без этого ZED-F9P может не отправлять эти сообщения,
    и pyubx2 их никогда не увидит.
    """
    try:
        from pyubx2 import UBXMessage
    except ImportError:
        print("[RF][WARN] pyubx2 not available for CFG-MSG; relying on defaults.")
        return

    print("[RF] Enabling UBX-NAV-SAT and UBX-NAV-STATUS on USB...")
    # rateUSB=1 означает 1 сообщение в секунду на USB-порту
    cfg_sat = UBXMessage.config_set(0, 0, [(0x01, 0x35, 1)])  # NAV-SAT
    cfg_status = UBXMessage.config_set(0, 0, [(0x01, 0x03, 1)])  # NAV-STATUS
    ser.write(cfg_sat.serialize())
    ser.write(cfg_status.serialize())
    time.sleep(1)  # дать приёмнику применить настройки


def _probe_zed_f9p(port, baud, duration_s):
    try:
        from serial import Serial
        from pyubx2 import UBXReader
    except ImportError:
        print("[RF][ERROR] pyubx2 / pyserial not installed.")
        print("[RF][INFO] Add to requirements.txt: pyubx2, pyserial")
        return False

    print(f"\n[RF] Probing ZED-F9P on {port} @ {baud}...")
    try:
        ser = Serial(port, baud, timeout=1)
    except Exception as error:
        print(f"[RF][ERROR] Cannot open {port}: {error}")
        return False

    # Ключевой шаг: включаем нужные сообщения до чтения
    _enable_ubx_messages(ser)

    ubr = UBXReader(ser)
    deadline = time.time() + duration_s
    saw_sat = False
    saw_spoof = False
    sat_count = 0

    print(f"[RF] Listening for UBX for {duration_s} seconds...")
    while time.time() < deadline:
        try:
            _, parsed = ubr.read()
        except Exception:
            continue
        if parsed is None:
            continue

        if parsed.identity == "NAV-SAT":
            num_sv = getattr(parsed, "numSV", 0)
            if num_sv > 0:
                sat_count = max(sat_count, num_sv)
                print(f"[RF] NAV-SAT: numSV={num_sv}")
                saw_sat = True
        elif parsed.identity == "NAV-STATUS":
            flags2 = getattr(parsed, "flags2", 0)
            spoof_state = (flags2 >> 3) & 0x03
            if spoof_state in (2, 3):
                print(
                    f"[RF] NAV-STATUS: spoofDetState={spoof_state} (spoofing indicated)"
                )
                saw_spoof = True

    ser.close()

    print("\n[RF] Probe summary:")
    print(f"[RF]   max satellites seen: {sat_count}")
    print(f"[RF]   spoofing detected: {saw_spoof}")
    return saw_sat or saw_spoof


def run_rf_probe(
    command_2,
    port="/dev/ttyACM0",
    baud=38400,
    duration_s=90,  # увеличено с 30: холодный старт ZED-F9P ~24-35 с
):
    process = _start_hackrf_transfer(command_2)
    if process is None:
        return False
    try:
        ok = _probe_zed_f9p(port, baud, duration_s)
    finally:
        print("\n[RF] Stopping hackrf_transfer...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        if process.stdout:
            process.stdout.close()
        print("[RF] hackrf_transfer stopped.")
    return ok
