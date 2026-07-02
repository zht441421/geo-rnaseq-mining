import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import patsy

from multi_dataset_common import (
    complete_dataset_group_confounding,
    meta_analyze_evidence,
)
from preanalysis_common import as_bool, is_missing


SCRNA_SCOPE = "scrna_pseudobulk"


def enabled_scrna_pseudobulk_contrasts(contrasts, analysis_id):
    return [
        row
        for row in contrasts
        if row.get("analysis_id") == analysis_id
        and row.get("data_scope") == SCRNA_SCOPE
        and as_bool(row.get("enabled")) is True
    ]


def included_plan_rows(plan, analysis_id=None):
    rows = [row for row in plan if as_bool(row.get("include")) is True]
    if analysis_id is not None:
        rows = [row for row in rows if row.get("analysis_id") == analysis_id]
    return rows


def analysis_strategy(plan, analysis_id):
    strategies = {
        row.get("analysis_strategy")
        for row in included_plan_rows(plan, analysis_id)
    }
    if len(strategies) != 1:
        raise ValueError(
            f"analysis_id {analysis_id} must define exactly one analysis_strategy"
        )
    return next(iter(strategies))


def read_pseudobulk_metadata(path):
    frame = pd.read_csv(path, sep="\t", dtype=str).fillna("NA")
    required = {
        "pseudobulk_id",
        "dataset_id",
        "subject_id",
        "sample_id",
        "cell_type",
        "group",
        "cell_count",
        "total_UMI",
        "detected_genes",
        "eligibility",
        "exclusion_reason",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing pseudobulk metadata columns: {sorted(missing)}")
    return frame


def eligible_metadata(metadata):
    return metadata.loc[
        (metadata["eligibility"] == "eligible")
        | (metadata.get("eligible_for_de", "false") == "true")
    ].copy()


def subject_counts_by_group(metadata, contrast):
    subset = metadata.loc[
        metadata["group"].isin([contrast["numerator"], contrast["denominator"]])
    ]
    grouped = (
        subset.groupby("group", observed=True)["subject_id"]
        .nunique()
        .to_dict()
    )
    return {
        contrast["numerator"]: int(grouped.get(contrast["numerator"], 0)),
        contrast["denominator"]: int(grouped.get(contrast["denominator"], 0)),
    }


def insufficient_subject_reasons(metadata, contrast, minimum):
    counts = subject_counts_by_group(metadata, contrast)
    return [
        f"insufficient_subjects:{group}:{count}<{minimum}"
        for group, count in counts.items()
        if count < minimum
    ]


def assert_no_subject_merging(metadata):
    bad = []
    for pseudobulk_id, frame in metadata.groupby("pseudobulk_id", observed=True):
        subjects = set(frame["subject_id"].astype(str))
        if len(subjects) != 1:
            bad.append(f"{pseudobulk_id}:{sorted(subjects)}")
    if bad:
        raise ValueError(
            "Pseudobulk samples must not merge different subject_id values: "
            + "; ".join(bad[:20])
        )


def validate_joint_preflight(metadata, plan, contrasts, analysis_id, config):
    strategy = analysis_strategy(plan, analysis_id)
    if strategy != "joint_model":
        raise RuntimeError(f"{analysis_id} is not configured as joint_model")
    plan_rows = included_plan_rows(plan, analysis_id)
    dataset_ids = [row["dataset_id"] for row in plan_rows]
    if len(dataset_ids) < 2:
        raise RuntimeError("combined pseudobulk joint model requires multiple datasets")
    if any(row.get("role") == "validation" for row in plan_rows):
        raise RuntimeError("validation datasets cannot enter combined pseudobulk joint model")
    analysis_contrasts = enabled_scrna_pseudobulk_contrasts(contrasts, analysis_id)
    if not analysis_contrasts:
        raise RuntimeError(f"No enabled {SCRNA_SCOPE} contrast exists for {analysis_id}")
    selected = metadata.loc[metadata["dataset_id"].isin(dataset_ids)].copy()
    manifest_like = selected.to_dict(orient="records")
    minimum = int(config["single_cell"]["pseudobulk"]["min_subjects_per_group"])
    issues = []
    for contrast in analysis_contrasts:
        if complete_dataset_group_confounding(
            manifest_like,
            contrast["numerator"],
            contrast["denominator"],
        ):
            issues.append(f"{contrast['contrast_id']}:dataset_group_complete_confounding")
        for dataset_id in dataset_ids:
            dataset_meta = selected.loc[selected["dataset_id"] == dataset_id]
            reasons = insufficient_subject_reasons(dataset_meta, contrast, minimum)
            if reasons:
                issues.append(f"{contrast['contrast_id']}:{dataset_id}:{';'.join(reasons)}")
        for cell_type, cell_meta in selected.groupby("cell_type", observed=True):
            comparison = cell_meta.loc[
                cell_meta["group"].isin([contrast["numerator"], contrast["denominator"]])
            ].copy()
            if comparison.empty:
                continue
            formula = contrast.get("design_formula") or "~ group"
            variables = [
                column
                for column in comparison.columns
                if column in formula.replace("~", " ").replace("+", " ").split()
            ]
            comparison = comparison.replace({"": np.nan, "NA": np.nan, "N/A": np.nan})
            try:
                matrix = patsy.dmatrix(
                    formula,
                    comparison,
                    return_type="dataframe",
                    NA_action="drop",
                )
            except Exception as error:
                issues.append(f"{contrast['contrast_id']}:{cell_type}:design_invalid:{error}")
                continue
            if len(matrix) != len(comparison):
                issues.append(f"{contrast['contrast_id']}:{cell_type}:design_rows_dropped")
            if np.linalg.matrix_rank(matrix.to_numpy()) != matrix.shape[1]:
                issues.append(f"{contrast['contrast_id']}:{cell_type}:design_matrix_not_full_rank")
    if issues:
        raise RuntimeError("Pseudobulk joint preflight failed: " + "; ".join(issues))
    return True


def read_dataset_pseudobulk_effects(result_root, dataset_id, contrast_id, cell_type):
    path = (
        Path(result_root)
        / dataset_id
        / "pseudobulk"
        / "deseq2"
        / contrast_id
        / safe_name(cell_type)
        / "deseq2_full_results.tsv"
    )
    if not path.is_file():
        return []
    frame = pd.read_csv(path, sep="\t")
    required = {"gene_id", "log2FoldChange", "lfcSE", "pvalue"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing DE result columns: {sorted(missing)}")
    evidence = []
    for row in frame.to_dict(orient="records"):
        try:
            effect = float(row["log2FoldChange"])
            se = float(row["lfcSE"])
            pvalue = float(row["pvalue"])
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in (effect, se, pvalue)) or se <= 0:
            continue
        evidence.append(
            {
                "gene_id": str(row["gene_id"]),
                "gene_symbol": row.get("gene_symbol", "NA"),
                "dataset_id": dataset_id,
                "log2FoldChange": effect,
                "lfcSE": se,
                "pvalue": pvalue,
                "sample_size": row.get("sample_size", 1),
            }
        )
    return evidence


def safe_name(value):
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))


def write_json(path, payload):
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def pseudobulk_meta_for_contrast(dataset_ids, contrast_id, cell_type, result_root, config):
    evidence = []
    for dataset_id in dataset_ids:
        evidence.extend(
            read_dataset_pseudobulk_effects(
                result_root,
                dataset_id,
                contrast_id,
                cell_type,
            )
        )
    results = meta_analyze_evidence(
        evidence,
        config["multi_dataset"]["meta"]["method"],
        float(config["multi_dataset"]["meta"]["alpha"]),
        int(config["multi_dataset"]["meta"]["min_studies"]),
    )
    for row in results:
        dataset_effects = json.loads(row["dataset_specific_effects"])
        row["n_datasets"] = row.pop("n_studies")
        row["n_subjects"] = sum(
            int(float(value.get("sample_size", 0)))
            for value in dataset_effects.values()
        )
    return results
