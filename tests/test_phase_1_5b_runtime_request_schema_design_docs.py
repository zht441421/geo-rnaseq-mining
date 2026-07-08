from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-5b-runtime-request-schema-design.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_5b_documents_design_only_boundary() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5b",
        "schema design only",
        "not implementation",
        "no runtime parser",
        "no runtime validator",
        "no api handler integration",
        "no real execution runner",
        "no snakemake execution",
        "no real geo download",
        "no real coze call",
        "no external network",
        "no artifacts/database",
        "no worker / scheduler / queue",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5b_documents_required_fields() -> None:
    text = _doc_text()

    required_terms = (
        "mode",
        "request_id",
        "dataset_accession",
        "analysis_type",
        "output_format",
        "execution_intent",
        "operator_approval",
        "input_manifest",
        "sandbox",
        "audit",
        "safety_flags",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5b_documents_safety_defaults() -> None:
    text = _doc_text()

    required_terms = (
        "real_execution_requested false",
        "allow_network false",
        "allow_pipeline_execution false",
        "allow_snakemake false",
        "allow_real_coze_call false",
        "operator approval approved false",
        "report_only true",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5b_documents_allowed_placeholders() -> None:
    text = _doc_text()

    required_terms = (
        "gse123456",
        "rnaseq_placeholder",
        "json / markdown / html",
        "zip not allowed",
        "request_id",
        "path / shell fragment",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5b_documents_forbidden_schema_content() -> None:
    text = _doc_text()

    required_terms = (
        "command / shell / subprocess not allowed",
        "secret / token / password / api_key not allowed",
        "absolute local paths not allowed",
        "artifact output outside sandbox not allowed",
        "database connection string not allowed",
        "path traversal not allowed",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5b_documents_next_phase_options() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5c manifest schema docs/tests only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
