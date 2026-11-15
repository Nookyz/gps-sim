from pathlib import Path

HACKRF_NAME = "Great Scott Gadgets HackRF"
HACKRF_VID_PID = "1d50:6089"
REPOSITORY_URL = "https://github.com/osqzss/gps-sdr-sim.git"

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR
GPS_SDR_DIR = PROJECT_DIR / "gps-sdr-sim"

BRDC_NAV_FILE = "brdc3190.26n"
SOURCE_NAV_FILE = PROJECT_DIR / BRDC_NAV_FILE
GPS_SDR_NAV_FILE = GPS_SDR_DIR / BRDC_NAV_FILE

GPS_SDR_SOURCE = GPS_SDR_DIR / "gpssim.c"
GPS_SDR_MAKEFILE = GPS_SDR_DIR / "Makefile"
GPS_SDR_EXECUTABLE = GPS_SDR_DIR / "gps-sdr-sim"
GPS_SDR_OUTPUT = GPS_SDR_DIR / "gpssim.bin"

SECONDS_TO_RUN = 360

LOCATIONS = {
    "hangzhou": {
        "name": "Hangzhou, China",
        "latitude": 30.286502,
        "longitude": 120.032669,
        "altitude": 100,
    },
    "paris": {
        "name": "Paris, France",
        "latitude": 48.856600,
        "longitude": 2.352200,
        "altitude": 35,
    },
    "uae": {
        "name": "Dubai, UAE",
        "latitude": 25.204800,
        "longitude": 55.270800,
        "altitude": 16,
    },
}

ACTIVE_LOCATION = "paris"

if ACTIVE_LOCATION not in LOCATIONS:
    raise ValueError(
        f"Unknown ACTIVE_LOCATION={ACTIVE_LOCATION!r}. "
        f"Choose: {', '.join(LOCATIONS)}"
    )

LOCATION = LOCATIONS[ACTIVE_LOCATION]

COMMAND_1 = [
    "./gps-sdr-sim",
    "-e",
    GPS_SDR_NAV_FILE.name,
    "-l",
    f"{LOCATION['latitude']},{LOCATION['longitude']},{LOCATION['altitude']}",
    "-d",
    str(SECONDS_TO_RUN),
    "-b",
    "8",
    "-o",
    GPS_SDR_OUTPUT.name,
    "-v",
]

# Configuration only. Not executed by this application.
COMMAND_2 = [
    "hackrf_transfer",
    "-t",
    GPS_SDR_OUTPUT.name,
    "-f",
    "1575420000",
    "-s",
    "2600000",
    "-a",
    "1",
    "-x",
    "0",
]
