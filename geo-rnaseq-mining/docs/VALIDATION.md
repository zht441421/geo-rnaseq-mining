# Validation

## Purpose

This document records validation commands and the latest known results. It
separates dry-runs, fixture validation, targeted module tests, and unverified
production paths.

## Standard Commands

```bash
python -m compileall -q workflow scripts tests
python -m unittest discover -s tests/unit -p "test_*.py" -v
pytest tests/unit -q
python -m unittest discover -s tests/integration -p "test_*.py" -v
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --quiet
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1 --printshellcmds
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --forceall all_full
snakemake --snakefile workflow/Snakefile --cores 1 --configfile tests/fixtures/config/test_config.yaml
```

Real GEO/SRA integration tests are opt-in and require:

- `RUN_GEO_NETWORK_TESTS=1`
- `RUN_SRA_NETWORK_TESTS=1`
- `SRA_TEST_ACCESSION`

## Latest Known Results

This final handoff did not rerun the full test suite. Results below summarize
commands run during the split commits on 2026-07-03.

| Area | Command / Check | Result | Notes |
| --- | --- | --- | --- |
| P0 full verification | `python -m compileall -q workflow scripts tests` | Passed | Earlier P0 verification. |
| P0 full verification | `python -m unittest discover -s tests/unit -p "test_*.py" -v` | Passed | 145 tests OK at that time. |
| P0 full verification | `pytest tests/unit -q` | Passed | 145 passed, 2 warnings, 45 subtests passed at that time. |
| P0 full verification | `python -m unittest discover -s tests/integration -p "test_*.py" -v` | Passed | 3 tests OK; 2 opt-in GEO/SRA tests skipped. |
| P0 full verification | default Snakemake dry-run | Passed | Default dry-run only. |
| P0 full verification | default Snakemake real execution | Passed | Skeleton / validation / empty-accession path only. |
| P0 full verification | `all_full` dry-run | Passed | Expanded skeleton/all_full DAG. |
| P0 full verification | fixture MVP e2e | Passed | Explicit fixture path only. |
| Stage 2 metadata | `python -m unittest tests.unit.test_stage2_suggested_outputs -v` | Passed | 3 tests OK. |
| MVP hardening | `python -m unittest tests.unit.test_mvp_pipeline -v` | Passed | 9 tests OK. |
| MVP hardening | fixture MVP command | Passed | Later run reported outputs present/up to date; no jobs rerun. |
| Reporting | `python -m unittest tests.unit.test_final_reporting -v` | Passed | 6 tests OK. |
| Bulk hardening | `python -m unittest tests.unit.test_bulk_analysis -v` | Passed | 9 tests OK. |
| Single-cell annotation | `python -m unittest tests.unit.test_single_cell_preprocessing -v` | Passed | 9 tests OK; AnnData duplicate-name warnings appeared in one test. |
| Pseudobulk | `python -m unittest tests.unit.test_pseudobulk_de -v` | Passed | 10 tests OK. |
| Bulk/scRNA integration | `python -m unittest tests.unit.test_bulk_scrna_integration -v` | Passed | 8 tests OK. |
| Project skeleton | `python -m unittest tests.unit.test_project_skeleton -v` | Passed | Rerun in several later stages; 16 tests OK. |
| Env definitions | YAML parse check for `workflow/envs/*.yaml` | Passed | Parsed all env YAML files. |
| Default dry-run | `snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --quiet` | Passed | Rerun repeatedly; Conda strict channel priority warning remains. |

## Failed Items

- No failures were recorded in the targeted validations listed above.

## Not Run / Not Verified

- A fresh full unit suite after the final env commit was not run.
- A fresh full integration suite after the final env commit was not run.
- R-level DESeq2 validation was not run.
- Native R/Bioconductor path was not validated.
- Real GEO/SRA network tests were not run except as opt-in skipped tests during
  the earlier integration run.
- Production real-data end-to-end execution was not run.
- Full Conda env solve/install was not run.

## Interpretation Boundaries

- Dry-run success does not mean real execution success.
- Fixture MVP success does not mean production real-data workflow success.
- Default skeleton / empty-accession success does not mean real GEO/SRA or
  production analysis success.
- Suggested annotations are review-required and not final.
- Candidate gene outputs are review-required and not final biological
  conclusions.
- Do not claim unrun tests passed.
