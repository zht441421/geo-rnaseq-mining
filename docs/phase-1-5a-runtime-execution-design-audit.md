# Phase 1.5a Runtime Execution Design Audit

Phase 1.5a is a design audit, not implementation. It asks what boundaries,
interfaces, approvals, sandboxing, manifests, audit reports, and failure
protections would be required before `geo-rnaseq-mining` could ever move from
mock / dry-run validator behavior toward controlled runtime execution.

This phase does not introduce runtime execution. It does not run a pipeline,
run Snakemake, download GEO data, call Coze, write artifacts/database, create a
worker/scheduler/queue, or implement a real execution runner.

Phase 1.5a also does not implement:

- runtime execution runner
- worker
- queue
- scheduler
- pipeline executor
- Snakemake wrapper
- GEO downloader
- Coze real client
- artifact writer
- database persistence

## A. Preconditions Before Any Real Execution

Before any future real execution can be considered, the project must define and
review all of these preconditions:

- explicit opt-in flag
- operator approval
- validated input manifest
- output sandbox directory
- audit/report-only preview
- no automatic network calls
- secrets outside repo
- controlled runner design
- worker / queue / scheduler design review before implementation
- persistence boundary design before implementation
- failure rollback / cleanup policy
- resource limits
- timeout policy
- reproducibility / provenance record
- local-only dry-run preview first

These are design gates. They do not grant permission to run anything in this
phase.

## B. Runtime Execution Boundary Proposal

If runtime execution is ever designed, it must be layered so each decision is
auditable before any controlled runner exists:

1. request validation layer
2. operator approval layer
3. manifest validation layer
4. execution planning layer
5. sandbox preparation layer
6. audit/report-only preview layer
7. only then controlled runner layer

The current phase allows only design writing. It does not implement any layer.
It must not introduce a runner, wrapper, worker, queue, scheduler, downloader,
database writer, artifact writer, shell adapter, or network client.

## C. Forbidden Default Behavior

The default behavior must forbid:

- no real execution runner
- no real GEO download
- no real RNA-seq processing
- no Snakemake execution
- no real Coze call
- no external network
- no shell command execution
- no subprocess execution
- real GEO download
- real RNA-seq processing
- Snakemake execution
- Coze real call
- external network access
- shell command execution
- subprocess execution
- artifact write
- database write
- background worker
- scheduler
- queue
- long-running server
- secrets in repo
- no artifacts/database
- no worker / scheduler / queue

Any future design must fail closed if a request attempts these actions without
explicit future approval boundaries.

## D. Required Failure Protections

A future runtime design must include these protections before implementation:

- deterministic rejection reasons
- no partial execution without approval
- no artifact write unless sandbox approved
- no network unless explicit future network boundary exists
- no secrets from repo
- timeout / cancellation design
- cleanup policy
- audit trail
- operator-visible report
- fail-closed behavior
- failure rollback / cleanup policy
- timeout policy
- provenance record

Failures must leave an operator-visible report that explains what was rejected,
what was not attempted, and which approval or design boundary was missing.

## E. Interface Design Questions

These questions remain open. Phase 1.5a records them for design review and does
not implement answers:

- execution request schema finalization
- manifest format
- allowed dataset accession policy
- whether GEO download is ever allowed
- where sandbox output lives
- how artifacts are named
- how logs are handled
- how provenance is stored
- how operator approval is recorded
- how external network is isolated
- how secrets are provided outside repo
- how pipeline command is represented without shell injection risk
- how dry-run report becomes approval package

These questions must be resolved before real runtime execution, worker design,
queue design, scheduler design, artifact writing, database persistence, or
external network access exists.

## F. Next Phase Options

The next phase must remain design-only unless a separate review explicitly
chooses otherwise. Safe next phase options are:

- Phase 1.5b runtime request schema design only
- Phase 1.5b dry-run execution plan preview only
- Phase 1.5b manifest schema docs/tests only

Do not directly enter real execution implementation. Do not skip from the
Phase 1.4 mock / dry-run baseline to a production runner, GEO downloader,
Snakemake wrapper, Coze real client, artifact writer, database persistence,
worker, queue, or scheduler.

## Current Decision

Phase 1.5a is documentation and documentation tests only. It extends the Phase
1.4 completion baseline by documenting what must be designed before runtime
execution can even be proposed. No real execution is implemented or approved in
this phase.
