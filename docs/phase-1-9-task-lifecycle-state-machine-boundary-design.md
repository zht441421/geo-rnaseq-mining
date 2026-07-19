# Phase 1.9 Task Lifecycle and State Machine Boundary Design

Phase 1.9 is a Platform Design Baseline convergence phase for
`geo-rnaseq-mining`. It is docs/tests-only, design-only, report-only, and not
runtime lifecycle implementation.

Phase 1.9 is not runtime lifecycle implementation.

## Scope and Readiness Conclusion

This document defines future lifecycle terminology, state classification,
allowed and blocked transitions, approval gates, cancellation, failure, retry,
idempotency, replay, concurrency, audit, and readiness boundaries. It does not
create executable lifecycle behavior.

The project is **not ready for runtime lifecycle implementation**.

The governing statements are:

- fail-closed by default
- Design controls are not enforced runtime controls.
- A documented transition does not create an executable transition.
- A status field is not a capability token.
- preview, validation, approval, planning, queueing, and execution remain
  separate concepts
- documentation acceptance does not approve implementation

## Existing Mock State Machine Compatibility Boundary

The existing Phase 1 in-memory mock and frontend prototype uses this vocabulary:

- queued
- validating
- ready
- running
- summarizing
- completed
- failed
- cancelled

Its existing mock happy path is:

```text
queued -> validating -> ready -> running -> summarizing -> completed
```

That vocabulary belongs only to the in-memory mock and frontend prototype. It
does not execute real jobs, is not the future platform lifecycle contract,
must not be promoted into runtime behavior by documentation alone, and must not
be modified during Phase 1.9. The existing mock state machine remains unchanged.

| Existing mock term | Future lifecycle distinction | Compatibility gap |
| --- | --- | --- |
| validating | validated | `validating` describes activity; `validated` records a passed gate |
| ready | approved / planned / queued | `ready` merges separate authority, planning, and dispatch concepts |
| completed | succeeded / artifact_validation_failed / cleanup failure | execution completion alone does not prove trustworthy success |
| cancelled | cancelling / cancelled after cleanup | the mock has no visible stop-and-cleanup interval |
| summarizing | artifact validation or report generation | summarizing does not prove artifact safety or authorize success |

This compatibility table is descriptive only. It does not define a migration,
adapter, mapping function, enum, or runtime integration.

## Lifecycle Assets and Actors

Lifecycle-relevant assets include:

- request
- canonical request identity
- manifest
- validation result
- preview
- execution plan
- approval record
- policy version
- task identity
- state version
- worker lease placeholder
- execution result
- artifact validation result
- cleanup result
- transition audit event

Lifecycle actors and actor placeholders include:

- user
- operator
- API placeholder
- validator placeholder
- planner placeholder
- queue placeholder
- worker placeholder
- artifact validator placeholder
- cleanup controller placeholder
- audit boundary

Placeholder actors are not implemented services. They have no runtime authority,
process, thread, network connection, queue, credential, or persistence behavior.

## State Vocabulary and Classification

The future platform lifecycle vocabulary includes:

- received
- rejected
- validated
- awaiting_review
- approved
- denied
- planned
- queued
- running
- cancelling
- cancelled
- failed
- succeeded
- artifact_validation_failed
- expired

### Pre-execution states

- received
- validated
- awaiting_review
- approved
- planned
- queued

### Active states

- running
- cancelling

### Terminal states

- rejected
- denied
- cancelled
- failed
- succeeded
- artifact_validation_failed
- expired

Terminal state classification does not authorize automatic deletion, retry,
restart, artifact persistence, audit deletion, or cleanup-data deletion.

## Allowed-Transition Matrix

The minimum happy path is:

```text
received -> validated -> awaiting_review -> approved -> planned -> queued -> running -> succeeded
```

| Previous state | Allowed next state | Required design gate |
| --- | --- | --- |
| received | rejected | request or validation rejection recorded |
| received | validated | validation completed successfully |
| validated | awaiting_review | operator review is required |
| validated | expired | validation or governing policy expired |
| awaiting_review | approved | explicit scoped operator approval |
| awaiting_review | denied | explicit operator denial |
| awaiting_review | expired | review or policy validity expired |
| approved | planned | approval relationship and freshness verified |
| approved | expired | approval or policy expired |
| planned | queued | plan and approval remain consistent and valid |
| planned | failed | planning/dispatch prerequisite failed |
| planned | expired | approval, plan, or policy expired |
| queued | running | future dispatch and lease gates satisfied |
| queued | cancelling | cancellation requires stop/lease/cleanup handling |
| queued | failed | queue or dispatch failure recorded |
| running | cancelling | cancellation request accepted for processing |
| running | failed | runtime or related failure recorded |
| running | artifact_validation_failed | required artifact validation failed |
| running | succeeded | every succeeded gate is satisfied |
| cancelling | cancelled | stop, lease release, and required cleanup confirmed |
| cancelling | failed | cancellation or cleanup failed |

Pre-execution cancellation may transition `received`, `validated`,
`awaiting_review`, `approved`, or `planned` to `cancelled` only when no worker
lease, execution resource, active operation, or cleanup obligation exists.
Otherwise cancellation must pass through cancelling.

This matrix documents allowed vocabulary. It does not execute a transition.

## Succeeded Gate

The transition `running -> succeeded` requires all of the following:

- execution result is complete
- required artifact validation passed
- no pending cancellation exists
- required cleanup completed
- request, manifest, validation result, preview, plan, approval, and policy
  relationships remain consistent
- approval remains valid and fresh
- no stale-state or concurrency conflict exists

Execution completion alone must not equal succeeded. Report generation,
summarization, or a successful worker exit alone must not bypass artifact,
approval, relationship, freshness, cancellation, cleanup, or concurrency gates.

## Blocked-Transition Matrix

| Blocked transition | Reason |
| --- | --- |
| received -> approved | validation and review were skipped |
| received -> queued | validation, review, approval, and planning were skipped |
| received -> running | all control gates were skipped |
| validated -> running | review, approval, planning, and queueing were skipped |
| awaiting_review -> planned | operator approval was skipped |
| approved -> running | planning and queue boundary were skipped |
| planned -> running | queue/dispatch boundary was skipped |
| denied -> approved | a terminal denial cannot be mutated into approval |
| rejected -> validated | a terminal rejection cannot resume in place |
| expired -> approved | expired authority cannot be revived in place |
| succeeded -> running | terminal tasks cannot restart in place |
| failed -> running | retry requires a new task identity |
| cancelled -> running | cancelled tasks cannot restart in place |
| artifact_validation_failed -> succeeded | a failed artifact cannot be relabeled as success |

The design also prohibits:

- skipping validation
- skipping operator approval
- bypassing gates by directly modifying a status field
- restarting a terminal task in place
- automatically converting failed to queued
- automatically converting cancelled to running
- treating execution completion as artifact success
- marking cancelled before stop and required cleanup complete
- continuing queued or running work after approval expiry
- reusing approval after request, manifest, plan, policy, or security-boundary
  change

Blocked transitions fail closed and use stable, non-sensitive reasons.

## Validation, Preview, Approval, Planning, and Execution Gates

- preview is report-only and does not authorize execution
- validation success does not authorize execution
- approval does not replace validation
- approval does not authorize secret disclosure
- approval does not authorize network access
- approval does not authorize database access
- approval does not authorize artifact writing
- approved means an approval decision exists
- approved does not mean planned, queued, or running
- execution requires relationship and freshness verification
- approval must bind to the same request, manifest, preview, plan, and policy
  version
- state values are not authorization capabilities

Documentation-only rejection vocabulary:

- VALIDATION_REQUIRED
- OPERATOR_APPROVAL_REQUIRED
- APPROVAL_DENIED
- APPROVAL_EXPIRED
- APPROVAL_STALE
- APPROVAL_REPLAY_NOT_ALLOWED
- RELATIONSHIP_MISMATCH
- PLAN_REQUIRED
- QUEUE_NOT_APPROVED
- EXECUTION_NOT_APPROVED
- STATE_TRANSITION_NOT_ALLOWED
- TERMINAL_STATE_RESTART_NOT_ALLOWED

These terms are not enums, constants, schemas, runtime models, or API fields.

## Cancellation and Cleanup Semantics

The lifecycle distinguishes:

- cancellation_requested
- cancelling
- cancelled

`cancellation_requested` is an event, not necessarily a state.
`cancelling` means stop and cleanup are incomplete. `cancelled` requires execution stopped,
worker lease released where applicable, and required cleanup confirmed.

Cancelling means stop and cleanup are incomplete.

Cleanup failure transitions to `failed` and uses
`failure_category = cleanup_failed`. Cancellation must not silently produce
cancelled, erase request/approval/transition/failure audit history, or
automatically delete artifacts. Deletion policy belongs to a separate
persistence and cleanup boundary.

Cancellation must not automatically delete artifacts.

Phase 1.9 sends no cancellation signal and implements no cleanup operation.

## Failure Taxonomy

The documentation-level failure categories are:

- validation_failed
- approval_denied
- planning_failed
- queue_failed
- runtime_failed
- artifact_validation_failed
- cancellation_failed
- cleanup_failed
- policy_expired
- relationship_mismatch
- concurrency_conflict

Recommended state relationships:

- validation_failed generally maps to rejected
- approval_denied maps to denied
- artifact_validation_failed maps to the explicit terminal state
  artifact_validation_failed
- planning, queue, runtime, cancellation, cleanup, relationship, and concurrency
  failures generally map to failed where applicable

This taxonomy does not implement failure detection, handling, storage, or
recovery.

## Retry Boundary

- retry is an explicit, human-visible new decision
- retry creates a new task_id
- the new task begins at received
- retry_of_task_id may be recorded
- terminal states are not resumed in place
- automatic infinite retry is prohibited
- expired approval cannot be reused
- changed request, manifest, plan, policy, or security boundary requires new
  validation and approval
- unchanged inputs still do not automatically authorize reuse of an old
  approval

Phase 1.9 implements no retry engine, retry logic, or retry storage.

## Terminal-State Rules

- terminal states cannot transition back to running
- terminal history cannot be overwritten
- a new attempt requires a new task identity
- terminal status does not imply cleanup data may be deleted
- terminal status does not imply audit data may be deleted
- artifact_validation_failed must not be relabeled succeeded without a new
  reviewed task
- cancelled must not be used when cleanup failed
- failed must retain a failure category
- expired cannot be converted directly to approved

A terminal state may lead an operator to create a distinct new task, but never
to mutate or restart the terminal task in place.

## Idempotency and Duplicate Requests

- an idempotency key binds to canonical request identity
- same key plus same canonical request may return the same task reference
- same key plus different payload must be rejected
- idempotency does not mean retry
- idempotency does not permit approval reuse
- idempotency does not resume a terminal task
- no idempotency store is implemented in this phase

An idempotency key is not a capability token or authorization decision.

## Replay and Stale Approval

- approval, preview, validation result, and plan bind to task/request/version
  identity
- stale approval must be rejected
- consumed or invalid approval must not be replayed
- terminal-task request replay must not restart the original task
- approval freshness must be checked before execution
- Phase 1.9 implements no replay store

Replay prevention remains conceptual until an independently approved authority
and storage boundary exists.

## Concurrency and TOCTOU

Future transition proposals should document:

- expected_previous_state
- expected_version
- next_state

Documentation-only rejection vocabulary:

- STATE_VERSION_CONFLICT
- STALE_STATE_UPDATE
- CONCURRENT_TRANSITION_NOT_ALLOWED

Concurrent updates must fail closed. Stale state must not overwrite a newer
state. Validation or approval checked earlier must be revalidated for
relationship and freshness before execution to address stale-state and TOCTOU
risk.

Stale state must not overwrite a newer state.

No lock, database transaction, compare-and-swap, state version store, or
concurrency mechanism is implemented.

## Single Authoritative State Source

The future platform requires one authoritative state source. Phase 1.9 does not
choose or implement a database or other state store.

None of these may independently become authoritative:

- audit event
- API response
- queue message
- worker local state
- client-side state
- preview output
- approval record

Every projection must be reconciled with the future authoritative source; this
requirement is documentation only.

## Audit Requirements

Every future transition should include:

- transition_id
- task_id
- actor_type
- actor_id_placeholder
- occurred_at_placeholder
- previous_state
- next_state
- reason_code
- request_id
- manifest_id
- preview_id
- plan_id
- approval_record_id
- policy_version
- expected_state_version
- resulting_state_version
- report_only

Audit visibility is required for:

- validation rejection
- approval denial
- approval expiry
- approval revocation
- cancellation request
- entry into cancelling
- cleanup outcome
- failure category
- retry decision
- replay rejection
- concurrency conflict
- terminal state

Audit design does not equal audit persistence implementation. Historical
transitions must not be overwritten, deleted, or silently rewritten. Phase 1.9
does not implement append-only storage or any audit storage.

Historical transitions must not be overwritten, deleted, or silently rewritten.

## Report-Only Lifecycle Assessment Schema

This documentation-only example is not a JSON Schema, Pydantic model, runtime
object, database row, API response, or queue message.

This example is not a runtime object.

```json
{
  "lifecycle_assessment_id": "lifecycle_placeholder_001",
  "mode": "design_only",
  "status": "report_only",
  "states_documented": true,
  "allowed_transitions_documented": true,
  "blocked_transitions_documented": true,
  "unresolved_dependencies": [
    "DATABASE_STATE_STORE_NOT_APPROVED",
    "QUEUE_NOT_APPROVED",
    "RUNTIME_EXECUTION_NOT_APPROVED"
  ],
  "database_written": false,
  "queue_created": false,
  "worker_started": false,
  "scheduler_started": false,
  "cancellation_signal_sent": false,
  "retry_performed": false,
  "audit_persisted": false,
  "runtime_executed": false,
  "approved_for_implementation": false,
  "readiness_conclusion": "not_ready_for_runtime_lifecycle_implementation"
}
```

All side-effect and implementation flags remain false. The example creates no
task, event, state record, queue message, database row, cancellation request,
retry, audit record, worker, scheduler, or execution.

## Remaining Dependencies

Unresolved dependencies include:

- database state store
- queue
- worker
- scheduler
- execution runner
- cancellation mechanism
- cleanup implementation
- retry policy implementation
- idempotency store
- replay protection store
- concurrency control
- audit persistence
- runtime authorization
- artifact validation enforcement
- sandbox enforcement
- network policy enforcement

No dependency is approved or implemented by this document.

## Explicit No-Go Decision

Phase 1.9 does not approve or implement:

- database state store
- queue
- worker
- scheduler
- execution runner
- cancellation signal
- retry engine
- idempotency store
- replay store
- concurrency lock
- audit persistence
- background service
- runtime API handler
- real state-machine integration
- artifact writer
- artifact registry
- sandbox
- network client
- secret system
- authentication or authorization
- real task execution
- pipeline execution
- Snakemake execution
- GEO/SRA download
- Coze integration

The existing mock state machine remains unchanged. Phase 1.9 modifies no API,
runtime, queue, persistence, worker, scheduler, runner, network, credential,
sandbox, or execution behavior.

## Scientific Pilot Relationship

The lifecycle vocabulary supports a later Scientific Pilot through:

- consistent pilot request identity
- explicit human review gate
- distinction among validation rejection, operator denial, runtime failure,
  artifact validation failure, and cancellation
- auditable retry and failure vocabulary
- separation of Scientific Pilot execution from product runtime
- consistent run-log and result-handoff terminology

Phase 1.9 does not start the Scientific Pilot. Phase 1.9 does not convert a
pilot into a queue or worker task. Scientific Pilot execution requires a
separate plan and explicit authorization.

Phase 1.9 does not convert a pilot into a queue or worker task.
Scientific Pilot execution requires a separate plan and explicit authorization.

## Final Readiness Conclusion

Lifecycle terminology is documented and transition requirements are
documented. Security and approval gates remain conceptual. No lifecycle
enforcement exists, no runtime state store exists, and no queue or execution
service exists.

The project remains not ready for runtime lifecycle implementation. The next
recommended stage is Platform Design Baseline Completion / Go-No-Go Audit.
Scientific Pilot Readiness Planning may follow only after that audit and under
separate authorization.

The next recommended stage is Platform Design Baseline Completion / Go-No-Go Audit.
Scientific Pilot Readiness Planning may follow only after that audit.
