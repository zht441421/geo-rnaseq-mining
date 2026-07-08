# Phase 1.5f Operator Approval Record Design

Phase 1.5f is operator approval record design only and not implementation. It
extends the Phase 1.5a through Phase 1.5e design baseline by drafting what a
future operator approval record should contain while remaining report-only,
fail-closed, and unable to escalate automatically into real execution.

This phase only documents a future approval record shape. It does not implement
or generate an approval system, approval API, approval database, approval
persistence, approval UI, operator authentication, authorization layer, runtime
validator, manifest validator, execution planner, execution runner, worker,
queue, scheduler, pipeline executor, Snakemake wrapper, GEO downloader, Coze
real client, artifact writer, or database persistence.

It is not implementation.

Phase 1.5f preserves the dry-run design boundary:

- no approval system
- no approval API
- no approval database
- no approval UI
- no authentication
- no authorization
- no API handler integration
- no real execution runner
- no pipeline execution
- no Snakemake execution
- no real GEO download
- no real Coze call
- no artifacts/database
- no worker / scheduler / queue

## A. Approval Scope

The approval record is documentation-only in this phase. It records review
intent for a future design boundary and must not trigger runtime work.

Scope constraints:

- approval record is documentation-only in this phase.
- approval record does not trigger execution.
- approval record does not override dry-run safety flags.
- approval record does not grant network access.
- approval record does not grant pipeline execution.
- approval record does not grant artifact/database write.
- approval record does not start worker/scheduler/queue.
- approval record must remain report-only until a future explicit runtime
  phase.

These constraints mean an approval record cannot become a runtime command,
queue message, job scheduler request, network permission, artifact writer
permission, or database write permission.

## B. Required Approval Record Fields

A future operator approval record should contain these fields before any
approval system, approval API, approval database, approval UI, authentication,
authorization, API endpoint, or runtime integration is designed:

| Field | Design intent |
| --- | --- |
| `approval_record_id` | Safe approval record identifier. |
| `request_id` | Safe runtime request identifier being reviewed. |
| `manifest_id` | Safe manifest identifier being reviewed. |
| `preview_id` | Safe preview identifier being reviewed. |
| `operator_id` | Placeholder operator identifier, not a credential. |
| `operator_role` | Placeholder role label for review context. |
| `decision` | Non-executing review decision. |
| `decision_reason` | Human-readable reason for the decision. |
| `reviewed_at_placeholder` | Placeholder review timestamp. |
| `reviewed_preview_version` | Preview design version reviewed. |
| `reviewed_manifest_version` | Manifest design version reviewed. |
| `reviewed_rejection_reasons` | Rejection reasons visible during review. |
| `approved_scope` | Future review scope only, not runtime permissions. |
| `denied_scope` | Explicitly denied runtime actions and permissions. |
| `safety_overrides` | Must remain empty in this phase. |
| `audit` | Operator-visible report-only audit metadata. |
| `expiration` | Placeholder expiration design. |
| `revocation` | Placeholder revocation design. |

These fields are design vocabulary only. Phase 1.5f does not store, validate,
persist, authenticate, authorize, route, or execute approval records.

## C. Decision Values

Future decision values must be non-executing:

- decision may be approved_for_future_runtime_review.
- decision may be rejected.
- decision may be needs_revision.
- decision must not mean execute_now.
- decision must not mean run_pipeline.
- decision must not mean allow_network.
- decision must not mean allow_artifact_write.
- decision must not mean allow_database_write.
- not execute_now.
- not run_pipeline.

The decision value must not be interpreted as permission to run a pipeline,
download data, call Coze, write artifacts, write a database, enqueue work, or
start a worker.

## D. Approved Scope Rules

The future `approved_scope` may describe only future review scope. It must not
directly authorize execution.

Allowed design-only scope fields:

- reviewed_request_id
- reviewed_manifest_id
- reviewed_preview_id
- approved_for_design_continuation
- approved_for_future_runtime_review

Forbidden approved_scope content:

- execute_now
- run_pipeline
- download_geo
- call_real_coze
- allow_network
- allow_snakemake
- allow_artifact_write
- allow_database_write
- start_worker
- enqueue_job
- schedule_job

Approval scope is a review boundary, not an execution boundary.

## E. Safety Override Rules

Safety override rules must fail closed:

- safety_overrides must be empty in this phase.
- operator approval cannot override fail-closed safety flags.
- operator approval cannot set allow_network true.
- operator approval cannot set allow_pipeline_execution true.
- operator approval cannot set allow_snakemake true.
- operator approval cannot set allow_real_coze_call true.
- operator approval cannot set allow_artifact_write true.
- operator approval cannot set allow_database_write true.
- operator approval cannot set allow_background_execution true.

Future rejection reasons:

- SAFETY_OVERRIDES_NOT_ALLOWED
- APPROVAL_CANNOT_ENABLE_NETWORK
- APPROVAL_CANNOT_ENABLE_PIPELINE_EXECUTION
- APPROVAL_CANNOT_ENABLE_SNAKEMAKE
- APPROVAL_CANNOT_ENABLE_REAL_COZE_CALL
- APPROVAL_CANNOT_ENABLE_ARTIFACT_WRITE
- APPROVAL_CANNOT_ENABLE_DATABASE_WRITE
- APPROVAL_CANNOT_ENABLE_BACKGROUND_EXECUTION

Operator approval must never be a shortcut around manifest validation, runtime
validation, safety flags, dry-run mode, or future approval rechecks.

## F. Audit Requirements

Future approval records should preserve operator-visible report-only audit
behavior:

- approval record must be operator-visible.
- approval record must link request_id / manifest_id / preview_id.
- approval record must include reviewed versions.
- approval record must include decision reason.
- approval record must include denied scope.
- approval record must include revocation placeholder.
- approval record must include expiration placeholder.
- no database persistence in this phase.
- no external audit service in this phase.

The audit section is documentation-only. It does not write an approval
database, call an external audit service, persist state, or create artifacts.

## G. Revocation And Expiration Design

Future runtime design must treat approval validity as conditional:

- approval may expire before future runtime.
- approval may be revoked before future runtime.
- revoked approval cannot be used.
- expired approval cannot be used.
- approval validity must be rechecked in a future runtime phase.
- current phase does not implement checking.

This phase does not implement expiration checking, revocation checking,
revocation storage, approval persistence, or approval lookup.

## H. Automatic Escalation Prevention

Approval records must not automatically escalate to runtime work:

- approval record must not start execution.
- approval record must not enqueue job.
- approval record must not schedule job.
- approval record must not create worker.
- approval record must not call API handler.
- approval record must not create artifacts.
- approval record must not write database.
- approval record must not call network.
- approval record must not download GEO.
- approval record must not run Snakemake.
- approval record must not run RNA-seq pipeline.
- approval record must not call real Coze.
- no automatic escalation to execution.
- no enqueue job.
- no schedule job.
- no worker.
- no GEO download.
- no Snakemake execution.
- no RNA-seq pipeline.
- no real Coze call.

An approval record is not a job, not a queue item, not a scheduler request, not
a runner input, and not an API handler instruction.

## I. Safe Approval Record Example

This safe approval record example is design-only. It is not an approval system
record, API response, database row, authentication artifact, authorization
decision, or runtime execution trigger.

```json
{
  "approval_record_id": "approval_placeholder_001",
  "request_id": "dryrun_001",
  "manifest_id": "manifest_placeholder_001",
  "preview_id": "preview_placeholder_001",
  "operator_id": "operator_placeholder",
  "operator_role": "reviewer",
  "decision": "approved_for_future_runtime_review",
  "decision_reason": "Design review only; does not authorize execution.",
  "reviewed_at_placeholder": "2026-01-01T00:00:00Z",
  "reviewed_preview_version": "0.1-design",
  "reviewed_manifest_version": "0.1-design",
  "reviewed_rejection_reasons": [],
  "approved_scope": {
    "reviewed_request_id": "dryrun_001",
    "reviewed_manifest_id": "manifest_placeholder_001",
    "reviewed_preview_id": "preview_placeholder_001",
    "approved_for_design_continuation": true,
    "approved_for_future_runtime_review": true
  },
  "denied_scope": [
    "execute_now",
    "run_pipeline",
    "download_geo",
    "call_real_coze",
    "allow_network",
    "allow_snakemake",
    "allow_artifact_write",
    "allow_database_write",
    "start_worker",
    "enqueue_job",
    "schedule_job"
  ],
  "safety_overrides": {},
  "audit": {
    "operator_visible": true,
    "report_only": true,
    "database_persisted": false,
    "external_audit_service_called": false
  },
  "expiration": {
    "expires_at_placeholder": "future_runtime_requires_recheck"
  },
  "revocation": {
    "revoked": false,
    "revocation_checked_by_future_runtime": true
  }
}
```

The example is safe because it denies execution permissions, keeps
safety_overrides empty, records report_only audit behavior, and requires future
runtime recheck for expiration and revocation.

## J. Forbidden Approval Record Content

Future approval records must not contain:

- secret
- token
- password
- api_key
- real credentials
- absolute local path
- command
- shell
- subprocess
- snakemake command
- real Coze URL
- external URL
- database connection string
- execute_now
- run_pipeline
- force_run
- skip_validation
- disable_safety_checks
- secret / token / password / api_key not allowed.
- command / shell / subprocess not allowed.
- skip_validation not allowed.
- disable_safety_checks not allowed.

Forbidden content must produce deterministic rejection in a future design before
any runtime approval system is implemented.

## K. Future Accepted Approval Record Conditions

Future accepted approval records are accepted only for future runtime review.
An accepted approval record does not mean real execution.

Future design acceptance conditions:

- required fields present.
- identifiers are safe.
- decision is one of allowed non-executing values.
- safety_overrides empty.
- approved_scope does not include execution/network/write permissions.
- denied_scope explicitly lists execution/network/write permissions.
- audit is report-only and operator-visible.
- expiration/revocation placeholders present.
- no forbidden fields present.

Required caveats:

- accepted approval record does not mean real execution.
- accepted approval record does not approve network access.
- accepted approval record does not approve pipeline execution.
- accepted approval record does not approve artifact/database write.
- accepted approval record does not bypass future validation.
- accepted approval record does not start worker, queue, or scheduler work.

## L. Safe Approval Outcome Examples

These examples are design-only outcomes. They are not outputs from an approval
system, approval API, approval database, API handler, execution planner, or
execution runner.

Accepted approval record outcome:

```json
{
  "accepted": true,
  "status": "accepted_for_future_runtime_review_only",
  "execution": "not_started",
  "network_performed": false,
  "artifacts_created": false,
  "database_written": false,
  "worker_started": false,
  "safety_overrides_applied": false
}
```

Rejected approval record outcome:

```json
{
  "accepted": false,
  "status": "rejected",
  "rejection_reasons": [
    "APPROVAL_CANNOT_ENABLE_NETWORK",
    "SAFETY_OVERRIDES_NOT_ALLOWED"
  ],
  "execution": "not_started",
  "network_performed": false,
  "artifacts_created": false,
  "database_written": false,
  "worker_started": false,
  "safety_overrides_applied": false
}
```

Both examples keep execution not_started, network_performed false,
artifacts_created false, database_written false, worker_started false, and
safety_overrides_applied false.

## M. Explicit Non-Goals

Phase 1.5f does not implement or generate any of the following:

- approval system
- approval API
- approval database
- approval UI
- authentication
- authorization
- runtime validator
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
- plan generator
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
server, create a worker, enqueue a job, schedule a job, or start background
execution.

## N. Next Phase Options

The next phase must remain design-only or documentation-test-only unless a
separate reviewed boundary explicitly chooses otherwise. Safe options are:

- Phase 1.5g dry-run preview test fixtures docs only
- Phase 1.5g approval record validation rules docs/tests only
- Phase 1.5g Phase 1.5 completion baseline / operator handoff

Do not directly enter real execution implementation. Do not skip from this
approval record design to an approval system, approval API, approval database,
real runner, worker, queue, scheduler, pipeline executor, Snakemake wrapper,
GEO downloader, Coze real client, artifact writer, database persistence, or
external network integration.
