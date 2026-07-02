#!/usr/bin/env python3

import argparse
import fnmatch
import hashlib
import time
import urllib.request
from pathlib import Path

import yaml

from data_entry_common import NA, read_tsv, sha256_file, write_tsv


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
    "message",
]


def allowed(row, patterns):
    text = f"{row.get('file_name', '')} {row.get('url', '')}"
    return any(fnmatch.fnmatch(text, pattern) for pattern in patterns)


def safe_filename(value):
    name = Path(value).name
    return "".join(character if character.isalnum() or character in "._-" else "_" for character in name)


def download_file(url, destination, retries, retry_delay, user_agent):
    destination = Path(destination)
    if destination.is_file() and destination.stat().st_size > 0:
        return "cached"
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(request, timeout=120) as response:
                with partial.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
            partial.replace(destination)
            return "downloaded"
        except Exception as error:
            last_error = error
            if attempt < retries:
                time.sleep(retry_delay)
    raise RuntimeError(f"Download failed after {retries} attempts: {last_error}")


def download_supplementary(rows, config, project_root):
    settings = config["data_entry"]
    enabled = bool(settings["supplementary_download_enabled"])
    patterns = settings.get("supplementary_allowlist") or []
    maximum = int(settings["supplementary_max_size_bytes"])
    cache_root = Path(project_root) / settings["download_cache_dir"]
    output = []
    url_results = {}
    for row in rows:
        url = row.get("url", NA)
        file_name = row.get("file_name", NA)
        status = "skipped"
        message = "Supplementary download is disabled."
        local_path = NA
        checksum = NA
        size = row.get("size_bytes", NA)
        if enabled and not patterns:
            message = "Download enabled but supplementary_allowlist is empty; no file was selected."
        elif enabled and not allowed(row, patterns):
            message = "File does not match supplementary_allowlist."
        elif enabled and size not in ("", NA):
            try:
                if int(size) > maximum:
                    message = f"File exceeds supplementary_max_size_bytes={maximum}."
                else:
                    status = "selected"
            except ValueError:
                status = "selected"
        elif enabled:
            status = "selected"
        if status == "selected":
            if url in url_results:
                local_path, size, checksum, status, message = url_results[url]
            else:
                prefix = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
                destination = (
                    cache_root
                    / safe_filename(row.get("dataset_id", "unmapped"))
                    / f"{prefix}_{safe_filename(file_name)}"
                )
                try:
                    download_status = download_file(
                        url,
                        destination,
                        int(settings.get("sra_retries", 3)),
                        float(settings.get("retry_delay_seconds", 10)),
                        config["geo"]["user_agent"],
                    )
                    local_path = str(destination)
                    size = destination.stat().st_size
                    checksum = sha256_file(destination)
                    status = "verified"
                    message = f"Supplementary file {download_status} and checksummed."
                except Exception as error:
                    status = "error"
                    message = str(error)
                url_results[url] = (local_path, size, checksum, status, message)
        output.append(
            {
                "dataset_id": row.get("dataset_id", NA),
                "sample_id": row.get("sample_id", NA),
                "data_type_confirmed": row.get("data_type_confirmed", NA),
                "source_type": "GEO_supplementary",
                "source_id": file_name,
                "source_url": url,
                "file_path": local_path,
                "file_size": size,
                "checksum": checksum,
                "status": status,
                "message": message,
            }
        )
    return output


def parse_args():
    parser = argparse.ArgumentParser(description="Download allowlisted GEO supplementary files.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config, encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    rows = download_supplementary(
        read_tsv(args.inventory), config, Path(args.project_root).resolve()
    )
    write_tsv(args.output, FIELDS, rows)
    print(f"Processed {len(rows)} supplementary download candidates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
