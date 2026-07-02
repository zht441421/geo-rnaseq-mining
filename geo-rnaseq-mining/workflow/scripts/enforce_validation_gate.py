#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def assert_validation_allowed(status, analysis_id=None):
    if status.get("critical_block"):
        raise RuntimeError(
            "Critical pre-analysis validation failures block the workflow. "
            "Open results/compatibility/validation_report.html and correct reviewed inputs."
        )
    if analysis_id and analysis_id in status.get("blocked_analysis_ids", []):
        raise RuntimeError(
            f"analysis_id {analysis_id!r} is blocked by validation errors. "
            "The selected strategy and user values will not be changed automatically."
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Enforce pre-analysis validation.")
    parser.add_argument("--status", required=True)
    parser.add_argument("--analysis-id")
    parser.add_argument("--marker", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    status = json.loads(Path(args.status).read_text(encoding="utf-8"))
    try:
        assert_validation_allowed(status, args.analysis_id)
    except RuntimeError as error:
        print(str(error))
        return 2
    marker = Path(args.marker)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("validation passed\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
