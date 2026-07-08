from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-4-completion-baseline.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_4_completion_baseline_documents_completed_units() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.4a",
        "phase 1.4b",
        "phase 1.4c",
        "phase 1.4d",
        "phase 1.4e",
        "phase 1.4f",
        "controlled execution boundary",
        "dry-run execution request contract",
        "validation / rejection matrix",
        "pure dry-run validator skeleton",
        "api mock integration",
        "api rejection matrix hardening",
        "e2ffee42e6bf72e4a3e1a72445a357ed19924ad1",
        "current branch: `123`",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_4_completion_baseline_documents_safety_guarantees() -> None:
    text = _doc_text()

    required_terms = (
        "no real geo download",
        "no real rna-seq pipeline",
        "no snakemake execution",
        "no real coze call",
        "no external network",
        "no real artifacts",
        "no database",
        "no worker / scheduler",
        "no real execution runner",
        "no secrets in repo",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_4_completion_baseline_documents_current_contract() -> None:
    text = _doc_text()

    required_terms = (
        "deterministic rejection reasons",
        "accepted dry-run is not_started",
        "rejected dry-run is not_started and has no job_id",
        "ordinary mock job still returns job_id",
        "output_format",
        "zip",
        "unsafe dataset accession rejected",
        "command/shell/subprocess fields rejected",
        "secret/token/password/api_key fields rejected",
        "artifact/database/worker/scheduler intent rejected",
        "multiple rejection reasons returned together",
        "mock api returns validation report",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_4_completion_baseline_documents_operator_handoff() -> None:
    text = _doc_text()

    required_terms = (
        "operator handoff",
        "safe tests",
        "tests that must not be added without review",
        "violates the safety boundary",
        "explicit opt-in",
        "operator approval",
        "validated input manifest",
        "output sandbox",
        "audit/report-only preview",
        "no automatic network calls",
        "controlled runner / worker design",
        "persistence boundary",
        "secrets management outside repo",
        "phase 1.5 or phase 1.4h should be decided separately",
        "dry-run-only api preview",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
