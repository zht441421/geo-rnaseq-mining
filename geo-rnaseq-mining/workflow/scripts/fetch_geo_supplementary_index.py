#!/usr/bin/env python3

import argparse
import json
import mimetypes
import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path

from metadata_io import (
    NA,
    cache_key,
    event,
    load_raw_json,
    read_tsv,
    utc_now,
    write_events,
    write_tsv,
)


FIELDS = [
    "gse_accession",
    "gsm_accession",
    "source_scope",
    "raw_metadata_key",
    "supplementary_file_name",
    "supplementary_url",
    "size_bytes",
    "file_type",
    "fetched_at_utc",
]


def iter_values(value):
    if isinstance(value, list):
        for item in value:
            yield from iter_values(item)
    elif value not in (None, "", NA):
        yield str(value)


def supplementary_values(metadata):
    if isinstance(metadata, dict):
        items = metadata.items()
    else:
        items = (
            (entry.get("field_name", NA), entry.get("values"))
            for entry in metadata
            if isinstance(entry, dict)
        )
    for key, value in items:
        if key.lower().startswith("supplementary_file"):
            for item in iter_values(value):
                yield key, item


def remote_size(
    url,
    timeout,
    user_agent,
    retries,
    retry_delay,
    opener=urllib.request.urlopen,
):
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": user_agent}, method="HEAD"
            )
            with opener(request, timeout=timeout) as response:
                value = response.headers.get("Content-Length")
            return value or NA
        except Exception as error:
            last_error = error
            if attempt < retries:
                time.sleep(retry_delay)
    raise RuntimeError(
        f"HEAD request failed after {retries} attempts for {url}: {last_error}"
    )


def collect_entries(
    rows,
    scope,
    use_head,
    cache_dir,
    timeout,
    user_agent,
    retries,
    retry_delay,
    opener,
):
    entries = []
    events = []
    cache_root = Path(cache_dir)
    for row in rows:
        accession = row.get("gsm_accession", NA)
        gse_accession = row.get("gse_accession", NA)
        try:
            metadata = load_raw_json(row.get("raw_metadata_json", NA))
        except (ValueError, TypeError) as error:
            events.append(
                event(
                    "fetch_geo_supplementary_index",
                    "ERROR",
                    "INVALID_RAW_METADATA_JSON",
                    error,
                    "Inspect the cached GEO record and rerun fetch_geo_metadata.",
                    accession=accession,
                )
            )
            continue
        for key, url in supplementary_values(metadata):
            parsed = urllib.parse.urlparse(url)
            filename = Path(urllib.parse.unquote(parsed.path)).name or NA
            guessed_type = mimetypes.guess_type(filename)[0]
            suffix = "".join(Path(filename).suffixes)
            file_type = guessed_type or suffix.lstrip(".") or NA
            size_bytes = NA
            if use_head and parsed.scheme in {"http", "https", "ftp"}:
                size_cache = cache_root / f"{cache_key(url)}.json"
                if size_cache.is_file():
                    size_bytes = json.loads(
                        size_cache.read_text(encoding="utf-8")
                    ).get("size_bytes", NA)
                else:
                    try:
                        size_bytes = remote_size(
                            url,
                            timeout,
                            user_agent,
                            retries,
                            retry_delay,
                            opener=opener,
                        )
                        size_cache.parent.mkdir(parents=True, exist_ok=True)
                        size_cache.write_text(
                            json.dumps({"url": url, "size_bytes": size_bytes}),
                            encoding="utf-8",
                        )
                    except Exception as error:
                        events.append(
                            event(
                                "fetch_geo_supplementary_index",
                                "WARNING",
                                "SUPPLEMENTARY_HEAD_FAILED",
                                error,
                                "The file index is retained with size_bytes=NA; retry later if size is required.",
                                accession=accession,
                            )
                        )
            entries.append(
                {
                    "gse_accession": gse_accession,
                    "gsm_accession": accession if scope == "GSM" else NA,
                    "source_scope": scope,
                    "raw_metadata_key": key,
                    "supplementary_file_name": filename,
                    "supplementary_url": url,
                    "size_bytes": size_bytes,
                    "file_type": file_type,
                    "fetched_at_utc": utc_now(),
                }
            )
    return entries, events


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build a GEO supplementary-file index without downloading files."
    )
    parser.add_argument("--series", required=True)
    parser.add_argument("--samples", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--legacy-output")
    parser.add_argument("--event-log", required=True)
    parser.add_argument("--cache-dir", required=True)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-delay", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--user-agent", default="geo-rnaseq-mining/0.1")
    parser.add_argument("--use-head", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    series_entries, series_events = collect_entries(
        read_tsv(args.series),
        "GSE",
        args.use_head,
        args.cache_dir,
        args.timeout,
        args.user_agent,
        args.retries,
        args.retry_delay,
        urllib.request.urlopen,
    )
    sample_entries, sample_events = collect_entries(
        read_tsv(args.samples),
        "GSM",
        args.use_head,
        args.cache_dir,
        args.timeout,
        args.user_agent,
        args.retries,
        args.retry_delay,
        urllib.request.urlopen,
    )
    entries = series_entries + sample_entries
    events = series_events + sample_events
    events.append(
        event(
            "fetch_geo_supplementary_index",
            "INFO",
            "SUPPLEMENTARY_INDEX_COMPLETE",
            f"Indexed {len(entries)} supplementary file references without downloading file content.",
            "No action required.",
        )
    )
    write_tsv(args.output, FIELDS, entries)
    if args.legacy_output:
        legacy_output = Path(args.legacy_output)
        legacy_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.output, legacy_output)
    write_events(args.event_log, events)


if __name__ == "__main__":
    main()
