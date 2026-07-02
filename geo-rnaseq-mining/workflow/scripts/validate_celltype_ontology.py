#!/usr/bin/env python3

import argparse
import re
from collections import defaultdict
from pathlib import Path

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


METRIC_FIELDS = {
    "dataset_id",
    "sample_id",
    "subject_id",
    "author_label",
    "cell_count",
}


def is_single_cell(row):
    data_type = row.get("data_type", "").lower()
    return "scrna" in data_type or "snrna" in data_type or "single_cell" in data_type


def validate_celltype_ontology(
    manifest, contrasts, plan, ontology, config, metrics=None
):
    issues = []
    metrics = metrics or []
    barcode_pattern = re.compile(config["validation"]["barcode_subject_pattern"])
    min_cells = int(config["validation"]["min_cells_per_celltype_sample"])
    min_donors = int(config["validation"]["min_donors_per_celltype_group"])
    included_sc = [
        row
        for row in manifest
        if as_bool(row.get("include")) is True
        and row.get("review_status") == "confirmed"
        and is_single_cell(row)
    ]
    for row in included_sc:
        subject_id = row.get("subject_id", "NA")
        if is_missing(subject_id):
            issues.append(
                make_issue(
                    "error",
                    "single_cell",
                    "SINGLE_CELL_SUBJECT_ID_MISSING",
                    f"Single-cell sample {row.get('sample_id')} has no subject_id.",
                    "Enter the human-confirmed donor/subject identifier before pseudobulk or proportion analysis.",
                    dataset_id=row.get("dataset_id", "NA"),
                    sample_id=row.get("sample_id", "NA"),
                )
            )
        elif barcode_pattern.fullmatch(subject_id):
            issues.append(
                make_issue(
                    "error",
                    "single_cell",
                    "SUBJECT_ID_LOOKS_LIKE_BARCODE",
                    f"subject_id {subject_id!r} resembles a cell barcode.",
                    "Replace it with the biological donor identifier; cells are not independent replicates.",
                    dataset_id=row.get("dataset_id", "NA"),
                    sample_id=row.get("sample_id", "NA"),
                    subject_id=subject_id,
                )
            )

    mappings = defaultdict(list)
    for row in ontology:
        mappings[(row.get("dataset_id"), row.get("author_label"))].append(row)
    for (dataset_id, author_label), rows in mappings.items():
        targets = {
            (
                row.get("harmonized_level1"),
                row.get("harmonized_level2"),
                row.get("harmonized_level3"),
            )
            for row in rows
            if row.get("review_status") != "excluded"
        }
        if len(targets) > 1:
            issues.append(
                make_issue(
                    "error",
                    "celltype_ontology",
                    "CELLTYPE_ONE_TO_MANY_CONFLICT",
                    f"author_label {author_label!r} maps to multiple harmonized targets in {dataset_id}.",
                    "Keep author_label unchanged and resolve one reviewed mapping explicitly.",
                    dataset_id=dataset_id,
                    details={"targets": sorted(targets)},
                )
            )

    sc_analysis_ids = set()
    for contrast in contrasts:
        if (
            as_bool(contrast.get("enabled")) is True
            and contrast.get("data_scope")
            in {"scrna_pseudobulk", "scrna_meta", "cell_proportion"}
        ):
            sc_analysis_ids.add(contrast.get("analysis_id"))
    if included_sc and sc_analysis_ids and not metrics:
        for analysis_id in sorted(sc_analysis_ids):
            issues.append(
                make_issue(
                    "warning",
                    "single_cell",
                    "CELLTYPE_METRICS_MISSING",
                    f"Cell and donor sufficiency cannot be verified for {analysis_id}.",
                    "Run prepare_single_cell_dataset to derive strict runtime metrics before pseudobulk fitting, or configure a reviewed metrics file.",
                    analysis_id=analysis_id,
                )
            )
    if metrics:
        missing_columns = METRIC_FIELDS - set(metrics[0])
        if missing_columns:
            issues.append(
                make_issue(
                    "critical",
                    "single_cell",
                    "CELLTYPE_METRICS_HEADER_INVALID",
                    f"Cell-type metrics file is missing columns: {sorted(missing_columns)}.",
                    "Regenerate the derived metrics file with the documented exact columns.",
                )
            )
        else:
            manifest_by_sample = {
                row.get("sample_id"): row for row in included_sc
            }
            metric_labels = defaultdict(set)
            donors_by_dataset_label_group = defaultdict(set)
            for metric in metrics:
                dataset_id = metric.get("dataset_id", "NA")
                sample_id = metric.get("sample_id", "NA")
                subject_id = metric.get("subject_id", "NA")
                author_label = metric.get("author_label", "NA")
                metric_labels[dataset_id].add(author_label)
                manifest_row = manifest_by_sample.get(sample_id)
                if manifest_row is None:
                    issues.append(
                        make_issue(
                            "error",
                            "single_cell",
                            "CELL_METRIC_SAMPLE_NOT_FOUND",
                            f"Cell metrics reference unknown or excluded sample_id {sample_id}.",
                            "Correct the derived metrics source; reviewed sample_id values are not rewritten.",
                            dataset_id=dataset_id,
                            sample_id=sample_id,
                        )
                    )
                    continue
                if manifest_row.get("subject_id") != subject_id:
                    issues.append(
                        make_issue(
                            "error",
                            "single_cell",
                            "CELL_METRIC_SUBJECT_MISMATCH",
                            f"Metrics subject_id {subject_id!r} does not match reviewed subject_id {manifest_row.get('subject_id')!r}.",
                            "Regenerate metrics from reviewed metadata; never overwrite the reviewed manifest.",
                            dataset_id=dataset_id,
                            sample_id=sample_id,
                            subject_id=subject_id,
                        )
                    )
                try:
                    cell_count = int(metric.get("cell_count", ""))
                except ValueError:
                    cell_count = -1
                if cell_count < min_cells:
                    issues.append(
                        make_issue(
                            "error",
                            "single_cell",
                            "INSUFFICIENT_CELLS_PER_CELLTYPE_SAMPLE",
                            f"{sample_id}/{author_label} has {cell_count} cells; minimum is {min_cells}.",
                            "Review cell QC thresholds or exclude this sample-cell-type combination explicitly.",
                            dataset_id=dataset_id,
                            sample_id=sample_id,
                            subject_id=subject_id,
                        )
                    )
                donors_by_dataset_label_group[
                    (
                        dataset_id,
                        author_label,
                        manifest_row.get("group", "NA"),
                    )
                ].add(subject_id)

            ontology_labels = defaultdict(set)
            harmonized_values = defaultdict(set)
            for row in ontology:
                dataset_id = row.get("dataset_id")
                ontology_labels[dataset_id].add(row.get("author_label"))
                for field in (
                    "harmonized_level1",
                    "harmonized_level2",
                    "harmonized_level3",
                ):
                    if not is_missing(row.get(field)):
                        harmonized_values[dataset_id].add(row.get(field))
            for dataset_id, labels in metric_labels.items():
                for label in sorted(labels - ontology_labels[dataset_id]):
                    check_id = (
                        "AUTHOR_LABEL_POSSIBLY_OVERWRITTEN"
                        if label in harmonized_values[dataset_id]
                        else "AUTHOR_LABEL_UNMAPPED"
                    )
                    issues.append(
                        make_issue(
                            "error",
                            "celltype_ontology",
                            check_id,
                            f"Original author_label {label!r} from cell metrics is absent from ontology mappings.",
                            "Restore the exact author label in author_label and place harmonized names only in harmonized_level fields.",
                            dataset_id=dataset_id,
                        )
                    )
            for (
                dataset_id,
                author_label,
                group,
            ), donors in donors_by_dataset_label_group.items():
                if len(donors) < min_donors:
                    issues.append(
                        make_issue(
                            "error",
                            "single_cell",
                            "INSUFFICIENT_DONORS_PER_CELLTYPE_GROUP",
                            f"{dataset_id}/{author_label}/{group} has {len(donors)} donors; minimum is {min_donors}.",
                            "Add donor-level replication or exclude this cell-type contrast explicitly.",
                            dataset_id=dataset_id,
                            details={
                                "author_label": author_label,
                                "group": group,
                                "donors": sorted(donors),
                            },
                        )
                    )

    for analysis_id in sc_analysis_ids:
        rows = rows_for_analysis(manifest, plan, analysis_id)
        relevant = [row for row in rows if is_single_cell(row)]
        contrast_rows = [
            row
            for row in contrasts
            if row.get("analysis_id") == analysis_id
            and as_bool(row.get("enabled")) is True
        ]
        for contrast in contrast_rows:
            minimum = int(contrast.get("min_replicates_per_group", "1"))
            for group in (contrast.get("numerator"), contrast.get("denominator")):
                donors = {
                    row.get("subject_id")
                    for row in relevant
                    if row.get("group") == group
                    and not is_missing(row.get("subject_id"))
                }
                if len(donors) < minimum:
                    issues.append(
                        make_issue(
                            "error",
                            "single_cell",
                            "PSEUDOBULK_INSUFFICIENT_DONORS",
                            f"{analysis_id}/{group} has {len(donors)} donors; minimum is {minimum}.",
                            "Provide sufficient subject-level replication; cells cannot be counted as replicates.",
                            analysis_id=analysis_id,
                            contrast_id=contrast.get("contrast_id", "NA"),
                        )
                    )
    if not issues:
        issues.append(
            pass_issue(
                "celltype_ontology",
                "CELLTYPE_DESIGN_VALID",
                "Cell-type ontology and available donor/cell metrics passed validation.",
            )
        )
    return sort_issues(issues)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate cell-type ontology and single-cell replicate design."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--ontology", required=True)
    parser.add_argument("--celltype-metrics")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config, encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    metrics = (
        read_tsv(args.celltype_metrics)
        if args.celltype_metrics and Path(args.celltype_metrics).is_file()
        else []
    )
    issues = validate_celltype_ontology(
        read_tsv(args.manifest),
        read_tsv(args.contrasts),
        read_tsv(args.dataset_plan),
        read_tsv(args.ontology),
        config,
        metrics,
    )
    write_tsv(args.output, ISSUE_FIELDS, issues)
    print(f"Wrote {len(issues)} single-cell validation records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
