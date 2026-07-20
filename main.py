"""
Aircraft Deal Bot V2
Main Entry Point
"""

import sys
import traceback
from datetime import datetime

from sources import run_all
from helpers import telegram


VERSION = "2.0"


def banner():

    print("=" * 60)
    print(f"Aircraft Deal Bot V{VERSION}")
    print("=" * 60)
    print(f"Started : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 60)
    print()


def footer():

    print()
    print("=" * 60)
    print("Run Complete")
    print("=" * 60)


def main():

    banner()

    try:

        run_all()

    except KeyboardInterrupt:

        print("\nStopped by user.")

    except Exception:

        error = traceback.format_exc()

        print(error)

        telegram(
            "⚠ Aircraft Deal Bot crashed.\n\n"
            + error[:3500]
        )

        sys.exit(1)

    footer()


if __name__ == "__main__":

    main()