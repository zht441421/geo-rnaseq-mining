#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path

from metadata_io import event, write_events, write_tsv


SERIES_COLUMNS = [
    "gse_accession",
    "title",
    "summary",
    "overall_design",
    "submission_date",
    "last_update_date",
    "pubmed_id",
    "organism",
    "raw_metadata_json",
    "fetched_at_utc",
    "cache_hit",
]
SAMPLE_COLUMNS = [
    "gse_accession",
    "gsm_accession",
    "title",
    "source_name",
    "organism",
    "platform",
    "characteristics_ch1_raw",
    "relation_raw",
    "srx_accessions",
    "raw_metadata_json",
    "fetched_at_utc",
    "cache_hit",
]
PLATFORM_COLUMNS = [
    "gse_accession",
    "gpl_accession",
    "title",
    "technology",
    "organism",
    "manufacturer",
    "raw_metadata_json",
    "fetched_at_utc",
    "cache_hit",
]


def configured_accessions(value):
    return [item.strip() for item in value.split(",") if item.strip()]


def write_header_only(args):
    write_tsv(args.series_output, SERIES_COLUMNS, [])
    write_tsv(args.samples_output, SAMPLE_COLUMNS, [])
    write_tsv(args.platforms_output, PLATFORM_COLUMNS, [])
    write_events(
        args.event_log,
        [
            event(
                "fetch_geo_metadata",
                "WARNING",
                "NO_ACCESSIONS",
                "No GSE accessions were configured; header-only raw metadata files were created.",
                "Add one or more GSE accessions under geo.accessions in config/config.yaml.",
            )
        ],
    )


def run_geoquery(args):
    command = [
        sys.executable,
        "workflow/scripts/run_rscript.py",
        "workflow/scripts/fetch_geo_metadata.R",
        "--accessions",
        args.accessions,
        "--series-output",
        args.series_output,
        "--samples-output",
        args.samples_output,
        "--platforms-output",
        args.platforms_output,
        "--event-log",
        args.event_log,
        "--cache-dir",
        args.cache_dir,
        "--retries",
        str(args.retries),
        "--retry-delay",
        str(args.retry_delay),
    ]
    return subprocess.run(command, check=False).returncode


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch GEO metadata, using GEOquery only when accessions are configured."
    )
    parser.add_argument("--accessions", nargs="?", default="", const="")
    parser.add_argument("--series-output", required=True, dest="series_output")
    parser.add_argument("--samples-output", required=True, dest="samples_output")
    parser.add_argument("--platforms-output", required=True, dest="platforms_output")
    parser.add_argument("--event-log", required=True, dest="event_log")
    parser.add_argument("--cache-dir", required=True, dest="cache_dir")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-delay", type=float, default=5, dest="retry_delay")
    return parser.parse_args()


def main():
    args = parse_args()
    Path(args.cache_dir).mkdir(parents=True, exist_ok=True)
    if not configured_accessions(args.accessions):
        write_header_only(args)
        print("No GSE accessions configured; wrote header-only GEO metadata files.")
        return 0
    return run_geoquery(args)


if __name__ == "__main__":
    raise SystemExit(main())
