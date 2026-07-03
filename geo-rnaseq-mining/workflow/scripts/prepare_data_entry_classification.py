#!/usr/bin/env python3

import argparse
import json
from collections import defaultdict
from pathlib import Path

from metadata_io import NA, read_tsv, write_tsv


FIELDS = [
    "dataset_id",
    "gse_id",
    "data_type_suggested",
    "entry_point_suggested",
    "confidence",
    "evidence",
    "requires_manual_review",
    "recommended_pipeline",
]


def lowered(value):
    return str(value or "").lower()


def evidence_json(items):
    return json.dumps(items, ensure_ascii=False, sort_keys=True)


def add_row(rows, seen, dataset_id, data_type, entry_point, confidence, evidence, pipeline):
    key = (dataset_id, data_type, entry_point, evidence_json(evidence))
    if key in seen:
        return
    seen.add(key)
    rows.append(
        {
            "dataset_id": dataset_id,
            "gse_id": dataset_id,
            "data_type_suggested": data_type,
            "entry_point_suggested": entry_point,
            "confidence": confidence,
            "evidence": evidence_json(evidence),
            "requires_manual_review": "true",
            "recommended_pipeline": pipeline,
        }
    )


def classify_runinfo(rows, seen, runinfo):
    for run in runinfo:
        dataset_id = run.get("gse_accession") or NA
        strategy = lowered(run.get("library_strategy"))
        source = lowered(run.get("library_source"))
        layout = run.get("library_layout") or NA
        srr = run.get("srr_accession") or NA
        if srr == NA:
            continue
        if "rna-seq" in strategy:
            add_row(
                rows,
                seen,
                dataset_id,
                "bulk_RNA-seq_candidate",
                "bulk_fastq",
                "medium",
                {
                    "source": "SRA RunInfo",
                    "srr_accession": srr,
                    "library_strategy": run.get("library_strategy", NA),
                    "library_source": run.get("library_source", NA),
                    "library_layout": layout,
                    "note": "RunInfo supports an RNA-seq FASTQ candidate but does not define final data_type.",
                },
                "sra_prefetch_then_fasterq",
            )


def classify_supplementary(rows, seen, supplementary):
    by_dataset = defaultdict(list)
    for item in supplementary:
        dataset_id = item.get("gse_accession") or NA
        by_dataset[dataset_id].append(item)

    for dataset_id, items in by_dataset.items():
        names = " ".join(
            lowered(item.get("supplementary_file_name"))
            + " "
            + lowered(item.get("supplementary_url"))
            + " "
            + lowered(item.get("file_type"))
            for item in items
        )
        evidence = {
            "source": "GEO supplementary file index",
            "files": [
                item.get("supplementary_file_name", NA)
                for item in items
                if item.get("supplementary_file_name")
            ],
            "note": "Remote file names are hints only; content must be reviewed or verified after download.",
        }
        has_10x_trio = all(
            token in names for token in ("matrix.mtx", "barcodes.tsv")
        ) and ("features.tsv" in names or "genes.tsv" in names)
        if has_10x_trio or "filtered_feature_bc_matrix" in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "single_cell_candidate",
                "scrna_10x_mtx",
                "medium",
                evidence,
                "download_then_10x_content_validation",
            )
        if ".h5ad" in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "single_cell_candidate",
                "scrna_h5ad",
                "low",
                evidence,
                "download_then_h5ad_counts_layer_review",
            )
        if ".rds" in names or ".rdata" in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "single_cell_candidate",
                "scrna_rds",
                "low",
                evidence,
                "download_then_rds_conversion_review",
            )
        if ".h5" in names and ".h5ad" not in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "single_cell_candidate",
                "scrna_10x_h5",
                "low",
                evidence,
                "download_then_10x_h5_content_validation",
            )
        if "fastq" in names or ".fq" in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "sequencing_candidate",
                "bulk_fastq",
                "low",
                evidence,
                "manual_modality_review_before_fastq_pipeline",
            )
        if "tpm" in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "bulk_expression_candidate",
                "bulk_tpm",
                "low",
                evidence,
                "exploratory_only_no_deseq2",
            )
        if "fpkm" in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "bulk_expression_candidate",
                "bulk_fpkm",
                "low",
                evidence,
                "exploratory_only_no_deseq2",
            )
        if "log" in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "bulk_expression_candidate",
                "bulk_log_expression",
                "low",
                evidence,
                "exploratory_only_no_deseq2",
            )
        if "count" in names and "tpm" not in names and "fpkm" not in names:
            add_row(
                rows,
                seen,
                dataset_id,
                "bulk_counts_candidate",
                "bulk_raw_counts",
                "low",
                evidence,
                "download_then_raw_integer_count_validation",
            )


def classify(samples, runinfo, supplementary):
    rows = []
    seen = set()
    classify_runinfo(rows, seen, runinfo)
    classify_supplementary(rows, seen, supplementary)
    known_datasets = {
        sample.get("gse_accession") or NA
        for sample in samples
    } | {
        row.get("gse_accession") or NA
        for row in runinfo
    } | {
        row.get("gse_accession") or NA
        for row in supplementary
    }
    for dataset_id in sorted(known_datasets):
        if dataset_id == NA:
            continue
        if not any(row["dataset_id"] == dataset_id for row in rows):
            add_row(
                rows,
                seen,
                dataset_id,
                "unknown",
                "ambiguous",
                "low",
                {
                    "source": "GEO/SRA metadata",
                    "note": "No sufficient data entry evidence was detected.",
                },
                "manual_entry_selection_required",
            )
    return rows


def parse_args():
    parser = argparse.ArgumentParser(
        description="Classify suggested data entry points without making formal decisions."
    )
    parser.add_argument("--samples", required=True)
    parser.add_argument("--runinfo", required=True)
    parser.add_argument("--supplementary", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = classify(
        read_tsv(args.samples),
        read_tsv(args.runinfo),
        read_tsv(args.supplementary),
    )
    write_tsv(args.output, FIELDS, rows)
    print(f"Prepared {len(rows)} suggested data entry classifications.")


if __name__ == "__main__":
    main()
