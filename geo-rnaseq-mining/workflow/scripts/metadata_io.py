import csv
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


NA = "NA"
EVENT_FIELDS = [
    "timestamp_utc",
    "rule",
    "accession",
    "severity",
    "event_type",
    "message",
    "suggested_action",
    "attempt",
    "cache_hit",
]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def normalize_missing(value):
    if value is None or value == "":
        return NA
    return value


def read_tsv(path):
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path, fieldnames, rows):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {field: normalize_missing(row.get(field)) for field in fieldnames}
            )


def write_events(path, events):
    write_tsv(path, EVENT_FIELDS, events)


def event(
    rule,
    severity,
    event_type,
    message,
    suggested_action,
    accession=NA,
    attempt=NA,
    cache_hit=False,
):
    return {
        "timestamp_utc": utc_now(),
        "rule": rule,
        "accession": accession,
        "severity": severity,
        "event_type": event_type,
        "message": str(message).replace("\t", " ").replace("\n", " "),
        "suggested_action": suggested_action,
        "attempt": attempt,
        "cache_hit": str(bool(cache_hit)).lower(),
    }


def cache_key(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch_bytes(
    url,
    cache_path,
    retries,
    retry_delay,
    timeout,
    headers=None,
    method="GET",
    opener=None,
):
    cache = Path(cache_path)
    if cache.is_file():
        return cache.read_bytes(), True, 0

    open_request = opener or urllib.request.urlopen
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(
                url, headers=headers or {}, method=method
            )
            with open_request(request, timeout=timeout) as response:
                content = response.read()
            cache.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache.with_suffix(cache.suffix + ".tmp")
            temporary.write_bytes(content)
            temporary.replace(cache)
            return content, False, attempt
        except Exception as error:
            last_error = error
            if attempt < retries:
                time.sleep(retry_delay)
    raise RuntimeError(
        f"Network request failed after {retries} attempts for {url}: {last_error}"
    )


def load_raw_json(value):
    if not value or value == NA:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, (dict, list)) else {}
