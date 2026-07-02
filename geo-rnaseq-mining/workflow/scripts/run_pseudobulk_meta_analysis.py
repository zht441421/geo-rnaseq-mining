#!/usr/bin/env python3

import argparse
import math
from pathlib import Path

import yaml

from preanalysis_common import read_tsv, write_tsv
from pseudobulk_common import (
    analysis_strategy,
    enabled_scrna_pseudobulk_contrasts,
    included_plan_rows,
    pseudobulk_meta_for_contrast,
    safe_name,
    write_json,
)


META_FIELDS = [
    "cell_type",
    "gene_id",
    "gene_symbol",
    "pooled_log2fc",
    "pooled_se",
    "meta_pvalue",
    "meta_padj",
    "I2",
    "direction_consistency",
    "n_datasets",
    "n_subjects",
    "dataset_specific_effects",
]


def discover_cell_types(result_root, dataset_ids, contrast_id):
    cell_types = set()
    for dataset_id in dataset_ids:
        contrast_dir = Path(result_root) / dataset_id / "pseudobulk" / "deseq2" / contrast_id
        if contrast_dir.is_dir():
            for child in contrast_dir.iterdir():
                if child.is_dir() and (child / "deseq2_full_results.tsv").is_file():
                    cell_types.add(child.name)
    return sorted(cell_types)


def run_meta_or_validation(config, plan, contrasts, analysis_id, result_root, output_dir, mode):
    strategy = analysis_strategy(plan, analysis_id)
    expected = "per_dataset_meta" if mode == "meta" else "stratified_validation"
    if strategy != expected:
        raise RuntimeError(f"{analysis_id} is not configured as {expected}")
    plan_rows = included_plan_rows(plan, analysis_id)
    discovery_ids = [row["dataset_id"] for row in plan_rows if row.get("role") != "validation"]
    validation_ids = [row["dataset_id"] for row in plan_rows if row.get("role") == "validation"]
    if mode == "meta" and validation_ids:
        raise RuntimeError("validation datasets cannot enter per_dataset_meta discovery evidence")
    if mode == "validation" and (not discovery_ids or not validation_ids):
        raise RuntimeError("stratified_validation requires discovery and validation datasets")
    analysis_contrasts = enabled_scrna_pseudobulk_contrasts(contrasts, analysis_id)
    output_dir = Path(output_dir)
    manifest = []
    for contrast in analysis_contrasts:
        contrast_id = contrast["contrast_id"]
        cell_types = discover_cell_types(result_root, discovery_ids, contrast_id)
        for cell_type in cell_types:
            discovery = pseudobulk_meta_for_contrast(
                discovery_ids,
                contrast_id,
                cell_type,
                result_root,
                config,
            )
            for row in discovery:
                row["cell_type"] = cell_type
            if mode == "meta":
                rows = [
                    {field: row.get(field, "NA") for field in META_FIELDS}
                    for row in discovery
                ]
                path = output_dir / contrast_id / safe_name(cell_type) / "meta_results.tsv"
                write_tsv(path, META_FIELDS, rows)
                significant = [
                    row for row in rows
                    if _finite(row["meta_padj"])
                    and float(row["meta_padj"]) < float(config["multi_dataset"]["meta"]["alpha"])
                ]
                write_tsv(path.parent / "meta_significant_results.tsv", META_FIELDS, significant)
                manifest.append(
                    {
                        "analysis_id": analysis_id,
                        "contrast_id": contrast_id,
                        "cell_type": cell_type,
                        "result": str(path),
                        "mode": "per_dataset_meta",
                    }
                )
            else:
                validation = {
                    row["gene_id"]: row
                    for row in pseudobulk_meta_for_contrast(
                        validation_ids,
                        contrast_id,
                        cell_type,
                        result_root,
                        config,
                    )
                }
                fields = [
                    "cell_type",
                    "gene_id",
                    "discovery_log2fc",
                    "discovery_padj",
                    "validation_log2fc",
                    "validation_pvalue",
                    "direction_consistency",
                    "replication_status",
                    "discovery_dataset_effects",
                    "validation_dataset_effects",
                ]
                rows = []
                for row in discovery:
                    val = validation.get(row["gene_id"])
                    concordant = (
                        val is not None
                        and math.copysign(1, row["pooled_log2fc"])
                        == math.copysign(1, val["pooled_log2fc"])
                    )
                    rows.append(
                        {
                            "cell_type": cell_type,
                            "gene_id": row["gene_id"],
                            "discovery_log2fc": row["pooled_log2fc"],
                            "discovery_padj": row["meta_padj"],
                            "validation_log2fc": val["pooled_log2fc"] if val else "NA",
                            "validation_pvalue": val["meta_pvalue"] if val else "NA",
                            "direction_consistency": str(concordant).lower() if val else "NA",
                            "replication_status": (
                                "replicated"
                                if val
                                and concordant
                                and _finite(val["meta_pvalue"])
                                and float(val["meta_pvalue"]) < float(config["multi_dataset"]["stratified_validation"]["replication_alpha"])
                                else "not_replicated"
                            ),
                            "discovery_dataset_effects": row["dataset_specific_effects"],
                            "validation_dataset_effects": val["dataset_specific_effects"] if val else "{}",
                        }
                    )
                path = output_dir / contrast_id / safe_name(cell_type) / "stratified_validation.tsv"
                write_tsv(path, fields, rows)
                manifest.append(
                    {
                        "analysis_id": analysis_id,
                        "contrast_id": contrast_id,
                        "cell_type": cell_type,
                        "result": str(path),
                        "mode": "stratified_validation",
                    }
                )
    write_tsv(
        output_dir / "results_manifest.tsv",
        ["analysis_id", "contrast_id", "cell_type", "result", "mode"],
        manifest,
    )
    write_json(
        output_dir / ".complete",
        {"analysis_id": analysis_id, "mode": mode, "result_count": len(manifest)},
    )


def _finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--result-root", default="results/per_dataset")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--mode", choices=["meta", "validation"], required=True)
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    run_meta_or_validation(
        config,
        read_tsv(args.dataset_plan),
        read_tsv(args.contrasts),
        args.analysis_id,
        args.result_root,
        args.output_dir,
        args.mode,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
