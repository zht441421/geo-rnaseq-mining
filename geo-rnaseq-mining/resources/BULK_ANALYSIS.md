# Single-dataset bulk RNA-seq analysis

The bulk module analyzes every `dataset_id` independently. It never pools GSE
samples, even when a later `dataset_plan.tsv` proposes a joint or Meta strategy.
All outputs are written under:

```text
results/per_dataset/{dataset_id}/bulk/
```

## Authority and activation

The module consumes only rows in `metadata/reviewed/sample_manifest.tsv` that
meet all of these conditions:

- `include=true`
- `review_status=confirmed`
- `data_type` contains `bulk`
- `data_type` does not contain `pseudobulk`

Set `bulk.enabled: true` only after the reviewed manifest, contrasts, and
dataset plan pass the pre-analysis gate. Every enabled bulk contrast must come
from `config/contrasts.tsv`, and its `analysis_id` must map to the dataset in
`config/dataset_plan.tsv`.

The workflow never changes `include`, `group`, `subject_id`, pairing, batch, or
contrast direction. Outliers remain in every derived matrix until the user
changes the reviewed manifest and reruns validation.

## Entry branch A: gene-level count matrix

Every included row for one dataset must reference the same `matrix_path`. The
matrix must have:

```text
gene_id  SAMPLE_1  SAMPLE_2  ...
```

The sample columns must exactly equal the included reviewed `sample_id` values
in the same order. The runtime validator rejects:

- duplicate sample columns;
- duplicate reviewed sample IDs;
- missing or extra sample columns;
- sample order differences;
- blank or duplicate gene IDs;
- missing, non-numeric, NaN, or infinite values;
- negative or non-integer counts;
- TPM/FPKM/CPM/log-like content or labels.

All-zero genes are reported but not removed from the staged raw-count copy.
DESeq2 creates a filtered derived object and records the filter count. The
reviewed source matrix is never overwritten.

## Entry branch B: FASTQ

Every included FASTQ sample must have `fastq_r1`; paired samples must also have
`fastq_r2`. One global configuration supplies the same reference definition,
strandedness, quantifier, and parameters to every sample in the dataset.

Required reference metadata:

```yaml
references:
  species: Homo sapiens
  genome_build: GRCh38
  annotation_release: <confirmed-release>
  gene_id_space: Ensembl_gene_id
  gtf: data/references/<annotation>.gtf
```

### Default: Salmon and tximport

```yaml
references:
  transcriptome_fasta: data/references/<transcriptome>.fa
  tx2gene: data/references/tx2gene.tsv
  salmon_index: data/references/salmon_index

bulk:
  quantification_method: salmon_tximport
  strandedness: unstranded
  salmon_libtype: A
```

The module runs FastQC for every sample, MultiQC for each dataset, Salmon for
each sample, and tximport for gene-level aggregation. It preserves the
unrounded tximport estimates and writes a separately rounded gene-count matrix
for count-model input. Tool logs, Salmon metadata, session information, and
version files remain in the dataset output tree.

### Optional: STAR and featureCounts

```yaml
references:
  fasta: data/references/<genome>.fa
  gtf: data/references/<annotation>.gtf
  star_index: data/references/star_index

bulk:
  quantification_method: star_featurecounts
  strandedness: unstranded
  featurecounts_strand: 0
```

STAR alignment runs per sample. featureCounts also runs per sample so reviewed
single- and paired-end layouts are handled explicitly; per-sample counts are
merged only after gene identity consistency checks.

## Quantification provenance

`qc/quantification_metrics.tsv` records:

- read or fragment count;
- mapped or mapping-equivalent count/rate;
- mapping metric type;
- library layout;
- configured strandedness;
- quantification method;
- genome, transcriptome, annotation, and gene ID references;
- quantifier version;
- quantification log path.

FastQC, MultiQC, Salmon, STAR, and featureCounts also write version files in
their own output directories. `provenance/input_provenance.json` records the
input matrix checksum, reviewed sample order, reference settings, and branch.

## Sample-level QC

The QC module writes:

```text
qc/sample_level/sample_qc_metrics.tsv
qc/sample_level/pca_coordinates.tsv
qc/sample_level/pca.png
qc/sample_level/sample_distance_heatmap.png
qc/sample_level/correlation_heatmap.png
qc/sample_level/hierarchical_clustering.png
qc/sample_level/qc_annotations.tsv
qc/sample_level/outlier_report.tsv
qc/sample_level/qc_session_info.txt
```

Annotations include available dataset, group, batch, sex, age, and subject
fields. Robust z scores are calculated for library size, detected genes, and
PCA distance. `outlier_report.tsv` always writes
`retained_for_analysis=true`; a flagged sample requires user review and a
reviewed manifest change, not automatic deletion.

## DESeq2

For each enabled bulk contrast, the module:

1. selects the current dataset only;
2. applies the user-confirmed optional subset;
3. keeps numerator and denominator samples;
4. coerces confirmed identifiers/categorical covariates to factors and a fully
   numeric age field to numeric;
5. constructs the exact `design_formula`;
6. recalculates the design matrix and stops unless it is full rank;
7. relevels `group` to the confirmed denominator;
8. runs DESeq2 without mutating the staged raw counts.

Formulas can reference `batch`, `dataset`/`dataset_id`, `sex`, `age`,
`subject_id`, `paired_group`, and interaction syntax supported by R formulas.
Because the module is single-dataset, a dataset term has zero variance and will
correctly fail the full-rank check unless the executed design actually contains
more than one estimable dataset level. Paired designs must include
`subject_id` or `paired_group`.

Each contrast directory contains:

```text
deseq2_full_results.tsv
deseq2_significant_results.tsv
normalized_counts.tsv
vst_matrix.tsv or rlog_matrix.tsv
design_matrix.tsv
contrast_qc.tsv
sample_cooks_distance.tsv
results_names.txt
ma_plot.png
volcano_plot.png
deg_heatmap.png
pca.png
session_info.txt
```

The full result is always retained. Significance uses
`bulk.deseq2_alpha` and `bulk.deseq2_abs_log2fc`.

## Enrichment and effect summaries

`deseq2/effect_direction_summary.tsv` records tested, significant, up, and
down gene counts plus effect-size summaries.

The base enrichment runner supports:

- GO over-representation analysis from `bulk.enrichment.go_gmt`;
- Reactome or KEGG over-representation analysis from
  `bulk.enrichment.pathway_gmt`;
- preranked GSEA from `bulk.enrichment.gsea_gmt`.

Missing GMT inputs produce explicit `skipped_missing_gmt` status records and
empty schema-correct result tables. They do not invent gene mappings.

WGCNA-style co-expression modules, NNLS immune infiltration, gene-set z-score
analysis, and univariate Cox survival analysis remain disabled by default.
They run only when their individual switches and required inputs are supplied.
`optional_modules/optional_modules_status.tsv` records each requested state and
outcome. No optional module overwrites counts or DESeq2 outputs.

## Commands

Validate all authority files and the analysis gate:

```bash
snakemake --profile profiles/local \
  resources/validation/.preanalysis_validation_passed
```

Run one dataset:

```bash
snakemake --profile profiles/local \
  results/per_dataset/<dataset_id>/bulk/.complete
```

Run all enabled, reviewed bulk datasets:

```bash
snakemake --profile profiles/local
```

The supplied Conda environments are the reproducible deployment contract.
Native Windows can run the R analysis scripts from an externally provisioned
compatible R/Bioconductor environment. FASTQ command-line tools remain most
portable under Linux/WSL/SLURM through the per-rule Conda environments.

## Tests

```bash
python -m unittest tests.unit.test_bulk_analysis -v
python -m unittest discover -s tests/unit -p "test_*.py" -v
```

The bulk tests cover simulated integer counts, fractional-count rejection,
sample-order rejection, non-full-rank design rejection, paired full-rank
design, and the invariant that outliers are never removed automatically.
