# Current State

## Date

2026-07-03 Asia/Shanghai

## Current Stage

Final split/cleanup handoff.

The implementation work from the workflow health-check follow-up has been
split into focused commits. Generated dirty files were cleaned. This handoff
does not continue feature development and does not rerun a full test suite.

## Overall Conclusion

The repository is substantially cleaner and the main workflow repair and
module-hardening changes are committed in small units. The default Snakemake
entry is executable for the safe skeleton / validation / empty-accession path,
and the explicit MVP fixture path remains separate.

This does not mean real production data, real GEO/SRA network access, native
R/Bioconductor execution, or production end-to-end analysis has been validated.

## Completed Commit Chain

- `e59ea116` `fix(workflow): make default entrypoint schema-valid and executable`
- `17ad95e4` `docs: add session handoff and validation state`
- `9ae0ec6e` `docs: refresh project overview and run modes`
- `ae003e58` `chore(workflow): add stage 1 compatibility skeleton rules`
- `b7c05b97` `refactor(authority): migrate reviewed inputs to metadata directory`
- `f97ed1cd` `feat(metadata): add stage 2 suggested output tooling`
- `9c10093b` `test(mvp): harden fixture e2e validation and provenance`
- `0745c142` `feat(reporting): surface test status and review limitations`
- `0611407b` `fix(bulk): reject non-raw count matrices before analysis`
- `04df21fe` `feat(scrna): mark suggested annotations as review-required`
- `bb26f073` `feat(scrna): aggregate pseudobulk by subject group and cell type`
- `b782ae25` `feat(integration): mark candidate genes as review-required`
- `18c5ec62` `chore(authority): update joint bulk reviewed metadata message`
- `098d682c` `chore(envs): add optional workflow conda environments`

## Completed Modules

- P0 default entry / schema / CI repair.
- Session handoff docs.
- README / project overview and run-mode boundaries.
- Stage 1 compatibility skeleton rules.
- Authority metadata migration to `metadata/reviewed/*`.
- Stage 2 metadata tooling and suggested outputs.
- MVP fixture e2e hardening, validation, provenance, and result path reporting.
- Reporting / test-status / review-limitations display.
- Bulk raw-count hardening.
- Single-cell suggested annotation review/finality contract.
- Pseudobulk implementation and DE input hardening.
- Bulk/scRNA integration candidate finality and confidence limits.
- `prepare_joint_bulk.py` reviewed metadata path message cleanup.
- Optional workflow Conda environment definitions.

## Current Remaining Items

- `scripts/*` top-level placeholders/scaffold remain untracked and undecided.
- `../AGENTS.md` remains untracked outside the repo subdirectory and has
  mojibake/encoding issues.
- Conda strict channel priority warning still appears during Snakemake dry-run.
- Real R/Bioconductor/DESeq2 execution has not been validated.
- Real GEO/SRA network paths have not been validated.
- Production real-data end-to-end execution has not been validated.
- Full Conda environment solve/install has not been validated.

## Git State Before This Handoff Update

- Branch: `123`
- HEAD: `098d682cb180748d73422038d779ad73811c04e6`
- Working tree before Markdown updates:

```text
?? ../AGENTS.md
?? scripts/build_manifest.py
?? scripts/bulk_deseq2.R
?? scripts/fetch_geo_metadata.R
?? scripts/integrate_bulk_sc.R
?? scripts/pseudobulk.R
?? scripts/render_report.R
?? scripts/scrna_scanpy.py
?? scripts/validate_contrasts.py
?? scripts/validate_dataset_plan.py
?? scripts/validate_manifest.py
```

After this handoff update, the docs modified by the handoff will also appear in
`git status --short` until committed or otherwise handled.

## Recent Validation Summary

This handoff did not rerun the full suite. It records the recent verification
performed during the split commits:

- P0 phase: full unit/integration/default/fixture MVP validation passed as
  recorded in `docs/VALIDATION.md`.
- Stage 2 metadata tooling: targeted unit tests and default dry-run passed.
- MVP e2e hardening: targeted unit tests passed; fixture command succeeded but
  reported outputs up to date during that later stage.
- Reporting/test-status: compileall, reporting unit tests, skeleton tests, and
  default dry-run passed.
- Bulk hardening: bulk unit tests, compileall, and default dry-run passed.
- Single-cell annotation: single-cell preprocessing tests, compileall, default
  dry-run, and skeleton tests passed.
- Pseudobulk: pseudobulk unit tests, compileall, default dry-run, and skeleton
  tests passed.
- Bulk/scRNA integration: integration unit tests, compileall, default dry-run,
  and skeleton tests passed.
- Env definitions: YAML parse check passed; default dry-run passed.

## Not Run

- A new full unit suite after the final env commit was not run.
- A new full integration suite after the final env commit was not run.
- `pytest tests/unit -q` was not rerun after the later split commits.
- R-level DESeq2 validation was not run.
- Real GEO/SRA network tests were not run.
- Full Conda env solve/install was not run.
- Production real-data end-to-end execution was not run.

## Production Boundaries

- Default dry-run success is not production validation.
- Default skeleton / empty-accession execution is not real GEO/SRA or real
  production analysis.
- Fixture MVP success is not production real-data validation.
- Suggested annotations are not reviewed and are not final.
- Candidate genes are review-required and are not final biological conclusions.
- R/Bioconductor/GEO/SRA production readiness remains unverified.

## Next Stage Entry

Read `docs/NEXT_TASK.md`. The next task is only to resolve remaining untracked
scaffolds and the instruction file. Do not start production e2e, new features,
or generated-file work during that task.
