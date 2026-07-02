#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

import yaml

from bulk_common import active_bulk_rows, bulk_entry_branch
from preanalysis_common import read_tsv, write_tsv


METRIC_FIELDS = [
    "dataset_id",
    "sample_id",
    "entry_branch",
    "read_count",
    "mapped_read_count",
    "mapping_rate",
    "mapping_metric",
    "library_layout",
    "strandedness",
    "quantification_method",
    "reference_genome",
    "transcriptome",
    "annotation_release",
    "gene_id_space",
    "software_version",
    "quantification_log",
]


def read_salmon_metrics(root, sample_id):
    quant_dir = Path(root) / "quantification" / "salmon" / sample_id
    metadata_path = quant_dir / "aux_info" / "meta_info.json"
    if not metadata_path.is_file():
        return {}
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    processed = payload.get("num_processed")
    mapped = payload.get("num_mapped")
    rate = payload.get("percent_mapped")
    if rate is None and processed:
        rate = 100 * float(mapped or 0) / float(processed)
    return {
        "read_count": processed,
        "mapped_read_count": mapped,
        "mapping_rate": rate,
        "mapping_metric": "mapping_equivalent_rate",
        "software_version": payload.get("salmon_version", "NA"),
        "quantification_log": str(quant_dir / "logs" / "salmon_quant.log"),
    }


def read_star_metrics(root, sample_id):
    alignment_dir = Path(root) / "alignment" / "star" / sample_id
    log_path = alignment_dir / "Log.final.out"
    values = {}
    if log_path.is_file():
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "|" not in line:
                continue
            key, value = (part.strip() for part in line.split("|", 1))
            values[key] = value
    read_count = values.get("Number of input reads", "NA")
    unique_rate = values.get("Uniquely mapped reads %", "NA")
    multi_rate = values.get("% of reads mapped to multiple loci", "0%")
    try:
        mapping_rate = float(unique_rate.rstrip("%")) + float(
            multi_rate.rstrip("%")
        )
    except (AttributeError, ValueError):
        mapping_rate = "NA"
    version = "NA"
    star_log = alignment_dir / "Log.out"
    if star_log.is_file():
        match = re.search(
            r"STAR version[=:\s]+([^\s]+)",
            star_log.read_text(encoding="utf-8", errors="replace"),
        )
        if match:
            version = match.group(1)
    return {
        "read_count": read_count,
        "mapped_read_count": "NA",
        "mapping_rate": mapping_rate,
        "mapping_metric": "genome_mapping_rate",
        "software_version": version,
        "quantification_log": str(log_path),
    }


def collect_metrics(config, manifest, dataset_id, bulk_root):
    rows = active_bulk_rows(manifest, dataset_id)
    branch = bulk_entry_branch(rows)
    bulk = config["bulk"]
    references = config["references"]
    method = bulk["quantification_method"] if branch == "fastq" else "provided_matrix"
    output = []
    for row in rows:
        if branch == "fastq" and method == "salmon_tximport":
            metrics = read_salmon_metrics(bulk_root, row["sample_id"])
        elif branch == "fastq" and method == "star_featurecounts":
            metrics = read_star_metrics(bulk_root, row["sample_id"])
        else:
            metrics = {}
        output.append(
            {
                "dataset_id": dataset_id,
                "sample_id": row["sample_id"],
                "entry_branch": branch,
                "read_count": metrics.get("read_count", "NA"),
                "mapped_read_count": metrics.get("mapped_read_count", "NA"),
                "mapping_rate": metrics.get("mapping_rate", "NA"),
                "mapping_metric": metrics.get("mapping_metric", "not_applicable"),
                "library_layout": row.get("library_layout", "NA"),
                "strandedness": bulk.get("strandedness", "NA"),
                "quantification_method": method,
                "reference_genome": references.get("genome_build", "NA"),
                "transcriptome": references.get("transcriptome_fasta", "NA"),
                "annotation_release": references.get("annotation_release", "NA"),
                "gene_id_space": references.get("gene_id_space", "NA"),
                "software_version": metrics.get("software_version", "NA"),
                "quantification_log": metrics.get("quantification_log", "NA"),
            }
        )
    return output


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect per-sample bulk read and quantification provenance."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--bulk-root", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    rows = collect_metrics(
        config,
        read_tsv(args.manifest),
        args.dataset_id,
        args.bulk_root,
    )
    write_tsv(args.output, METRIC_FIELDS, rows)
    print(f"Wrote {len(rows)} bulk quantification metric records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
