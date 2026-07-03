#!/usr/bin/env python3

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path

from metadata_io import NA, read_tsv, utc_now


def escaped(value):
    return html.escape(str(value if value not in (None, "") else ""))


def json_pretty(value):
    if value in (None, "", NA):
        return escaped(value or NA)
    try:
        return escaped(json.dumps(json.loads(value), ensure_ascii=False, indent=2))
    except (TypeError, ValueError):
        return escaped(value)


def render_report(manifest, conflicts, unmapped, dataset_plan=None, classification=None):
    dataset_plan = dataset_plan or []
    classification = classification or []
    conflicts_by_gsm = defaultdict(list)
    for conflict in conflicts:
        conflicts_by_gsm[conflict.get("gsm_id", NA)].append(conflict)
    rows = []
    for row in manifest:
        gsm = row.get("gsm_id", NA)
        conflict_items = conflicts_by_gsm.get(gsm, [])
        conflict_html = "".join(
            (
                f"<li class='{escaped(item.get('severity', 'warning'))}'>"
                f"<strong>{escaped(item.get('conflict_type', NA))}</strong>: "
                f"{escaped(item.get('suggested_action', NA))}</li>"
            )
            for item in conflict_items
        ) or "<li>None recorded</li>"
        rows.append(
            f"""
            <section class="sample">
              <h2>{escaped(gsm)} / {escaped(row.get("srr_id", NA))}</h2>
              <div class="grid">
                <article>
                  <h3>Raw reference</h3>
                  <dl>
                    <dt>GSE</dt><dd>{escaped(row.get("gse_id", NA))}</dd>
                    <dt>Title</dt><dd>{escaped(row.get("geo_title", NA))}</dd>
                    <dt>Source</dt><dd>{escaped(row.get("geo_source_name", NA))}</dd>
                    <dt>Platform</dt><dd>{escaped(row.get("platform", NA))}</dd>
                    <dt>SRX / SRR</dt><dd>{escaped(row.get("srx_id", NA))} / {escaped(row.get("srr_id", NA))}</dd>
                    <dt>Library</dt><dd>{escaped(row.get("library_strategy", NA))}; {escaped(row.get("library_source", NA))}; {escaped(row.get("library_layout", NA))}</dd>
                  </dl>
                  <details><summary>Raw characteristics</summary><pre>{json_pretty(row.get("geo_characteristics_raw", NA))}</pre></details>
                  <details><summary>Supplementary files</summary><pre>{json_pretty(row.get("supplementary_files", NA))}</pre></details>
                </article>
                <article>
                  <h3>Suggestions only</h3>
                  <dl>
                    <dt>Sample ID</dt><dd>{escaped(row.get("suggested_sample_id", NA))}</dd>
                    <dt>Group</dt><dd>{escaped(row.get("suggested_group", NA))}</dd>
                    <dt>Condition</dt><dd>{escaped(row.get("suggested_condition", NA))}</dd>
                    <dt>Tissue</dt><dd>{escaped(row.get("suggested_tissue", NA))}</dd>
                    <dt>Batch</dt><dd>{escaped(row.get("suggested_batch", NA))}</dd>
                    <dt>Data type</dt><dd>{escaped(row.get("suggested_data_type", NA))}</dd>
                    <dt>Confidence</dt><dd>{escaped(row.get("suggestion_confidence", NA))}</dd>
                    <dt>Manual review</dt><dd>{escaped(row.get("requires_manual_review", NA))}</dd>
                  </dl>
                  <details><summary>Suggestion evidence</summary><pre>{json_pretty(row.get("suggestion_evidence", NA))}</pre></details>
                </article>
                <article>
                  <h3>Conflicts and warnings</h3>
                  <ul>{conflict_html}</ul>
                  <p><strong>Formal review status:</strong> {escaped(row.get("review_status", ""))}</p>
                  <p>Formal fields remain blank in the TSV and must be completed there.</p>
                </article>
              </div>
            </section>
            """
        )
    unmapped_rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{escaped(row.get(field, NA))}</td>"
            for field in ("gse_id", "gsm_id", "srx_id", "srr_id", "reason")
        )
        + "</tr>"
        for row in unmapped
    ) or '<tr><td colspan="5">None recorded</td></tr>'
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GEO metadata review report</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
    .notice {{ padding: 1rem; background: #fff7ed; border-left: 5px solid #f97316; }}
    .sample {{ border-top: 2px solid #d1d5db; margin-top: 2rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr)); gap: 1rem; }}
    article {{ background: #f8fafc; padding: 1rem; border-radius: .4rem; }}
    dt {{ font-weight: 700; margin-top: .5rem; }}
    dd {{ margin-left: 0; }}
    pre {{ white-space: pre-wrap; word-break: break-word; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d1d5db; padding: .4rem; text-align: left; }}
    .critical {{ color: #b91c1c; }}
    .warning {{ color: #92400e; }}
  </style>
</head>
<body>
  <h1>GEO metadata review report</h1>
  <p>Generated at {escaped(utc_now())}</p>
  <p class="notice"><strong>Human review required.</strong> Suggestions are not formal analysis metadata and must not be copied automatically.</p>
  <p>Manifest rows: {len(manifest)}; conflicts/warnings: {len(conflicts)}; unmapped records: {len(unmapped)}.</p>
  <p>Suggested dataset plan rows: {len(dataset_plan)}; suggested data-entry classifications: {len(classification)}.</p>
  <h2>Unmapped records</h2>
  <table><thead><tr><th>GSE</th><th>GSM</th><th>SRX</th><th>SRR</th><th>Reason</th></tr></thead>
  <tbody>{unmapped_rows}</tbody></table>
  {''.join(rows)}
</body>
</html>
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Render a standalone human metadata review report."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--conflicts", required=True)
    parser.add_argument("--unmapped-runs", required=True)
    parser.add_argument("--dataset-plan")
    parser.add_argument("--data-entry-classification")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_report(
            read_tsv(args.manifest),
            read_tsv(args.conflicts),
            read_tsv(args.unmapped_runs),
            read_tsv(args.dataset_plan) if args.dataset_plan else [],
            read_tsv(args.data_entry_classification)
            if args.data_entry_classification
            else [],
        ),
        encoding="utf-8",
    )
    print(f"Wrote metadata review report to {output}")


if __name__ == "__main__":
    main()
