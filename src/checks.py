from .gps_sdr import (
    check_project_paths,
    check_repository,
    build_repository,
    prepare_navigation_file,
    check_gps_sdr_files,
    check_gpssim_bin,
    run_directory_diagnostics,
)
from .hackrf import check_hackrf, check_hackrf_info


def run_checks(mode):
    checks = [
        ("Project paths", check_project_paths),
        ("Repository", check_repository),
        ("Build environment", build_repository),
        ("Navigation file", prepare_navigation_file),
    ]
    if mode == "hardware":
        checks.extend(
            [
                ("HackRF USB visibility", check_hackrf),
                ("HackRF diagnostics", check_hackrf_info),
            ]
        )
    checks.extend(
        [
            ("GPS SDR files", check_gps_sdr_files),
            ("GPS BIN", check_gpssim_bin),
            ("Directory diagnostics", run_directory_diagnostics),
        ]
    )

    results = {}
    for name, function in checks:
        success = function()
        results[name] = success
        if not success:
            print(f"\n[ERROR] Failed stage: {name}")
            break

    print("\n================================")
    print("          FINAL REPORT")
    print("================================")
    for name, success in results.items():
        print(f"[{'SUCCESS' if success else 'FAILED'}] {name}")

    complete = len(results) == len(checks) and all(results.values())
    if complete:
        print("\n[SUCCESS] All requested checks passed.")
    else:
        print("\n[ERROR] Diagnostic process did not complete.")
    return complete
