#!/usr/bin/env python3

import argparse
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import yaml

from preanalysis_common import read_tsv
from single_cell_common import (
    aggregate_pseudobulk,
    celltype_metrics,
    ontology_mapping,
    validate_raw_counts,
    write_json,
)


def prepare_pseudobulk(
    config,
    ontology,
    dataset_id,
    clustered_path,
    output_counts,
    output_metadata,
    output_metrics,
    output_provenance,
):
    adata = ad.read_h5ad(clustered_path)
    if "counts" not in adata.layers:
        raise ValueError("Clustered AnnData is missing layers['counts']")
    validate_raw_counts(adata.layers["counts"], clustered_path)
    for column in ("dataset_id", "sample_id", "subject_id", "group", "author_label"):
        if column not in adata.obs:
            raise ValueError(f"Clustered AnnData is missing obs[{column!r}]")
    missing_subjects = adata.obs["subject_id"].astype(str).isin(
        {"", "NA", "N/A", "null", "None"}
    )
    if missing_subjects.any():
        raise ValueError("Every pseudobulk cell requires reviewed subject_id")
    missing_labels = adata.obs["author_label"].astype(str).isin(
        {"", "NA", "N/A", "null", "None"}
    )
    if missing_labels.any():
        raise ValueError(
            "Author labels are required before subject-level cell-type pseudobulk"
        )
    mapping = ontology_mapping(ontology, dataset_id)
    observed = set(adata.obs["author_label"].astype(str))
    unmapped = sorted(observed - set(mapping))
    if unmapped:
        raise ValueError(
            f"Author cell-type labels lack confirmed ontology mappings: {unmapped}"
        )
    for level in (
        "harmonized_level1",
        "harmonized_level2",
        "harmonized_level3",
    ):
        adata.obs[level] = [
            mapping[label].get(level, "NA")
            for label in adata.obs["author_label"].astype(str)
        ]
    adata.X = adata.layers["counts"].copy()
    retained = np.ones(adata.n_obs, dtype=bool)
    counts, metadata = aggregate_pseudobulk(adata, retained, config)
    qc = pd.DataFrame(
        {
            "cell_id": adata.obs_names.astype(str),
            "qc_retained": True,
        }
    )
    metrics = celltype_metrics(adata, qc)
    for path in (
        output_counts,
        output_metadata,
        output_metrics,
        output_provenance,
    ):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    counts.to_csv(output_counts, sep="\t", index=False, lineterminator="\n")
    metadata.to_csv(
        output_metadata,
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    metrics.to_csv(output_metrics, sep="\t", index=False, lineterminator="\n")
    write_json(
        output_provenance,
        {
            "dataset_id": dataset_id,
            "source": str(clustered_path),
            "source_layer": "counts",
            "pseudobulk_level": "subject_id",
            "pseudobulk_source": "raw_counts",
            "pseudobulk_count": int(len(metadata)),
            "eligible_pseudobulk_count": int(
                (metadata["eligibility"] == "eligible").sum()
            ),
            "ineligible_pseudobulk_count": int(
                (metadata["eligibility"] != "eligible").sum()
            ),
            "min_cells_per_pseudobulk": int(
                config["single_cell"]["pseudobulk"]["min_cells_per_pseudobulk"]
            ),
            "min_subjects_per_group": int(
                config["single_cell"]["pseudobulk"]["min_subjects_per_group"]
            ),
            "min_total_counts": int(
                config["single_cell"]["pseudobulk"]["min_total_counts"]
            ),
            "min_detected_genes": int(
                config["single_cell"]["pseudobulk"]["min_detected_genes"]
            ),
            "cell_replication_used": False,
        },
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--ontology", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--clustered", required=True)
    parser.add_argument("--output-counts", required=True)
    parser.add_argument("--output-metadata", required=True)
    parser.add_argument("--output-metrics", required=True)
    parser.add_argument("--output-provenance", required=True)
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    prepare_pseudobulk(
        config,
        read_tsv(args.ontology),
        args.dataset_id,
        args.clustered,
        args.output_counts,
        args.output_metadata,
        args.output_metrics,
        args.output_provenance,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
