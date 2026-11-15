from .config import HACKRF_NAME, HACKRF_VID_PID
from .shell import run_command


def check_hackrf():
    print("\n[4] Checking HackRF USB visibility...")
    result = run_command(["lsusb"])
    if result is None or result.returncode != 0:
        return False
    found = (
        HACKRF_NAME.lower() in result.stdout.lower()
        or HACKRF_VID_PID.lower() in result.stdout.lower()
    )
    if found:
        print("[SUCCESS] HackRF USB device is visible inside the container.")
    else:
        print("[ERROR] HackRF is not visible inside the container.")
    return found


def check_hackrf_info():
    print("\n[5] Checking HackRF using hackrf_info...")
    result = run_command(["hackrf_info"])
    if result is None or result.returncode != 0:
        print("[ERROR] hackrf_info failed.")
        return False
    if "Found HackRF" in result.stdout:
        print("[SUCCESS] HackRF detected by libhackrf.")
        return True
    print("[ERROR] HackRF was not confirmed by hackrf_info.")
    return False
