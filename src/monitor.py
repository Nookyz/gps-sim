import subprocess
import time

from .config import COMMAND_2, GPS_SDR_DIR, GPS_SDR_OUTPUT


def run_transmission_loop():
    """
    Repeatedly transmit gpssim.bin via HackRF.

    Each iteration runs COMMAND_2 (hackrf_transfer) to completion,
    waits 2 seconds, then repeats. Press CTRL+C to stop.
    """
    print("\n================================")
    print("       STARTING TRANSMISSION")
    print("================================")

    if not GPS_SDR_OUTPUT.is_file() or GPS_SDR_OUTPUT.stat().st_size == 0:
        print("[ERROR] gpssim.bin is missing or empty. Transmission not started.")
        return False

    print(f"[INFO] Using IQ file: {GPS_SDR_OUTPUT}")
    print(f"[INFO] File size: {GPS_SDR_OUTPUT.stat().st_size} bytes")
    print("[INFO] Press CTRL+C to stop.")

    iteration = 1
    try:
        while True:
            print(f"\n[LOOP] Iteration: {iteration}", flush=True)
            print(f"[TX] Starting hackrf_transfer...", flush=True)

            result = subprocess.run(
                COMMAND_2,
                cwd=GPS_SDR_DIR,
                check=False,
            )

            if result.returncode != 0:
                print(
                    f"[TX][ERROR] hackrf_transfer exited with {result.returncode}",
                    flush=True,
                )
                print("[TX][INFO] Retrying in 2 seconds...", flush=True)
            else:
                print("[TX] Transmission finished.", flush=True)

            iteration += 1
            print("[WAIT] Waiting 2 seconds...", flush=True)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[STOP] Transmission loop stopped by user.", flush=True)
        return True
