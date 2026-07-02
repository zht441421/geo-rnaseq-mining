#!/usr/bin/env python3

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import mannwhitneyu

from multi_dataset_common import bh_adjust
from preanalysis_common import as_bool, read_tsv


RESULT_FIELDS = [
    "dataset_id",
    "analysis_id",
    "contrast_id",
    "author_label",
    "numerator",
    "denominator",
    "numerator_subjects",
    "denominator_subjects",
    "numerator_mean_proportion",
    "denominator_mean_proportion",
    "proportion_difference",
    "pvalue",
    "padj",
    "test",
]


def dataset_analysis_ids(plan, dataset_id):
    return {
        row["analysis_id"]
        for row in plan
        if row.get("dataset_id") == dataset_id
        and as_bool(row.get("include")) is True
    }


def analyze_cell_proportions(metadata, contrasts, plan, dataset_id):
    frame = pd.DataFrame(metadata)
    if frame.empty:
        return [], pd.DataFrame()
    frame["cell_count"] = pd.to_numeric(frame["cell_count"], errors="raise")
    subject_totals = frame.groupby(
        ["dataset_id", "subject_id", "group"],
        observed=True,
    )["cell_count"].transform("sum")
    frame["proportion"] = frame["cell_count"] / subject_totals
    analysis_ids = dataset_analysis_ids(plan, dataset_id)
    results = []
    for contrast in contrasts:
        if (
            contrast.get("analysis_id") not in analysis_ids
            or contrast.get("data_scope") != "cell_proportion"
            or as_bool(contrast.get("enabled")) is not True
        ):
            continue
        numerator = contrast["numerator"]
        denominator = contrast["denominator"]
        for label, subset in frame.groupby("author_label", observed=True):
            numerator_values = subset.loc[
                subset["group"] == numerator,
                "proportion",
            ].to_numpy()
            denominator_values = subset.loc[
                subset["group"] == denominator,
                "proportion",
            ].to_numpy()
            if not len(numerator_values) or not len(denominator_values):
                continue
            pvalue = float(
                mannwhitneyu(
                    numerator_values,
                    denominator_values,
                    alternative="two-sided",
                ).pvalue
            )
            results.append(
                {
                    "dataset_id": dataset_id,
                    "analysis_id": contrast["analysis_id"],
                    "contrast_id": contrast["contrast_id"],
                    "author_label": label,
                    "numerator": numerator,
                    "denominator": denominator,
                    "numerator_subjects": len(numerator_values),
                    "denominator_subjects": len(denominator_values),
                    "numerator_mean_proportion": float(
                        np.mean(numerator_values)
                    ),
                    "denominator_mean_proportion": float(
                        np.mean(denominator_values)
                    ),
                    "proportion_difference": float(
                        np.mean(numerator_values)
                        - np.mean(denominator_values)
                    ),
                    "pvalue": pvalue,
                    "padj": math.nan,
                    "test": "subject_level_mann_whitney_u",
                }
            )
    adjusted = bh_adjust([row["pvalue"] for row in results])
    for row, padj in zip(results, adjusted):
        row["padj"] = float(padj)
    return results, frame


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze cell-type proportions at subject level."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--output-results", required=True)
    parser.add_argument("--output-proportions", required=True)
    parser.add_argument("--output-marker", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        yaml.safe_load(handle)
    results, proportions = analyze_cell_proportions(
        read_tsv(args.metadata),
        read_tsv(args.contrasts),
        read_tsv(args.dataset_plan),
        args.dataset_id,
    )
    output = Path(args.output_results)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results, columns=RESULT_FIELDS).to_csv(
        output,
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    proportions.to_csv(
        args.output_proportions,
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    Path(args.output_marker).write_text(
        f"dataset_id={args.dataset_id}\nresult_count={len(results)}\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(results)} subject-level cell proportion results.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
