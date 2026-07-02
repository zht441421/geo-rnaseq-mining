#!/usr/bin/env python3

import argparse
from pathlib import Path

import yaml

from multi_dataset_common import COMPATIBILITY_FIELDS, assess_compatibility
from preanalysis_common import read_tsv, write_tsv


def parse_args():
    parser = argparse.ArgumentParser(
        description="Assess technical compatibility without changing dataset_plan.tsv."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--geo-samples")
    parser.add_argument("--sra-runinfo")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    rows = assess_compatibility(
        read_tsv(args.manifest),
        read_tsv(args.dataset_plan),
        read_tsv(args.contrasts),
        config,
        read_tsv(args.geo_samples) if args.geo_samples else [],
        read_tsv(args.sra_runinfo) if args.sra_runinfo else [],
    )
    write_tsv(args.output, COMPATIBILITY_FIELDS, rows)
    print(
        f"Wrote {len(rows)} dataset compatibility records; "
        "analysis_strategy values were not modified."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
