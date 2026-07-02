#!/usr/bin/env python3

import argparse
import json
import math
from pathlib import Path

import yaml

from multi_dataset_common import (
    collect_contrast_evidence,
    enabled_bulk_contrasts,
    included_plan_rows,
    leave_one_dataset_out,
    meta_analyze_evidence,
)
from preanalysis_common import read_tsv, write_tsv
from run_bulk_meta_analysis import (
    LOO_DETAIL_FIELDS,
    LOO_SUMMARY_FIELDS,
    ensure_meta_compatibility,
)


VALIDATION_FIELDS = [
    "gene_id",
    "gene_symbol",
    "discovery_effect",
    "discovery_se",
    "discovery_pvalue",
    "discovery_padj",
    "discovery_n_studies",
    "candidate_selected",
    "validation_effect",
    "validation_se",
    "validation_pvalue",
    "validation_padj",
    "validation_n_studies",
    "direction_concordance",
    "replication_status",
    "discovery_dataset_effects",
    "validation_dataset_effects",
]


def run_stratified_validation(
    config,
    plan,
    contrasts,
    compatibility,
    analysis_id,
    result_root,
    output_dir,
    consensus_dir,
):
    plan_rows = included_plan_rows(plan, analysis_id)
    strategies = {row.get("analysis_strategy") for row in plan_rows}
    if strategies != {"stratified_validation"}:
        raise RuntimeError(
            f"{analysis_id} is not configured exclusively as stratified_validation"
        )
    discovery_ids = [
        row["dataset_id"] for row in plan_rows if row.get("role") == "discovery"
    ]
    validation_ids = [
        row["dataset_id"] for row in plan_rows if row.get("role") == "validation"
    ]
    if not discovery_ids or not validation_ids:
        raise RuntimeError(
            "stratified_validation requires explicit discovery and validation datasets"
        )
    analysis_contrasts = enabled_bulk_contrasts(contrasts, analysis_id)
    if not analysis_contrasts:
        raise RuntimeError(f"No enabled bulk contrast exists for {analysis_id}")
    contrast_ids = [row["contrast_id"] for row in analysis_contrasts]
    ensure_meta_compatibility(
        compatibility,
        analysis_id,
        discovery_ids + validation_ids,
        contrast_ids,
    )
    meta_settings = config["multi_dataset"]["meta"]
    validation_settings = config["multi_dataset"]["stratified_validation"]
    method = meta_settings["method"]
    discovery_alpha = float(meta_settings["alpha"])
    validation_alpha = float(validation_settings["replication_alpha"])
    effect_threshold = float(config["bulk"]["deseq2_abs_log2fc"])
    require_direction = bool(validation_settings["require_same_direction"])
    output_dir = Path(output_dir)
    consensus_dir = Path(consensus_dir)
    manifest = []

    for contrast in analysis_contrasts:
        contrast_id = contrast["contrast_id"]
        discovery_evidence = collect_contrast_evidence(
            discovery_ids,
            contrast_id,
            result_root,
        )
        validation_evidence = collect_contrast_evidence(
            validation_ids,
            contrast_id,
            result_root,
        )
        discovery_results = meta_analyze_evidence(
            discovery_evidence,
            method,
            discovery_alpha,
            1,
        )
        validation_results = {
            row["gene_id"]: row
            for row in meta_analyze_evidence(
                validation_evidence,
                method,
                validation_alpha,
                1,
            )
        }
        output_rows = []
        for discovery in discovery_results:
            validation = validation_results.get(discovery["gene_id"])
            selected = (
                math.isfinite(discovery["meta_padj"])
                and discovery["meta_padj"] < discovery_alpha
                and abs(discovery["pooled_log2fc"]) >= effect_threshold
            )
            concordant = (
                validation is not None
                and math.copysign(1, discovery["pooled_log2fc"])
                == math.copysign(1, validation["pooled_log2fc"])
            )
            validation_significant = (
                validation is not None
                and math.isfinite(validation["meta_pvalue"])
                and validation["meta_pvalue"] < validation_alpha
            )
            if not selected:
                replication = "not_discovery_candidate"
            elif validation is None:
                replication = "not_tested_in_validation"
            elif require_direction and not concordant:
                replication = "direction_mismatch"
            elif not validation_significant:
                replication = "not_significant_in_validation"
            else:
                replication = "replicated"
            output_rows.append(
                {
                    "gene_id": discovery["gene_id"],
                    "gene_symbol": discovery["gene_symbol"],
                    "discovery_effect": discovery["pooled_log2fc"],
                    "discovery_se": discovery["pooled_se"],
                    "discovery_pvalue": discovery["meta_pvalue"],
                    "discovery_padj": discovery["meta_padj"],
                    "discovery_n_studies": discovery["n_studies"],
                    "candidate_selected": str(selected).lower(),
                    "validation_effect": (
                        validation["pooled_log2fc"] if validation else "NA"
                    ),
                    "validation_se": (
                        validation["pooled_se"] if validation else "NA"
                    ),
                    "validation_pvalue": (
                        validation["meta_pvalue"] if validation else "NA"
                    ),
                    "validation_padj": (
                        validation["meta_padj"] if validation else "NA"
                    ),
                    "validation_n_studies": (
                        validation["n_studies"] if validation else 0
                    ),
                    "direction_concordance": (
                        str(concordant).lower() if validation else "NA"
                    ),
                    "replication_status": replication,
                    "discovery_dataset_effects": discovery[
                        "dataset_specific_effects"
                    ],
                    "validation_dataset_effects": (
                        validation["dataset_specific_effects"]
                        if validation
                        else "{}"
                    ),
                }
            )
        contrast_dir = output_dir / contrast_id
        result_path = contrast_dir / "stratified_validation.tsv"
        write_tsv(result_path, VALIDATION_FIELDS, output_rows)
        write_tsv(
            contrast_dir / "replicated_candidates.tsv",
            VALIDATION_FIELDS,
            [
                row
                for row in output_rows
                if row["replication_status"] == "replicated"
            ],
        )
        loo_summary, loo_detail = leave_one_dataset_out(
            discovery_evidence,
            method,
            discovery_alpha,
            1,
            float(meta_settings["loo_effect_change_threshold"]),
        )
        consensus_contrast = consensus_dir / contrast_id
        write_tsv(
            consensus_contrast / "leave_one_discovery_dataset_out_summary.tsv",
            LOO_SUMMARY_FIELDS,
            loo_summary,
        )
        write_tsv(
            consensus_contrast / "leave_one_discovery_dataset_out_details.tsv",
            LOO_DETAIL_FIELDS,
            loo_detail,
        )
        manifest.append(
            {
                "analysis_id": analysis_id,
                "contrast_id": contrast_id,
                "analysis_strategy": "stratified_validation",
                "discovery_dataset_ids": ";".join(discovery_ids),
                "validation_dataset_ids": ";".join(validation_ids),
                "result": str(result_path),
                "candidate_count": sum(
                    row["candidate_selected"] == "true" for row in output_rows
                ),
                "replicated_count": sum(
                    row["replication_status"] == "replicated"
                    for row in output_rows
                ),
            }
        )

    fields = [
        "analysis_id",
        "contrast_id",
        "analysis_strategy",
        "discovery_dataset_ids",
        "validation_dataset_ids",
        "result",
        "candidate_count",
        "replicated_count",
    ]
    write_tsv(output_dir / "results_manifest.tsv", fields, manifest)
    (output_dir / ".complete").write_text(
        json.dumps(
            {
                "analysis_id": analysis_id,
                "strategy": "stratified_validation",
                "discovery_dataset_ids": discovery_ids,
                "validation_dataset_ids": validation_ids,
                "candidate_selection_uses_validation": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (consensus_dir / ".complete").write_text(
        f"analysis_id={analysis_id}\ncontrast_count={len(contrast_ids)}\n",
        encoding="utf-8",
    )
    return manifest


def parse_args():
    parser = argparse.ArgumentParser(description="Run strict discovery/validation analysis.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--compatibility", required=True)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--result-root", default="results/per_dataset")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--consensus-dir", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    run_stratified_validation(
        config,
        read_tsv(args.dataset_plan),
        read_tsv(args.contrasts),
        read_tsv(args.compatibility),
        args.analysis_id,
        args.result_root,
        args.output_dir,
        args.consensus_dir,
    )
    print(f"Completed stratified validation for {args.analysis_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
