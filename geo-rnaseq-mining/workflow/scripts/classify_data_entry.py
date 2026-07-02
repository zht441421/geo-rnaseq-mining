#!/usr/bin/env python3

import argparse
from collections import defaultdict
from pathlib import Path

from data_entry_common import (
    INVENTORY_FIELDS,
    NA,
    classify_local_file,
    classify_remote_candidate,
    confirmed_family,
    is_missing,
    read_tsv,
    write_tsv,
)


def resolve(value, project_root):
    path = Path(value)
    return path if path.is_absolute() else Path(project_root) / path


def classify_entries(manifest, supplementary_inventory, project_root):
    output = []
    matrix_samples = defaultdict(set)
    for row in manifest:
        if not is_missing(row.get("matrix_path")):
            matrix_samples[str(resolve(row["matrix_path"], project_root))].add(
                row.get("sample_id", NA)
            )
    for row in manifest:
        dataset_id = row.get("dataset_id", NA)
        sample_id = row.get("sample_id", NA)
        data_type = row.get("data_type", NA)
        matrix_path = row.get("matrix_path", NA)
        r1 = row.get("fastq_r1", NA)
        r2 = row.get("fastq_r2", NA)
        layout = row.get("library_layout", NA).upper()
        if not is_missing(matrix_path):
            resolved = resolve(matrix_path, project_root)
            classified = classify_local_file(
                dataset_id,
                sample_id,
                data_type,
                resolved,
                matrix_samples[str(resolved)],
                source_type="reviewed_matrix_path",
            )
            output.append({key: classified.get(key, NA) for key in INVENTORY_FIELDS})
        fastq_values = [value for value in (r1, r2) if not is_missing(value)]
        paired_status = (
            "complete"
            if layout == "PAIRED" and len(fastq_values) == 2
            else "incomplete"
            if layout == "PAIRED"
            else "single"
            if layout == "SINGLE"
            else "unknown"
        )
        for source_id, value in (("R1", r1), ("R2", r2)):
            if is_missing(value):
                continue
            classified = classify_local_file(
                dataset_id,
                sample_id,
                data_type,
                resolve(value, project_root),
                source_type="reviewed_fastq_path",
                source_id=source_id,
            )
            classified["paired_end_status"] = paired_status
            output.append({key: classified.get(key, NA) for key in INVENTORY_FIELDS})
        srr_id = row.get("srr_id", NA)
        if not is_missing(srr_id):
            family = confirmed_family(data_type)
            output.append(
                {
                    "dataset_id": dataset_id,
                    "sample_id": sample_id,
                    "data_type_confirmed": data_type,
                    "entry_point": f"{family}_fastq_candidate",
                    "file_path": NA,
                    "file_format": "sra_remote",
                    "file_size": NA,
                    "checksum": NA,
                    "count_type": NA,
                    "is_integer": NA,
                    "likely_normalized": NA,
                    "paired_end_status": "expected_paired"
                    if layout == "PAIRED"
                    else "expected_single"
                    if layout == "SINGLE"
                    else "unknown",
                    "recommended_pipeline": "sra_prefetch_then_fasterq",
                    "technical_consistency": "unverified",
                    "requires_manual_review": "true",
                    "source_type": "SRA",
                    "source_url": NA,
                    "source_id": srr_id,
                    "has_negative": NA,
                    "likely_log_transformed": NA,
                    "duplicate_gene_ids": NA,
                    "sample_columns_match": NA,
                    "status": "remote_candidate",
                    "message": "SRA run is reviewed but has not yet been verified locally.",
                }
            )

    for row in supplementary_inventory:
        classified = classify_remote_candidate(
            {
                "file_name": row.get("file_name", NA),
                "url": row.get("url", NA),
                "file_type": row.get("file_type", NA),
            }
        )
        output.append(
            {
                "dataset_id": row.get("dataset_id", NA),
                "sample_id": row.get("sample_id", NA),
                "data_type_confirmed": row.get("data_type_confirmed", NA),
                "entry_point": classified["entry_point"],
                "file_path": NA,
                "file_format": classified["file_format"],
                "file_size": row.get("size_bytes", NA),
                "checksum": NA,
                "count_type": classified["count_type"],
                "is_integer": NA,
                "likely_normalized": NA,
                "paired_end_status": NA,
                "recommended_pipeline": "download_then_content_classification",
                "technical_consistency": classified["technical_consistency"],
                "requires_manual_review": "true",
                "source_type": "GEO_supplementary",
                "source_url": row.get("url", NA),
                "source_id": row.get("file_name", NA),
                "has_negative": NA,
                "likely_log_transformed": NA,
                "duplicate_gene_ids": NA,
                "sample_columns_match": NA,
                "status": "remote_candidate",
                "message": "Hints only: "
                + ",".join(classified.get("candidate_hints", []))
                + ". Content was not classified from extension alone.",
            }
        )
    return output


def parse_args():
    parser = argparse.ArgumentParser(
        description="Classify reviewed technical data entry points."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--supplementary-inventory", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = classify_entries(
        read_tsv(args.manifest),
        read_tsv(args.supplementary_inventory),
        Path(args.project_root).resolve(),
    )
    write_tsv(args.output, INVENTORY_FIELDS, rows)
    print(f"Classified {len(rows)} technical entry candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
