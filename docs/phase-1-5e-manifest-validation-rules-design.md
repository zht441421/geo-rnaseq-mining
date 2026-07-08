# Phase 1.5e Manifest Validation Rules Design

Phase 1.5e is manifest validation rules docs/tests only and not
implementation. It extends the Phase 1.5c input manifest schema design and the
Phase 1.5d dry-run execution plan preview design by drafting future manifest
validation rule categories for `geo-rnaseq-mining`.

It is not implementation.

This phase only documents future accept/reject behavior. It does not implement
or generate a manifest validator, manifest parser, runtime validator, JSON
schema file, Pydantic model, API handler integration, execution planner, plan
generator, execution runner, worker, queue, scheduler, pipeline executor,
Snakemake wrapper, GEO downloader, Coze real client, artifact writer, or
database persistence.

Phase 1.5e preserves the dry-run design boundary:

- no manifest validator
- no manifest parser
- no runtime validator
- no JSON schema file
- no Pydantic model
- no API handler integration
- no execution planner
- no plan generator
- no real execution runner
- no pipeline execution
- no Snakemake execution
- no real GEO download
- no real Coze call
- no external network
- no artifacts/database
- no worker / scheduler / queue

## A. Validation Scope

These rules are documentation-only. They describe future accept/reject behavior
for a manifest validator that does not exist in this phase.

Scope constraints:

- rules are documentation-only.
- rules describe future accept/reject behavior.
- no manifest file is parsed in this phase.
- no filesystem checks.
- no file existence checks.
- no network checks.
- no GEO metadata fetch.
- no execution planning.
- no API handler integration.
- no runtime execution.

The rules below are design vocabulary only. They must not be treated as a JSON
schema file, Pydantic model, parser implementation, validator implementation,
runtime validator, or API endpoint.

## B. Required Manifest Presence Rules

A future manifest should be rejected unless these top-level sections are
present:

- manifest_id
- manifest_version
- dataset
- samples
- analysis
- inputs
- outputs
- provenance
- safety
- audit

Future rejection reason:

- MANIFEST_MISSING_REQUIRED_FIELD

Missing fields should produce deterministic rejection reasons. This design does
not parse a manifest or enforce the rule in code.

## C. Identifier Safety Rules

Future validation should require safe identifiers only:

- manifest_id safe identifier only.
- request_id safe identifier only.
- sample_id safe identifier only.
- sandbox_id safe identifier only.
- no path separators.
- no shell fragments.
- no path traversal.
- no whitespace-only identifiers.
- no absolute local paths.

Future rejection reasons:

- UNSAFE_MANIFEST_ID
- UNSAFE_REQUEST_ID
- UNSAFE_SAMPLE_ID
- UNSAFE_SANDBOX_ID
- PATH_TRAVERSAL_NOT_ALLOWED
- ABSOLUTE_LOCAL_PATH_NOT_ALLOWED
- SHELL_FRAGMENT_NOT_ALLOWED

These rules are designed to keep identifiers from becoming filesystem paths,
shell fragments, command carriers, or sandbox escape instructions.

## D. Dataset Rules

Future validation should keep dataset information declarative and offline:

- dataset_accession required.
- dataset_accession accession-like only, e.g. `GSE123456`.
- dataset_source must remain placeholder / not downloaded.
- no automatic GEO download.
- no external URL.
- no external network access.

Future rejection reasons:

- DATASET_ACCESSION_REQUIRED
- UNSAFE_DATASET_ACCESSION
- DATASET_SOURCE_MUST_BE_PLACEHOLDER
- GEO_DOWNLOAD_NOT_ALLOWED
- EXTERNAL_URL_NOT_ALLOWED
- NETWORK_ACCESS_NOT_ALLOWED

Dataset metadata may be described by a manifest, but it must not be fetched in
this phase and must not imply future network approval.

## E. Samples Rules

Future validation should keep samples metadata-only:

- samples must be metadata-only.
- samples must be a non-empty list in future validation.
- each sample should contain sample_id.
- sample_id must be safe.
- condition / replicate / source_name / library_strategy may be descriptive
  metadata.
- no FASTQ real path.
- no BAM real path.
- no count matrix real path.
- no file existence checks.
- no data download.

Future rejection reasons:

- SAMPLES_REQUIRED
- SAMPLE_ID_REQUIRED
- UNSAFE_SAMPLE_ID
- REAL_FASTQ_PATH_NOT_ALLOWED
- REAL_BAM_PATH_NOT_ALLOWED
- REAL_COUNT_MATRIX_PATH_NOT_ALLOWED
- FILE_EXISTENCE_CHECK_NOT_ALLOWED
- DATA_DOWNLOAD_NOT_ALLOWED

These rules avoid turning metadata placeholders into local file probes,
download requests, or real analysis inputs.

## F. Analysis Rules

Future validation should keep analysis intent descriptive:

- analysis_type currently only rnaseq_placeholder.
- analysis goal and contrast are descriptive only.
- normalization_plan documentation-only.
- differential_expression_plan documentation-only.
- no DESeq2 execution.
- no edgeR execution.
- no Salmon execution.
- no STAR execution.
- no featureCounts execution.
- no Snakemake execution.
- no pipeline execution.

Future rejection reasons:

- UNSUPPORTED_ANALYSIS_TYPE
- REAL_RNASEQ_PIPELINE_NOT_ALLOWED
- DESEQ2_EXECUTION_NOT_ALLOWED
- EDGER_EXECUTION_NOT_ALLOWED
- SALMON_EXECUTION_NOT_ALLOWED
- STAR_EXECUTION_NOT_ALLOWED
- FEATURECOUNTS_EXECUTION_NOT_ALLOWED
- SNAKEMAKE_NOT_ALLOWED
- PIPELINE_EXECUTION_NOT_ALLOWED

Accepted analysis metadata must still remain dry-run-only and must not schedule
or start a pipeline.

## G. Inputs Rules

Future validation should allow placeholder references only:

- inputs must contain placeholder references only.
- no command.
- no shell.
- no subprocess.
- no snakemake command.
- no external URL.
- no secret.
- no token.
- no password.
- no api_key.
- no absolute local path.
- no path traversal.

Future rejection reasons:

- INPUTS_MUST_BE_PLACEHOLDER_ONLY
- COMMAND_FIELD_NOT_ALLOWED
- SHELL_FIELD_NOT_ALLOWED
- SUBPROCESS_FIELD_NOT_ALLOWED
- SNAKEMAKE_COMMAND_NOT_ALLOWED
- EXTERNAL_URL_NOT_ALLOWED
- SECRET_FIELD_NOT_ALLOWED
- TOKEN_FIELD_NOT_ALLOWED
- PASSWORD_FIELD_NOT_ALLOWED
- API_KEY_FIELD_NOT_ALLOWED
- ABSOLUTE_LOCAL_PATH_NOT_ALLOWED
- PATH_TRAVERSAL_NOT_ALLOWED

Inputs must not become a command transport, shell adapter, downloader, secret
container, or filesystem scanner.

## H. Outputs Rules

Future validation should keep outputs report-only:

- output_format allowed only json / markdown / html.
- zip not allowed.
- sandbox_id placeholder only.
- write_artifacts must be false.
- report_only must be true.
- no artifact output outside sandbox.
- no database write.

Future rejection reasons:

- UNSUPPORTED_OUTPUT_FORMAT
- ZIP_OUTPUT_NOT_ALLOWED
- SANDBOX_ID_REQUIRED
- ARTIFACT_WRITE_NOT_ALLOWED
- REPORT_ONLY_REQUIRED
- ARTIFACT_OUTPUT_OUTSIDE_SANDBOX_NOT_ALLOWED
- DATABASE_WRITE_NOT_ALLOWED

Output settings must not create artifacts, prepare a real sandbox, or write a
database in this phase.

## I. Provenance Rules

Future validation should keep provenance documentation-only:

- provenance documentation-only.
- request_id required.
- no real credentials.
- no secrets from environment.
- no database persistence.
- no system user secret access.

Future rejection reasons:

- PROVENANCE_REQUEST_ID_REQUIRED
- REAL_CREDENTIALS_NOT_ALLOWED
- ENV_SECRET_ACCESS_NOT_ALLOWED
- DATABASE_PERSISTENCE_NOT_ALLOWED
- SYSTEM_USER_SECRET_ACCESS_NOT_ALLOWED

Provenance must not read environment secrets, system user secrets, credentials,
or persistent stores.

## J. Safety Rules

Future validation should require safety flags to fail closed:

- allow_network false.
- allow_pipeline_execution false.
- allow_snakemake false.
- allow_real_coze_call false.
- allow_artifact_write false.
- allow_database_write false.
- allow_background_execution false.

Future rejection reasons:

- NETWORK_ACCESS_NOT_ALLOWED
- PIPELINE_EXECUTION_NOT_ALLOWED
- SNAKEMAKE_NOT_ALLOWED
- REAL_COZE_CALL_NOT_ALLOWED
- ARTIFACT_WRITE_NOT_ALLOWED
- DATABASE_WRITE_NOT_ALLOWED
- BACKGROUND_EXECUTION_NOT_ALLOWED

Missing or omitted safety flags must not imply permission.

## K. Audit Rules

Future validation should require operator-visible report-only audit behavior:

- report_only true.
- include_rejection_reasons true.
- operator_visible true.
- approval_required_for_future_runtime true.
- no automatic escalation to execution.

Future rejection reasons:

- REPORT_ONLY_REQUIRED
- REJECTION_REASONS_REQUIRED
- OPERATOR_VISIBLE_REPORT_REQUIRED
- FUTURE_RUNTIME_APPROVAL_REQUIRED
- AUTOMATIC_EXECUTION_ESCALATION_NOT_ALLOWED

Audit acceptance must not become runtime approval.

## L. Deterministic Rejection Behavior

A future validator should return deterministic rejection reasons. Multiple
rejection reasons may be returned together, and rejection order should be
stable. Stable rejection order should be defined before implementation.

Rejected manifest behavior:

- rejected manifest must not create artifacts.
- rejected manifest must not start execution.
- rejected manifest must not write database.
- rejected manifest must not call network.
- rejected manifest must remain preview/report-only.
- execution not_started.
- artifacts_created false.
- network_performed false.
- database_written false.

This phase does not implement deterministic rejection reasons or stable
rejection order. It only records the expected future behavior.

## M. Future Accepted Manifest Conditions

Future accepted manifests are accepted only for dry-run preview. An accepted
dry-run manifest does not mean real execution.

Future dry-run accepted conditions:

- all required sections present.
- identifiers are safe.
- dataset accession is accession-like.
- samples are metadata-only.
- analysis is rnaseq_placeholder.
- inputs are placeholder-only.
- output_format is json / markdown / html.
- write_artifacts false.
- report_only true.
- all safety flags false.
- audit is operator-visible.
- no forbidden fields present.

Required caveats:

- accepted dry-run manifest does not mean real execution.
- accepted dry-run manifest does not create artifacts.
- accepted dry-run manifest does not approve network access.
- accepted dry-run manifest does not approve pipeline execution.
- accepted dry-run manifest does not write database.
- accepted dry-run manifest does not start worker, queue, or scheduler work.

## N. Safe Validation Outcome Examples

These examples are design-only outcome examples. They are not outputs from a
manifest validator, runtime validator, API handler, execution planner, or plan
generator.

Accepted dry-run manifest outcome:

```json
{
  "accepted": true,
  "mode": "dry_run",
  "status": "accepted_for_preview_only",
  "rejection_reasons": [],
  "execution": "not_started",
  "artifacts_created": false,
  "network_performed": false,
  "database_written": false
}
```

Rejected manifest outcome:

```json
{
  "accepted": false,
  "mode": "dry_run",
  "status": "rejected",
  "rejection_reasons": [
    "UNSAFE_DATASET_ACCESSION",
    "ARTIFACT_WRITE_NOT_ALLOWED"
  ],
  "execution": "not_started",
  "artifacts_created": false,
  "network_performed": false,
  "database_written": false
}
```

Both examples keep execution not_started, artifacts_created false,
network_performed false, and database_written false.

## O. Explicit Non-Goals

Phase 1.5e does not implement or generate any of the following:

- manifest validator
- manifest parser
- runtime validator
- JSON schema file
- Pydantic model
- API endpoint
- API handler integration
- filesystem checks
- file existence checks
- GEO download
- RNA-seq pipeline
- Snakemake wrapper
- Snakemake execution
- execution planner
- plan generator
- execution runner
- real execution runner
- sandbox creation
- artifact writing
- artifact writer
- database persistence
- queue / worker / scheduler
- real runtime execution
- worker / queue / scheduler
- GEO downloader
- Coze real client

It also does not run pipeline tasks, run Snakemake, download datasets, call
real Coze services, create artifacts, write a database, start a long-running
server, or start background execution.

## P. Next Phase Options

The next phase must remain design-only or documentation-test-only unless a
separate reviewed boundary explicitly chooses otherwise. Safe options are:

- Phase 1.5f operator approval record design only
- Phase 1.5f dry-run preview test fixtures docs only
- Phase 1.5f manifest validation rules test matrix docs only

Do not directly enter real execution implementation. Do not skip from these
validation rule designs to a manifest validator, runtime validator, real
runner, planner, worker, queue, scheduler, pipeline executor, Snakemake
wrapper, GEO downloader, Coze real client, artifact writer, database
persistence, or external network integration.
