#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd
import yaml

from preanalysis_common import read_tsv
from pseudobulk_common import (
    enabled_scrna_pseudobulk_contrasts,
    included_plan_rows,
    read_pseudobulk_metadata,
    validate_joint_preflight,
    write_json,
)
from single_cell_common import validate_raw_counts


def prepare_joint_pseudobulk(
    config,
    plan,
    contrasts,
    analysis_id,
    result_root,
    output_counts,
    output_metadata,
    output_provenance,
):
    plan_rows = included_plan_rows(plan, analysis_id)
    dataset_ids = [row["dataset_id"] for row in plan_rows]
    metadata_frames = []
    count_frames = []
    first_genes = None
    for dataset_id in dataset_ids:
        base = Path(result_root) / dataset_id / "pseudobulk" / "input"
        counts_path = base / "raw_counts.tsv"
        metadata_path = base / "sample_metadata.tsv"
        if not counts_path.is_file() or not metadata_path.is_file():
            raise RuntimeError(f"Missing pseudobulk input for {dataset_id}")
        metadata = read_pseudobulk_metadata(metadata_path)
        metadata = metadata.loc[metadata["eligibility"] == "eligible"].copy()
        counts = pd.read_csv(counts_path, sep="\t")
        validate_raw_counts(counts.iloc[:, 1:].to_numpy(), counts_path)
        if counts.columns[1:].tolist() != metadata["pseudobulk_id"].tolist():
            raise RuntimeError(f"Pseudobulk count/metadata order differs for {dataset_id}")
        genes = counts["gene_id"].astype(str).tolist()
        if first_genes is None:
            first_genes = genes
        elif genes != first_genes:
            raise RuntimeError("Pseudobulk gene IDs differ across datasets")
        metadata_frames.append(metadata)
        count_frames.append(counts)
    metadata_all = pd.concat(metadata_frames, ignore_index=True)
    validate_joint_preflight(metadata_all, plan, contrasts, analysis_id, config)
    combined = count_frames[0][["gene_id"]].copy()
    for counts in count_frames:
        combined = pd.concat([combined, counts.iloc[:, 1:]], axis=1)
    if combined.columns[1:].tolist() != metadata_all["pseudobulk_id"].tolist():
        raise RuntimeError("Combined pseudobulk count and metadata order differ")
    Path(output_counts).parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_counts, sep="\t", index=False, lineterminator="\n")
    metadata_all.to_csv(output_metadata, sep="\t", index=False, lineterminator="\n")
    write_json(
        output_provenance,
        {
            "analysis_id": analysis_id,
            "analysis_strategy": "joint_model",
            "dataset_ids": dataset_ids,
            "contrast_ids": [
                row["contrast_id"]
                for row in enabled_scrna_pseudobulk_contrasts(contrasts, analysis_id)
            ],
            "replicate_unit": "subject_id",
            "cell_replication_used": False,
        },
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--result-root", default="results/per_dataset")
    parser.add_argument("--output-counts", required=True)
    parser.add_argument("--output-metadata", required=True)
    parser.add_argument("--output-provenance", required=True)
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    prepare_joint_pseudobulk(
        config,
        read_tsv(args.dataset_plan),
        read_tsv(args.contrasts),
        args.analysis_id,
        args.result_root,
        args.output_counts,
        args.output_metadata,
        args.output_provenance,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
