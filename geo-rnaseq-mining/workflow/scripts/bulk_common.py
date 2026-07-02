import csv
import gzip
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from preanalysis_common import (
    as_bool,
    is_missing,
    make_issue,
    pass_issue,
    sort_issues,
)


def is_bulk_data_type(value):
    lowered = str(value or "").lower()
    return "bulk" in lowered and "pseudobulk" not in lowered


def active_bulk_rows(manifest, dataset_id=None):
    rows = [
        row
        for row in manifest
        if as_bool(row.get("include")) is True
        and row.get("review_status") == "confirmed"
        and is_bulk_data_type(row.get("data_type"))
    ]
    if dataset_id is not None:
        rows = [row for row in rows if row.get("dataset_id") == dataset_id]
    return rows


def open_text(path):
    path = Path(path)
    if str(path).lower().endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8-sig", newline="")
    return path.open(encoding="utf-8-sig", newline="")


def matrix_header(path):
    with open_text(path) as handle:
        first_line = handle.readline()
    if not first_line:
        return "\t", []
    delimiter = "," if first_line.count(",") > first_line.count("\t") else "\t"
    return delimiter, next(csv.reader([first_line], delimiter=delimiter))


def blocking_issues(issues):
    return [
        issue
        for issue in issues
        if issue["status"] == "fail"
        and issue["severity"] in {"critical", "error"}
    ]


def validate_bulk_count_matrix(path, expected_sample_ids, dataset_id="NA"):
    path = Path(path)
    issues = []
    if not path.is_file():
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "BULK_COUNT_MATRIX_MISSING",
                f"Bulk count matrix does not exist: {path}",
                "Restore the reviewed matrix path; the program will not rewrite it.",
                dataset_id=dataset_id,
            )
        )
        return None, sort_issues(issues)

    delimiter, header = matrix_header(path)
    if len(header) < 2:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "BULK_COUNT_MATRIX_EMPTY",
                "Bulk count matrix has no sample columns.",
                "Provide a gene-by-sample raw count matrix.",
                dataset_id=dataset_id,
            )
        )
        return None, sort_issues(issues)

    observed_sample_ids = header[1:]
    duplicate_samples = sorted(
        sample_id
        for sample_id, count in Counter(observed_sample_ids).items()
        if count > 1
    )
    if duplicate_samples:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "DUPLICATE_BULK_SAMPLE_COLUMNS",
                f"Count matrix contains duplicate sample columns: {duplicate_samples}",
                "Correct duplicate matrix columns without changing reviewed sample_id values.",
                dataset_id=dataset_id,
                details={"duplicate_sample_ids": duplicate_samples},
            )
        )

    expected_sample_ids = list(expected_sample_ids)
    expected_duplicates = sorted(
        sample_id
        for sample_id, count in Counter(expected_sample_ids).items()
        if count > 1
    )
    if expected_duplicates:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "DUPLICATE_BULK_MANIFEST_SAMPLES",
                f"Reviewed bulk rows contain duplicate sample_id values: {expected_duplicates}",
                "Correct the reviewed manifest; samples are never merged automatically.",
                dataset_id=dataset_id,
                details={"duplicate_sample_ids": expected_duplicates},
            )
        )

    expected_set = set(expected_sample_ids)
    observed_set = set(observed_sample_ids)
    missing = sorted(expected_set - observed_set)
    extra = sorted(observed_set - expected_set)
    if missing or extra:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "BULK_SAMPLE_COLUMNS_MISMATCH",
                f"Matrix and reviewed manifest samples differ; missing={missing}, extra={extra}.",
                "Make matrix sample columns exactly match included reviewed sample_id values.",
                dataset_id=dataset_id,
                details={"missing": missing, "extra": extra},
            )
        )
    elif observed_sample_ids != expected_sample_ids:
        issues.append(
            make_issue(
                "error",
                "bulk_matrix",
                "BULK_SAMPLE_ORDER_MISMATCH",
                "Matrix sample order differs from reviewed manifest order.",
                "Rebuild the matrix in reviewed manifest order; the workflow will not silently reorder it.",
                dataset_id=dataset_id,
                details={
                    "expected_order": expected_sample_ids,
                    "observed_order": observed_sample_ids,
                },
            )
        )

    try:
        frame = pd.read_csv(path, sep=delimiter, dtype=str, keep_default_na=False)
    except Exception as error:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "BULK_COUNT_MATRIX_UNREADABLE",
                f"Bulk count matrix cannot be parsed: {error}",
                "Provide an uncompressed or gzip-compressed TSV/CSV matrix with one header row.",
                dataset_id=dataset_id,
            )
        )
        return None, sort_issues(issues)

    if frame.empty:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "BULK_COUNT_MATRIX_EMPTY",
                "Bulk count matrix has no gene rows.",
                "Provide a non-empty raw gene-level count matrix.",
                dataset_id=dataset_id,
            )
        )
        return None, sort_issues(issues)

    gene_ids = frame.iloc[:, 0].astype(str)
    blank_gene_ids = int(gene_ids.str.strip().eq("").sum())
    duplicate_gene_ids = sorted(
        gene_id
        for gene_id, count in Counter(gene_ids).items()
        if count > 1
    )
    if blank_gene_ids:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "BLANK_BULK_GENE_IDS",
                f"Count matrix contains {blank_gene_ids} blank gene IDs.",
                "Restore stable, non-empty gene identifiers.",
                dataset_id=dataset_id,
            )
        )
    if duplicate_gene_ids:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "DUPLICATE_BULK_GENE_IDS",
                f"Count matrix contains {len(duplicate_gene_ids)} duplicated gene IDs.",
                "Resolve gene identifiers before analysis; rows are not summed automatically.",
                dataset_id=dataset_id,
                details={"examples": duplicate_gene_ids[:20]},
            )
        )

    values = frame.iloc[:, 1:]
    numeric = values.apply(pd.to_numeric, errors="coerce")
    non_numeric_count = int(numeric.isna().to_numpy().sum())
    numeric_array = numeric.to_numpy(dtype=float)
    finite_count = int(np.isfinite(numeric_array).sum())
    expected_value_count = int(numeric_array.size)
    if non_numeric_count or finite_count != expected_value_count:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "NON_NUMERIC_BULK_COUNTS",
                "Count matrix contains missing, non-numeric, NaN, or infinite values.",
                "Use a complete raw non-negative integer count matrix.",
                dataset_id=dataset_id,
                details={
                    "non_numeric_or_missing": non_numeric_count,
                    "non_finite": expected_value_count - finite_count,
                },
            )
        )

    finite_values = numeric_array[np.isfinite(numeric_array)]
    fractional_count = int(
        np.sum(~np.isclose(finite_values, np.rint(finite_values)))
    )
    negative_count = int(np.sum(finite_values < 0))
    if fractional_count:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "NON_INTEGER_BULK_COUNTS",
                f"Count matrix contains {fractional_count} non-integer values.",
                "TPM, FPKM, CPM, log values, and other normalized expression cannot enter DESeq2.",
                dataset_id=dataset_id,
            )
        )
    if negative_count:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "NEGATIVE_BULK_COUNTS",
                f"Count matrix contains {negative_count} negative values.",
                "Use unmodified raw non-negative counts.",
                dataset_id=dataset_id,
            )
        )

    all_zero_count = 0
    if finite_count == expected_value_count:
        all_zero_count = int(np.sum(np.isclose(numeric_array.sum(axis=1), 0)))
        if all_zero_count:
            issues.append(
                make_issue(
                    "warning",
                    "bulk_matrix",
                    "ALL_ZERO_BULK_GENES",
                    f"Count matrix contains {all_zero_count} all-zero genes.",
                    "Retain the raw matrix; downstream derived analysis may filter these genes and must report the filter.",
                    dataset_id=dataset_id,
                    details={"all_zero_gene_count": all_zero_count},
                )
            )

    labels = " ".join([path.name, *header]).lower()
    explicit_normalized = next(
        (term for term in ("tpm", "fpkm", "cpm", "log2", "log_expression") if term in labels),
        None,
    )
    column_sums = (
        numeric_array.sum(axis=0)
        if finite_count == expected_value_count
        else np.array([], dtype=float)
    )
    near_million = bool(column_sums.size) and bool(
        np.all((column_sums >= 950000) & (column_sums <= 1050000))
    )
    maximum = float(np.max(finite_values)) if finite_values.size else math.nan
    log_like = bool(
        fractional_count
        and not negative_count
        and finite_values.size
        and maximum <= 100
    )
    if explicit_normalized or near_million or log_like:
        issues.append(
            make_issue(
                "critical",
                "bulk_matrix",
                "NORMALIZED_BULK_MATRIX_SUSPECTED",
                "Matrix content or labels are consistent with TPM/FPKM/CPM/log-like expression.",
                "Provide raw gene-level counts; normalized matrices are excluded from DESeq2.",
                dataset_id=dataset_id,
                details={
                    "explicit_hint": explicit_normalized or "NA",
                    "all_library_sums_near_one_million": near_million,
                    "log_like_values": log_like,
                    "maximum": maximum,
                },
            )
        )

    if not blocking_issues(issues):
        issues.append(
            pass_issue(
                "bulk_matrix",
                "BULK_COUNT_MATRIX_VALID",
                "Bulk count matrix is numeric, non-negative, integer, uniquely keyed, and ordered exactly as reviewed.",
                dataset_id=dataset_id,
            )
        )
        standardized = pd.DataFrame(
            np.rint(numeric_array).astype(np.int64),
            columns=observed_sample_ids,
        )
        standardized.insert(0, "gene_id", gene_ids.to_list())
    else:
        standardized = None
    return standardized, sort_issues(issues)


def validate_bulk_entry_contract(rows, dataset_id):
    issues = []
    if not rows:
        return [
            make_issue(
                "error",
                "bulk_entry",
                "NO_ACTIVE_BULK_SAMPLES",
                f"No confirmed included bulk samples exist for {dataset_id}.",
                "Confirm reviewed bulk samples before enabling the dataset.",
                dataset_id=dataset_id,
            )
        ]
    matrix_values = [
        row.get("matrix_path") for row in rows if not is_missing(row.get("matrix_path"))
    ]
    fastq_rows = [
        row
        for row in rows
        if not is_missing(row.get("fastq_r1")) or not is_missing(row.get("fastq_r2"))
    ]
    if matrix_values and fastq_rows:
        issues.append(
            make_issue(
                "critical",
                "bulk_entry",
                "MIXED_BULK_ENTRY_BRANCHES",
                f"Dataset {dataset_id} mixes matrix and FASTQ entry branches.",
                "Choose one reviewed entry branch for the entire dataset.",
                dataset_id=dataset_id,
            )
        )
    elif matrix_values:
        unique_paths = sorted(set(matrix_values))
        if len(unique_paths) != 1 or len(matrix_values) != len(rows):
            issues.append(
                make_issue(
                    "critical",
                    "bulk_entry",
                    "INCONSISTENT_BULK_MATRIX_PATH",
                    "All included samples in a matrix-entry dataset must reference the same matrix.",
                    "Confirm one shared raw gene-level count matrix path for every included sample.",
                    dataset_id=dataset_id,
                    details={"paths": unique_paths},
                )
            )
    else:
        for row in rows:
            sample_id = row.get("sample_id", "NA")
            layout = str(row.get("library_layout", "")).upper()
            if is_missing(row.get("fastq_r1")):
                issues.append(
                    make_issue(
                        "critical",
                        "bulk_entry",
                        "BULK_FASTQ_R1_MISSING",
                        f"FASTQ sample {sample_id} has no fastq_r1.",
                        "Restore the reviewed FASTQ path or set include=false.",
                        dataset_id=dataset_id,
                        sample_id=sample_id,
                    )
                )
            if layout == "PAIRED" and is_missing(row.get("fastq_r2")):
                issues.append(
                    make_issue(
                        "critical",
                        "bulk_entry",
                        "BULK_FASTQ_R2_MISSING",
                        f"Paired FASTQ sample {sample_id} has no fastq_r2.",
                        "Provide both reviewed mates.",
                        dataset_id=dataset_id,
                        sample_id=sample_id,
                    )
                )
    return sort_issues(issues)


def bulk_entry_branch(rows):
    matrix_present = any(not is_missing(row.get("matrix_path")) for row in rows)
    fastq_present = any(
        not is_missing(row.get("fastq_r1")) or not is_missing(row.get("fastq_r2"))
        for row in rows
    )
    if matrix_present and not fastq_present:
        return "matrix"
    if fastq_present and not matrix_present:
        return "fastq"
    return "invalid"


def validate_bulk_reference_config(config, branch, dataset_id):
    if branch != "fastq":
        return []
    references = config.get("references", {})
    method = config.get("bulk", {}).get("quantification_method")
    issues = []
    required_metadata = (
        "species",
        "genome_build",
        "annotation_release",
        "gene_id_space",
    )
    required_paths = ["gtf"]
    if method == "salmon_tximport":
        required_paths.extend(["transcriptome_fasta", "tx2gene", "salmon_index"])
    elif method == "star_featurecounts":
        required_paths.extend(["fasta", "star_index"])
        expected_strand = {
            "unstranded": 0,
            "forward": 1,
            "reverse": 2,
        }.get(config.get("bulk", {}).get("strandedness"))
        observed_strand = config.get("bulk", {}).get("featurecounts_strand")
        if expected_strand != observed_strand:
            issues.append(
                make_issue(
                    "critical",
                    "bulk_reference",
                    "BULK_STRANDEDNESS_PARAMETER_MISMATCH",
                    "bulk.strandedness and featurecounts_strand encode different settings.",
                    "Use one consistent reviewed strandedness setting for every sample.",
                    dataset_id=dataset_id,
                    details={
                        "strandedness": config.get("bulk", {}).get("strandedness"),
                        "featurecounts_strand": observed_strand,
                        "expected_featurecounts_strand": expected_strand,
                    },
                )
            )
    else:
        issues.append(
            make_issue(
                "critical",
                "bulk_reference",
                "UNSUPPORTED_BULK_QUANTIFICATION_METHOD",
                f"Unsupported bulk quantification_method: {method!r}.",
                "Use salmon_tximport or star_featurecounts.",
                dataset_id=dataset_id,
            )
        )
    for key in required_metadata:
        value = references.get(key)
        if is_missing(value) or str(value).lower() == "unknown":
            issues.append(
                make_issue(
                    "critical",
                    "bulk_reference",
                    "BULK_REFERENCE_METADATA_MISSING",
                    f"Required reference metadata {key!r} is not confirmed.",
                    "Record one consistent reference definition before FASTQ quantification.",
                    dataset_id=dataset_id,
                    details={"field": key},
                )
            )
    for key in required_paths:
        value = references.get(key)
        if is_missing(value):
            issues.append(
                make_issue(
                    "critical",
                    "bulk_reference",
                    "BULK_REFERENCE_PATH_MISSING",
                    f"Required reference path {key!r} is not configured.",
                    "Configure the reviewed reference path before FASTQ quantification.",
                    dataset_id=dataset_id,
                    details={"field": key},
                )
            )
        elif not Path(value).exists():
            issues.append(
                make_issue(
                    "critical",
                    "bulk_reference",
                    "BULK_REFERENCE_PATH_NOT_FOUND",
                    f"Configured reference path does not exist: {value}",
                    "Restore the configured reference without changing reference versions.",
                    dataset_id=dataset_id,
                    details={"field": key, "path": str(value)},
                )
            )
    return sort_issues(issues)


def robust_z_scores(values):
    values = np.asarray(values, dtype=float)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad > 0:
        return 0.6744897501960817 * (values - median) / mad
    standard_deviation = float(np.std(values))
    if standard_deviation > 0:
        return (values - float(np.mean(values))) / standard_deviation
    return np.zeros_like(values)


def calculate_sample_qc(
    counts,
    sample_metadata,
    detected_gene_min_count=1,
    outlier_z_threshold=3.0,
):
    sample_ids = list(counts.columns[1:])
    count_values = counts.iloc[:, 1:].to_numpy(dtype=float)
    library_sizes = count_values.sum(axis=0)
    detected_genes = (count_values >= detected_gene_min_count).sum(axis=0)
    transformed = np.log2(count_values + 1).T
    centered = transformed - transformed.mean(axis=0, keepdims=True)
    if centered.size and centered.shape[0] > 1:
        left, singular, _ = np.linalg.svd(centered, full_matrices=False)
        component_count = min(5, left.shape[1], singular.shape[0])
        coordinates = left[:, :component_count] * singular[:component_count]
        pca_distance = np.sqrt(
            np.sum(
                (coordinates - np.median(coordinates, axis=0, keepdims=True)) ** 2,
                axis=1,
            )
        )
    else:
        pca_distance = np.zeros(len(sample_ids))
    library_z = robust_z_scores(np.log10(library_sizes + 1))
    detected_z = robust_z_scores(detected_genes)
    pca_z = robust_z_scores(pca_distance)
    metadata_by_sample = {
        row.get("sample_id"): row for row in sample_metadata
    }
    metrics = []
    outliers = []
    for index, sample_id in enumerate(sample_ids):
        metadata = metadata_by_sample.get(sample_id, {})
        flagged_metrics = [
            name
            for name, value in (
                ("library_size", library_z[index]),
                ("detected_genes", detected_z[index]),
                ("pca_distance", pca_z[index]),
            )
            if abs(value) >= outlier_z_threshold
        ]
        flagged = bool(flagged_metrics)
        metrics.append(
            {
                "sample_id": sample_id,
                "dataset_id": metadata.get("dataset_id", "NA"),
                "group": metadata.get("group", "NA"),
                "batch": metadata.get("batch", "NA"),
                "subject_id": metadata.get("subject_id", "NA"),
                "library_size": int(library_sizes[index]),
                "detected_genes": int(detected_genes[index]),
                "library_size_robust_z": float(library_z[index]),
                "detected_genes_robust_z": float(detected_z[index]),
                "pca_distance_robust_z": float(pca_z[index]),
                "outlier_flag": str(flagged).lower(),
            }
        )
        outliers.append(
            {
                "sample_id": sample_id,
                "dataset_id": metadata.get("dataset_id", "NA"),
                "outlier_flag": str(flagged).lower(),
                "flagged_metrics": ";".join(flagged_metrics) or "none",
                "retained_for_analysis": "true",
                "required_action": (
                    "user_review_manifest"
                    if flagged
                    else "none"
                ),
            }
        )
    return metrics, outliers


def provenance_payload(config, dataset_id, branch, sample_ids, counts_path):
    references = config.get("references", {})
    bulk = config.get("bulk", {})
    return {
        "dataset_id": dataset_id,
        "entry_branch": branch,
        "sample_ids_in_analysis_order": list(sample_ids),
        "sample_count": len(sample_ids),
        "counts_input": str(counts_path),
        "quantification_method": (
            bulk.get("quantification_method") if branch == "fastq" else "provided_matrix"
        ),
        "strandedness": bulk.get("strandedness"),
        "reference": {
            key: references.get(key)
            for key in (
                "species",
                "genome_build",
                "annotation_release",
                "gene_id_space",
                "fasta",
                "gtf",
                "transcriptome_fasta",
                "tx2gene",
                "salmon_index",
                "star_index",
                "checksums_file",
            )
        },
    }


def write_json(path, payload):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
