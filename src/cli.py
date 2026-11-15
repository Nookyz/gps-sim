import argparse

from .config import COMMAND_1, GPS_SDR_OUTPUT, LOCATION
from .checks import run_checks
from .gps_sdr import generate_offline_data
from .monitor import run_transmission_loop
from .rf_probe import run_rf_probe


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare gps-sdr-sim, generate IQ, transmit via HackRF, or probe ZED-F9P."
    )
    parser.add_argument("--mode", choices=("software", "hardware"), default="software")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument(
        "--tx",
        action="store_true",
        help="Transmit gpssim.bin via HackRF in a loop (COMMAND_2).",
    )
    parser.add_argument(
        "--rf",
        action="store_true",
        help="Transmit AND probe ZED-F9P UBX output (requires --mode hardware).",
    )
    parser.add_argument(
        "--detached",
        action="store_true",
        help="Exit after checks/generation; do not start TX or monitor loop.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print("================================")
    print("         GPS SIM AUTO")
    print(f"         MODE: {args.mode.upper()}")
    print("================================")

    if not run_checks(args.mode):
        return 1

    if args.generate:
        if not generate_offline_data(COMMAND_1, LOCATION["name"]):
            return 1
    else:
        print("\n[INFO] --generate not passed; gpssim.bin was not regenerated.")

    if not GPS_SDR_OUTPUT.is_file() or GPS_SDR_OUTPUT.stat().st_size == 0:
        print("\n[ERROR] gpssim.bin is missing. Pass --generate or provide the file.")
        return 1

    if args.detached:
        print("\n[INFO] --detached passed; TX/monitor skipped.")
        return 0

    if args.rf:
        if args.mode != "hardware":
            print("[ERROR] --rf requires --mode hardware.")
            return 1
        from .config import COMMAND_2

        if not run_rf_probe(COMMAND_2):
            return 1
        return 0

    # if args.tx:
    #     if args.mode != "hardware":
    #         print("[ERROR] --tx requires --mode hardware.")
    #         return 1
    #     run_transmission_loop()
    #     return 0

    # print("\n[INFO] No --tx/--rf passed; starting monitor-only loop (no RF).")
    # run_transmission_loop.__self__ if False else None  # noqa — просто чтобы напомнить
    # # На самом деле: без --tx/--rf передача не запускается.
    # # Если нужен только мониторинг — он был в monitor.py, но здесь он не нужен.
    # print("[INFO] Nothing to do. Pass --tx or --rf to transmit.")
    return 0
