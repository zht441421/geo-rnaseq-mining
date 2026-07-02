#!/usr/bin/env python3

import argparse
from collections import defaultdict

from data_entry_common import NA, is_missing, read_tsv, write_tsv


FIELDS = [
    "dataset_id",
    "sample_id",
    "data_type_confirmed",
    "gse_id",
    "gsm_id",
    "srr_id",
    "file_name",
    "url",
    "size_bytes",
    "file_type",
    "source_scope",
    "inventory_status",
    "requires_manual_review",
]


def inventory_supplementary(manifest, supplementary):
    by_gsm = defaultdict(list)
    by_gse = defaultdict(list)
    for row in manifest:
        by_gsm[row.get("gsm_id", NA)].append(row)
        by_gse[row.get("gse_id", NA)].append(row)
    output = []
    for source in supplementary:
        gse = source.get("gse_accession", NA)
        gsm = source.get("gsm_accession", NA)
        matched = by_gsm.get(gsm, []) if not is_missing(gsm) else by_gse.get(gse, [])
        if not matched:
            matched = [
                {
                    "dataset_id": NA,
                    "sample_id": NA,
                    "data_type": NA,
                    "gse_id": gse,
                    "gsm_id": gsm,
                    "srr_id": NA,
                }
            ]
        for sample in matched:
            output.append(
                {
                    "dataset_id": sample.get("dataset_id", NA),
                    "sample_id": sample.get("sample_id", NA),
                    "data_type_confirmed": sample.get("data_type", NA),
                    "gse_id": sample.get("gse_id", gse),
                    "gsm_id": sample.get("gsm_id", gsm),
                    "srr_id": sample.get("srr_id", NA),
                    "file_name": source.get("supplementary_file_name", NA),
                    "url": source.get("supplementary_url", NA),
                    "size_bytes": source.get("size_bytes", NA),
                    "file_type": source.get("file_type", NA),
                    "source_scope": source.get("source_scope", NA),
                    "inventory_status": "mapped"
                    if sample.get("sample_id", NA) != NA
                    else "unmapped",
                    "requires_manual_review": "true",
                }
            )
    return output


def parse_args():
    parser = argparse.ArgumentParser(
        description="Map GEO supplementary references to reviewed samples."
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--supplementary", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    rows = inventory_supplementary(
        read_tsv(args.manifest), read_tsv(args.supplementary)
    )
    write_tsv(args.output, FIELDS, rows)
    print(f"Inventoried {len(rows)} supplementary file/sample references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
