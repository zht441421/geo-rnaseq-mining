# Current State

## Date

2026-07-03 Asia/Shanghai

## Current Stage

P0 workflow-entry repair complete; session handoff in progress.

This document reflects the repository state after the P0 fixes that made the
default Snakemake entry safe to execute while preserving explicit MVP fixture
execution. This Markdown handoff did not rerun tests; validation status below
comes from the most recent P0 repair verification performed in this session.

## Overall Conclusion

### Verified Facts

- The default Snakemake entry now completes with `config/config.yaml`.
- The default entry represents skeleton / validation / empty-accession
  execution only.
- The explicit MVP fixture path still runs through `mvp_pipeline` when invoked
  with `tests/fixtures/config/test_config.yaml`.
- Both `config/config.yaml` and `tests/fixtures/config/test_config.yaml` pass
  the strict config schema after the P0 repair.
- CI now includes a default skeleton execution step in addition to default
  dry-run and fixture MVP e2e.

### Not Verified / Inferred Risks

- Real GEO/SRA network fetching has not been run in this stage.
- Native R/Bioconductor DESeq2 execution has not been run in this stage.
- Real biological production data end-to-end execution has not been run.
- Dry-run success is not evidence of real execution success.
- Fixture MVP success is not evidence of production real-data workflow success.
- Default skeleton / empty-accession success is not evidence of real GEO/SRA or
  production analysis success.

## Workflow Run Modes

### Default Skeleton / Validation Mode

Command:

```bash
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1
```

Meaning: validates and runs the safe default empty-accession skeleton path.
Marker output records `mode=skeleton_validation` and
`production_validated=false`.

Not meaning: real GEO/SRA, native R/Bioconductor, or real production analysis
has completed.

### Explicit MVP Fixture Mode

Command:

```bash
snakemake --snakefile workflow/Snakefile --cores 1 --configfile tests/fixtures/config/test_config.yaml
```

Meaning: runs the MVP fixture e2e path using test fixture inputs and
`mvp_pipeline`.

Not meaning: production real-data workflow support has been validated.

### Real Production Mode

Requires explicit real inputs and runtime support:

- real `geo.accessions`;
- completed human-reviewed `metadata/reviewed/*` files;
- required references/indexes such as FASTA, GTF, Salmon, or STAR resources for
  enabled modules;
- suitable GEO/SRA, R/Bioconductor, and external-tool runtime;
- exact commands and observed results recorded after execution.

## Completed Content

- P0 default entry conflict fixed in `workflow/Snakefile`.
- P0 schema conflict fixed by adding optional strict `mvp` config schema.
- Fixture MVP config updated to satisfy strict schema without copying fixtures
  into default production config.
- README run-mode boundaries updated.
- CI default skeleton execution step added.
- Markdown handoff documents updated or created:
  - `docs/CURRENT_STATE.md`
  - `docs/CHANGELOG.md`
  - `docs/DECISIONS.md`
  - `docs/NEXT_TASK.md`
  - `docs/VALIDATION.md`

## Unfinished Content

- No real production run has been validated.
- No real GEO/SRA network run has been validated.
- No native R/Bioconductor DESeq2 run has been validated.
- No final commit/staging plan has been prepared for the large dirty working
  tree.

## Priority Status

- P0: Resolved for default entry, strict `mvp` schema support, and run-mode
  documentation.
- P1: Open. Some workflow rules still hard-code `config/config.yaml` or
  `metadata/reviewed/*`, reducing config portability.
- P2: Open. Conda warns that strict channel priority is not configured.
- P2: Open. Real GEO/SRA and native R/Bioconductor validation remain opt-in and
  unrun.
- P3: Open. Longer-term production profile separation and real-data validation
  automation remain future work.

## Modified Files Summary For P0 Repair

- `.github/workflows/ci.yml`: added default skeleton execution step.
- `README.md`: added/updated run-mode boundary language.
- `tests/fixtures/config/test_config.yaml`: added schema-required fixture
  placeholders while keeping fixture mode explicit.
- `workflow/Snakefile`: default `all` now routes to skeleton mode unless
  `mvp.enabled=true`.
- `workflow/schemas/config.schema.yaml`: added optional strict `mvp` section.

This Markdown handoff modified only allowed Markdown files.

## Recent Validation Record

These commands were run after the P0 repair and before this Markdown handoff.
This Markdown handoff did not rerun them.

| Command | Result | Key Notes |
| --- | --- | --- |
| `python -m compileall -q workflow scripts tests` | Passed | Static Python compilation succeeded. |
| `python -m unittest discover -s tests/unit -p "test_*.py" -v` | Passed | 145 tests OK. |
| `pytest tests/unit -q` | Passed | 145 passed, 2 warnings, 45 subtests passed. |
| `python -m unittest discover -s tests/integration -p "test_*.py" -v` | Passed | 3 tests OK; 2 opt-in GEO/SRA tests skipped. |
| `snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --quiet` | Passed | Default dry-run only. |
| `snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1 --printshellcmds` | Passed | Default skeleton / validation execution completed. |
| `snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --forceall all_full` | Passed | Dry-run expanded 23 skeleton/all_full jobs. |
| `snakemake --snakefile workflow/Snakefile --cores 1 --configfile tests/fixtures/config/test_config.yaml` | Passed | Explicit MVP fixture e2e completed through `mvp_pipeline`. |
| jsonschema validation for `config/config.yaml` | Passed | Default config passes schema. |
| jsonschema validation for `tests/fixtures/config/test_config.yaml` | Passed | Fixture MVP config passes schema. |

## Failed Tests

- No failures were recorded in the most recent P0 verification.

## Not Run

- This Markdown handoff did not rerun tests.
- Real GEO/SRA network tests were not run:
  - `RUN_GEO_NETWORK_TESTS=1`
  - `RUN_SRA_NETWORK_TESTS=1` plus `SRA_TEST_ACCESSION`
- Real configured GSE/GEOquery fetch was not run.
- Native R/Bioconductor DESeq2 execution was not run.
- Real biological production dataset e2e was not run.

## Known Risks

- The working tree is still dirty with many tracked modifications and untracked
  files spanning multiple stages.
- Some generated outputs and markers are present in the working tree.
- Default skeleton success can be misread as production readiness unless the
  run-mode boundaries are preserved.
- Native Windows may be unsuitable for full R/Bioconductor/GEOquery validation;
  Linux, WSL, or a container is recommended for real production validation.

## Git State Summary

- Branch: `123`
- HEAD: `cb85b98c6048774627084863bab5d99f0962d1bb`
- Working tree: dirty.
- Notable tracked modified files include:
  - `.github/workflows/ci.yml`
  - `README.md`
  - `config/config.yaml`
  - `tests/fixtures/config/test_config.yaml`
  - `workflow/Snakefile`
  - `workflow/schemas/config.schema.yaml`
  - multiple `workflow/rules/*` and `workflow/scripts/*` files
  - several unit test files
  - resource documentation files
- Notable untracked files include:
  - root `AGENTS.md`
  - `geo-rnaseq-mining/PROJECT_BRIEF.md`
  - `geo-rnaseq-mining/docs/*`
  - `metadata/reviewed/*.tsv`
  - additional workflow envs/rules/scripts and Stage 2 test files

Use `git status --short` for the exact current list before making any new
changes.

## Next Stage Entry

Read `docs/NEXT_TASK.md`. The next task is a commit-readiness and dirty-tree
audit only; do not start real-data validation or refactoring until that task is
complete or superseded by explicit user instruction.
