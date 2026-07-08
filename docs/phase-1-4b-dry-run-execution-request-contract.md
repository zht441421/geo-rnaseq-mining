# Phase 1.4b Dry-Run Execution Request Contract

This document defines the dry-run execution request contract for future
controlled execution design in `geo-rnaseq-mining`. It is a documentation and
test contract only. It does not execute GEO download, RNA-seq processing,
Snakemake, Coze calls, external network requests, artifact writing, database
persistence, workers, or schedulers.

## Default Mode

The default execution mode is `dry_run`.

Real execution is forbidden by default. A request that lacks explicit opt-in
must remain in dry-run planning and must not cross into production execution.

The dry-run contract may validate shape, describe proposed actions, report
missing approvals, and produce an audit/report-only preview. It must not:

- download GEO or SRA data;
- run an RNA-seq pipeline;
- run Snakemake;
- call real Coze services;
- make external network requests;
- write real analysis artifacts;
- create database records;
- start background workers or schedulers;
- spawn subprocesses or shell commands.

## Request Shape

A future dry-run execution request should use an explicit, reviewable shape:

```json
{
  "mode": "dry_run",
  "dataset_accession": "GSEXXXXXX",
  "analysis_type": "rnaseq_placeholder",
  "output_format": "json",
  "allow_network": false,
  "allow_pipeline_execution": false,
  "allow_snakemake": false,
  "allow_real_coze_call": false,
  "operator_approved": false
}
```

Required fields:

- `mode`: must default to `dry_run`.
- `dataset_accession`: a GEO-like accession string, not a URL, local path, or
  shell fragment.
- `analysis_type`: a placeholder analysis type, not a free-form command.
- `output_format`: a contract value such as `json`.
- `allow_network`: must be `false` in Phase 1.4b.
- `allow_pipeline_execution`: must be `false` in Phase 1.4b.
- `allow_snakemake`: must be `false` in Phase 1.4b.
- `allow_real_coze_call`: must be `false` in Phase 1.4b.
- `operator_approved`: must be `false` until a future operator approval design
  exists.

## Required Future Controls

Before any future request can move beyond dry-run, a separate design must
define:

- explicit opt-in flag;
- operator confirmation;
- validated input manifest;
- output sandbox directory;
- audit/report-only preview;
- no secrets in repo, docs, tests, prompts, or examples;
- no automatic network call;
- no background worker or scheduler by default;
- no Snakemake by default.

These controls are future requirements. They are not implemented by Phase 1.4b.

## Rejected Intent Examples

The contract must reject or keep in dry-run any request that attempts to enable
real execution before the future controls exist.

Rejected intent examples:

```json
{
  "mode": "execute",
  "allow_pipeline_execution": true
}
```

```json
{
  "mode": "dry_run",
  "allow_network": true,
  "dataset_accession": "https://example.invalid/GSE123456"
}
```

```json
{
  "mode": "dry_run",
  "allow_snakemake": true,
  "analysis_type": "snakemake --cores 8"
}
```

```json
{
  "mode": "dry_run",
  "allow_real_coze_call": true
}
```

These examples are documentation-only negative cases. They must not be executed
as commands, network calls, Coze calls, Snakemake runs, or pipeline requests.

## Expected Dry-Run Response Shape

A future dry-run response may describe the proposed plan without executing it:

```json
{
  "mode": "dry_run",
  "accepted": true,
  "execution_started": false,
  "network_called": false,
  "pipeline_started": false,
  "snakemake_started": false,
  "real_coze_called": false,
  "artifact_written": false,
  "database_written": false,
  "operator_approval_required": true,
  "message": "Dry-run only. No real execution has started."
}
```

This response shape is a planning contract. It does not imply that a runtime
endpoint, worker, scheduler, persistent registry, or production runner exists.

## Current Decision

Phase 1.4b only defines the dry-run request and response boundary. The project
must continue to reject real execution by default until a later phase designs
operator approval, sandboxing, audit boundaries, and production-safe execution
controls.
