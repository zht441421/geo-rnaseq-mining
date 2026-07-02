#!/usr/bin/env python3

import argparse
import re
from collections import Counter

import numpy as np
import pandas as pd
import patsy
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


DESIGN_FIELDS = ISSUE_FIELDS + [
    "design_formula",
    "n_rows",
    "n_columns",
    "rank",
    "full_rank",
]
CROSSTAB_FIELDS = [
    "analysis_id",
    "dataset_id",
    "group",
    "sample_count",
    "subject_count",
    "fraction_of_analysis",
]


def with_metrics(issue, formula="NA", n_rows=0, n_columns=0, rank=0, full_rank="NA"):
    enriched = issue.copy()
    enriched.update(
        {
            "design_formula": formula,
            "n_rows": str(n_rows),
            "n_columns": str(n_columns),
            "rank": str(rank),
            "full_rank": str(full_rank).lower()
            if isinstance(full_rank, bool)
            else str(full_rank),
        }
    )
    return enriched


def subset_rows(rows, contrast, manifest_columns):
    subset_column = contrast.get("subset_column", "NA")
    if is_missing(subset_column):
        return rows, None
    if subset_column not in manifest_columns:
        return [], f"subset_column {subset_column!r} is absent"
    subset_value = contrast.get("subset_value", "NA")
    return [row for row in rows if row.get(subset_column) == subset_value], None


def formula_variables(formula, columns):
    return [
        column
        for column in columns
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(column)}(?![A-Za-z0-9_])", formula)
    ]


def build_crosstab(manifest, plan):
    output = []
    analysis_ids = sorted(
        {
            row.get("analysis_id", "NA")
            for row in plan
            if as_bool(row.get("include")) is True
        }
    )
    for analysis_id in analysis_ids:
        rows = rows_for_analysis(manifest, plan, analysis_id)
        total = len(rows)
        counts = Counter(
            (row.get("dataset_id", "NA"), row.get("group", "NA")) for row in rows
        )
        for (dataset_id, group), sample_count in sorted(counts.items()):
            subjects = {
                row.get("subject_id")
                for row in rows
                if row.get("dataset_id") == dataset_id
                and row.get("group") == group
                and not is_missing(row.get("subject_id"))
            }
            output.append(
                {
                    "analysis_id": analysis_id,
                    "dataset_id": dataset_id,
                    "group": group,
                    "sample_count": str(sample_count),
                    "subject_count": str(len(subjects)),
                    "fraction_of_analysis": f"{sample_count / total:.6f}"
                    if total
                    else "0",
                }
            )
    return output


def validate_design_matrices(manifest, contrasts, plan, config):
    issues = []
    manifest = [
        {**row, "dataset": row.get("dataset_id", "NA")}
        for row in manifest
    ]
    manifest_columns = list(manifest[0]) if manifest else []
    max_missing = float(config["validation"]["max_missing_covariate_fraction"])
    for contrast in contrasts:
        if as_bool(contrast.get("enabled")) is not True:
            continue
        analysis_id = contrast.get("analysis_id", "NA")
        contrast_id = contrast.get("contrast_id", "NA")
        formula = contrast.get("design_formula", "")
        rows = rows_for_analysis(manifest, plan, analysis_id)
        rows, subset_error = subset_rows(rows, contrast, manifest_columns)
        if subset_error:
            issues.append(
                with_metrics(
                    make_issue(
                        "error",
                        "design_matrix",
                        "DESIGN_SUBSET_INVALID",
                        f"Cannot build design for {contrast_id}: {subset_error}.",
                        "Correct subset_column/subset_value manually.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                    ),
                    formula,
                )
            )
            continue
        comparison_rows = [
            row
            for row in rows
            if row.get("group")
            in {contrast.get("numerator"), contrast.get("denominator")}
        ]
        if not comparison_rows:
            issues.append(
                with_metrics(
                    make_issue(
                        "error",
                        "design_matrix",
                        "NO_DESIGN_SAMPLES",
                        f"No samples are available to build design for {contrast_id}.",
                        "Resolve dataset plan, subset, group, and inclusion metadata.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                    ),
                    formula,
                )
            )
            continue
        variables = formula_variables(formula, manifest_columns)
        for variable in variables:
            missing_count = sum(
                is_missing(row.get(variable)) for row in comparison_rows
            )
            fraction = missing_count / len(comparison_rows)
            if fraction > 0:
                severity = "error" if fraction > max_missing else "warning"
                issues.append(
                    with_metrics(
                        make_issue(
                            severity,
                            "design_matrix",
                            "SEVERE_MISSING_COVARIATE"
                            if severity == "error"
                            else "MISSING_COVARIATE",
                            f"Covariate {variable!r} is missing in {missing_count}/{len(comparison_rows)} samples ({fraction:.1%}).",
                            "Complete the reviewed covariate or revise the formula explicitly; rows are not imputed.",
                            analysis_id=analysis_id,
                            contrast_id=contrast_id,
                            details={"variable": variable, "missing_fraction": fraction},
                        ),
                        formula,
                    )
                )
            observed = {
                row.get(variable)
                for row in comparison_rows
                if not is_missing(row.get(variable))
            }
            if len(observed) <= 1:
                issues.append(
                    with_metrics(
                        make_issue(
                            "error",
                            "design_matrix",
                            "ZERO_VARIANCE_COVARIATE",
                            f"Design covariate {variable!r} has no variation.",
                            "Remove the covariate from the confirmed formula or provide a design with variation.",
                            analysis_id=analysis_id,
                            contrast_id=contrast_id,
                            details={"variable": variable, "values": sorted(observed)},
                        ),
                        formula,
                    )
                )
        if as_bool(contrast.get("paired")) is True and not re.search(
            r"\b(subject_id|paired_group)\b", formula
        ):
            issues.append(
                with_metrics(
                    make_issue(
                        "warning",
                        "design_matrix",
                        "PAIRED_FACTOR_NOT_IN_FORMULA",
                        f"Paired contrast {contrast_id} formula does not reference subject_id or paired_group.",
                        "Confirm that the paired blocking factor is represented in the design formula.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                    ),
                    formula,
                )
            )
        frame = pd.DataFrame(comparison_rows)
        frame = frame.astype(object)
        frame = frame.where(
            ~frame.isin({"", "NA", "N/A", "null", "None"}),
            np.nan,
        )
        if "age" in variables:
            numeric_age = pd.to_numeric(frame["age"], errors="coerce")
            if numeric_age.notna().sum() == frame["age"].notna().sum():
                frame["age"] = numeric_age
        try:
            matrix = patsy.dmatrix(
                formula,
                frame,
                return_type="dataframe",
                NA_action="drop",
            )
        except Exception as error:
            issues.append(
                with_metrics(
                    make_issue(
                        "error",
                        "design_matrix",
                        "DESIGN_FORMULA_INVALID",
                        f"Design formula for {contrast_id} cannot be evaluated: {error}",
                        "Correct variable names and formula syntax manually.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                        details={"available_columns": manifest_columns},
                    ),
                    formula,
                )
            )
            continue
        n_rows, n_columns = matrix.shape
        rank = int(np.linalg.matrix_rank(matrix.to_numpy()))
        full_rank = rank == n_columns
        if n_rows < len(comparison_rows):
            dropped = len(comparison_rows) - n_rows
            issues.append(
                with_metrics(
                    make_issue(
                        "error",
                        "design_matrix",
                        "DESIGN_ROWS_DROPPED",
                        f"Patsy dropped {dropped} samples because design covariates are missing.",
                        "Complete covariates or revise the formula; silent row dropping is not allowed.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                    ),
                    formula,
                    n_rows,
                    n_columns,
                    rank,
                    full_rank,
                )
            )
        if not full_rank:
            issues.append(
                with_metrics(
                    make_issue(
                        "error",
                        "design_matrix",
                        "DESIGN_MATRIX_NOT_FULL_RANK",
                        f"Design matrix rank is {rank} but has {n_columns} columns.",
                        "Resolve confounding or redundant covariates; do not use batch correction to repair an unidentifiable design.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                        details={"columns": list(matrix.columns)},
                    ),
                    formula,
                    n_rows,
                    n_columns,
                    rank,
                    full_rank,
                )
            )
        if full_rank and n_rows == len(comparison_rows):
            issues.append(
                with_metrics(
                    pass_issue(
                        "design_matrix",
                        "DESIGN_MATRIX_FULL_RANK",
                        f"Design matrix for {contrast_id} is full rank.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                    ),
                    formula,
                    n_rows,
                    n_columns,
                    rank,
                    full_rank,
                )
            )
    return sorted(
        issues,
        key=lambda row: (
            {"critical": 0, "error": 1, "warning": 2, "info": 3}[row["severity"]],
            row["analysis_id"],
            row["contrast_id"],
            row["check_id"],
        ),
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Validate formal analysis designs.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--design-validation", required=True)
    parser.add_argument("--crosstab", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with open(args.config, encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    manifest = read_tsv(args.manifest)
    contrasts = read_tsv(args.contrasts)
    plan = read_tsv(args.dataset_plan)
    issues = validate_design_matrices(manifest, contrasts, plan, config)
    write_tsv(args.design_validation, DESIGN_FIELDS, issues)
    write_tsv(args.crosstab, CROSSTAB_FIELDS, build_crosstab(manifest, plan))
    print(f"Wrote {len(issues)} design-matrix validation records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
