# scRNA-seq and snRNA-seq single-dataset analysis

## Stage boundary

Every GSE and every sample is preprocessed and quality-controlled independently
before any cross-dataset integration is considered. `single_cell.enabled=true`
enables preprocessing only. Subject-level pseudobulk and cell-proportion
analysis additionally require `single_cell.downstream_analysis_enabled=true`,
reviewed author labels, confirmed ontology mappings, contrasts, and a dataset
plan.

No preprocessing result authorizes cross-GSE integration.

## Supported inputs

The reviewed manifest `matrix_path` may reference:

- a 10X MTX directory;
- a 10X H5 file;
- a Cell Ranger output directory containing one filtered or raw matrix result;
- an H5AD file with `layers["counts"]`;
- an RDS containing a Seurat or SingleCellExperiment object with a counts assay;
- a Cell Ranger or equivalent quantification result generated from FASTQ.

RDS conversion uses `convert_single_cell_rds.R`, Seurat,
SingleCellExperiment, and zellkonverter. The resulting H5AD is temporary; the
source RDS is never modified.

## AnnData contract

All saved objects use AnnData. Barcodes become:

```text
dataset_id:sample_id:original_barcode
```

`obs` retains at least `dataset_id`, `gse_id`, `sample_id`, `subject_id`,
`group`, `batch`, `technology`, `tissue`, and `condition`. It also preserves
`original_barcode`, `author_label`, QC metrics, and filtering evidence.

`var` retains at least `gene_id_original`, `gene_id_canonical`, `gene_symbol`,
`reference_build`, and `mapping_status`. No unreviewed gene-ID remapping is
performed; absent mappings are recorded as identity mappings.

Matrix roles are explicit:

- `layers["counts"]`: immutable non-negative integer raw counts;
- pre-QC and post-QC `X`: raw counts;
- clustered `X`: normalize-total and log1p expression;
- `layers["log_normalized"]`: log-normalized expression;
- optional `layers["scaled"]`: scaled expression when explicitly enabled;
- `obsm["X_pca_unintegrated"]`: scaled-HVG PCA without integration;
- `obsm["X_umap"]`: neighbor-graph embedding.

## Per-sample QC

The workflow calculates separately within each `sample_id`:

- `total_counts`;
- `n_genes_by_counts`;
- `pct_counts_mt`;
- `pct_counts_ribo`;
- `pct_counts_hb`;
- `complexity`;
- doublet score and prediction;
- optional ambient-RNA score.

`single_cell.qc.strategy` selects `hard`, `mad`, or `combined`. Hard limits,
MAD multipliers, minimum cells for MAD, and gene prefixes all come from
`config/config.yaml`. MAD bounds are calculated independently per sample.
Every cell receives `qc_retained` and a semicolon-separated `filter_reason`.

If a sample has zero retained cells, the workflow stops after writing its
pre-QC object and QC evidence. It never silently removes the whole sample.

## Doublets and ambient RNA

Doublet estimation always loops over samples. Supported methods are:

- `scrublet` (default);
- `doubletdetection` (alternative).

Small samples receive an explicit `not_estimable_too_few_cells` status.
Predicted doublets affect cell retention only when
`doublet.exclude_predicted=true`.

Ambient RNA assessment is optional. `low_count_profile` estimates a
sample-specific background profile from the configured low-count quantile and
records an ambient score. It is an assessment, not an unrecorded count
correction.

## Normalization, clustering, and annotation suggestions

Post-QC cells undergo `normalize_total`, `log1p`, highly-variable gene
selection, transient scaling, unintegrated PCA, neighbors, UMAP, and Leiden.
The random seed and every parameter are configured and recorded.

Cluster outputs include:

- ranked cluster markers;
- marker dotplot;
- cluster-by-sample composition;
- cluster-by-author-label composition;
- `suggested_annotation`.

Marker-set annotation is advisory only. `author_label` and confirmed ontology
labels are never overwritten.

## Subject-level pseudobulk DE

Pseudobulk aggregation consumes `layers["counts"]` only. It groups cells by
`dataset_id`, `subject_id`, `sample_id`, `cell_type`, and configured
`single_cell.pseudobulk.extra_strata`. It never merges distinct subjects to
meet thresholds and never treats cells as case/control replicates.

Each pseudobulk sample records `subject_id`, `sample_id`, `dataset_id`,
`cell_type`, `group`, `cell_count`, `total_UMI`, `detected_genes`,
`eligibility`, and `exclusion_reason`. Eligibility is controlled by
`min_cells_per_pseudobulk`, `min_subjects_per_group`, `min_total_counts`, and
`min_detected_genes`.

Per-dataset DESeq2 uses raw aggregated counts, the reviewed design formula, and
reviewed contrasts from `contrasts.tsv`. Outputs include full and significant
DE results, PCA, MA plot, volcano plot, sample correlation, and subject/cell
statistics for each cell type.

Combined pseudobulk joint models, per-dataset pseudobulk Meta analysis, and
stratified validation are selected only by `dataset_plan.tsv`. Joint models
fail closed when dataset and group are completely confounded, the design matrix
is not full rank, a dataset lacks an estimable group comparison, or donor
counts are insufficient.

## Outputs

```text
results/per_dataset/<dataset_id>/single_cell/
├── preprocessing/.complete
├── objects/
│   ├── pre_qc.h5ad
│   ├── post_qc.h5ad
│   └── clustered.h5ad
├── qc/
│   ├── cell_qc.tsv
│   ├── sample_thresholds.tsv
│   ├── sample_summary.tsv
│   ├── doublet_status.tsv
│   └── ambient_rna_status.tsv
├── markers/
│   ├── cluster_markers.tsv
│   ├── cluster_sample_composition.tsv
│   ├── cluster_author_label_composition.tsv
│   └── suggested_annotations.tsv
├── plots/
│   ├── qc_by_sample.png
│   ├── pca_unintegrated.png
│   ├── umap.png
│   └── marker_dotplot.png
└── provenance/preprocessing.json
```

```text
results/per_dataset/<dataset_id>/pseudobulk/
├── input/
│   ├── raw_counts.tsv
│   └── sample_metadata.tsv
├── deseq2/
│   └── <contrast_id>/<cell_type>/
│       ├── deseq2_full_results.tsv
│       ├── deseq2_significant_results.tsv
│       ├── pca.png
│       ├── ma_plot.png
│       ├── volcano_plot.png
│       ├── sample_correlation.tsv
│       └── subject_cell_stats.tsv
└── provenance/pseudobulk.json
```

Cross-dataset pseudobulk outputs use:

```text
results/merged_analysis/scrna_pseudobulk/
results/meta_analysis/scrna_pseudobulk/
```

Run one dataset:

```bash
snakemake --profile profiles/local \
  results/per_dataset/<dataset_id>/single_cell/preprocessing/.complete
```
