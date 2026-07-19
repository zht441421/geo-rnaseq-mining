# Next Task

## Task Identity

- Next stage: Scientific Pilot Readiness Planning
- Status: not started
- Authorization required: separate explicit instruction
- Scope: planning-only

## Purpose

The next stage may define a planning framework for a later Scientific Pilot.
It may identify the pilot question, dataset-selection criteria, manual review
gates, evidence requirements, run-log structure, result handoff, stop
conditions, and execution authorization boundary.

This file does not contain the Scientific Pilot Readiness Plan. It records only
the future scope and authorization boundary after Phase 1.10 Project State
Synchronization.

## Required Boundaries

Scientific Pilot Readiness Planning must remain planning-only.
It must not download data or run a pipeline.

It must not:

- start Scientific Pilot execution
- download GEO/SRA data
- access external network services
- run pipeline or Snakemake execution
- implement runtime behavior
- create a queue, worker, database, scheduler, or runner
- create artifacts or sandboxes
- access credentials or secrets
- call Coze
- modify API behavior, schemas, or state-machine behavior

Scientific Pilot execution requires a later separate human Go/No-Go
authorization. Planning authorization is not execution authorization.

## Current Prerequisites

The Platform Design Baseline through Phase 1.9 is complete and synchronized.
The Platform Design Baseline Completion / Go-No-Go Audit is complete.

Audit recommendation for Scientific Pilot Readiness Planning:
`GO WITH CONDITIONS`.

Runtime implementation readiness remains `NO`.

## Conditions To Preserve

- Keep the next phase planning-only.
- Preserve separation between scientific validation and runtime implementation.
- Maintain governance/status documents as the source of current state.
- Require separate human Go/No-Go before Scientific Pilot execution.
- Require separate authorization before any external data or network access.
- Do not treat design documentation as runtime enforcement.

## First Reading Set For The Next Stage

- `docs/PROJECT_SPEC.md`
- `docs/DECISIONS.md`
- `docs/CURRENT_STATE.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`
- `PROJECT_SUMMARY_FOR_USER.md`
- `docs/phase-1-10-project-state-synchronization.md`
- `docs/phase-1-9-task-lifecycle-state-machine-boundary-design.md`
- `docs/phase-1-8-secrets-management-redaction-boundary.md`
- `docs/phase-1-7-cross-boundary-security-threat-model.md`
