import subprocess

from .config import GPS_SDR_DIR


def run_command(command, cwd=None):
    print(f"\n[RUN] {' '.join(map(str, command))}", flush=True)
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout, end="", flush=True)
        if result.stderr:
            print(result.stderr, end="", flush=True)
        print(f"[EXIT CODE] {result.returncode}", flush=True)
        return result
    except FileNotFoundError:
        print(f"[ERROR] Command not found: {command[0]}")
    except Exception as error:
        print(f"[ERROR] {error}")
    return None


def run_directory_command(command):
    print(f"\n[WORKDIR] {GPS_SDR_DIR}", flush=True)
    return run_command(command, cwd=GPS_SDR_DIR)
