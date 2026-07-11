# Phase 1.6c Artifact Persistence Boundary Design

Phase 1.6c is artifact persistence boundary design docs/tests only for
`geo-rnaseq-mining`. It follows the Phase 1.6a runtime implementation
readiness audit and the Phase 1.6b sandbox boundary design.

This phase is not implementation. It designs future artifact persistence
boundaries only. It does not create artifact directories, write artifact files,
implement an artifact writer, implement an artifact registry, write a database,
implement sandbox code, connect an API handler, implement runtime execution,
run a pipeline, run Snakemake, download GEO data, call Coze, perform external
network access, or create worker/scheduler/queue infrastructure.

## Artifact Persistence Readiness Conclusion

The current project is **not ready for artifact persistence implementation**.

Reasons:

- artifact naming policy remains design only
- artifact retention policy remains design only
- artifact overwrite policy remains design only
- artifact audit metadata remains design only
- sandbox implementation is still not approved
- database persistence is still not approved
- runtime execution is still not approved
- artifact writer is still not approved

Phase 1.6c only designs the artifact persistence boundary. It does not approve
artifact writer implementation, and it is not allowed to move directly from
Phase 1.6c into real runtime implementation.

## Design-Only Boundary

Phase 1.6c does not implement or approve:

- artifact writer
- artifact persistence
- artifact directory creation
- artifact file creation
- artifact registry
- database persistence
- sandbox implementation
- runtime execution
- runtime parser
- runtime validator
- manifest parser
- manifest validator
- execution planner
- plan generator
- approval system
- API handler integration
- worker / queue / scheduler
- pipeline executor
- Snakemake wrapper
- GEO downloader
- Coze real client
- network boundary implementation

This phase is documentation and documentation tests only. No artifact
directory is created, no artifact file is written, no database rows are
written, no sandbox directory is created, and no runtime work is started.

## Artifact Persistence Principles

Future artifact persistence must follow these principles:

- fail-closed by default
- report-only until future runtime approval
- no artifact writes by default
- write_artifacts must remain false
- accepted dry-run does not permit artifact creation
- accepted approval record does not permit artifact creation
- artifacts may only exist inside an approved sandbox root in a future phase
- no writing outside approved sandbox root
- no artifact overwrite by default
- no user-controlled artifact paths
- no absolute local paths accepted
- no path traversal accepted
- no symlink traversal
- no hidden database persistence
- no hidden network upload
- no automatic escalation from approval to execution

Passing a request, manifest, dry-run preview, approval record, sandbox preview,
or documentation test must not imply permission to create artifact directories
or write artifact files.

## Future Artifact Identity And Naming Rules

Future artifact identity and naming must be safe, narrow, and independent of
raw user-controlled paths.

Future requirements:

- artifact format allowlist is future policy only
- artifact_id required before any future persisted artifact
- artifact_id must be safe identifier only
- artifact type must be from a narrow allowlist
- artifact filename must be derived from trusted policy, not raw user input
- artifact extension must match allowed output_format
- output_format allowed only json / markdown / html
- zip remains not allowed
- no path separators
- no drive letters
- no colon
- no dot-dot
- no whitespace-only names
- no shell fragments
- no URL-like values
- no absolute local paths

Suggested future rejection reasons:

- ARTIFACT_ID_REQUIRED
- UNSAFE_ARTIFACT_ID
- UNSUPPORTED_ARTIFACT_TYPE
- UNSAFE_ARTIFACT_FILENAME
- UNSUPPORTED_OUTPUT_FORMAT
- ZIP_OUTPUT_NOT_ALLOWED
- PATH_SEPARATOR_NOT_ALLOWED
- DRIVE_LETTER_NOT_ALLOWED
- COLON_NOT_ALLOWED
- PATH_TRAVERSAL_NOT_ALLOWED
- ABSOLUTE_LOCAL_PATH_NOT_ALLOWED
- SHELL_FRAGMENT_NOT_ALLOWED
- URL_VALUE_NOT_ALLOWED

These are design-only rejection reasons. Phase 1.6c does not implement a
parser, validator, artifact writer, registry, database writer, or API handler.

## Future Artifact Storage Policy

Future artifact storage policy must derive storage from the approved sandbox
boundary, not from user input.

Future storage policy:

- artifact storage root must be derived from approved sandbox root
- artifact storage root must not come from request body
- artifact storage root must not come from manifest
- artifact storage root must not come from Coze/user prompt
- artifact storage root must not be repository root
- artifact storage root must not be source code directory
- artifact storage root must not be home directory
- artifact storage root must be outside source code tree
- artifact final path must be resolved and normalized before use
- artifact final path must remain inside approved sandbox root

This phase does not configure a storage root, create a directory, check the
filesystem, inspect files, inspect symlinks, or write artifacts.

## Future Overwrite / Retention / Cleanup Policy

Future artifact persistence cannot begin until lifecycle rules are defined.

Future requirements:

- overwrite disabled by default
- artifact overwrite requires explicit future policy
- retention policy required before implementation
- cleanup policy required before implementation
- rollback policy required before implementation
- partial artifact cleanup required before implementation
- cancellation cleanup required before implementation
- failed execution cleanup required before implementation
- orphan artifact handling required before implementation
- no artifact deletion implementation in this phase

Suggested future rejection reasons:

- ARTIFACT_OVERWRITE_NOT_ALLOWED
- RETENTION_POLICY_REQUIRED
- CLEANUP_POLICY_REQUIRED
- ROLLBACK_POLICY_REQUIRED
- PARTIAL_ARTIFACT_CLEANUP_POLICY_REQUIRED
- CANCELLATION_CLEANUP_POLICY_REQUIRED
- FAILED_EXECUTION_CLEANUP_POLICY_REQUIRED

These policies must be reviewed before artifact persistence, cleanup, rollback,
or deletion behavior is implemented.

## Future Artifact Audit Metadata

Future persisted artifacts must carry operator-visible audit metadata before
artifact persistence can be implemented.

Future artifact audit metadata fields:

- artifact_id
- request_id
- manifest_id
- preview_id
- approval_record_id
- sandbox_id
- artifact_type
- output_format
- created_at_placeholder
- created_by_runtime_phase
- report_only
- checksum_placeholder
- provenance_placeholder
- cleanup_policy_id
- retention_policy_id

Audit metadata is documentation-only in this phase:

- no database persistence in this phase
- no database write in this phase
- no external audit service in this phase
- no checksum calculation in this phase
- no checksum computation in this phase
- no file inspection in this phase

## Future Artifact Privacy / Leakage Boundary

Future artifacts must be checked against leakage risks before any persistence
implementation exists.

Future requirements:

- no secrets or credentials in artifact metadata
- no local path leakage
- artifacts must not contain secrets
- artifacts must not contain tokens
- artifacts must not contain passwords
- artifacts must not contain api_key
- artifacts must not contain real credentials
- artifacts must not include raw local absolute paths
- artifacts must not expose system user secrets
- artifacts must not upload to network
- artifacts must not be sent to real Coze
- artifact redaction policy required before implementation

Suggested future rejection reasons:

- SECRET_IN_ARTIFACT_NOT_ALLOWED
- TOKEN_IN_ARTIFACT_NOT_ALLOWED
- PASSWORD_IN_ARTIFACT_NOT_ALLOWED
- API_KEY_IN_ARTIFACT_NOT_ALLOWED
- REAL_CREDENTIALS_IN_ARTIFACT_NOT_ALLOWED
- LOCAL_PATH_LEAK_NOT_ALLOWED
- NETWORK_UPLOAD_NOT_ALLOWED
- REAL_COZE_UPLOAD_NOT_ALLOWED
- ARTIFACT_REDACTION_POLICY_REQUIRED

These requirements are design-only. Phase 1.6c does not inspect files,
calculate checksums, redact artifacts, upload artifacts, call Coze, or persist
artifact metadata.

## Artifact Persistence Preview Schema Design

This example is a future artifact persistence preview schema design only. It is
not implementation, not an API response, not a filesystem operation, not a
database row, not an approval record, and not permission to write artifacts.

```json
{
  "artifact_preview_id": "artifact_preview_placeholder_001",
  "mode": "dry_run",
  "status": "preview_only",
  "request_id": "dryrun_001",
  "manifest_id": "manifest_placeholder_001",
  "preview_id": "preview_placeholder_001",
  "approval_record_id": "approval_placeholder_001",
  "sandbox_id": "sandbox_placeholder_001",
  "artifact_id": "artifact_placeholder_001",
  "artifact_type": "report_placeholder",
  "output_format": "json",
  "artifact_filename": "placeholder_report.json",
  "storage_root_source": "approved_sandbox_root_required",
  "final_path": "placeholder_not_a_real_path",
  "path_normalized": false,
  "directories_created": false,
  "files_written": false,
  "artifacts_created": false,
  "database_written": false,
  "network_performed": false,
  "write_artifacts": false,
  "approved_for_implementation": false,
  "rejection_reasons": [
    "ARTIFACT_PERSISTENCE_NOT_APPROVED",
    "ARTIFACT_WRITE_NOT_ALLOWED"
  ]
}
```

The example remains safe because it is preview-only, uses placeholders, keeps
write_artifacts false, keeps directories_created false, keeps files_written
false, keeps artifacts_created false, keeps database_written false, keeps
network_performed false, and keeps approved_for_implementation false.
All write and execution flags are false in the preview schema.

## Explicit No-Go Decision

- Artifact writer is not approved.
- Artifact persistence is not approved.
- Artifact directory creation is not approved.
- Artifact file creation is not approved.
- Artifact registry is not approved.
- Database persistence is not approved.
- Sandbox implementation is not approved.
- Runtime execution is not approved.
- Runtime API handler integration is not approved.
- Worker / queue / scheduler is not approved.
- Real execution runner is not approved.
- Network upload is not approved.
- Real Coze upload is not approved.

These no-go decisions preserve the Phase 1.6c design-only boundary. They also
preserve the Phase 1.5, Phase 1.6a, and Phase 1.6b decisions that dry-run
previews, approval records, readiness audits, and sandbox previews do not
automatically escalate to execution or persistence.

## Recommended Next Phase Options

The next phase should remain design-only or documentation-test-only. Recommended
options are:

- Phase 1.6d network boundary design docs/tests only
- Phase 1.6d threat model docs/tests only
- Phase 1.6d artifact validation rules docs/tests only
- Phase 1.6d database persistence boundary design docs/tests only

Do not directly enter real execution implementation.

## Final Phase 1.6c Decision

Phase 1.6c is artifact persistence boundary design docs/tests only. The current
conclusion is not ready for artifact persistence implementation. The project
must not implement artifact writer, artifact registry, artifact persistence,
artifact directory creation, artifact file creation, database persistence,
sandbox implementation, network upload, runtime execution, API integration,
workers, queues, schedulers, GEO downloaders, Snakemake wrappers, or real Coze
clients from this phase.
