#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


def merge_count_files(inputs, sample_ids, output_path):
    if len(inputs) != len(sample_ids):
        raise ValueError("Count input and sample ID lengths differ")
    merged = None
    for input_path, sample_id in zip(inputs, sample_ids):
        frame = pd.read_csv(input_path, sep="\t")
        if list(frame.columns) != ["gene_id", sample_id]:
            raise ValueError(
                f"Unexpected columns in {input_path}: {list(frame.columns)}"
            )
        if frame["gene_id"].duplicated().any():
            raise ValueError(f"Duplicate gene IDs in {input_path}")
        merged = frame if merged is None else merged.merge(
            frame,
            on="gene_id",
            how="outer",
            validate="one_to_one",
        )
    if merged is None or merged.isna().any().any():
        raise ValueError("Per-sample featureCounts gene spaces are inconsistent")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output, sep="\t", index=False, lineterminator="\n")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge per-sample featureCounts matrices in reviewed order."
    )
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--sample-ids", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    merge_count_files(args.inputs, args.sample_ids, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
