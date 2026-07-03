# Session Handoff

## Stage

Final split/cleanup handoff.

All requested implementation groups have been split into focused commits.
Generated dirty files were cleaned. This handoff updates documentation only.

## Git State

- Branch: `123`
- HEAD: `098d682cb180748d73422038d779ad73811c04e6`
- Working tree before this handoff document update:

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

After this handoff, the updated `docs/*.md` files will also be dirty until
committed or otherwise handled.

## Completed Commits

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

## Remaining Untracked

- `../AGENTS.md`
- `scripts/build_manifest.py`
- `scripts/bulk_deseq2.R`
- `scripts/fetch_geo_metadata.R`
- `scripts/integrate_bulk_sc.R`
- `scripts/pseudobulk.R`
- `scripts/render_report.R`
- `scripts/scrna_scanpy.py`
- `scripts/validate_contrasts.py`
- `scripts/validate_dataset_plan.py`
- `scripts/validate_manifest.py`

## Validation Summary

- Earlier P0 full validation passed, including unit discovery, pytest, limited
  integration tests, default dry-run, default skeleton execution, `all_full`
  dry-run, fixture MVP e2e, and schema checks.
- Each later implementation commit ran targeted tests plus default Snakemake
  dry-run before commit.
- The final env commit ran YAML parse checks and default Snakemake dry-run.
- Snakemake dry-runs continue to emit the Conda strict channel priority warning.

## Still Not Verified

- R/Bioconductor/DESeq2 production path.
- Real GEO/SRA network path.
- Production real-data end-to-end workflow.
- Full Conda environment solve/install.
- A fresh full test suite after the final env commit.

## Next Step

Resolve remaining untracked scaffolds and instruction file.

Read `docs/NEXT_TASK.md` before taking action. Do not stage, commit, delete, or
repair `scripts/*` or `../AGENTS.md` without explicit user confirmation.

## Boundaries

- Do not claim fixture/dry-run success as production validation.
- Do not claim suggested annotations are reviewed or final.
- Do not claim candidate genes are final biological conclusions.
- Do not commit `scripts/*` or `../AGENTS.md` without explicit review.
- Do not continue feature development during handoff.
