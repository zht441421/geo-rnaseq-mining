#!/usr/bin/env python3

import argparse
import json
from collections import OrderedDict
from pathlib import Path

import yaml

from metadata_io import NA, read_tsv, write_tsv


FIELDS = [
    "dataset_id",
    "gse_id",
    "suggested_analysis_id",
    "suggested_include",
    "suggested_role",
    "suggested_merge_group",
    "suggested_analysis_strategy",
    "suggestion_evidence",
    "suggestion_confidence",
    "requires_manual_review",
    "analysis_id",
    "include",
    "role",
    "merge_group",
    "analysis_strategy",
    "reference_dataset",
    "notes",
]


def build_dataset_plan(manifest_rows, analysis_id):
    datasets = OrderedDict()
    for row in manifest_rows:
        dataset_id = row.get("dataset_id") or row.get("gse_id") or NA
        if dataset_id == NA or dataset_id in datasets:
            continue
        datasets[dataset_id] = row.get("gse_id") or dataset_id

    output = []
    for dataset_id, gse_id in datasets.items():
        evidence = {
            "dataset_id": {
                "value": dataset_id,
                "evidence": [
                    "Dataset identifiers are copied from raw GEO accessions only."
                ],
                "confidence": "high",
            },
            "suggested_analysis_id": {
                "value": analysis_id,
                "evidence": [
                    "Default analysis_id is copied from config/project metadata."
                ],
                "confidence": "low",
            },
            "suggested_analysis_strategy": {
                "value": "per_dataset_candidate",
                "evidence": [
                    "Per-dataset analysis is the conservative suggestion before human review."
                ],
                "confidence": "low",
            },
        }
        output.append(
            {
                "dataset_id": dataset_id,
                "gse_id": gse_id,
                "suggested_analysis_id": analysis_id,
                "suggested_include": "undetermined",
                "suggested_role": "discovery_candidate",
                "suggested_merge_group": "unassigned",
                "suggested_analysis_strategy": "per_dataset_candidate",
                "suggestion_evidence": json.dumps(
                    evidence, ensure_ascii=False, sort_keys=True
                ),
                "suggestion_confidence": "low",
                "requires_manual_review": "true",
                "analysis_id": "",
                "include": "",
                "role": "",
                "merge_group": "",
                "analysis_strategy": "",
                "reference_dataset": "",
                "notes": "",
            }
        )
    return output


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare suggested dataset plan rows for human review."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    analysis_id = config.get("project", {}).get("analysis_id", "example_analysis")
    rows = build_dataset_plan(read_tsv(args.manifest), analysis_id)
    write_tsv(args.output, FIELDS, rows)
    print(f"Prepared {len(rows)} suggested dataset plan rows.")


if __name__ == "__main__":
    main()
