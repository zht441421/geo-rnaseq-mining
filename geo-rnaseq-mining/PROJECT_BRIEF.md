# Project Brief

## Project

`geo-rnaseq-mining` is an enterprise MVP for GEO bulk RNA-seq and
scRNA-seq/snRNA-seq data mining. The MVP prioritizes reproducibility,
auditability, explicit user confirmation, and staged delivery over broad
feature coverage.

## MVP Goal

Deliver a minimal but stable workflow that can eventually support:

1. GEO/SRA metadata fetch.
2. Suggested manifest generation for human review.
3. Human-confirmed sample manifest, contrasts, and dataset plan validation.
4. Bulk RNA-seq differential expression from raw integer counts.
5. Single-cell QC, clustering, and candidate annotation outputs.
6. Subject-level single-cell pseudobulk differential expression.
7. Bulk to single-cell candidate gene mapping.
8. HTML report generation.
9. Test records and session handoff records.

## Operating Principle

The project follows a strict "human review plus automated execution" model.
Metadata fetched from GEO/SRA can suggest review fields, but it is never the
authority for formal biological decisions.

Formal analysis authority files:

- `metadata/reviewed/sample_manifest.tsv`
- `metadata/reviewed/contrasts.tsv`
- `metadata/reviewed/dataset_plan.tsv`
- `metadata/reviewed/celltype_ontology.tsv`

## Stage Policy

Only the current stage recorded in `docs/NEXT_TASK.md` may be executed. After
the current stage is complete, stop and update the handoff files before any
next-stage implementation.

## Out of Scope for MVP

The MVP reserves interfaces or TODOs, but does not implement:

- Complex multi-GSE meta-analysis.
- ComBat-seq.
- scVI deep integration.
- Cell-cell communication analysis.
- Trajectory analysis.
- RNA velocity.
- Regulatory network analysis.
- Automated biological conclusion generation.
- Production web UI.
- Task scheduling platform.
- User permission system.

## Non-Negotiable Constraints

1. Do not infer final groups from GEO titles, characteristics, or filenames.
2. Do not infer case/control, tissue, subject identity, or paired status.
3. Bulk differential expression must use raw integer counts.
4. TPM, FPKM, CPM, and log expression must not enter DESeq2.
5. Multiple GSE datasets must not be merged by default.
6. Stop joint models when `dataset_id` and `group` are fully confounded.
7. Single-cell group comparison must use subject-level pseudobulk.
8. Pseudobulk must use raw counts.
9. Do not treat single cells as independent biological replicates.
10. Integrated embeddings must not be used as DESeq2 input.
11. Automated cell annotation requires review status and is not final.
12. Do not automatically delete outlier samples without confirmation.
13. Do not claim unrun tests have passed.
