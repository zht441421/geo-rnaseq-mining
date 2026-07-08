from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-5-completion-baseline.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_5_completion_baseline_documents_boundary() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5 completion baseline",
        "operator handoff",
        "design-only safety baseline",
        "not implementation",
        "no runtime implementation",
        "no parser / validator implementation",
        "no api handler integration",
        "no approval system",
        "no planner / runner",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5_completion_baseline_summarizes_completed_units() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5a runtime execution design audit",
        "phase 1.5b runtime request schema design",
        "phase 1.5c input manifest schema design",
        "phase 1.5d dry-run execution plan preview design",
        "phase 1.5e manifest validation rules design",
        "phase 1.5f operator approval record design",
        "5fb0b32",
        "244043e",
        "50227fb",
        "3c42f26",
        "b530098",
        "19d6965",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5_completion_baseline_documents_no_runtime_systems() -> None:
    text = _doc_text()

    required_terms = (
        "no real rna-seq pipeline execution",
        "no snakemake execution",
        "no geo download",
        "no real coze call",
        "no external network access",
        "no artifacts/database",
        "no worker / queue / scheduler",
        "no json schema file",
        "no pydantic model",
        "no approval api",
        "no approval database",
        "no authentication",
        "no authorization",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5_completion_baseline_documents_future_entry_criteria() -> None:
    text = _doc_text()

    required_terms = (
        "explicit runtime opt-in",
        "reviewed runtime request schema",
        "reviewed manifest schema",
        "reviewed manifest validation rules",
        "reviewed dry-run preview",
        "reviewed operator approval record",
        "safety flags",
        "safety flags cannot be overridden by approval",
        "sandbox design review",
        "artifact persistence design review",
        "database persistence design review",
        "network boundary design review",
        "secrets management outside repository",
        "command injection threat model",
        "path traversal threat model",
        "resource limit policy",
        "timeout policy",
        "cancellation policy",
        "cleanup policy",
        "audit trail policy",
        "rollback policy",
        "no automatic escalation from approval to execution",
        "fail-closed behavior",
        "dry-run preview remains mandatory before runtime",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5_completion_baseline_documents_forbidden_next_steps() -> None:
    text = _doc_text()

    required_terms = (
        "real execution runner",
        "geo downloader",
        "snakemake wrapper",
        "real coze client",
        "database persistence",
        "artifact writer",
        "worker / queue / scheduler",
        "approval api",
        "approval database",
        "authentication / authorization implementation",
        "api handler integration for runtime",
        "pipeline execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5_completion_baseline_documents_next_options() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.6a runtime implementation readiness audit docs/tests only",
        "phase 1.6a sandbox boundary design docs/tests only",
        "phase 1.6a artifact persistence boundary design docs/tests only",
        "phase 1.6a network boundary design docs/tests only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
