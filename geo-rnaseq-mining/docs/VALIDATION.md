# Validation

## Purpose

This file records the fixed validation command set and the latest known
verification summary for the repository. It separates dry-run, fixture e2e,
default skeleton execution, and real production validation.

## Standard Commands

### Static Python Compilation

```bash
python -m compileall -q workflow scripts tests
```

### Unit Tests

```bash
python -m unittest discover -s tests/unit -p "test_*.py" -v
pytest tests/unit -q
```

### Integration Tests

```bash
python -m unittest discover -s tests/integration -p "test_*.py" -v
```

Real GEO/SRA integration tests are opt-in and require environment variables:

- `RUN_GEO_NETWORK_TESTS=1`
- `RUN_SRA_NETWORK_TESTS=1`
- `SRA_TEST_ACCESSION`

### Default Snakemake Dry-Run

```bash
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --quiet
```

### Default Snakemake Real Execution

```bash
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --cores 1 --printshellcmds
```

This is default skeleton / validation / empty-accession execution only.

### all_full Dry-Run

```bash
snakemake --snakefile workflow/Snakefile --configfile config/config.yaml --dry-run --forceall all_full
```

### Fixture MVP E2E

```bash
snakemake --snakefile workflow/Snakefile --cores 1 --configfile tests/fixtures/config/test_config.yaml
```

This uses fixture data only.

## Latest Run Summary

Latest validation source: P0 default-entry repair verification from
2026-07-03 Asia/Shanghai.

This Markdown handoff did not rerun tests. The table below records the latest
known results from the immediately preceding P0 verification.

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

## Failed Items

- No failures were recorded in the latest P0 verification.

## Not Run

- This Markdown handoff did not rerun tests.
- Real GEO/SRA network tests were not run.
- Real configured GSE/GEOquery fetch was not run.
- Native R/Bioconductor DESeq2 execution was not run.
- Real biological production dataset e2e was not run.

## Interpretation Boundaries

- Dry-run success does not mean real execution success.
- Fixture MVP success does not mean production real-data workflow success.
- Default skeleton / empty-accession success does not mean real GEO/SRA or
  production analysis success.
- Default real execution currently means the configured skeleton / validation
  path completed and wrote `production_validated=false`.
- Do not claim unrun tests passed.
