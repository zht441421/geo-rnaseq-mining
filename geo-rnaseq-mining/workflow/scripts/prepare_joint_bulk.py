#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import yaml

from bulk_common import active_bulk_rows, blocking_issues, validate_bulk_count_matrix
from multi_dataset_common import (
    analysis_strategy,
    dominant_dataset,
    duplicate_cross_dataset_identities,
    enabled_bulk_contrasts,
    included_plan_rows,
)
from preanalysis_common import (
    ISSUE_FIELDS,
    make_issue,
    pass_issue,
    read_tsv,
    write_tsv,
)
from validate_analysis_design import validate_design_matrices


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compatibility_blockers(rows, analysis_id, dataset_ids, contrast_ids):
    blockers = []
    indexed = {
        (row.get("dataset_id"), row.get("contrast_id")): row
        for row in rows
        if row.get("analysis_id") == analysis_id
    }
    for dataset_id in dataset_ids:
        for contrast_id in contrast_ids:
            row = indexed.get((dataset_id, contrast_id))
            if not row or row.get("compatible_for_joint_model") != "true":
                reason = (
                    row.get("incompatibility_reason")
                    if row
                    else "compatibility_record_missing"
                )
                blockers.append(
                    make_issue(
                        "critical",
                        "joint_model",
                        "JOINT_MODEL_COMPATIBILITY_FAILED",
                        f"{dataset_id}/{contrast_id} is not approved for joint modeling: {reason}.",
                        "Correct inputs or explicitly revise dataset_plan.tsv; the workflow will not change strategy.",
                        analysis_id=analysis_id,
                        dataset_id=dataset_id,
                        contrast_id=contrast_id,
                    )
                )
    return blockers


def prepare_joint_dataset(
    config,
    manifest,
    plan,
    contrasts,
    compatibility,
    analysis_id,
    dataset_root,
    output_counts,
    output_metadata,
    output_validation,
    output_provenance,
):
    plan_rows = included_plan_rows(plan, analysis_id)
    dataset_ids = [row["dataset_id"] for row in plan_rows]
    analysis_contrasts = enabled_bulk_contrasts(contrasts, analysis_id)
    contrast_ids = [row["contrast_id"] for row in analysis_contrasts]
    issues = []
    if not analysis_contrasts:
        issues.append(
            make_issue(
                "critical",
                "joint_model",
                "NO_ENABLED_BULK_CONTRAST",
                f"No enabled bulk contrast is defined for {analysis_id}.",
                "Define the reviewed contrast in config/contrasts.tsv.",
                analysis_id=analysis_id,
            )
        )
    if analysis_strategy(plan, analysis_id) != "joint_model":
        issues.append(
            make_issue(
                "critical",
                "joint_model",
                "JOINT_MODEL_NOT_SELECTED",
                f"{analysis_id} is not configured as joint_model.",
                "Set analysis_strategy explicitly in dataset_plan.tsv.",
                analysis_id=analysis_id,
            )
        )
    if len(dataset_ids) < 2:
        issues.append(
            make_issue(
                "critical",
                "joint_model",
                "JOINT_MODEL_REQUIRES_MULTIPLE_DATASETS",
                "A joint model requires at least two included datasets.",
                "Revise dataset_plan.tsv without changing strategy automatically.",
                analysis_id=analysis_id,
            )
        )
    validation_ids = [
        row["dataset_id"] for row in plan_rows if row.get("role") == "validation"
    ]
    if validation_ids:
        issues.append(
            make_issue(
                "critical",
                "joint_model",
                "VALIDATION_DATA_IN_DISCOVERY_MODEL",
                f"Validation datasets cannot enter a joint discovery model: {validation_ids}.",
                "Use stratified_validation in dataset_plan.tsv.",
                analysis_id=analysis_id,
            )
        )
    issues.extend(
        compatibility_blockers(
            compatibility,
            analysis_id,
            dataset_ids,
            contrast_ids,
        )
    )

    analysis_rows = [
        row
        for row in active_bulk_rows(manifest)
        if row.get("dataset_id") in set(dataset_ids)
    ]
    identities = duplicate_cross_dataset_identities(analysis_rows)
    if identities:
        issues.append(
            make_issue(
                "critical",
                "joint_model",
                "OVERLAPPING_SAMPLE_IDENTITIES",
                f"Cross-dataset sample identities overlap: {identities[:20]}.",
                "Resolve duplicate or overlapping samples manually.",
                analysis_id=analysis_id,
                details={"identities": identities},
            )
        )
    dominance = dominant_dataset(
        analysis_rows,
        float(config["validation"]["dataset_dominance_fraction"]),
    )
    if dominance:
        issues.append(
            make_issue(
                "warning",
                "joint_model",
                "DATASET_SAMPLE_SIZE_DOMINANCE",
                f"{dominance[0]} contributes {dominance[1]:.1%} of joint-model samples.",
                "Review influence diagnostics; do not interpret pooled evidence as balanced.",
                analysis_id=analysis_id,
                dataset_id=dominance[0],
                details={"fraction": dominance[1], "counts": dominance[2]},
            )
        )

    design_issues = [
        row
        for row in validate_design_matrices(manifest, contrasts, plan, config)
        if row.get("analysis_id") == analysis_id
    ]
    issues.extend(design_issues)

    count_frames = []
    metadata_frames = []
    first_gene_ids = None
    input_hashes = {}
    for dataset_id in dataset_ids:
        input_dir = Path(dataset_root) / dataset_id / "bulk" / "input"
        counts_path = input_dir / "raw_counts.tsv"
        metadata_path = input_dir / "sample_metadata.tsv"
        expected_rows = active_bulk_rows(manifest, dataset_id)
        expected_samples = [row["sample_id"] for row in expected_rows]
        frame, matrix_issues = validate_bulk_count_matrix(
            counts_path,
            expected_samples,
            dataset_id,
        )
        issues.extend(matrix_issues)
        if frame is None:
            continue
        gene_ids = frame["gene_id"].astype(str).tolist()
        if first_gene_ids is None:
            first_gene_ids = gene_ids
        elif gene_ids != first_gene_ids:
            issues.append(
                make_issue(
                    "critical",
                    "joint_model",
                    "JOINT_GENE_ID_ORDER_MISMATCH",
                    f"{dataset_id} gene IDs or their order differ from the first dataset.",
                    "Requantify with one reference/annotation or provide explicitly harmonized raw counts.",
                    analysis_id=analysis_id,
                    dataset_id=dataset_id,
                )
            )
        if not metadata_path.is_file():
            issues.append(
                make_issue(
                    "critical",
                    "joint_model",
                    "JOINT_SAMPLE_METADATA_MISSING",
                    f"Prepared metadata is missing for {dataset_id}: {metadata_path}.",
                    "Run independent per-dataset preparation and QC first.",
                    analysis_id=analysis_id,
                    dataset_id=dataset_id,
                )
            )
            continue
        metadata = pd.read_csv(metadata_path, sep="\t", dtype=str).fillna("NA")
        observed_samples = metadata.get("sample_id", pd.Series(dtype=str)).tolist()
        if observed_samples != expected_samples:
            issues.append(
                make_issue(
                    "critical",
                    "joint_model",
                    "JOINT_METADATA_SAMPLE_ORDER_MISMATCH",
                    f"{dataset_id} prepared metadata order differs from reviewed manifest.",
                    "Regenerate per-dataset inputs; samples are not silently reordered.",
                    analysis_id=analysis_id,
                    dataset_id=dataset_id,
                )
            )
        metadata["dataset"] = dataset_id
        metadata["dataset_id"] = dataset_id
        count_frames.append((dataset_id, frame))
        metadata_frames.append(metadata)
        input_hashes[str(counts_path)] = sha256_file(counts_path)
        input_hashes[str(metadata_path)] = sha256_file(metadata_path)

    write_tsv(output_validation, ISSUE_FIELDS, issues)
    provenance = {
        "analysis_id": analysis_id,
        "analysis_strategy": "joint_model",
        "dataset_ids": dataset_ids,
        "contrast_ids": contrast_ids,
        "input_sha256": input_hashes,
        "ordinary_combat_used": False,
        "blocking_issue_count": len(blocking_issues(issues)),
    }
    Path(output_provenance).parent.mkdir(parents=True, exist_ok=True)
    Path(output_provenance).write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if blocking_issues(issues):
        check_ids = sorted({row["check_id"] for row in blocking_issues(issues)})
        raise RuntimeError(
            f"Joint-model preflight failed for {analysis_id}: {', '.join(check_ids)}"
        )

    combined = count_frames[0][1][["gene_id"]].copy()
    for _, frame in count_frames:
        combined = pd.concat([combined, frame.iloc[:, 1:]], axis=1)
    metadata = pd.concat(metadata_frames, ignore_index=True)
    if combined.columns[1:].tolist() != metadata["sample_id"].tolist():
        raise RuntimeError("Combined count and metadata sample orders differ")
    Path(output_counts).parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_counts, sep="\t", index=False, lineterminator="\n")
    metadata.to_csv(output_metadata, sep="\t", index=False, lineterminator="\n")
    issues.append(
        pass_issue(
            "joint_model",
            "JOINT_MODEL_INPUTS_VALID",
            "Joint-model raw counts and metadata passed all hard gates.",
            analysis_id=analysis_id,
        )
    )
    write_tsv(output_validation, ISSUE_FIELDS, issues)
    return issues


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare guarded joint bulk inputs.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--compatibility", required=True)
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--dataset-root", default="results/per_dataset")
    parser.add_argument("--output-counts", required=True)
    parser.add_argument("--output-metadata", required=True)
    parser.add_argument("--output-validation", required=True)
    parser.add_argument("--output-provenance", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    prepare_joint_dataset(
        config,
        read_tsv(args.manifest),
        read_tsv(args.dataset_plan),
        read_tsv(args.contrasts),
        read_tsv(args.compatibility),
        args.analysis_id,
        args.dataset_root,
        args.output_counts,
        args.output_metadata,
        args.output_validation,
        args.output_provenance,
    )
    print(f"Prepared joint-model inputs for {args.analysis_id}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
