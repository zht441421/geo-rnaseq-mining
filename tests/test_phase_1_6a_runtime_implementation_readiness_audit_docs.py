from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = (
        repo_root
        / "docs"
        / "phase-1-6a-runtime-implementation-readiness-audit.md"
    )

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_6a_documents_scope_and_conclusion() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.6a",
        "runtime implementation readiness audit",
        "docs/tests only",
        "not implementation",
        "not ready for real runtime implementation",
        "real runtime implementation is not approved",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6a_documents_readiness_dimensions() -> None:
    text = _doc_text()

    required_terms = (
        "runtime request readiness",
        "manifest readiness",
        "dry-run preview readiness",
        "operator approval readiness",
        "sandbox readiness",
        "artifact persistence readiness",
        "database persistence readiness",
        "network boundary readiness",
        "secrets readiness",
        "threat model readiness",
        "resource and lifecycle readiness",
        "api integration readiness",
        "implementation approval status",
        "not approved",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6a_documents_missing_runtime_components() -> None:
    text = _doc_text()

    required_terms = (
        "runtime parser still missing by design",
        "runtime validator still missing by design",
        "manifest parser still missing by design",
        "manifest validator still missing by design",
        "execution planner still missing by design",
        "plan generator still missing by design",
        "approval system still missing by design",
        "approval api/database/ui/auth still missing by design",
        "runtime api handler integration does not exist",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6a_documents_boundary_gaps() -> None:
    text = _doc_text()

    required_terms = (
        "sandbox implementation does not exist",
        "artifact persistence design not implemented",
        "database write currently forbidden",
        "network currently forbidden",
        "secrets must remain outside repository",
        "command injection threat model required",
        "path traversal threat model required",
        "resource limit policy missing",
        "timeout policy missing",
        "cancellation policy missing",
        "cleanup policy missing",
        "rollback policy missing",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6a_documents_no_go_decisions() -> None:
    text = _doc_text()

    required_terms = (
        "real execution runner is not approved",
        "geo downloader is not approved",
        "snakemake wrapper is not approved",
        "real coze client is not approved",
        "artifact writer is not approved",
        "database persistence is not approved",
        "worker / queue / scheduler is not approved",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6a_documents_next_options() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.6b sandbox boundary design docs/tests only",
        "phase 1.6b artifact persistence boundary design docs/tests only",
        "phase 1.6b network boundary design docs/tests only",
        "phase 1.6b threat model docs/tests only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
