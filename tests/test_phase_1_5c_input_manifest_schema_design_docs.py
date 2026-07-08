from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-5c-input-manifest-schema-design.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_5c_documents_design_only_boundary() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5c",
        "manifest schema docs/tests only",
        "not implementation",
        "no manifest parser",
        "no manifest validator",
        "no json schema file",
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


def test_phase_1_5c_documents_required_top_level_fields() -> None:
    text = _doc_text()

    required_terms = (
        "manifest_id",
        "manifest_version",
        "dataset",
        "samples",
        "analysis",
        "inputs",
        "outputs",
        "provenance",
        "safety",
        "audit",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5c_documents_dataset_section() -> None:
    text = _doc_text()

    required_terms = (
        "dataset_accession",
        "geo_placeholder_not_downloaded",
        "no automatic geo download",
        "no external network",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5c_documents_samples_section() -> None:
    text = _doc_text()

    required_terms = (
        "metadata-only placeholder",
        "no fastq / bam / count matrix real paths",
        "no absolute local paths",
        "no path traversal",
        "no shell fragments",
        "no unvalidated urls",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5c_documents_analysis_section() -> None:
    text = _doc_text()

    required_terms = (
        "rnaseq_placeholder",
        "no deseq2 / edger / salmon / star / featurecounts",
        "no snakemake execution",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5c_documents_inputs_outputs_sections() -> None:
    text = _doc_text()

    required_terms = (
        "output_format json / markdown / html",
        "zip not allowed",
        "write_artifacts false",
        "report_only true",
        "command",
        "shell",
        "subprocess",
        "snakemake command",
        "absolute local paths",
        "external urls",
        "secrets",
        "token",
        "password",
        "api_key",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5c_documents_safety_and_audit_flags() -> None:
    text = _doc_text()

    required_terms = (
        "allow_network false",
        "allow_pipeline_execution false",
        "allow_snakemake false",
        "allow_real_coze_call false",
        "allow_artifact_write false",
        "allow_database_write false",
        "allow_background_execution false",
        "operator_visible true",
        "approval_required_for_future_runtime true",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5c_documents_next_phase_options() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5d dry-run execution plan preview design only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
