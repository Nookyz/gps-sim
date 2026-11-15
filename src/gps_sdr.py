import shutil

from .config import (
    GPS_SDR_DIR,
    GPS_SDR_SOURCE,
    GPS_SDR_MAKEFILE,
    GPS_SDR_EXECUTABLE,
    GPS_SDR_OUTPUT,
    GPS_SDR_NAV_FILE,
    SOURCE_NAV_FILE,
    REPOSITORY_URL,
    PROJECT_DIR,
)
from .shell import run_command, run_directory_command


def check_project_paths():
    print("\n[0] Checking project paths...")
    print(f"[INFO] Project directory: {PROJECT_DIR}")
    print(f"[INFO] GPS SDR directory: {GPS_SDR_DIR}")
    if not PROJECT_DIR.is_dir():
        print("[ERROR] Project directory not found.")
        return False
    print("[SUCCESS] Project paths verified.")
    return True


def check_repository():
    print("\n[1] Checking GPS SDR repository...")
    if not GPS_SDR_DIR.exists():
        print("[INFO] Repository not found; cloning it...")
        result = run_command(
            ["git", "clone", REPOSITORY_URL, str(GPS_SDR_DIR)],
            cwd=PROJECT_DIR,
        )
        if result is None or result.returncode != 0:
            print("[ERROR] Git clone failed.")
            return False
        print("[SUCCESS] Repository cloned.")

    if not GPS_SDR_DIR.is_dir():
        print("[ERROR] GPS SDR directory does not exist.")
        return False
    if not (GPS_SDR_DIR / ".git").is_dir():
        print("[ERROR] gps-sdr-sim exists but is not a Git repository.")
        return False
    if not GPS_SDR_SOURCE.is_file():
        print("[ERROR] gpssim.c not found.")
        return False
    if not GPS_SDR_MAKEFILE.is_file():
        print("[ERROR] Makefile not found.")
        return False

    print("[SUCCESS] Repository verified.")
    return True


def build_repository():
    print("\n[2] Building GPS SDR repository...")
    for tool, args in (("GCC", ["gcc", "--version"]), ("Make", ["make", "--version"])):
        result = run_command(args)
        if result is None or result.returncode != 0:
            print(f"[ERROR] {tool} is unavailable.")
            return False
        print(f"[OK] {tool} is installed.")

    result = run_command(["make"], cwd=GPS_SDR_DIR)
    if result is None or result.returncode != 0:
        print("[ERROR] Repository build failed.")
        return False
    if not GPS_SDR_EXECUTABLE.is_file() or GPS_SDR_EXECUTABLE.stat().st_size == 0:
        print("[ERROR] gps-sdr-sim executable was not created or is empty.")
        return False
    print(f"[SUCCESS] Executable created: {GPS_SDR_EXECUTABLE}")
    return True


def prepare_navigation_file():
    print("\n[3] Preparing navigation file...")
    if not SOURCE_NAV_FILE.is_file():
        print(f"[ERROR] Navigation file not found: {SOURCE_NAV_FILE}")
        print("[INFO] Place the configured navigation file in the project root.")
        return False
    try:
        shutil.copy2(SOURCE_NAV_FILE, GPS_SDR_NAV_FILE)
    except Exception as error:
        print(f"[ERROR] Navigation file copy failed: {error}")
        return False
    if not GPS_SDR_NAV_FILE.is_file() or GPS_SDR_NAV_FILE.stat().st_size == 0:
        print("[ERROR] Destination navigation file is missing or empty.")
        return False
    print("[SUCCESS] Navigation file copied and verified.")
    return True


def check_gps_sdr_files():
    print("\n[6] Checking GPS SDR files...")
    for file_path in (GPS_SDR_SOURCE, GPS_SDR_NAV_FILE, GPS_SDR_EXECUTABLE):
        if not file_path.is_file():
            print(f"[ERROR] File not found: {file_path}")
            return False
        print(f"[OK] Found: {file_path.name}")
    print("[SUCCESS] GPS SDR files verified.")
    return True


def check_gpssim_bin():
    print("\n[7] Checking gpssim.bin...")
    if not GPS_SDR_OUTPUT.is_file():
        print("[INFO] gpssim.bin does not exist yet.")
        return True
    size = GPS_SDR_OUTPUT.stat().st_size
    if size == 0:
        print("[ERROR] gpssim.bin is empty.")
        return False
    print(f"[OK] gpssim.bin exists ({size} bytes).")
    return True


def run_directory_diagnostics():
    print("\n[8] Checking working directory...")
    pwd = run_command(["pwd"], cwd=GPS_SDR_DIR)
    if pwd is None or pwd.returncode != 0:
        return False
    listing = run_command(["ls", "-lh"], cwd=GPS_SDR_DIR)
    return listing is not None and listing.returncode == 0


def generate_offline_data(command, location_name):
    print("\n[INFO] Generating offline IQ data...")
    print(f"[INFO] Selected location: {location_name}")
    result = run_directory_command(command)
    if result is None or result.returncode != 0:
        print("[ERROR] Offline data generation failed.")
        return False
    if not GPS_SDR_OUTPUT.is_file() or GPS_SDR_OUTPUT.stat().st_size == 0:
        print("[ERROR] gpssim.bin was not created or is empty.")
        return False
    print(f"[SUCCESS] Offline data created: {GPS_SDR_OUTPUT}")
    return True
