# Phase 2.1 Scientific Pilot Readiness Planning

Phase 2.1 is Scientific Pilot Readiness Planning for `geo-rnaseq-mining`.

This phase is docs/tests-only, planning-only, scientific-governance-only,
no-external-data-access, no-scientific-execution, and no-runtime-
implementation. Scientific planning is not scientific execution. Dataset
identification is not dataset download. Readiness assessment is not run
authorization. Manual review approval is not automatic execution approval.

## 1. Phase Identity

- Phase: Phase 2.1
- Title: Scientific Pilot Readiness Planning
- Classification: docs/tests-only
- Scope: planning-only
- External data access: not authorized
- Scientific Pilot execution: not authorized
- Scientific execution: not authorized
- Runtime implementation: not authorized

Phase 2.1 defines governance requirements for a future Scientific Pilot. It
does not implement or perform those requirements.

Phase 2.1 does not authorize Scientific Pilot execution. Phase 2.1 does not
authorize dataset search or download. Phase 2.1 does not authorize runtime
implementation.

## 2. Baseline

- Branch: `123`
- Synchronized SHA: `29d8a1644be4cfb72cfafe0a33814f3e3b447392`
- HEAD equals `origin/123`: yes
- Working tree was clean at phase start: yes
- HEAD had no tag at phase start: yes
- Platform Design Baseline is complete: yes
- Phase 1.10 Project State Synchronization is complete and synchronized: yes

This baseline records repository state only. It does not include credentials,
tokens, secrets, environment values, dataset identifiers, or scientific
results.

## 3. Purpose

Phase 2.1 defines whether a future Scientific Pilot can be safely and
meaningfully authorized. It establishes the planning framework for a narrow
RNA-seq pilot question, dataset eligibility, manual review, evidence
requirements, stop conditions, result interpretation, and handoff.

This phase does not:

- select a final live dataset
- download data
- run analysis
- generate scientific findings
- validate biological hypotheses
- implement runtime controls

## 4. Pilot Scientific Question Template

A future pilot must use one narrow, testable scientific question. If no
existing project document already provides an approved question, Phase 2.1
provides a placeholder template only and does not select a live question.

Required template fields:

- biological context
- condition or phenotype
- comparison groups
- organism
- tissue or cell type
- assay type
- expected evidence
- excluded interpretations
- intended learning objective
- reason the question is suitable for a pilot

The future question must be specific enough that a reviewer can determine the
eligible samples, comparison groups, expected input type, and interpretation
limits before execution.

Prohibited question patterns:

- broad exploratory fishing
- undefined phenotype comparisons
- multiple unrelated diseases or tissues
- claims of causality
- clinical conclusions
- production-level benchmarking

No actual live scientific question is selected in Phase 2.1.

## 5. Pilot Scope Boundary

The future Scientific Pilot must be deliberately small. The recommended
planning boundary is:

- one public study
- one organism
- one tissue or cell context
- one assay family
- one primary comparison
- a small sample count suitable for manual verification
- one planned output package
- no cohort merging
- no multi-study meta-analysis
- no batch integration across unrelated studies
- no clinical decision support
- no production SLA

Because no existing project policy defines exact pilot sample-count limits,
Phase 2.1 does not invent exact limits. The future sample count must be a
human-approved bounded range selected before execution authorization.

## 6. Dataset-Selection Criteria

Dataset-selection criteria are planning criteria only. Phase 2.1 does not
search for, name, or select candidate datasets.

Required inclusion criteria:

- public accessibility
- clear study metadata
- clear organism
- clear assay type
- identifiable biological groups
- adequate sample annotations
- sufficient replication for the intended comparison
- raw or count-level data availability appropriate for the future method
- traceable accession identifiers
- no requirement for private credentials
- no controlled-access human data
- manageable expected data volume
- compatible licensing or reuse terms
- absence of obvious ethical restrictions for the planned use

Required exclusion criteria:

- controlled-access data
- unclear consent or reuse conditions
- ambiguous group labels
- missing sample-level metadata
- mixed organisms
- mixed assay types without a predefined separation rule
- single-sample comparison
- unclear treatment or phenotype
- studies requiring clinical interpretation
- studies requiring identity linkage
- studies whose size exceeds the future approved operational budget
- studies requiring custom runtime features not yet designed

## 7. Dataset Candidate Record Schema

The dataset candidate record is a report-only planning record. It is not a
runtime schema, not a database schema, not a manifest parser contract, and not
an authorization to perform lookup or download.

Suggested candidate record fields:

- candidate_id
- source_repository
- accession
- title
- organism
- tissue_or_cell_type
- assay_type
- biological_question_fit
- comparison_groups
- sample_count_summary
- metadata_completeness
- replication_assessment
- expected_data_type
- expected_data_volume
- access_classification
- ethics_or_consent_notes
- license_or_reuse_notes
- known_confounders
- exclusion_flags
- reviewer_notes
- recommendation
- reviewed_by
- reviewed_at
- evidence_references

This record does not authorize network lookup. It does not authorize data
download. Any recommendation must be human-reviewed and recorded before a later
Go/No-Go decision.

## 8. Manual Review Gates

No gate may automatically trigger execution. Gate 7 requires explicit human
authorization in a later phase.

### Gate 1 - Scientific Question Approval

- Required evidence: completed pilot question template and excluded
  interpretations.
- Reviewer role: scientific reviewer.
- Pass condition: one narrow, testable question is approved.
- Fail condition: question is broad, causal, clinical, or under-specified.
- Unresolved condition: required context or comparison details are missing.
- Required recorded decision: approve, reject, or needs revision.

### Gate 2 - Candidate Dataset Eligibility Review

- Required evidence: candidate record and inclusion/exclusion assessment.
- Reviewer role: dataset reviewer.
- Pass condition: candidate meets planning inclusion criteria and no exclusion
  criterion applies.
- Fail condition: any hard exclusion criterion applies.
- Unresolved condition: eligibility evidence is incomplete.
- Required recorded decision: eligible, ineligible, or unresolved.

### Gate 3 - Metadata Completeness Review

- Required evidence: metadata summary and sample/group table.
- Reviewer role: metadata reviewer.
- Pass condition: sample identities, groups, organism, assay, and tissue/cell
  context are reviewable.
- Fail condition: key sample-level metadata are missing or contradictory.
- Unresolved condition: metadata needs manual clarification.
- Required recorded decision: complete, incomplete, or clarification required.

### Gate 4 - Ethics/Access/Reuse Review

- Required evidence: access classification, consent or reuse notes, and
  license/reuse notes.
- Reviewer role: ethics/access reviewer.
- Pass condition: data are public, reusable for the planned purpose, and not
  controlled access.
- Fail condition: controlled access, credential requirement, unclear reuse, or
  identity-linkage concern.
- Unresolved condition: access or reuse status cannot be verified.
- Required recorded decision: acceptable, rejected, or unresolved.

### Gate 5 - Operational-Size Review

- Required evidence: expected data-volume estimate and sample-count summary.
- Reviewer role: operations reviewer.
- Pass condition: expected size fits the future approved budget.
- Fail condition: expected size exceeds budget or cannot be bounded.
- Unresolved condition: size estimate is missing or uncertain.
- Required recorded decision: size approved, size rejected, or size unresolved.

### Gate 6 - Analysis-Plan Review

- Required evidence: preliminary analysis outline, input assumptions,
  comparison definition, QC outline, and limitations.
- Reviewer role: analysis reviewer.
- Pass condition: the plan is coherent, bounded, and does not require
  unavailable runtime capability.
- Fail condition: plan requires unsupported tools, hidden assumptions, or scope
  expansion.
- Unresolved condition: method, QC threshold, input type, or model choice is
  not settled.
- Required recorded decision: plan accepted, plan rejected, or revision needed.

### Gate 7 - Execution Go/No-Go

- Required evidence: complete evidence package and all previous gate decisions.
- Reviewer role: named human approver.
- Pass condition: explicit later-phase Go authorization names the approved
  question, dataset, scope, commands or workflow, files, outputs, stop
  conditions, and no-go items.
- Fail condition: any required approval, evidence item, or boundary is absent.
- Unresolved condition: any evidence item, reviewer, scope, or command/workflow
  boundary is unsettled.
- Required recorded decision: Go, No-Go, or deferred.

Gate 7 does not exist in Phase 2.1 as execution approval. It is a future
authorization boundary.

## 9. Evidence Package Requirements

Before Scientific Pilot execution can be considered, the following minimum
evidence must exist:

- approved pilot question
- candidate dataset record
- accession evidence
- dataset metadata summary
- sample/group table
- inclusion/exclusion assessment
- replication assessment
- expected input-type description
- expected data-volume estimate
- ethics/access/reuse review
- known confounders
- preliminary analysis outline
- expected outputs
- success criteria
- failure criteria
- stop conditions
- human Go/No-Go record

Evidence may be manually assembled during a later authorized dataset-review
phase. Phase 2.1 does not access external data to assemble this package.

## 10. Preliminary Analysis-Plan Boundary

A future pilot analysis plan must describe what would be analyzed without
implementing it. It must include:

- input assumptions
- sample inclusion rules
- group labels
- metadata normalization rules
- basic quality checks
- primary comparison
- planned normalization approach
- planned statistical comparison
- multiple-testing handling
- effect-size reporting
- minimum interpretability requirements
- output tables
- output plots
- limitations
- no-go conditions

Phase 2.1 does not select tools. Do not select tools in Phase 2.1. Phase 2.1
does not install tools, write executable workflow steps, prescribe commands,
or modify Snakemake files.

## 11. Pilot Success Criteria

Planning-level pilot success requires:

- dataset eligibility can be independently verified
- all included samples have traceable metadata
- comparison groups are unambiguous
- analysis inputs can be described without hidden assumptions
- outputs can be linked back to source samples
- results can be interpreted within a narrow scientific question
- limitations are explicitly recorded
- no unsupported causal or clinical claim is made
- run evidence is complete enough for independent review
- stop conditions are respected

Statistical significance alone is not sufficient for pilot success.

## 12. Pilot Failure Criteria

Planning-level or future execution failure includes:

- insufficient replication
- contradictory metadata
- unresolvable sample identity
- access or licensing uncertainty
- uncontrolled study heterogeneity
- missing required evidence
- excessive operational size
- unsupported input type
- required runtime capability absent
- quality-control failure
- reviewer rejection
- scientific question drift
- attempt to broaden scope during execution

Failure criteria must be recorded, not hidden by manual exclusions or scope
changes.

## 13. Stop Conditions

Pre-execution stop conditions:

- candidate requires controlled access
- metadata is materially incomplete
- sample groups cannot be verified
- ethics or reuse status is unclear
- expected data volume is not approved
- analysis plan requires unavailable runtime capability
- human Go/No-Go record is missing

Future execution stop conditions, defined here as planning-only requirements:

- downloaded content does not match approved accession
- sample manifest differs from approved record
- unexpected assay type is detected
- required samples are missing
- checksum or integrity evidence fails
- quality thresholds fail
- scope expands beyond approval
- credentials or secrets would be required unexpectedly
- network access exceeds approved endpoints
- runtime state cannot be authoritatively recorded

These conditions are not implemented in Phase 2.1.

## 14. Run-Log Requirements

A future scientific run log must contain:

- run_id
- pilot_plan_version
- authorization_record
- approved_question
- approved_dataset_candidate
- accessions
- operator
- start_time
- end_time
- input_manifest_reference
- software/environment reference
- analysis-plan reference
- commands_or_workflow_reference
- checkpoints
- manual decisions
- warnings
- deviations
- stop events
- output references
- validation results
- reviewer
- final disposition

This is a report-only specification. No run log is created in Phase 2.1. No
runtime persistence is implemented.

## 15. Result Package Requirements

A future pilot result package must include:

- executive scientific summary
- approved question
- dataset provenance
- final sample table
- exclusions and reasons
- quality-control summary
- primary result tables
- result plots
- effect sizes
- uncertainty measures
- multiple-testing information
- limitations
- deviations from plan
- failed checks
- reproducibility references
- run log
- reviewer sign-off
- final recommendation

The result package must prohibit:

- clinical claims
- causal claims unsupported by design
- population-level generalization beyond the dataset
- hidden manual exclusions
- undocumented parameter changes

## 16. Interpretation Boundary

The pilot tests scientific and operational feasibility. The pilot does not
establish clinical validity. It does not establish production readiness. It
does not authorize automated interpretation. It does not validate all RNA-seq
use cases. It does not replace domain-expert review.

## 17. Execution Authorization Boundary

Phase 2.1 does not authorize Scientific Pilot execution.

A later execution authorization must include:

- approved scientific question
- approved candidate dataset
- approved accessions
- approved dataset size
- approved analysis plan
- approved network scope
- approved storage scope
- approved credentials boundary, if any
- approved stop conditions
- named human approver
- exact allowed commands or workflow
- exact allowed files
- exact allowed outputs
- exact commit baseline
- explicit no-go items

Planning approval must not be interpreted as execution approval.

## 18. Relationship To Runtime Implementation

Scientific Pilot planning is separate from Runtime MVP. Pilot execution may
remain manual and tightly bounded. No queue, worker, scheduler, runner,
database, or service is authorized.

Pilot findings may later inform runtime requirements, but pilot results must
not silently change Platform Design Baseline decisions. Runtime implementation
still requires a separate Go/No-Go. Runtime implementation still requires a
separate Go/No-Go decision.

## 19. Current Unresolved Items

The following planning questions must be resolved later and must not be
resolved by guessing:

- exact biological question
- exact candidate dataset
- exact accession list
- exact sample-count bound
- exact analysis method
- exact QC thresholds
- exact statistical model
- exact expected outputs
- exact network endpoints
- exact storage budget
- exact execution environment
- named reviewers and approver
- execution date
- retention policy for downloaded data and outputs

## 20. Explicit No-Go

Phase 2.1 does not authorize or perform:

- GEO search
- GEO download
- SRA search
- SRA download
- NCBI access
- Entrez access
- external HTTP requests
- browser automation
- Coze
- credentials
- tokens
- environment-secret reads
- file download
- Snakemake
- RNA-seq pipeline execution
- alignment
- quantification
- differential expression
- plotting scientific results
- report generation from live data
- database
- queue
- worker
- scheduler
- runner
- sandbox
- artifact creation
- state-store implementation
- retry
- replay
- cancellation
- cleanup
- authn/authz
- runtime implementation
- Scientific Pilot execution

## 21. Completion Criteria

Phase 2.1 is complete only when:

- the pilot planning document contains all required sections
- scientific question requirements are explicit
- scope boundaries are explicit
- dataset inclusion/exclusion criteria are explicit
- manual gates are explicit
- evidence requirements are explicit
- success/failure criteria are explicit
- stop conditions are explicit
- run-log requirements are explicit
- result-package requirements are explicit
- execution remains separately authorized
- runtime remains unauthorized
- no external data or network access occurs
- documentation-only tests pass
- no whitelist-external file changes

Completion of Phase 2.1 does not authorize Scientific Pilot execution, runtime
implementation, external data access, or dataset download.
