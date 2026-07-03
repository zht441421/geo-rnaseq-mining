#!/usr/bin/env python3

import argparse
import csv
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml


MANIFEST_FIELDS = [
    "path",
    "module",
    "size_bytes",
    "sha256",
    "modified_utc",
]


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path):
    path = Path(path)
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def module_for(path):
    parts = Path(path).parts
    if "per_dataset" in parts:
        return "per_dataset"
    if "meta_analysis" in parts:
        return "meta_analysis"
    if "merged_analysis" in parts:
        return "merged_analysis"
    if "consensus" in parts:
        return "consensus"
    if "compatibility" in parts:
        return "compatibility"
    return "other"


def inventory_results(result_root, excluded_root):
    result_root = Path(result_root)
    excluded_root = Path(excluded_root).resolve()
    rows = []
    if not result_root.is_dir():
        return rows
    for path in sorted(item for item in result_root.rglob("*") if item.is_file()):
        if excluded_root in path.resolve().parents:
            continue
        stat = path.stat()
        rows.append(
            {
                "path": str(path),
                "module": module_for(path),
                "size_bytes": stat.st_size,
                "sha256": sha256_file(path),
                "modified_utc": datetime.fromtimestamp(
                    stat.st_mtime,
                    tz=timezone.utc,
                ).isoformat(),
            }
        )
    return rows


def authority_snapshot(paths):
    return {
        str(path): {
            "exists": Path(path).is_file(),
            "sha256": sha256_file(path) if Path(path).is_file() else "NA",
        }
        for path in paths
    }


def render_table(rows, columns):
    if not rows:
        return "<p>None.</p>"
    header = "".join(f"<th>{html.escape(column)}</th>" for column in columns)
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row.get(column, 'NA')))}</td>"
            for column in columns
        )
        + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"


def generate_report(
    config,
    validation_status,
    issue_files,
    result_root,
    authority_files,
    output_html,
    output_manifest,
    output_provenance,
):
    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    inventory = inventory_results(result_root, output_html.parent)
    with Path(output_manifest).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=MANIFEST_FIELDS,
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(inventory)
    issues = []
    for path in issue_files:
        for row in read_tsv(path):
            if row.get("status") == "fail":
                issues.append(row)
    if not config["reporting"]["include_warnings"]:
        issues = [
            row
            for row in issues
            if row.get("severity") in {"critical", "error"}
        ]
    validation_payload = {}
    if Path(validation_status).is_file():
        validation_payload = json.loads(
            Path(validation_status).read_text(encoding="utf-8")
        )
    snapshot = authority_snapshot(authority_files)
    provenance = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "project": config["project"]["name"],
        "validation_status": validation_payload,
        "authority_snapshot": snapshot,
        "result_file_count": len(inventory),
        "result_manifest_sha256": sha256_file(output_manifest),
        "reporting_config": config["reporting"],
    }
    Path(output_provenance).write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    module_counts = {}
    for row in inventory:
        module_counts[row["module"]] = module_counts.get(row["module"], 0) + 1
    module_rows = [
        {"module": module, "file_count": count}
        for module, count in sorted(module_counts.items())
    ]
    authority_rows = [
        {"path": path, **details} for path, details in snapshot.items()
    ]
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{html.escape(config['reporting']['title'])}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #17202a; }}
table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
th, td {{ border: 1px solid #ccd1d1; padding: .45rem; text-align: left; }}
th {{ background: #eef3f6; }}
code {{ background: #f4f6f7; padding: .15rem .3rem; }}
</style>
</head>
<body>
<h1>{html.escape(config['reporting']['title'])}</h1>
<p>Generated: {html.escape(provenance['generated_utc'])}</p>
<h2>Validation</h2>
<pre>{html.escape(json.dumps(validation_payload, ensure_ascii=False, indent=2))}</pre>
<h2>Open validation findings</h2>
{render_table(issues, ['severity', 'scope', 'check_id', 'analysis_id', 'dataset_id', 'message'])}
<h2>Result modules</h2>
{render_table(module_rows, ['module', 'file_count'])}
<h2>Test and execution status</h2>
<p>This report records validation payloads and file hashes only. It does not
certify any test as passed unless an explicit test-status artifact is provided
by the workflow.</p>
<h2>Authority snapshot</h2>
{render_table(authority_rows, ['path', 'exists', 'sha256'])}
<h2>Known limitations</h2>
<ul>
<li>Suggested metadata, automated cell-type labels, and candidate genes require human review.</li>
<li>Automated bulk/single-cell integration output is candidate evidence only, not a final biological conclusion.</li>
<li>Unrun real GEO/SRA network tests and native R/Bioconductor execution must remain visible in handoff or test-status records.</li>
</ul>
<h2>Reproducibility</h2>
<p>Complete file-level hashes are stored in <code>{html.escape(str(output_manifest))}</code>.
Report provenance is stored in <code>{html.escape(str(output_provenance))}</code>.</p>
</body>
</html>
"""
    output_html.write_text(document, encoding="utf-8")
    return {
        "result_file_count": len(inventory),
        "issue_count": len(issues),
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a provenance-aware project report."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--validation-status", required=True)
    parser.add_argument("--issue-files", nargs="*", default=[])
    parser.add_argument("--result-root", default="results")
    parser.add_argument("--authority-files", nargs="+", required=True)
    parser.add_argument("--output-html", required=True)
    parser.add_argument("--output-manifest", required=True)
    parser.add_argument("--output-provenance", required=True)
    parser.add_argument("--output-marker", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    summary = generate_report(
        config,
        args.validation_status,
        args.issue_files,
        args.result_root,
        args.authority_files,
        args.output_html,
        args.output_manifest,
        args.output_provenance,
    )
    Path(args.output_marker).write_text(
        f"result_file_count={summary['result_file_count']}\n"
        f"issue_count={summary['issue_count']}\n",
        encoding="utf-8",
    )
    print(
        f"Generated project report with {summary['result_file_count']} result files."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
