# geo-rnaseq-mining

Enterprise MVP scaffold for mining GEO bulk RNA-seq and scRNA-seq/snRNA-seq
datasets with an auditable "human review first, automated execution second"
workflow.

This repository is currently handed off at Stage 1: project skeleton,
documentation framework, and Snakemake scaffolding. The project directory also
contains pre-existing experimental workflow modules from earlier work; they are
not promoted by this handoff as the requested Stage 2-8 MVP deliverables.

## Authority Model

GEO/SRA metadata is reference material only. Formal analyses must use the
human-reviewed authority files:

- `metadata/reviewed/sample_manifest.tsv`
- `metadata/reviewed/contrasts.tsv`
- `metadata/reviewed/dataset_plan.tsv`
- `metadata/reviewed/celltype_ontology.tsv`

Suggested files may help review, but must not be used as formal analysis input
until the user confirms the required fields.

## Run Modes

The default configuration is a safe skeleton / validation mode. It uses the
empty-accession `config/config.yaml` and reviewed metadata templates, and it can
complete without real GEO/SRA network access or production references:

```bash
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1
```

This default success means the configured skeleton, validation, empty metadata,
and data-inventory path can run. It does not prove that a real biological
analysis, real GEO/SRA fetch, native R/Bioconductor execution, or production
bulk/single-cell workflow has completed.

The MVP fixture end-to-end path is explicit and uses only test fixtures:

```bash
snakemake --snakefile workflow/Snakefile --cores 1 --configfile tests/fixtures/config/test_config.yaml
```

Do not copy fixture paths into `config/config.yaml` for production analysis.

For a real production run, provide real `geo.accessions`, completed
human-reviewed files under `metadata/reviewed/`, reference/index paths such as
FASTA/GTF/Salmon/STAR resources as required by the enabled modules, and a
runtime with the needed GEO/SRA, R/Bioconductor, and external tool
dependencies. Record the exact production validation commands and results
before claiming real-data support.

## Non-Negotiable Constraints

- Do not infer final case/control groups from GEO titles, characteristics, or
  filenames.
- Do not infer subject identity, tissue, paired status, or inclusion status
  without user confirmation.
- Bulk DESeq2 input must be raw integer counts, not TPM, FPKM, CPM, or log
  expression.
- Multiple GSE datasets must not be merged by default.
- Joint models must stop when `dataset_id` and `group` are fully confounded.
- Single-cell differential analysis must use subject-level pseudobulk raw
  counts.
- Individual cells must not be treated as biological replicates.
- Integrated embeddings are for visualization, graph construction, clustering,
  and label transfer only; they must not be used as DESeq2 input.
- Automated cell-type annotations are candidate annotations only and require a
  review status.
- Do not remove outlier samples automatically without confirmation.
- Do not report unrun tests as passed.

## Stage 1 Contents

- Project context documents under `docs/`
- Manual authority file templates under `metadata/reviewed/` and `config/`
- Snakemake entrypoint under `workflow/Snakefile`
- Rule skeletons under `workflow/rules/`
- Conda environment skeletons under `workflow/envs/`
- Stage placeholder scripts under `scripts/`
- Test documentation under `tests/`

## Required Start-of-Session Reads

Every future development session must first read and reconcile:

- `PROJECT_BRIEF.md`
- `docs/CURRENT_STATE.md`
- `docs/DECISIONS.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`
- `docs/SESSION_HANDOFF.md`

Then inspect the actual file state. Do not rely on chat history.

## Stage 1 Verification

Run the skeleton checks from the repository root:

```bash
python -m unittest tests.unit.test_project_skeleton -v
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --quiet
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1
```

If a command is not available in the current environment, record it as not run
or failed in `docs/CURRENT_STATE.md` and `docs/SESSION_HANDOFF.md`.

## Next Stage

The next authorized work is Stage 2: GEO/SRA metadata fetch and suggested
manifest generation. See `docs/NEXT_TASK.md`.
