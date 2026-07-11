# Phase 1.6d Artifact Validation Rules

Phase 1.6d is artifact validation rules docs/tests only for
`geo-rnaseq-mining`. It follows the Phase 1.6a readiness audit, Phase 1.6b
sandbox boundary design, and Phase 1.6c artifact persistence boundary design.

This phase is not implementation. It designs the rules that a future artifact
proposal must satisfy before any runtime write, persistence, or execution can
be considered. It does not implement a validator runtime, inspect a filesystem,
resolve a path, create an artifact, write a database, call a network service,
or authorize execution.

## Scope And Readiness Conclusion

The current project is **not ready for artifact validator runtime implementation**.
Phase 1.6d records validation vocabulary, rule ordering,
rejection codes, audit boundaries, and a report-only result schema. It does not
create executable validation behavior.

The governing decisions are:

- fail-closed by default
- report-only until future runtime approval
- validation success does not authorize write
- validation success does not authorize execution
- approval record cannot bypass validation
- validation does not grant persistence permission
- validation does not grant API, worker, queue, or scheduler permission

## Validation Trust Model

A future artifact proposal, request body, manifest, prompt, filename, path,
metadata value, and declared size are untrusted inputs. Trusted policy must be
separate, operator-controlled, reviewed, and unavailable for mutation by the
proposal being validated.

The following must come only from future trusted policy:

- artifact type allowlist
- output-format allowlist
- filename derivation policy
- size limits
- approved sandbox root policy
- overwrite policy
- retention policy
- cleanup policy
- redaction policy

Request bodies, manifests, Coze/user prompts, dataset accessions, and artifact
metadata must not expand or replace these policies. Missing trusted policy is
a rejection condition, not permission to use a permissive default.

## Fail-Closed Validation Sequence

A future validator must evaluate a proposal in a stable, documented order:

1. confirm that required trusted policies are present
2. validate required metadata fields and safe identifiers
3. validate metadata relationships across request, manifest, preview,
   approval, and sandbox identifiers
4. validate artifact type against the trusted allowlist
5. validate filename safety
6. validate extension and output-format consistency
7. validate declared size against trusted size policy
8. validate path assumptions against the approved sandbox boundary
9. reject overwrite unless a separate future policy explicitly permits it
10. reject hidden persistence, network, or execution side effects
11. produce a deterministic, redacted, report-only result

Any missing rule, unknown value, inconsistent relationship, policy lookup
failure, or internal validation uncertainty must fail closed. Multiple
rejection codes may be reported in stable order. Passing one step does not
skip later steps and does not authorize a write or execution.

## Artifact Type Allowlist

Future artifact type validation must require `artifact_type` and compare it
with a narrow trusted allowlist. Unknown types, empty values, aliases not
defined by policy, and user-defined extensions to the allowlist must be
rejected.

The allowlist is future policy only. Phase 1.6d does not configure it, load it,
or implement a type validator.

## Filename Safety Rules

A future artifact filename must be derived from trusted naming policy, not raw
user input. It must be a filename only, never a path.

Future filename rules must reject:

- empty or whitespace-only names
- path separators
- drive letters and colon syntax
- dot-dot and path traversal
- absolute local paths
- UNC paths
- URL-like values
- shell fragments
- control characters and null bytes
- unsafe leading-dot or hidden-file semantics unless explicitly reviewed
- double-extension ambiguity

No user-controlled artifact paths are allowed. Filename validation must not
inspect the filesystem or attempt to determine whether a real file exists.

## Extension And Output-Format Consistency

The future output-format allowlist remains narrow and policy-controlled. The
Phase 1.6c design candidates are `json`, `markdown`, and `html`.
Zip remains not allowed. This list is design vocabulary, not a runtime configuration.

The filename extension must match the allowed `output_format`. Case changes,
double extensions, declared MIME values, or user aliases must not bypass the
rule. An absent, unknown, or inconsistent format fails closed.

## Required Metadata And Relationship Checks

A future artifact proposal must include these metadata fields before it can be
considered valid:

- artifact_id
- request_id
- manifest_id
- preview_id
- approval_record_id
- sandbox_id
- artifact_type
- output_format
- artifact_filename
- report_only
- retention_policy_id
- cleanup_policy_id

Identifiers must be safe identifiers, not paths, URLs, shell fragments, or
credentials. The request, manifest, preview, approval record, and sandbox
relationships must refer to the same reviewed proposal chain. A mismatch must
be rejected.

For Phase 1.6d design examples, `report_only` must remain true. Metadata must
not contain secrets, tokens, passwords, api_key values, real credentials, raw
local absolute paths, or unredacted dangerous input.

## Size Boundary Concepts

Future trusted policy must define a per-artifact size limit, an aggregate per-request
size limit, and a metadata size limit. Missing size policy,
unknown size, negative size, non-integer size, overflow-like values, and
declared size above policy limits must fail closed.

Required future boundaries include an aggregate per-request size limit.

A declared size is untrusted and cannot replace future enforcement during a
separately approved write phase. Phase 1.6d performs no file inspection and no size
computation. It also performs no checksum computation and no temporary artifact
creation.

There is no size computation in this phase.

## Sandbox And Path Assumptions

Future artifact validation may rely only on an approved sandbox policy. The
sandbox root must come from trusted operator configuration and must not come
from a request, manifest, prompt, filename, or artifact metadata.

Future path enforcement must normalize and resolve the proposed final path,
then prove that it remains inside the approved sandbox root. It must reject
path escape, symlink traversal, UNC paths, absolute paths, drive-letter paths,
and repository or source-tree storage.

Phase 1.6d does not configure a sandbox root, implement a path resolver,
inspect symlinks, inspect the filesystem, or create a sandbox directory.

## Overwrite Policy

Artifact overwrite is disabled by default. A matching artifact identifier,
filename, or destination must not trigger automatic replacement. Validation
success does not authorize overwrite. A separate reviewed future overwrite
policy is required before any overwrite can be considered.

Phase 1.6d does not look up existing artifacts, query a registry, delete a
file, replace a file, or implement rollback and cleanup behavior.

## Network And Hidden Persistence Prohibition

Validation must be side-effect free. It must not:

- upload an artifact
- call real Coze
- download GEO data
- perform URL discovery or any external network request
- write or query an artifact registry
- write or query a database
- create a directory or temporary artifact
- enqueue a worker, queue, or scheduler job
- invoke a pipeline or Snakemake
- escalate from preview or approval to execution

No hidden database persistence and no hidden network upload are permitted.
Future policy lookup must not be invented as permission for these side effects.

## Validation Result Schema Design

This example is documentation-only and report-only. It is not a runtime
response, approval record, persisted row, or execution instruction.

```json
{
  "artifact_validation_preview_id": "validation_preview_placeholder_001",
  "mode": "dry_run",
  "status": "report_only",
  "artifact_id": "artifact_placeholder_001",
  "request_id": "dryrun_placeholder_001",
  "manifest_id": "manifest_placeholder_001",
  "preview_id": "preview_placeholder_001",
  "approval_record_id": "approval_placeholder_001",
  "sandbox_id": "sandbox_placeholder_001",
  "valid": false,
  "report_only": true,
  "files_inspected": false,
  "paths_resolved": false,
  "directories_created": false,
  "files_written": false,
  "artifacts_created": false,
  "database_written": false,
  "network_performed": false,
  "write_approved": false,
  "execution_approved": false,
  "approved_for_implementation": false,
  "rejection_reasons": [
    "ARTIFACT_VALIDATION_NOT_APPROVED",
    "WRITE_NOT_APPROVED",
    "EXECUTION_NOT_APPROVED"
  ]
}
```

All filesystem, persistence, network, write, and execution flags remain false.
The result must use stable rejection-code ordering and must not echo unsafe raw
values.

## Rejection-Code Catalog

Suggested future rejection codes are:

- ARTIFACT_VALIDATION_NOT_APPROVED
- ARTIFACT_TYPE_REQUIRED
- INVALID_ARTIFACT_TYPE
- ARTIFACT_TYPE_NOT_ALLOWLISTED
- ARTIFACT_FILENAME_REQUIRED
- INVALID_FILENAME
- PATH_SEPARATOR_NOT_ALLOWED
- DRIVE_LETTER_NOT_ALLOWED
- COLON_NOT_ALLOWED
- PATH_ESCAPE_ATTEMPT
- ABSOLUTE_LOCAL_PATH_NOT_ALLOWED
- UNC_PATH_NOT_ALLOWED
- SYMLINK_TRAVERSAL_NOT_ALLOWED
- CONTROL_CHARACTER_NOT_ALLOWED
- NULL_BYTE_NOT_ALLOWED
- URL_VALUE_NOT_ALLOWED
- SHELL_FRAGMENT_NOT_ALLOWED
- OUTPUT_FORMAT_REQUIRED
- UNSUPPORTED_OUTPUT_FORMAT
- UNSAFE_EXTENSION
- OUTPUT_FORMAT_EXTENSION_MISMATCH
- ZIP_OUTPUT_NOT_ALLOWED
- MISSING_METADATA
- INVALID_METADATA_IDENTIFIER
- METADATA_RELATIONSHIP_MISMATCH
- SENSITIVE_METADATA_NOT_ALLOWED
- LOCAL_PATH_LEAK_NOT_ALLOWED
- SIZE_POLICY_REQUIRED
- INVALID_SIZE_DECLARATION
- SIZE_LIMIT_EXCEEDED
- SANDBOX_POLICY_REQUIRED
- OUTPUT_PATH_OUTSIDE_SANDBOX_NOT_ALLOWED
- ARTIFACT_OVERWRITE_NOT_ALLOWED
- RETENTION_POLICY_REQUIRED
- CLEANUP_POLICY_REQUIRED
- WRITE_NOT_APPROVED
- NETWORK_UPLOAD_NOT_ALLOWED
- HIDDEN_DATABASE_PERSISTENCE_NOT_ALLOWED
- EXECUTION_NOT_APPROVED

These codes are schema design only. Phase 1.6d does not create an enum, JSON
Schema, Pydantic model, parser, or executable validator.

## Auditability And Redaction

A future validation report must be operator-visible, deterministic, and safe
to audit. It may record rule identifiers, rejection codes, placeholder IDs,
policy identifiers, and pass/fail status. It must not record or echo secrets,
credentials, tokens, passwords, api_key values, raw absolute paths, shell
fragments, or other dangerous original values.

Validation reports remain report-only until future runtime approval. Phase
1.6d does not persist an audit record, write a database, call an external audit
service, calculate a checksum, or inspect an artifact.

## Explicit No-Go Decision

- Validator runtime is not approved.
- Artifact writer is not approved.
- Artifact persistence is not approved.
- Artifact registry is not approved.
- Database persistence is not approved.
- Storage backend is not approved.
- Sandbox implementation is not approved.
- Filesystem inspection is not approved.
- Path resolver is not approved.
- Runtime execution is not approved.
- Runtime API handler integration is not approved.
- Worker / queue / scheduler integration is not approved.
- Network upload is not approved.
- GEO downloader is not approved.
- Snakemake wrapper is not approved.
- Real Coze client is not approved.

Passing documentation tests, receiving a valid report, accepting a preview, or
having an approval record does not authorize implementation, persistence,
write, or execution.

## Final Phase 1.6d Decision

Phase 1.6d is artifact validation rules docs/tests only. It defines future
fail-closed validation and audit boundaries but does not implement them.
Do not directly enter real runtime implementation from this phase.
