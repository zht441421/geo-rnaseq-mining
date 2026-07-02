# Snakemake script wrappers

Rule-specific wrappers belong here. Reusable user-facing utilities belong under
`scripts/python/` or `scripts/R/`.

Bulk wrappers include strict matrix validation and staging, quantification
metric collection, Salmon/tximport aggregation, featureCounts normalization,
sample-level QC, DESeq2, and enrichment. Their contract is documented in
`resources/BULK_ANALYSIS.md`.

Multi-dataset bulk wrappers add guarded compatibility assessment, joint DESeq2,
per-dataset Meta analysis, strict stratified validation, and
leave-one-dataset-out stability analysis. Their contract is documented in
`resources/MULTI_DATASET_BULK.md`.

Single-cell wrappers resolve 10X, Cell Ranger, H5AD, and RDS inputs; enforce the
AnnData counts/metadata contract; perform sample-specific hard/MAD QC and
doublet estimation; generate unintegrated PCA, UMAP, Leiden, markers, and
advisory annotations; then optionally aggregate subject-level pseudobulk, run
per-cell-type DESeq2, and perform reviewed-strategy pseudobulk joint, Meta, or
validation summaries.
Their contract is documented in `resources/SINGLE_CELL_ANALYSIS.md`.

Bulk/single-cell integration wrappers combine bulk DE, bulk Meta/joint evidence,
single-cell marker and cell-type expression evidence, cell proportion summaries,
single-cell pseudobulk evidence, LODO stability, validation status, and confirmed
cell-type ontology into consensus gene, cell-type, support-matrix, scoring, and
plot-source tables. Dominant cell types are reported only as potential major
expression sources, not causal sources.

The reporting wrapper inventories result artifacts and hashes both results and
authority files. Its contract is documented in `resources/REPORTING.md`.
