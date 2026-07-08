# Phase 1.5d Dry-Run Execution Plan Preview Design

Phase 1.5d is dry-run execution plan preview design only and not
implementation. It extends the Phase 1.5a runtime execution design audit, the
Phase 1.5b runtime request schema design, and the Phase 1.5c input manifest
schema design by drafting what a future dry-run execution plan preview should
show to an operator.

This phase only documents a future preview shape. It does not implement or
generate an execution planner, runtime planner, plan generator, runtime request
parser, manifest parser, manifest validator, API handler integration,
execution runner, worker, queue, scheduler, pipeline executor, Snakemake
wrapper, GEO downloader, Coze real client, artifact writer, or database
persistence.

It is not implementation.

Phase 1.5d preserves the dry-run design boundary:

- no execution planner
- no runtime planner
- no plan generator
- no generated real plan object
- no runtime request parser
- no manifest parser
- no manifest validator
- no API handler integration
- no real execution runner
- no execution runner
- no worker / scheduler / queue
- no pipeline execution
- no Snakemake execution
- no real GEO download
- no real Coze call
- no external network
- no artifacts/database
- no artifact writing
- no database writing

## A. Required Top-Level Preview Fields

A future dry-run execution plan preview should require these top-level fields
before any planner, generator, parser, validator, API endpoint, or execution
runner is designed:

| Field | Design intent |
| --- | --- |
| `preview_id` | Safe preview identifier for operator-visible audit correlation. |
| `request_id` | Safe runtime request identifier. |
| `manifest_id` | Safe input manifest identifier. |
| `mode` | Must remain `dry_run`. |
| `status` | Preview status, not runtime status. |
| `plan_summary` | Human-readable design-only summary. |
| `planned_steps` | Descriptive future steps only. |
| `blocked_actions` | Actions refused by the dry-run safety boundary. |
| `safety_assessment` | Fail-closed safety flags and rejection behavior. |
| `operator_review` | Approval requirements for future runtime work. |
| `sandbox_preview` | Placeholder sandbox information only. |
| `audit_report` | Report-only audit preview content. |
| `next_allowed_actions` | Safe design/documentation follow-up options. |

These names are design vocabulary only. Phase 1.5d does not add an execution
planner, runtime planner, plan generator, real plan object, runtime parser,
manifest parser, manifest validator, API route, filesystem check, sandbox
creation, artifact writer, database writer, worker, scheduler, queue, or
execution runner.

## B. Required Preview Defaults

A future preview must default to safe, report-only behavior. Missing fields
must not imply permission to execute.

- mode dry_run: `mode` must be `dry_run`.
- status preview_only / blocked / rejected: `status` may only be
  `preview_only`, `blocked`, or `rejected`.
- status must not be `running`.
- status must not be `completed`.
- no execution_started true.
- no artifact_created true.
- no network_performed true.
- no database_written true.
- no worker_started true.
- audit_report.report_only true.
- operator_review.approval_required true.

These defaults are preview design requirements only. They do not start,
schedule, queue, persist, download, run, or approve anything.

## C. Planned Steps Section

The future `planned_steps` section should describe possible future review
steps without executing them. Suggested placeholder steps are:

- validate_runtime_request
- validate_input_manifest
- assess_safety_flags
- prepare_output_sandbox_placeholder
- generate_operator_visible_report
- wait_for_future_operator_approval

Planned steps are descriptive only:

- planned steps are descriptive only.
- no subprocess.
- no shell command.
- no Snakemake invocation.
- no GEO download.
- no RNA-seq processing.
- no Coze call.
- no file write.
- no database write.
- no background execution.

The preview must not treat planned steps as commands, runnable tasks, workflow
nodes, queue entries, or shell fragments.

## D. Blocked Actions Section

The future `blocked_actions` section must list actions refused by default. At a
minimum, it should include:

- real_geo_download
- real_rnaseq_pipeline
- snakemake_execution
- real_coze_call
- external_network_access
- shell_command_execution
- subprocess_execution
- artifact_write
- database_write
- worker_start
- scheduler_start
- queue_enqueue
- long_running_server

These blocked actions explain what was not attempted. They are not operational
instructions and must not be mapped to runtime code in this phase.

## E. Safety Assessment Section

The future `safety_assessment` section must fail closed:

- allow_network false.
- allow_pipeline_execution false.
- allow_snakemake false.
- allow_real_coze_call false.
- allow_artifact_write false.
- allow_database_write false.
- allow_background_execution false.
- fail_closed true.
- deterministic_rejection_reasons true.

The assessment records why the preview remains dry-run-only. It does not grant
permissions, connect to services, create files, start workers, or persist
state.

## F. Operator Review Section

The future `operator_review` section must make human review explicit:

- approval_required true.
- approved false.
- approval_record null.
- operator_visible true.
- review_required_before_runtime true.
- no automatic escalation to execution.

The preview must not infer approval from a valid request, valid manifest, safe
placeholder, or passing documentation test. Any future runtime approval must be
separately designed and reviewed.

## G. Sandbox Preview Section

The future `sandbox_preview` section may describe a placeholder sandbox only:

- `sandbox_id` is a placeholder.
- sandbox_path not a real path.
- `sandbox_path` must not be a real local machine path.
- write_artifacts false.
- no directories are created.
- directories_created false.
- no files are written.
- files_written false.
- no cleanup is needed because nothing is created.

Phase 1.5d does not create directories, inspect filesystem locations, check
file existence, write files, or prepare a real output sandbox.

## H. Audit Report Section

The future `audit_report` section should remain report-only:

- report_only true.
- include_request_summary true.
- include_manifest_summary true.
- include_blocked_actions true.
- include_rejection_reasons true.
- include_next_allowed_actions true.
- no database persistence.
- database_persisted false.

The audit report is documentation-only in this phase. It does not write a
database row, artifact, log file, approval record, queue message, or worker
state.

## I. Safe Dry-Run Preview Example

This safe dry-run preview example is a design example only. It is not a real
plan object, execution planner output, runtime request response, API fixture,
or operator approval.

```json
{
  "preview_id": "preview_placeholder_001",
  "request_id": "dryrun_001",
  "manifest_id": "manifest_placeholder_001",
  "mode": "dry_run",
  "status": "preview_only",
  "plan_summary": "Design-only preview; no execution is started.",
  "planned_steps": [
    "validate_runtime_request",
    "validate_input_manifest",
    "assess_safety_flags",
    "prepare_output_sandbox_placeholder",
    "generate_operator_visible_report",
    "wait_for_future_operator_approval"
  ],
  "blocked_actions": [
    "real_geo_download",
    "real_rnaseq_pipeline",
    "snakemake_execution",
    "real_coze_call",
    "external_network_access",
    "shell_command_execution",
    "subprocess_execution",
    "artifact_write",
    "database_write",
    "worker_start",
    "scheduler_start",
    "queue_enqueue",
    "long_running_server"
  ],
  "safety_assessment": {
    "allow_network": false,
    "allow_pipeline_execution": false,
    "allow_snakemake": false,
    "allow_real_coze_call": false,
    "allow_artifact_write": false,
    "allow_database_write": false,
    "allow_background_execution": false,
    "fail_closed": true,
    "deterministic_rejection_reasons": true
  },
  "operator_review": {
    "approval_required": true,
    "approved": false,
    "approval_record": null,
    "operator_visible": true,
    "review_required_before_runtime": true,
    "no_automatic_escalation_to_execution": true
  },
  "sandbox_preview": {
    "sandbox_id": "sandbox_placeholder_001",
    "sandbox_path": "placeholder_not_a_real_path",
    "write_artifacts": false,
    "directories_created": false,
    "files_written": false
  },
  "audit_report": {
    "report_only": true,
    "include_request_summary": true,
    "include_manifest_summary": true,
    "include_blocked_actions": true,
    "include_rejection_reasons": true,
    "include_next_allowed_actions": true,
    "database_persisted": false
  },
  "next_allowed_actions": [
    "review_preview_documentation",
    "design_manifest_validation_rules",
    "design_operator_approval_record"
  ]
}
```

The example remains safe because it is preview-only, keeps `mode` at `dry_run`,
keeps all execution permissions false, records blocked actions, requires future
operator review, uses a non-path sandbox placeholder, writes nothing, and
persists nothing.

## J. Explicit Non-Goals

Phase 1.5d does not implement or generate any of the following:

- execution planner
- runtime planner
- plan generator
- runtime parser
- runtime request parser
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
- execution runner
- real execution runner
- sandbox creation
- artifact writing
- artifact writer
- database persistence
- queue / worker / scheduler
- real runtime execution
- worker / queue / scheduler
- GEO downloader
- Coze real client

It also does not run pipeline tasks, run Snakemake, download datasets, call
real Coze services, create artifacts, write a database, start a long-running
server, or start background execution.

## K. Next Phase Options

The next phase must remain design-only or documentation-test-only unless a
separate reviewed boundary explicitly chooses otherwise. Safe options are:

- Phase 1.5e manifest validation rules docs/tests only
- Phase 1.5e operator approval record design only
- Phase 1.5e dry-run preview test fixtures docs only

Do not directly enter real execution implementation. Do not skip from this
dry-run preview design to a real runner, planner, worker, queue, scheduler,
pipeline executor, Snakemake wrapper, GEO downloader, Coze real client,
artifact writer, database persistence, or external network integration.
