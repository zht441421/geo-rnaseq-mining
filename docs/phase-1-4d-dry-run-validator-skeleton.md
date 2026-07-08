# Phase 1.4d Dry-Run Validator Skeleton

This phase introduces a minimal pure-function validator skeleton for future
dry-run execution requests. The implementation lives in
`api/dry_run_validator.py` and is covered by
`tests/test_phase_1_4d_dry_run_validator.py`.

The validator only inspects request intent. It does not implement an endpoint,
start a server, download GEO data, run RNA-seq processing, run Snakemake, call
real Coze, make external network requests, write real artifacts, write a
database, spawn subprocesses, or create a queue, worker, or scheduler.

## Function Contract

The public function is:

```python
validate_dry_run_request(request: Mapping[str, Any]) -> dict[str, Any]
```

The returned structure is:

```json
{
  "accepted": true,
  "mode": "dry_run",
  "rejection_reasons": [],
  "warnings": []
}
```

`accepted` is `false` when the request includes real-execution intent or an
unsafe field. `mode` remains `dry_run`; the validator never upgrades a request
into real execution.

## Accepted Baseline

The accepted baseline is planning-only:

```json
{
  "mode": "dry_run",
  "dataset_accession": "GSE123456",
  "analysis_type": "rnaseq_placeholder",
  "output_format": "json",
  "allow_network": false,
  "allow_pipeline_execution": false,
  "allow_snakemake": false,
  "allow_real_coze_call": false,
  "operator_approved": false
}
```

Missing execution permission flags default to safe false behavior. This means a
missing `allow_network`, `allow_pipeline_execution`, `allow_snakemake`,
`allow_real_coze_call`, or `operator_approved` field must not create permission
to execute.

## Rejected Conditions

The validator rejects the Phase 1.4c matrix conditions with stable reason
codes:

- `REAL_EXECUTION_NOT_ALLOWED`
- `NETWORK_ACCESS_NOT_ALLOWED`
- `PIPELINE_EXECUTION_NOT_ALLOWED`
- `SNAKEMAKE_NOT_ALLOWED`
- `REAL_COZE_CALL_NOT_ALLOWED`
- `OPERATOR_APPROVAL_NOT_ACTIVE_IN_THIS_PHASE`
- `UNSUPPORTED_OUTPUT_FORMAT`
- `UNSAFE_DATASET_ACCESSION`
- `COMMAND_FIELD_NOT_ALLOWED`
- `SECRET_FIELD_NOT_ALLOWED`
- `ARTIFACT_WRITE_NOT_ALLOWED`
- `DATABASE_WRITE_NOT_ALLOWED`
- `BACKGROUND_EXECUTION_NOT_ALLOWED`

The skeleton deliberately does not include production approval, sandbox
creation, manifest loading, artifact persistence, database persistence, network
access, or workflow dispatch. Those controls must be designed in a later phase
before any real execution path can exist.

## Current Decision

Phase 1.4d is a local validation skeleton only. It converts the Phase 1.4c
documentation matrix into a pure in-memory validation function and tests, while
preserving the dry-run default and no-side-effect execution boundary.
