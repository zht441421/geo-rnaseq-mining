# Phase 1.4c Dry-Run Validation / Rejection Matrix

This document defines the documentation-level validation and rejection matrix
for future dry-run execution requests in `geo-rnaseq-mining`. It is not a
runtime validator and it does not implement an endpoint, worker, scheduler,
queue, database, artifact writer, Snakemake runner, Coze caller, or pipeline
adapter.

Phase 1.4c does not start a server, access the network, download GEO data, run
RNA-seq processing, run Snakemake, call Coze, write real artifacts, or write a
database. A later implementation phase must separately design operator
approval, sandboxing, audit boundaries, and runtime validation before any real
execution path exists.

Runtime validation is not implemented. This phase does not start a server,
access the network, download GEO data, run RNA-seq processing, run Snakemake,
call Coze, write real artifacts, or write a database.

## Accepted Dry-Run Request Conditions

An accepted request is planning-only. It may describe the proposed action and
return an audit/report-only preview, but it must not execute anything.

| Field or intent | Accepted condition | Notes |
|---|---|---|
| `mode` | `dry_run` | Default and only accepted mode in this phase. |
| `allow_network` | `false` | No external network call and no GEO download. |
| `allow_pipeline_execution` | `false` | No RNA-seq pipeline starts. |
| `allow_snakemake` | `false` | No Snakemake execution starts. |
| `allow_real_coze_call` | `false` | No real Coze service is called. |
| `operator_approved` | `false` | Operator approval is not active in this phase. |
| `output_format` | `json`, `markdown`, or `html` | `zip` remains unsupported. |
| `dataset_accession` | accession-like placeholder such as `GSE123456` | This must not trigger download. |
| `analysis_type` | placeholder value such as `rnaseq_placeholder` | This is not a command. |

## Rejected Request Conditions

The following conditions must be rejected or kept in dry-run failure state by
any future validator. In Phase 1.4c they are only documentation-level contract
requirements.

| Rejected condition | Rejection reason |
|---|---|
| `mode = run` | `REAL_EXECUTION_NOT_ALLOWED` |
| `mode = execute` | `REAL_EXECUTION_NOT_ALLOWED` |
| `allow_network = true` | `NETWORK_ACCESS_NOT_ALLOWED` |
| `allow_pipeline_execution = true` | `PIPELINE_EXECUTION_NOT_ALLOWED` |
| `allow_snakemake = true` | `SNAKEMAKE_NOT_ALLOWED` |
| `allow_real_coze_call = true` | `REAL_COZE_CALL_NOT_ALLOWED` |
| `operator_approved = true` with real execution intent | `OPERATOR_APPROVAL_NOT_ACTIVE_IN_THIS_PHASE` |
| `dataset_accession` contains a URL | `UNSAFE_DATASET_ACCESSION` |
| `dataset_accession` contains a shell fragment | `UNSAFE_DATASET_ACCESSION` |
| `output_format = zip` | `UNSUPPORTED_OUTPUT_FORMAT` |
| request contains `command` | `COMMAND_FIELD_NOT_ALLOWED` |
| request contains `shell` | `COMMAND_FIELD_NOT_ALLOWED` |
| request contains `subprocess` | `COMMAND_FIELD_NOT_ALLOWED` |
| request contains a Snakemake command | `SNAKEMAKE_NOT_ALLOWED` |
| request contains `secret`, `token`, `password`, or `api_key` | `SECRET_FIELD_NOT_ALLOWED` |
| request asks to write real artifacts | `ARTIFACT_WRITE_NOT_ALLOWED` |
| request asks to write database records | `DATABASE_WRITE_NOT_ALLOWED` |
| request asks for a background worker or scheduler | `BACKGROUND_EXECUTION_NOT_ALLOWED` |

## Rejection Reasons

The documented rejection reasons are:

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

These reason codes are a contract target only. They do not imply that a runtime
validator already exists.

## Negative Documentation Examples

These examples are intentionally unsafe and must remain non-executable examples.

```json
{
  "mode": "run",
  "allow_pipeline_execution": true
}
```

Expected reason: `REAL_EXECUTION_NOT_ALLOWED` or
`PIPELINE_EXECUTION_NOT_ALLOWED`.

```json
{
  "mode": "dry_run",
  "allow_network": true,
  "dataset_accession": "https://example.invalid/GSE123456"
}
```

Expected reason: `NETWORK_ACCESS_NOT_ALLOWED` or `UNSAFE_DATASET_ACCESSION`.

```json
{
  "mode": "dry_run",
  "allow_snakemake": true,
  "command": "snakemake --cores 8"
}
```

Expected reason: `SNAKEMAKE_NOT_ALLOWED` or `COMMAND_FIELD_NOT_ALLOWED`.

```json
{
  "mode": "dry_run",
  "token": "REDACTED_EXAMPLE_ONLY"
}
```

Expected reason: `SECRET_FIELD_NOT_ALLOWED`.

## Current Decision

Phase 1.4c defines the accepted and rejected request matrix. Runtime validation
is not implemented in this phase. Any future runtime validator must preserve
the dry-run default, explicit opt-in requirement, rejection reasons, operator
approval boundary, output sandbox boundary, and audit/report-only preview
before real execution is considered.
