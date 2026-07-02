#!/usr/bin/env python3

import argparse
from collections import Counter, defaultdict

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


def validate_contrasts(manifest, contrasts, plan):
    issues = []
    analysis_ids = sorted({row.get("analysis_id", "NA") for row in contrasts})
    for analysis_id in analysis_ids:
        analysis_rows = rows_for_analysis(manifest, plan, analysis_id)
        analysis_contrasts = [
            row
            for row in contrasts
            if row.get("analysis_id") == analysis_id
            and as_bool(row.get("enabled")) is True
        ]
        dataset_ids = sorted({row.get("dataset_id", "NA") for row in analysis_rows})
        for row in analysis_rows:
            if is_missing(row.get("group")):
                issues.append(
                    make_issue(
                        "error",
                        "biological_design",
                        "GROUP_MISSING",
                        f"Included sample {row.get('sample_id')} has no group.",
                        "Assign group manually in the reviewed manifest or set include=false.",
                        analysis_id=analysis_id,
                        dataset_id=row.get("dataset_id", "NA"),
                        sample_id=row.get("sample_id", "NA"),
                        subject_id=row.get("subject_id", "NA"),
                    )
                )
            if is_missing(row.get("subject_id")):
                issues.append(
                    make_issue(
                        "error",
                        "biological_design",
                        "SUBJECT_ID_MISSING",
                        f"Included sample {row.get('sample_id')} has no subject_id.",
                        "Enter the human-confirmed biological replicate identifier; do not derive it from GSM or barcode.",
                        analysis_id=analysis_id,
                        dataset_id=row.get("dataset_id", "NA"),
                        sample_id=row.get("sample_id", "NA"),
                    )
                )

        paired_analysis = bool(analysis_contrasts) and all(
            as_bool(contrast.get("paired")) is True
            for contrast in analysis_contrasts
        )
        subject_groups = defaultdict(set)
        subject_rows = defaultdict(list)
        for row in analysis_rows:
            subject = row.get("subject_id", "NA")
            group = row.get("group", "NA")
            if not is_missing(subject) and not is_missing(group):
                subject_groups[subject].add(group)
                subject_rows[subject].append(row)
        for subject, groups in subject_groups.items():
            if len(groups) > 1 and not paired_analysis:
                issues.append(
                    make_issue(
                        "error",
                        "biological_design",
                        "SUBJECT_GROUP_CONFLICT",
                        f"subject_id {subject} is assigned to multiple groups: {sorted(groups)}.",
                        "Correct the reviewed group/subject relationship or define an explicit paired contrast.",
                        analysis_id=analysis_id,
                        dataset_id=";".join(
                            sorted(
                                {
                                    row.get("dataset_id", "NA")
                                    for row in subject_rows[subject]
                                }
                            )
                        ),
                        subject_id=subject,
                    )
                )

        for contrast in analysis_contrasts:
            contrast_id = contrast.get("contrast_id", "NA")
            numerator = contrast.get("numerator", "")
            denominator = contrast.get("denominator", "")
            if numerator == denominator:
                issues.append(
                    make_issue(
                        "error",
                        "contrast",
                        "IDENTICAL_CONTRAST_GROUPS",
                        f"Contrast {contrast_id} has identical numerator and denominator {numerator!r}.",
                        "Confirm contrast direction and enter two different groups.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                    )
                )
                continue
            subset_column = contrast.get("subset_column", "NA")
            subset_value = contrast.get("subset_value", "NA")
            selected = analysis_rows
            if not is_missing(subset_column):
                if subset_column not in (manifest[0] if manifest else {}):
                    issues.append(
                        make_issue(
                            "error",
                            "contrast",
                            "SUBSET_COLUMN_MISSING",
                            f"Contrast {contrast_id} references absent subset_column {subset_column!r}.",
                            "Correct subset_column manually or use NA for no subset.",
                            analysis_id=analysis_id,
                            contrast_id=contrast_id,
                        )
                    )
                    selected = []
                else:
                    selected = [
                        row
                        for row in selected
                        if row.get(subset_column) == subset_value
                    ]
            observed_groups = {
                row.get("group") for row in selected if not is_missing(row.get("group"))
            }
            for direction, group in (
                ("numerator", numerator),
                ("denominator", denominator),
            ):
                if group not in observed_groups:
                    issues.append(
                        make_issue(
                            "error",
                            "contrast",
                            "CONTRAST_GROUP_NOT_FOUND",
                            f"{direction} group {group!r} for contrast {contrast_id} is absent.",
                            "Correct the contrast or reviewed sample groups; the program will not reverse direction.",
                            analysis_id=analysis_id,
                            contrast_id=contrast_id,
                            details={
                                "observed_groups": sorted(observed_groups),
                                "direction": direction,
                            },
                        )
                    )
            minimum = int(contrast.get("min_replicates_per_group", "1"))
            for group in (numerator, denominator):
                group_rows = [row for row in selected if row.get("group") == group]
                subjects = {
                    row.get("subject_id")
                    for row in group_rows
                    if not is_missing(row.get("subject_id"))
                }
                if len(subjects) < minimum:
                    issues.append(
                        make_issue(
                            "error",
                            "contrast",
                            "INSUFFICIENT_SUBJECT_REPLICATES",
                            f"Contrast {contrast_id}, group {group!r} has {len(subjects)} subject-level replicates; minimum is {minimum}.",
                            "Add valid biological replicates, lower the threshold explicitly, or disable the contrast.",
                            analysis_id=analysis_id,
                            contrast_id=contrast_id,
                            details={
                                "group": group,
                                "subjects": sorted(subjects),
                                "datasets": dataset_ids,
                            },
                        )
                    )

            if as_bool(contrast.get("paired")) is True:
                comparison_rows = [
                    row
                    for row in selected
                    if row.get("group") in {numerator, denominator}
                ]
                pairs = defaultdict(list)
                for row in comparison_rows:
                    pair_id = row.get("paired_group", "NA")
                    if is_missing(pair_id):
                        issues.append(
                            make_issue(
                                "error",
                                "paired_design",
                                "PAIRED_GROUP_MISSING",
                                f"Paired contrast {contrast_id} includes sample {row.get('sample_id')} without paired_group.",
                                "Assign paired_group manually for every paired sample.",
                                analysis_id=analysis_id,
                                dataset_id=row.get("dataset_id", "NA"),
                                sample_id=row.get("sample_id", "NA"),
                                subject_id=row.get("subject_id", "NA"),
                                contrast_id=contrast_id,
                            )
                        )
                    else:
                        pairs[pair_id].append(row)
                for pair_id, pair_rows in pairs.items():
                    group_counts = Counter(row.get("group") for row in pair_rows)
                    subject_ids = {
                        row.get("subject_id")
                        for row in pair_rows
                        if not is_missing(row.get("subject_id"))
                    }
                    complete = (
                        group_counts[numerator] == 1
                        and group_counts[denominator] == 1
                        and len(pair_rows) == 2
                    )
                    if not complete:
                        issues.append(
                            make_issue(
                                "error",
                                "paired_design",
                                "INCOMPLETE_PAIR",
                                f"paired_group {pair_id} is not one complete {numerator}/{denominator} pair.",
                                "Provide exactly one reviewed sample from each contrast group for this pair.",
                                analysis_id=analysis_id,
                                contrast_id=contrast_id,
                                details={
                                    "pair_id": pair_id,
                                    "group_counts": dict(group_counts),
                                    "sample_ids": [
                                        row.get("sample_id") for row in pair_rows
                                    ],
                                },
                            )
                        )
                    if len(subject_ids) > 1:
                        issues.append(
                            make_issue(
                                "error",
                                "paired_design",
                                "PAIR_SUBJECT_CONFLICT",
                                f"paired_group {pair_id} contains multiple subject_id values: {sorted(subject_ids)}.",
                                "Correct subject_id or paired_group manually; pairs are not reassigned automatically.",
                                analysis_id=analysis_id,
                                contrast_id=contrast_id,
                            )
                        )
            if not any(
                item["analysis_id"] == analysis_id
                and item["contrast_id"] == contrast_id
                and item["status"] == "fail"
                for item in issues
            ):
                issues.append(
                    pass_issue(
                        "contrast",
                        "CONTRAST_VALID",
                        f"Contrast {contrast_id} passed group, replicate, and pairing checks.",
                        analysis_id=analysis_id,
                        contrast_id=contrast_id,
                    )
                )
    if not contrasts:
        issues.append(
            make_issue(
                "warning",
                "contrast",
                "NO_CONTRASTS_DEFINED",
                "No contrast rows are defined.",
                "Add and confirm contrasts before formal differential analysis.",
            )
        )
    return sort_issues(issues)


def parse_args():
    parser = argparse.ArgumentParser(description="Validate reviewed contrasts.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--contrasts", required=True)
    parser.add_argument("--dataset-plan", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    issues = validate_contrasts(
        read_tsv(args.manifest),
        read_tsv(args.contrasts),
        read_tsv(args.dataset_plan),
    )
    write_tsv(args.output, ISSUE_FIELDS, issues)
    print(f"Wrote {len(issues)} contrast validation records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
