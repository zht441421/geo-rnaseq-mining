from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-4b-dry-run-execution-request-contract.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_4b_dry_run_request_contract_terms_are_documented() -> None:
    text = _doc_text()

    required_terms = (
        "dry-run execution request contract",
        '"mode": "dry_run"',
        '"allow_network": false',
        '"allow_pipeline_execution": false',
        '"allow_snakemake": false',
        '"allow_real_coze_call": false',
        '"operator_approved": false',
        "explicit opt-in flag",
        "operator confirmation",
        "validated input manifest",
        "output sandbox directory",
        "audit/report-only preview",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_4b_dry_run_contract_rejects_real_execution_intent() -> None:
    text = _doc_text()

    rejected_terms = (
        "real execution is forbidden by default",
        '"mode": "execute"',
        '"allow_pipeline_execution": true',
        '"allow_network": true',
        '"allow_snakemake": true',
        '"allow_real_coze_call": true',
        "documentation-only negative cases",
        "must not be executed",
    )

    missing_terms = [term for term in rejected_terms if term not in text]

    assert missing_terms == []
