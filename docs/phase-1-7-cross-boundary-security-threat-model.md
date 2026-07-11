# Phase 1.7 Cross-Boundary Security Threat Model

Phase 1.7 is a Cross-Boundary Security Threat Model docs/tests only phase for
`geo-rnaseq-mining`. It builds on the Phase 1.6a readiness audit, Phase 1.6b
sandbox boundary, Phase 1.6c artifact persistence boundary, and Phase 1.6d
artifact validation rules.

## Scope And Readiness Conclusion

This phase documents assets, actors, trust boundaries, threats, current design
controls, remaining risks, and future prerequisites. It is not implementation.
The threat model does not authorize implementation, runtime execution, writes,
persistence, network access, or security enforcement.

The project is not ready for runtime security enforcement. Design controls are
not actually enforced controls. Passing documentation tests or accepting this
threat model does not approve a runtime, API handler, sandbox, artifact writer,
database, network client, worker, queue, scheduler, or external integration.

## Assets

Assets requiring future protection include:

- task request and its safety flags
- manifest and dataset identity
- execution preview and blocked-action report
- approval record, scope, expiration, and revocation state
- validation result and rejection reasons
- artifact metadata, identity, filename, format, and lifecycle policy
- audit information and operator-visible decision history
- credentials/secrets boundary, without storing real credentials here
- trusted policy identifiers and cross-record relationships
- future GEO, Snakemake, and Coze interfaces
- future sandbox root and artifact destination policy
- future database, registry, and network configuration

Availability, integrity, confidentiality, provenance, and relationship
consistency are all security properties of these assets.

## Actors

- **User:** supplies task intent and untrusted input; cannot grant execution.
- **Operator:** reviews previews and approvals; future authority must be scoped,
  authenticated, revocable, and auditable.
- **Future runtime service:** would interpret approved inputs, but does not exist
  as an approved runtime in this phase.
- **Future worker:** would perform bounded work, but worker integration is not
  approved.
- **External service:** includes future GEO, Coze, storage, audit, identity, or
  other network services; all remain outside the trusted boundary by default.
- **Attacker:** may act through malicious input, compromised identity, replay,
  confused-deputy behavior, dependency compromise, or external-service abuse.

No actor may infer write or execution permission from a successful preview,
approval record, validation result, or documentation test.

## Trust Boundaries

### User Input Boundary

Task text, identifiers, paths, filenames, URLs, size declarations, output
formats, and policy-like values are untrusted. User input cannot configure a
sandbox root, allowlist, credential source, overwrite permission, or network
destination.

### Manifest Boundary

A manifest is structured design input, not trusted execution authority. It
cannot bypass request rules, introduce secrets, trigger GEO download, or grant
filesystem, database, network, or execution access.

### Approval Boundary

An approval record is a scoped decision record, not an execution token.
Expiration, revocation, replay resistance, actor identity, scope binding, and
proposal relationship checks remain future prerequisites.

### Validation Boundary

Validation must fail closed and remain report-only. Validation success does not
authorize write or execution, and an approval record cannot bypass validation.
The validator runtime does not exist in this phase.

### Sandbox Boundary

The sandbox root must be future trusted operator configuration, not user input.
Normalization, containment, symlink safety, TOCTOU resistance, cleanup, and
resource isolation remain unimplemented.

### Artifact Boundary

Artifact identity, naming, format, size, overwrite, retention, cleanup,
redaction, and audit metadata are design policies only. No artifact writer,
registry, or persistence layer is approved.

### Network Boundary

Network access is prohibited. Future GEO, Coze, identity, audit, or storage
interfaces require allowlists, destination validation, credential scoping,
timeouts, provenance, and exfiltration controls before implementation.

### Audit Boundary

Audit information must be deterministic, redacted, operator-visible, and
tamper-evident in a future phase. No audit persistence, external audit service,
or trusted audit storage exists in this phase.

## Threat Classification

This model uses STRIDE as an organizing framework:

- **Spoofing:** forged user/operator/service identity or approval ownership.
- **Tampering:** altered manifest, preview, approval, validation result,
  artifact metadata, policy identifier, or audit information.
- **Repudiation:** missing or mutable decision history that prevents reliable
  attribution.
- **Information Disclosure:** secret leakage, local path leakage, sensitive
  error disclosure, artifact leakage, or network exfiltration.
- **Denial of Service:** resource exhaustion, oversized proposals, stuck work,
  cancellation failure, or cleanup failure.
- **Elevation of Privilege:** approval bypass, unsafe policy injection,
  privilege escalation, or automatic transition to execution.

STRIDE classification is analysis vocabulary only and does not provide runtime
protection.

## Specific Threats

The cross-boundary threat set includes:

- path traversal and output path escape
- symlink traversal and link substitution
- TOCTOU between validation and future use
- overwrite abuse and identifier collision
- command injection and shell-fragment propagation
- unsafe input propagation across request, manifest, preview, and artifact
- approval bypass
- stale approval after scope or proposal changes
- replay of approval, preview, validation result, or request identifiers
- ID relationship mismatch across request, manifest, preview, approval,
  sandbox, validation, and artifact records
- privilege escalation and confused-deputy behavior
- secret leakage and credential exposure
- local path leakage
- hidden persistence to database, registry, file, cache, or audit service
- network exfiltration
- SSRF-like risk through URL, accession, callback, redirect, or service input
- resource exhaustion through size, count, CPU, memory, disk, or time pressure
- cancellation failure
- cleanup failure, partial state, and orphan artifacts
- audit tampering, deletion, reordering, or forgery
- sensitive error disclosure

## Existing Design Controls

The project already documents these design controls:

- fail-closed by default
- report-only until future runtime approval
- approval/execution separation
- validation/write/execution separation
- artifact validation rules and stable rejection-code concepts
- path safety concepts, sandbox containment, and traversal rejection
- overwrite disabled by default
- network prohibition
- hidden persistence prohibition
- no automatic escalation from approval to execution
- redaction concepts for credentials, local paths, and unsafe values

These controls reduce design ambiguity. They do not enforce security because
the corresponding runtime, identity, sandbox, persistence, network, audit, and
lifecycle systems are not implemented or approved.

## Control Mapping

| Threat | Current design mitigation | Remaining gap | Future prerequisite |
| --- | --- | --- | --- |
| Path traversal | Reject separators, dot-dot, absolute paths, and sandbox escape | No resolver or filesystem enforcement | Reviewed path enforcement and sandbox implementation |
| Symlink traversal / TOCTOU | Explicit rejection and no filesystem inspection now | No atomic containment enforcement | Threat-reviewed filesystem API and race-safe sandbox design |
| Overwrite abuse | Overwrite disabled by default | No registry collision or atomic-create enforcement | Approved overwrite, registry, rollback, and cleanup policy |
| Command injection | Shell fragments and unsafe values are forbidden | No runtime command construction boundary | Execution interface design that avoids shell interpretation |
| Unsafe input propagation | Trust model and staged relationship checks | No taint tracking or executable validator | Approved parsers, validators, and canonical data model |
| Approval bypass | Approval does not authorize execution and cannot bypass validation | No identity, authorization, expiry, or revocation enforcement | Refined approval security boundary and authentication design |
| Stale approval / replay | IDs and relationship matching are required by design | No nonce, version, expiry, or replay store | Approval binding, freshness, revocation, and anti-replay design |
| ID relationship mismatch | Phase 1.6d requires cross-record consistency | No validator runtime | Approved deterministic relationship validator |
| Privilege escalation | No automatic escalation and least-authority intent | No authentication or authorization system | Identity, role, scope, and authorization boundary design |
| Secret leakage | Secrets and credentials forbidden in request, metadata, and reports | No secret provider, scanner, or runtime redaction | Secrets management and redaction boundary design |
| Local path leakage | Raw absolute paths forbidden and reports must be redacted | No runtime error or log redaction | Structured error and audit redaction enforcement design |
| Hidden persistence | Database, registry, file, and audit writes prohibited | No controlled persistence boundary | Separate database and audit persistence boundary reviews |
| Network exfiltration | External network access and upload prohibited | No egress enforcement | Network boundary with destination and data-flow controls |
| SSRF-like risk | URLs and user-controlled network destinations forbidden | No URL parser, DNS, redirect, or IP controls | Network threat design and allowlisted client boundary |
| Resource exhaustion | Size policies and fail-closed unknown sizes are designed | No CPU, memory, disk, count, or timeout enforcement | Resource and lifecycle limit design |
| Cancellation failure | Cancellation cleanup required before persistence | No state machine or cancellation protocol | Task lifecycle/state machine and idempotent cleanup design |
| Cleanup failure | Partial, failed, orphan, and rollback policies required | No cleanup implementation | Reviewed lifecycle, rollback, and recovery design |
| Audit tampering | Stable, operator-visible, redacted audit vocabulary | No tamper-evident storage or access control | Audit logging and persistence boundary design |
| Sensitive error disclosure | Rejection codes must not echo dangerous raw values | No structured runtime error enforcement | Error contract and redaction enforcement design |

## Remaining Risks

Design controls are not actually enforced controls. The remaining risk is high
for any real execution because the system has no approved runtime parser,
validator, authentication, authorization, sandbox, artifact writer, database,
network control, resource limiter, task state machine, audit storage, secret
provider, or recovery mechanism.

Documentation can identify unsafe transitions but cannot prevent them. A future
implementation must be separately scoped, reviewed, tested, and manually
approved. No single approval record or successful validation result may close
all remaining gaps.

## Threat Assessment Schema Design

The following is a documentation-only, report-only example. It is not a JSON
Schema, Python model, validator, API response, database row, or persisted audit
record.

```json
{
  "threat_assessment_id": "threat_assessment_placeholder_001",
  "mode": "design_only",
  "status": "report_only",
  "assets_reviewed": ["placeholder_only"],
  "trust_boundaries_reviewed": ["placeholder_only"],
  "threats_identified": ["PATH_TRAVERSAL_RISK"],
  "design_controls_identified": ["FAIL_CLOSED_DESIGN_ONLY"],
  "remaining_gaps": ["RUNTIME_ENFORCEMENT_NOT_APPROVED"],
  "files_inspected": false,
  "artifacts_created": false,
  "sandbox_created": false,
  "database_written": false,
  "audit_persisted": false,
  "network_performed": false,
  "runtime_enforced": false,
  "write_approved": false,
  "execution_approved": false,
  "approved_for_implementation": false
}
```

All side-effect and approval flags remain false. Phase 1.7 does not create a
JSON schema, Python model, Pydantic model, validator, or threat-scanning tool.

## Explicit No-Go Decision

- Runtime security enforcement is not approved.
- Authentication system implementation is not approved.
- Authorization system implementation is not approved.
- Secrets management system implementation is not approved.
- Database implementation is not approved.
- Storage backend implementation is not approved.
- Network controls implementation is not approved.
- Sandbox implementation is not approved.
- Artifact writer, registry, and persistence are not approved.
- Validator runtime is not approved.
- Audit storage and audit persistence are not approved.
- API handler integration is not approved.
- Worker / queue / scheduler integration is not approved.
- GEO downloader, Snakemake execution, and Coze integration are not approved.

The threat model does not authorize implementation.
Do not directly enter real runtime implementation from Phase 1.7.

## Next Phase Recommendation

Recommend exactly one next topic: **Phase 1.8 secrets management and redaction
boundary design docs/tests only**. Credentials affect operator identity, future
network clients, error handling, audit information, and external interfaces;
their trusted source, scope, rotation, non-disclosure, and redaction boundaries
must be designed before any network or runtime integration is considered.

This recommendation does not approve a secret loader, credential provider,
authentication system, network client, or runtime implementation.

## Final Phase 1.7 Decision

Phase 1.7 is a Cross-Boundary Security Threat Model docs/tests only phase. It
records design controls and remaining risks but provides no runtime security
enforcement. The project remains not ready for real runtime implementation.
