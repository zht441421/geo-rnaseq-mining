#!/usr/bin/env python3

import argparse
import html
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from preanalysis_common import ISSUE_FIELDS, as_bool, read_tsv


def escaped(value):
    return html.escape(str(value if value is not None else ""))


def authority_issues(path):
    if not Path(path).is_file():
        return []
    report = json.loads(Path(path).read_text(encoding="utf-8"))
    output = []
    for item in report.get("issues", []):
        output.append(
            {
                "severity": "critical",
                "scope": "authority_schema",
                "check_id": item.get("code", "AUTHORITY_SCHEMA_INVALID"),
                "analysis_id": "NA",
                "dataset_id": "NA",
                "sample_id": "NA",
                "subject_id": "NA",
                "contrast_id": "NA",
                "status": "fail",
                "message": item.get("reason", "Reviewed authority file is invalid."),
                "suggested_action": item.get(
                    "suggested_action", "Correct the reviewed authority file manually."
                ),
                "details": json.dumps(item, ensure_ascii=False, sort_keys=True),
            }
        )
    return output


def blocked_analysis_ids(issues, dataset_plan):
    dataset_to_analyses = defaultdict(set)
    all_analyses = set()
    for row in dataset_plan:
        analysis_id = row.get("analysis_id", "NA")
        all_analyses.add(analysis_id)
        if as_bool(row.get("include")) is True:
            dataset_to_analyses[row.get("dataset_id", "NA")].add(analysis_id)
    blocked = set()
    for item in issues:
        if item.get("severity") != "error":
            continue
        analysis_id = item.get("analysis_id", "NA")
        dataset_id = item.get("dataset_id", "NA")
        if analysis_id != "NA":
            blocked.add(analysis_id)
        elif dataset_id != "NA":
            for value in dataset_id.split(";"):
                blocked.update(dataset_to_analyses.get(value, set()))
        else:
            blocked.update(all_analyses)
    return sorted(blocked)


def render_report(issues, validated_manifest, crosstab, status):
    counts = status["counts"]
    severity_cards = "".join(
        f"<div class='card {severity}'><strong>{severity}</strong><span>{counts.get(severity, 0)}</span></div>"
        for severity in ("critical", "error", "warning", "info")
    )
    issue_rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{escaped(item.get(field, 'NA'))}</td>"
            for field in (
                "severity",
                "scope",
                "check_id",
                "analysis_id",
                "dataset_id",
                "sample_id",
                "message",
                "suggested_action",
            )
        )
        + "</tr>"
        for item in issues
    ) or '<tr><td colspan="8">No validation records.</td></tr>'
    crosstab_rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{escaped(row.get(field, 'NA'))}</td>"
            for field in (
                "analysis_id",
                "dataset_id",
                "group",
                "sample_count",
                "subject_count",
                "fraction_of_analysis",
            )
        )
        + "</tr>"
        for row in crosstab
    ) or '<tr><td colspan="6">No included analysis samples.</td></tr>'
    eligible = sum(
        row.get("validation_eligible") == "true" for row in validated_manifest
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pre-analysis validation report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #172033; }}
    .cards {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
    .card {{ padding: 1rem; border-radius: .4rem; background: #eef2ff; min-width: 8rem; }}
    .card span {{ display: block; font-size: 2rem; }}
    .critical {{ border-left: 6px solid #991b1b; }}
    .error {{ border-left: 6px solid #dc2626; }}
    .warning {{ border-left: 6px solid #d97706; }}
    .info {{ border-left: 6px solid #2563eb; }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid #cbd5e1; padding: .45rem; text-align: left; vertical-align: top; }}
    th {{ background: #f1f5f9; position: sticky; top: 0; }}
    .notice {{ padding: 1rem; background: #fff7ed; border-left: 6px solid #f97316; }}
  </style>
</head>
<body>
  <h1>Formal pre-analysis validation</h1>
  <p>Generated at {escaped(status["generated_at_utc"])}</p>
  <p class="notice">No user-reviewed value was modified. Critical issues block the workflow. Errors block the listed analysis_id values.</p>
  <div class="cards">{severity_cards}</div>
  <p>Reviewed manifest rows: {len(validated_manifest)}; validation-eligible rows: {eligible}.</p>
  <p><strong>Blocked analyses:</strong> {escaped(", ".join(status["blocked_analysis_ids"]) or "none")}</p>
  <h2>Dataset × group cross-tabulation</h2>
  <table>
    <thead><tr><th>analysis_id</th><th>dataset_id</th><th>group</th><th>samples</th><th>subjects</th><th>fraction</th></tr></thead>
    <tbody>{crosstab_rows}</tbody>
  </table>
  <h2>Validation records</h2>
  <table>
    <thead><tr><th>severity</th><th>scope</th><th>check_id</th><th>analysis_id</th><th>dataset_id</th><th>sample_id</th><th>message</th><th>suggested action</th></tr></thead>
    <tbody>{issue_rows}</tbody>
  </table>
</body>
</html>
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Aggregate formal pre-analysis validation records."
    )
    parser.add_argument("--authority-report", required=True)
    parser.add_argument("--validated-manifest", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--crosstab", required=True)
    parser.add_argument("--issue-files", nargs="+", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--status", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    issues = authority_issues(args.authority_report)
    for issue_file in args.issue_files:
        issues.extend(read_tsv(issue_file))
    unique = {}
    for item in issues:
        key = tuple(item.get(field, "") for field in ISSUE_FIELDS)
        unique[key] = item
    issues = sorted(
        unique.values(),
        key=lambda item: (
            {"critical": 0, "error": 1, "warning": 2, "info": 3}.get(
                item.get("severity"), 99
            ),
            item.get("analysis_id", "NA"),
            item.get("check_id", ""),
        ),
    )
    counts = Counter(item.get("severity", "info") for item in issues)
    dataset_plan = read_tsv(args.dataset_plan)
    status = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "counts": {
            severity: counts.get(severity, 0)
            for severity in ("critical", "error", "warning", "info")
        },
        "critical_block": counts.get("critical", 0) > 0,
        "blocked_analysis_ids": blocked_analysis_ids(issues, dataset_plan),
        "formal_analysis_allowed": counts.get("critical", 0) == 0,
    }
    status_path = Path(args.status)
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_report(
            issues,
            read_tsv(args.validated_manifest),
            read_tsv(args.crosstab),
            status,
        ),
        encoding="utf-8",
    )
    print(
        "Validation report written: "
        + ", ".join(f"{key}={value}" for key, value in status["counts"].items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
