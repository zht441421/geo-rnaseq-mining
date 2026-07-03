# Next Task

## Next Stage Goal

Resolve remaining untracked scaffolds and instruction file.

The only remaining untracked items after generated cleanup and env commits are
top-level `scripts/*` placeholders/scaffold and `../AGENTS.md`. The next
session should decide what to do with those files and stop.

## Scope

Allowed to inspect:

- `scripts/*`
- `../AGENTS.md`
- current Git status
- handoff docs listed below

Possible outcomes to plan, after user confirmation:

- delete `scripts/*`;
- convert `scripts/*` into real thin wrappers;
- commit `scripts/*` as explicit scaffold;
- repair or relocate `../AGENTS.md`;
- leave one or both groups untracked.

## Explicit Non-Goals

- Do not handle production e2e validation.
- Do not add new features.
- Do not modify workflow logic.
- Do not handle generated files.
- Do not rerun or claim R/Bioconductor/GEO/SRA production validation.
- Do not use `git clean`.
- Do not delete or commit `scripts/*` or `../AGENTS.md` without explicit user
  confirmation.

## Required Start Reads

Read these first:

- `docs/CURRENT_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/VALIDATION.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`

Then run:

```bash
git branch --show-current
git rev-parse HEAD
git status --short
git log --oneline -n 20
```

## Suggested Read-Only Inspection

```bash
git ls-files --others --exclude-standard
Get-Content -TotalCount 120 scripts/build_manifest.py
Get-Content -TotalCount 120 scripts/bulk_deseq2.R
Get-Content -TotalCount 120 scripts/fetch_geo_metadata.R
Get-Content -TotalCount 120 scripts/integrate_bulk_sc.R
Get-Content -TotalCount 120 scripts/pseudobulk.R
Get-Content -TotalCount 120 scripts/render_report.R
Get-Content -TotalCount 120 scripts/scrna_scanpy.py
Get-Content -TotalCount 120 scripts/validate_contrasts.py
Get-Content -TotalCount 120 scripts/validate_dataset_plan.py
Get-Content -TotalCount 120 scripts/validate_manifest.py
Get-Content -TotalCount 160 ../AGENTS.md
```

## Completion Standard

- Each remaining untracked file is classified.
- A user-approved action is selected for `scripts/*`.
- A user-approved action is selected for `../AGENTS.md`.
- No production validation or feature development is started.

## Stop Conditions

- Stop before deleting files.
- Stop before staging or committing files.
- Stop before repairing encoding or moving `../AGENTS.md`.
- Stop before implementing wrappers.

## Do Not Handle Opportunistically

- Conda strict channel priority.
- Real GEO/SRA network access.
- Native R/Bioconductor/DESeq2 execution.
- Production real-data e2e.
- Any generated output cleanup beyond the already completed generated cleanup.
