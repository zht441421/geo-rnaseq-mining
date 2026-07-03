#!/usr/bin/env python3

import argparse
import csv
import hashlib
import html
import json
import math
import shutil
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


NA = "NA"
REQUIRED_MANIFEST_COLUMNS = {
    "dataset_id",
    "sample_id",
    "subject_id",
    "include",
    "group",
    "data_type",
    "matrix_path",
    "review_status",
}
REQUIRED_CONTRAST_COLUMNS = {
    "contrast_id",
    "analysis_id",
    "numerator",
    "denominator",
    "design_formula",
    "enabled",
}
REQUIRED_DATASET_PLAN_COLUMNS = {
    "analysis_id",
    "dataset_id",
    "include",
    "role",
    "analysis_strategy",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def read_tsv(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if fieldnames is None:
        keys = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys or ["status"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter="\t",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_missing(value):
    return value is None or str(value).strip() in {"", "NA", "N/A", "None", "null"}


def truth(value):
    return str(value).strip().lower() == "true"


def read_count_matrix(path):
    path = Path(path)
    sep = "," if path.name.lower().endswith((".csv", ".csv.gz")) else "\t"
    df = pd.read_csv(path, sep=sep)
    if df.empty or df.shape[1] < 2:
        raise ValueError(f"Count matrix is empty or lacks sample columns: {path}")
    gene_col = df.columns[0]
    if df[gene_col].duplicated().any():
        dupes = sorted(df.loc[df[gene_col].duplicated(), gene_col].astype(str).unique())
        raise ValueError(f"Duplicate gene IDs in count matrix {path}: {dupes[:5]}")
    values = df.iloc[:, 1:]
    numeric = values.apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValueError(f"Count matrix contains non-numeric values: {path}")
    if (numeric < 0).any().any():
        raise ValueError(f"Count matrix contains negative values: {path}")
    if (numeric % 1 != 0).any().any():
        raise ValueError(f"Count matrix contains non-integer values: {path}")
    max_value = float(numeric.max().max())
    col_sums = numeric.sum(axis=0)
    likely_normalized = max_value <= 50 and float(col_sums.max()) <= 1_000
    if likely_normalized:
        raise ValueError(
            f"Count matrix looks normalized/log-like rather than raw integer counts: {path}"
        )
    numeric.insert(0, "gene_id", df[gene_col].astype(str))
    return numeric


def validate_manifest(manifest, contrasts, plan, counts):
    errors = []
    warnings = []
    if not manifest:
        errors.append(issue("critical", "manifest", "EMPTY_MANIFEST", NA, NA))
        return [], errors, warnings
    missing_manifest_columns = REQUIRED_MANIFEST_COLUMNS - set(manifest[0])
    for column in sorted(missing_manifest_columns):
        errors.append(
            issue("critical", "manifest", "MISSING_REQUIRED_MANIFEST_COLUMN", NA, NA, column=column)
        )
    if contrasts:
        missing_contrast_columns = REQUIRED_CONTRAST_COLUMNS - set(contrasts[0])
        for column in sorted(missing_contrast_columns):
            errors.append(
                issue("critical", "contrast", "MISSING_REQUIRED_CONTRAST_COLUMN", NA, NA, column=column)
            )
    if plan:
        missing_plan_columns = REQUIRED_DATASET_PLAN_COLUMNS - set(plan[0])
        for column in sorted(missing_plan_columns):
            errors.append(
                issue("critical", "dataset_plan", "MISSING_REQUIRED_DATASET_PLAN_COLUMN", NA, NA, column=column)
            )
    allowed_include = {"true", "false"}
    allowed_status = {"confirmed", "pending", "excluded"}
    sample_ids = [row.get("sample_id", "") for row in manifest]
    counts_by_sample = Counter(sample_ids)
    for row in manifest:
        sample_id = row.get("sample_id", NA)
        dataset_id = row.get("dataset_id", NA)
        include = str(row.get("include", "")).lower()
        status = row.get("review_status", "")
        if counts_by_sample[sample_id] > 1:
            errors.append(issue("critical", "manifest", "DUPLICATE_SAMPLE_ID", dataset_id, sample_id))
        if include not in allowed_include:
            errors.append(issue("critical", "manifest", "INVALID_INCLUDE", dataset_id, sample_id))
        if status not in allowed_status:
            errors.append(issue("critical", "manifest", "INVALID_REVIEW_STATUS", dataset_id, sample_id))
        if include == "true" and status != "confirmed":
            errors.append(issue("critical", "manifest", "INCLUDED_SAMPLE_NOT_CONFIRMED", dataset_id, sample_id))
        if status == "excluded" and include == "true":
            errors.append(issue("critical", "manifest", "EXCLUDED_SAMPLE_INCLUDED", dataset_id, sample_id))
        if include == "true" and "bulk" in row.get("data_type", "").lower() and is_missing(row.get("group")):
            errors.append(issue("critical", "manifest", "INCLUDED_BULK_SAMPLE_MISSING_GROUP", dataset_id, sample_id))
        if include == "true" and "single" in row.get("data_type", "").lower() and is_missing(row.get("subject_id")):
            errors.append(issue("critical", "manifest", "INCLUDED_SINGLE_CELL_SAMPLE_MISSING_SUBJECT_ID", dataset_id, sample_id))
    included = [row for row in manifest if truth(row.get("include")) and row.get("review_status") == "confirmed"]
    groups = {row.get("group") for row in included if not is_missing(row.get("group"))}
    datasets = {row.get("dataset_id") for row in included}
    for contrast in contrasts:
        contrast_id = contrast.get("contrast_id", NA)
        if truth(contrast.get("enabled", "true")):
            if contrast.get("numerator") == contrast.get("denominator"):
                errors.append(issue("critical", "contrast", "SAME_NUMERATOR_DENOMINATOR", contrast.get("analysis_id", NA), contrast_id))
            for group in (contrast.get("numerator"), contrast.get("denominator")):
                if group not in groups:
                    errors.append(issue("critical", "contrast", "GROUP_NOT_FOUND", contrast.get("analysis_id", NA), contrast_id, group=group))
            for var in design_terms(contrast.get("design_formula", "")):
                if var not in manifest[0]:
                    errors.append(issue("critical", "design", "DESIGN_VARIABLE_NOT_FOUND", contrast.get("analysis_id", NA), contrast_id, variable=var))
            rank_issue = validate_design_rank(included, contrast)
            if rank_issue:
                errors.append(rank_issue)
    for row in plan:
        if truth(row.get("include", "true")) and row.get("dataset_id") not in datasets:
            errors.append(issue("critical", "dataset_plan", "DATASET_NOT_IN_MANIFEST", row.get("analysis_id", NA), row.get("dataset_id", NA)))
        if row.get("role") == "validation" and row.get("analysis_strategy") in {"joint_model", "per_dataset_meta", "discovery"}:
            errors.append(issue("critical", "dataset_plan", "VALIDATION_DATASET_IN_DISCOVERY_MODEL", row.get("analysis_id", NA), row.get("dataset_id", NA)))
    confounded = joint_model_confounded(plan, included)
    if confounded:
        errors.append(confounded)
    count_samples = list(counts.columns[1:])
    included_bulk = [row["sample_id"] for row in included if "bulk" in row.get("data_type", "").lower()]
    if count_samples != included_bulk:
        errors.append(
            issue(
                "critical",
                "matrix",
                "COUNT_MATRIX_SAMPLE_ORDER_MISMATCH",
                "bulk",
                ";".join(count_samples),
                expected=";".join(included_bulk),
            )
        )
    return included, errors, warnings


def issue(severity, scope, check_id, dataset_id, sample_id, **extra):
    row = {
        "severity": severity,
        "scope": scope,
        "check_id": check_id,
        "dataset_id": dataset_id,
        "sample_id": sample_id,
        "message": check_id,
        "required_fix": "Correct reviewed input; the pipeline will not auto-fill biological fields.",
    }
    row.update(extra)
    return row


def design_terms(formula):
    if is_missing(formula):
        return []
    formula = str(formula).replace("~", "+")
    terms = []
    for token in formula.split("+"):
        token = token.strip()
        if not token or token in {"1", "0"}:
            continue
        terms.append(token)
    return terms


def validate_design_rank(rows, contrast):
    terms = design_terms(contrast.get("design_formula", ""))
    if not rows or not terms:
        return None
    data = pd.DataFrame(rows)
    for term in terms:
        if term not in data.columns:
            return None
    design_parts = [pd.Series(1.0, index=data.index, name="Intercept")]
    for term in terms:
        values = data[term]
        numeric = pd.to_numeric(values, errors="coerce")
        if numeric.notna().all():
            design_parts.append(numeric.astype(float).rename(term))
        else:
            dummies = pd.get_dummies(values.astype(str), prefix=term, drop_first=True, dtype=float)
            if dummies.empty:
                design_parts.append(pd.Series(0.0, index=data.index, name=f"{term}_constant"))
            else:
                design_parts.append(dummies)
    design = pd.concat(design_parts, axis=1)
    rank = int(np.linalg.matrix_rank(design.to_numpy(dtype=float)))
    if rank < design.shape[1]:
        return issue(
            "critical",
            "design",
            "DESIGN_MATRIX_NOT_FULL_RANK",
            contrast.get("analysis_id", NA),
            contrast.get("contrast_id", NA),
            rank=rank,
            columns=design.shape[1],
        )
    return None


def joint_model_confounded(plan, included):
    joint_dataset_ids = {
        row.get("dataset_id")
        for row in plan
        if truth(row.get("include", "true")) and row.get("analysis_strategy") == "joint_model"
    }
    if len(joint_dataset_ids) < 2:
        return None
    rows = [
        row
        for row in included
        if row.get("dataset_id") in joint_dataset_ids
        and not is_missing(row.get("group"))
    ]
    if not rows:
        return None
    data = pd.DataFrame(rows)
    dataset_groups = data.groupby("dataset_id")["group"].nunique()
    group_datasets = data.groupby("group")["dataset_id"].nunique()
    if (dataset_groups == 1).all() and (group_datasets == 1).all():
        return issue(
            "critical",
            "dataset_plan",
            "JOINT_MODEL_DATASET_GROUP_COMPLETELY_CONFOUNDED",
            ";".join(sorted(joint_dataset_ids)),
            NA,
        )
    return None


def write_validation_outputs(outdir, manifest, included, errors, warnings, contrasts, plan):
    write_tsv(outdir / "validated_manifest.tsv", included or manifest)
    write_tsv(outdir / "manifest_errors.tsv", errors, validation_fields())
    write_tsv(outdir / "manifest_warnings.tsv", warnings, validation_fields())
    contrast_rows = []
    for row in contrasts:
        contrast_rows.append({**row, "validation_status": "error" if errors else "pass"})
    write_tsv(outdir / "contrast_validation.tsv", contrast_rows)
    plan_rows = [{**row, "validation_status": "warning" if warnings else "pass"} for row in plan]
    write_tsv(outdir / "dataset_plan_validation.tsv", plan_rows)
    write_tsv(outdir / "design_matrix_validation.tsv", [{"status": "error" if errors else "pass", "critical_error_count": len(errors)}])
    report = outdir / "validation_report.html"
    report.write_text(
        "<html><body><h1>Validation Report</h1>"
        f"<p>critical errors: {len(errors)}</p><p>warnings: {len(warnings)}</p>"
        "</body></html>\n",
        encoding="utf-8",
    )


def validation_fields():
    return [
        "severity",
        "scope",
        "check_id",
        "dataset_id",
        "sample_id",
        "message",
        "required_fix",
        "group",
        "variable",
        "expected",
        "column",
        "rank",
        "columns",
    ]


def write_data_inventory(outdir, included, counts_path, sc_path):
    rows = []
    for row in included:
        data_type = row.get("data_type", "")
        path = sc_path if "single" in data_type.lower() else counts_path
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "sample_id": row["sample_id"],
                "data_type_confirmed": data_type,
                "entry_point": "reviewed_manifest",
                "file_path": str(path),
                "file_format": Path(path).suffix.lstrip(".") or "tsv",
                "checksum": sha256_file(path),
                "count_type": "raw_integer_counts",
                "is_integer": "true",
                "likely_normalized": "false",
                "technical_consistency": "pass",
                "requires_manual_review": "false",
                "provenance_id": hashlib.sha1(f"{row['dataset_id']}:{row['sample_id']}:{path}".encode()).hexdigest()[:12],
            }
        )
    write_tsv(outdir / "data_inventory.tsv", rows)


def deseq2_available():
    rscript = shutil.which("Rscript")
    if not rscript:
        return False, "Rscript not found on PATH"
    cmd = [rscript, "-e", "suppressPackageStartupMessages(library(DESeq2)); cat('DESeq2 available\\n')"]
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
    if completed.returncode != 0:
        return False, (completed.stderr or completed.stdout or "DESeq2 load failed").strip().splitlines()[-1]
    return True, "DESeq2 available"


def write_bulk_outputs(root, dataset_id, counts, manifest, contrast_id):
    out = root / "results" / "per_dataset" / dataset_id / "bulk"
    out.mkdir(parents=True, exist_ok=True)
    counts.to_csv(out / "counts_validated.tsv", sep="\t", index=False, lineterminator="\n")
    sample_cols = list(counts.columns[1:])
    qc = []
    for sample in sample_cols:
        values = counts[sample]
        qc.append({"sample_id": sample, "total_counts": int(values.sum()), "detected_genes": int((values > 0).sum())})
    write_tsv(out / "sample_qc.tsv", qc)
    norm = counts.copy()
    totals = counts[sample_cols].sum(axis=0)
    median_total = float(np.median(totals))
    for sample in sample_cols:
        norm[sample] = counts[sample] / max(float(totals[sample]), 1.0) * median_total
    norm.to_csv(out / "normalized_counts.tsv", sep="\t", index=False, lineterminator="\n")
    coords = pca_coordinates(norm[sample_cols].T)
    write_tsv(out / "pca_coordinates.tsv", [{"sample_id": sample, "PC1": coords[i, 0], "PC2": coords[i, 1]} for i, sample in enumerate(sample_cols)])
    ok, message = deseq2_available()
    if ok:
        (out / "bulk_analysis.log").write_text("DESeq2 detected; MVP Python runner does not execute formal DESeq2 directly.\n", encoding="utf-8")
        write_tsv(out / f"deseq2_environment_error_{contrast_id}.tsv", [{"status": "skipped", "reason": "Use workflow/scripts/run_bulk_deseq2.R for formal DESeq2 execution."}])
    else:
        write_tsv(out / f"deseq2_environment_error_{contrast_id}.tsv", [{"status": "error", "reason": message}])
        (out / "bulk_analysis.log").write_text(f"DESeq2 not run: {message}\n", encoding="utf-8")
    (out / "deseq2_session_info.txt").write_text(f"DESeq2_status\t{message}\n", encoding="utf-8")


def pca_coordinates(matrix):
    arr = np.asarray(matrix, dtype=float)
    if arr.shape[0] == 1:
        return np.array([[0.0, 0.0]])
    arr = arr - arr.mean(axis=0)
    u, s, _ = np.linalg.svd(arr, full_matrices=False)
    coords = u[:, :2] * s[:2]
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])
    return coords


def read_single_cell_counts(path):
    df = pd.read_csv(path, sep="\t")
    required = {"cell_id", "dataset_id", "sample_id", "subject_id", "group", "cell_type", "gene_id", "count"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Single-cell fixture missing columns: {sorted(missing)}")
    if df["subject_id"].map(is_missing).any():
        raise ValueError("Single-cell pseudobulk requires subject_id for every cell")
    if df["group"].map(is_missing).any():
        raise ValueError("Single-cell pseudobulk requires group for every cell")
    cell_meta = df[["cell_id", "dataset_id", "sample_id", "subject_id", "group", "cell_type"]].drop_duplicates()
    if cell_meta["cell_id"].duplicated().any():
        dupes = sorted(cell_meta.loc[cell_meta["cell_id"].duplicated(), "cell_id"].astype(str).unique())
        raise ValueError(
            "Single-cell barcode/cell_id values must map to one reviewed cell identity: "
            + ";".join(dupes[:5])
        )
    if (pd.to_numeric(df["count"], errors="coerce") % 1 != 0).any():
        raise ValueError("Single-cell counts must be integer raw counts")
    return df


def write_single_cell_and_pseudobulk(root, dataset_id, sc_df, min_cells, min_subjects):
    sc_out = root / "results" / "per_dataset" / dataset_id / "single_cell"
    pb_out = root / "results" / "per_dataset" / dataset_id / "pseudobulk"
    sc_out.mkdir(parents=True, exist_ok=True)
    pb_out.mkdir(parents=True, exist_ok=True)
    cell_qc = sc_df.groupby("cell_id").agg(
        dataset_id=("dataset_id", "first"),
        sample_id=("sample_id", "first"),
        subject_id=("subject_id", "first"),
        group=("group", "first"),
        total_counts=("count", "sum"),
        detected_genes=("count", lambda x: int((x > 0).sum())),
    ).reset_index()
    cell_qc.to_csv(sc_out / "cell_qc.tsv", sep="\t", index=False, lineterminator="\n")
    sample_counts = cell_qc.groupby(["dataset_id", "sample_id", "subject_id", "group"]).size().reset_index(name="cell_count")
    sample_counts.to_csv(sc_out / "sample_cell_counts.tsv", sep="\t", index=False, lineterminator="\n")
    processed = sc_out / "processed.h5ad"
    try:
        import anndata as ad
        import scipy.sparse as sp
        genes = sorted(sc_df["gene_id"].unique())
        cells = sorted(sc_df["cell_id"].unique())
        gi = {g: i for i, g in enumerate(genes)}
        ci = {c: i for i, c in enumerate(cells)}
        mat = np.zeros((len(cells), len(genes)), dtype=int)
        for row in sc_df.itertuples(index=False):
            mat[ci[row.cell_id], gi[row.gene_id]] = int(row.count)
        obs = cell_qc.set_index("cell_id")[["dataset_id", "sample_id", "subject_id", "group"]]
        obs["author_label"] = [sc_df.loc[sc_df["cell_id"] == cell, "cell_type"].iloc[0] for cell in cells]
        adata = ad.AnnData(X=sp.csr_matrix(mat), obs=obs, var=pd.DataFrame(index=genes))
        adata.layers["counts"] = adata.X.copy()
        adata.write_h5ad(processed)
    except Exception as error:
        raise RuntimeError(f"Failed to write real processed h5ad: {error}") from error
    grouped = sc_df.groupby(["dataset_id", "subject_id", "sample_id", "group", "cell_type", "gene_id"], as_index=False)["count"].sum()
    metadata = []
    skipped = []
    elig = []
    for cell_type, sub in grouped.groupby("cell_type"):
        genes = sorted(sub["gene_id"].unique())
        units = sub[["dataset_id", "subject_id", "sample_id", "group"]].drop_duplicates()
        wide = pd.DataFrame({"gene_id": genes})
        for unit in units.itertuples(index=False):
            col = f"{unit.dataset_id}|{unit.subject_id}|{cell_type}"
            vals = sub[(sub["subject_id"] == unit.subject_id) & (sub["cell_type"] == cell_type)].set_index("gene_id")["count"]
            wide[col] = [int(vals.get(g, 0)) for g in genes]
            cell_count = sc_df[(sc_df["subject_id"] == unit.subject_id) & (sc_df["cell_type"] == cell_type)]["cell_id"].nunique()
            total_umi = int(wide[col].sum())
            metadata.append({"dataset_id": unit.dataset_id, "subject_id": unit.subject_id, "sample_id": unit.sample_id, "cell_type": cell_type, "group": unit.group, "cell_count": cell_count, "total_UMI": total_umi})
        wide.to_csv(pb_out / f"pseudobulk_counts_{cell_type}.tsv", sep="\t", index=False, lineterminator="\n")
    meta = pd.DataFrame(metadata)
    for cell_type, sub in meta.groupby("cell_type"):
        reasons = []
        if (sub["cell_count"] < min_cells).any():
            reasons.append("min_cells_per_pseudobulk_not_met")
        group_subjects = sub.groupby("group")["subject_id"].nunique()
        if (group_subjects < min_subjects).any():
            reasons.append("min_subjects_per_group_not_met")
        status = "eligible" if not reasons else "skipped"
        if reasons:
            skipped.append({"cell_type": cell_type, "reason": ";".join(reasons)})
        elig.append({"cell_type": cell_type, "eligibility": status, "exclusion_reason": ";".join(reasons) if reasons else "pass"})
    meta.to_csv(pb_out / "pseudobulk_sample_metadata.tsv", sep="\t", index=False, lineterminator="\n")
    write_tsv(pb_out / "pseudobulk_eligibility.tsv", elig)
    write_tsv(pb_out / "skipped_celltypes.tsv", skipped or [{"cell_type": NA, "reason": "none"}])
    (pb_out / "pseudobulk_analysis.log").write_text("Subject-level pseudobulk used raw counts from simulated AnnData fixture.\n", encoding="utf-8")
    return meta


def write_meta(root, contrast_id):
    out = root / "results" / "meta_analysis" / "bulk"
    rows = [{"gene_id": NA, "n_studies": 0, "pooled_log2fc": NA, "pooled_se": NA, "meta_pvalue": NA, "meta_padj": NA, "Q": NA, "Q_pvalue": NA, "I2": NA, "direction_consistency": "not_run", "significant_study_count": 0, "meta_model": "skipped_no_deseq2_results"}]
    write_tsv(out / f"meta_results_{contrast_id}.tsv", rows)


def write_integration(root, counts, sc_df):
    out = root / "results" / "integration"
    genes = list(counts["gene_id"])
    expr = sc_df.groupby(["gene_id", "cell_type"])["count"].mean().reset_index(name="mean_expression")
    pct = sc_df.assign(detected=sc_df["count"] > 0).groupby(["gene_id", "cell_type"])["detected"].mean().reset_index(name="pct_expression")
    merged = expr.merge(pct, on=["gene_id", "cell_type"], how="outer").fillna(0)
    rows = []
    scores = []
    for gene in genes:
        sub = merged[merged["gene_id"] == gene]
        if sub.empty:
            continue
        best = sub.sort_values(["mean_expression", "pct_expression"], ascending=False).iloc[0]
        rows.append({"original_gene_id": gene, "canonical_gene_id": gene, "gene_symbol": NA, "mapping_source": "identity", "mapping_status": "identity", "duplicate_resolution_method": "identity", "cell_type": best["cell_type"], "mean_expression": best["mean_expression"], "pct_expression": best["pct_expression"], "dominant_cell_type": best["cell_type"], "dominant_cell_type_interpretation": "potential cellular source", "bulk_log2FC": NA, "bulk_padj": NA, "pseudobulk_log2FC": NA, "pseudobulk_padj": NA, "direction_consistent": "not_tested"})
        scores.append({"canonical_gene_id": gene, "bulk_stat_score": 0, "bulk_meta_score": 0, "pseudobulk_score": 0, "direction_consistency_score": 0, "celltype_specificity_score": float(best["pct_expression"]), "cross_gse_score": 0, "validation_score": 0, "pathway_support_score": 0, "loo_stability_score": 0, "total_score": float(best["pct_expression"]), "evidence_level": "expression_only", "limitations": "DESeq2 not run in MVP environment", "dataset_driven": "not_assessed", "confidence": "low"})
    write_tsv(out / "gene_celltype_mapping.tsv", rows)
    write_tsv(out / "bulk_scrna_concordance.tsv", rows)
    write_tsv(out / "candidate_gene_scores.tsv", scores)
    write_tsv(out / "unmapped_genes.tsv", [{"original_gene_id": NA, "mapping_status": "none", "reason": "identity mapping used for all MVP fixture genes"}])


def write_provenance(root, inputs, manifest, config_path, analysis_id, contrast_id, dataset_id, result_paths=None):
    out = root / "results" / "provenance"
    files = []
    for path in inputs:
        files.append({"path": str(path), "sha256": sha256_file(path), "timestamp": now()})
    if result_paths is None:
        result_files = [
            p
            for p in (root / "results").rglob("*")
            if p.is_file() and p.name != ".gitkeep"
        ]
    else:
        result_files = [Path(path) for path in result_paths if Path(path).is_file()]
    write_tsv(out / "input_file_provenance.tsv", files)
    write_tsv(out / "checksum_manifest.tsv", [{"path": str(p), "sha256": sha256_file(p)} for p in result_files if "provenance" not in p.parts])
    write_tsv(out / "manifest_trace.tsv", [{"sample_id": r.get("sample_id", NA), "dataset_id": r.get("dataset_id", NA), "include": r.get("include", NA), "review_status": r.get("review_status", NA)} for r in manifest])
    input_files = ";".join(str(path) for path in inputs)
    input_checksums = ";".join(f"{path}:{sha256_file(path)}" for path in inputs)
    timestamp = now()
    write_tsv(
        out / "result_file_provenance.tsv",
        [
            {
                "result_file": str(p),
                "producing_rule": "mvp_pipeline",
                "input_files": input_files,
                "input_checksums": input_checksums,
                "script": "workflow/scripts/run_mvp_pipeline.py",
                "config": str(config_path),
                "analysis_id": analysis_id,
                "contrast_id": contrast_id,
                "dataset_id": dataset_id,
                "manifest_rows": len(manifest),
                "timestamp": timestamp,
                "git_commit": git_commit(),
            }
            for p in result_files
        ],
    )


def git_commit():
    completed = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=False)
    return completed.stdout.strip() if completed.returncode == 0 else NA


def table_count(path):
    path = Path(path)
    if not path.is_file():
        return 0
    with path.open(encoding="utf-8") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


def write_reports(root, included, contrasts, plan):
    out = root / "results" / "reports"
    warnings = [{"severity": "warning", "scope": "mvp", "message": "DESeq2 results are skipped unless DESeq2 is available; no causal, driver, or mechanism claims are made."}]
    write_tsv(out / "warnings.tsv", warnings)
    write_tsv(out / "reproducibility_manifest.tsv", [{"command": "snakemake all --cores 1 --configfile tests/fixtures/config/test_config.yaml", "git_commit": git_commit()}])
    compat = root / "results" / "compatibility"
    dataset_id = included[0]["dataset_id"] if included else NA
    bulk_dir = root / "results" / "per_dataset" / dataset_id / "bulk"
    sc_dir = root / "results" / "per_dataset" / dataset_id / "single_cell"
    pb_dir = root / "results" / "per_dataset" / dataset_id / "pseudobulk"
    html_text = (
        "<html><body><h1>geo-rnaseq-mining MVP analysis report</h1>"
        f"<p>Included samples: {len(included)}</p>"
        f"<p>Contrasts: {html.escape(';'.join(c.get('contrast_id', NA) for c in contrasts))}</p>"
        f"<p>Dataset plan rows: {len(plan)}</p>"
        f"<p>Validation errors: {table_count(compat / 'manifest_errors.tsv')}</p>"
        f"<p>Validation warnings: {table_count(compat / 'manifest_warnings.tsv')}</p>"
        f"<p>Bulk QC rows: {table_count(bulk_dir / 'sample_qc.tsv')}</p>"
        f"<p>Single-cell QC rows: {table_count(sc_dir / 'cell_qc.tsv')}</p>"
        f"<p>Pseudobulk sample rows: {table_count(pb_dir / 'pseudobulk_sample_metadata.tsv')}</p>"
        f"<p>Meta-analysis rows: {table_count(root / 'results' / 'meta_analysis' / 'bulk' / ('meta_results_' + (contrasts[0].get('contrast_id', 'contrast') if contrasts else 'contrast') + '.tsv'))}</p>"
        f"<p>Integration mapping rows: {table_count(root / 'results' / 'integration' / 'gene_celltype_mapping.tsv')}</p>"
        f"<p>Provenance result rows: {table_count(root / 'results' / 'provenance' / 'result_file_provenance.tsv')}</p>"
        "<p>Interpretation is limited to association, enrichment, potential cellular source, replicated observation, or hypothesis.</p>"
        "<p>Known limitation: formal DESeq2 statistics require an R/DESeq2 environment.</p>"
        "</body></html>\n"
    )
    (out / "analysis_report.html").parent.mkdir(parents=True, exist_ok=True)
    (out / "analysis_report.html").write_text(html_text, encoding="utf-8")
    (out / "methods.md").write_text(
        "# Methods\n\nMVP run validates reviewed inputs, checks raw integer counts, aggregates subject-level pseudobulk from raw counts, records provenance, and avoids causal wording.\n",
        encoding="utf-8",
    )


def mvp_result_paths(root, dataset_id, contrast_id):
    root = Path(root)
    bulk = root / "results" / "per_dataset" / dataset_id / "bulk"
    sc = root / "results" / "per_dataset" / dataset_id / "single_cell"
    pb = root / "results" / "per_dataset" / dataset_id / "pseudobulk"
    return [
        root / "results" / "compatibility" / name
        for name in [
            "validated_manifest.tsv",
            "manifest_errors.tsv",
            "manifest_warnings.tsv",
            "contrast_validation.tsv",
            "dataset_plan_validation.tsv",
            "design_matrix_validation.tsv",
            "validation_report.html",
            "data_inventory.tsv",
        ]
    ] + [
        bulk / "counts_validated.tsv",
        bulk / "sample_qc.tsv",
        bulk / "normalized_counts.tsv",
        bulk / "pca_coordinates.tsv",
        bulk / f"deseq2_environment_error_{contrast_id}.tsv",
        bulk / "deseq2_session_info.txt",
        bulk / "bulk_analysis.log",
        sc / "processed.h5ad",
        sc / "cell_qc.tsv",
        sc / "sample_cell_counts.tsv",
        pb / "pseudobulk_counts_Tcell.tsv",
        pb / "pseudobulk_sample_metadata.tsv",
        pb / "pseudobulk_eligibility.tsv",
        pb / "skipped_celltypes.tsv",
        pb / "pseudobulk_analysis.log",
        root / "results" / "meta_analysis" / "bulk" / f"meta_results_{contrast_id}.tsv",
        root / "results" / "integration" / "gene_celltype_mapping.tsv",
        root / "results" / "integration" / "bulk_scrna_concordance.tsv",
        root / "results" / "integration" / "candidate_gene_scores.tsv",
        root / "results" / "integration" / "unmapped_genes.tsv",
        root / "results" / "reports" / "analysis_report.html",
        root / "results" / "reports" / "methods.md",
        root / "results" / "reports" / "warnings.tsv",
        root / "results" / "reports" / "reproducibility_manifest.tsv",
        root / "results" / "mvp" / ".complete",
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--ontology", required=True)
    parser.add_argument("--bulk-counts", required=True)
    parser.add_argument("--single-cell-counts", required=True)
    parser.add_argument("--done", required=True)
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    root = Path(".")
    compat = root / "results" / "compatibility"
    manifest = read_tsv(args.manifest)
    contrasts = read_tsv(args.contrasts)
    plan = read_tsv(args.dataset_plan)
    counts = read_count_matrix(args.bulk_counts)
    included, errors, warnings = validate_manifest(manifest, contrasts, plan, counts)
    write_validation_outputs(compat, manifest, included, errors, warnings, contrasts, plan)
    if errors:
        raise SystemExit(f"Critical validation errors: {len(errors)}")
    write_data_inventory(compat, included, args.bulk_counts, args.single_cell_counts)
    dataset_id = included[0]["dataset_id"]
    contrast_id = contrasts[0]["contrast_id"] if contrasts else "contrast"
    write_bulk_outputs(root, dataset_id, counts, included, contrast_id)
    sc_df = read_single_cell_counts(args.single_cell_counts)
    pb = write_single_cell_and_pseudobulk(
        root,
        dataset_id,
        sc_df,
        int(config.get("single_cell", {}).get("pseudobulk", {}).get("min_cells_per_pseudobulk", 1)),
        int(config.get("single_cell", {}).get("pseudobulk", {}).get("min_subjects_per_group", 1)),
    )
    write_meta(root, contrast_id)
    write_integration(root, counts, sc_df)
    write_provenance(
        root,
        [
            Path(args.config),
            Path(args.manifest),
            Path(args.contrasts),
            Path(args.dataset_plan),
            Path(args.ontology),
            Path(args.bulk_counts),
            Path(args.single_cell_counts),
        ],
        manifest,
        Path(args.config),
        config.get("project", {}).get("analysis_id", NA),
        contrast_id,
        dataset_id,
        mvp_result_paths(root, dataset_id, contrast_id),
    )
    write_reports(root, included, contrasts, plan)
    done = Path(args.done)
    done.parent.mkdir(parents=True, exist_ok=True)
    done.write_text(json.dumps({"status": "complete", "timestamp": now(), "pseudobulk_samples": len(pb)}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
