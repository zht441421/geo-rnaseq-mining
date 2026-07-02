#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from data_entry_common import NA, read_tsv, sha256_file, write_tsv
from sra_pipeline import fastq_record_count


FIELDS = [
    "dataset_id",
    "sample_id",
    "data_type_confirmed",
    "source_type",
    "source_id",
    "source_url",
    "file_path",
    "file_size",
    "checksum",
    "status",
    "paired_end_status",
    "message",
]


def verify_file(path, checksum):
    file_path = Path(path)
    if not file_path.is_file():
        return False, "File is missing."
    observed = sha256_file(file_path)
    if checksum not in ("", NA) and observed != checksum:
        return False, f"Checksum mismatch: expected {checksum}, observed {observed}."
    if str(file_path).lower().endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
        try:
            fastq_record_count(file_path)
        except Exception as error:
            return False, f"FASTQ integrity failure: {error}"
    return True, "File exists, checksum matches, and format integrity passed."


def verify_downloads(manifest, supplementary_status, sra_status_paths):
    output = []
    for row in supplementary_status:
        status = row.get("status", "unknown")
        message = row.get("message", "")
        if status == "verified":
            valid, message = verify_file(row.get("file_path"), row.get("checksum"))
            status = "verified" if valid else "error"
        output.append(
            {
                **{field: row.get(field, NA) for field in FIELDS},
                "status": status,
                "paired_end_status": NA,
                "message": message,
            }
        )
    manifest_by_srr = {
        row.get("srr_id"): row
        for row in manifest
        if row.get("srr_id") not in ("", NA)
    }
    for status_path in sra_status_paths:
        status_data = json.loads(Path(status_path).read_text(encoding="utf-8"))
        srr = status_data.get("srr", NA)
        sample = manifest_by_srr.get(srr, {})
        files = status_data.get("files", [])
        if not files:
            output.append(
                {
                    "dataset_id": sample.get("dataset_id", NA),
                    "sample_id": sample.get("sample_id", NA),
                    "data_type_confirmed": sample.get("data_type", NA),
                    "source_type": "SRA_FASTQ",
                    "source_id": srr,
                    "source_url": NA,
                    "file_path": NA,
                    "file_size": NA,
                    "checksum": NA,
                    "status": status_data.get("status", "unknown"),
                    "paired_end_status": status_data.get(
                        "paired_end_status", NA
                    ),
                    "message": status_data.get(
                        "error", status_data.get("reason", "No FASTQ files.")
                    ),
                }
            )
            continue
        for item in files:
            valid, message = verify_file(item["path"], item.get("checksum", NA))
            output.append(
                {
                    "dataset_id": sample.get("dataset_id", NA),
                    "sample_id": sample.get("sample_id", NA),
                    "data_type_confirmed": sample.get("data_type", NA),
                    "source_type": "SRA_FASTQ",
                    "source_id": srr,
                    "source_url": NA,
                    "file_path": item["path"],
                    "file_size": item.get("size", NA),
                    "checksum": item.get("checksum", NA),
                    "status": "verified" if valid else "error",
                    "paired_end_status": status_data.get(
                        "paired_end_status", NA
                    ),
                    "message": message,
                }
            )
    return output


def parse_args():
    parser = argparse.ArgumentParser(description="Verify downloaded supplementary and SRA files.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--supplementary-status", required=True)
    parser.add_argument("--sra-status", nargs="*", default=[])
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = verify_downloads(
        read_tsv(args.manifest),
        read_tsv(args.supplementary_status),
        args.sra_status,
    )
    write_tsv(args.output, FIELDS, rows)
    print(f"Verified {len(rows)} downloaded file records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
