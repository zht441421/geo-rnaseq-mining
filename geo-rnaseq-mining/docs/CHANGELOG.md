# Changelog

## 2026-07-03 - P0 Default Entry Repair And Markdown Handoff

### Changed

- Repaired the default Snakemake entry so `config/config.yaml` can execute the
  safe skeleton / validation / empty-accession path without requiring
  `mvp.enabled=true`.
- Kept the MVP e2e path explicit through
  `tests/fixtures/config/test_config.yaml`.
- Added strict optional `mvp` config schema support while preserving
  `additionalProperties: false`.
- Added CI coverage for default skeleton real execution.
- Added run-mode boundary documentation to README.
- Updated Markdown handoff documents for low-context continuation.

### Modified Files

- `.github/workflows/ci.yml`
- `README.md`
- `tests/fixtures/config/test_config.yaml`
- `workflow/Snakefile`
- `workflow/schemas/config.schema.yaml`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/DECISIONS.md`
- `docs/NEXT_TASK.md`
- `docs/VALIDATION.md`

### Validation

- `python -m compileall -q workflow scripts tests`: passed.
- `python -m unittest discover -s tests/unit -p "test_*.py" -v`: passed,
  145 tests OK.
- `pytest tests/unit -q`: passed, 145 passed, 2 warnings, 45 subtests passed.
- `python -m unittest discover -s tests/integration -p "test_*.py" -v`:
  passed, 3 tests OK with 2 opt-in GEO/SRA tests skipped.
- `snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --quiet`:
  passed.
- `snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1 --printshellcmds`:
  passed; this is default skeleton / validation execution only.
- `snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --forceall all_full`:
  passed; dry-run expanded 23 skeleton/all_full jobs.
- `snakemake --snakefile workflow/Snakefile --cores 1 --configfile tests/fixtures/config/test_config.yaml`:
  passed; explicit MVP fixture e2e completed.

This Markdown handoff did not rerun tests; it records the latest P0 repair
verification above.

### Known Issues

- Real GEO/SRA network tests were not run.
- Native R/Bioconductor DESeq2 execution was not run.
- Real production biological dataset e2e execution was not run.
- The working tree remains dirty with many tracked modifications and untracked
  files from multiple stages.

### Notes

- Default skeleton success must not be described as production validation.
- Fixture MVP success must not be described as real-data production success.
- Dry-run success must not be described as real execution success.

## 2026-07-03

### Stage 9 Added

- Added `write_test_status` to `workflow/scripts/final_reporting.py`.
- Added `collect_test_status` to reporting rules.
- Added final-reporting unit coverage for default test-status rows.

### Stage 9 Changed

- HTML reporting now consumes a machine-readable `test_status.tsv` when
  reporting is enabled.
- Reproducibility manifest inputs now include `test_status.tsv`.
- Default generated test-status rows explicitly record tests and real-runtime
  validations as `not_run`, never as passed.

### Stage 9 Verified

- Targeted final-reporting/project-skeleton tests passed: 22 tests OK.
- Full unit suite passed: 145 tests OK.
- Integration suite passed: 3 tests OK, 2 opt-in network/SRA tests skipped.
- Snakemake dry-run passed.
- `all_full` passed on the default empty-accession configuration; all requested
  files were present and up to date.

### Stage 9 Known Limits

- Real GEO/SRA network tests were not run.
- Native R/Bioconductor DESeq2 execution was not run.
- Real biological dataset end-to-end execution was not run.
- No further MVP feature stage remains; next work is final review and
  real-data/native-runtime validation.

### Stage 8 Added

- Added report coverage for candidate gene and automated annotation review
  limitations.
- Added HTML report sections for automated review status and test/execution
  status.

### Stage 8 Changed

- `final_reporting.py` now renders candidate gene scores as
  hypothesis-generating evidence requiring human review.
- `final_reporting.py` now states that no tests are reported as passed when no
  machine-readable test-status artifact is supplied.
- `reporting.smk` now passes candidate score and suggested annotation TSVs to
  the report when the corresponding modules are enabled.
- `generate_project_report.py` now includes explicit test-status and
  known-limitations language.

### Stage 8 Verified

- Reporting targeted tests passed: 10 tests OK.
- Full unit suite passed: 144 tests OK.
- Integration suite passed: 3 tests OK, 2 opt-in network/SRA tests skipped.
- Snakemake dry-run passed.
- `all_full` passed on the default empty-accession configuration; all requested
  files were present and up to date.

### Stage 8 Known Limits

- Report rendering from a real completed biological dataset package was not run
  in this stage.
- Real GEO/SRA network tests and native R/Bioconductor execution remain
  unverified in this local session.
- Test-record and final handoff reconciliation is deferred to Stage 9.

### Stage 7 Added

- Added bulk-to-single-cell integration tests for:
  - opposite bulk/pseudobulk direction limiting confidence;
  - single-GSE support limiting confidence;
  - candidate gene scores being marked as non-final and requiring human review.

### Stage 7 Changed

- `candidate_gene_scores.tsv` now includes
  `is_final_biological_conclusion` and `required_action`.
- Candidate confidence is now limited by ambiguous one-to-many gene mapping,
  opposite bulk/pseudobulk direction, single-GSE support, or validation failure.

### Stage 7 Verified

- Bulk/scRNA integration targeted tests passed: 8 tests OK.
- Related multi-dataset/pseudobulk tests passed: 21 tests OK.
- Full unit suite passed: 143 tests OK.
- Integration suite passed: 3 tests OK, 2 opt-in network/SRA tests skipped.
- Snakemake dry-run passed.
- `all_full` passed on the default empty-accession configuration; all requested
  files were present and up to date.

### Stage 7 Known Limits

- Real biological dataset bulk-to-single-cell integration was not run in this
  stage.
- Native R/Bioconductor DESeq2 execution was not run in this stage.
- HTML report generation readiness is deferred to Stage 8.

### Stage 6 Added

- Added pseudobulk tests for subject/group-level aggregation, provenance
  threshold recording, and R-side raw-count validation before coercion.

### Stage 6 Changed

- Pseudobulk aggregation now groups by dataset, subject, group, and cell type
  instead of dataset, subject, sample, and cell type.
- `prepare_single_cell_pseudobulk.py` now records eligibility counts,
  threshold settings, and `cell_replication_used=false` in provenance.
- `run_single_cell_pseudobulk_deseq2.R` now validates finite non-negative
  integer raw aggregated counts before integer coercion.

### Stage 6 Verified

- Pseudobulk targeted tests passed: 10 tests OK.
- Single-cell targeted tests passed: 14 tests OK.
- Full unit suite passed: 142 tests OK.
- Integration suite passed: 3 tests OK, 2 opt-in network/SRA tests skipped.
- Snakemake dry-run passed.
- `all_full` passed on the default empty-accession configuration; all requested
  files were present and up to date.

### Stage 6 Known Limits

- Native R/Bioconductor pseudobulk DE execution was not run in this stage.
- Bulk-to-single-cell candidate mapping is deferred to Stage 7.

### Stage 5 Added

- Added single-cell candidate annotation contract coverage in
  `tests/unit/test_single_cell_preprocessing.py`.

### Stage 5 Changed

- `suggested_annotations.tsv` now records `review_status`, `is_final`, and
  `required_action` for automated candidate labels.
- Clustered AnnData objects now record suggested annotation review status and
  finality in `obs`.
- Single-cell preprocessing provenance now includes `matrix_contract` and
  `annotation_contract`.

### Stage 5 Verified

- Single-cell/reporting targeted tests passed: 14 tests OK.
- Pseudobulk/integration guard tests passed: 15 tests OK.
- Full unit suite passed: 140 tests OK.
- Integration suite passed: 3 tests OK, 2 opt-in network/SRA tests skipped.
- Snakemake dry-run passed.
- `all_full` passed on the default empty-accession configuration; all requested
  files were present and up to date.

### Stage 5 Known Limits

- Real single-cell dataset execution was not run in this stage.
- Subject-level pseudobulk DE readiness is deferred to Stage 6.

### Stage 4 Added

- Added bulk raw-count readiness tests for:
  - TPM-named integer matrices.
  - CPM-like integer matrices.
  - R-side raw-count validation before coercion.

### Stage 4 Changed

- Hardened `workflow/scripts/run_bulk_deseq2.R` to validate finite
  non-negative integer raw counts before integer coercion.
- Hardened `workflow/scripts/run_bulk_qc.R` to validate finite non-negative
  integer raw counts before QC calculations.

### Stage 4 Verified

- Bulk targeted tests passed: 9 tests OK.
- MVP/data-entry targeted tests passed: 21 tests OK.
- Full unit suite passed: 139 tests OK.
- Integration suite passed: 3 tests OK, 2 opt-in network/SRA tests skipped.
- Snakemake dry-run passed.
- `all_full` passed on the default empty-accession configuration; all requested
  files were present and up to date.

### Stage 4 Known Limits

- Native DESeq2 execution with a real R/Bioconductor runtime was not run in this
  stage.
- Real GEO/SRA network tests remain opt-in and were not run.

### Stage 3 Added

- Added authority-path regression coverage in
  `tests/unit/test_project_skeleton.py`.
- Added explicit missing-authority-file coverage in
  `tests/unit/test_authority_config.py`.

### Stage 3 Changed

- Switched formal authority defaults and rule inputs to reviewed paths:
  - `metadata/reviewed/sample_manifest.tsv`
  - `metadata/reviewed/contrasts.tsv`
  - `metadata/reviewed/dataset_plan.tsv`
  - `metadata/reviewed/celltype_ontology.tsv`
- Updated `config/config.yaml` so `single_cell.celltype_ontology_file` and
  `multi_dataset.dataset_plan_file` point at `metadata/reviewed/*`.
- Updated validation, bulk, single-cell, multi-dataset, integration, and
  reporting rules to consume reviewed authority files for formal inputs.
- Updated `workflow/scripts/authority_config.py` to report missing reviewed
  authority files as `MISSING_AUTHORITY_FILE` with `source_sha256` value
  `MISSING`.
- Updated README, project brief, decisions, and authority-related resources to
  describe `metadata/reviewed/*` as the formal authority location.

### Stage 3 Verified

- Targeted authority/path tests passed: 27 tests OK.
- Snakemake dry-run passed.
- Full unit suite passed: 136 tests OK.
- Integration suite passed: 3 tests OK, 2 opt-in network/SRA tests skipped.
- `all_full` passed on the default empty-accession configuration. The initial
  Stage 3 run completed 23 of 23 jobs; the final handoff rerun reported all
  requested files present and up to date.

### Stage 3 Known Limits

- Real GEO/SRA network tests remain opt-in and were not run in this stage.
- Real configured GSE fetching still needs a compatible R/Bioconductor runtime.

### Stage 2 Added

- Added `workflow/scripts/fetch_geo_metadata.py` as a portable wrapper that
  writes header-only GEO raw metadata when no GSE accessions are configured and
  delegates configured accessions to `run_rscript.py`/GEOquery.
- Added `workflow/scripts/prepare_dataset_plan_suggested.py`.
- Added `workflow/scripts/prepare_data_entry_classification.py`.
- Added `metadata/reviewed/dataset_plan.tsv`,
  `metadata/reviewed/contrasts.tsv`, and
  `metadata/reviewed/celltype_ontology.tsv` header templates.
- Added `tests/unit/test_stage2_suggested_outputs.py`.

### Stage 2 Changed

- `fetch_geo_supplementary_index` now writes
  `metadata/raw/geo_supplementary_files_raw.tsv` and keeps the prior
  `metadata/raw/supplementary_files_raw.tsv` as a compatibility copy.
- `generate_metadata_review_report.py` now accepts suggested dataset-plan and
  data-entry classification inputs.
- `workflow/rules/metadata.smk` now includes `prepare_dataset_plan_suggested`
  and `prepare_data_entry_classification` in the metadata review DAG.

### Stage 2 Verified

- Stage 2 path check passed: 17 required paths present.
- Project skeleton unit test passed: 15 tests OK.
- Full unit suite passed: 134 tests OK.
- Integration suite passed: 3 tests OK, 2 opt-in network/SRA tests skipped.
- Snakemake dry-run passed.
- Default empty-accession `all_full` check passed on Windows without R; the DAG
  was already up to date.

### Stage 2 Known Limits

- Real GEOquery fetching with configured accessions still requires a working
  R/Bioconductor environment, best run on Linux/WSL/container rather than native
  Windows.

### Added

- Added `PROJECT_BRIEF.md`.
- Added persistent context documents:
  - `docs/CURRENT_STATE.md`
  - `docs/DECISIONS.md`
  - `docs/CHANGELOG.md`
  - `docs/NEXT_TASK.md`
  - `docs/SESSION_HANDOFF.md`
- Added top-level Stage 1 placeholder scripts requested by the MVP plan.
- Added compatibility rule skeleton files for the requested rule names.
- Added requested conda environment skeletons:
  - `workflow/envs/metadata.yaml`
  - `workflow/envs/bulk.yaml`
  - `workflow/envs/scrna.yaml`
  - `workflow/envs/report.yaml`
- Added `.gitkeep` markers for required empty deliverable directories.

### Changed

- Updated `README.md` to describe the Stage 1 handoff and authority model.

### Not Implemented

- Real GEO/SRA network validation on this Windows host.
- DESeq2 analysis.
- Scanpy analysis.
- Pseudobulk analysis.
- Bulk to single-cell integration.
- Report rendering.

### Verified

- Stage 1 required path check passed.
- Project skeleton unit test passed: 15 tests OK.
- Snakemake dry-run passed with exit code 0.
- Full existing unit test suite passed: 122 tests OK.
