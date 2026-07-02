#!/usr/bin/env python3

import argparse
import gzip
import json
import subprocess
import time
from pathlib import Path

from data_entry_common import sha256_file


def run_command(command):
    subprocess.run(command, check=True)


def prefetch_command(srr, output_dir, max_size):
    return [
        "prefetch",
        srr,
        "--output-directory",
        str(output_dir),
        "--max-size",
        str(max_size),
    ]


def fasterq_command(sra_path, output_dir, temp_dir, threads, paired):
    command = [
        "fasterq-dump",
        str(sra_path),
        "--outdir",
        str(output_dir),
        "--temp",
        str(temp_dir),
        "--threads",
        str(threads),
    ]
    if paired:
        command.append("--split-files")
    return command


def status_is_valid(status_path):
    path = Path(status_path)
    if not path.is_file():
        return False
    try:
        status = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return False
    if status.get("status") != "verified":
        return False
    for item in status.get("files", []):
        file_path = Path(item["path"])
        if not file_path.is_file() or sha256_file(file_path) != item["checksum"]:
            return False
    return True


def write_status(path, payload):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def fastq_record_count(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    lines = 0
    with opener(path, "rt", encoding="utf-8", errors="strict") as handle:
        for line_number, line in enumerate(handle, start=1):
            position = (line_number - 1) % 4
            if position == 0 and not line.startswith("@"):
                raise ValueError(f"FASTQ record header invalid at line {line_number}: {path}")
            if position == 2 and not line.startswith("+"):
                raise ValueError(f"FASTQ separator invalid at line {line_number}: {path}")
            lines += 1
    if lines == 0 or lines % 4:
        raise ValueError(f"FASTQ line count is not a non-zero multiple of four: {path}")
    return lines // 4


def prefetch_run(args):
    if status_is_valid(args.status):
        print(f"{args.srr}: verified cache reused")
        return 0
    if not args.enabled:
        write_status(
            args.status,
            {"status": "skipped", "srr": args.srr, "reason": "sra_download_enabled=false", "files": []},
        )
        return 0
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(1, args.retries + 1):
        try:
            run_command(prefetch_command(args.srr, output_dir, args.max_size))
            sra_path = output_dir / args.srr / f"{args.srr}.sra"
            if not sra_path.is_file():
                raise FileNotFoundError(f"prefetch did not create {sra_path}")
            run_command(["vdb-validate", str(sra_path)])
            write_status(
                args.status,
                {
                    "status": "verified",
                    "stage": "prefetch",
                    "srr": args.srr,
                    "attempt": attempt,
                    "files": [
                        {
                            "path": str(sra_path),
                            "size": sra_path.stat().st_size,
                            "checksum": sha256_file(sra_path),
                        }
                    ],
                },
            )
            return 0
        except Exception as error:
            last_error = error
            if attempt < args.retries:
                time.sleep(args.retry_delay)
    write_status(
        args.status,
        {"status": "error", "stage": "prefetch", "srr": args.srr, "error": str(last_error), "files": []},
    )
    return 2


def fasterq_run(args):
    if status_is_valid(args.status):
        print(f"{args.srr}: verified FASTQ cache reused")
        return 0
    prefetch_status = json.loads(Path(args.prefetch_status).read_text(encoding="utf-8"))
    if prefetch_status.get("status") == "skipped":
        write_status(
            args.status,
            {"status": "skipped", "srr": args.srr, "reason": "prefetch skipped", "files": []},
        )
        return 0
    if prefetch_status.get("status") != "verified":
        write_status(
            args.status,
            {"status": "error", "srr": args.srr, "reason": "prefetch not verified", "files": []},
        )
        return 2
    sra_path = Path(prefetch_status["files"][0]["path"])
    output_dir = Path(args.output_dir)
    temp_dir = Path(args.temp_dir) / args.srr
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    paired = args.layout.upper() == "PAIRED"
    try:
        run_command(
            fasterq_command(sra_path, output_dir, temp_dir, args.threads, paired)
        )
        fastqs = (
            [output_dir / f"{args.srr}_1.fastq", output_dir / f"{args.srr}_2.fastq"]
            if paired
            else [output_dir / f"{args.srr}.fastq"]
        )
        if not all(path.is_file() for path in fastqs):
            raise FileNotFoundError(f"Expected FASTQ outputs were not created: {fastqs}")
        record_counts = [fastq_record_count(path) for path in fastqs]
        if paired and record_counts[0] != record_counts[1]:
            raise ValueError(
                f"Paired FASTQ record counts differ: {record_counts[0]} vs {record_counts[1]}"
            )
        compressed = []
        for fastq in fastqs:
            run_command(["pigz", "-p", str(args.threads), "-f", str(fastq)])
            gz_path = Path(str(fastq) + ".gz")
            run_command(["pigz", "-t", str(gz_path)])
            fastq_record_count(gz_path)
            compressed.append(gz_path)
        write_status(
            args.status,
            {
                "status": "verified",
                "stage": "fasterq",
                "srr": args.srr,
                "layout": args.layout,
                "paired_end_status": "complete" if paired else "single",
                "record_counts": record_counts,
                "files": [
                    {
                        "path": str(path),
                        "size": path.stat().st_size,
                        "checksum": sha256_file(path),
                    }
                    for path in compressed
                ],
            },
        )
        return 0
    except Exception as error:
        write_status(
            args.status,
            {"status": "error", "stage": "fasterq", "srr": args.srr, "error": str(error), "files": []},
        )
        return 2


def parse_args():
    parser = argparse.ArgumentParser(description="Cached SRA prefetch and FASTQ conversion.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prefetch = subparsers.add_parser("prefetch")
    prefetch.add_argument("--srr", required=True)
    prefetch.add_argument("--output-dir", required=True)
    prefetch.add_argument("--status", required=True)
    prefetch.add_argument("--max-size", default="50G")
    prefetch.add_argument("--retries", type=int, default=3)
    prefetch.add_argument("--retry-delay", type=float, default=10)
    prefetch.add_argument("--enabled", action="store_true")

    fasterq = subparsers.add_parser("fasterq")
    fasterq.add_argument("--srr", required=True)
    fasterq.add_argument("--layout", required=True)
    fasterq.add_argument("--prefetch-status", required=True)
    fasterq.add_argument("--output-dir", required=True)
    fasterq.add_argument("--temp-dir", required=True)
    fasterq.add_argument("--status", required=True)
    fasterq.add_argument("--threads", type=int, default=4)
    return parser.parse_args()


def main():
    args = parse_args()
    return prefetch_run(args) if args.command == "prefetch" else fasterq_run(args)


if __name__ == "__main__":
    raise SystemExit(main())
