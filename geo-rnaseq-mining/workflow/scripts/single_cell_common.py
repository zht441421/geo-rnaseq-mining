import hashlib
import json
import math
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import anndata as ad
import matplotlib
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import sparse
from scipy.stats import median_abs_deviation

from preanalysis_common import as_bool, is_missing

matplotlib.use("Agg")


def is_single_cell_data_type(value):
    lowered = str(value or "").lower()
    return any(
        term in lowered
        for term in ("scrna", "snrna", "single_cell", "single-cell")
    )


def active_single_cell_rows(manifest, dataset_id=None):
    rows = [
        row
        for row in manifest
        if as_bool(row.get("include")) is True
        and row.get("review_status") == "confirmed"
        and is_single_cell_data_type(row.get("data_type"))
    ]
    if dataset_id is not None:
        rows = [row for row in rows if row.get("dataset_id") == dataset_id]
    return rows


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def input_fingerprint(path):
    path = Path(path)
    if path.is_file():
        return sha256_file(path)
    if path.is_dir():
        digest = hashlib.sha256()
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(str(child.relative_to(path)).encode())
            digest.update(sha256_file(child).encode())
        return digest.hexdigest()
    return "missing"


def resolve_single_cell_entry(path):
    path = Path(path)
    if not path.is_dir():
        return path
    direct_matrix = (
        (path / "matrix.mtx").exists()
        or (path / "matrix.mtx.gz").exists()
    )
    direct_barcodes = (
        (path / "barcodes.tsv").exists()
        or (path / "barcodes.tsv.gz").exists()
    )
    direct_features = any(
        (path / name).exists()
        for name in (
            "features.tsv",
            "features.tsv.gz",
            "genes.tsv",
            "genes.tsv.gz",
        )
    )
    if direct_matrix and direct_barcodes and direct_features:
        return path
    candidates = [
        path / "outs" / "filtered_feature_bc_matrix",
        path / "filtered_feature_bc_matrix",
        path / "outs" / "raw_feature_bc_matrix",
        path / "raw_feature_bc_matrix",
        path / "outs" / "filtered_feature_bc_matrix.h5",
        path / "filtered_feature_bc_matrix.h5",
        path / "outs" / "raw_feature_bc_matrix.h5",
        path / "raw_feature_bc_matrix.h5",
    ]
    existing = [candidate for candidate in candidates if candidate.exists()]
    if len(existing) != 1:
        raise ValueError(
            f"Cell Ranger directory {path} must contain exactly one recognized "
            f"matrix result; observed {len(existing)}"
        )
    return existing[0]


def convert_rds_to_h5ad(path, converter_script=None):
    script = (
        Path(converter_script)
        if converter_script
        else Path(__file__).with_name("convert_single_cell_rds.R")
    )
    if not script.exists():
        raise ValueError(f"RDS converter script does not exist: {script}")
    temporary = tempfile.NamedTemporaryFile(suffix=".h5ad", delete=False)
    temporary.close()
    output = Path(temporary.name)
    launcher = Path(__file__).with_name("run_rscript.py")
    command = [
        sys.executable,
        str(launcher),
        str(script),
        "--input",
        str(path),
        "--output",
        str(output),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0 or not output.exists():
        output.unlink(missing_ok=True)
        message = completed.stderr.strip() or completed.stdout.strip()
        raise ValueError(f"RDS conversion failed for {path}: {message}")
    return output


def ensure_gene_metadata(adata, config):
    original = (
        adata.var["gene_id_original"].astype(str)
        if "gene_id_original" in adata.var
        else pd.Series(adata.var_names.astype(str), index=adata.var_names)
    )
    if "gene_id_canonical" in adata.var:
        canonical = adata.var["gene_id_canonical"].astype(str)
        mapping_status = adata.var.get(
            "mapping_status",
            pd.Series("provided", index=adata.var_names),
        ).astype(str)
    else:
        canonical = original.copy()
        mapping_status = pd.Series("identity", index=adata.var_names, dtype=str)
    symbol_column = next(
        (
            column
            for column in ("gene_symbol", "gene_symbols", "symbol")
            if column in adata.var
        ),
        None,
    )
    symbols = (
        adata.var[symbol_column].astype(str)
        if symbol_column
        else original.copy()
    )
    reference_build = str(config["references"].get("genome_build") or "unknown")
    adata.var["gene_id_original"] = original.to_numpy()
    adata.var["gene_id_canonical"] = canonical.to_numpy()
    adata.var["gene_symbol"] = symbols.to_numpy()
    adata.var["reference_build"] = reference_build
    adata.var["mapping_status"] = mapping_status.to_numpy()
    return adata


def validate_raw_counts(matrix, source):
    values = matrix.data if sparse.issparse(matrix) else np.asarray(matrix).ravel()
    if values.size and (
        np.any(~np.isfinite(values))
        or np.any(values < 0)
        or np.any(~np.isclose(values, np.rint(values)))
    ):
        raise ValueError(
            f"{source} does not contain finite non-negative integer raw counts"
        )


def read_single_cell_entry(path, count_layer, config=None):
    source_path = Path(path)
    path = resolve_single_cell_entry(source_path)
    converted_path = None
    if path.is_dir():
        adata = sc.read_10x_mtx(
            path,
            var_names="gene_ids",
            make_unique=False,
            cache=False,
        )
    elif path.suffix.lower() == ".h5ad":
        adata = ad.read_h5ad(path)
        if count_layer not in adata.layers:
            raise ValueError(
                f"{path} is missing required raw counts layer {count_layer!r}"
            )
        adata.X = adata.layers[count_layer].copy()
    elif path.suffix.lower() in {".h5", ".hdf5"}:
        adata = sc.read_10x_h5(path)
    elif path.suffix.lower() == ".rds":
        converted_path = convert_rds_to_h5ad(
            path,
            (config or {}).get("single_cell", {}).get("rds_converter_script"),
        )
        adata = ad.read_h5ad(converted_path)
        if count_layer not in adata.layers:
            converted_path.unlink(missing_ok=True)
            raise ValueError(
                f"Converted RDS is missing required raw counts layer {count_layer!r}"
            )
        adata.X = adata.layers[count_layer].copy()
    else:
        raise ValueError(f"Unsupported single-cell entry: {path}")
    if path.suffix.lower() not in {".h5ad", ".rds"}:
        adata.layers[count_layer] = adata.X.copy()
    matrix = adata.X
    validate_raw_counts(matrix, source_path)
    if adata.var_names.has_duplicates:
        duplicates = [
            gene_id
            for gene_id, count in Counter(adata.var_names.astype(str)).items()
            if count > 1
        ]
        raise ValueError(f"{path} contains duplicate gene IDs: {duplicates[:20]}")
    if adata.obs_names.has_duplicates:
        raise ValueError(f"{path} contains duplicate cell barcodes")
    adata.var_names = adata.var_names.astype(str)
    adata.obs_names = adata.obs_names.astype(str)
    if sparse.issparse(adata.X):
        rounded = sparse.csr_matrix(adata.X.copy())
        rounded.data = np.rint(rounded.data).astype(np.int64)
        adata.X = rounded
    else:
        adata.X = sparse.csr_matrix(
            np.rint(np.asarray(adata.X)).astype(np.int64)
        )
    adata.layers[count_layer] = adata.X.copy()
    if config is not None:
        ensure_gene_metadata(adata, config)
    if converted_path is not None:
        converted_path.unlink(missing_ok=True)
    return adata


def read_cell_annotations(path):
    if not path:
        return pd.DataFrame()
    frame = pd.read_csv(path, sep="\t", dtype=str).fillna("NA")
    required = {"barcode", "sample_id", "author_label"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            f"Cell annotation file is missing columns: {sorted(missing)}"
        )
    if frame.duplicated(["sample_id", "barcode"]).any():
        raise ValueError(
            "Cell annotation file contains duplicate sample_id/barcode pairs"
        )
    return frame


def annotation_values(annotations, barcodes, sample_ids=None):
    values = []
    for index, barcode in enumerate(barcodes):
        matches = annotations.loc[annotations["barcode"] == barcode]
        if sample_ids is not None:
            matches = matches.loc[
                matches["sample_id"] == str(sample_ids[index])
            ]
        if len(matches) != 1:
            raise ValueError(
                f"Expected one annotation for barcode {barcode!r}, "
                f"observed {len(matches)}"
            )
        values.append(matches.iloc[0])
    return values


def ontology_mapping(ontology, dataset_id):
    mapping = {}
    for row in ontology:
        if (
            row.get("dataset_id") == dataset_id
            and row.get("review_status") == "confirmed"
        ):
            label = row.get("author_label")
            if label in mapping:
                raise ValueError(
                    f"Multiple confirmed ontology mappings for {dataset_id}/{label}"
                )
            mapping[label] = row
    return mapping


def attach_reviewed_metadata(
    adata,
    rows,
    config,
    annotations,
):
    sample_column = config["single_cell"]["sample_id_column"]
    label_column = config["single_cell"]["author_celltype_column"]
    rows_by_sample = {row["sample_id"]: row for row in rows}
    source_barcodes = adata.obs_names.astype(str)
    if sample_column in adata.obs:
        sample_ids = adata.obs[sample_column].astype(str)
    elif len(rows) == 1:
        sample_ids = pd.Series(
            rows[0]["sample_id"],
            index=adata.obs_names,
            dtype=str,
        )
    elif not annotations.empty:
        matched = annotation_values(annotations, source_barcodes)
        sample_ids = pd.Series(
            [row["sample_id"] for row in matched],
            index=adata.obs_names,
            dtype=str,
        )
    else:
        raise ValueError(
            "A shared single-cell object requires a reviewed sample_id column "
            "or cell_annotations_file"
        )
    unknown_samples = sorted(set(sample_ids) - set(rows_by_sample))
    if unknown_samples:
        raise ValueError(
            f"Single-cell object contains unknown sample IDs: {unknown_samples}"
        )
    if label_column in adata.obs:
        labels = adata.obs[label_column].astype(str)
    elif not annotations.empty:
        matched = annotation_values(
            annotations,
            source_barcodes,
            sample_ids.to_numpy(),
        )
        labels = pd.Series(
            [row["author_label"] for row in matched],
            index=adata.obs_names,
            dtype=str,
        )
    else:
        raise ValueError(
            f"Author cell-type column {label_column!r} is missing and no "
            "cell_annotations_file was supplied"
        )
    if labels.isin({"", "NA", "N/A", "null", "None"}).any():
        raise ValueError("Author cell-type labels contain missing values")
    adata.obs["source_barcode"] = source_barcodes
    adata.obs["original_barcode"] = source_barcodes
    adata.obs["sample_id"] = sample_ids.to_numpy()
    adata.obs["author_label"] = labels.to_numpy()
    for field in rows[0]:
        adata.obs[field] = [
            rows_by_sample[sample_id].get(field, "NA")
            for sample_id in adata.obs["sample_id"]
        ]
    adata.obs_names = pd.Index(
        [
            f"{dataset_id}:{sample_id}:{barcode}"
            for dataset_id, sample_id, barcode in zip(
                adata.obs["dataset_id"],
                adata.obs["sample_id"],
                adata.obs["source_barcode"],
            )
        ]
    )
    if adata.obs_names.has_duplicates:
        raise ValueError("Cell identities remain duplicated after sample prefixing")
    return adata


def load_reviewed_single_cell_dataset(
    manifest,
    ontology,
    config,
    dataset_id,
):
    rows = active_single_cell_rows(manifest, dataset_id)
    if not rows:
        raise ValueError(f"No confirmed included single-cell samples for {dataset_id}")
    if any(is_missing(row.get("subject_id")) for row in rows):
        raise ValueError("Every included single-cell sample requires subject_id")
    paths = defaultdict(list)
    for row in rows:
        path = row.get("matrix_path")
        if is_missing(path):
            raise ValueError(
                f"Single-cell sample {row['sample_id']} has no matrix_path"
            )
        paths[str(Path(path))].append(row)
    annotations = read_cell_annotations(
        config["single_cell"].get("cell_annotations_file")
    )
    objects = []
    fingerprints = {}
    for path, path_rows in paths.items():
        if not Path(path).exists():
            raise ValueError(f"Single-cell input does not exist: {path}")
        adata = read_single_cell_entry(
            path,
            config["single_cell"]["count_layer"],
            config,
        )
        adata = attach_reviewed_metadata(
            adata,
            path_rows,
            config,
            annotations,
        )
        objects.append(adata)
        fingerprints[path] = input_fingerprint(path)
    gene_orders = [item.var_names.astype(str).tolist() for item in objects]
    if any(order != gene_orders[0] for order in gene_orders[1:]):
        raise ValueError(
            "Single-cell sample gene IDs or order differ; automatic harmonization "
            "is prohibited"
        )
    combined = ad.concat(
        objects,
        axis=0,
        join="inner",
        merge="same",
        index_unique=None,
    )
    mapping = ontology_mapping(ontology, dataset_id)
    observed_labels = set(combined.obs["author_label"].astype(str))
    unmapped = sorted(observed_labels - set(mapping))
    if unmapped:
        raise ValueError(
            f"Author cell-type labels lack confirmed ontology mappings: {unmapped}"
        )
    for level in (
        "harmonized_level1",
        "harmonized_level2",
        "harmonized_level3",
    ):
        combined.obs[level] = [
            mapping[label].get(level, "NA")
            for label in combined.obs["author_label"].astype(str)
        ]
    return combined, fingerprints


def calculate_cell_qc(adata, config):
    raw = sparse.csr_matrix(adata.X)
    total_counts = np.asarray(raw.sum(axis=1)).ravel()
    detected_genes = np.asarray((raw > 0).sum(axis=1)).ravel()
    prefixes = tuple(config["single_cell"]["mitochondrial_gene_prefixes"])
    mitochondrial = np.array(
        [str(gene_id).startswith(prefixes) for gene_id in adata.var_names]
    )
    mito_counts = (
        np.asarray(raw[:, mitochondrial].sum(axis=1)).ravel()
        if mitochondrial.any()
        else np.zeros(adata.n_obs)
    )
    mito_percent = np.divide(
        100 * mito_counts,
        total_counts,
        out=np.zeros_like(total_counts, dtype=float),
        where=total_counts > 0,
    )
    settings = config["single_cell"]["qc"]
    retained = (
        (detected_genes >= int(settings["min_genes"]))
        & (detected_genes <= int(settings["max_genes"]))
        & (total_counts >= float(settings["min_counts"]))
        & (mito_percent <= float(settings["max_mito_percent"]))
    )
    qc = adata.obs[
        [
            "dataset_id",
            "sample_id",
            "subject_id",
            "group",
            "author_label",
            "source_barcode",
        ]
    ].copy()
    qc.insert(0, "cell_id", adata.obs_names.astype(str))
    qc["total_counts"] = total_counts
    qc["detected_genes"] = detected_genes
    qc["mitochondrial_percent"] = mito_percent
    qc["qc_retained"] = retained
    qc["doublet_score"] = np.nan
    qc["predicted_doublet"] = False
    if config["single_cell"]["scrublet"]["enabled"]:
        temporary = adata.copy()
        sc.pp.scrublet(
            temporary,
            expected_doublet_rate=float(
                config["single_cell"]["scrublet"]["expected_doublet_rate"]
            ),
            random_state=int(config["reproducibility"]["random_seed"]),
        )
        scores = temporary.obs["doublet_score"].to_numpy(dtype=float)
        predicted = temporary.obs["predicted_doublet"].to_numpy(dtype=bool)
        qc["doublet_score"] = scores
        qc["predicted_doublet"] = predicted
        retained &= ~predicted
        qc["qc_retained"] = retained
    return qc, retained


def aggregate_pseudobulk(adata, retained, config):
    obs = adata.obs.loc[retained].copy()
    if "counts" not in adata.layers:
        raise ValueError("AnnData is missing layers['counts'] for pseudobulk")
    validate_raw_counts(adata.layers["counts"], "pseudobulk counts layer")
    matrix = sparse.csr_matrix(adata.layers["counts"])[retained, :]
    pseudobulk_config = config["single_cell"].get("pseudobulk", {})
    if "cell_type" not in obs:
        if "harmonized_level2" in obs:
            obs["cell_type"] = obs["harmonized_level2"].astype(str)
        else:
            obs["cell_type"] = obs["author_label"].astype(str)
    extra = pseudobulk_config.get("extra_strata", []) or []
    missing_extra = [field for field in extra if field not in obs]
    if missing_extra:
        raise ValueError(f"Pseudobulk extra_strata columns unavailable: {missing_extra}")
    grouping = ["dataset_id", "subject_id", "group", "cell_type", *extra]
    groups = obs.groupby(grouping, sort=True, observed=True).indices
    count_columns = {}
    metadata = []
    min_cells = int(
        pseudobulk_config.get(
            "min_cells_per_pseudobulk",
            pseudobulk_config.get("min_cells", 1),
        )
    )
    min_total_counts = int(pseudobulk_config.get("min_total_counts", 0))
    min_detected_genes = int(pseudobulk_config.get("min_detected_genes", 0))
    for index, (key, indices) in enumerate(groups.items(), start=1):
        if len(grouping) == 1:
            key_values = (key,)
        else:
            key_values = tuple(key)
        values_by_field = dict(zip(grouping, key_values))
        dataset_id = values_by_field["dataset_id"]
        subject_id = values_by_field["subject_id"]
        group = values_by_field["group"]
        cell_type = values_by_field["cell_type"]
        subset = obs.iloc[indices]
        author_values = sorted(set(subset.get("author_label", pd.Series("NA", index=subset.index)).astype(str)))
        author_label = author_values[0] if len(author_values) == 1 else "multiple"
        pseudobulk_id = f"PB{index:05d}"
        cell_count = len(indices)
        aggregated = np.asarray(
            matrix[np.asarray(indices), :].sum(axis=0)
        ).ravel().astype(np.int64)
        count_columns[pseudobulk_id] = aggregated
        total_umi = int(aggregated.sum())
        detected_genes = int((aggregated > 0).sum())
        reasons = []
        if cell_count < min_cells:
            reasons.append("min_cells_per_pseudobulk")
        if total_umi < min_total_counts:
            reasons.append("min_total_counts")
        if detected_genes < min_detected_genes:
            reasons.append("min_detected_genes")
        eligibility = "eligible" if not reasons else "ineligible"
        sample_ids = sorted(set(subset["sample_id"].astype(str)))
        sample_id = sample_ids[0] if len(sample_ids) == 1 else "multiple"
        base = {
            field: (
                next(iter(field_values))
                if len(field_values := set(subset[field].astype(str))) == 1
                else "NA"
            )
            for field in (
                "condition",
                "tissue",
                "batch",
                "sex",
                "age",
                "timepoint",
                "treatment",
                "paired_group",
            )
            if field in obs
        }
        for field in extra:
            base[field] = values_by_field[field]
        metadata.append(
            {
                "pseudobulk_id": pseudobulk_id,
                "dataset_id": dataset_id,
                "subject_id": subject_id,
                "sample_id": sample_id,
                "group": group,
                "cell_type": cell_type,
                "author_label": author_label,
                "sample_ids": ";".join(sample_ids),
                "cell_count": cell_count,
                "total_UMI": total_umi,
                "detected_genes": detected_genes,
                "eligibility": eligibility,
                "exclusion_reason": ";".join(reasons) if reasons else "pass",
                "eligible_for_de": str(eligibility == "eligible").lower(),
                **base,
            }
        )
    counts = pd.DataFrame({"gene_id": adata.var_names.astype(str)})
    for pseudobulk_id, values in count_columns.items():
        counts[pseudobulk_id] = values
    return counts, pd.DataFrame(metadata)


def celltype_metrics(adata, qc):
    retained_ids = set(qc.loc[qc["qc_retained"], "cell_id"])
    retained = adata.obs_names.isin(retained_ids)
    rows = (
        adata.obs.loc[retained]
        .groupby(
            [
                "dataset_id",
                "sample_id",
                "subject_id",
                "author_label",
            ],
            observed=True,
        )
        .size()
        .reset_index(name="cell_count")
    )
    return rows


def normalize_for_visualization(adata, retained, config):
    output = adata[retained].copy()
    output.layers["counts"] = sparse.csr_matrix(output.X.copy())
    sc.pp.normalize_total(
        output,
        target_sum=float(config["single_cell"]["normalization"]["target_sum"]),
    )
    sc.pp.log1p(output)
    max_hvg = min(
        int(config["single_cell"]["normalization"]["highly_variable_genes"]),
        output.n_vars,
    )
    if output.n_obs >= 3 and output.n_vars >= 3:
        sc.pp.highly_variable_genes(
            output,
            n_top_genes=max_hvg,
            flavor="seurat",
        )
        n_components = min(
            int(config["single_cell"]["normalization"]["pca_components"]),
            output.n_obs - 1,
            max_hvg - 1,
        )
        if n_components >= 2:
            sc.pp.pca(
                output,
                n_comps=n_components,
                mask_var="highly_variable",
                random_state=int(config["reproducibility"]["random_seed"]),
            )
            if output.n_obs >= 10:
                neighbors = min(15, output.n_obs - 1)
                sc.pp.neighbors(
                    output,
                    n_neighbors=neighbors,
                    n_pcs=n_components,
                )
                sc.tl.umap(
                    output,
                    random_state=int(config["reproducibility"]["random_seed"]),
                )
    return output


REQUIRED_OBS_COLUMNS = (
    "dataset_id",
    "gse_id",
    "sample_id",
    "subject_id",
    "group",
    "batch",
    "technology",
    "tissue",
    "condition",
)


def attach_preprocessing_metadata(adata, rows, config, annotations):
    sample_column = config["single_cell"]["sample_id_column"]
    label_column = config["single_cell"]["author_celltype_column"]
    rows_by_sample = {row["sample_id"]: row for row in rows}
    original_barcodes = adata.obs_names.astype(str)
    if sample_column in adata.obs:
        sample_ids = adata.obs[sample_column].astype(str)
    elif len(rows) == 1:
        sample_ids = pd.Series(rows[0]["sample_id"], index=adata.obs_names)
    elif not annotations.empty:
        matched = annotation_values(annotations, original_barcodes)
        sample_ids = pd.Series(
            [row["sample_id"] for row in matched],
            index=adata.obs_names,
        )
    else:
        raise ValueError(
            "A shared single-cell object requires a reviewed sample_id column "
            "or cell_annotations_file"
        )
    unknown = sorted(set(sample_ids.astype(str)) - set(rows_by_sample))
    if unknown:
        raise ValueError(f"Single-cell object contains unknown sample IDs: {unknown}")
    if label_column in adata.obs:
        author_labels = adata.obs[label_column].astype(str)
    elif not annotations.empty:
        matched = annotation_values(
            annotations,
            original_barcodes,
            sample_ids.astype(str).to_numpy(),
        )
        author_labels = pd.Series(
            [row["author_label"] for row in matched],
            index=adata.obs_names,
        )
    else:
        author_labels = pd.Series("NA", index=adata.obs_names)
    adata.obs["original_barcode"] = original_barcodes
    adata.obs["source_barcode"] = original_barcodes
    adata.obs["sample_id"] = sample_ids.astype(str).to_numpy()
    adata.obs["author_label"] = author_labels.astype(str).to_numpy()
    for field in rows[0]:
        adata.obs[field] = [
            rows_by_sample[sample_id].get(field, "NA")
            for sample_id in adata.obs["sample_id"].astype(str)
        ]
    adata.obs["technology"] = [
        rows_by_sample[sample_id].get("technology")
        or rows_by_sample[sample_id].get("data_type")
        or "unknown"
        for sample_id in adata.obs["sample_id"].astype(str)
    ]
    for column in REQUIRED_OBS_COLUMNS:
        if column not in adata.obs:
            adata.obs[column] = "NA"
        adata.obs[column] = adata.obs[column].astype(str)
    adata.obs_names = pd.Index(
        [
            f"{dataset_id}:{sample_id}:{barcode}"
            for dataset_id, sample_id, barcode in zip(
                adata.obs["dataset_id"],
                adata.obs["sample_id"],
                adata.obs["original_barcode"],
            )
        ]
    )
    if adata.obs_names.has_duplicates:
        raise ValueError(
            "Cell identities remain duplicated after dataset/sample prefixing"
        )
    return adata


def load_single_cell_preprocessing_dataset(manifest, config, dataset_id):
    rows = active_single_cell_rows(manifest, dataset_id)
    if not rows:
        raise ValueError(f"No confirmed included single-cell samples for {dataset_id}")
    if any(is_missing(row.get("subject_id")) for row in rows):
        raise ValueError("Every included single-cell sample requires subject_id")
    paths = defaultdict(list)
    for row in rows:
        path = row.get("matrix_path")
        if is_missing(path):
            raise ValueError(
                f"Single-cell sample {row['sample_id']} has no matrix_path"
            )
        paths[str(Path(path))].append(row)
    annotations = read_cell_annotations(
        config["single_cell"].get("cell_annotations_file")
    )
    objects = []
    fingerprints = {}
    for path, path_rows in paths.items():
        if not Path(path).exists():
            raise ValueError(f"Single-cell input does not exist: {path}")
        current = read_single_cell_entry(
            path,
            config["single_cell"]["count_layer"],
            config,
        )
        current = attach_preprocessing_metadata(
            current,
            path_rows,
            config,
            annotations,
        )
        objects.append(current)
        fingerprints[path] = input_fingerprint(path)
    gene_orders = [
        item.var["gene_id_original"].astype(str).tolist()
        for item in objects
    ]
    if any(order != gene_orders[0] for order in gene_orders[1:]):
        raise ValueError(
            "Single-cell sample gene IDs or order differ; automatic harmonization "
            "is prohibited"
        )
    combined = ad.concat(
        objects,
        axis=0,
        join="inner",
        merge="same",
        index_unique=None,
    )
    combined.layers["counts"] = sparse.csr_matrix(
        combined.layers[config["single_cell"]["count_layer"]].copy()
    )
    combined.X = combined.layers["counts"].copy()
    ensure_gene_metadata(combined, config)
    return combined, fingerprints


def _gene_mask(adata, prefixes):
    symbols = adata.var["gene_symbol"].astype(str)
    originals = adata.var["gene_id_original"].astype(str)
    prefixes = tuple(prefixes)
    return np.asarray(
        [
            symbol.startswith(prefixes) or original.startswith(prefixes)
            for symbol, original in zip(symbols, originals)
        ],
        dtype=bool,
    )


def _percent_counts(matrix, mask, totals):
    if not mask.any():
        return np.zeros(matrix.shape[0], dtype=float)
    values = np.asarray(matrix[:, mask].sum(axis=1)).ravel()
    return np.divide(
        100.0 * values,
        totals,
        out=np.zeros_like(totals, dtype=float),
        where=totals > 0,
    )


def calculate_qc_metrics(adata, config):
    counts = sparse.csr_matrix(adata.layers["counts"])
    total_counts = np.asarray(counts.sum(axis=1)).ravel()
    n_genes = np.asarray((counts > 0).sum(axis=1)).ravel()
    qc_settings = config["single_cell"]["qc"]
    mt_mask = _gene_mask(
        adata,
        config["single_cell"]["mitochondrial_gene_prefixes"],
    )
    ribo_mask = _gene_mask(
        adata,
        qc_settings["gene_prefixes"]["ribosomal"],
    )
    hb_mask = _gene_mask(
        adata,
        qc_settings["gene_prefixes"]["hemoglobin"],
    )
    complexity = np.divide(
        np.log10(n_genes + 1),
        np.log10(total_counts + 1),
        out=np.zeros_like(total_counts, dtype=float),
        where=total_counts > 0,
    )
    metrics = pd.DataFrame(index=adata.obs_names)
    for column in REQUIRED_OBS_COLUMNS:
        metrics[column] = adata.obs[column].astype(str)
    metrics["original_barcode"] = adata.obs["original_barcode"].astype(str)
    metrics["author_label"] = adata.obs["author_label"].astype(str)
    metrics["total_counts"] = total_counts
    metrics["n_genes_by_counts"] = n_genes
    metrics["pct_counts_mt"] = _percent_counts(counts, mt_mask, total_counts)
    metrics["pct_counts_ribo"] = _percent_counts(
        counts,
        ribo_mask,
        total_counts,
    )
    metrics["pct_counts_hb"] = _percent_counts(counts, hb_mask, total_counts)
    metrics["complexity"] = complexity
    return metrics


def _doublet_with_scrublet(sample, settings, random_seed):
    temporary = sample.copy()
    sc.pp.scrublet(
        temporary,
        expected_doublet_rate=float(settings["expected_doublet_rate"]),
        random_state=random_seed,
    )
    return (
        temporary.obs["doublet_score"].to_numpy(dtype=float),
        temporary.obs["predicted_doublet"].to_numpy(dtype=bool),
    )


def _doublet_with_doubletdetection(sample, settings, random_seed):
    try:
        import doubletdetection
    except ImportError as error:
        raise RuntimeError(
            "doubletdetection is required for doublet.method=doubletdetection"
        ) from error
    classifier = doubletdetection.BoostClassifier(
        n_iters=int(settings["n_iterations"]),
        clustering_algorithm="leiden",
        standard_scaling=True,
        random_state=random_seed,
        verbose=False,
    )
    labels = classifier.fit(sample.layers["counts"]).predict(
        p_thresh=float(settings["pvalue_threshold"]),
        voter_thresh=float(settings["voter_threshold"]),
    )
    scores = classifier.doublet_score()
    return np.asarray(scores, dtype=float), np.asarray(labels == 1, dtype=bool)


def run_doublet_detection_by_sample(adata, config, detector=None):
    settings = config["single_cell"]["doublet"]
    metrics = pd.DataFrame(
        {
            "doublet_score": np.nan,
            "predicted_doublet": False,
            "doublet_method": "disabled",
            "doublet_status": "disabled",
        },
        index=adata.obs_names,
    )
    status_rows = []
    for sample_id, positions in adata.obs.groupby(
        "sample_id",
        sort=True,
        observed=True,
    ).indices.items():
        positions = np.asarray(positions)
        status = "disabled"
        method = settings["method"]
        if settings["enabled"]:
            if len(positions) < int(settings["min_cells"]):
                status = "not_estimable_too_few_cells"
            else:
                sample = adata[positions].copy()
                if detector is not None:
                    scores, predicted = detector(sample, str(sample_id), method)
                elif method == "scrublet":
                    scores, predicted = _doublet_with_scrublet(
                        sample,
                        settings["scrublet"],
                        int(config["reproducibility"]["random_seed"]),
                    )
                elif method == "doubletdetection":
                    scores, predicted = _doublet_with_doubletdetection(
                        sample,
                        settings["doubletdetection"],
                        int(config["reproducibility"]["random_seed"]),
                    )
                else:
                    raise ValueError(f"Unsupported doublet method: {method}")
                metrics.iloc[
                    positions,
                    metrics.columns.get_loc("doublet_score"),
                ] = scores
                metrics.iloc[
                    positions,
                    metrics.columns.get_loc("predicted_doublet"),
                ] = predicted
                status = "completed"
        metrics.iloc[
            positions,
            metrics.columns.get_loc("doublet_method"),
        ] = method
        metrics.iloc[
            positions,
            metrics.columns.get_loc("doublet_status"),
        ] = status
        status_rows.append(
            {
                "sample_id": sample_id,
                "method": method,
                "cell_count": len(positions),
                "status": status,
            }
        )
    return metrics, pd.DataFrame(status_rows)


def assess_ambient_rna_by_sample(adata, config):
    settings = config["single_cell"]["ambient_rna"]
    scores = pd.Series(np.nan, index=adata.obs_names, dtype=float)
    status_rows = []
    for sample_id, positions in adata.obs.groupby(
        "sample_id",
        sort=True,
        observed=True,
    ).indices.items():
        positions = np.asarray(positions)
        method = settings["method"]
        status = "disabled"
        if method == "low_count_profile":
            sample_counts = sparse.csr_matrix(
                adata.layers["counts"][positions, :]
            )
            totals = np.asarray(sample_counts.sum(axis=1)).ravel()
            cutoff = np.quantile(
                totals,
                float(settings["low_count_quantile"]),
            )
            background_cells = totals <= cutoff
            background = np.asarray(
                sample_counts[background_cells].sum(axis=0)
            ).ravel()
            background_total = background.sum()
            if background_total > 0:
                background = background / background_total
                cell_totals = np.maximum(totals, 1)
                cell_profiles = sample_counts.multiply(1 / cell_totals[:, None])
                sample_scores = np.asarray(cell_profiles @ background).ravel()
                scores.iloc[positions] = sample_scores
                status = "completed"
            else:
                status = "not_estimable_zero_background"
        elif method != "none":
            raise ValueError(f"Unsupported ambient RNA method: {method}")
        status_rows.append(
            {
                "sample_id": sample_id,
                "method": method,
                "cell_count": len(positions),
                "status": status,
            }
        )
    return scores, pd.DataFrame(status_rows)


def _mad_bounds(values, lower_mads, upper_mads):
    median = float(np.median(values))
    deviation = float(median_abs_deviation(values, scale="normal"))
    if not np.isfinite(deviation) or deviation == 0:
        return -np.inf, np.inf
    return (
        median - lower_mads * deviation,
        median + upper_mads * deviation,
    )


def apply_sample_qc_thresholds(metrics, config):
    settings = config["single_cell"]["qc"]
    strategy = settings["strategy"]
    hard = settings["hard"]
    mad = settings["mad"]
    metric_contract = {
        "total_counts": (
            hard["min_counts"],
            hard["max_counts"],
            True,
            True,
        ),
        "n_genes_by_counts": (
            hard["min_genes"],
            hard["max_genes"],
            True,
            True,
        ),
        "pct_counts_mt": (None, hard["max_pct_mt"], False, True),
        "pct_counts_ribo": (None, hard["max_pct_ribo"], False, True),
        "pct_counts_hb": (None, hard["max_pct_hb"], False, True),
        "complexity": (hard["min_complexity"], None, True, False),
    }
    retained = pd.Series(True, index=metrics.index)
    reasons = {cell_id: [] for cell_id in metrics.index}
    threshold_rows = []
    for sample_id, sample_frame in metrics.groupby(
        "sample_id",
        sort=True,
        observed=True,
    ):
        sample_index = sample_frame.index
        for metric, (
            hard_lower,
            hard_upper,
            use_mad_lower,
            use_mad_upper,
        ) in metric_contract.items():
            values = sample_frame[metric].to_numpy(dtype=float)
            mad_lower = -np.inf
            mad_upper = np.inf
            mad_applied = (
                mad["enabled"]
                and len(values) >= int(mad["min_cells"])
                and metric in mad["metrics"]
            )
            if mad_applied:
                mad_lower, mad_upper = _mad_bounds(
                    values,
                    float(mad["lower_n_mads"]),
                    float(mad["upper_n_mads"]),
                )
            lower_bounds = []
            upper_bounds = []
            if strategy in {"hard", "combined"} and hard_lower is not None:
                lower_bounds.append(float(hard_lower))
            if strategy in {"hard", "combined"} and hard_upper is not None:
                upper_bounds.append(float(hard_upper))
            if strategy in {"mad", "combined"} and mad_applied and use_mad_lower:
                lower_bounds.append(float(mad_lower))
            if strategy in {"mad", "combined"} and mad_applied and use_mad_upper:
                upper_bounds.append(float(mad_upper))
            effective_lower = max(lower_bounds) if lower_bounds else -np.inf
            effective_upper = min(upper_bounds) if upper_bounds else np.inf
            failures = (values < effective_lower) | (values > effective_upper)
            for cell_id in sample_index[failures]:
                reasons[cell_id].append(metric)
            retained.loc[sample_index[failures]] = False
            threshold_rows.append(
                {
                    "sample_id": sample_id,
                    "metric": metric,
                    "strategy": strategy,
                    "hard_lower": hard_lower,
                    "hard_upper": hard_upper,
                    "mad_lower": mad_lower if mad_applied else np.nan,
                    "mad_upper": mad_upper if mad_applied else np.nan,
                    "effective_lower": effective_lower,
                    "effective_upper": effective_upper,
                    "mad_applied": mad_applied,
                }
            )
    return (
        retained,
        pd.Series(
            [
                ";".join(reasons[cell_id]) if reasons[cell_id] else "pass"
                for cell_id in metrics.index
            ],
            index=metrics.index,
        ),
        pd.DataFrame(threshold_rows),
    )


def calculate_preprocessing_qc(adata, config, detector=None):
    metrics = calculate_qc_metrics(adata, config)
    doublets, doublet_status = run_doublet_detection_by_sample(
        adata,
        config,
        detector=detector,
    )
    ambient_scores, ambient_status = assess_ambient_rna_by_sample(adata, config)
    metrics = metrics.join(doublets)
    metrics["ambient_rna_score"] = ambient_scores
    retained, reasons, thresholds = apply_sample_qc_thresholds(metrics, config)
    if config["single_cell"]["doublet"]["exclude_predicted"]:
        doublet_fail = metrics["predicted_doublet"].astype(bool)
        retained &= ~doublet_fail
        reasons.loc[doublet_fail] = reasons.loc[doublet_fail].map(
            lambda value: (
                "predicted_doublet"
                if value == "pass"
                else f"{value};predicted_doublet"
            )
        )
    metrics.insert(0, "cell_id", metrics.index.astype(str))
    metrics["qc_retained"] = retained.to_numpy(dtype=bool)
    metrics["filter_reason"] = reasons.to_numpy()
    sample_summary = (
        metrics.groupby("sample_id", observed=True)
        .agg(
            input_cells=("cell_id", "size"),
            retained_cells=("qc_retained", "sum"),
            predicted_doublets=("predicted_doublet", "sum"),
        )
        .reset_index()
    )
    failed_samples = sample_summary.loc[
        sample_summary["retained_cells"] == 0,
        "sample_id",
    ].astype(str).tolist()
    return {
        "cell_qc": metrics,
        "retained": pd.Series(
            metrics["qc_retained"].to_numpy(dtype=bool),
            index=adata.obs_names,
        ),
        "thresholds": thresholds,
        "sample_summary": sample_summary,
        "doublet_status": doublet_status,
        "ambient_status": ambient_status,
        "failed_samples": failed_samples,
    }


def create_post_qc_object(adata, retained):
    output = adata[retained.to_numpy(dtype=bool)].copy()
    output.X = sparse.csr_matrix(output.layers["counts"].copy())
    output.uns["matrix_contract"] = {
        "X": "raw_counts",
        "counts_layer": "raw_nonnegative_integer_counts",
        "stage": "post_qc",
    }
    return output


def cluster_single_cell_object(post_qc, config):
    output = post_qc.copy()
    output.X = sparse.csr_matrix(output.layers["counts"].copy())
    sc.pp.normalize_total(
        output,
        target_sum=float(config["single_cell"]["normalization"]["target_sum"]),
    )
    sc.pp.log1p(output)
    output.layers["log_normalized"] = output.X.copy()
    max_hvg = min(
        int(config["single_cell"]["normalization"]["highly_variable_genes"]),
        output.n_vars,
    )
    if output.n_obs >= 3 and output.n_vars >= 3:
        sc.pp.highly_variable_genes(
            output,
            n_top_genes=max_hvg,
            flavor=config["single_cell"]["normalization"]["hvg_flavor"],
        )
        hvg_count = int(output.var["highly_variable"].sum())
        components = min(
            int(config["single_cell"]["normalization"]["pca_components"]),
            output.n_obs - 1,
            max(hvg_count - 1, 1),
        )
        if components >= 2:
            scaled = output[:, output.var["highly_variable"]].copy()
            sc.pp.scale(
                scaled,
                max_value=float(
                    config["single_cell"]["normalization"]["scale_max_value"]
                ),
            )
            sc.tl.pca(
                scaled,
                n_comps=components,
                random_state=int(config["reproducibility"]["random_seed"]),
            )
            output.obsm["X_pca_unintegrated"] = scaled.obsm["X_pca"].copy()
            output.obsm["X_pca"] = scaled.obsm["X_pca"].copy()
            output.uns["pca_unintegrated"] = scaled.uns["pca"].copy()
            if config["single_cell"]["normalization"]["store_scaled_layer"]:
                scaled_full = np.zeros(output.shape, dtype=np.float32)
                scaled_full[:, output.var["highly_variable"].to_numpy()] = scaled.X
                output.layers["scaled"] = scaled_full
            if output.n_obs >= 4:
                sc.pp.neighbors(
                    output,
                    n_neighbors=min(
                        int(config["single_cell"]["clustering"]["n_neighbors"]),
                        output.n_obs - 1,
                    ),
                    use_rep="X_pca_unintegrated",
                )
                sc.tl.umap(
                    output,
                    random_state=int(config["reproducibility"]["random_seed"]),
                )
                sc.tl.leiden(
                    output,
                    resolution=float(
                        config["single_cell"]["clustering"]["leiden_resolution"]
                    ),
                    key_added="leiden",
                    random_state=int(config["reproducibility"]["random_seed"]),
                    flavor="igraph",
                    n_iterations=2,
                    directed=False,
                )
    if "leiden" not in output.obs:
        output.obs["leiden"] = "0"
    output.obs["suggested_annotation"] = "unassigned"
    output.uns["matrix_contract"] = {
        "X": "log1p_normalized_expression",
        "counts_layer": "raw_nonnegative_integer_counts",
        "log_normalized_layer": "log1p_normalized_expression",
        "scaled_layer": (
            "scaled_expression"
            if "scaled" in output.layers
            else "not_stored; used transiently for PCA"
        ),
        "obsm/X_pca_unintegrated": "unintegrated_scaled_hvg_pca",
        "obsm/X_umap": "neighbor_graph_embedding",
        "stage": "clustered",
    }
    validate_raw_counts(output.layers["counts"], "clustered counts layer")
    return output


def cluster_markers(clustered, config):
    if clustered.obs["leiden"].nunique() < 2 or clustered.n_obs < 4:
        return pd.DataFrame(
            columns=[
                "cluster",
                "gene_id_original",
                "gene_id_canonical",
                "gene_symbol",
                "score",
                "logfoldchange",
                "pvalue",
                "padj",
            ]
        )
    sc.tl.rank_genes_groups(
        clustered,
        groupby="leiden",
        method=config["single_cell"]["annotation"]["marker_test"],
        use_raw=False,
        layer="log_normalized",
        pts=True,
    )
    frames = []
    for cluster in clustered.obs["leiden"].cat.categories:
        frame = sc.get.rank_genes_groups_df(clustered, group=cluster)
        frame = frame.head(
            int(config["single_cell"]["annotation"]["markers_per_cluster"])
        )
        by_name = clustered.var.reindex(frame["names"].astype(str))
        frames.append(
            pd.DataFrame(
                {
                    "cluster": str(cluster),
                    "gene_id_original": by_name["gene_id_original"].to_numpy(),
                    "gene_id_canonical": by_name["gene_id_canonical"].to_numpy(),
                    "gene_symbol": by_name["gene_symbol"].to_numpy(),
                    "score": frame["scores"].to_numpy(),
                    "logfoldchange": frame["logfoldchanges"].to_numpy(),
                    "pvalue": frame["pvals"].to_numpy(),
                    "padj": frame["pvals_adj"].to_numpy(),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def cluster_sample_composition(clustered):
    composition = (
        clustered.obs.groupby(["leiden", "sample_id"], observed=True)
        .size()
        .reset_index(name="cell_count")
    )
    totals = composition.groupby(
        "leiden",
        observed=True,
    )["cell_count"].transform("sum")
    composition["cluster_fraction"] = composition["cell_count"] / totals
    author = (
        clustered.obs.groupby(["leiden", "author_label"], observed=True)
        .size()
        .reset_index(name="author_label_cells")
    )
    return composition, author


def write_json(path, payload):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
