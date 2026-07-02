#!/usr/bin/env python3

import argparse
from pathlib import Path

import yaml

from preanalysis_common import read_tsv
from single_cell_common import (
    aggregate_pseudobulk,
    calculate_cell_qc,
    celltype_metrics,
    load_reviewed_single_cell_dataset,
    normalize_for_visualization,
    write_json,
)


def prepare_single_cell_dataset(
    config,
    manifest,
    ontology,
    dataset_id,
    output_h5ad,
    output_qc,
    output_metrics,
    output_counts,
    output_metadata,
    output_provenance,
):
    adata, fingerprints = load_reviewed_single_cell_dataset(
        manifest,
        ontology,
        config,
        dataset_id,
    )
    qc, retained = calculate_cell_qc(adata, config)
    if not retained.any():
        raise RuntimeError(f"All cells failed configured QC for {dataset_id}")
    pseudobulk_counts, pseudobulk_metadata = aggregate_pseudobulk(
        adata,
        retained,
        config,
    )
    if pseudobulk_metadata.empty:
        raise RuntimeError(f"No subject-level pseudobulk samples for {dataset_id}")
    metrics = celltype_metrics(adata, qc)
    processed = normalize_for_visualization(adata, retained, config)
    Path(output_h5ad).parent.mkdir(parents=True, exist_ok=True)
    processed.write_h5ad(output_h5ad, compression="gzip")
    qc.to_csv(output_qc, sep="\t", index=False, lineterminator="\n")
    metrics.to_csv(output_metrics, sep="\t", index=False, lineterminator="\n")
    pseudobulk_counts.to_csv(
        output_counts,
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    pseudobulk_metadata.to_csv(
        output_metadata,
        sep="\t",
        index=False,
        lineterminator="\n",
    )
    write_json(
        output_provenance,
        {
            "dataset_id": dataset_id,
            "source": "reviewed_manifest",
            "input_fingerprints": fingerprints,
            "raw_cells": int(adata.n_obs),
            "retained_cells": int(retained.sum()),
            "removed_cells": int((~retained).sum()),
            "raw_genes": int(adata.n_vars),
            "pseudobulk_level": "subject_id",
            "pseudobulk_source": "raw_counts",
            "pseudobulk_count": int(len(pseudobulk_metadata)),
            "ambient_rna_method": config["single_cell"]["ambient_rna"]["method"],
            "scrublet_enabled": bool(
                config["single_cell"]["scrublet"]["enabled"]
            ),
            "random_seed": int(config["reproducibility"]["random_seed"]),
        },
    )
    return {
        "raw_cells": adata.n_obs,
        "retained_cells": int(retained.sum()),
        "pseudobulk_count": len(pseudobulk_metadata),
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare reviewed single-cell raw counts and subject pseudobulk."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--ontology", required=True)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--output-h5ad", required=True)
    parser.add_argument("--output-qc", required=True)
    parser.add_argument("--output-metrics", required=True)
    parser.add_argument("--output-counts", required=True)
    parser.add_argument("--output-metadata", required=True)
    parser.add_argument("--output-provenance", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    with Path(args.config).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    summary = prepare_single_cell_dataset(
        config,
        read_tsv(args.manifest),
        read_tsv(args.ontology),
        args.dataset_id,
        args.output_h5ad,
        args.output_qc,
        args.output_metrics,
        args.output_counts,
        args.output_metadata,
        args.output_provenance,
    )
    print(
        f"Prepared {args.dataset_id}: {summary['retained_cells']}/"
        f"{summary['raw_cells']} cells retained and "
        f"{summary['pseudobulk_count']} pseudobulk samples."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
