#!/usr/bin/env python3

import argparse
import csv
import gzip
import math
from collections import Counter, defaultdict
from pathlib import Path

from preanalysis_common import (
    ISSUE_FIELDS,
    active_samples,
    as_bool,
    is_missing,
    make_issue,
    pass_issue,
    read_tsv,
    sort_issues,
    write_tsv,
)


FASTQ_SUFFIXES = (
    ".fastq",
    ".fq",
    ".fastq.gz",
    ".fq.gz",
)
TABULAR_MATRIX_SUFFIXES = (
    ".tsv",
    ".txt",
    ".csv",
    ".tsv.gz",
    ".txt.gz",
    ".csv.gz",
)
SINGLE_CELL_MATRIX_SUFFIXES = (
    ".h5ad",
    ".h5",
    ".hdf5",
    ".rds",
    ".mtx",
    ".mtx.gz",
)
MANIFEST_FIELDS = [
    "dataset_id",
    "gse_id",
    "gsm_id",
    "srx_id",
    "srr_id",
    "sample_id",
    "subject_id",
    "include",
    "group",
    "condition",
    "tissue",
    "batch",
    "sex",
    "age",
    "timepoint",
    "treatment",
    "paired_group",
    "data_type",
    "library_layout",
    "matrix_path",
    "fastq_r1",
    "fastq_r2",
    "notes",
    "reviewer_note",
    "review_status",
]


def resolve_path(value, project_root):
    path = Path(value)
    return path if path.is_absolute() else Path(project_root) / path


def has_suffix(path, suffixes):
    lowered = str(path).lower()
    return any(lowered.endswith(suffix) for suffix in suffixes)


def split_identifier_values(value):
    if is_missing(value):
        return []
    tokens = str(value).replace(",", ";").split(";")
    return [token.strip() for token in tokens if not is_missing(token.strip())]


def normalized_resolved_path(value, project_root):
    return str(resolve_path(value, project_root).resolve())


def inspect_count_matrix(path):
    path = Path(path)
    delimiter = "," if str(path).lower().endswith((".csv", ".csv.gz")) else "\t"
    opener = gzip.open if str(path).lower().endswith(".gz") else open
    result = {
        "sample_columns": [],
        "duplicate_columns": [],
        "non_numeric_count": 0,
        "fractional_count": 0,
        "negative_count": 0,
        "row_width_errors": 0,
        "gene_rows": 0,
    }
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            result["empty"] = True
            return result
        result["empty"] = len(header) < 2
        result["sample_columns"] = header[1:]
        counts = Counter(header[1:])
        result["duplicate_columns"] = sorted(
            column for column, count in counts.items() if count > 1
        )
        for values in reader:
            if not values or all(value == "" for value in values):
                continue
            result["gene_rows"] += 1
            if len(values) != len(header):
                result["row_width_errors"] += 1
                continue
            for value in values[1:]:
                try:
                    numeric = float(value)
                except ValueError:
                    result["non_numeric_count"] += 1
                    continue
                if not math.isfinite(numeric):
                    result["non_numeric_count"] += 1
                elif numeric < 0:
                    result["negative_count"] += 1
                elif not numeric.is_integer():
                    result["fractional_count"] += 1
    return result


def validate_manifest_rows(manifest, project_root):
    issues = []
    identity_conflicts = []
    sample_counts = Counter(row.get("sample_id", "") for row in manifest)
    for row in manifest:
        sample_id = row.get("sample_id", "NA")
        dataset_id = row.get("dataset_id", "NA")
        include = as_bool(row.get("include"))
        status = row.get("review_status", "")
        if sample_counts[sample_id] > 1:
            item = make_issue(
                "critical",
                "manifest",
                "DUPLICATE_SAMPLE_ID",
                f"sample_id {sample_id!r} occurs {sample_counts[sample_id]} times.",
                "Assign a globally unique sample_id to every retained row, including excluded rows.",
                dataset_id=dataset_id,
                sample_id=sample_id,
            )
            issues.append(item)
            identity_conflicts.append(item)
        if include is True and status != "confirmed":
            check_id = (
                "PENDING_SAMPLE_INCLUDED"
                if status == "pending"
                else "UNCONFIRMED_SAMPLE_INCLUDED"
            )
            issues.append(
                make_issue(
                    "critical",
                    "manifest",
                    check_id,
                    f"Included sample {sample_id} has review_status={status!r}.",
                    "Set include=false or complete human review and set review_status=confirmed.",
                    dataset_id=dataset_id,
                    sample_id=sample_id,
                )
            )
        if status == "excluded" and include is True:
            issues.append(
                make_issue(
                    "critical",
                    "manifest",
                    "EXCLUDED_SAMPLE_INCLUDED",
                    f"Excluded sample {sample_id} is marked include=true.",
                    "Keep the excluded row for audit but set include=false.",
                    dataset_id=dataset_id,
                    sample_id=sample_id,
                )
            )

    for identifier in ("gsm_id", "srr_id"):
        identifier_samples = defaultdict(set)
        for row in manifest:
            values = (
                split_identifier_values(row.get(identifier, "NA"))
                if identifier == "srr_id"
                else [row.get(identifier, "NA")]
            )
            for value in values:
                if is_missing(value):
                    continue
                identifier_samples[value].add(row.get("sample_id", "NA"))
        for value, sample_ids in identifier_samples.items():
            if len(sample_ids) > 1:
                item = make_issue(
                    "critical",
                    "sample_identity",
                    f"DUPLICATE_{identifier.upper()}",
                    f"{identifier} {value} is assigned to multiple sample_id values.",
                    "Resolve the identity conflict manually; do not merge or rename runs automatically.",
                    sample_id=";".join(sorted(sample_ids)),
                    details={identifier: value, "sample_ids": sorted(sample_ids)},
                )
                issues.append(item)
                identity_conflicts.append(item)

    matrix_rows = defaultdict(list)
    fastq_path_samples = defaultdict(list)
    included = active_samples(manifest)
    all_sample_ids = {row.get("sample_id", "NA") for row in manifest}
    excluded_ids = {
        row.get("sample_id", "NA")
        for row in manifest
        if as_bool(row.get("include")) is False
    }
    for row in included:
        sample_id = row["sample_id"]
        dataset_id = row["dataset_id"]
        data_type = row.get("data_type", "")
        matrix_path = row.get("matrix_path", "NA")
        fastq_r1 = row.get("fastq_r1", "NA")
        fastq_r2 = row.get("fastq_r2", "NA")
        layout = row.get("library_layout", "NA").upper()
        present_inputs = [
            value
            for value in (matrix_path, fastq_r1, fastq_r2)
            if not is_missing(value)
        ]
        if not present_inputs:
            issues.append(
                make_issue(
                    "error",
                    "manifest",
                    "NO_ANALYSIS_INPUT",
                    f"Included sample {sample_id} has no matrix or FASTQ path.",
                    "Provide reviewed relative paths or set include=false.",
                    dataset_id=dataset_id,
                    sample_id=sample_id,
                )
            )
        for field, value in (
            ("matrix_path", matrix_path),
            ("fastq_r1", fastq_r1),
            ("fastq_r2", fastq_r2),
        ):
            if is_missing(value):
                continue
            resolved = resolve_path(value, project_root)
            if not resolved.is_file():
                issues.append(
                    make_issue(
                        "error",
                        "manifest",
                        "INPUT_PATH_NOT_FOUND",
                        f"{field} does not exist: {value}",
                        "Correct the reviewed path or restore the referenced file; paths are never rewritten automatically.",
                        dataset_id=dataset_id,
                        sample_id=sample_id,
                        details={"field": field, "resolved_path": str(resolved)},
                    )
                )
            if field.startswith("fastq") and not has_suffix(resolved, FASTQ_SUFFIXES):
                issues.append(
                    make_issue(
                        "error",
                        "manifest",
                        "FASTQ_FORMAT_MISMATCH",
                        f"{field} is not a recognized FASTQ path: {value}",
                        "Confirm data_type and provide a .fastq/.fq file, optionally gzip-compressed.",
                        dataset_id=dataset_id,
                        sample_id=sample_id,
                    )
                )
            if field.startswith("fastq"):
                fastq_path_samples[normalized_resolved_path(value, project_root)].append(
                    {
                        "dataset_id": dataset_id,
                        "sample_id": sample_id,
                        "field": field,
                        "path": value,
                    }
                )
        if (
            layout == "PAIRED"
            and not is_missing(fastq_r1)
            and not is_missing(fastq_r2)
            and normalized_resolved_path(fastq_r1, project_root)
            == normalized_resolved_path(fastq_r2, project_root)
        ):
            issues.append(
                make_issue(
                    "critical",
                    "manifest",
                    "PAIRED_FASTQ_MATES_IDENTICAL",
                    f"Paired-end sample {sample_id} uses the same file for fastq_r1 and fastq_r2.",
                    "Correct the reviewed FASTQ mate paths; mates are never inferred or swapped automatically.",
                    dataset_id=dataset_id,
                    sample_id=sample_id,
                    details={"fastq_r1": fastq_r1, "fastq_r2": fastq_r2},
                )
            )
        if layout == "PAIRED" and (is_missing(fastq_r1) != is_missing(fastq_r2)):
            issues.append(
                make_issue(
                    "error",
                    "manifest",
                    "INCOMPLETE_PAIRED_FASTQ",
                    f"Paired-end sample {sample_id} does not have both FASTQ mates.",
                    "Provide both fastq_r1 and fastq_r2 or correct library_layout manually.",
                    dataset_id=dataset_id,
                    sample_id=sample_id,
                )
            )
        if layout == "SINGLE" and not is_missing(fastq_r2):
            issues.append(
                make_issue(
                    "warning",
                    "manifest",
                    "SINGLE_END_WITH_R2",
                    f"Single-end sample {sample_id} has fastq_r2.",
                    "Confirm library_layout and FASTQ assignment manually.",
                    dataset_id=dataset_id,
                    sample_id=sample_id,
                )
            )
        if not is_missing(matrix_path):
            resolved_matrix = resolve_path(matrix_path, project_root)
            matrix_rows[str(resolved_matrix)].append(row)
            lowered_type = data_type.lower()
            if ("bulk" in lowered_type or "pseudobulk" in lowered_type) and not has_suffix(
                resolved_matrix, TABULAR_MATRIX_SUFFIXES
            ):
                issues.append(
                    make_issue(
                        "error",
                        "manifest",
                        "COUNT_MATRIX_FORMAT_MISMATCH",
                        f"{data_type} sample {sample_id} references unsupported count matrix format {matrix_path}.",
                        "Provide a tab-delimited or CSV raw count matrix with sample_id column names.",
                        dataset_id=dataset_id,
                        sample_id=sample_id,
                    )
                )
            if (
                ("scrna" in lowered_type or "snrna" in lowered_type)
                and "pseudobulk" not in lowered_type
                and not resolved_matrix.is_dir()
                and not has_suffix(
                    resolved_matrix,
                    SINGLE_CELL_MATRIX_SUFFIXES,
                )
            ):
                issues.append(
                    make_issue(
                        "error",
                        "manifest",
                        "SINGLE_CELL_MATRIX_FORMAT_MISMATCH",
                        f"Single-cell sample {sample_id} references unsupported format {matrix_path}.",
                        "Provide a reviewed 10X MTX/H5, Cell Ranger directory, "
                        "H5AD, or RDS raw-count input.",
                        dataset_id=dataset_id,
                        sample_id=sample_id,
                )
            )

    for resolved_path, uses in fastq_path_samples.items():
        sample_ids = sorted({item["sample_id"] for item in uses})
        fields = sorted({item["field"] for item in uses})
        if len(sample_ids) > 1:
            item = make_issue(
                "critical",
                "sample_identity",
                "FASTQ_PATH_REUSED_ACROSS_SAMPLES",
                f"FASTQ path is assigned to multiple sample_id values: {sample_ids}",
                "Resolve the reviewed FASTQ ownership manually; runs are not shared across biological samples automatically.",
                sample_id=";".join(sample_ids),
                details={"resolved_path": resolved_path, "uses": uses},
            )
            issues.append(item)
            identity_conflicts.append(item)
        elif len(fields) > 1:
            item = make_issue(
                "critical",
                "sample_identity",
                "FASTQ_PATH_REUSED_WITHIN_SAMPLE",
                f"FASTQ path is assigned to multiple FASTQ fields for sample_id {sample_ids[0]}.",
                "Correct the reviewed R1/R2 fields before analysis.",
                sample_id=sample_ids[0],
                details={"resolved_path": resolved_path, "uses": uses},
            )
            issues.append(item)
            identity_conflicts.append(item)

    for matrix_path, rows in matrix_rows.items():
        path = Path(matrix_path)
        if not path.is_file() or not has_suffix(path, TABULAR_MATRIX_SUFFIXES):
            continue
        inspected = inspect_count_matrix(path)
        dataset_ids = sorted({row["dataset_id"] for row in rows})
        expected = {row["sample_id"] for row in rows}
        observed = set(inspected["sample_columns"])
        if inspected.get("empty") or inspected["gene_rows"] == 0:
            issues.append(
                make_issue(
                    "critical",
                    "matrix",
                    "EMPTY_COUNT_MATRIX",
                    f"Count matrix has no usable gene rows: {path}",
                    "Restore a non-empty raw count matrix.",
                    dataset_id=";".join(dataset_ids),
                    details=inspected,
                )
            )
            continue
        if inspected["duplicate_columns"]:
            issues.append(
                make_issue(
                    "critical",
                    "matrix",
                    "DUPLICATE_COUNT_COLUMNS",
                    f"Count matrix contains duplicate sample columns: {inspected['duplicate_columns']}",
                    "Correct the matrix column identities before analysis.",
                    dataset_id=";".join(dataset_ids),
                    details={"matrix_path": matrix_path},
                )
            )
        missing_columns = sorted(expected - observed)
        if missing_columns:
            issues.append(
                make_issue(
                    "error",
                    "matrix",
                    "COUNT_SAMPLE_COLUMNS_MISSING",
                    f"Count matrix is missing reviewed sample_id columns: {missing_columns}",
                    "Make matrix column names exactly match sample_id; do not rename reviewed sample_id automatically.",
                    dataset_id=";".join(dataset_ids),
                    details={"matrix_path": matrix_path, "missing": missing_columns},
                )
            )
        extra_columns = sorted(observed - expected)
        if extra_columns:
            unknown = sorted(set(extra_columns) - all_sample_ids)
            severity = "error" if unknown else "warning"
            issues.append(
                make_issue(
                    severity,
                    "matrix",
                    "COUNT_MATRIX_EXTRA_COLUMNS",
                    f"Count matrix contains columns not selected for this matrix: {extra_columns}",
                    "Confirm whether columns are excluded reviewed samples; subset only in downstream derived outputs.",
                    dataset_id=";".join(dataset_ids),
                    details={
                        "matrix_path": matrix_path,
                        "unknown_columns": unknown,
                        "reviewed_excluded_columns": sorted(
                            set(extra_columns) & excluded_ids
                        ),
                    },
                )
            )
        for count_key, check_id, label in (
            ("non_numeric_count", "NON_NUMERIC_COUNT_MATRIX", "non-numeric"),
            ("fractional_count", "NON_INTEGER_COUNT_MATRIX", "fractional"),
            ("negative_count", "NEGATIVE_COUNT_MATRIX", "negative"),
            ("row_width_errors", "MALFORMED_COUNT_MATRIX_ROWS", "malformed"),
        ):
            if inspected[count_key]:
                issues.append(
                    make_issue(
                        "critical",
                        "matrix",
                        check_id,
                        f"Count matrix contains {inspected[count_key]} {label} values/rows.",
                        "Use an unmodified raw non-negative integer count matrix; TPM/FPKM/CPM/log values are not accepted.",
                        dataset_id=";".join(dataset_ids),
                        details={"matrix_path": matrix_path, **inspected},
                    )
                )
    if manifest and not issues:
        issues.append(
            pass_issue(
                "manifest",
                "MANIFEST_VALID",
                "Manifest identity, input paths, and matrix checks passed.",
            )
        )
    return sort_issues(issues), sort_issues(identity_conflicts)


def write_validated_manifest(path, manifest, issues):
    base_fields = list(manifest[0]) if manifest else MANIFEST_FIELDS
    issue_counts = Counter(
        item["sample_id"]
        for item in issues
        if item["status"] == "fail" and item["sample_id"] != "NA"
    )
    blocking_samples = {
        item["sample_id"]
        for item in issues
        if item["severity"] in {"critical", "error"} and item["sample_id"] != "NA"
    }
    output_rows = []
    for row in manifest:
        copied = row.copy()
        sample_id = row.get("sample_id", "NA")
        copied["validation_eligible"] = str(
            as_bool(row.get("include")) is True
            and row.get("review_status") == "confirmed"
            and sample_id not in blocking_samples
        ).lower()
        copied["validation_issue_count"] = str(issue_counts[sample_id])
        output_rows.append(copied)
    write_tsv(
        path,
        base_fields + ["validation_eligible", "validation_issue_count"],
        output_rows,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Validate reviewed sample manifest.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--validated-manifest", required=True)
    parser.add_argument("--errors", required=True)
    parser.add_argument("--warnings", required=True)
    parser.add_argument("--identity-conflicts", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        missing_issue = make_issue(
            "critical",
            "manifest",
            "REVIEWED_MANIFEST_MISSING",
            f"Reviewed manifest does not exist: {manifest_path}",
            "Create metadata/reviewed/sample_manifest.tsv from the project template and complete human review.",
        )
        write_validated_manifest(args.validated_manifest, [], [missing_issue])
        write_tsv(args.errors, ISSUE_FIELDS, [missing_issue])
        write_tsv(args.warnings, ISSUE_FIELDS, [])
        write_tsv(args.identity_conflicts, ISSUE_FIELDS, [])
        return 0
    manifest = read_tsv(manifest_path)
    issues, identity_conflicts = validate_manifest_rows(
        manifest, Path(args.project_root).resolve()
    )
    write_validated_manifest(args.validated_manifest, manifest, issues)
    write_tsv(
        args.errors,
        ISSUE_FIELDS,
        [item for item in issues if item["severity"] in {"critical", "error"}],
    )
    write_tsv(
        args.warnings,
        ISSUE_FIELDS,
        [item for item in issues if item["severity"] in {"warning", "info"}],
    )
    write_tsv(args.identity_conflicts, ISSUE_FIELDS, identity_conflicts)
    print(
        f"Validated {len(manifest)} manifest rows; "
        f"{sum(item['severity'] in {'critical', 'error'} for item in issues)} blocking issues."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
