#!/usr/bin/env python3

import argparse
from collections import Counter, defaultdict

import yaml

from preanalysis_common import (
    ISSUE_FIELDS,
    as_bool,
    is_missing,
    make_issue,
    pass_issue,
    read_tsv,
    rows_for_analysis,
    sort_issues,
    write_tsv,
)


def enabled_contrasts(contrasts, analysis_id):
    return [
        row
        for row in contrasts
        if row.get("analysis_id") == analysis_id
        and as_bool(row.get("enabled")) is True
    ]


def subject_count(rows, group):
    return len(
        {
            row.get("subject_id")
            for row in rows
            if row.get("group") == group and not is_missing(row.get("subject_id"))
        }
    )


def validate_dataset_plan(manifest, contrasts, plan, config):
    issues = []
    manifest_datasets = {row.get("dataset_id", "NA") for row in manifest}
    dominance_threshold = float(
        config["validation"]["dataset_dominance_fraction"]
    )
    compatibility = config["validation"].get("dataset_compatibility") or {}

    for plan_row in plan:
        dataset_id = plan_row.get("dataset_id", "NA")
        analysis_id = plan_row.get("analysis_id", "NA")
        if dataset_id not in manifest_datasets:
            issues.append(
                make_issue(
                    "error",
                    "dataset_plan",
                    "PLANNED_DATASET_NOT_FOUND",
                    f"dataset_plan references {dataset_id}, which is absent from the reviewed manifest.",
                    "Correct dataset_id or add reviewed manifest rows; datasets are not substituted automatically.",
                    analysis_id=analysis_id,
                    dataset_id=dataset_id,
                )
            )

    analysis_ids = sorted({row.get("analysis_id", "NA") for row in plan})
    for analysis_id in analysis_ids:
        included_plan = [
            row
            for row in plan
            if row.get("analysis_id") == analysis_id
            and as_bool(row.get("include")) is True
        ]
        if not included_plan:
            issues.append(
                make_issue(
                    "warning",
                    "dataset_plan",
                    "NO_INCLUDED_DATASETS",
                    f"analysis_id {analysis_id} has no included datasets.",
                    "Set include=true only after confirming the intended datasets.",
                    analysis_id=analysis_id,
                )
            )
            continue
        strategies = {row.get("analysis_strategy") for row in included_plan}
        if len(strategies) > 1:
            issues.append(
                make_issue(
                    "error",
                    "dataset_plan",
                    "MIXED_ANALYSIS_STRATEGIES",
                    f"analysis_id {analysis_id} contains multiple strategies: {sorted(strategies)}.",
                    "Choose one explicit strategy for the analysis or split it into separate analysis_id values.",
                    analysis_id=analysis_id,
                )
            )
        analysis_rows = rows_for_analysis(manifest, plan, analysis_id)
        role_rows = defaultdict(list)
        for row in included_plan:
            role_rows[row.get("role", "NA")].append(row)
        discovery_datasets = {
            row.get("dataset_id") for row in role_rows.get("discovery", [])
        }
        validation_rows = role_rows.get("validation", [])
        for validation_row in validation_rows:
            strategy = validation_row.get("analysis_strategy")
            same_model = strategy in {"joint_model", "per_dataset_meta"}
            shared_merge = (
                not is_missing(validation_row.get("merge_group"))
                and any(
                    row.get("merge_group") == validation_row.get("merge_group")
                    for row in role_rows.get("discovery", [])
                )
            )
            if discovery_datasets and (same_model or shared_merge):
                issues.append(
                    make_issue(
                        "error",
                        "dataset_plan",
                        "VALIDATION_DATA_IN_DISCOVERY_MODEL",
                        f"Validation dataset {validation_row.get('dataset_id')} is configured in the discovery analysis model.",
                        "Use stratified_validation or an independent analysis_id; validation data must not enter discovery estimation.",
                        analysis_id=analysis_id,
                        dataset_id=validation_row.get("dataset_id", "NA"),
                    )
                )

        dataset_counts = Counter(row.get("dataset_id") for row in analysis_rows)
        total = sum(dataset_counts.values())
        if total and len(dataset_counts) > 1:
            dominant_dataset, dominant_count = dataset_counts.most_common(1)[0]
            fraction = dominant_count / total
            if fraction >= dominance_threshold:
                issues.append(
                    make_issue(
                        "warning",
                        "dataset_plan",
                        "DATASET_SAMPLE_SIZE_DOMINANCE",
                        f"Dataset {dominant_dataset} contributes {fraction:.1%} of samples to {analysis_id}.",
                        "Review influence diagnostics and avoid interpreting a pooled estimate as balanced evidence.",
                        analysis_id=analysis_id,
                        dataset_id=dominant_dataset,
                        details={"fraction": fraction, "counts": dict(dataset_counts)},
                    )
                )

        for contrast in enabled_contrasts(contrasts, analysis_id):
            contrast_id = contrast.get("contrast_id", "NA")
            numerator = contrast.get("numerator")
            denominator = contrast.get("denominator")
            minimum = int(contrast.get("min_replicates_per_group", "1"))
            for plan_row in included_plan:
                dataset_id = plan_row.get("dataset_id")
                dataset_rows = [
                    row
                    for row in analysis_rows
                    if row.get("dataset_id") == dataset_id
                ]
                strategy = plan_row.get("analysis_strategy")
                if strategy in {"joint_model", "per_dataset_meta"}:
                    missing_groups = [
                        group
                        for group in (numerator, denominator)
                        if subject_count(dataset_rows, group) < minimum
                    ]
                    if missing_groups:
                        check_id = (
                            "JOINT_DATASET_MISSING_COMPARISON"
                            if strategy == "joint_model"
                            else "META_DATASET_NOT_ESTIMABLE"
                        )
                        severity = "critical" if strategy == "joint_model" else "error"
                        issues.append(
                            make_issue(
                                severity,
                                "dataset_plan",
                                check_id,
                                f"Dataset {dataset_id} cannot independently estimate {contrast_id}; insufficient groups {missing_groups}.",
                                "Correct the reviewed plan or add valid subject-level replicates; the strategy will not be changed automatically.",
                                analysis_id=analysis_id,
                                dataset_id=dataset_id,
                                contrast_id=contrast_id,
                            )
                        )

            joint_rows = [
                row
                for row in included_plan
                if row.get("analysis_strategy") == "joint_model"
            ]
            if len(joint_rows) > 1:
                joint_datasets = {row.get("dataset_id") for row in joint_rows}
                comparison_rows = [
                    row
                    for row in analysis_rows
                    if row.get("dataset_id") in joint_datasets
                    and row.get("group") in {numerator, denominator}
                ]
                groups_by_dataset = defaultdict(set)
                datasets_by_group = defaultdict(set)
                for row in comparison_rows:
                    groups_by_dataset[row.get("dataset_id")].add(row.get("group"))
                    datasets_by_group[row.get("group")].add(row.get("dataset_id"))
                complete_confounding = (
                    groups_by_dataset
                    and all(len(groups) == 1 for groups in groups_by_dataset.values())
                    and all(
                        len(datasets_by_group.get(group, set())) == 1
                        for group in (numerator, denominator)
                    )
                )
                if complete_confounding:
                    issues.append(
                        make_issue(
                            "critical",
                            "dataset_plan",
                            "DATASET_GROUP_COMPLETE_CONFOUNDING",
                            f"dataset and group are completely confounded for joint_model contrast {contrast_id}.",
                            "Stop the joint model and revise the user-confirmed plan; the workflow will not switch to Meta analysis automatically.",
                            analysis_id=analysis_id,
                            contrast_id=contrast_id,
                            details={
                                "groups_by_dataset": {
                                    key: sorted(value)
                                    for key, value in groups_by_dataset.items()
                                }
                            },
                        )
                    )

        merge_groups = defaultdict(list)
        for row in included_plan:
            merge_group = row.get("merge_group", "NA")
            if not is_missing(merge_group):
                merge_groups[merge_group].append(row.get("dataset_id"))
        for merge_group, dataset_ids in merge_groups.items():
            dataset_ids = sorted(set(dataset_ids))
            integration_rows = [
                row
                for row in included_plan
                if row.get("merge_group") == merge_group
                and row.get("analysis_strategy") == "single_cell_integration"
            ]
            if integration_rows and len(dataset_ids) < 2:
                issues.append(
                    make_issue(
                        "error",
                        "dataset_plan",
                        "INTEGRATION_REQUIRES_MULTIPLE_DATASETS",
                        f"merge_group {merge_group} has fewer than two datasets.",
                        "Add only user-confirmed datasets or use independent_only; "
                        "the workflow will not change strategy automatically.",
                        analysis_id=analysis_id,
                        dataset_id=";".join(dataset_ids),
                    )
                )
            if len(dataset_ids) < 2:
                continue
            data_types = {
                row.get("data_type")
                for row in analysis_rows
                if row.get("dataset_id") in dataset_ids
                and not is_missing(row.get("data_type"))
            }
            if len(data_types) > 1:
                single_cell_modalities = all(
                    any(
                        term in str(value).lower()
                        for term in ("scrna", "snrna", "single_cell", "single-cell")
                    )
                    for value in data_types
                )
                explicitly_allowed = (
                    integration_rows
                    and single_cell_modalities
                    and config["single_cell_integration"]["allow_scrna_snrna"]
                )
                if explicitly_allowed:
                    issues.append(
                        make_issue(
                            "warning",
                            "dataset_plan",
                            "SCRNA_SNRNA_INTEGRATION_REQUIRES_REVIEW",
                            f"merge_group {merge_group} explicitly combines "
                            f"modalities {sorted(data_types)}.",
                            "Review modality-specific conservation diagnostics; "
                            "integration is not evidence that cell and nucleus "
                            "profiles are biologically equivalent.",
                            analysis_id=analysis_id,
                            dataset_id=";".join(dataset_ids),
                        )
                    )
                else:
                    issues.append(
                        make_issue(
                            "critical",
                            "dataset_plan",
                            "INCOMPATIBLE_DATA_TYPES_MERGED",
                            f"merge_group {merge_group} contains multiple data_type values: {sorted(data_types)}.",
                            "Separate data types or explicitly authorize scRNA/snRNA "
                            "integration in both dataset_plan.tsv and config.yaml.",
                            analysis_id=analysis_id,
                            dataset_id=";".join(dataset_ids),
                        )
                    )
            missing_compatibility = [
                dataset_id
                for dataset_id in dataset_ids
                if dataset_id not in compatibility
            ]
            if missing_compatibility:
                issues.append(
                    make_issue(
                        "error",
                        "dataset_plan",
                        "DATASET_COMPATIBILITY_UNVERIFIABLE",
                        f"No explicit species/reference/gene-ID compatibility metadata for {missing_compatibility}.",
                        "Populate validation.dataset_compatibility in config.yaml with species, reference_genome, and gene_id_space.",
                        analysis_id=analysis_id,
                        dataset_id=";".join(missing_compatibility),
                    )
                )
            else:
                for field, check_id in (
                    ("species", "INCOMPATIBLE_SPECIES_MERGED"),
                    ("reference_genome", "INCOMPATIBLE_REFERENCE_GENOMES"),
                    ("gene_id_space", "INCOMPATIBLE_GENE_ID_SPACES"),
                ):
                    values = {
                        compatibility[dataset_id].get(field, "unknown")
                        for dataset_id in dataset_ids
                    }
                    if len(values) > 1 or "unknown" in values:
                        severity = "critical" if field == "species" else "error"
                        issues.append(
                            make_issue(
                                severity,
                                "dataset_plan",
                                check_id,
                                f"merge_group {merge_group} has incompatible or unknown {field}: {sorted(values)}.",
                                f"Confirm compatible {field} values explicitly; no conversion or liftover is performed automatically.",
                                analysis_id=analysis_id,
                                dataset_id=";".join(dataset_ids),
                            )
                        )
        for row in included_plan:
            if (
                row.get("analysis_strategy") == "single_cell_integration"
                and is_missing(row.get("merge_group"))
            ):
                issues.append(
                    make_issue(
                        "error",
                        "dataset_plan",
                        "INTEGRATION_MERGE_GROUP_REQUIRED",
                        f"Dataset {row.get('dataset_id')} requests integration "
                        "without a merge_group.",
                        "Set the user-confirmed merge_group; the program will not "
                        "assign one automatically.",
                        analysis_id=analysis_id,
                        dataset_id=row.get("dataset_id", "NA"),
                    )
                )
        if not any(
            item["analysis_id"] == analysis_id and item["status"] == "fail"
            for item in issues
        ):
            issues.append(
                pass_issue(
                    "dataset_plan",
                    "DATASET_PLAN_VALID",
                    f"Dataset plan for {analysis_id} passed configured compatibility checks.",
                    analysis_id=analysis_id,
                )
            )
    if not plan:
        issues.append(
            make_issue(
                "warning",
                "dataset_plan",
                "NO_DATASET_PLAN_ROWS",
                "No dataset plan rows are defined.",
                "Define dataset roles and analysis strategies before multi-dataset analysis.",
            )
        )
    return sort_issues(issues)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate reviewed dataset plan.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config, encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    issues = validate_dataset_plan(
        read_tsv(args.manifest),
        read_tsv(args.contrasts),
        read_tsv(args.dataset_plan),
        config,
    )
    write_tsv(args.output, ISSUE_FIELDS, issues)
    print(f"Wrote {len(issues)} dataset-plan validation records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
