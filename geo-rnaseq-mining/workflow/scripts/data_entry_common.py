import csv
import gzip
import hashlib
import json
import math
import os
from collections import Counter
from pathlib import Path


NA = "NA"
INVENTORY_FIELDS = [
    "dataset_id",
    "sample_id",
    "data_type_confirmed",
    "entry_point",
    "file_path",
    "file_format",
    "file_size",
    "checksum",
    "count_type",
    "is_integer",
    "likely_normalized",
    "paired_end_status",
    "recommended_pipeline",
    "technical_consistency",
    "requires_manual_review",
    "source_type",
    "source_url",
    "source_id",
    "has_negative",
    "likely_log_transformed",
    "duplicate_gene_ids",
    "sample_columns_match",
    "status",
    "message",
]


def is_missing(value):
    return value is None or str(value) in {"", "NA", "N/A", "null", "None"}


def read_tsv(path):
    path = Path(path)
    if not path.is_file():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
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
        writer.writerows(rows)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def confirmed_family(data_type):
    lowered = (data_type or "").lower()
    if any(term in lowered for term in ("scrna", "snrna", "single_cell", "single-cell")):
        return "single_cell"
    if "bulk" in lowered:
        return "bulk"
    return "unknown"


def open_text(path):
    return (
        gzip.open(path, "rt", encoding="utf-8-sig", newline="")
        if str(path).lower().endswith(".gz")
        else Path(path).open(encoding="utf-8-sig", newline="")
    )


def read_magic(path, size=16):
    path = Path(path)
    if str(path).lower().endswith(".gz"):
        with gzip.open(path, "rb") as handle:
            return handle.read(size)
    with path.open("rb") as handle:
        return handle.read(size)


def inspect_tabular_matrix(path, expected_sample_ids=None):
    expected_sample_ids = set(expected_sample_ids or [])
    path = Path(path)
    with open_text(path) as handle:
        first_line = handle.readline()
        if not first_line:
            return {"recognized": True, "empty": True, "file_format": "tabular"}
        delimiter = "," if first_line.count(",") > first_line.count("\t") else "\t"
        header = next(csv.reader([first_line], delimiter=delimiter))
        if len(header) < 2:
            return {"recognized": False}
        sample_columns = header[1:]
        duplicate_columns = sorted(
            name for name, count in Counter(sample_columns).items() if count > 1
        )
        gene_ids = Counter()
        column_sums = [0.0] * len(sample_columns)
        integer = True
        negative = False
        numeric = True
        fractional_count = 0
        maximum = None
        minimum = None
        row_count = 0
        malformed_rows = 0
        reader = csv.reader(handle, delimiter=delimiter)
        for values in reader:
            if not values or all(value == "" for value in values):
                continue
            row_count += 1
            if len(values) != len(header):
                malformed_rows += 1
                continue
            gene_ids[values[0]] += 1
            for index, value in enumerate(values[1:]):
                try:
                    number = float(value)
                except ValueError:
                    numeric = False
                    continue
                if not math.isfinite(number):
                    numeric = False
                    continue
                column_sums[index] += number
                integer = integer and number.is_integer()
                fractional_count += int(not number.is_integer())
                negative = negative or number < 0
                maximum = number if maximum is None else max(maximum, number)
                minimum = number if minimum is None else min(minimum, number)
    labels = " ".join([path.name, *header]).lower()
    explicit_type = None
    for value in ("tpm", "fpkm", "cpm"):
        if value in labels:
            explicit_type = value
            break
    if "log2" in labels or "log expression" in labels:
        explicit_type = "log_transformed"
    nonzero_sums = [total for total in column_sums if total != 0]
    near_million = bool(nonzero_sums) and all(
        900000 <= total <= 1100000 for total in nonzero_sums
    )
    likely_log = (
        numeric
        and not integer
        and not negative
        and maximum is not None
        and maximum <= 100
        and fractional_count > 0
    )
    if explicit_type:
        count_type = explicit_type
    elif near_million and not integer:
        count_type = "tpm_or_cpm_likely"
    elif numeric and integer and not negative:
        count_type = "raw_integer_counts"
    elif likely_log:
        count_type = "log_transformed_likely"
    elif numeric:
        count_type = "non_integer_expression"
    else:
        count_type = "unknown"
    return {
        "recognized": True,
        "empty": row_count == 0,
        "file_format": "csv_matrix" if delimiter == "," else "tsv_matrix",
        "sample_columns": sample_columns,
        "sample_columns_match": (
            str(expected_sample_ids.issubset(set(sample_columns))).lower()
            if expected_sample_ids
            else NA
        ),
        "missing_sample_columns": sorted(expected_sample_ids - set(sample_columns)),
        "duplicate_sample_columns": duplicate_columns,
        "is_integer": str(integer and numeric).lower(),
        "has_negative": str(negative).lower(),
        "likely_log_transformed": str(likely_log).lower(),
        "likely_normalized": str(
            explicit_type is not None or near_million or likely_log
        ).lower(),
        "count_type": count_type,
        "duplicate_gene_ids": sum(count - 1 for count in gene_ids.values() if count > 1),
        "duplicate_gene_id_examples": sorted(
            gene_id for gene_id, count in gene_ids.items() if count > 1
        )[:20],
        "row_count": row_count,
        "malformed_rows": malformed_rows,
        "column_sums": column_sums,
        "minimum": minimum,
        "maximum": maximum,
    }


def inspect_matrix_market(path):
    with open_text(path) as handle:
        header = handle.readline().strip()
        if not header.startswith("%%MatrixMarket"):
            return {"recognized": False}
        integer_declared = " integer " in f" {header.lower()} "
        negative = False
        fractional = False
        entries = 0
        dimensions_seen = False
        for line in handle:
            if line.startswith("%") or not line.strip():
                continue
            parts = line.split()
            if not dimensions_seen:
                dimensions_seen = True
                continue
            if len(parts) < 3:
                continue
            entries += 1
            number = float(parts[2])
            negative = negative or number < 0
            fractional = fractional or not number.is_integer()
    return {
        "recognized": True,
        "empty": entries == 0,
        "file_format": "matrix_market",
        "is_integer": str(integer_declared and not fractional).lower(),
        "has_negative": str(negative).lower(),
        "likely_log_transformed": "false",
        "likely_normalized": str(fractional).lower(),
        "count_type": "raw_integer_counts"
        if integer_declared and not fractional and not negative
        else "non_integer_expression",
        "duplicate_gene_ids": NA,
        "sample_columns_match": NA,
    }


def inspect_hdf5(path):
    try:
        import h5py
    except ImportError:
        return {
            "recognized": True,
            "file_format": "hdf5_uninspected",
            "requires_dependency": "h5py",
        }
    try:
        with h5py.File(path, "r") as handle:
            keys = set(handle.keys())
            if {"obs", "var", "X"}.issubset(keys) or {"obs", "var"}.issubset(keys):
                return {
                    "recognized": True,
                    "file_format": "h5ad",
                    "count_type": "requires_h5ad_layer_review",
                    "is_integer": NA,
                    "likely_normalized": NA,
                    "has_negative": NA,
                    "likely_log_transformed": NA,
                    "duplicate_gene_ids": NA,
                    "sample_columns_match": NA,
                }
            if "matrix" in keys:
                matrix = handle["matrix"]
                required = {"barcodes", "data", "indices", "indptr", "shape"}
                valid_10x = required.issubset(set(matrix.keys()))
                integer = True
                negative = False
                if valid_10x:
                    data = matrix["data"]
                    chunk = max(1, min(len(data), 1_000_000))
                    for start in range(0, len(data), chunk):
                        values = data[start : start + chunk]
                        integer = integer and all(float(value).is_integer() for value in values)
                        negative = negative or any(value < 0 for value in values)
                return {
                    "recognized": valid_10x,
                    "file_format": "10x_h5" if valid_10x else "hdf5_unknown",
                    "count_type": "raw_integer_counts"
                    if valid_10x and integer and not negative
                    else "unknown",
                    "is_integer": str(integer).lower() if valid_10x else NA,
                    "likely_normalized": "false" if valid_10x and integer else NA,
                    "has_negative": str(negative).lower() if valid_10x else NA,
                    "likely_log_transformed": "false",
                    "duplicate_gene_ids": NA,
                    "sample_columns_match": NA,
                }
            return {"recognized": True, "file_format": "hdf5_unknown"}
    except OSError:
        return {"recognized": False}


def inspect_10x_directory(path):
    path = Path(path)
    search_roots = [
        path,
        path / "filtered_feature_bc_matrix",
        path / "raw_feature_bc_matrix",
        path / "outs" / "filtered_feature_bc_matrix",
        path / "outs" / "raw_feature_bc_matrix",
    ]
    candidates = {
        "matrix": ["matrix.mtx", "matrix.mtx.gz"],
        "features": ["features.tsv", "features.tsv.gz", "genes.tsv", "genes.tsv.gz"],
        "barcodes": ["barcodes.tsv", "barcodes.tsv.gz"],
    }
    for search_root in search_roots:
        found = {}
        for key, names in candidates.items():
            found[key] = next(
                (
                    search_root / name
                    for name in names
                    if (search_root / name).is_file()
                ),
                None,
            )
        if all(found.values()):
            inspected = inspect_matrix_market(found["matrix"])
            inspected.update(
                {
                    "recognized": True,
                    "file_format": "10x_mtx_directory"
                    if search_root == path
                    else "cellranger_output_directory",
                    "component_files": {
                        key: str(value) for key, value in found.items()
                    },
                }
            )
            return inspected
    return {"recognized": False}


def inspect_fastq(path):
    try:
        with open_text(path) as handle:
            lines = [handle.readline() for _ in range(4)]
    except (OSError, UnicodeDecodeError):
        return {"recognized": False}
    valid = (
        all(lines)
        and lines[0].startswith("@")
        and lines[2].startswith("+")
        and len(lines[1].rstrip()) == len(lines[3].rstrip())
    )
    return {"recognized": valid, "file_format": "fastq" if valid else "unknown"}


def inspect_local_entry(path, expected_sample_ids=None):
    path = Path(path)
    if path.is_dir():
        inspected = inspect_10x_directory(path)
        if inspected.get("recognized"):
            inspected["file_size"] = sum(
                file.stat().st_size for file in path.rglob("*") if file.is_file()
            )
            return inspected
        return {
            "recognized": False,
            "file_format": "directory_unknown",
            "file_size": NA,
        }
    if not path.is_file():
        return {"recognized": False, "file_format": "missing", "file_size": NA}
    magic = read_magic(path)
    if magic.startswith(b"\x89HDF\r\n\x1a\n"):
        inspected = inspect_hdf5(path)
    elif magic.startswith(b"%%MatrixMarket"):
        inspected = inspect_matrix_market(path)
    elif magic.startswith((b"RDX", b"RDA")):
        inspected = {"recognized": True, "file_format": "rds_or_rdata"}
    elif magic.startswith(b"@"):
        inspected = inspect_fastq(path)
    else:
        inspected = inspect_tabular_matrix(path, expected_sample_ids)
        if not inspected.get("recognized") and path.suffix.lower() == ".rds":
            inspected = {"recognized": True, "file_format": "rds_unverified"}
    inspected["file_size"] = path.stat().st_size
    inspected["checksum"] = sha256_file(path)
    return inspected


def entry_point_for(file_format, family, count_type):
    if file_format == "fastq":
        return f"{family}_fastq" if family in {"bulk", "single_cell"} else "fastq"
    if file_format == "10x_mtx_directory":
        return "single_cell_10x_mtx"
    if file_format == "cellranger_output_directory":
        return "single_cell_cellranger_directory"
    if file_format == "10x_h5":
        return "single_cell_10x_h5"
    if file_format == "h5ad":
        return "single_cell_h5ad"
    if file_format.startswith("rds"):
        return "single_cell_rds_candidate"
    if file_format in {"tsv_matrix", "csv_matrix", "matrix_market"}:
        if family == "bulk" and count_type == "raw_integer_counts":
            return "bulk_gene_count_matrix"
        if family == "bulk":
            return "bulk_expression_matrix_exploratory"
        if family == "single_cell":
            return "single_cell_matrix_candidate"
        return "expression_matrix"
    return "unknown"


def recommended_pipeline(entry_point, count_type):
    if entry_point == "bulk_gene_count_matrix" and count_type == "raw_integer_counts":
        return "bulk_raw_count_qc_then_deseq2"
    if entry_point == "bulk_expression_matrix_exploratory":
        return "exploratory_only_no_deseq2"
    if entry_point == "bulk_fastq":
        return "bulk_fastq_quantification"
    if entry_point.startswith("single_cell_"):
        return "single_cell_raw_count_workflow"
    if entry_point == "single_cell_fastq":
        return "cellranger_or_equivalent"
    return "manual_entry_selection_required"


def classify_local_file(
    dataset_id,
    sample_id,
    data_type_confirmed,
    path,
    expected_sample_ids=None,
    source_type="reviewed_path",
    source_url=NA,
    source_id=NA,
):
    inspected = inspect_local_entry(path, expected_sample_ids)
    family = confirmed_family(data_type_confirmed)
    file_format = inspected.get("file_format", "unknown")
    count_type = inspected.get("count_type", NA)
    entry_point = entry_point_for(file_format, family, count_type)
    detected_family = (
        "single_cell"
        if entry_point.startswith("single_cell")
        else "bulk"
        if entry_point.startswith("bulk")
        else "unknown"
    )
    conflict = (
        family != "unknown"
        and detected_family != "unknown"
        and family != detected_family
    )
    normalized = inspected.get("likely_normalized", NA) == "true"
    if conflict:
        consistency = "error:data_type_file_conflict"
        manual = "true"
        message = (
            f"Confirmed data_type={data_type_confirmed} conflicts with detected "
            f"entry family={detected_family}."
        )
    elif normalized and family == "bulk":
        consistency = "warning:normalized_matrix_exploratory_only"
        manual = "true"
        message = "Likely normalized matrix; DESeq2 is prohibited."
    elif not inspected.get("recognized"):
        consistency = "warning:unrecognized_content"
        manual = "true"
        message = "File content could not be recognized."
    elif file_format == "h5ad" and count_type == "requires_h5ad_layer_review":
        consistency = "warning:h5ad_raw_counts_unverified"
        manual = "true"
        message = "H5AD structure detected; raw count layer requires manual confirmation."
    else:
        consistency = "consistent"
        manual = "false"
        message = "Technical entry is consistent with confirmed data_type."
    return {
        "dataset_id": dataset_id,
        "sample_id": sample_id,
        "data_type_confirmed": data_type_confirmed,
        "entry_point": entry_point,
        "file_path": str(path),
        "file_format": file_format,
        "file_size": inspected.get("file_size", NA),
        "checksum": inspected.get("checksum", NA),
        "count_type": count_type,
        "is_integer": inspected.get("is_integer", NA),
        "likely_normalized": inspected.get("likely_normalized", NA),
        "paired_end_status": NA,
        "recommended_pipeline": recommended_pipeline(entry_point, count_type),
        "technical_consistency": consistency,
        "requires_manual_review": manual,
        "source_type": source_type,
        "source_url": source_url,
        "source_id": source_id,
        "has_negative": inspected.get("has_negative", NA),
        "likely_log_transformed": inspected.get("likely_log_transformed", NA),
        "duplicate_gene_ids": inspected.get("duplicate_gene_ids", NA),
        "sample_columns_match": inspected.get("sample_columns_match", NA),
        "status": "available" if inspected.get("recognized") else "unrecognized",
        "message": message,
        "_inspection": inspected,
    }


def classify_remote_candidate(row):
    name = " ".join(
        [
            row.get("file_name", ""),
            row.get("url", ""),
            row.get("file_type", ""),
        ]
    ).lower()
    hints = []
    for term in (
        "matrix.mtx",
        "features.tsv",
        "barcodes.tsv",
        "filtered_feature_bc_matrix",
        ".h5ad",
        ".h5",
        ".rds",
        "count",
        "tpm",
        "fpkm",
        "fastq",
    ):
        if term in name:
            hints.append(term)
    return {
        "candidate_hints": hints,
        "file_format": "remote_uninspected",
        "entry_point": "unverified_remote_candidate",
        "count_type": "unverified",
        "requires_manual_review": "true",
        "technical_consistency": "warning:content_not_downloaded",
    }


def json_details(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
