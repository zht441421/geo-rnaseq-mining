#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


def normalize_featurecounts(input_path, sample_id, output_path):
    with Path(input_path).open(encoding="utf-8", newline="") as handle:
        lines = [line for line in handle if not line.startswith("#")]
    reader = csv.reader(lines, delimiter="\t")
    header = next(reader)
    if len(header) < 7:
        raise ValueError("featureCounts output has no count column")
    rows = []
    for values in reader:
        if len(values) != len(header):
            raise ValueError("featureCounts output contains malformed rows")
        count = float(values[-1])
        if count < 0 or not count.is_integer():
            raise ValueError("featureCounts emitted a non-integer or negative count")
        rows.append((values[0], int(count)))
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["gene_id", sample_id])
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(description="Normalize one featureCounts result.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    normalize_featurecounts(args.input, args.sample_id, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
