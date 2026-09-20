"""Require statement and branch coverage independently instead of a blended percentage.

Coverage.py's fail_under applies to their combined score. A high statement count can
therefore hide untested branches. This gate consumes its JSON report after the suite.
"""

import argparse
import json
from pathlib import Path


def check_report(report: dict) -> None:
    totals = report["totals"]
    for covered, total in [
        ("covered_lines", "num_statements"),
        ("covered_branches", "num_branches"),
    ]:
        if totals[total] <= 0 or 100 * totals[covered] / totals[total] < 95:
            raise ValueError(f"Python {covered} coverage must reach 95%.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    check_report(report)
    totals = report["totals"]
    print(
        f"Python lines: {100 * totals['covered_lines'] / totals['num_statements']:.2f}%; branches: {100 * totals['covered_branches'] / totals['num_branches']:.2f}% (95% required each)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
