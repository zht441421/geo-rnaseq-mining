# Phase 1.5b Runtime Request Schema Design

Phase 1.5b is schema design only and not implementation. It drafts a future
runtime request schema for `geo-rnaseq-mining` after the Phase 1.5a runtime
execution design audit and the Phase 1.4 dry-run baseline.

This phase does not create a runtime parser, runtime validator, API handler
integration, execution runner, worker, queue, scheduler, pipeline executor,
Snakemake wrapper, GEO downloader, Coze real client, artifact writer, or
database persistence.

Phase 1.5b preserves the dry-run safety boundary:

- no runtime parser
- no runtime validator
- no API handler integration
- no real execution runner
- no Snakemake execution
- no real GEO download
- no real Coze call
- no external network
- no artifacts/database
- no worker / scheduler / queue

## A. Required Top-Level Fields

A future runtime request schema should require these top-level fields before
any parser or validator is designed:

| Field | Design intent |
| --- | --- |
| `mode` | Execution mode. The only safe default is `dry_run`. |
| `request_id` | Safe request identifier for audit correlation. |
| `dataset_accession` | Accession-like placeholder, not a URL or path. |
| `analysis_type` | Placeholder analysis label, not a command. |
| `output_format` | One of the dry-run formats: `json`, `markdown`, or `html`. |
| `execution_intent` | Object containing future execution intent flags. |
| `operator_approval` | Object containing future approval status and record references. |
| `input_manifest` | Object describing a future validated input manifest reference. |
| `sandbox` | Object describing a future output sandbox reference. |
| `audit` | Object describing report-only audit behavior. |
| `safety_flags` | Object containing fail-closed safety permissions. |

These names are design vocabulary only. Phase 1.5b does not add a schema file,
parser, runtime validator, API endpoint, or execution planner.

## B. Required Safety Defaults

A future schema must default to safe, report-only behavior. Missing or omitted
permission fields must not imply permission.

- mode default still dry_run.
- real_execution_requested false: `execution_intent.real_execution_requested`
  must default to `false`.
- allow_network false: `safety_flags.allow_network` must default to `false`.
- allow_pipeline_execution false: `safety_flags.allow_pipeline_execution` must
  default to `false`.
- allow_snakemake false: `safety_flags.allow_snakemake` must default to
  `false`.
- allow_real_coze_call false: `safety_flags.allow_real_coze_call` must default
  to `false`.
- operator approval approved false: `operator_approval.approved` must default
  to `false`.
- sandbox.write_artifacts false: `sandbox.write_artifacts` must default to
  `false`.
- report_only true: `audit.report_only` must default to `true`.

These defaults are design requirements for a future phase. They do not approve
or enable real execution in this phase.

## C. Allowed Placeholder Values

Current Phase 1.5b examples may use only placeholders that cannot trigger work:

- `dataset_accession` may be an accession-like placeholder such as
  `GSE123456`.
- `analysis_type` may be `rnaseq_placeholder`.
- `output_format` remains json / markdown / html.
- zip not allowed.
- `request_id` must be a safe identifier with path / shell fragment forbidden.

These values are documentation examples only. They do not validate, download,
stage, execute, persist, or submit anything.

## D. Forbidden Schema Content

The future runtime request schema must reject or refuse to define fields that
can smuggle execution, credentials, persistence, or unsafe paths. These items
are forbidden design content:

- command / shell / subprocess not allowed.
- snakemake command not allowed.
- real Coze URL not allowed.
- secret / token / password / api_key not allowed.
- absolute local paths not allowed.
- artifact output outside sandbox not allowed.
- database connection string not allowed.
- worker / scheduler instruction not allowed.
- background execution request not allowed.
- unvalidated URL not allowed.
- shell fragment not allowed.
- path traversal not allowed.

The schema must stay declarative and fail closed. It must not become a command
transport, shell adapter, network client, persistence instruction, or worker
control plane.

## E. Safe Dry-Run-Only Request Example

This example is a schema design example only. It is not a fixture for real
runtime execution and must not be treated as operator approval.

```json
{
  "mode": "dry_run",
  "request_id": "dryrun_001",
  "dataset_accession": "GSE123456",
  "analysis_type": "rnaseq_placeholder",
  "output_format": "json",
  "execution_intent": {
    "real_execution_requested": false
  },
  "operator_approval": {
    "approved": false,
    "approved_by": null,
    "approval_record": null
  },
  "input_manifest": {
    "manifest_id": "manifest_placeholder_001",
    "validated": false
  },
  "sandbox": {
    "sandbox_id": "sandbox_placeholder_001",
    "write_artifacts": false
  },
  "audit": {
    "report_only": true,
    "include_rejection_reasons": true
  },
  "safety_flags": {
    "allow_network": false,
    "allow_pipeline_execution": false,
    "allow_snakemake": false,
    "allow_real_coze_call": false
  }
}
```

The example remains dry-run-only because `mode` is `dry_run`, operator approval
is not granted, artifacts are not writable, network and pipeline permissions
are false, and audit behavior is report-only.

## F. Explicit Non-Goals

Phase 1.5b does not implement or generate any of the following:

- JSON schema file generation
- Pydantic model
- runtime parser
- runtime validator
- API endpoint
- API handler integration
- execution planner
- sandbox creation
- artifact writing
- database persistence
- queue / worker / scheduler
- real runtime execution

It also does not implement worker / queue / scheduler, GEO downloader,
Snakemake wrapper, Coze real client, artifact writer, database writer, or a
production execution runner.

## G. Next Phase Options

The next phase must remain design-only or documentation-test-only unless a
separate reviewed boundary explicitly chooses otherwise. Safe options are:

- Phase 1.5c manifest schema docs/tests only
- Phase 1.5c dry-run execution plan preview design only
- Phase 1.5c runtime request schema test fixture docs only

Do not directly enter real execution implementation. Do not skip from this
schema design to a real runner, worker, queue, scheduler, pipeline executor,
Snakemake wrapper, GEO downloader, Coze real client, artifact writer, database
persistence, or external network integration.
