from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_DOC = REPO_ROOT / "docs" / "phase-1-10-project-state-synchronization.md"
CURRENT_STATE = REPO_ROOT / "docs" / "CURRENT_STATE.md"
NEXT_TASK = REPO_ROOT / "docs" / "NEXT_TASK.md"
CHANGELOG = REPO_ROOT / "docs" / "CHANGELOG.md"
SUMMARY = REPO_ROOT / "PROJECT_SUMMARY_FOR_USER.md"
SYNC_SHA = "93bd2016ee920aa29b0d786a70a701fe3e0f5fca"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def _assert_terms(text: str, terms: tuple[str, ...]) -> None:
    missing = [term for term in terms if term not in text]
    assert missing == []


def test_phase_1_10_document_exists_and_records_scope() -> None:
    assert PHASE_DOC.exists()
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "phase 1.10",
            "project state synchronization",
            "governance-only",
            "docs/tests-only",
            "no-runtime",
            "does not implement runtime behavior",
            SYNC_SHA,
        ),
    )


def test_phase_1_10_records_audit_conclusions_and_next_phase() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "scientific pilot readiness planning",
            "go with conditions",
            "runtime implementation",
            "`no`",
            "scientific pilot execution",
            "does not authorize",
            "runtime implementation",
            "next authorized theme",
            "must not download data or run a pipeline",
        ),
    )


def test_phase_1_10_records_conditions_dependencies_and_no_go() -> None:
    text = _read(PHASE_DOC)
    _assert_terms(
        text,
        (
            "keep the next phase planning-only",
            "separate human go/no-go",
            "do not treat design documentation as runtime enforcement",
            "request/manifest runtime parser and validator",
            "authoritative state store",
            "artifact validation enforcement",
            "retry, replay, and idempotency stores",
            "concurrency and stale-state enforcement",
            "explicit no-go",
            "state-machine behavior",
            "geo/sra access",
            "coze access",
            "snakemake",
        ),
    )


def test_current_state_reflects_synchronized_governance_state() -> None:
    text = _read(CURRENT_STATE)
    _assert_terms(
        text,
        (
            "phase 1.10 project state synchronization is the current task",
            "current branch: `123`",
            SYNC_SHA,
            "phase 1.9 task lifecycle and state machine boundary design: complete",
            "platform design baseline completion / go-no-go audit: complete",
            "scientific pilot readiness planning: `go with conditions`",
            "runtime implementation readiness: `no`",
            "scientific pilot readiness planning: not started",
            "scientific pilot execution: not authorized",
            "no tag at head",
        ),
    )
    assert "environment solve all-env dry-run coverage verification" not in text


def test_next_task_is_planning_only_and_prohibits_execution() -> None:
    text = _read(NEXT_TASK)
    _assert_terms(
        text,
        (
            "next stage: scientific pilot readiness planning",
            "scope: planning-only",
            "must not download data or run a pipeline",
            "scientific pilot execution requires a later separate human go/no-go",
            "external network services",
            "pipeline or snakemake execution",
            "queue, worker, database, scheduler, or runner",
            "artifacts or sandboxes",
            "credentials or secrets",
        ),
    )


def test_project_summary_reflects_platform_audit_conclusion() -> None:
    text = _read(SUMMARY)
    _assert_terms(
        text,
        (
            "phase 1.1-1.9 platform design baseline is complete",
            "phase 1.9 is synchronized locally and remotely",
            "platform design baseline completion / go-no-go audit is complete",
            "scientific pilot readiness planning: `go with conditions`",
            "runtime implementation readiness: `no`",
            "phase 1.10 project state synchronization",
            "next recommended phase is scientific pilot readiness planning",
            "that phase has not started",
            "scientific pilot execution is not authorized",
            "runtime implementation is not authorized",
        ),
    )


def test_changelog_includes_phase_1_10_entry() -> None:
    text = _read(CHANGELOG)
    _assert_terms(
        text,
        (
            "phase 1.10 project state synchronization",
            "platform design baseline completion / go-no-go audit",
            "go with conditions",
            "runtime readiness conclusion: `no`",
            "created `docs/phase-1-10-project-state-synchronization.md`",
            "created `tests/test_phase_1_10_project_state_synchronization_docs.py`",
            "no runtime implementation",
            "no scientific execution",
            "no network or external data access",
            "no commit or push",
        ),
    )


def test_governance_documents_do_not_claim_runtime_or_pilot_execution() -> None:
    combined = "\n".join(
        _read(path) for path in (PHASE_DOC, CURRENT_STATE, NEXT_TASK, CHANGELOG, SUMMARY)
    )
    forbidden_claims = (
        "runtime controls are implemented",
        "runtime implementation is authorized",
        "scientific pilot execution has started",
        "scientific pilot execution is authorized",
        "geo/sra download is authorized",
        "pipeline execution is authorized",
    )
    assert [claim for claim in forbidden_claims if claim in combined] == []
