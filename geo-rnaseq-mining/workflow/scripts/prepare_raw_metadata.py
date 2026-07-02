#!/usr/bin/env python3

import argparse
import hashlib
from pathlib import Path

from metadata_io import EVENT_FIELDS, read_tsv, utc_now, write_tsv


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Combine metadata fetch events and generate SHA-256 checksums."
    )
    parser.add_argument("--data-files", nargs="+", required=True)
    parser.add_argument("--event-files", nargs="+", required=True)
    parser.add_argument("--fetch-log", required=True)
    parser.add_argument("--checksums", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    events = []
    for event_file in args.event_files:
        events.extend(read_tsv(event_file))
    events.sort(key=lambda row: row.get("timestamp_utc", ""))
    write_tsv(args.fetch_log, EVENT_FIELDS, events)

    files_to_hash = [*args.data_files, args.fetch_log]
    checksum_path = Path(args.checksums)
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8", newline="\n") as handle:
        for file_path in files_to_hash:
            handle.write(f"{sha256_file(file_path)}  {file_path}\n")
    print(
        f"{utc_now()} wrote {len(events)} events and "
        f"{len(files_to_hash)} SHA-256 checksums"
    )


if __name__ == "__main__":
    main()
