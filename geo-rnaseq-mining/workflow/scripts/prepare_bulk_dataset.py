#!/usr/bin/env python3

import argparse
import hashlib
from pathlib import Path

import yaml

from bulk_common import (
    active_bulk_rows,
    blocking_issues,
    bulk_entry_branch,
    provenance_payload,
    validate_bulk_count_matrix,
    validate_bulk_entry_contract,
    validate_bulk_reference_config,
    write_json,
)
from preanalysis_common import ISSUE_FIELDS, read_tsv, write_tsv


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_metadata(path, rows):
    fields = list(rows[0]) + ["dataset", "analysis_sample_order"]
    output_rows = []
    for index, row in enumerate(rows, start=1):
        copied = row.copy()
        copied["dataset"] = row["dataset_id"]
        copied["analysis_sample_order"] = str(index)
        output_rows.append(copied)
    write_tsv(path, fields, output_rows)


def prepare_dataset(
    config,
    manifest,
    dataset_id,
    counts_input,
    output_counts,
    output_metadata,
    output_validation,
    output_provenance,
):
    rows = active_bulk_rows(manifest, dataset_id)
    branch = bulk_entry_branch(rows)
    issues = validate_bulk_entry_contract(rows, dataset_id)
    issues.extend(validate_bulk_reference_config(config, branch, dataset_id))
    sample_ids = [row["sample_id"] for row in rows]
    standardized, matrix_issues = validate_bulk_count_matrix(
        counts_input,
        sample_ids,
        dataset_id,
    )
    issues.extend(matrix_issues)
    issues = sorted(
        issues,
        key=lambda row: (
            {"critical": 0, "error": 1, "warning": 2, "info": 3}[row["severity"]],
            row["check_id"],
        ),
    )
    write_tsv(output_validation, ISSUE_FIELDS, issues)
    payload = provenance_payload(
        config,
        dataset_id,
        branch,
        sample_ids,
        counts_input,
    )
    if Path(counts_input).is_file():
        payload["counts_input_sha256"] = sha256_file(counts_input)
    payload["blocking_issue_count"] = len(blocking_issues(issues))
    write_json(output_provenance, payload)
    if blocking_issues(issues):
        check_ids = sorted({issue["check_id"] for issue in blocking_issues(issues)})
        raise RuntimeError(
            f"Bulk input validation failed for {dataset_id}: {', '.join(check_ids)}"
        )
    output = Path(output_counts)
    output.parent.mkdir(parents=True, exist_ok=True)
    standardized.to_csv(output, sep="\t", index=False, lineterminator="\n")
    write_metadata(output_metadata, rows)
    return issues


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate and stage one reviewed bulk dataset without changing raw inputs."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--counts-input", required=True)
    parser.add_argument("--output-counts", required=True)
    parser.add_argument("--output-metadata", required=True)
    parser.add_argument("--output-validation", required=True)
    parser.add_argument("--output-provenance", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    manifest = read_tsv(args.manifest)
    issues = prepare_dataset(
        config,
        manifest,
        args.dataset_id,
        args.counts_input,
        args.output_counts,
        args.output_metadata,
        args.output_validation,
        args.output_provenance,
    )
    print(
        f"Prepared bulk dataset {args.dataset_id}; "
        f"{sum(issue['severity'] == 'warning' for issue in issues)} warnings."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
