# Phase 1.6b Sandbox Boundary Design

Phase 1.6b is sandbox boundary design docs/tests only for
`geo-rnaseq-mining`. It follows the Phase 1.6a runtime implementation
readiness audit, which concluded that the project is not ready for real
runtime implementation and that sandbox readiness is not ready.

This phase is not implementation. It designs future sandbox boundaries only.
It does not create a sandbox directory, write files, write artifacts, write a
database, implement sandbox code, connect an API handler, implement runtime
execution, run a pipeline, run Snakemake, download GEO data, call Coze, perform
external network access, or create worker/scheduler/queue infrastructure.

## Sandbox Readiness Conclusion

The current project is **not ready for sandbox implementation**.

Reasons:

- sandbox path policy remains design only
- path normalization/enforcement remains unimplemented
- artifact write boundary remains unimplemented
- cleanup/rollback/audit policy remains unimplemented
- runtime execution is still not approved
- artifact writing is still not approved
- database/network/worker side effects are still not approved

Phase 1.6b only designs the sandbox boundary. It does not approve sandbox
implementation, and it is not allowed to move directly from Phase 1.6b into
real runtime implementation.

## Design-Only Boundary

Phase 1.6b does not implement or approve:

- sandbox implementation
- sandbox directory creation
- filesystem write
- artifact writer
- artifact persistence
- database persistence
- network boundary implementation
- runtime execution
- runtime parser
- runtime validator
- manifest parser
- manifest validator
- execution planner
- plan generator
- approval system
- approval API
- approval database
- approval UI
- authentication
- authorization
- API handler integration
- worker / queue / scheduler
- pipeline executor
- Snakemake wrapper
- GEO downloader
- Coze real client

This phase is documentation and documentation tests only. No directories are
created, no files are created as analysis outputs, no artifacts are created,
no database rows are written, and no runtime work is started.

## Sandbox Boundary Principles

Future sandbox behavior must follow these principles:

- fail-closed by default
- report-only until future runtime approval
- no implicit filesystem writes
- no absolute local paths accepted from request or manifest
- no path traversal accepted
- no user-controlled output root
- no writing outside approved sandbox root
- no artifact overwrite by default
- no symlink traversal
- no hidden network side effects
- no database persistence side effects
- no worker / scheduler side effects
- no automatic escalation from approval to execution

Passing a request, manifest, dry-run preview, approval record, or documentation
test must not imply permission to create directories or write files.

## Future Sandbox Identifier Rules

A future sandbox_id must be treated as a safe identifier, not as a path.

Future sandbox_id requirements:

- sandbox_id required before any future artifact write
- sandbox_id must be safe identifier only
- allowed characters should be narrow, e.g. lowercase letters, digits, dash,
  underscore
- no path separators
- no drive letters
- no colon
- no dot-dot
- no whitespace-only id
- no shell fragments
- no URL-like values
- no absolute local paths

Suggested future rejection reasons:

- SANDBOX_ID_REQUIRED
- UNSAFE_SANDBOX_ID
- PATH_SEPARATOR_NOT_ALLOWED
- DRIVE_LETTER_NOT_ALLOWED
- COLON_NOT_ALLOWED
- PATH_TRAVERSAL_NOT_ALLOWED
- ABSOLUTE_LOCAL_PATH_NOT_ALLOWED
- SHELL_FRAGMENT_NOT_ALLOWED
- URL_VALUE_NOT_ALLOWED

These are design-only rejection reasons. Phase 1.6b does not implement a
parser, validator, API handler, or sandbox enforcement code.

## Future Sandbox Root Policy

Future sandbox root policy must be based on trusted operator configuration,
not user input.

Future root policy:

- sandbox root must be configured by trusted operator configuration
- sandbox root must not come from request body
- sandbox root must not come from manifest
- sandbox root must not come from Coze/user prompt
- sandbox root must not be inferred from dataset accession
- sandbox root must not be a project source directory
- sandbox root must not be repository root
- sandbox root must not be home directory
- sandbox root must not be system temp without explicit policy
- sandbox root must be outside source code tree
- sandbox root must be resolved and normalized before use

This phase does not configure a root, create a directory, check the
filesystem, inspect symlinks, or write files.

## Future Path Normalization And Enforcement

Future sandbox enforcement must normalize and verify every output path before
any artifact write is attempted.

Future enforcement requirements:

- normalize requested sandbox path
- resolve final output path
- verify final output path stays inside approved sandbox root
- reject path traversal
- reject symlink traversal
- reject absolute local paths supplied by user
- reject drive-letter paths
- reject UNC paths
- reject URL paths
- reject shell fragments
- reject control characters
- reject null bytes
- reject overwrites unless future overwrite policy explicitly allows it

Suggested future rejection reasons:

- OUTPUT_PATH_OUTSIDE_SANDBOX_NOT_ALLOWED
- SYMLINK_TRAVERSAL_NOT_ALLOWED
- UNC_PATH_NOT_ALLOWED
- CONTROL_CHARACTER_NOT_ALLOWED
- NULL_BYTE_NOT_ALLOWED
- ARTIFACT_OVERWRITE_NOT_ALLOWED

This enforcement is not implemented in Phase 1.6b. The current document only
records the required future behavior.

## Future Artifact Write Boundary

Artifact writing remains forbidden by default.

Boundary requirements:

- artifact writing remains false by default
- write_artifacts must remain false until future explicit runtime phase
- accepted dry-run does not permit writes
- accepted approval record does not permit writes
- future artifact writes require runtime opt-in
- future artifact writes require approved sandbox root
- future artifact writes require safe sandbox_id
- future artifact writes require validated manifest
- future artifact writes require dry-run preview
- future artifact writes require operator-visible approval
- future artifact writes require artifact naming policy
- future artifact writes require overwrite policy
- future artifact writes require cleanup policy
- future artifact writes require audit policy

No artifact writer is implemented in this phase. No files are created in this
phase. No directories are created in this phase.

## Cleanup / Rollback / Audit Design

Future sandbox implementation cannot begin until lifecycle behavior is designed.

Future requirements:

- cleanup policy required before sandbox implementation
- rollback policy required before sandbox implementation
- partial write handling required before sandbox implementation
- failed execution cleanup required before sandbox implementation
- cancellation cleanup required before sandbox implementation
- audit trail required before sandbox implementation
- operator-visible sandbox report required before sandbox implementation
- no database persistence in this phase
- no external audit service in this phase

The future sandbox report must be operator-visible and report-only until a
separate runtime implementation phase is manually approved.

## Sandbox Preview Schema Design

This example is a future sandbox preview schema design only. It is not an
implementation, not an API response, not a filesystem operation, not an
approval record, and not permission to write artifacts.

```json
{
  "sandbox_preview_id": "sandbox_preview_placeholder_001",
  "sandbox_id": "sandbox_placeholder_001",
  "mode": "dry_run",
  "status": "preview_only",
  "sandbox_root_source": "trusted_operator_configuration_required",
  "sandbox_root_configured": false,
  "sandbox_path": "placeholder_not_a_real_path",
  "path_normalized": false,
  "directories_created": false,
  "files_written": false,
  "artifacts_created": false,
  "database_written": false,
  "network_performed": false,
  "write_artifacts": false,
  "approved_for_implementation": false,
  "rejection_reasons": [
    "SANDBOX_IMPLEMENTATION_NOT_APPROVED",
    "ARTIFACT_WRITE_NOT_ALLOWED"
  ]
}
```

The example remains safe because it is preview-only, uses placeholders, keeps
write_artifacts false, keeps directories_created false, keeps files_written
false, keeps artifacts_created false, keeps database_written false, keeps
network_performed false, and keeps approved_for_implementation false.

## Explicit No-Go Decision

- Sandbox implementation is not approved.
- Sandbox directory creation is not approved.
- Artifact writer is not approved.
- Artifact persistence is not approved.
- Database persistence is not approved.
- Network boundary implementation is not approved.
- Runtime execution is not approved.
- Runtime API handler integration is not approved.
- Worker / queue / scheduler is not approved.
- Real execution runner is not approved.

These no-go decisions preserve the Phase 1.6b design-only boundary. They also
preserve the Phase 1.5 and Phase 1.6a decisions that approval records, dry-run
previews, and readiness audits do not automatically escalate to execution.

## Recommended Next Phase Options

The next phase should remain design-only or documentation-test-only. Recommended
options are:

- Phase 1.6c artifact persistence boundary design docs/tests only
- Phase 1.6c network boundary design docs/tests only
- Phase 1.6c threat model docs/tests only
- Phase 1.6c sandbox validation rules docs/tests only

Do not directly enter real execution implementation.

## Final Phase 1.6b Decision

Phase 1.6b is sandbox boundary design docs/tests only. The current conclusion
is not ready for sandbox implementation. The project must not implement
sandbox code, create sandbox directories, write files, write artifacts, persist
database state, perform network operations, start workers, or run real runtime
execution from this phase.
