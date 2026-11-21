import subprocess
import time

from .config import (
    GPS_SDR_DIR,
    GPS_SDR_OUTPUT,
)  # noqa: F401  (GPS_SDR_OUTPUT may be useful)


def _start_hackrf_transfer(command):
    """Start hackrf_transfer in the background and check that it does not exit immediately."""
    print("\n[RF] Starting hackrf_transfer in background...")
    print(f"[RF] {' '.join(map(str, command))}")
    process = subprocess.Popen(
        command,
        cwd=GPS_SDR_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    # Allow time for the transmitter to initialize
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
    Explicitly enable NAV-SAT and NAV-STATUS on the USB port.
    Without this, ZED-F9P may not transmit these messages,
    and pyubx2 will never receive them.
    """
    try:
        from pyubx2 import UBXMessage
    except ImportError:
        print("[RF][WARN] pyubx2 not available for CFG-MSG; relying on defaults.")
        return

    print("[RF] Enabling UBX-NAV-SAT and UBX-NAV-STATUS on USB...")
    try:
        # rateUSB=1 means one message per second on the USB port
        cfg_sat = UBXMessage.config_set(0, 0, [(0x01, 0x35, 1)])  # NAV-SAT
        cfg_status = UBXMessage.config_set(0, 0, [(0x01, 0x03, 1)])  # NAV-STATUS
        ser.write(cfg_sat.serialize())
        ser.write(cfg_status.serialize())
        time.sleep(1)  # Allow the receiver to apply the settings
    except Exception as error:
        print(f"[RF][WARN] Failed to send CFG-MSG: {error}")


def _unwrap_ubx_read(result):
    """
    UBXReader.read() returns different formats depending on the pyubx2 version:
      - (raw_data, parsed_data)           -> 2 elements
      - (raw_data, parsed_data, something) -> 3 elements
      - None
    Returns parsed_data or None.
    """
    if result is None:
        return None
    if isinstance(result, tuple):
        if len(result) == 2:
            return result[1]
        if len(result) >= 3:
            return result[1]
        return None
    # Handle the case where a parsed object is returned directly
    return result


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

    try:
        _enable_ubx_messages(ser)

        ubr = UBXReader(ser)
        deadline = time.time() + duration_s
        saw_sat = False
        saw_spoof = False
        sat_count = 0

        print(f"[RF] Listening for UBX for {duration_s} seconds...")
        while time.time() < deadline:
            try:
                parsed = _unwrap_ubx_read(ubr.read())
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

        print("\n[RF] Probe summary:")
        print(f"[RF]   max satellites seen: {sat_count}")
        print(f"[RF]   spoofing detected: {saw_spoof}")
        return saw_sat or saw_spoof
    finally:
        try:
            ser.close()
        except Exception:
            pass


def run_rf_probe(
    command_2,
    port="/dev/ttyACM0",
    baud=38400,
    duration_s=90,  # ZED-F9P cold start takes approximately 24-35 seconds
):
    process = _start_hackrf_transfer(command_2)
    if process is None:
        return False
    try:
        ok = _probe_zed_f9p(port, baud, duration_s)
    finally:
        print("\n[RF] Stopping hackrf_transfer...")
        if process.poll() is None:
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
