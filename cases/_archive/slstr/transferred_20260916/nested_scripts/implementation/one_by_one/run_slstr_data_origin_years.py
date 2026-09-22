"""Run SLSTR origin-data extraction year by year with resumable outputs.

The worker script keeps its historical single-year processing logic.  This
wrapper supplies the year and waits for each year to finish before starting
the next one, so a failed year cannot silently hide later failures.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


WORKER = Path(__file__).with_name("slstr_data_origin.py")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2017)
    parser.add_argument("--end-year", type=int, default=2025)
    parser.add_argument(
        "--data-root",
        default="/media/hero/slstr_heihe/heihe",
        help="Directory containing <year>/raw and <year>/tif",
    )
    args = parser.parse_args()

    if args.start_year > args.end_year:
        parser.error("--start-year must not be greater than --end-year")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["LS4T_DATA_ROOT"] = args.data_root

    for year in range(args.start_year, args.end_year + 1):
        env["LS4T_YEAR"] = str(year)
        print(f"===== START {year} =====", flush=True)
        result = subprocess.run([sys.executable, str(WORKER)], env=env)
        if result.returncode != 0:
            print(f"===== FAILED {year} (exit {result.returncode}) =====", flush=True)
            return result.returncode
        print(f"===== DONE {year} =====", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
