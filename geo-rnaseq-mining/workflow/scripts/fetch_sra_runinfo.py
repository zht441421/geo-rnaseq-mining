#!/usr/bin/env python3

import argparse
import csv
import io
import json
import os
import re
import time
import urllib.parse
from pathlib import Path

from metadata_io import (
    NA,
    event,
    fetch_bytes,
    read_tsv,
    utc_now,
    write_events,
    write_tsv,
)


RUNINFO_URL = "https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/runinfo"
FIELDS = [
    "gse_accession",
    "gsm_accession",
    "srx_accession",
    "srr_accession",
    "library_strategy",
    "library_source",
    "library_layout",
    "organism",
    "runinfo_source_url",
    "raw_runinfo_json",
    "fetched_at_utc",
    "cache_hit",
]


def extract_srx_accessions(sample):
    values = sample.get("srx_accessions", "")
    accessions = set(re.findall(r"SRX\d+", values or ""))
    accessions.update(re.findall(r"SRX\d+", sample.get("relation_raw", "") or ""))
    return sorted(accessions)


def parse_runinfo(content):
    text = content.decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def build_url(srx, email="", api_key=""):
    query = {"acc": srx}
    if email:
        query["email"] = email
    if api_key:
        query["api_key"] = api_key
    return f"{RUNINFO_URL}?{urllib.parse.urlencode(query)}"


def collect_runinfo(
    samples,
    cache_dir,
    retries,
    retry_delay,
    timeout,
    request_interval,
    email,
    api_key,
    user_agent,
    fetcher=fetch_bytes,
):
    rows = []
    events = []
    cache_root = Path(cache_dir)
    for sample in samples:
        gsm = sample.get("gsm_accession", NA)
        gse = sample.get("gse_accession", NA)
        srx_accessions = extract_srx_accessions(sample)
        if not srx_accessions:
            rows.append(
                {
                    "gse_accession": gse,
                    "gsm_accession": gsm,
                    "srx_accession": NA,
                    "srr_accession": NA,
                    "library_strategy": NA,
                    "library_source": NA,
                    "library_layout": NA,
                    "organism": sample.get("organism", NA),
                    "runinfo_source_url": NA,
                    "raw_runinfo_json": NA,
                    "fetched_at_utc": utc_now(),
                    "cache_hit": "false",
                }
            )
            events.append(
                event(
                    "fetch_sra_runinfo",
                    "WARNING",
                    "NO_SRX_RELATION",
                    f"No SRX accession was present in the raw GEO relation fields for {gsm}.",
                    "Review the GEO record manually; do not infer a subject or run mapping.",
                    accession=gsm,
                )
            )
            continue

        for srx in srx_accessions:
            url = build_url(srx, email, api_key)
            try:
                content, cache_hit, attempt = fetcher(
                    url,
                    cache_root / f"{srx}.csv",
                    retries,
                    retry_delay,
                    timeout,
                    headers={"User-Agent": user_agent},
                )
                if not cache_hit and request_interval > 0:
                    time.sleep(request_interval)
                run_rows = parse_runinfo(content)
                if not run_rows:
                    raise ValueError("NCBI RunInfo returned no rows")
                for run_row in run_rows:
                    rows.append(
                        {
                            "gse_accession": gse,
                            "gsm_accession": gsm,
                            "srx_accession": run_row.get("Experiment") or srx,
                            "srr_accession": run_row.get("Run") or NA,
                            "library_strategy": run_row.get("LibraryStrategy") or NA,
                            "library_source": run_row.get("LibrarySource") or NA,
                            "library_layout": run_row.get("LibraryLayout") or NA,
                            "organism": run_row.get("ScientificName")
                            or sample.get("organism")
                            or NA,
                            "runinfo_source_url": url,
                            "raw_runinfo_json": json.dumps(
                                run_row, ensure_ascii=False, sort_keys=True
                            ),
                            "fetched_at_utc": utc_now(),
                            "cache_hit": str(cache_hit).lower(),
                        }
                    )
                events.append(
                    event(
                        "fetch_sra_runinfo",
                        "INFO",
                        "SRA_RUNINFO_FETCH_COMPLETE",
                        f"Retained {len(run_rows)} RunInfo rows for {gsm}/{srx}.",
                        "No action required.",
                        accession=srx,
                        attempt=attempt,
                        cache_hit=cache_hit,
                    )
                )
            except Exception as error:
                rows.append(
                    {
                        "gse_accession": gse,
                        "gsm_accession": gsm,
                        "srx_accession": srx,
                        "srr_accession": NA,
                        "library_strategy": NA,
                        "library_source": NA,
                        "library_layout": NA,
                        "organism": sample.get("organism", NA),
                        "runinfo_source_url": url,
                        "raw_runinfo_json": NA,
                        "fetched_at_utc": utc_now(),
                        "cache_hit": "false",
                    }
                )
                events.append(
                    event(
                        "fetch_sra_runinfo",
                        "ERROR",
                        "SRA_RUNINFO_FETCH_FAILED",
                        error,
                        "Check NCBI availability and the SRX accession, then rerun; cached successful queries are preserved.",
                        accession=srx,
                    )
                )
    return rows, events


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch NCBI SRA RunInfo while preserving all GSM-SRX-SRR rows."
    )
    parser.add_argument("--samples", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--event-log", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-delay", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--request-interval", type=float, default=0.34)
    parser.add_argument("--email", default="")
    parser.add_argument("--api-key-env", default="NCBI_API_KEY")
    parser.add_argument("--user-agent", default="geo-rnaseq-mining/0.1")
    return parser.parse_args()


def main():
    args = parse_args()
    rows, events = collect_runinfo(
        read_tsv(args.samples),
        args.cache_dir,
        args.retries,
        args.retry_delay,
        args.timeout,
        args.request_interval,
        args.email,
        os.environ.get(args.api_key_env, ""),
        args.user_agent,
    )
    write_tsv(args.output, FIELDS, rows)
    write_events(args.event_log, events)


if __name__ == "__main__":
    main()
