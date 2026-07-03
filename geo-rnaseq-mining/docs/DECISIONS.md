# Decisions

## 2026-07-03 - D015: Default Entry Is Skeleton Validation, Not Production

### Decision

The default Snakemake entry must be executable with `config/config.yaml`, but
its success represents only the safe skeleton / validation / empty-accession
path. MVP fixture execution remains explicit through
`tests/fixtures/config/test_config.yaml`, and real production execution
requires real inputs and runtime dependencies.

### Rationale

The previous default `rule all` required `mvp.enabled=true` and failed under
the default configuration. The repair makes the default entry useful for
smoke-testing the repository while preventing fixture or skeleton success from
being confused with real biological analysis completion.

### Scope

- Default Snakemake entry behavior.
- Config schema acceptance of optional `mvp` settings.
- README, CI, and handoff wording around run modes and validation status.

### Boundaries

- Do not copy fixture paths into `config/config.yaml` for production.
- Do not describe default skeleton / empty-accession success as real production
  validation.
- Do not describe fixture MVP e2e success as real production data support.
- Do not describe dry-run success as real execution success.

## D001: Human-reviewed files are authoritative

Formal analysis may only consume:

- `metadata/reviewed/sample_manifest.tsv`
- `metadata/reviewed/contrasts.tsv`
- `metadata/reviewed/dataset_plan.tsv`
- `metadata/reviewed/celltype_ontology.tsv`

Suggested metadata outputs are review aids only.

Legacy files under `config/` may remain as templates or compatibility examples,
but formal workflow rules must not use them as authoritative analysis inputs.

## D002: Stage-gated development

Only tasks in `docs/NEXT_TASK.md` are authorized for the next development
session. After a stage is complete, update the handoff documents and stop.

## D003: Preserve existing uncommitted work

The working tree contained a pre-existing modification to
`workflow/rules/common.smk`. It is treated as user or prior-session work and was
not reverted.

## D004: Placeholder scripts fail clearly

Top-level Stage 1 placeholder scripts must exit with an explicit "not
implemented in Stage 1" message if called. They must not silently generate
analysis outputs.

## D005: Stage 2 suggested outputs are not authority

`metadata/suggested/sample_manifest_suggested.tsv`,
`metadata/suggested/dataset_plan_suggested.tsv`, and
`metadata/suggested/data_entry_classification.tsv` are review aids only. They
must not populate final `group`, `subject_id`, `include`, `batch`,
`data_type`, `entry_point`, contrast, or merge-strategy decisions.

## D006: Empty accession metadata runs are valid skeleton runs

When `geo.accessions` is empty, the metadata fetch step may generate header-only
raw metadata files and warning events. This supports reproducible local
validation without requiring R/GEOquery, but it is not evidence that real GEO
network fetching has been tested.

## D007: Real GEOquery execution requires a compatible runtime

Configured GSE accessions still use GEOquery through the portable R launcher.
Native Windows conda could not solve the required Bioconductor packages in this
session, so real GEO fetch validation should be performed in Linux, WSL, or a
container before claiming real-accession support.

## D008: Missing reviewed authority files are validation errors

Formal Snakemake rules may reference reviewed authority paths through params so
that validation can run and emit structured reports. A missing reviewed
authority file must be reported as `MISSING_AUTHORITY_FILE`; it must not be
silently replaced by a legacy `config/*` file.

## D009: Bulk R boundaries must revalidate raw counts

Bulk R scripts must validate finite non-negative integer raw counts before any
numeric or integer coercion. Upstream Python validation is required, but it is
not the only guard against TPM, FPKM, CPM, log, fractional, negative, missing,
or non-finite values reaching DESeq2 or bulk QC.

## D010: Automated single-cell annotations are never final

Automated cluster annotation outputs must carry explicit review metadata:
`review_status=not_reviewed`, `is_final=false`, and
`required_action=human_review_required`. These suggestions must not overwrite
`author_label` and must not be treated as confirmed ontology mappings.

## D011: Pseudobulk replicate unit is subject-group, not sample

Subject-level pseudobulk aggregation must not create biological replicates from
multiple samples belonging to the same subject and group. The aggregation key is
dataset, subject, group, cell type, plus any explicitly reviewed extra strata.
Different groups for the same subject remain separate observations so paired or
longitudinal designs can be modeled with `subject_id` or `paired_group`.

## D012: Bulk/scRNA integration is candidate evidence only

Automated bulk-to-single-cell integration outputs must not be presented as
final biological conclusions. Candidate gene scores must include
`is_final_biological_conclusion=false` and
`required_action=human_review_required`.

Confidence must be marked `limited` when evidence is constrained by single-GSE
support, opposite bulk/pseudobulk direction, ambiguous one-to-many gene mapping,
or upstream validation failure.

## D013: Reports must not infer test success or final review

HTML reports may display validation payloads, provenance, candidate-gene
scores, suggested annotations, and test-status artifacts, but they must not
infer that missing or unrun tests passed.

Reports must keep automated annotations and bulk/single-cell candidate genes in
a review-required state unless a formal reviewed authority file or explicit
test-status artifact supports a stronger statement.

## D014: Default machine-readable test status is conservative

Workflow-generated `test_status.tsv` rows must default to `not_run` /
`not_run_by_workflow` for tests and validations not executed by the workflow
itself. The artifact may make outstanding validation work visible, but it must
not mark unit tests, integration tests, opt-in network tests, real GEO fetches,
native R/Bioconductor execution, or real-data end-to-end runs as passed unless
those exact commands are actually run and recorded.
