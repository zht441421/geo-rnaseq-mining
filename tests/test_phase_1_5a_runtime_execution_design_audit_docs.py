from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-5a-runtime-execution-design-audit.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_5a_documents_design_audit_boundary() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5a",
        "design audit",
        "not implementation",
        "no real execution runner",
        "no real geo download",
        "no real rna-seq processing",
        "no snakemake execution",
        "no real coze call",
        "no external network",
        "no shell command execution",
        "no subprocess execution",
        "no artifacts/database",
        "no worker / scheduler / queue",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5a_documents_preconditions() -> None:
    text = _doc_text()

    required_terms = (
        "explicit opt-in",
        "operator approval",
        "validated input manifest",
        "output sandbox",
        "audit/report-only preview",
        "secrets outside repo",
        "controlled runner design",
        "worker / queue / scheduler design review before implementation",
        "persistence boundary design",
        "failure rollback / cleanup policy",
        "resource limits",
        "timeout policy",
        "provenance record",
        "local-only dry-run preview first",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5a_documents_runtime_boundary_layers() -> None:
    text = _doc_text()

    required_terms = (
        "request validation layer",
        "operator approval layer",
        "manifest validation layer",
        "execution planning layer",
        "sandbox preparation layer",
        "audit/report-only preview layer",
        "only then controlled runner layer",
        "does not implement any layer",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5a_documents_failure_protections() -> None:
    text = _doc_text()

    required_terms = (
        "deterministic rejection reasons",
        "no partial execution without approval",
        "no artifact write unless sandbox approved",
        "no network unless explicit future network boundary exists",
        "no secrets from repo",
        "timeout / cancellation design",
        "cleanup policy",
        "audit trail",
        "operator-visible report",
        "fail-closed behavior",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5a_documents_interface_questions_and_next_options() -> None:
    text = _doc_text()

    required_terms = (
        "execution request schema finalization",
        "manifest format",
        "allowed dataset accession policy",
        "whether geo download is ever allowed",
        "where sandbox output lives",
        "how artifacts are named",
        "how logs are handled",
        "how provenance is stored",
        "how operator approval is recorded",
        "how external network is isolated",
        "how secrets are provided outside repo",
        "how pipeline command is represented without shell injection risk",
        "how dry-run report becomes approval package",
        "runtime request schema design only",
        "dry-run execution plan preview only",
        "manifest schema docs/tests only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
