#!/usr/bin/env python3

import argparse
from pathlib import Path

from data_entry_common import (
    INVENTORY_FIELDS,
    NA,
    classify_local_file,
    read_tsv,
    write_tsv,
)


def build_inventory(classified, verified):
    output = [row.copy() for row in classified]
    for row in verified:
        if row.get("status") == "verified" and row.get("file_path") not in ("", NA):
            classified_file = classify_local_file(
                row.get("dataset_id", NA),
                row.get("sample_id", NA),
                row.get("data_type_confirmed", NA),
                Path(row["file_path"]),
                expected_sample_ids=[row.get("sample_id")]
                if row.get("source_type") == "GEO_supplementary"
                else None,
                source_type=row.get("source_type", NA),
                source_url=row.get("source_url", NA),
                source_id=row.get("source_id", NA),
            )
            classified_file["paired_end_status"] = row.get(
                "paired_end_status", NA
            )
            classified_file["status"] = "verified"
            classified_file["message"] = (
                row.get("message", "") + " " + classified_file.get("message", "")
            ).strip()
            output.append(
                {
                    field: classified_file.get(field, NA)
                    for field in INVENTORY_FIELDS
                }
            )
        elif row.get("status") == "error":
            output.append(
                {
                    "dataset_id": row.get("dataset_id", NA),
                    "sample_id": row.get("sample_id", NA),
                    "data_type_confirmed": row.get("data_type_confirmed", NA),
                    "entry_point": "download_error",
                    "file_path": row.get("file_path", NA),
                    "file_format": "unknown",
                    "file_size": row.get("file_size", NA),
                    "checksum": row.get("checksum", NA),
                    "count_type": NA,
                    "is_integer": NA,
                    "likely_normalized": NA,
                    "paired_end_status": row.get("paired_end_status", NA),
                    "recommended_pipeline": "manual_download_repair_required",
                    "technical_consistency": "error:download_verification_failed",
                    "requires_manual_review": "true",
                    "source_type": row.get("source_type", NA),
                    "source_url": row.get("source_url", NA),
                    "source_id": row.get("source_id", NA),
                    "has_negative": NA,
                    "likely_log_transformed": NA,
                    "duplicate_gene_ids": NA,
                    "sample_columns_match": NA,
                    "status": "error",
                    "message": row.get("message", "Download verification failed."),
                }
            )
    output.sort(
        key=lambda row: (
            row.get("dataset_id", NA),
            row.get("sample_id", NA),
            row.get("source_type", NA),
            row.get("file_path", NA),
        )
    )
    return output


def parse_args():
    parser = argparse.ArgumentParser(description="Build final technical data inventory.")
    parser.add_argument("--classified", required=True)
    parser.add_argument("--verified", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = build_inventory(read_tsv(args.classified), read_tsv(args.verified))
    write_tsv(args.output, INVENTORY_FIELDS, rows)
    print(f"Wrote {len(rows)} final data inventory records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
