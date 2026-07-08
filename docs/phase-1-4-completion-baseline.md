# Phase 1.4 Completion Baseline

This document records the Phase 1.4 completion baseline and operator handoff
for `geo-rnaseq-mining`. It is a documentation and test baseline only. It does
not introduce runtime execution, production execution, network access, data
download, analysis output, persistence, a queue, a worker, or a scheduler.

## Baseline

- Current branch: `123`
- Current baseline commit:
  `e2ffee42e6bf72e4a3e1a72445a357ed19924ad1`
- Short baseline commit: `e2ffee4`
- Baseline meaning: Phase 1.4a through Phase 1.4f are complete as mock,
  contract, validation, API integration, and rejection hardening work.

## Phase 1.4 Completed Units

- Phase 1.4a controlled execution boundary
- Phase 1.4b dry-run execution request contract
- Phase 1.4c dry-run validation / rejection matrix
- Phase 1.4d pure dry-run validator skeleton
- Phase 1.4e API mock integration
- Phase 1.4f API rejection matrix hardening

The completed chain is:

```text
controlled execution boundary
-> dry-run execution request contract
-> validation / rejection matrix
-> pure dry-run validator skeleton
-> API mock integration
-> API rejection matrix hardening
```

## Current Safety Guarantees

The current baseline preserves these safety guarantees:

- no real GEO download
- no real RNA-seq pipeline
- no Snakemake execution
- no real Coze call
- no external network call from validator/mock tests
- no external network
- no long-running server
- no real artifacts
- no database
- no worker / scheduler
- no real execution runner
- no secrets in repo

These guarantees apply to the dry-run validator, the mock API integration, the
HTTP mock tests, and the Phase 1.4 documentation tests. They do not certify any
future runtime integration.

## Current Contract

The current Phase 1.4 contract is:

- dry-run validator returns deterministic accepted/rejected result
- rejection reasons are stable
- deterministic rejection reasons are preserved through mock API responses
- `output_format` `json`, `markdown`, and `html` are allowed
- `output_format` `zip` is rejected
- unsafe dataset accession rejected
- command/shell/subprocess fields rejected
- secret/token/password/api_key fields rejected
- artifact/database/worker/scheduler intent rejected
- multiple rejection reasons returned together
- mock API returns validation report
- accepted dry-run is not_started
- rejected dry-run is not_started and has no job_id
- ordinary mock job still returns job_id

Accepted dry-run validation only means the request shape passed the dry-run
contract. It does not mean any real execution was approved, queued, scheduled,
started, or persisted.

Rejected dry-run validation reports must remain deterministic and must not
allocate `job_id`.

## Operator Handoff

This operator handoff is for keeping Phase 1.4 safe while deciding whether a
future Phase 1.5 or Phase 1.4h should exist.

Safe tests for this baseline:

```bash
python -m pytest tests/test_phase_1_4_completion_baseline_docs.py -q -p no:cacheprovider
python -m pytest tests/test_phase_1_4_execution_boundary_docs.py tests/test_phase_1_4b_dry_run_request_contract_docs.py tests/test_phase_1_4c_dry_run_validation_matrix_docs.py -q -p no:cacheprovider
python -m pytest tests/test_phase_1_4d_dry_run_validator.py tests/test_phase_1_4e_api_mock_dry_run_validator.py tests/test_phase_1_4f_api_rejection_matrix.py -q -p no:cacheprovider
python -m unittest tests.test_api_mock tests.test_api_http_server -v
```

These tests are safe because they are documentation checks, pure function
checks, in-memory mock service checks, or short-lived loopback HTTP mock checks.

Tests that must not be added without review:

- tests that download GEO or SRA data
- tests that run an RNA-seq pipeline
- tests that run Snakemake
- tests that call real Coze services
- tests that make external network calls
- tests that start a long-running server
- tests that write real artifacts
- tests that write a database
- tests that create a queue, worker, or scheduler
- tests that require secrets, tokens, passwords, or API keys

A future change violates the safety boundary if it introduces automatic
network calls, writes persistent state, accepts arbitrary commands, starts
workflow execution, allocates a real execution runner, treats mock artifacts as
deliverables, or allows dry-run validation to schedule real work.

## Before Real Runtime Execution

Before any future real runtime execution is considered, a separate reviewed
design must define:

- explicit opt-in
- operator approval
- validated input manifest
- output sandbox
- audit/report-only preview
- no automatic network calls
- controlled runner / worker design
- persistence boundary
- persistence boundary design
- secrets management outside repo

Those controls must be designed before any production runner, durable job
store, queue, scheduler, worker, external data access, or report writer exists.

## Next Possible Phase

Phase 1.5 or Phase 1.4h should be decided separately. No real execution may be
introduced automatically.

If runtime integration is considered, it should start with a read-only design
or a dry-run-only API preview. That preview must preserve the current baseline:
no real GEO download, no real RNA-seq pipeline, no Snakemake execution, no real
Coze call, no external network, no real artifacts, no database, no worker /
scheduler, and no real execution runner.
