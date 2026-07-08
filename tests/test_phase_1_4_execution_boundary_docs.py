from pathlib import Path


def test_phase_1_4_controlled_execution_boundary_doc_exists() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-4-controlled-execution-boundary.md"

    assert doc_path.exists()


def test_phase_1_4_controlled_execution_boundary_terms_are_documented() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-4-controlled-execution-boundary.md"
    text = doc_path.read_text(encoding="utf-8").lower()

    required_terms = (
        "controlled execution boundary",
        "dry-run",
        "mock",
        "real geo download",
        "snakemake execution",
        "real coze call",
        "no secrets",
        "explicit opt-in",
        "operator checklist",
        "external network call",
        "audit/report-only mode",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
