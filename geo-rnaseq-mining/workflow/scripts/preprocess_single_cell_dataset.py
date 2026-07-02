#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import scanpy as sc
import yaml

from preanalysis_common import read_tsv
from single_cell_common import (
    calculate_preprocessing_qc,
    cluster_markers,
    cluster_sample_composition,
    cluster_single_cell_object,
    create_post_qc_object,
    load_single_cell_preprocessing_dataset,
    write_json,
)


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def placeholder_plot(path, message):
    ensure_parent(path)
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.axis("off")
    axis.text(0.5, 0.5, message, ha="center", va="center")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def write_qc_plot(qc, path):
    metrics = [
        "total_counts",
        "n_genes_by_counts",
        "pct_counts_mt",
        "pct_counts_ribo",
        "pct_counts_hb",
        "complexity",
        "doublet_score",
    ]
    figure, axes = plt.subplots(3, 3, figsize=(15, 12))
    axes = axes.ravel()
    samples = sorted(qc["sample_id"].astype(str).unique())
    for axis, metric in zip(axes, metrics):
        values = [
            qc.loc[qc["sample_id"].astype(str) == sample, metric]
            .dropna()
            .to_numpy()
            for sample in samples
        ]
        axis.boxplot(values, tick_labels=samples, showfliers=True)
        axis.set_title(metric)
        axis.tick_params(axis="x", rotation=45)
    for axis in axes[len(metrics) :]:
        axis.axis("off")
    figure.tight_layout()
    ensure_parent(path)
    figure.savefig(path, dpi=160)
    plt.close(figure)


def write_embedding_plot(clustered, embedding, path):
    key = f"X_{embedding}"
    if key not in clustered.obsm:
        placeholder_plot(path, f"{embedding.upper()} was not estimable")
        return
    coordinates = clustered.obsm[key]
    figure, axis = plt.subplots(figsize=(8, 7))
    groups = clustered.obs["sample_id"].astype(str)
    for sample_id in sorted(groups.unique()):
        selected = groups == sample_id
        axis.scatter(
            coordinates[selected, 0],
            coordinates[selected, 1],
            s=8,
            alpha=0.7,
            label=sample_id,
        )
    axis.set_xlabel(f"{embedding.upper()}1")
    axis.set_ylabel(f"{embedding.upper()}2")
    axis.legend(markerscale=2, fontsize=8)
    figure.tight_layout()
    ensure_parent(path)
    figure.savefig(path, dpi=160)
    plt.close(figure)


def read_marker_sets(path):
    if not path:
        return {}
    sets = {}
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) >= 3:
                sets[fields[0]] = set(fields[2:])
    return sets


def add_suggested_annotations(clustered, markers, config):
    marker_sets = read_marker_sets(
        config["single_cell"]["annotation"]["marker_sets_gmt"]
    )
    suggestions = {}
    for cluster in clustered.obs["leiden"].astype(str).unique():
        cluster_markers_frame = markers.loc[
            markers["cluster"].astype(str) == cluster
        ]
        top_symbols = set(
            cluster_markers_frame["gene_symbol"].astype(str).head(50)
        )
        scores = {
            label: len(top_symbols & genes)
            for label, genes in marker_sets.items()
        }
        best = max(scores, key=scores.get) if scores and max(scores.values()) > 0 else None
        suggestions[cluster] = best or "unassigned"
    clustered.obs["suggested_annotation"] = (
        clustered.obs["leiden"].astype(str).map(suggestions).fillna("unassigned")
    )
    clustered.uns["annotation_contract"] = {
        "author_label_column": "author_label",
        "suggested_label_column": "suggested_annotation",
        "author_or_confirmed_labels_overwritten": False,
        "suggestion_method": (
            "marker_overlap" if marker_sets else "none_no_marker_sets"
        ),
    }
    return pd.DataFrame(
        [
            {
                "cluster": cluster,
                "suggested_annotation": label,
                "suggestion_method": (
                    "marker_overlap" if marker_sets else "none_no_marker_sets"
                ),
            }
            for cluster, label in sorted(suggestions.items())
        ]
    )


def write_marker_dotplot(clustered, markers, path):
    if markers.empty or clustered.obs["leiden"].nunique() < 2:
        placeholder_plot(path, "Cluster markers were not estimable")
        return
    genes = (
        markers.groupby("cluster", observed=True)
        .head(3)["gene_id_original"]
        .astype(str)
        .drop_duplicates()
        .tolist()
    )
    try:
        plot = sc.pl.dotplot(
            clustered,
            var_names=genes,
            groupby="leiden",
            layer="log_normalized",
            show=False,
            return_fig=True,
        )
        plot.savefig(path)
        plt.close("all")
    except (ValueError, KeyError):
        placeholder_plot(path, "Marker dotplot was not estimable")


def preprocess_single_cell_dataset(
    config,
    manifest,
    dataset_id,
    outputs,
    detector=None,
):
    adata, fingerprints = load_single_cell_preprocessing_dataset(
        manifest,
        config,
        dataset_id,
    )
    qc_result = calculate_preprocessing_qc(adata, config, detector=detector)
    qc = qc_result["cell_qc"]
    for column in (
        "total_counts",
        "n_genes_by_counts",
        "pct_counts_mt",
        "pct_counts_ribo",
        "pct_counts_hb",
        "complexity",
        "doublet_score",
        "predicted_doublet",
        "ambient_rna_score",
        "qc_retained",
        "filter_reason",
    ):
        adata.obs[column] = qc.set_index("cell_id").loc[
            adata.obs_names,
            column,
        ].to_numpy()
    adata.uns["matrix_contract"] = {
        "X": "raw_counts",
        "counts_layer": "raw_nonnegative_integer_counts",
        "stage": "pre_qc",
    }
    for path in outputs.values():
        ensure_parent(path)
    adata.write_h5ad(outputs["pre_qc"], compression="gzip")
    qc.to_csv(outputs["qc"], sep="\t", index=False, lineterminator="\n")
    qc_result["thresholds"].to_csv(
        outputs["thresholds"],
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    qc_result["sample_summary"].to_csv(
        outputs["sample_summary"],
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    qc_result["doublet_status"].to_csv(
        outputs["doublet_status"],
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    qc_result["ambient_status"].to_csv(
        outputs["ambient_status"],
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    write_qc_plot(qc, outputs["qc_plot"])
    if qc_result["failed_samples"]:
        write_json(
            outputs["provenance"],
            {
                "dataset_id": dataset_id,
                "status": "blocked_sample_without_retained_cells",
                "failed_samples": qc_result["failed_samples"],
                "sample_removed_automatically": False,
                "input_fingerprints": fingerprints,
            },
        )
        raise RuntimeError(
            "QC retained zero cells for samples "
            f"{qc_result['failed_samples']}; no sample was automatically removed. "
            "Review thresholds and the reviewed manifest."
        )
    post_qc = create_post_qc_object(adata, qc_result["retained"])
    post_qc.write_h5ad(outputs["post_qc"], compression="gzip")
    clustered = cluster_single_cell_object(post_qc, config)
    markers = cluster_markers(clustered, config)
    suggestions = add_suggested_annotations(clustered, markers, config)
    clustered.write_h5ad(outputs["clustered"], compression="gzip")
    markers.to_csv(outputs["markers"], sep="\t", index=False, lineterminator="\n")
    composition, author_composition = cluster_sample_composition(clustered)
    composition.to_csv(
        outputs["composition"],
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    author_composition.to_csv(
        outputs["author_composition"],
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    suggestions.to_csv(
        outputs["suggestions"],
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    write_embedding_plot(
        clustered,
        "pca_unintegrated",
        outputs["pca_plot"],
    )
    write_embedding_plot(clustered, "umap", outputs["umap_plot"])
    write_marker_dotplot(clustered, markers, outputs["dotplot"])
    write_json(
        outputs["provenance"],
        {
            "dataset_id": dataset_id,
            "status": "complete",
            "input_fingerprints": fingerprints,
            "input_cells": int(adata.n_obs),
            "retained_cells": int(post_qc.n_obs),
            "input_genes": int(adata.n_vars),
            "samples": sorted(adata.obs["sample_id"].astype(str).unique()),
            "qc_strategy": config["single_cell"]["qc"]["strategy"],
            "doublet_method": config["single_cell"]["doublet"]["method"],
            "ambient_rna_method": config["single_cell"]["ambient_rna"]["method"],
            "normalization": "normalize_total_log1p",
            "pca": "unintegrated_scaled_hvg",
            "random_seed": int(config["reproducibility"]["random_seed"]),
            "sample_removed_automatically": False,
            "author_labels_overwritten": False,
        },
    )
    Path(outputs["marker"]).write_text(
        json.dumps(
            {
                "dataset_id": dataset_id,
                "status": "complete",
                "input_cells": int(adata.n_obs),
                "retained_cells": int(post_qc.n_obs),
                "sample_removed_automatically": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "input_cells": int(adata.n_obs),
        "retained_cells": int(post_qc.n_obs),
        "samples": int(adata.obs["sample_id"].nunique()),
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Preprocess one reviewed scRNA-seq or snRNA-seq dataset."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dataset-id", required=True)
    for option in (
        "pre-qc",
        "post-qc",
        "clustered",
        "qc",
        "thresholds",
        "sample-summary",
        "doublet-status",
        "ambient-status",
        "markers",
        "composition",
        "author-composition",
        "suggestions",
        "qc-plot",
        "pca-plot",
        "umap-plot",
        "dotplot",
        "provenance",
        "marker",
    ):
        parser.add_argument(f"--output-{option}", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    output_keys = {
        key.removeprefix("output_"): value
        for key, value in vars(args).items()
        if key.startswith("output_")
    }
    summary = preprocess_single_cell_dataset(
        config,
        read_tsv(args.manifest),
        args.dataset_id,
        output_keys,
    )
    print(
        f"Preprocessed {args.dataset_id}: {summary['retained_cells']}/"
        f"{summary['input_cells']} cells retained across "
        f"{summary['samples']} samples."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
