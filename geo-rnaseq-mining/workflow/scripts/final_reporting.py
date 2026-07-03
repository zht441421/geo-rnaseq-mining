#!/usr/bin/env python3

import argparse
import csv
import hashlib
import html
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import yaml


NA = "NA"
FASTQ_SUFFIXES = (".fastq", ".fq", ".fastq.gz", ".fq.gz", ".sra", ".bam", ".cram")

PROVENANCE_FIELDS = [
    "path",
    "module",
    "size_bytes",
    "sha256",
    "modified_utc",
]
SOFTWARE_FIELDS = ["software", "version", "source", "command"]
REFERENCE_FIELDS = ["reference_field", "value", "exists", "sha256", "status"]
AUDIT_FIELDS = [
    "field",
    "record_id",
    "original_value",
    "suggested_value",
    "final_user_value",
    "review_status",
    "reviewer_note",
    "modification_timestamp",
    "source_file",
    "pipeline_version",
]
EXCLUSION_FIELDS = ["scope", "record_id", "reason", "source_file", "review_status"]
WARNING_FIELDS = ["severity", "scope", "check_id", "analysis_id", "dataset_id", "message", "source_file"]
REPRO_FIELDS = ["artifact", "path", "sha256", "description"]
PACKAGE_FIELDS = ["path", "included", "reason", "size_bytes", "sha256"]
CHECKSUM_REPORT_FIELDS = ["path", "module", "size_bytes", "sha256"]
CANDIDATE_SCORE_FIELDS = [
    "canonical_gene_id",
    "best_bulk_log2fc",
    "best_pseudobulk_log2fc",
    "bulk_pseudobulk_direction",
    "dominant_cell_type",
    "limitations",
    "dataset_driven",
    "confidence",
    "is_final_biological_conclusion",
    "required_action",
]
SUGGESTED_ANNOTATION_FIELDS = [
    "cluster",
    "suggested_label",
    "review_status",
    "is_final",
    "required_action",
]
TEST_STATUS_FIELDS = ["scope", "command", "status", "result", "notes"]
DEFAULT_TEST_STATUS_ROWS = [
    {
        "scope": "unit_tests",
        "command": 'python -m unittest discover -s tests/unit -p "test_*.py" -v',
        "status": "not_run_by_workflow",
        "result": "not_run",
        "notes": "Run manually and record exact command output in the current session handoff.",
    },
    {
        "scope": "integration_tests",
        "command": 'python -m unittest discover -s tests/integration -p "test_*.py" -v',
        "status": "not_run_by_workflow",
        "result": "not_run",
        "notes": "Opt-in network/SRA tests may be skipped unless their environment variables are set.",
    },
    {
        "scope": "snakemake_dry_run",
        "command": "snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --quiet",
        "status": "not_run_by_workflow",
        "result": "not_run",
        "notes": "Run manually for the active configuration before claiming DAG readiness.",
    },
    {
        "scope": "all_full_default",
        "command": "snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1 all_full --printshellcmds",
        "status": "not_run_by_workflow",
        "result": "not_run",
        "notes": "Default empty-accession run is not evidence of real GEO/SRA or native R/Bioconductor execution.",
    },
    {
        "scope": "real_geo_sra_network",
        "command": "RUN_GEO_NETWORK_TESTS=1 and RUN_SRA_NETWORK_TESTS=1 with SRA_TEST_ACCESSION",
        "status": "opt_in_not_run_by_default",
        "result": "not_run",
        "notes": "Requires explicit opt-in network test environment.",
    },
    {
        "scope": "native_r_bioconductor",
        "command": "configured real-accession GEOquery and DESeq2 execution",
        "status": "not_run_by_workflow",
        "result": "not_run",
        "notes": "Validate in Linux, WSL, or a container before claiming real-accession support.",
    },
]


def now():
    return datetime.now(timezone.utc).isoformat()


def read_tsv(path):
    path = Path(path)
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_many_tsv(paths):
    rows = []
    for path in paths or []:
        rows.extend(read_tsv(path))
    return rows


def write_tsv(path, fieldnames, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path):
    path = Path(path)
    if not path.is_file():
        return NA
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def module_for(path):
    parts = Path(path).parts
    for name in ("per_dataset", "merged_analysis", "meta_analysis", "consensus", "integration", "compatibility", "reports"):
        if name in parts:
            return name
    return "other"


def is_large_raw(path):
    lowered = str(path).lower()
    return lowered.endswith(FASTQ_SUFFIXES)


def iter_files(root):
    root = Path(root)
    if not root.exists():
        return []
    return sorted(item for item in root.rglob("*") if item.is_file())


def collect_file_rows(roots):
    rows = []
    for root in roots:
        for path in iter_files(root):
            if is_large_raw(path):
                continue
            stat = path.stat()
            rows.append(
                {
                    "path": str(path),
                    "module": module_for(path),
                    "size_bytes": stat.st_size,
                    "sha256": sha256_file(path),
                    "modified_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
    return rows


def command_version(command):
    resolved = shutil.which(command[0])
    if not resolved:
        return "not_found"
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    except Exception as error:
        return f"error:{error}"
    text = (completed.stdout or completed.stderr).strip().splitlines()
    return text[0] if text else f"exit_code={completed.returncode}"


def rscript_version_command():
    launcher = Path(__file__).with_name("run_rscript.py")
    if launcher.is_file():
        return [sys.executable, str(launcher), "--version"]
    return ["Rscript", "--version"]


def collect_provenance(args):
    rows = collect_file_rows(args.roots)
    write_tsv(args.output, PROVENANCE_FIELDS, rows)
    Path(args.marker).write_text(f"file_count={len(rows)}\n", encoding="utf-8")


def collect_software_versions(args):
    commands = {
        "python": ["python", "--version"],
        "snakemake": ["snakemake", "--version"],
        "Rscript": rscript_version_command(),
        "platform": [],
    }
    rows = []
    for name, command in commands.items():
        rows.append(
            {
                "software": name,
                "version": platform.platform() if name == "platform" else command_version(command),
                "source": "runtime",
                "command": " ".join(command) if command else "platform.platform()",
            }
        )
    write_tsv(args.output, SOFTWARE_FIELDS, rows)
    Path(args.marker).write_text(f"software_count={len(rows)}\n", encoding="utf-8")


def collect_reference_metadata(args):
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    references = config.get("references", {})
    rows = []
    for key, value in sorted(references.items()):
        path = Path(str(value)) if value not in (None, "") else None
        exists = path.is_file() if path else False
        rows.append(
            {
                "reference_field": key,
                "value": value if value is not None else NA,
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else NA,
                "status": "confirmed_path" if exists else "metadata_or_unresolved",
            }
        )
    write_tsv(args.output, REFERENCE_FIELDS, rows)
    Path(args.marker).write_text(f"reference_count={len(rows)}\n", encoding="utf-8")


def row_id(row):
    for key in ("sample_id", "contrast_id", "analysis_id", "dataset_id", "author_label"):
        if row.get(key):
            return row[key]
    return NA


def build_audit_trail(args):
    pipeline_version = git_version()
    audit = []
    exclusions = []
    warnings = []
    for source in args.authority_files:
        rows = read_tsv(source)
        for row in rows:
            rid = row_id(row)
            review_status = row.get("review_status", row.get("status", NA))
            if row.get("include") == "false":
                exclusions.append(
                    {
                        "scope": "authority",
                        "record_id": rid,
                        "reason": row.get("exclusion_reason", row.get("notes", "include=false")),
                        "source_file": source,
                        "review_status": review_status,
                    }
                )
            for field, final_value in row.items():
                if field.endswith("_suggested") or field.endswith("_raw"):
                    continue
                audit.append(
                    {
                        "field": field,
                        "record_id": rid,
                        "original_value": row.get(f"{field}_raw", NA),
                        "suggested_value": row.get(f"{field}_suggested", NA),
                        "final_user_value": final_value if final_value not in (None, "") else NA,
                        "review_status": review_status,
                        "reviewer_note": row.get("reviewer_note", row.get("notes", NA)),
                        "modification_timestamp": row.get("modified_at", row.get("modification_timestamp", NA)),
                        "source_file": source,
                        "pipeline_version": pipeline_version,
                    }
                )
    for issue_file in args.issue_files:
        for row in read_tsv(issue_file):
            if row.get("severity") in {"warning", "error", "critical"} or row.get("status") == "fail":
                warnings.append(
                    {
                        "severity": row.get("severity", "warning"),
                        "scope": row.get("scope", NA),
                        "check_id": row.get("check_id", NA),
                        "analysis_id": row.get("analysis_id", NA),
                        "dataset_id": row.get("dataset_id", NA),
                        "message": row.get("message", NA),
                        "source_file": issue_file,
                    }
                )
    write_tsv(args.audit, AUDIT_FIELDS, audit)
    write_tsv(args.exclusions, EXCLUSION_FIELDS, exclusions)
    write_tsv(args.warnings, WARNING_FIELDS, warnings)
    Path(args.marker).write_text(f"audit_count={len(audit)}\nwarning_count={len(warnings)}\n", encoding="utf-8")


def git_version():
    try:
        completed = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False)
    except Exception:
        return "git_unavailable"
    if completed.returncode != 0:
        return "uncommitted_no_head"
    return completed.stdout.strip()


def safe_text(value):
    text = str(value)
    banned = [" causal ", " driver ", " mechanism "]
    lowered = f" {text.lower()} "
    if any(word in lowered for word in banned):
        return text + " [requires explicit cause-and-effect evidence]"
    return text


def render_analysis_report(args):
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    manifest = read_tsv(args.manifest)
    contrasts = read_tsv(args.contrasts)
    plan = read_tsv(args.dataset_plan)
    warnings = read_tsv(args.warnings)
    exclusions = read_tsv(args.exclusions)
    software = read_tsv(args.software) if getattr(args, "software", None) else []
    references = read_tsv(args.references) if getattr(args, "references", None) else []
    checksums = read_tsv(args.checksums) if getattr(args, "checksums", None) else []
    audit = read_tsv(args.audit) if getattr(args, "audit", None) else []
    candidate_scores = read_many_tsv(getattr(args, "candidate_scores", []))
    suggested_annotations = read_many_tsv(getattr(args, "suggested_annotations", []))
    test_status = read_tsv(args.test_status) if getattr(args, "test_status", None) else []
    sections = [
        "Project objective",
        "Input GSE",
        "Included and excluded samples",
        "Human-confirmed fields",
        "Dataset plan by analysis_id",
        "Each contrast",
        "Data entry",
        "Raw files and checksum",
        "Reference genome and GTF",
        "Software and versions",
        "Parameters",
        "QC",
        "Outlier samples",
        "Design formula",
        "Confounding checks",
        "Bulk results",
        "Single-cell results",
        "Pseudobulk results",
        "Meta-analysis",
        "Leave-one-dataset-out",
        "Bulk and single-cell joint results",
        "Automated review status",
        "Test and execution status",
        "Warnings",
        "Known limitations",
        "Complete reproduction command",
    ]
    body = [
        "<!doctype html><html><head><meta charset='utf-8'><title>Analysis report</title>",
        "<style>body{font-family:system-ui,sans-serif;margin:2rem;} table{border-collapse:collapse;width:100%;} td,th{border:1px solid #bbb;padding:.35rem;} th{background:#eef3f6;}</style>",
        "</head><body>",
        f"<h1>{html.escape(config['reporting']['title'])}</h1>",
        "<p>Conclusion language is constrained to association, enrichment, potential cellular source, replicated observation, or hypothesis unless explicit cause-and-effect evidence is supplied.</p>",
        "<p>Automated annotations and bulk/single-cell candidate genes are review queues, not final biological conclusions.</p>",
    ]
    for section in sections:
        body.append(f"<h2>{html.escape(section)}</h2>")
        if section == "Project objective":
            body.append(f"<p>{html.escape(config['project'].get('description', config['project'].get('name', 'RNA-seq mining')))}</p>")
        elif section == "Input GSE":
            body.append(table(manifest, ["dataset_id", "sample_id", "review_status", "include"]))
        elif section == "Included and excluded samples":
            body.append(table(exclusions, EXCLUSION_FIELDS))
        elif section == "Human-confirmed fields":
            body.append("<p>Only fields with reviewed authority status are treated as final user values. Suggestions are not facts.</p>")
            body.append(table(audit[:200], AUDIT_FIELDS))
        elif section == "Dataset plan by analysis_id":
            body.append(table(plan, ["analysis_id", "dataset_id", "include", "role", "analysis_strategy", "reference_dataset"]))
        elif section == "Each contrast":
            body.append(table(contrasts, ["analysis_id", "contrast_id", "data_scope", "numerator", "denominator", "enabled"]))
        elif section == "Raw files and checksum":
            body.append(table(checksums[:200], CHECKSUM_REPORT_FIELDS))
        elif section == "Reference genome and GTF":
            body.append(table(references, REFERENCE_FIELDS))
        elif section == "Software and versions":
            body.append(table(software, SOFTWARE_FIELDS))
        elif section == "Design formula":
            body.append(table(contrasts, ["analysis_id", "contrast_id", "data_scope", "design_formula", "paired"]))
        elif section == "Warnings":
            body.append(table(warnings, WARNING_FIELDS))
        elif section == "Bulk and single-cell joint results":
            body.append("<p>Candidate genes are hypothesis-generating integration evidence and require human review before biological interpretation.</p>")
            body.append(table(candidate_scores, CANDIDATE_SCORE_FIELDS))
        elif section == "Automated review status":
            body.append("<p>Automated cell-type suggestions and candidate gene scores are not reviewed authority unless their own review fields say so.</p>")
            body.append(table(suggested_annotations, SUGGESTED_ANNOTATION_FIELDS))
            body.append(table(candidate_scores, ["canonical_gene_id", "is_final_biological_conclusion", "required_action", "confidence", "limitations"]))
        elif section == "Test and execution status":
            if test_status:
                body.append(table(test_status, TEST_STATUS_FIELDS))
            else:
                body.append("<p>No machine-readable test status file was supplied to this report; no tests are reported as passed by the HTML report.</p>")
        elif section == "Known limitations":
            body.append("<ul><li>Unconfirmed authority fields are not interpreted as facts.</li><li>Automated cell-type labels and candidate genes require human review before final interpretation.</li><li>Single-GSE support, ambiguous gene mapping, failed validation, and opposite bulk/pseudobulk direction limit confidence.</li><li>Raw integer counts are required for DESeq2, and pseudobulk replicate units must remain subject/group/cell type.</li><li>Dominant cell type means potential cellular source only, not cause-and-effect source.</li><li>Deconvolution cannot by itself establish cell movement, disease origin, or pathway-of-action claims.</li></ul>")
        elif section == "Complete reproduction command":
            body.append("<pre>snakemake --snakefile workflow/Snakefile --directory . --configfile config/config.yaml --use-conda --cores &lt;N&gt;</pre>")
        else:
            body.append("<p>See accompanying TSV artifacts in results/reports and module-specific results directories.</p>")
    body.append("</body></html>")
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text("\n".join(body), encoding="utf-8")
    if getattr(args, "validation_report", None) and getattr(args, "validation_output", None):
        validation_output = Path(args.validation_output)
        validation_output.parent.mkdir(parents=True, exist_ok=True)
        if Path(args.validation_report).is_file():
            shutil.copyfile(args.validation_report, validation_output)
        else:
            validation_output.write_text(
                "<!doctype html><html><body><h1>Validation report unavailable</h1></body></html>\n",
                encoding="utf-8",
            )
    Path(args.marker).write_text("analysis_report=complete\n", encoding="utf-8")


def table(rows, fields):
    if not rows:
        return "<p>No confirmed records available.</p>"
    header = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
    body = []
    for row in rows:
        body.append("<tr>" + "".join(f"<td>{html.escape(safe_text(row.get(field, NA)))}</td>" for field in fields) + "</tr>")
    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_methods_report(args):
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    software = read_tsv(args.software) if getattr(args, "software", None) else []
    references = read_tsv(args.references) if getattr(args, "references", None) else []
    lines = [
        "# Methods",
        "",
        "This report records computational association, enrichment, potential cellular source, replicated observation, and hypothesis-generating analyses.",
        "Strong cause-and-effect wording is not used unless explicitly supported by reviewed input evidence.",
        "",
        "## Parameters",
        "```yaml",
        yaml.safe_dump(config, sort_keys=False),
        "```",
        "",
        "## Software Versions",
        "",
        markdown_table(software, SOFTWARE_FIELDS),
        "",
        "## Reference Versions",
        "",
        markdown_table(references, REFERENCE_FIELDS),
        "",
        "## Reproduction",
        "```powershell",
        "snakemake --snakefile workflow/Snakefile --directory . --configfile config/config.yaml --use-conda --cores <N>",
        "```",
    ]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text("\n".join(lines), encoding="utf-8")
    Path(args.marker).write_text("methods_report=complete\n", encoding="utf-8")


def markdown_table(rows, fields):
    header = "| " + " | ".join(fields) + " |"
    separator = "| " + " | ".join("---" for _ in fields) + " |"
    if not rows:
        return "\n".join([header, separator])
    body = [
        "| " + " | ".join(str(row.get(field, NA)).replace("|", "\\|") for field in fields) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def package_results(args):
    roots = [Path(path) for path in args.roots if Path(path).exists()]
    package_rows = []
    output = Path(args.output)
    output_resolved = output.resolve()
    excluded_outputs = {output_resolved, Path(args.manifest).resolve(), Path(args.marker).resolve()}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for root in roots:
            for path in iter_files(root):
                path_resolved = path.resolve()
                include = not is_large_raw(path) and path_resolved not in excluded_outputs
                if is_large_raw(path):
                    reason = "excluded_large_raw_sequence_file"
                elif path_resolved in excluded_outputs:
                    reason = "excluded_package_output"
                else:
                    reason = "included"
                stat = path.stat()
                package_rows.append(
                    {
                        "path": str(path),
                        "included": str(include).lower(),
                        "reason": reason,
                        "size_bytes": stat.st_size,
                        "sha256": sha256_file(path) if include else NA,
                    }
                )
                if include:
                    archive.add(path, arcname=str(path))
    write_tsv(args.manifest, PACKAGE_FIELDS, package_rows)
    Path(args.marker).write_text(f"package={output}\nfile_count={sum(row['included']=='true' for row in package_rows)}\n", encoding="utf-8")


def reproducibility_manifest(args):
    rows = []
    for artifact in args.artifacts:
        path = Path(artifact)
        rows.append(
            {
                "artifact": path.name,
                "path": str(path),
                "sha256": sha256_file(path),
                "description": "final reporting artifact",
            }
        )
    write_tsv(args.output, REPRO_FIELDS, rows)
    Path(args.marker).write_text(f"artifact_count={len(rows)}\n", encoding="utf-8")


def snapshot_parameters(args):
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.config, output)
    Path(args.marker).write_text("parameter_snapshot=complete\n", encoding="utf-8")


def write_test_status(args):
    write_tsv(args.output, TEST_STATUS_FIELDS, DEFAULT_TEST_STATUS_ROWS)
    Path(args.marker).write_text(
        f"test_status_records={len(DEFAULT_TEST_STATUS_ROWS)}\n"
        "result=not_run_by_workflow\n",
        encoding="utf-8",
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Final reporting utilities.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("collect_provenance")
    p.add_argument("--roots", nargs="+", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("collect_software_versions")
    p.add_argument("--output", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("collect_reference_metadata")
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("build_audit_trail")
    p.add_argument("--authority-files", nargs="+", required=True)
    p.add_argument("--issue-files", nargs="*", default=[])
    p.add_argument("--audit", required=True)
    p.add_argument("--exclusions", required=True)
    p.add_argument("--warnings", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("render_analysis_report")
    p.add_argument("--config", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--contrasts", required=True)
    p.add_argument("--dataset-plan", required=True)
    p.add_argument("--warnings", required=True)
    p.add_argument("--exclusions", required=True)
    p.add_argument("--software")
    p.add_argument("--references")
    p.add_argument("--checksums")
    p.add_argument("--audit")
    p.add_argument("--candidate-scores", nargs="*", default=[])
    p.add_argument("--suggested-annotations", nargs="*", default=[])
    p.add_argument("--test-status")
    p.add_argument("--validation-report")
    p.add_argument("--validation-output")
    p.add_argument("--output", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("render_methods_report")
    p.add_argument("--config", required=True)
    p.add_argument("--software")
    p.add_argument("--references")
    p.add_argument("--output", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("package_results")
    p.add_argument("--roots", nargs="+", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("reproducibility_manifest")
    p.add_argument("--artifacts", nargs="+", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("snapshot_parameters")
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--marker", required=True)
    p = sub.add_parser("write_test_status")
    p.add_argument("--output", required=True)
    p.add_argument("--marker", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    globals()[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
