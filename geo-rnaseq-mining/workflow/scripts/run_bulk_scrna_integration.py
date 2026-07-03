#!/usr/bin/env python3

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

from preanalysis_common import read_tsv, write_tsv


NA = "NA"

OUTPUT_TABLES = {
    "gene_celltype_mapping.tsv": [
        "original_gene_id",
        "canonical_gene_id",
        "gene_symbol",
        "mapping_source",
        "mapping_status",
        "duplicate_resolution_method",
        "cell_type",
        "average_expression",
        "expression_cell_fraction",
        "is_dominant_cell_type",
        "dominant_cell_type_note",
    ],
    "bulk_scrna_concordance.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "cell_type",
        "bulk_log2fc",
        "bulk_padj",
        "pseudobulk_log2fc",
        "pseudobulk_padj",
        "effect_direction_consistency",
        "dominant_cell_type",
        "dominant_cell_type_interpretation",
        "cell_type_specificity",
    ],
    "consensus_genes.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "bulk_dataset_support",
        "pseudobulk_dataset_support",
        "direction_consistency",
        "bulk_meta_padj",
        "pseudobulk_meta_padj",
        "loo_stable",
        "dataset_driven",
        "validation_replication_status",
        "evidence_level",
    ],
    "consensus_pathways.tsv": [
        "pathway_id",
        "pathway_name",
        "supporting_genes",
        "pathway_support_score",
        "limitations",
    ],
    "candidate_gene_scores.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "bulk_stat_score",
        "bulk_meta_score",
        "pseudobulk_score",
        "direction_consistency_score",
        "celltype_specificity_score",
        "cross_gse_score",
        "validation_score",
        "pathway_support_score",
        "loo_stability_score",
        "total_score",
        "evidence_level",
        "limitations",
        "dataset_driven",
        "confidence",
        "is_final_biological_conclusion",
        "required_action",
    ],
    "dataset_support_matrix.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "dataset_id",
        "modality",
        "effect",
        "padj",
        "supports_consensus_direction",
        "is_significant",
    ],
    "celltype_specific_effects.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "cell_type",
        "average_expression",
        "expression_cell_fraction",
        "pseudobulk_log2fc",
        "pseudobulk_padj",
        "cell_type_specificity",
        "dominant_cell_type",
        "effect_direction_consistency",
    ],
    "unmapped_genes.tsv": [
        "original_gene_id",
        "mapping_status",
        "mapping_source",
        "duplicate_resolution_method",
        "reason",
    ],
    "dotplot.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "cell_type",
        "average_expression",
        "expression_cell_fraction",
        "total_score",
    ],
    "heatmap.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "cell_type",
        "value",
        "value_type",
    ],
    "effect_scatter.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "cell_type",
        "bulk_log2fc",
        "pseudobulk_log2fc",
        "effect_direction_consistency",
    ],
    "candidate_evidence_plot.tsv": [
        "canonical_gene_id",
        "gene_symbol",
        "component",
        "score",
    ],
    "sankey_edges.tsv": [
        "source",
        "target",
        "value",
        "edge_type",
    ],
    "deconvolution_interface.tsv": [
        "status",
        "signature_source",
        "cell_type",
        "bulk_cell_fraction_change",
        "within_celltype_transcription_change",
        "interpretation_limitations",
    ],
}


def finite_float(value, default=math.nan):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def safe_pvalue_score(value):
    pvalue = finite_float(value)
    if not math.isfinite(pvalue):
        return 0.0
    return min(1.0, max(0.0, -math.log10(max(pvalue, 1e-300)) / 10.0))


def sign(value):
    value = finite_float(value)
    if not math.isfinite(value) or value == 0:
        return 0
    return 1 if value > 0 else -1


def truth(value):
    return str(value).lower() == "true"


def strip_ensembl_version(value):
    text = str(value)
    if "." in text and text.split(".")[-1].isdigit():
        return ".".join(text.split(".")[:-1])
    return text


def build_gene_mapper(mapping_rows, canonicalize_versions=True):
    by_original = defaultdict(list)
    for row in mapping_rows:
        original = str(row.get("original_gene_id") or row.get("gene_id") or "").strip()
        canonical = str(row.get("canonical_gene_id") or row.get("canonical_id") or "").strip()
        if not original or not canonical:
            continue
        by_original[original].append(
            {
                "original_gene_id": original,
                "canonical_gene_id": canonical,
                "gene_symbol": row.get("gene_symbol", row.get("symbol", NA)) or NA,
                "mapping_source": row.get("mapping_source", row.get("source", "mapping_file")) or "mapping_file",
                "mapping_status": row.get("mapping_status", "mapped") or "mapped",
                "duplicate_resolution_method": row.get("duplicate_resolution_method", "explicit_mapping") or "explicit_mapping",
            }
        )

    def map_gene(original_gene_id):
        original = str(original_gene_id)
        keys = [original]
        if canonicalize_versions:
            stripped = strip_ensembl_version(original)
            if stripped != original:
                keys.append(stripped)
        matches = []
        for key in keys:
            matches.extend(by_original.get(key, []))
        unique = {
            (row["canonical_gene_id"], row["gene_symbol"], row["mapping_source"]): row
            for row in matches
        }
        matches = list(unique.values())
        canonical_ids = {row["canonical_gene_id"] for row in matches}
        if len(canonical_ids) > 1:
            return [
                {
                    **row,
                    "original_gene_id": original,
                    "mapping_status": "ambiguous_one_to_many",
                    "duplicate_resolution_method": "unresolved_one_to_many",
                }
                for row in matches
            ]
        if len(matches) == 1:
            return [{**matches[0], "original_gene_id": original}]
        canonical = strip_ensembl_version(original) if canonicalize_versions else original
        return [
            {
                "original_gene_id": original,
                "canonical_gene_id": canonical,
                "gene_symbol": NA,
                "mapping_source": "identity",
                "mapping_status": "identity",
                "duplicate_resolution_method": "identity",
            }
        ]

    return map_gene


def read_optional(path):
    if not path:
        return []
    return read_tsv(path)


def coerce_gene_rows(rows, map_gene):
    mapped = []
    unmapped = []
    for row in rows:
        original = row.get("gene_id") or row.get("original_gene_id") or row.get("canonical_gene_id")
        if not original:
            continue
        mappings = map_gene(original)
        for mapping in mappings:
            merged = {**row, **mapping}
            if mapping["mapping_status"] in {"unmapped", "ambiguous_one_to_many"}:
                unmapped.append(
                    {
                        "original_gene_id": mapping["original_gene_id"],
                        "mapping_status": mapping["mapping_status"],
                        "mapping_source": mapping["mapping_source"],
                        "duplicate_resolution_method": mapping["duplicate_resolution_method"],
                        "reason": mapping["mapping_status"],
                    }
                )
            mapped.append(merged)
    return mapped, unmapped


def index_best_effect(rows, effect_columns, padj_columns, extra_key=None):
    indexed = {}
    for row in rows:
        key = row["canonical_gene_id"] if extra_key is None else (row["canonical_gene_id"], row.get(extra_key, NA))
        effect = next((finite_float(row.get(col)) for col in effect_columns if math.isfinite(finite_float(row.get(col)))), math.nan)
        padj = next((finite_float(row.get(col)) for col in padj_columns if math.isfinite(finite_float(row.get(col)))), math.nan)
        current = indexed.get(key)
        if current is None or (math.isfinite(padj) and padj < finite_float(current.get("padj"))):
            indexed[key] = {**row, "effect": effect, "padj": padj}
    return indexed


def direction_label(a, b):
    first = sign(a)
    second = sign(b)
    if first == 0 or second == 0:
        return "not_comparable"
    return "same" if first == second else "opposite"


def celltype_expression_summary(avg_rows, prop_rows, specificity_delta=0.05):
    prop_index = {
        (row.get("canonical_gene_id"), row.get("cell_type")): row
        for row in prop_rows
    }
    by_gene = defaultdict(list)
    for row in avg_rows:
        gene = row["canonical_gene_id"]
        cell_type = row.get("cell_type", row.get("author_label", NA))
        average = finite_float(row.get("average_expression", row.get("mean_expression", row.get("avg_expression"))), 0.0)
        prop = prop_index.get((gene, cell_type), {})
        fraction = finite_float(prop.get("expression_cell_fraction", prop.get("pct_expr", prop.get("fraction"))), math.nan)
        by_gene[gene].append(
            {
                **row,
                "cell_type": cell_type,
                "average_expression": average,
                "expression_cell_fraction": fraction,
            }
        )
    summary = {}
    for gene, rows in by_gene.items():
        rows = sorted(rows, key=lambda item: item["average_expression"], reverse=True)
        total = sum(max(0.0, row["average_expression"]) for row in rows)
        top = rows[0] if rows else {}
        second = rows[1]["average_expression"] if len(rows) > 1 else 0.0
        dominant = top.get("cell_type", NA)
        specificity = top["average_expression"] / total if total > 0 else 0.0
        ambiguous = (
            not rows
            or len(rows) > 1
            and abs(top["average_expression"] - second) <= specificity_delta * max(top["average_expression"], 1e-9)
        )
        summary[gene] = {
            "rows": rows,
            "dominant_cell_type": "ambiguous" if ambiguous else dominant,
            "dominant_cell_type_note": (
                "ambiguous_dominant_cell_type" if ambiguous else "potential_major_expression_source_not_causal"
            ),
            "cell_type_specificity": specificity,
        }
    return summary


def dataset_effect_rows(mapped_rows, modality):
    rows = []
    for row in mapped_rows:
        dataset_id = row.get("dataset_id", row.get("study_id", NA))
        if dataset_id in {"", NA, None}:
            continue
        effect = finite_float(row.get("log2FoldChange", row.get("pooled_log2fc")))
        padj = finite_float(row.get("padj", row.get("meta_padj", row.get("pvalue"))))
        rows.append(
            {
                "canonical_gene_id": row["canonical_gene_id"],
                "gene_symbol": row.get("gene_symbol", NA),
                "dataset_id": dataset_id,
                "modality": modality,
                "effect": effect,
                "padj": padj,
                "is_significant": str(math.isfinite(padj) and padj < 0.05).lower(),
            }
        )
    return rows


def evidence_level(total):
    if total >= 0.75:
        return "high"
    if total >= 0.5:
        return "moderate"
    if total >= 0.25:
        return "low"
    return "limited"


def confidence(level, limitations):
    limiting_flags = {
        "ambiguous_one_to_many",
        "bulk_pseudobulk_opposite_direction",
        "single_gse_support",
        "validation_failed",
    }
    if limiting_flags & set(limitations):
        return "limited"
    return {"high": "high", "moderate": "moderate", "low": "low"}.get(level, "limited")


def integrate_bulk_scrna(
    config,
    bulk_rows,
    bulk_meta_rows,
    pseudobulk_rows,
    pseudobulk_meta_rows,
    marker_rows,
    avg_expr_rows,
    expr_prop_rows,
    cell_proportion_rows,
    loo_rows,
    validation_rows,
    ontology_rows,
    mapping_rows,
):
    settings = config.get("bulk_scrna_integration", {})
    map_gene = build_gene_mapper(
        mapping_rows,
        bool(settings.get("canonicalize_ensembl_versions", True)),
    )
    mapped_bulk, unmapped_bulk = coerce_gene_rows(bulk_rows, map_gene)
    mapped_bulk_meta, unmapped_bulk_meta = coerce_gene_rows(bulk_meta_rows, map_gene)
    mapped_pb, unmapped_pb = coerce_gene_rows(pseudobulk_rows, map_gene)
    mapped_pb_meta, unmapped_pb_meta = coerce_gene_rows(pseudobulk_meta_rows, map_gene)
    mapped_markers, unmapped_markers = coerce_gene_rows(marker_rows, map_gene)
    mapped_avg, unmapped_avg = coerce_gene_rows(avg_expr_rows, map_gene)
    mapped_prop, unmapped_prop = coerce_gene_rows(expr_prop_rows, map_gene)
    unmapped = unmapped_bulk + unmapped_bulk_meta + unmapped_pb + unmapped_pb_meta + unmapped_markers + unmapped_avg + unmapped_prop

    known_celltypes = {
        row.get("harmonized_level2") or row.get("cell_type") or row.get("author_label")
        for row in ontology_rows
        if row.get("review_status") == "confirmed"
    }
    expr_summary = celltype_expression_summary(
        mapped_avg,
        mapped_prop,
        float(settings.get("dominant_celltype_min_delta", 0.05)),
    )
    bulk_best = index_best_effect(
        mapped_bulk + mapped_bulk_meta,
        ["log2FoldChange", "pooled_log2fc"],
        ["padj", "meta_padj", "pvalue"],
    )
    pb_best = index_best_effect(
        mapped_pb + mapped_pb_meta,
        ["log2FoldChange", "pooled_log2fc"],
        ["padj", "meta_padj", "pvalue"],
        extra_key="cell_type",
    )
    bulk_meta_best = index_best_effect(mapped_bulk_meta, ["pooled_log2fc"], ["meta_padj", "meta_pvalue"])
    pb_meta_best = index_best_effect(mapped_pb_meta, ["pooled_log2fc"], ["meta_padj", "meta_pvalue"], extra_key="cell_type")
    loo_index = {row.get("gene_id", row.get("canonical_gene_id")): row for row in loo_rows}
    validation_index = {row.get("gene_id", row.get("canonical_gene_id")): row for row in validation_rows}

    genes = sorted({
        *bulk_best.keys(),
        *(key[0] for key in pb_best),
        *expr_summary.keys(),
    })
    default_weights = {
        "bulk_stat_score": 1.0,
        "bulk_meta_score": 1.0,
        "pseudobulk_score": 1.0,
        "direction_consistency_score": 1.0,
        "celltype_specificity_score": 1.0,
        "cross_gse_score": 1.0,
        "validation_score": 1.0,
        "pathway_support_score": 0.0,
        "loo_stability_score": 1.0,
    }
    weights = {**default_weights, **settings.get("scoring_weights", {})}
    weight_total = sum(max(0.0, float(value)) for value in weights.values()) or 1.0

    tables = {name: [] for name in OUTPUT_TABLES}
    for gene in genes:
        expression = expr_summary.get(gene, {"rows": [], "dominant_cell_type": "missing", "dominant_cell_type_note": "missing_cell_type_expression", "cell_type_specificity": 0.0})
        bulk = bulk_best.get(gene, {})
        symbol = bulk.get("gene_symbol") or next((row.get("gene_symbol") for row in expression["rows"] if row.get("gene_symbol") not in {None, "", NA}), NA)
        cell_rows = expression["rows"] or [{"cell_type": "missing", "average_expression": math.nan, "expression_cell_fraction": math.nan}]
        cell_types = [row["cell_type"] for row in cell_rows]
        if known_celltypes:
            for missing in sorted(known_celltypes - set(cell_types)):
                cell_rows.append({"cell_type": missing, "average_expression": math.nan, "expression_cell_fraction": math.nan, "missing_cell_type": True})
        best_pb = None
        for row in cell_rows:
            candidate = pb_best.get((gene, row["cell_type"]))
            if candidate and (best_pb is None or finite_float(candidate.get("padj")) < finite_float(best_pb.get("padj"))):
                best_pb = candidate
        best_pb = best_pb or {}
        direction = direction_label(bulk.get("effect"), best_pb.get("effect"))
        bulk_support = len({row["dataset_id"] for row in dataset_effect_rows(mapped_bulk, "bulk") if row["canonical_gene_id"] == gene and row["is_significant"] == "true"})
        pb_support = len({row["dataset_id"] for row in dataset_effect_rows(mapped_pb, "pseudobulk") if row["canonical_gene_id"] == gene and row["is_significant"] == "true"})
        loo = loo_index.get(gene, {})
        validation = validation_index.get(gene, {})
        replication = validation.get("replication_status", "not_available")
        dataset_driven = truth(loo.get("dataset_driven")) or bulk_support <= 1 and pb_support == 0
        limitations = []
        if direction == "opposite":
            limitations.append("bulk_pseudobulk_opposite_direction")
        if bulk_support <= 1:
            limitations.append("single_gse_support")
        if expression["dominant_cell_type"] in {"ambiguous", "missing"}:
            limitations.append(expression["dominant_cell_type_note"])
        if replication not in {"replicated", "not_available", NA, ""}:
            limitations.append("validation_failed")
        if any(row.get("mapping_status") == "ambiguous_one_to_many" for row in mapped_bulk + mapped_pb if row["canonical_gene_id"] == gene):
            limitations.append("ambiguous_one_to_many")
        bulk_meta = bulk_meta_best.get(gene, {})
        pb_meta = pb_meta_best.get((gene, best_pb.get("cell_type", expression["dominant_cell_type"])), {})
        component = {
            "bulk_stat_score": safe_pvalue_score(bulk.get("padj")),
            "bulk_meta_score": safe_pvalue_score(bulk_meta.get("padj")),
            "pseudobulk_score": safe_pvalue_score(best_pb.get("padj")),
            "direction_consistency_score": 1.0 if direction == "same" else 0.0,
            "celltype_specificity_score": float(expression["cell_type_specificity"]),
            "cross_gse_score": min(1.0, (bulk_support + pb_support) / 4.0),
            "validation_score": 1.0 if replication == "replicated" else 0.0,
            "pathway_support_score": 0.0,
            "loo_stability_score": 0.0 if truth(loo.get("dataset_driven")) else 1.0,
        }
        total = sum(component[key] * float(weights.get(key, 0.0)) for key in component) / weight_total
        level = evidence_level(total)
        tables["candidate_gene_scores.tsv"].append(
            {
                "canonical_gene_id": gene,
                "gene_symbol": symbol or NA,
                **component,
                "total_score": total,
                "evidence_level": level,
                "limitations": ";".join(sorted(set(limitations))) if limitations else "none",
                "dataset_driven": str(dataset_driven).lower(),
                "confidence": confidence(level, limitations),
                "is_final_biological_conclusion": "false",
                "required_action": "human_review_required",
            }
        )
        tables["consensus_genes.tsv"].append(
            {
                "canonical_gene_id": gene,
                "gene_symbol": symbol or NA,
                "bulk_dataset_support": bulk_support,
                "pseudobulk_dataset_support": pb_support,
                "direction_consistency": direction,
                "bulk_meta_padj": bulk_meta.get("padj", NA),
                "pseudobulk_meta_padj": pb_meta.get("padj", NA),
                "loo_stable": str(not truth(loo.get("dataset_driven"))).lower(),
                "dataset_driven": str(dataset_driven).lower(),
                "validation_replication_status": replication,
                "evidence_level": level,
            }
        )
        for row in cell_rows:
            cell_type = row["cell_type"]
            if row.get("missing_cell_type"):
                limitations_for_cell = "missing_cell_type"
            else:
                limitations_for_cell = "none"
            pb = pb_best.get((gene, cell_type), {})
            tables["gene_celltype_mapping.tsv"].append(
                {
                    "original_gene_id": row.get("original_gene_id", gene),
                    "canonical_gene_id": gene,
                    "gene_symbol": row.get("gene_symbol", symbol or NA),
                    "mapping_source": row.get("mapping_source", "identity"),
                    "mapping_status": row.get("mapping_status", "identity"),
                    "duplicate_resolution_method": row.get("duplicate_resolution_method", "identity"),
                    "cell_type": cell_type,
                    "average_expression": row.get("average_expression", NA),
                    "expression_cell_fraction": row.get("expression_cell_fraction", NA),
                    "is_dominant_cell_type": str(cell_type == expression["dominant_cell_type"]).lower(),
                    "dominant_cell_type_note": limitations_for_cell if limitations_for_cell != "none" else expression["dominant_cell_type_note"],
                }
            )
            tables["bulk_scrna_concordance.tsv"].append(
                {
                    "canonical_gene_id": gene,
                    "gene_symbol": symbol or NA,
                    "cell_type": cell_type,
                    "bulk_log2fc": bulk.get("effect", NA),
                    "bulk_padj": bulk.get("padj", NA),
                    "pseudobulk_log2fc": pb.get("effect", NA),
                    "pseudobulk_padj": pb.get("padj", NA),
                    "effect_direction_consistency": direction_label(bulk.get("effect"), pb.get("effect")),
                    "dominant_cell_type": expression["dominant_cell_type"],
                    "dominant_cell_type_interpretation": "potential_major_expression_source_not_causal",
                    "cell_type_specificity": expression["cell_type_specificity"],
                }
            )
            tables["celltype_specific_effects.tsv"].append(
                {
                    "canonical_gene_id": gene,
                    "gene_symbol": symbol or NA,
                    "cell_type": cell_type,
                    "average_expression": row.get("average_expression", NA),
                    "expression_cell_fraction": row.get("expression_cell_fraction", NA),
                    "pseudobulk_log2fc": pb.get("effect", NA),
                    "pseudobulk_padj": pb.get("padj", NA),
                    "cell_type_specificity": expression["cell_type_specificity"],
                    "dominant_cell_type": expression["dominant_cell_type"],
                    "effect_direction_consistency": direction_label(bulk.get("effect"), pb.get("effect")),
                }
            )
            tables["dotplot.tsv"].append(
                {
                    "canonical_gene_id": gene,
                    "gene_symbol": symbol or NA,
                    "cell_type": cell_type,
                    "average_expression": row.get("average_expression", NA),
                    "expression_cell_fraction": row.get("expression_cell_fraction", NA),
                    "total_score": total,
                }
            )
            tables["heatmap.tsv"].append(
                {
                    "canonical_gene_id": gene,
                    "gene_symbol": symbol or NA,
                    "cell_type": cell_type,
                    "value": pb.get("effect", NA),
                    "value_type": "pseudobulk_log2fc",
                }
            )
            tables["effect_scatter.tsv"].append(
                {
                    "canonical_gene_id": gene,
                    "gene_symbol": symbol or NA,
                    "cell_type": cell_type,
                    "bulk_log2fc": bulk.get("effect", NA),
                    "pseudobulk_log2fc": pb.get("effect", NA),
                    "effect_direction_consistency": direction_label(bulk.get("effect"), pb.get("effect")),
                }
            )
        for component_name, score in component.items():
            tables["candidate_evidence_plot.tsv"].append(
                {
                    "canonical_gene_id": gene,
                    "gene_symbol": symbol or NA,
                    "component": component_name,
                    "score": score,
                }
            )
        tables["sankey_edges.tsv"].append(
            {
                "source": "bulk_DEG",
                "target": expression["dominant_cell_type"],
                "value": 1,
                "edge_type": "potential_expression_source_not_causal",
            }
        )

    support_rows = dataset_effect_rows(mapped_bulk, "bulk") + dataset_effect_rows(mapped_pb, "pseudobulk")
    consensus_sign = {
        row["canonical_gene_id"]: sign(row["bulk_log2fc"] if row["bulk_log2fc"] != NA else row.get("pseudobulk_log2fc"))
        for row in tables["bulk_scrna_concordance.tsv"]
    }
    for row in support_rows:
        row["supports_consensus_direction"] = str(sign(row["effect"]) == consensus_sign.get(row["canonical_gene_id"]) and sign(row["effect"]) != 0).lower()
        tables["dataset_support_matrix.tsv"].append(row)
    if not tables["dataset_support_matrix.tsv"]:
        for gene in genes:
            tables["dataset_support_matrix.tsv"].append(
                {
                    "canonical_gene_id": gene,
                    "gene_symbol": NA,
                    "dataset_id": NA,
                    "modality": NA,
                    "effect": NA,
                    "padj": NA,
                    "supports_consensus_direction": "false",
                    "is_significant": "false",
                }
            )
    tables["unmapped_genes.tsv"].extend(unmapped)
    tables["consensus_pathways.tsv"].append(
        {
            "pathway_id": NA,
            "pathway_name": "not_run",
            "supporting_genes": "",
            "pathway_support_score": 0,
            "limitations": "pathway_support_input_not_provided",
        }
    )
    if settings.get("deconvolution", {}).get("enabled", False):
        status = "interface_ready_not_interpreted_as_causality"
    else:
        status = "disabled"
    tables["deconvolution_interface.tsv"].append(
        {
            "status": status,
            "signature_source": "single_cell_reference" if status != "disabled" else NA,
            "cell_type": NA,
            "bulk_cell_fraction_change": NA,
            "within_celltype_transcription_change": NA,
            "interpretation_limitations": "distinguish_cell_fraction_change_from_within_celltype_transcription;not_cell_migration_or_disease_causality",
        }
    )
    return tables


def write_outputs(tables, integration_dir, consensus_dir):
    integration_dir = Path(integration_dir)
    consensus_dir = Path(consensus_dir)
    for name, rows in tables.items():
        root = consensus_dir if name in {"consensus_genes.tsv", "consensus_pathways.tsv"} else integration_dir
        write_tsv(root / name, OUTPUT_TABLES[name], rows)
    (integration_dir / ".complete").write_text("bulk_scrna_integration_complete\n", encoding="utf-8")
    (consensus_dir / ".complete").write_text("bulk_scrna_consensus_complete\n", encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(description="Integrate bulk and single-cell RNA-seq evidence.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--bulk-de", action="append", default=[])
    parser.add_argument("--bulk-meta")
    parser.add_argument("--bulk-joint")
    parser.add_argument("--markers", action="append", default=[])
    parser.add_argument("--celltype-average-expression", action="append", default=[])
    parser.add_argument("--celltype-expression-proportion", action="append", default=[])
    parser.add_argument("--cell-proportion", action="append", default=[])
    parser.add_argument("--pseudobulk", action="append", default=[])
    parser.add_argument("--pseudobulk-meta")
    parser.add_argument("--bulk-loo")
    parser.add_argument("--validation")
    parser.add_argument("--ontology", required=True)
    parser.add_argument("--gene-mapping")
    parser.add_argument("--output-dir", default="results/integration")
    parser.add_argument("--consensus-dir", default="results/consensus")
    return parser.parse_args()


def rows_from_many(paths):
    rows = []
    for path in paths or []:
        rows.extend(read_optional(path))
    return rows


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    tables = integrate_bulk_scrna(
        config,
        rows_from_many(args.bulk_de) + read_optional(args.bulk_joint),
        read_optional(args.bulk_meta),
        rows_from_many(args.pseudobulk),
        read_optional(args.pseudobulk_meta),
        rows_from_many(args.markers),
        rows_from_many(args.celltype_average_expression),
        rows_from_many(args.celltype_expression_proportion),
        rows_from_many(args.cell_proportion),
        read_optional(args.bulk_loo),
        read_optional(args.validation),
        read_tsv(args.ontology),
        read_optional(args.gene_mapping),
    )
    write_outputs(tables, args.output_dir, args.consensus_dir)
    print(f"Wrote bulk/single-cell integration outputs to {args.output_dir} and {args.consensus_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
