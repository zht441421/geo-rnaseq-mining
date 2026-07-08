# Phase 1.4a Controlled Execution Boundary

This document defines the controlled execution boundary for the next phase of
`geo-rnaseq-mining`. It is a boundary contract only. It does not enable real
GEO download, real RNA-seq processing, Snakemake execution, real Coze calls, or
production execution.

## Current Phase

The project remains in the mock, contract, and placeholder stage.

Allowed work in this phase:

- contract tests;
- mock API tests;
- documentation tests;
- schema and response examples;
- local dry-run planning;
- audit/report-only mode for design review.

Not allowed by default:

- real GEO download;
- real RNA-seq processing;
- Snakemake execution;
- real Coze call;
- external network call;
- writing real analysis outputs;
- persistent job registry;
- production worker or scheduler.

## Controlled Execution Requirements

Before any future task can cross from mock planning into real execution, the
project must first define and review these controls:

- explicit opt-in flag for any non-mock action;
- dry-run mode that validates intent without downloading, processing, or
  writing real outputs;
- safe input validation for GEO accessions, analysis type, requested output,
  and caller identity;
- output sandbox directory with clear retention and cleanup rules;
- no secrets in repo, docs, tests, prompts, or examples;
- no background execution without a separately reviewed worker design;
- no automatic network calls;
- operator checklist for every manual transition from mock to execution;
- audit/report-only mode that records proposed actions without performing
  them.

These controls must be implemented before any production candidate runner,
queue, worker, scheduler, persistent registry, or result storage is introduced.

## Mock And Dry-Run Boundary

Mock and dry-run behavior may describe what would happen, but it must not do
the work. A dry-run may validate a request, produce a checklist, and report a
planned command or planned output location. It must not:

- fetch GEO or SRA data;
- run Snakemake;
- start an RNA-seq pipeline;
- call real Coze services;
- call external APIs;
- write real analysis artifacts;
- store durable job state;
- spawn subprocesses or shell commands.

Any example artifacts must stay synthetic, such as `mock://` references or
plain text placeholders. They are not files, reports, download URLs, or
biological results.

## Operator Checklist

Before approving any future controlled execution design, an operator must
confirm:

- the request has an explicit opt-in flag;
- dry-run mode exists and has been reviewed first;
- input validation rejects paths, shell fragments, URLs, and unknown fields;
- output is limited to a sandbox directory;
- no secrets, tokens, passwords, or API keys are committed;
- no Coze workflow can execute arbitrary shell commands;
- no automatic network call is made by default;
- no worker, scheduler, or persistent registry is introduced without a separate
  design review;
- rollback and audit/report-only behavior are documented.

## Current Decision

Phase 1.4a keeps the project on the safe side of the boundary. The correct
next step is to continue refining the contract, tests, and operator handoff.
Running real GEO download, real RNA-seq processing, Snakemake, or real Coze
integration remains out of scope.
