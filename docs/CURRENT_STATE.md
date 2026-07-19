# Current Project State

Last updated for Phase 2.1 Scientific Pilot Readiness Planning.

This document records the current governance state for `geo-rnaseq-mining`.
Historical entries in `docs/CHANGELOG.md` describe earlier environment,
mock-API, and design phases; those historical entries are not the active
project state.

## Repository Baseline

- Current branch: `123`
- Current synchronized HEAD: `29d8a1644be4cfb72cfafe0a33814f3e3b447392`
- Current synchronized `origin/123`: `29d8a1644be4cfb72cfafe0a33814f3e3b447392`
- HEAD equals `origin/123`: yes
- Working tree was clean at Phase 2.1 start: yes
- HEAD tag status: no tag at HEAD

## Current Active Task

Phase 2.1 Scientific Pilot Readiness Planning is the current phase.

This phase is docs/tests-only, planning-only, scientific-governance-only,
no-external-data-access, no-scientific-execution, and no-runtime. It defines a
future pilot question template, pilot scope boundary, dataset-selection
criteria, evidence requirements, manual review gates, stop conditions,
run-log requirements, result-package requirements, interpretation rules, and
handoff requirements.

Scientific Pilot Readiness Planning is in progress.

Phase 2.1 does not select a dataset. Phase 2.1 does not start scientific
analysis. Phase 2.1 does not authorize Scientific Pilot execution. Phase 2.1
does not authorize dataset search or download. Phase 2.1 does not authorize
runtime implementation.

## Completed Platform Baseline

- Phase 1.1-1.9 Platform Design Baseline: complete
- Phase 1.9 Task Lifecycle and State Machine Boundary Design: complete
- Platform Design Baseline Completion / Go-No-Go Audit: complete
- Phase 1.10 Project State Synchronization: complete and synchronized

## Audit Conclusion

Scientific Pilot Readiness Planning: `GO WITH CONDITIONS`

Runtime implementation readiness: `NO`

The `GO WITH CONDITIONS` recommendation applies only to entering planning. It
is not authorization for Scientific Pilot execution, external data access,
GEO/SRA download, network access, pipeline execution, Snakemake execution,
runtime implementation, queue/worker/database creation, artifact writing,
sandbox creation, credential access, or Coze access.

## Historical Phase 1.10 Continuity

This section preserves continuity language for the completed Phase 1.10
documentation tests. It is historical and does not define the current active
task.

- Historical Phase 1.10 statement: Phase 1.10 Project State Synchronization is
  the current task.
- Historical Phase 1.10 statement: Phase 1.10 Project State Synchronization is the current task.
- Historical Phase 1.10 synchronized SHA:
  `93bd2016ee920aa29b0d786a70a701fe3e0f5fca`
- Historical Phase 1.10 roadmap statement: Scientific Pilot Readiness Planning:
  not started.
- Historical Phase 1.10 roadmap statement: Scientific Pilot Readiness Planning: not started.

## Current Roadmap State

- Platform Design Baseline: complete
- Platform Audit: complete
- Phase 1.10 Project State Synchronization: complete and synchronized
- Phase 2.1 Scientific Pilot Readiness Planning: in progress
- Scientific Pilot Candidate Dataset Review: not started
- Scientific Pilot execution: not authorized
- Runtime MVP: not started
- Production Readiness: not started

## Runtime Readiness

Runtime readiness remains `NO`.

Design and planning controls remain non-runtime controls. A documented
readiness plan is not an executable capability. Planning approval is not
execution approval.

Unresolved future implementation dependencies include request and manifest
runtime parsers and validators, planner, approval enforcement, authentication
and authorization, authoritative state store, database, queue, worker,
scheduler, execution runner, sandbox enforcement, artifact writer and
registry, artifact validation enforcement, audit persistence, secret provider
and redaction enforcement, network policy enforcement, cancellation and
cleanup protocol, retry, replay, idempotency stores, and concurrency and
stale-state enforcement.

## Next Authorized Theme

The next recommended stage after Phase 2.1 is Scientific Pilot Candidate
Dataset Review and Execution Go/No-Go Preparation.

That future stage requires a separate explicit instruction. It must remain
review/planning-only unless separately authorized. Candidate datasets may be
identified and reviewed only under a separate network-access authorization.
It must not download data, run a pipeline, execute a Scientific Pilot, or
implement runtime behavior.

## Explicit No-Go State

The following remain not authorized:

- Scientific Pilot execution
- Dataset search or dataset download
- GEO/SRA/NCBI/Entrez access
- External HTTP requests or browser automation
- Runtime implementation
- API behavior changes
- State-machine behavior changes
- Schema changes
- Database, queue, worker, scheduler, or runner creation
- Sandbox or artifact creation
- Network client, Coze access, or credential access
- Pipeline or Snakemake execution
- Retry, replay, cancellation, or background-service implementation
- Authentication or authorization implementation
