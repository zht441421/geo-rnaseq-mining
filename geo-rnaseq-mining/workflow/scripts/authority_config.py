#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator


TABLE_SPECS = {
    "sample_manifest": {
        "headers": [
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
        ],
        "schema": "sample_manifest.schema.json",
    },
    "contrasts": {
        "headers": [
            "contrast_id",
            "analysis_id",
            "data_scope",
            "numerator",
            "denominator",
            "subset_column",
            "subset_value",
            "design_formula",
            "paired",
            "min_replicates_per_group",
            "enabled",
            "notes",
        ],
        "schema": "contrasts.schema.json",
    },
    "dataset_plan": {
        "headers": [
            "analysis_id",
            "dataset_id",
            "include",
            "role",
            "merge_group",
            "analysis_strategy",
            "reference_dataset",
            "notes",
        ],
        "schema": "dataset_plan.schema.json",
    },
    "celltype_ontology": {
        "headers": [
            "dataset_id",
            "author_label",
            "harmonized_level1",
            "harmonized_level2",
            "harmonized_level3",
            "mapping_method",
            "confidence",
            "review_status",
            "notes",
        ],
        "schema": "celltype_ontology.schema.json",
    },
}


@dataclass
class ValidationIssue:
    code: str
    table: str
    path: str
    line: int
    field: str
    value: str
    reason: str
    suggested_action: str

    def format(self):
        return (
            f"[{self.code}] {self.path}:{self.line} field={self.field!r} "
            f"value={self.value!r}: {self.reason} "
            f"Suggested action: {self.suggested_action}"
        )


class AuthorityValidationError(Exception):
    def __init__(self, issues, report):
        self.issues = issues
        self.report = report
        super().__init__("\n".join(issue.format() for issue in issues))


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_or_missing(path):
    path = Path(path)
    return sha256_file(path) if path.is_file() else "MISSING"


def issue(code, table, path, line, field, value, reason, action):
    return ValidationIssue(
        code=code,
        table=table,
        path=str(path),
        line=line,
        field=field,
        value=str(value),
        reason=reason,
        suggested_action=action,
    )


def load_schema(path):
    with Path(path).open(encoding="utf-8") as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return schema


def convert_value(value, property_schema, table, path, line, field, issues):
    expected_type = property_schema.get("type")
    if expected_type == "boolean":
        if value == "true":
            return True
        if value == "false":
            return False
        issues.append(
            issue(
                "INVALID_BOOLEAN",
                table,
                path,
                line,
                field,
                value,
                "Boolean fields accept only lowercase 'true' or 'false'.",
                "Replace the value explicitly with true or false; do not leave it unknown.",
            )
        )
        return value
    if expected_type == "integer":
        if re.fullmatch(r"[0-9]+", value):
            return int(value)
        issues.append(
            issue(
                "INVALID_INTEGER",
                table,
                path,
                line,
                field,
                value,
                "Expected a non-negative base-10 integer.",
                "Enter an integer without units or decimal notation.",
            )
        )
        return value
    return value


def read_table(table, path, schema):
    path = Path(path)
    issues = []
    rows = []
    expected_headers = TABLE_SPECS[table]["headers"]
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        try:
            headers = next(reader)
        except StopIteration:
            return [], [
                issue(
                    "EMPTY_FILE",
                    table,
                    path,
                    1,
                    "<header>",
                    "",
                    "The authority file is empty and has no header.",
                    "Restore the complete template header before validation.",
                )
            ]
        if headers != expected_headers:
            missing = [name for name in expected_headers if name not in headers]
            extra = [name for name in headers if name not in expected_headers]
            issues.append(
                issue(
                    "HEADER_MISMATCH",
                    table,
                    path,
                    1,
                    "<header>",
                    "\t".join(headers),
                    f"Expected the exact ordered header. Missing={missing}; extra={extra}.",
                    "Use the project template exactly; do not rename or append columns.",
                )
            )
            return [], issues

        properties = schema["properties"]
        validator = Draft202012Validator(schema)
        for line_number, values in enumerate(reader, start=2):
            if not values or all(value == "" for value in values):
                issues.append(
                    issue(
                        "BLANK_ROW",
                        table,
                        path,
                        line_number,
                        "<row>",
                        "",
                        "Blank rows are not allowed in authority files.",
                        "Delete the blank row without changing any populated row.",
                    )
                )
                continue
            if len(values) != len(headers):
                issues.append(
                    issue(
                        "COLUMN_COUNT_MISMATCH",
                        table,
                        path,
                        line_number,
                        "<row>",
                        f"{len(values)} columns",
                        f"Expected {len(headers)} tab-separated columns.",
                        "Check embedded tabs and trailing fields in this row.",
                    )
                )
                continue
            raw_row = dict(zip(headers, values))
            typed_row = {}
            for field, value in raw_row.items():
                if value != value.strip():
                    issues.append(
                        issue(
                            "SURROUNDING_WHITESPACE",
                            table,
                            path,
                            line_number,
                            field,
                            value,
                            "Leading or trailing whitespace is not accepted.",
                            "Review the value and remove whitespace manually.",
                        )
                    )
                typed_row[field] = convert_value(
                    value,
                    properties[field],
                    table,
                    path,
                    line_number,
                    field,
                    issues,
                )
            for validation_error in validator.iter_errors(typed_row):
                field = (
                    str(next(iter(validation_error.path)))
                    if validation_error.path
                    else "<row>"
                )
                issues.append(
                    issue(
                        "SCHEMA_VIOLATION",
                        table,
                        path,
                        line_number,
                        field,
                        raw_row.get(field, ""),
                        validation_error.message,
                        "Correct the reviewed TSV explicitly according to the field dictionary.",
                    )
                )
            rows.append(
                {
                    "line": line_number,
                    "raw": raw_row,
                    "typed": typed_row,
                }
            )
    return rows, issues


def duplicate_issues(table, path, rows, fields, code):
    seen = {}
    issues = []
    for record in rows:
        key = tuple(record["raw"][field] for field in fields)
        if key in seen:
            issues.append(
                issue(
                    code,
                    table,
                    path,
                    record["line"],
                    ",".join(fields),
                    "|".join(key),
                    f"Duplicate key; first observed on line {seen[key]}.",
                    "Assign unique reviewed identifiers; excluded rows must remain but still need unique keys.",
                )
            )
        else:
            seen[key] = record["line"]
    return issues


def cross_validate(tables, paths):
    issues = []
    issues.extend(
        duplicate_issues(
            "sample_manifest",
            paths["sample_manifest"],
            tables["sample_manifest"],
            ["sample_id"],
            "DUPLICATE_SAMPLE_ID",
        )
    )
    issues.extend(
        duplicate_issues(
            "contrasts",
            paths["contrasts"],
            tables["contrasts"],
            ["contrast_id"],
            "DUPLICATE_CONTRAST_ID",
        )
    )
    issues.extend(
        duplicate_issues(
            "dataset_plan",
            paths["dataset_plan"],
            tables["dataset_plan"],
            ["analysis_id", "dataset_id"],
            "DUPLICATE_DATASET_PLAN",
        )
    )
    issues.extend(
        duplicate_issues(
            "celltype_ontology",
            paths["celltype_ontology"],
            tables["celltype_ontology"],
            ["dataset_id", "author_label"],
            "DUPLICATE_AUTHOR_LABEL",
        )
    )

    for record in tables["contrasts"]:
        raw = record["raw"]
        if raw["numerator"] == raw["denominator"]:
            issues.append(
                issue(
                    "IDENTICAL_CONTRAST_GROUPS",
                    "contrasts",
                    paths["contrasts"],
                    record["line"],
                    "numerator,denominator",
                    raw["numerator"],
                    "Numerator and denominator must be different.",
                    "Confirm contrast direction and enter two distinct group labels.",
                )
            )

    plan_analysis_ids = {
        record["raw"]["analysis_id"] for record in tables["dataset_plan"]
    }
    plan_dataset_ids = {
        record["raw"]["dataset_id"] for record in tables["dataset_plan"]
    }
    manifest_dataset_ids = {
        record["raw"]["dataset_id"] for record in tables["sample_manifest"]
    }
    for record in tables["contrasts"]:
        analysis_id = record["raw"]["analysis_id"]
        if analysis_id not in plan_analysis_ids:
            issues.append(
                issue(
                    "UNKNOWN_ANALYSIS_ID",
                    "contrasts",
                    paths["contrasts"],
                    record["line"],
                    "analysis_id",
                    analysis_id,
                    "The analysis_id is absent from dataset_plan.tsv.",
                    "Add the reviewed dataset plan or correct analysis_id manually.",
                )
            )
    for record in tables["sample_manifest"]:
        dataset_id = record["raw"]["dataset_id"]
        if plan_dataset_ids and dataset_id not in plan_dataset_ids:
            issues.append(
                issue(
                    "UNKNOWN_DATASET_ID",
                    "sample_manifest",
                    paths["sample_manifest"],
                    record["line"],
                    "dataset_id",
                    dataset_id,
                    "The dataset_id is absent from dataset_plan.tsv.",
                    "Add an explicit dataset plan row or correct dataset_id manually.",
                )
            )
    allowed_ontology_datasets = plan_dataset_ids | manifest_dataset_ids
    for record in tables["celltype_ontology"]:
        dataset_id = record["raw"]["dataset_id"]
        if allowed_ontology_datasets and dataset_id not in allowed_ontology_datasets:
            issues.append(
                issue(
                    "UNKNOWN_ONTOLOGY_DATASET",
                    "celltype_ontology",
                    paths["celltype_ontology"],
                    record["line"],
                    "dataset_id",
                    dataset_id,
                    "The dataset_id is absent from the manifest and dataset plan.",
                    "Correct dataset_id without changing author_label.",
                )
            )
    return issues


def validate_authority_files(paths, schema_dir):
    paths = {name: Path(path) for name, path in paths.items()}
    schema_dir = Path(schema_dir)
    before_hashes = {name: sha256_or_missing(path) for name, path in paths.items()}
    tables = {}
    issues = []
    for table, table_path in paths.items():
        schema = load_schema(schema_dir / TABLE_SPECS[table]["schema"])
        if not table_path.is_file():
            rows, table_issues = [], [
                issue(
                    "MISSING_AUTHORITY_FILE",
                    table,
                    table_path,
                    0,
                    "<file>",
                    "",
                    "The reviewed authority file does not exist.",
                    "Create the reviewed TSV from the project template, complete human review, and rerun validation.",
                )
            ]
        else:
            rows, table_issues = read_table(table, table_path, schema)
        tables[table] = rows
        issues.extend(table_issues)
    issues.extend(cross_validate(tables, paths))
    after_hashes = {name: sha256_or_missing(path) for name, path in paths.items()}
    for table in paths:
        if before_hashes[table] != after_hashes[table]:
            issues.append(
                issue(
                    "AUTHORITY_FILE_MUTATED",
                    table,
                    paths[table],
                    0,
                    "<file>",
                    after_hashes[table],
                    "An authority file changed while it was being validated.",
                    "Stop the workflow and restore the reviewed file from version control.",
                )
            )

    report = {
        "status": "invalid" if issues else "valid",
        "validated_at_utc": utc_now(),
        "authority_precedence": [
            "reviewed_authority_files",
            "config.yaml",
            "suggested_values",
            "raw_geo_sra_fields",
        ],
        "source_sha256": before_hashes,
        "row_counts": {name: len(rows) for name, rows in tables.items()},
        "excluded_samples_preserved": sum(
            record["raw"]["review_status"] == "excluded"
            for record in tables["sample_manifest"]
        ),
        "issues": [asdict(item) for item in issues],
    }
    if issues:
        raise AuthorityValidationError(issues, report)
    return {
        "tables": {
            name: [record["raw"].copy() for record in rows]
            for name, rows in tables.items()
        },
        "report": report,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read and strictly validate the four reviewed authority TSV files."
    )
    parser.add_argument("--sample-manifest", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--celltype-ontology", required=True)
    parser.add_argument("--schema-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write invalid status without exiting non-zero; a later validation gate must enforce it.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    paths = {
        "sample_manifest": args.sample_manifest,
        "contrasts": args.contrasts,
        "dataset_plan": args.dataset_plan,
        "celltype_ontology": args.celltype_ontology,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = validate_authority_files(paths, args.schema_dir)
        report = result["report"]
    except AuthorityValidationError as error:
        report = error.report
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        for validation_issue in error.issues:
            print(validation_issue.format(), file=sys.stderr)
        return 0 if args.report_only else 2
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "Validated reviewed authority files without modification: "
        + ", ".join(
            f"{table}={count}" for table, count in report["row_counts"].items()
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
