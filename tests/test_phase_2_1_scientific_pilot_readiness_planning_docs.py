from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_DOC = REPO_ROOT / "docs" / "phase-2-1-scientific-pilot-readiness-planning.md"
CURRENT_STATE = REPO_ROOT / "docs" / "CURRENT_STATE.md"
NEXT_TASK = REPO_ROOT / "docs" / "NEXT_TASK.md"
CHANGELOG = REPO_ROOT / "docs" / "CHANGELOG.md"
SUMMARY = REPO_ROOT / "PROJECT_SUMMARY_FOR_USER.md"
SYNC_SHA = "29d8a1644be4cfb72cfafe0a33814f3e3b447392"


def _read(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").lower().split())


def _assert_terms(text: str, terms: tuple[str, ...]) -> None:
    missing = [term for term in terms if term not in text]
    assert missing == []


def test_phase_2_1_document_exists_and_records_identity() -> None:
    assert PHASE_DOC.exists()
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "phase 2.1",
            "scientific pilot readiness planning",
            "docs/tests-only",
            "planning-only",
            "no-external-data-access",
            "no-scientific-execution",
            "no-runtime",
            SYNC_SHA,
        ),
    )


def test_phase_2_1_scope_and_authorization_boundaries() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "scientific pilot execution: not authorized",
            "runtime implementation: not authorized",
            "external data access: not authorized",
            "phase 2.1 does not authorize scientific pilot execution",
            "phase 2.1 does not authorize dataset search or download",
            "phase 2.1 does not authorize runtime implementation",
        ),
    )


def test_scientific_question_template_and_scope_boundary() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "pilot scientific question template",
            "biological context",
            "condition or phenotype",
            "comparison groups",
            "organism",
            "tissue or cell type",
            "assay type",
            "expected evidence",
            "excluded interpretations",
            "intended learning objective",
            "one narrow, testable scientific question",
            "pilot scope boundary",
            "one public study",
            "one primary comparison",
            "no multi-study meta-analysis",
            "no clinical decision support",
        ),
    )


def test_dataset_selection_criteria_and_candidate_record_schema() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "dataset-selection criteria",
            "required inclusion criteria",
            "public accessibility",
            "clear study metadata",
            "traceable accession identifiers",
            "no controlled-access human data",
            "required exclusion criteria",
            "controlled-access data",
            "ambiguous group labels",
            "single-sample comparison",
            "dataset candidate record schema",
            "candidate_id",
            "source_repository",
            "accession",
            "metadata_completeness",
            "replication_assessment",
            "recommendation must be human-reviewed",
        ),
    )


def test_manual_gates_and_evidence_package() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "manual review gates",
            "gate 1 - scientific question approval",
            "gate 2 - candidate dataset eligibility review",
            "gate 3 - metadata completeness review",
            "gate 4 - ethics/access/reuse review",
            "gate 5 - operational-size review",
            "gate 6 - analysis-plan review",
            "gate 7 - execution go/no-go",
            "no gate may automatically trigger execution",
            "evidence package requirements",
            "approved pilot question",
            "candidate dataset record",
            "sample/group table",
            "human go/no-go record",
        ),
    )


def test_analysis_plan_success_failure_and_stop_conditions() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "preliminary analysis-plan boundary",
            "input assumptions",
            "basic quality checks",
            "planned normalization approach",
            "multiple-testing handling",
            "do not select tools",
            "pilot success criteria",
            "statistical significance alone is not sufficient",
            "pilot failure criteria",
            "insufficient replication",
            "scientific question drift",
            "stop conditions",
            "pre-execution stop conditions",
            "future execution stop conditions",
            "these conditions are not implemented in phase 2.1",
        ),
    )


def test_run_log_result_package_interpretation_and_runtime_separation() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "run-log requirements",
            "run_id",
            "authorization_record",
            "commands_or_workflow_reference",
            "no run log is created in phase 2.1",
            "result package requirements",
            "executive scientific summary",
            "reviewer sign-off",
            "interpretation boundary",
            "does not establish clinical validity",
            "execution authorization boundary",
            "exact allowed commands or workflow",
            "relationship to runtime implementation",
            "scientific pilot planning is separate from runtime mvp",
            "runtime implementation still requires a separate go/no-go",
        ),
    )


def test_unresolved_items_explicit_no_go_and_completion_criteria() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "current unresolved items",
            "exact biological question",
            "exact candidate dataset",
            "exact accession list",
            "named reviewers and approver",
            "explicit no-go",
            "geo search",
            "sra download",
            "ncbi access",
            "entrez access",
            "external http requests",
            "snakemake",
            "runtime implementation",
            "scientific pilot execution",
            "completion criteria",
            "execution remains separately authorized",
            "runtime remains unauthorized",
        ),
    )


def test_governance_documents_reflect_phase_2_1_state() -> None:
    current = _read(CURRENT_STATE)
    next_task = _read(NEXT_TASK)
    summary = _read(SUMMARY)
    changelog = _read(CHANGELOG)
    _assert_terms(
        current,
        (
            "phase 2.1 scientific pilot readiness planning is the current phase",
            "scientific pilot readiness planning is in progress",
            "phase 1.10 project state synchronization: complete and synchronized",
            "scientific pilot execution: not authorized",
            "dataset search or dataset download",
            "runtime implementation",
            "no tag at head",
            SYNC_SHA,
        ),
    )
    _assert_terms(
        next_task,
        (
            "scientific pilot candidate dataset review and execution go/no-go preparation",
            "review/planning-only",
            "separate network-access authorization",
            "must not download geo/sra data",
            "must not",
            "execute the scientific pilot",
            "implement runtime behavior",
        ),
    )
    _assert_terms(
        summary,
        (
            "platform design baseline is complete",
            "phase 1.10 project state synchronization is complete and synchronized",
            "phase 2.1 scientific pilot readiness planning",
            "no dataset has been selected",
            "no data has been downloaded",
            "no pipeline has run",
            "scientific pilot execution is not authorized",
            "runtime implementation remains unauthorized",
        ),
    )
    _assert_terms(
        changelog,
        (
            "phase 2.1 scientific pilot readiness planning",
            "planning-only",
            "pilot scientific question template",
            "dataset-selection inclusion and exclusion criteria",
            "manual review gates",
            "evidence package requirements",
            "pilot success and failure criteria",
            "stop conditions",
            "run-log and result-package requirements",
            "no git commit or push during this implementation stage",
        ),
    )


def test_governance_documents_do_not_claim_execution_or_runtime_started() -> None:
    combined = "\n".join(
        _read(path) for path in (PHASE_DOC, CURRENT_STATE, NEXT_TASK, CHANGELOG, SUMMARY)
    )
    forbidden_claims = (
        "scientific pilot execution has started",
        "scientific analysis has started",
        "dataset selection is complete",
        "data download is complete",
        "pipeline execution is complete",
        "runtime controls are implemented",
        "runtime implementation is authorized",
    )
    assert [claim for claim in forbidden_claims if claim in combined] == []
