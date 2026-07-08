# Phase 1.4f API Rejection Matrix Hardening

Phase 1.4f hardens the mock API rejection matrix coverage added around the
Phase 1.4e dry-run validator integration. This phase adds tests and
documentation only. It does not broaden validator behavior and does not
introduce real execution.

## Scope

Phase 1.4f covers the mock API submit path at two layers:

- `MockJobService.submit_job(payload)`
- HTTP `POST /jobs`

The tests verify that validator rejection reasons are passed through the mock
API response without creating a job or starting execution.

## Service-Layer Rejection Coverage

The service-layer matrix now covers:

- `mode=run` and `mode=execute`
- `allow_network=true`
- `allow_pipeline_execution=true`
- `allow_snakemake=true`
- `allow_real_coze_call=true`
- `operator_approved=true`
- `output_format=zip`
- unsafe `dataset_accession` values, including URL-like values and shell-like
  fragments
- `command`, `shell`, `subprocess`, `snakemake`, and `snakefile` fields
- `secret`, `token`, `password`, and `api_key` field names
- artifact write intent
- database write intent
- worker and scheduler intent
- multi-risk payloads returning multiple deterministic rejection reasons

Rejected dry-run validation reports do not include `job_id`. They keep
`execution` set to `not_started`.

Accepted dry-run validation reports also keep `execution` set to `not_started`
and do not include `job_id`.

## HTTP Rejection Coverage

The HTTP matrix verifies:

- rejected dry-run `POST /jobs` responses include
  `validation.accepted=false`
- rejected dry-run HTTP responses include deterministic
  `validation.rejection_reasons`
- rejected dry-run HTTP responses do not include `job_id`
- accepted dry-run HTTP responses remain `not_started` and say no real
  execution has started
- ordinary mock job submit still returns `201` and a mock `job_id`
- dry-run validation reports still return `200`

## Existing Contract Compatibility

The ordinary mock job contract is unchanged:

- `json`, `markdown`, and `html` remain allowed `output_format` values.
- `zip` remains rejected.
- ordinary mock job submit returns `201` and a `job_id`.
- existing happy-path and negative-path API tests remain in place.

## Safety Boundary

Phase 1.4f does not:

- download GEO data;
- run RNA-seq processing;
- run Snakemake;
- call real Coze;
- make external network calls;
- write real artifacts;
- write a database;
- create a queue, worker, or scheduler;
- implement a real execution runner;
- store secrets, tokens, passwords, or API keys.

The phase only adds mock API rejection coverage and documentation.

## Verification

Phase 1.4f adds:

```bash
python -m pytest tests/test_phase_1_4f_api_rejection_matrix.py -q -p no:cacheprovider
```

The broader safe regression set remains:

```bash
python -m pytest tests/test_phase_1_4e_api_mock_dry_run_validator.py -q -p no:cacheprovider
python -m pytest tests/test_phase_1_4d_dry_run_validator.py -q -p no:cacheprovider
python -m pytest tests/test_phase_1_4_execution_boundary_docs.py tests/test_phase_1_4b_dry_run_request_contract_docs.py tests/test_phase_1_4c_dry_run_validation_matrix_docs.py -q -p no:cacheprovider
python -m unittest tests.test_api_mock tests.test_api_http_server -v
```
