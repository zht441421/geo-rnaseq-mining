# Phase 1.5c Input Manifest Schema Design

Phase 1.5c is manifest schema docs/tests only and not implementation. It
extends the Phase 1.5b runtime request schema design by drafting a future input
manifest schema for `geo-rnaseq-mining`.

This phase only documents a future manifest shape. It does not implement or
generate a manifest parser, manifest validator, JSON schema file, Pydantic
model, API handler integration, runtime execution runner, worker, queue,
scheduler, pipeline executor, Snakemake wrapper, GEO downloader, Coze real
client, artifact writer, or database persistence.

Phase 1.5c preserves the dry-run design boundary:

- no manifest parser
- no manifest validator
- no JSON schema file
- no API handler integration
- no real execution runner
- no runtime execution runner
- no pipeline execution
- no Snakemake execution
- no real GEO download
- no automatic GEO download
- no real Coze call
- no external network
- no artifacts/database
- no artifact writing
- no database writing
- no worker / scheduler / queue

## A. Required Top-Level Fields

A future input manifest schema should require these top-level fields before any
parser, validator, JSON schema file, Pydantic model, API endpoint, or execution
planner is designed:

| Field | Design intent |
| --- | --- |
| `manifest_id` | Safe manifest identifier for future audit correlation. |
| `manifest_version` | Design-version label for the manifest shape. |
| `dataset` | Dataset identity and metadata placeholder. |
| `samples` | Metadata-only sample descriptions. |
| `analysis` | Documentation-only analysis plan. |
| `inputs` | Placeholder references only, not paths or commands. |
| `outputs` | Report-only output intent and sandbox placeholder. |
| `provenance` | Documentation-only request provenance. |
| `safety` | Fail-closed future permission flags. |
| `audit` | Operator-visible report-only audit behavior. |

These field names are design vocabulary only. Phase 1.5c does not add runtime
parsing, runtime validation, API routing, filesystem checks, file existence
checks, sandbox creation, artifact writing, or execution planning.

## B. Dataset Section

The future `dataset` section should identify the dataset without fetching data:

| Field | Design intent |
| --- | --- |
| `dataset_accession` | Accession-like value such as `GSE123456`; not a URL, path, or command. |
| `dataset_source` | Default placeholder such as `geo_placeholder_not_downloaded`. |

Dataset design constraints:

- `dataset_accession` only allows an accession-like value, for example
  `GSE123456`.
- `dataset_source` defaults to placeholder / not downloaded.
- no URL download by default.
- no automatic GEO download.
- no external network access.
- dataset metadata may be described but not fetched in this phase.

## C. Samples Section

The future `samples` section should be a metadata-only placeholder. Suggested
fields for each sample are:

| Field | Design intent |
| --- | --- |
| `sample_id` | Safe sample identifier. |
| `condition` | Metadata-only condition label. |
| `replicate` | Metadata-only replicate number. |
| `source_name` | Metadata-only source description. |
| `library_strategy` | Metadata-only strategy label such as `RNA-Seq`. |

Sample design constraints:

- metadata-only placeholder.
- no FASTQ / BAM / count matrix real paths.
- no requirement for FASTQ, BAM, or count matrix paths.
- no absolute local paths.
- no path traversal.
- no shell fragments.
- no unvalidated URLs.
- no file existence checks.
- no filesystem checks.
- no data download.

## D. Analysis Section

The future `analysis` section should describe the requested analysis plan
without running tools:

| Field | Design intent |
| --- | --- |
| `analysis_type` | Placeholder value such as `rnaseq_placeholder`. |
| `analysis_goal` | Human-readable design-only analysis goal. |
| `contrast` | Metadata-only comparison label. |
| `normalization_plan` | Documentation-only normalization plan. |
| `differential_expression_plan` | Documentation-only differential expression plan. |

Analysis design constraints:

- current phase only describes a plan.
- no RNA-seq execution.
- no DESeq2 / edgeR / Salmon / STAR / featureCounts execution.
- no Snakemake execution.
- no pipeline executor.
- no real execution runner.

## E. Inputs Section

The future `inputs` section should contain only placeholder references. It must
not become an execution transport, downloader, shell adapter, credential
container, or filesystem probe.

Allowed design content:

- placeholder references only.
- metadata-only references such as `placeholder_metadata_only`.

Forbidden design content:

- command
- shell
- subprocess
- snakemake command
- absolute local paths
- external URLs
- unvalidated URLs
- secrets
- token
- password
- api_key
- shell fragments
- path traversal

Phase 1.5c does not use these fields to read files, validate paths, download
data, invoke subprocesses, call network clients, or start execution.

## F. Outputs Section

The future `outputs` section should describe report-only output intent:

| Field | Design intent |
| --- | --- |
| `output_format` | One of `json`, `markdown`, or `html`. |
| `sandbox_id` | Placeholder sandbox identifier only. |
| `write_artifacts` | Must remain `false` in this design phase. |
| `report_only` | Must remain `true` in this design phase. |

Output design constraints:

- output_format json / markdown / html.
- zip not allowed.
- `sandbox_id` is only a placeholder.
- write_artifacts false.
- report_only true.
- no real artifacts created.
- no sandbox creation.
- no artifact writer.
- no database persistence.

## G. Provenance Section

The future `provenance` section should be documentation-only:

| Field | Design intent |
| --- | --- |
| `requested_by` | Placeholder requester label, not a credential. |
| `request_id` | Safe request identifier for future audit correlation. |
| `created_at_placeholder` | Placeholder timestamp. |
| `source_documentation` | Documentation reference for the design source. |
| `dry_run_only` | Must remain `true` in this design phase. |

Provenance design constraints:

- provenance is documentation-only in this phase.
- no system user secrets are read.
- no real credentials are used.
- no database is written.
- no persistence boundary is implemented.

## H. Safety Section

The future `safety` section must fail closed. Required design defaults are:

- allow_network false.
- allow_pipeline_execution false.
- allow_snakemake false.
- allow_real_coze_call false.
- allow_artifact_write false.
- allow_database_write false.
- allow_background_execution false.

Missing safety fields must not imply permission. These flags are design
requirements for a later phase and do not approve runtime work.

## I. Audit Section

The future `audit` section must remain operator-visible and report-only:

- report_only true.
- include_rejection_reasons true.
- operator_visible true.
- approval_required_for_future_runtime true.

Audit information is a design record only in this phase. It does not create an
approval record, queue work, schedule work, start a worker, persist a database
row, or write artifacts.

## J. Safe Manifest Example

This safe manifest example is a design example only. It is not a fixture for
runtime execution and must not be treated as operator approval.

```json
{
  "manifest_id": "manifest_placeholder_001",
  "manifest_version": "0.1-design",
  "dataset": {
    "dataset_accession": "GSE123456",
    "dataset_source": "geo_placeholder_not_downloaded"
  },
  "samples": [
    {
      "sample_id": "sample_placeholder_001",
      "condition": "control",
      "replicate": 1,
      "source_name": "placeholder",
      "library_strategy": "RNA-Seq"
    }
  ],
  "analysis": {
    "analysis_type": "rnaseq_placeholder",
    "analysis_goal": "design-only differential expression plan",
    "contrast": "treated_vs_control",
    "normalization_plan": "documentation-only",
    "differential_expression_plan": "documentation-only"
  },
  "inputs": {
    "input_references": [
      "placeholder_metadata_only"
    ]
  },
  "outputs": {
    "output_format": "json",
    "sandbox_id": "sandbox_placeholder_001",
    "write_artifacts": false,
    "report_only": true
  },
  "provenance": {
    "requested_by": "operator_placeholder",
    "request_id": "dryrun_001",
    "created_at_placeholder": "2026-01-01T00:00:00Z",
    "source_documentation": "Phase 1.5c design only",
    "dry_run_only": true
  },
  "safety": {
    "allow_network": false,
    "allow_pipeline_execution": false,
    "allow_snakemake": false,
    "allow_real_coze_call": false,
    "allow_artifact_write": false,
    "allow_database_write": false,
    "allow_background_execution": false
  },
  "audit": {
    "report_only": true,
    "include_rejection_reasons": true,
    "operator_visible": true,
    "approval_required_for_future_runtime": true
  }
}
```

The example remains safe because it is metadata-only, uses placeholders, keeps
all execution permissions false, keeps artifact and database writes disabled,
and keeps audit behavior report-only.

## K. Explicit Non-Goals

Phase 1.5c does not implement or generate any of the following:

- manifest parser
- manifest validator
- JSON schema file
- Pydantic model
- API endpoint
- API handler integration
- filesystem checks
- file existence checks
- GEO download
- RNA-seq pipeline
- Snakemake wrapper
- Snakemake execution
- execution planner
- sandbox creation
- artifact writing
- artifact writer
- database persistence
- queue / worker / scheduler
- real runtime execution
- real execution runner
- worker / queue / scheduler
- GEO downloader
- Coze real client

It also does not run pipeline tasks, download datasets, call real Coze
services, create artifacts, write a database, or start background execution.

## L. Next Phase Options

The next phase must remain design-only or documentation-test-only unless a
separate reviewed boundary explicitly chooses otherwise. Safe options are:

- Phase 1.5d dry-run execution plan preview design only
- Phase 1.5d manifest test fixtures docs only
- Phase 1.5d manifest validation rules docs/tests only

Do not directly enter real execution implementation. Do not skip from this
manifest design to a real runner, worker, queue, scheduler, pipeline executor,
Snakemake wrapper, GEO downloader, Coze real client, artifact writer, database
persistence, or external network integration.
