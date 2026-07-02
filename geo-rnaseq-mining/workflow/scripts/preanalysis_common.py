import csv
import json
from collections import defaultdict
from pathlib import Path


NA_VALUES = {"", "NA", "N/A", "null", "None"}
ISSUE_FIELDS = [
    "severity",
    "scope",
    "check_id",
    "analysis_id",
    "dataset_id",
    "sample_id",
    "subject_id",
    "contrast_id",
    "status",
    "message",
    "suggested_action",
    "details",
]
SEVERITY_ORDER = {"critical": 0, "error": 1, "warning": 2, "info": 3}


def is_missing(value):
    return value is None or str(value) in NA_VALUES


def as_bool(value):
    if value is True or value == "true":
        return True
    if value is False or value == "false":
        return False
    return None


def read_tsv(path):
    path = Path(path)
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path, fieldnames, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def make_issue(
    severity,
    scope,
    check_id,
    message,
    suggested_action,
    analysis_id="NA",
    dataset_id="NA",
    sample_id="NA",
    subject_id="NA",
    contrast_id="NA",
    status="fail",
    details=None,
):
    if severity not in SEVERITY_ORDER:
        raise ValueError(f"Unsupported severity: {severity}")
    return {
        "severity": severity,
        "scope": scope,
        "check_id": check_id,
        "analysis_id": analysis_id or "NA",
        "dataset_id": dataset_id or "NA",
        "sample_id": sample_id or "NA",
        "subject_id": subject_id or "NA",
        "contrast_id": contrast_id or "NA",
        "status": status,
        "message": message,
        "suggested_action": suggested_action,
        "details": json.dumps(details or {}, ensure_ascii=False, sort_keys=True),
    }


def pass_issue(scope, check_id, message, **identifiers):
    return make_issue(
        "info",
        scope,
        check_id,
        message,
        "No action required.",
        status="pass",
        **identifiers,
    )


def sort_issues(issues):
    return sorted(
        issues,
        key=lambda row: (
            SEVERITY_ORDER.get(row["severity"], 99),
            row.get("analysis_id", "NA"),
            row.get("dataset_id", "NA"),
            row.get("sample_id", "NA"),
            row["check_id"],
        ),
    )


def active_samples(manifest):
    return [
        row
        for row in manifest
        if as_bool(row.get("include")) is True
        and row.get("review_status") == "confirmed"
    ]


def samples_by_dataset(manifest):
    grouped = defaultdict(list)
    for row in active_samples(manifest):
        grouped[row.get("dataset_id", "NA")].append(row)
    return grouped


def rows_for_analysis(manifest, plan, analysis_id):
    included_datasets = {
        row["dataset_id"]
        for row in plan
        if row.get("analysis_id") == analysis_id and as_bool(row.get("include")) is True
    }
    return [
        row
        for row in active_samples(manifest)
        if row.get("dataset_id") in included_datasets
    ]


def issue_counts(issues):
    counts = {severity: 0 for severity in SEVERITY_ORDER}
    for item in issues:
        counts[item["severity"]] = counts.get(item["severity"], 0) + 1
    return counts
