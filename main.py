import sys

from src.cli import main

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[STOP] Program stopped by user.")
        sys.exit(130)
    except Exception as error:
        print(f"\n[ERROR] Unexpected error: {error}")
        sys.exit(1)
