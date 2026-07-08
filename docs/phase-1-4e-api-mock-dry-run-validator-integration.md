# Phase 1.4e API Mock Dry-Run Validator Integration

Phase 1.4e connects the Phase 1.4d pure dry-run validator to the existing
mock API submit contract. The integration returns a validation report for
dry-run execution request intent only. It does not create a real job, run a
pipeline, or start any production execution path.

## Scope

Implemented files:

- `api/mock_service.py`
- `api/http_server.py`
- `tests/test_phase_1_4e_api_mock_dry_run_validator.py`

Reference files:

- `api/dry_run_validator.py`
- `docs/phase-1-4d-dry-run-validator-skeleton.md`

The mock API calls `validate_dry_run_request(payload)` when a submit payload
contains dry-run execution fields such as `mode`, `dataset_accession`,
`operator_approved`, or `allow_*`.

Normal mock job submit payloads still use the existing `JobSubmitRequest`
schema and the existing in-memory job status response contract.

## Accepted Dry-Run Response

An accepted dry-run request returns a deterministic validation report:

```json
{
  "status": "accepted",
  "mode": "dry_run",
  "validation": {
    "accepted": true,
    "mode": "dry_run",
    "rejection_reasons": [],
    "warnings": []
  },
  "execution": "not_started",
  "mock": true,
  "message": "Dry-run request accepted for validation only; no real execution has started."
}
```

Accepted means validation accepted the request shape. It does not mean real
execution was started, scheduled, approved, queued, or persisted.

No `job_id` is allocated for this validation report.

## Rejected Dry-Run Response

A rejected dry-run request also returns a deterministic validation report:

```json
{
  "status": "rejected",
  "mode": "dry_run",
  "validation": {
    "accepted": false,
    "mode": "dry_run",
    "rejection_reasons": ["REAL_EXECUTION_NOT_ALLOWED"],
    "warnings": []
  },
  "execution": "not_started",
  "mock": true,
  "message": "Dry-run request rejected by validation; no real execution has started."
}
```

Rejected dry-run requests do not create a job and do not start execution.
Rejection reasons are ordered by the Phase 1.4d validator contract, so the same
payload returns the same reason list every time.

Examples of rejected reason codes include:

- `REAL_EXECUTION_NOT_ALLOWED`
- `NETWORK_ACCESS_NOT_ALLOWED`
- `PIPELINE_EXECUTION_NOT_ALLOWED`
- `SNAKEMAKE_NOT_ALLOWED`
- `REAL_COZE_CALL_NOT_ALLOWED`
- `UNSUPPORTED_OUTPUT_FORMAT`
- `UNSAFE_DATASET_ACCESSION`

## Output Format Contract

The output format contract remains unchanged:

- `json` is allowed.
- `markdown` is allowed.
- `html` is allowed.
- `zip` is rejected.

For normal mock job submit payloads, `zip` is still rejected by the existing
schema as `INVALID_OUTPUT_FORMAT`. For dry-run validation payloads, `zip`
returns `UNSUPPORTED_OUTPUT_FORMAT` in `validation.rejection_reasons`.

## HTTP Behavior

`POST /jobs` returns the existing `201` status for normal mock job creation.

For dry-run validation reports, `POST /jobs` returns `200` because no job was
created. The response body is the same validation report returned by
`MockJobService.submit_job(payload)`.

The HTTP server remains a short-lived local mock in tests. Importing
`api.http_server` still does not bind a port.

## Safety Boundary

Phase 1.4e does not:

- download GEO data;
- run RNA-seq processing;
- run Snakemake;
- call real Coze;
- make external network calls;
- write real artifacts;
- write a database;
- create a worker, queue, or scheduler;
- create a real execution runner;
- store secrets, tokens, passwords, or API keys.

The integration only inspects request intent and returns a report.

Any future real execution integration must be designed as a separate controlled
phase with explicit operator approval, sandboxing, persistence boundaries,
network controls, audit behavior, and rollback strategy.

## Verification

Phase 1.4e adds:

```bash
python -m pytest tests/test_phase_1_4e_api_mock_dry_run_validator.py -q -p no:cacheprovider
```

The test covers accepted dry-run validation, rejected real-execution intent,
rejected network, pipeline, workflow, and Coze flags, rejected `zip`, unsafe
dataset accession, deterministic validation results, existing output format
compatibility, existing happy-path job creation, existing negative-path schema
rejection, and a short-lived loopback HTTP validation report.

## Phase 1.4f Follow-Up

Phase 1.4f hardens the API rejection matrix around this integration. The
follow-up adds service-layer and HTTP-layer tests for real-execution modes,
execution permission flags, operator approval, unsafe dataset accessions,
command-like fields, secret-like fields, artifact and database write intent,
background execution intent, and multi-risk deterministic rejection reasons.

Phase 1.4f does not change the dry-run validator or introduce real execution.
Rejected dry-run validation reports still omit `job_id` and keep `execution`
set to `not_started`. Accepted dry-run validation reports also remain
`not_started`, while ordinary mock job submissions keep the existing `201` and
`job_id` contract.
