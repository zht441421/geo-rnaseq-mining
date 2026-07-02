import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta, chi2, norm

from bulk_common import (
    active_bulk_rows,
    blocking_issues,
    bulk_entry_branch,
    validate_bulk_count_matrix,
)
from preanalysis_common import as_bool, is_missing


COMPATIBILITY_FIELDS = [
    "analysis_id",
    "dataset_id",
    "contrast_id",
    "analysis_strategy",
    "role",
    "species",
    "tissue",
    "data_type",
    "platform",
    "library_strategy",
    "library_layout",
    "reference_genome",
    "annotation_version",
    "gene_id_type",
    "count_source",
    "case_count",
    "control_count",
    "raw_data_available",
    "compatible_for_joint_model",
    "compatible_for_meta_analysis",
    "incompatibility_reason",
    "requires_manual_review",
]

META_FIELDS = [
    "gene_id",
    "gene_symbol",
    "n_studies",
    "pooled_log2fc",
    "pooled_se",
    "confidence_interval",
    "ci_lower",
    "ci_upper",
    "meta_pvalue",
    "meta_padj",
    "Q",
    "Q_pvalue",
    "I2",
    "tau2",
    "direction_consistency",
    "significant_study_count",
    "dataset_specific_effects",
    "meta_model",
]


def enabled_bulk_contrasts(contrasts, analysis_id):
    return [
        row
        for row in contrasts
        if row.get("analysis_id") == analysis_id
        and row.get("data_scope") == "bulk"
        and as_bool(row.get("enabled")) is True
    ]


def included_plan_rows(plan, analysis_id=None):
    rows = [row for row in plan if as_bool(row.get("include")) is True]
    if analysis_id is not None:
        rows = [row for row in rows if row.get("analysis_id") == analysis_id]
    return rows


def analysis_strategy(plan, analysis_id):
    strategies = {
        row.get("analysis_strategy")
        for row in included_plan_rows(plan, analysis_id)
    }
    if len(strategies) != 1:
        raise ValueError(
            f"analysis_id {analysis_id} must define exactly one analysis_strategy"
        )
    return next(iter(strategies))


def uniform_value(values):
    observed = sorted(
        {
            str(value)
            for value in values
            if not is_missing(value)
            and str(value).strip().lower() not in {"unknown", "na", "n/a"}
        }
    )
    if not observed:
        return "unknown", True
    if len(observed) == 1:
        return observed[0], False
    return ";".join(observed), True


def metadata_maps(geo_rows, sra_rows):
    geo_by_gsm = {
        row.get("gsm_accession"): row
        for row in geo_rows
        if not is_missing(row.get("gsm_accession"))
    }
    sra_by_srr = {
        row.get("srr_accession"): row
        for row in sra_rows
        if not is_missing(row.get("srr_accession"))
    }
    return geo_by_gsm, sra_by_srr


def dataset_technical_profile(
    dataset_id,
    manifest_rows,
    config,
    geo_by_gsm=None,
    sra_by_srr=None,
):
    geo_by_gsm = geo_by_gsm or {}
    sra_by_srr = sra_by_srr or {}
    compatibility = (
        config.get("validation", {})
        .get("dataset_compatibility", {})
        .get(dataset_id, {})
    )
    references = config.get("references", {})
    tissue, tissue_review = uniform_value(
        row.get("tissue") for row in manifest_rows
    )
    data_type, data_type_review = uniform_value(
        row.get("data_type") for row in manifest_rows
    )
    layout, layout_review = uniform_value(
        row.get("library_layout") for row in manifest_rows
    )
    organisms = []
    platforms = []
    library_strategies = []
    for row in manifest_rows:
        geo = geo_by_gsm.get(row.get("gsm_id"), {})
        sra = sra_by_srr.get(row.get("srr_id"), {})
        organisms.append(geo.get("organism"))
        platforms.append(geo.get("platform"))
        library_strategies.append(sra.get("library_strategy"))
    species, species_review = uniform_value(
        [
            compatibility.get("species"),
            *organisms,
            references.get("species"),
        ]
    )
    platform, platform_review = uniform_value(
        [compatibility.get("platform"), *platforms]
    )
    library_strategy, strategy_review = uniform_value(
        [compatibility.get("library_strategy"), *library_strategies]
    )
    reference_genome = (
        compatibility.get("reference_genome")
        or references.get("genome_build")
        or "unknown"
    )
    annotation_version = (
        compatibility.get("annotation_version")
        or compatibility.get("annotation_release")
        or references.get("annotation_release")
        or "unknown"
    )
    gene_id_type = (
        compatibility.get("gene_id_type")
        or compatibility.get("gene_id_space")
        or references.get("gene_id_space")
        or "unknown"
    )
    branch = bulk_entry_branch(manifest_rows)
    if branch == "fastq":
        count_source = f"uniform_fastq_{config['bulk']['quantification_method']}"
        quantification_source = config["bulk"]["quantification_method"]
        raw_available = all(
            Path(row.get("fastq_r1", "")).is_file()
            and (
                str(row.get("library_layout", "")).upper() != "PAIRED"
                or Path(row.get("fastq_r2", "")).is_file()
            )
            for row in manifest_rows
        )
        count_blocking = False
    elif branch == "matrix":
        quantification_source = (
            compatibility.get("quantification_source")
            or compatibility.get("count_generation_method")
            or "unknown"
        )
        matrix_paths = {
            row.get("matrix_path")
            for row in manifest_rows
            if not is_missing(row.get("matrix_path"))
        }
        raw_available = len(matrix_paths) == 1 and Path(
            next(iter(matrix_paths), "")
        ).is_file()
        count_blocking = True
        count_source = "author_matrix_unverified"
        if raw_available:
            expected = [row["sample_id"] for row in manifest_rows]
            _, issues = validate_bulk_count_matrix(
                next(iter(matrix_paths)),
                expected,
                dataset_id,
            )
            count_blocking = bool(blocking_issues(issues))
            count_source = (
                "author_raw_integer_counts"
                if not count_blocking
                else "normalized_or_invalid_matrix"
            )
    else:
        count_source = "mixed_or_missing"
        quantification_source = "unknown"
        raw_available = False
        count_blocking = True
    return {
        "species": species,
        "tissue": tissue,
        "data_type": data_type,
        "platform": platform,
        "library_strategy": library_strategy,
        "library_layout": layout,
        "reference_genome": str(reference_genome),
        "annotation_version": str(annotation_version),
        "gene_id_type": str(gene_id_type),
        "count_source": count_source,
        "quantification_source": str(quantification_source),
        "raw_data_available": raw_available,
        "profile_requires_review": any(
            (
                tissue_review,
                data_type_review,
                layout_review,
                species_review,
                platform_review,
                strategy_review,
            )
        ),
        "count_blocking": count_blocking,
        "allow_author_counts_joint_model": bool(
            compatibility.get(
                "allow_author_counts_joint_model",
                config.get("multi_dataset", {})
                .get("joint_model", {})
                .get("allow_author_counts", False),
            )
        ),
    }


def complete_dataset_group_confounding(rows, numerator, denominator):
    comparison = [
        row
        for row in rows
        if row.get("group") in {numerator, denominator}
    ]
    groups_by_dataset = defaultdict(set)
    datasets_by_group = defaultdict(set)
    for row in comparison:
        groups_by_dataset[row.get("dataset_id")].add(row.get("group"))
        datasets_by_group[row.get("group")].add(row.get("dataset_id"))
    return bool(groups_by_dataset) and all(
        len(groups) == 1 for groups in groups_by_dataset.values()
    ) and all(
        len(datasets_by_group.get(group, set())) == 1
        for group in (numerator, denominator)
    )


def duplicate_cross_dataset_identities(rows):
    conflicts = set()
    for field in ("sample_id", "subject_id", "gsm_id", "srr_id"):
        datasets_by_value = defaultdict(set)
        for row in rows:
            value = row.get(field)
            if not is_missing(value):
                datasets_by_value[value].add(row.get("dataset_id"))
        for value, datasets in datasets_by_value.items():
            if len(datasets) > 1:
                conflicts.add(f"{field}:{value}")
    return sorted(conflicts)


def dominant_dataset(rows, threshold):
    counts = Counter(row.get("dataset_id") for row in rows)
    total = sum(counts.values())
    if not total or len(counts) < 2:
        return None
    dataset_id, count = counts.most_common(1)[0]
    fraction = count / total
    if fraction >= threshold:
        return dataset_id, fraction, dict(counts)
    return None


def assess_compatibility(
    manifest,
    plan,
    contrasts,
    config,
    geo_rows=None,
    sra_rows=None,
):
    geo_by_gsm, sra_by_srr = metadata_maps(geo_rows or [], sra_rows or [])
    active_rows = active_bulk_rows(manifest)
    rows_by_dataset = defaultdict(list)
    for row in active_rows:
        rows_by_dataset[row.get("dataset_id")].append(row)
    output = []
    grouped_output = defaultdict(list)
    for plan_row in included_plan_rows(plan):
        analysis_id = plan_row.get("analysis_id", "NA")
        dataset_id = plan_row.get("dataset_id", "NA")
        dataset_rows = rows_by_dataset.get(dataset_id, [])
        profile = dataset_technical_profile(
            dataset_id,
            dataset_rows,
            config,
            geo_by_gsm,
            sra_by_srr,
        ) if dataset_rows else {
            "species": "unknown",
            "tissue": "unknown",
            "data_type": "unknown",
            "platform": "unknown",
            "library_strategy": "unknown",
            "library_layout": "unknown",
            "reference_genome": "unknown",
            "annotation_version": "unknown",
            "gene_id_type": "unknown",
            "count_source": "missing",
            "quantification_source": "unknown",
            "raw_data_available": False,
            "profile_requires_review": True,
            "count_blocking": True,
            "allow_author_counts_joint_model": False,
        }
        analysis_contrasts = enabled_bulk_contrasts(contrasts, analysis_id) or [
            {
                "contrast_id": "NA",
                "numerator": "case",
                "denominator": "control",
            }
        ]
        for contrast in analysis_contrasts:
            numerator = contrast.get("numerator", "case")
            denominator = contrast.get("denominator", "control")
            reasons = []
            if not dataset_rows:
                reasons.append("no_active_reviewed_bulk_samples")
            if profile["count_blocking"]:
                reasons.append("raw_integer_counts_unavailable")
            if str(profile["data_type"]).lower().find("bulk") < 0:
                reasons.append("not_bulk_data")
            case_count = sum(
                row.get("group") == numerator for row in dataset_rows
            )
            control_count = sum(
                row.get("group") == denominator for row in dataset_rows
            )
            if case_count == 0 or control_count == 0:
                reasons.append("contrast_not_estimable_within_dataset")
            if plan_row.get("role") == "validation" and plan_row.get(
                "analysis_strategy"
            ) != "stratified_validation":
                reasons.append("validation_dataset_in_non_stratified_strategy")
            row = {
                "analysis_id": analysis_id,
                "dataset_id": dataset_id,
                "contrast_id": contrast.get("contrast_id", "NA"),
                "analysis_strategy": plan_row.get("analysis_strategy", "NA"),
                "role": plan_row.get("role", "NA"),
                **{
                    field: profile[field]
                    for field in (
                        "species",
                        "tissue",
                        "data_type",
                        "platform",
                        "library_strategy",
                        "library_layout",
                        "reference_genome",
                        "annotation_version",
                        "gene_id_type",
                        "count_source",
                    )
                },
                "case_count": str(case_count),
                "control_count": str(control_count),
                "raw_data_available": str(
                    profile["raw_data_available"]
                ).lower(),
                "compatible_for_joint_model": "false",
                "compatible_for_meta_analysis": str(not reasons).lower(),
                "incompatibility_reason": ";".join(reasons) or "none",
                "requires_manual_review": str(
                    profile["profile_requires_review"] or bool(reasons)
                ).lower(),
                "_allow_author_counts_joint_model": profile[
                    "allow_author_counts_joint_model"
                ],
                "_quantification_source": profile["quantification_source"],
            }
            output.append(row)
            grouped_output[
                (analysis_id, contrast.get("contrast_id", "NA"))
            ].append(row)

    dominance_threshold = float(
        config.get("validation", {}).get("dataset_dominance_fraction", 0.8)
    )
    for (analysis_id, contrast_id), rows in grouped_output.items():
        plan_rows = included_plan_rows(plan, analysis_id)
        strategy = analysis_strategy(plan, analysis_id)
        manifest_rows = [
            row
            for row in active_rows
            if row.get("dataset_id")
            in {item.get("dataset_id") for item in plan_rows}
        ]
        numerator = next(
            (
                row.get("numerator")
                for row in enabled_bulk_contrasts(contrasts, analysis_id)
                if row.get("contrast_id") == contrast_id
            ),
            "case",
        )
        denominator = next(
            (
                row.get("denominator")
                for row in enabled_bulk_contrasts(contrasts, analysis_id)
                if row.get("contrast_id") == contrast_id
            ),
            "control",
        )
        cross_reasons = []
        for field in (
            "species",
            "tissue",
            "data_type",
            "reference_genome",
            "annotation_version",
            "gene_id_type",
        ):
            values = {
                row[field]
                for row in rows
                if str(row[field]).lower() not in {"unknown", "na", ""}
            }
            if len(values) != 1 or any(
                str(row[field]).lower() in {"unknown", "na", ""}
                for row in rows
            ):
                cross_reasons.append(f"incompatible_or_unknown_{field}")
        identities = duplicate_cross_dataset_identities(manifest_rows)
        if identities:
            cross_reasons.append("overlapping_sample_identity")
        if complete_dataset_group_confounding(
            manifest_rows,
            numerator,
            denominator,
        ):
            cross_reasons.append("dataset_group_complete_confounding")
        if any(row["role"] == "validation" for row in rows):
            cross_reasons.append("validation_dataset_excluded_from_joint_model")
        count_sources = {row["count_source"] for row in rows}
        fastq_uniform = (
            len(count_sources) == 1
            and next(iter(count_sources), "").startswith("uniform_fastq_")
        )
        author_counts = count_sources == {"author_raw_integer_counts"}
        author_allowed = all(
            row["_allow_author_counts_joint_model"] for row in rows
        )
        author_quantification_sources = {
            row["_quantification_source"]
            for row in rows
            if str(row["_quantification_source"]).lower()
            not in {"unknown", "na", ""}
        }
        author_quantification_compatible = (
            len(author_quantification_sources) == 1
            and all(
                str(row["_quantification_source"]).lower()
                not in {"unknown", "na", ""}
                for row in rows
            )
        )
        if not fastq_uniform and not (
            author_counts
            and author_allowed
            and author_quantification_compatible
        ):
            cross_reasons.append("count_sources_not_approved_for_joint_model")
        if author_counts and not author_quantification_compatible:
            cross_reasons.append(
                "author_count_quantification_source_incompatible_or_unknown"
            )
        dominance = dominant_dataset(manifest_rows, dominance_threshold)
        for row in rows:
            individual_reasons = [
                reason
                for reason in row["incompatibility_reason"].split(";")
                if reason and reason != "none"
            ]
            joint_reasons = sorted(set(individual_reasons + cross_reasons))
            row["compatible_for_joint_model"] = str(
                strategy == "joint_model" and not joint_reasons
            ).lower()
            meta_reasons = [
                reason
                for reason in joint_reasons
                if reason
                not in {
                    "count_sources_not_approved_for_joint_model",
                    "dataset_group_complete_confounding",
                    "validation_dataset_excluded_from_joint_model",
                }
            ]
            row["compatible_for_meta_analysis"] = str(
                not meta_reasons
            ).lower()
            if joint_reasons:
                row["incompatibility_reason"] = ";".join(joint_reasons)
            if dominance:
                row["requires_manual_review"] = "true"
                dominance_reason = (
                    f"dataset_sample_size_dominance:{dominance[0]}:"
                    f"{dominance[1]:.6f}"
                )
                existing = [
                    value
                    for value in row["incompatibility_reason"].split(";")
                    if value and value != "none"
                ]
                row["incompatibility_reason"] = ";".join(
                    sorted(set([*existing, dominance_reason]))
                )
            row.pop("_allow_author_counts_joint_model", None)
            row.pop("_quantification_source", None)
    return output


def bh_adjust(pvalues):
    values = np.asarray(pvalues, dtype=float)
    adjusted = np.full(values.shape, np.nan)
    finite = np.isfinite(values)
    if not np.any(finite):
        return adjusted
    finite_values = values[finite]
    order = np.argsort(finite_values)
    ranked = finite_values[order]
    count = len(ranked)
    corrected = ranked * count / np.arange(1, count + 1)
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    corrected = np.minimum(corrected, 1.0)
    restored = np.empty(count)
    restored[order] = corrected
    adjusted[finite] = restored
    return adjusted


def effect_meta_statistics(effects, standard_errors):
    effects = np.asarray(effects, dtype=float)
    standard_errors = np.asarray(standard_errors, dtype=float)
    variances = standard_errors ** 2
    fixed_weights = 1.0 / variances
    fixed_effect = float(np.sum(fixed_weights * effects) / np.sum(fixed_weights))
    fixed_se = float(math.sqrt(1.0 / np.sum(fixed_weights)))
    q_value = float(np.sum(fixed_weights * (effects - fixed_effect) ** 2))
    degrees_freedom = max(0, len(effects) - 1)
    q_pvalue = (
        float(chi2.sf(q_value, degrees_freedom))
        if degrees_freedom > 0
        else 1.0
    )
    denominator = float(
        np.sum(fixed_weights)
        - np.sum(fixed_weights ** 2) / np.sum(fixed_weights)
    )
    tau2 = (
        max(0.0, (q_value - degrees_freedom) / denominator)
        if denominator > 0
        else 0.0
    )
    random_weights = 1.0 / (variances + tau2)
    random_effect = float(
        np.sum(random_weights * effects) / np.sum(random_weights)
    )
    random_se = float(math.sqrt(1.0 / np.sum(random_weights)))
    i2 = (
        max(0.0, (q_value - degrees_freedom) / q_value) * 100
        if q_value > 0 and degrees_freedom > 0
        else 0.0
    )
    return {
        "fixed_effect": fixed_effect,
        "fixed_se": fixed_se,
        "random_effect": random_effect,
        "random_se": random_se,
        "Q": q_value,
        "Q_pvalue": q_pvalue,
        "I2": i2,
        "tau2": tau2,
    }


def robust_rank_pvalue(normalized_ranks):
    ranks = np.sort(np.asarray(normalized_ranks, dtype=float))
    count = len(ranks)
    if count == 0:
        return math.nan
    probabilities = [
        beta.cdf(rank, index, count - index + 1)
        for index, rank in enumerate(ranks, start=1)
    ]
    return min(1.0, min(probabilities) * count)


def meta_gene(evidence, method, alpha=0.05):
    valid = [
        row
        for row in evidence
        if math.isfinite(float(row["log2FoldChange"]))
        and math.isfinite(float(row["lfcSE"]))
        and float(row["lfcSE"]) > 0
        and math.isfinite(float(row["pvalue"]))
    ]
    if not valid:
        return None
    effects = np.array([float(row["log2FoldChange"]) for row in valid])
    standard_errors = np.array([float(row["lfcSE"]) for row in valid])
    pvalues = np.clip(
        np.array([float(row["pvalue"]) for row in valid]),
        np.finfo(float).tiny,
        1.0,
    )
    sample_sizes = np.array(
        [max(1.0, float(row.get("sample_size", 1))) for row in valid]
    )
    statistics = effect_meta_statistics(effects, standard_errors)
    if method == "fixed_effect":
        pooled = statistics["fixed_effect"]
        pooled_se = statistics["fixed_se"]
        meta_pvalue = float(2 * norm.sf(abs(pooled / pooled_se)))
    else:
        pooled = statistics["random_effect"]
        pooled_se = statistics["random_se"]
        if method == "random_effects":
            meta_pvalue = float(2 * norm.sf(abs(pooled / pooled_se)))
        elif method == "fisher":
            meta_pvalue = float(
                chi2.sf(-2 * np.sum(np.log(pvalues)), 2 * len(pvalues))
            )
        elif method == "weighted_stouffer":
            signed_z = norm.isf(pvalues / 2) * np.sign(effects)
            weights = np.sqrt(sample_sizes)
            combined_z = float(
                np.sum(weights * signed_z) / math.sqrt(np.sum(weights ** 2))
            )
            meta_pvalue = float(2 * norm.sf(abs(combined_z)))
        elif method == "robust_rank_aggregation":
            normalized_ranks = [
                float(row.get("normalized_rank", 1.0))
                for row in valid
            ]
            meta_pvalue = robust_rank_pvalue(normalized_ranks)
        else:
            raise ValueError(f"Unsupported meta method: {method}")
    ci_lower = pooled - 1.96 * pooled_se
    ci_upper = pooled + 1.96 * pooled_se
    signs = set(np.sign(effects))
    direction = (
        "consistent_up"
        if signs == {1.0}
        else "consistent_down"
        if signs == {-1.0}
        else "mixed"
    )
    dataset_effects = {
        row["dataset_id"]: {
            "log2FoldChange": float(row["log2FoldChange"]),
            "lfcSE": float(row["lfcSE"]),
            "pvalue": float(row["pvalue"]),
            "sample_size": float(row.get("sample_size", 1)),
        }
        for row in valid
    }
    return {
        "gene_id": valid[0]["gene_id"],
        "gene_symbol": valid[0].get("gene_symbol") or "NA",
        "n_studies": len(valid),
        "pooled_log2fc": pooled,
        "pooled_se": pooled_se,
        "confidence_interval": f"{ci_lower:.8g};{ci_upper:.8g}",
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "meta_pvalue": meta_pvalue,
        "meta_padj": math.nan,
        "Q": statistics["Q"],
        "Q_pvalue": statistics["Q_pvalue"],
        "I2": statistics["I2"],
        "tau2": statistics["tau2"],
        "direction_consistency": direction,
        "significant_study_count": sum(
            float(row["pvalue"]) < alpha for row in valid
        ),
        "dataset_specific_effects": json.dumps(
            dataset_effects,
            ensure_ascii=False,
            sort_keys=True,
        ),
        "meta_model": method,
    }


def assign_normalized_ranks(evidence):
    by_dataset = defaultdict(list)
    for row in evidence:
        by_dataset[row["dataset_id"]].append(row)
    for rows in by_dataset.values():
        rows.sort(key=lambda item: float(item.get("pvalue", 1.0)))
        count = len(rows)
        for index, row in enumerate(rows, start=1):
            row["normalized_rank"] = index / count


def meta_analyze_evidence(evidence, method, alpha=0.05, min_studies=2):
    copied = [dict(row) for row in evidence]
    assign_normalized_ranks(copied)
    by_gene = defaultdict(list)
    for row in copied:
        by_gene[row["gene_id"]].append(row)
    results = []
    for gene_id in sorted(by_gene):
        result = meta_gene(by_gene[gene_id], method, alpha)
        if result and result["n_studies"] >= min_studies:
            results.append(result)
    adjusted = bh_adjust([row["meta_pvalue"] for row in results])
    for row, padj in zip(results, adjusted):
        row["meta_padj"] = float(padj)
    return sorted(
        results,
        key=lambda row: (
            math.inf if not math.isfinite(row["meta_padj"]) else row["meta_padj"],
            row["gene_id"],
        ),
    )


def leave_one_dataset_out(
    evidence,
    method,
    alpha=0.05,
    min_studies=2,
    effect_change_threshold=0.5,
):
    full = {
        row["gene_id"]: row
        for row in meta_analyze_evidence(
            evidence,
            method,
            alpha,
            min_studies,
        )
    }
    datasets = sorted({row["dataset_id"] for row in evidence})
    detail = []
    by_gene_exclusions = defaultdict(list)
    for dataset_id in datasets:
        subset = [
            row for row in evidence if row["dataset_id"] != dataset_id
        ]
        subset_results = meta_analyze_evidence(
            subset,
            method,
            alpha,
            max(1, min_studies - 1),
        )
        for row in subset_results:
            record = {
                "gene_id": row["gene_id"],
                "excluded_dataset": dataset_id,
                "pooled_log2fc": row["pooled_log2fc"],
                "meta_pvalue": row["meta_pvalue"],
                "meta_padj": row["meta_padj"],
                "significant": str(row["meta_padj"] < alpha).lower(),
            }
            detail.append(record)
            by_gene_exclusions[row["gene_id"]].append(record)
    summary = []
    for gene_id, full_row in full.items():
        exclusions = by_gene_exclusions.get(gene_id, [])
        full_effect = float(full_row["pooled_log2fc"])
        full_significant = full_row["meta_padj"] < alpha
        sign_stable = bool(exclusions) and all(
            np.sign(float(row["pooled_log2fc"])) == np.sign(full_effect)
            for row in exclusions
        )
        significance_stable = bool(exclusions) and all(
            (row["meta_padj"] < alpha) == full_significant
            for row in exclusions
        )
        max_effect_change = max(
            (
                abs(float(row["pooled_log2fc"]) - full_effect)
                for row in exclusions
            ),
            default=math.nan,
        )
        dataset_driven = (
            not sign_stable
            or not significance_stable
            or (
                math.isfinite(max_effect_change)
                and max_effect_change > effect_change_threshold
            )
        )
        summary.append(
            {
                "gene_id": gene_id,
                "dataset_driven": str(dataset_driven).lower(),
                "sign_stable": str(sign_stable).lower(),
                "significance_stable": str(significance_stable).lower(),
                "max_effect_change": max_effect_change,
                "full_pooled_log2fc": full_effect,
                "full_meta_padj": full_row["meta_padj"],
                "excluded_dataset_count": len(exclusions),
            }
        )
    return summary, detail


def read_dataset_effects(
    result_path,
    dataset_id,
    sample_size,
):
    frame = pd.read_csv(result_path, sep="\t")
    required = {"gene_id", "log2FoldChange", "lfcSE", "pvalue"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(
            f"{result_path} is missing DESeq2 columns: {sorted(missing)}"
        )
    evidence = []
    for record in frame.to_dict(orient="records"):
        try:
            effect = float(record["log2FoldChange"])
            standard_error = float(record["lfcSE"])
            pvalue = float(record["pvalue"])
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in (effect, standard_error, pvalue)):
            continue
        evidence.append(
            {
                "gene_id": str(record["gene_id"]),
                "gene_symbol": record.get("gene_symbol", "NA"),
                "dataset_id": dataset_id,
                "log2FoldChange": effect,
                "lfcSE": standard_error,
                "pvalue": pvalue,
                "sample_size": sample_size,
            }
        )
    return evidence


def sample_size_from_contrast_qc(path):
    frame = pd.read_csv(path, sep="\t")
    if "sample_count" not in frame.columns or frame.empty:
        raise ValueError(f"{path} does not contain sample_count")
    values = pd.to_numeric(frame["sample_count"], errors="coerce").dropna()
    if values.empty:
        raise ValueError(f"{path} has no valid sample_count")
    return float(values.iloc[0])


def collect_contrast_evidence(dataset_ids, contrast_id, result_root):
    evidence = []
    for dataset_id in dataset_ids:
        contrast_dir = (
            Path(result_root)
            / dataset_id
            / "bulk"
            / "deseq2"
            / contrast_id
        )
        sample_size = sample_size_from_contrast_qc(
            contrast_dir / "contrast_qc.tsv"
        )
        evidence.extend(
            read_dataset_effects(
                contrast_dir / "deseq2_full_results.tsv",
                dataset_id,
                sample_size,
            )
        )
    return evidence
