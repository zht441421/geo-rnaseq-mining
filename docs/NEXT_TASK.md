# Next Task

## Task Identity

- Future next stage: Scientific Pilot Candidate Dataset Review and Execution
  Go/No-Go Preparation
- Status: not started
- Authorization required: separate explicit instruction
- Scope: review/planning-only unless separately authorized

Future next stage: Scientific Pilot Candidate Dataset Review and Execution Go/No-Go Preparation.

## Purpose

The future stage may prepare a candidate dataset review package and execution
Go/No-Go decision record for a later Scientific Pilot. It may identify and
review candidate datasets only under a separate network-access authorization.

This file does not perform dataset review, select a dataset, name candidate
accessions, download data, or authorize execution. It records only the future
scope and authorization boundary after Phase 2.1 Scientific Pilot Readiness
Planning.

## Required Boundaries

The future task must remain review/planning-only unless separately authorized.
It must not:

- download GEO/SRA data
- run a pipeline or Snakemake
- execute the Scientific Pilot
- implement runtime behavior
- create a queue, worker, database, scheduler, or runner
- create artifacts or sandboxes
- access credentials or secrets
- call Coze
- modify API behavior, schemas, or state-machine behavior

It must not download GEO/SRA data.

Candidate dataset lookup requires a separate network-access authorization.
Dataset download requires a separate execution/data-access authorization.
Scientific Pilot execution requires a later explicit human Go/No-Go
authorization.

## Current Prerequisites

The Platform Design Baseline through Phase 1.9 is complete. The Platform
Design Baseline Completion / Go-No-Go Audit is complete. Phase 1.10 Project
State Synchronization is complete and synchronized.

Phase 2.1 Scientific Pilot Readiness Planning defines the required pilot
question template, scope boundary, dataset-selection criteria, manual review
gates, evidence package, success/failure criteria, stop conditions, run-log
requirements, result-package requirements, interpretation boundary, and
execution authorization boundary.

Runtime implementation readiness remains `NO`.

## Conditions To Preserve

- Keep candidate dataset review separate from dataset download.
- Keep Scientific Pilot execution separate from readiness planning.
- Preserve separation between scientific feasibility and runtime
  implementation.
- Require separate human Go/No-Go before Scientific Pilot execution.
- Require separate authorization before any external data or network access.
- Do not treat planning documentation as runtime enforcement.

## Historical Phase 1.10 Handoff Continuity

This section preserves completed Phase 1.10 handoff language for continuity
tests. It is historical and does not define the future next task after Phase
2.1.

- Next stage: Scientific Pilot Readiness Planning
- Scope: planning-only
- Historical boundary: must not download data or run a pipeline.
- Historical boundary: Scientific Pilot execution requires a later separate
  human Go/No-Go.
- Historical boundary: Scientific Pilot execution requires a later separate human Go/No-Go.
- Historical blocked items: external network services, pipeline or Snakemake
  execution, queue, worker, database, scheduler, or runner, artifacts or
  sandboxes, credentials or secrets.
- Historical blocked item: pipeline or Snakemake execution.

## First Reading Set For The Future Stage

- `docs/PROJECT_SPEC.md`
- `docs/DECISIONS.md`
- `docs/CURRENT_STATE.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`
- `PROJECT_SUMMARY_FOR_USER.md`
- `docs/phase-2-1-scientific-pilot-readiness-planning.md`
- `docs/phase-1-10-project-state-synchronization.md`
- `docs/phase-1-9-task-lifecycle-state-machine-boundary-design.md`
- `docs/phase-1-8-secrets-management-redaction-boundary.md`
- `docs/phase-1-7-cross-boundary-security-threat-model.md`
