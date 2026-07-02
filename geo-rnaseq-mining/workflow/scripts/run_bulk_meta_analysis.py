#!/usr/bin/env python3

import argparse
import json
import math
from pathlib import Path

import yaml

from multi_dataset_common import (
    META_FIELDS,
    analysis_strategy,
    collect_contrast_evidence,
    enabled_bulk_contrasts,
    included_plan_rows,
    leave_one_dataset_out,
    meta_analyze_evidence,
)
from preanalysis_common import read_tsv, write_tsv


LOO_SUMMARY_FIELDS = [
    "gene_id",
    "dataset_driven",
    "sign_stable",
    "significance_stable",
    "max_effect_change",
    "full_pooled_log2fc",
    "full_meta_padj",
    "excluded_dataset_count",
]
LOO_DETAIL_FIELDS = [
    "gene_id",
    "excluded_dataset",
    "pooled_log2fc",
    "meta_pvalue",
    "meta_padj",
    "significant",
]


def ensure_meta_compatibility(
    compatibility,
    analysis_id,
    dataset_ids,
    contrast_ids,
):
    indexed = {
        (row.get("dataset_id"), row.get("contrast_id")): row
        for row in compatibility
        if row.get("analysis_id") == analysis_id
    }
    failures = []
    for dataset_id in dataset_ids:
        for contrast_id in contrast_ids:
            row = indexed.get((dataset_id, contrast_id))
            if not row or row.get("compatible_for_meta_analysis") != "true":
                failures.append(
                    f"{dataset_id}/{contrast_id}:"
                    f"{row.get('incompatibility_reason') if row else 'missing'}"
                )
    if failures:
        raise RuntimeError(
            "Meta-analysis compatibility failed: " + "; ".join(failures)
        )


def run_meta_analysis(
    config,
    plan,
    contrasts,
    compatibility,
    analysis_id,
    result_root,
    output_dir,
    consensus_dir,
):
    if analysis_strategy(plan, analysis_id) != "per_dataset_meta":
        raise RuntimeError(f"{analysis_id} is not configured as per_dataset_meta")
    plan_rows = included_plan_rows(plan, analysis_id)
    validation = [
        row["dataset_id"] for row in plan_rows if row.get("role") == "validation"
    ]
    if validation:
        raise RuntimeError(
            f"Validation leakage into per_dataset_meta is forbidden: {validation}"
        )
    dataset_ids = [row["dataset_id"] for row in plan_rows]
    analysis_contrasts = enabled_bulk_contrasts(contrasts, analysis_id)
    if not analysis_contrasts:
        raise RuntimeError(f"No enabled bulk contrast exists for {analysis_id}")
    contrast_ids = [row["contrast_id"] for row in analysis_contrasts]
    ensure_meta_compatibility(
        compatibility,
        analysis_id,
        dataset_ids,
        contrast_ids,
    )
    settings = config["multi_dataset"]["meta"]
    method = settings["method"]
    alpha = float(settings["alpha"])
    min_studies = int(settings["min_studies"])
    effect_threshold = float(config["bulk"]["deseq2_abs_log2fc"])
    output_dir = Path(output_dir)
    consensus_dir = Path(consensus_dir)
    manifest = []
    for contrast in analysis_contrasts:
        contrast_id = contrast["contrast_id"]
        evidence = collect_contrast_evidence(
            dataset_ids,
            contrast_id,
            result_root,
        )
        results = meta_analyze_evidence(
            evidence,
            method,
            alpha,
            min_studies,
        )
        significant = [
            row
            for row in results
            if math.isfinite(row["meta_padj"])
            and row["meta_padj"] < alpha
            and abs(row["pooled_log2fc"]) >= effect_threshold
        ]
        contrast_dir = output_dir / contrast_id
        meta_path = contrast_dir / "meta_results.tsv"
        significant_path = contrast_dir / "meta_significant_results.tsv"
        write_tsv(meta_path, META_FIELDS, results)
        write_tsv(significant_path, META_FIELDS, significant)
        loo_summary, loo_detail = leave_one_dataset_out(
            evidence,
            method,
            alpha,
            min_studies,
            float(settings["loo_effect_change_threshold"]),
        )
        consensus_contrast = consensus_dir / contrast_id
        write_tsv(
            consensus_contrast / "leave_one_dataset_out_summary.tsv",
            LOO_SUMMARY_FIELDS,
            loo_summary,
        )
        write_tsv(
            consensus_contrast / "leave_one_dataset_out_details.tsv",
            LOO_DETAIL_FIELDS,
            loo_detail,
        )
        manifest.append(
            {
                "analysis_id": analysis_id,
                "contrast_id": contrast_id,
                "analysis_strategy": "per_dataset_meta",
                "meta_model": method,
                "dataset_ids": ";".join(dataset_ids),
                "meta_results": str(meta_path),
                "significant_results": str(significant_path),
                "loo_summary": str(
                    consensus_contrast / "leave_one_dataset_out_summary.tsv"
                ),
                "gene_count": str(len(results)),
                "significant_gene_count": str(len(significant)),
            }
        )
    manifest_fields = [
        "analysis_id",
        "contrast_id",
        "analysis_strategy",
        "meta_model",
        "dataset_ids",
        "meta_results",
        "significant_results",
        "loo_summary",
        "gene_count",
        "significant_gene_count",
    ]
    write_tsv(output_dir / "results_manifest.tsv", manifest_fields, manifest)
    write_tsv(
        output_dir / "meta_analysis_status.tsv",
        ["analysis_id", "analysis_strategy", "meta_model", "dataset_count"],
        [
            {
                "analysis_id": analysis_id,
                "analysis_strategy": "per_dataset_meta",
                "meta_model": method,
                "dataset_count": len(dataset_ids),
            }
        ],
    )
    (output_dir / ".complete").write_text(
        json.dumps(
            {
                "analysis_id": analysis_id,
                "strategy": "per_dataset_meta",
                "meta_model": method,
                "dataset_ids": dataset_ids,
                "contrast_ids": contrast_ids,
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
    parser = argparse.ArgumentParser(description="Run guarded per-dataset bulk Meta analysis.")
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
    run_meta_analysis(
        config,
        read_tsv(args.dataset_plan),
        read_tsv(args.contrasts),
        read_tsv(args.compatibility),
        args.analysis_id,
        args.result_root,
        args.output_dir,
        args.consensus_dir,
    )
    print(f"Completed per-dataset Meta analysis for {args.analysis_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
