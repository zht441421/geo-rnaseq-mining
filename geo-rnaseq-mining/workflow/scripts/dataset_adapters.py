#!/usr/bin/env python3

import argparse
import csv
import gzip
import hashlib
from pathlib import Path

import yaml


FINAL_BIOLOGICAL_FIELDS = {
    "group",
    "subject_id",
    "include",
    "batch",
    "contrast",
    "analysis_strategy",
}


def load_registry(path):
    with Path(path).open(encoding="utf-8") as handle:
        registry = yaml.safe_load(handle) or {}
    adapters = registry.get("adapters", [])
    if not isinstance(adapters, list):
        raise ValueError("adapter registry must contain an adapters list")
    names = set()
    for adapter in adapters:
        name = adapter.get("name")
        if not name:
            raise ValueError("adapter missing name")
        if name in names:
            raise ValueError(f"duplicate adapter name: {name}")
        names.add(name)
        if adapter.get("writes_final_biological_fields") is not False:
            raise ValueError(f"adapter {name} may not write final biological fields")
        if adapter.get("output_scope") != "data_inventory_or_suggested_mapping":
            raise ValueError(f"adapter {name} has unsafe output_scope")
        int(adapter.get("priority", 0))
    return sorted(adapters, key=lambda row: int(row.get("priority", 0)))


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_bulk_matrix(path):
    path = Path(path)
    delimiter = "," if path.name.lower().endswith((".csv", ".csv.gz")) else "\t"
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader, [])
        if len(header) < 2:
            raise ValueError("bulk matrix is empty or lacks sample columns")
        genes = set()
        max_value = 0.0
        total = 0.0
        fractional = False
        negative = False
        for row in reader:
            if not row:
                continue
            gene = row[0]
            if gene in genes:
                raise ValueError(f"duplicate gene_id: {gene}")
            genes.add(gene)
            for value in row[1:]:
                number = float(value)
                max_value = max(max_value, number)
                total += number
                fractional = fractional or not number.is_integer()
                negative = negative or number < 0
        likely_tpm = fractional or (0 < max_value <= 50 and total <= 10_000)
    return {
        "file_format": path.suffix.lstrip(".") or "tsv",
        "checksum": sha256_file(path),
        "is_integer": str(not fractional and not negative).lower(),
        "likely_normalized": str(likely_tpm).lower(),
        "technical_consistency": "error:likely_normalized" if likely_tpm else "pass",
        "requires_manual_review": str(likely_tpm).lower(),
    }


def inspect_10x_dir(path):
    path = Path(path)
    required = ["matrix.mtx", "barcodes.tsv", "features.tsv"]
    missing = [name for name in required if not (path / name).is_file()]
    if missing:
        return {
            "file_format": "10x_mtx_dir",
            "checksum": "NA",
            "is_integer": "NA",
            "likely_normalized": "NA",
            "technical_consistency": "error:missing_10x_files:" + ";".join(missing),
            "requires_manual_review": "true",
        }
    return {
        "file_format": "10x_mtx_dir",
        "checksum": "NA",
        "is_integer": "true",
        "likely_normalized": "false",
        "technical_consistency": "pass",
        "requires_manual_review": "false",
    }


def adapt_path(registry, dataset_id, sample_id, path):
    path = Path(path)
    for adapter in registry:
        if not adapter.get("enabled", True):
            continue
        name = adapter["name"]
        if name == "generic_bulk_matrix":
            suffixes = tuple(adapter.get("allowed_extensions", []))
            if any(str(path).lower().endswith(suffix) for suffix in suffixes):
                info = inspect_bulk_matrix(path)
                return {
                    "dataset_id": dataset_id,
                    "sample_id": sample_id,
                    "adapter": name,
                    "data_type_confirmed": adapter["data_type"],
                    "entry_point": "generic_adapter",
                    "file_path": str(path),
                    **info,
                }
        if name == "generic_10x" and path.is_dir():
            info = inspect_10x_dir(path)
            return {
                "dataset_id": dataset_id,
                "sample_id": sample_id,
                "adapter": name,
                "data_type_confirmed": adapter["data_type"],
                "entry_point": "generic_adapter",
                "file_path": str(path),
                **info,
            }
    raise ValueError(f"no enabled adapter matched {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--path")
    parser.add_argument("--dataset-id", default="NA")
    parser.add_argument("--sample-id", default="NA")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    registry = load_registry(args.registry)
    rows = []
    if args.path:
        rows.append(adapt_path(registry, args.dataset_id, args.sample_id, args.path))
    else:
        rows = [
            {
                "adapter": row["name"],
                "enabled": str(row.get("enabled", True)).lower(),
                "priority": row.get("priority", "NA"),
                "status": "valid",
            }
            for row in registry
        ]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with Path(args.output).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
