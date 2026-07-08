from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-5e-manifest-validation-rules-design.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_5e_documents_design_only_boundary() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5e",
        "manifest validation rules docs/tests only",
        "not implementation",
        "no manifest validator",
        "no manifest parser",
        "no runtime validator",
        "no json schema file",
        "no api handler integration",
        "no real execution runner",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5e_documents_required_manifest_sections() -> None:
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
        "manifest_missing_required_field",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5e_documents_identifier_and_dataset_rejections() -> None:
    text = _doc_text()

    required_terms = (
        "unsafe_manifest_id",
        "unsafe_request_id",
        "unsafe_sample_id",
        "unsafe_sandbox_id",
        "path_traversal_not_allowed",
        "absolute_local_path_not_allowed",
        "shell_fragment_not_allowed",
        "dataset_accession_required",
        "unsafe_dataset_accession",
        "geo_download_not_allowed",
        "network_access_not_allowed",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5e_documents_samples_analysis_rejections() -> None:
    text = _doc_text()

    required_terms = (
        "samples_required",
        "real_fastq_path_not_allowed",
        "real_bam_path_not_allowed",
        "real_count_matrix_path_not_allowed",
        "unsupported_analysis_type",
        "real_rnaseq_pipeline_not_allowed",
        "deseq2_execution_not_allowed",
        "edger_execution_not_allowed",
        "salmon_execution_not_allowed",
        "star_execution_not_allowed",
        "featurecounts_execution_not_allowed",
        "snakemake_not_allowed",
        "pipeline_execution_not_allowed",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5e_documents_inputs_rejections() -> None:
    text = _doc_text()

    required_terms = (
        "inputs_must_be_placeholder_only",
        "command_field_not_allowed",
        "shell_field_not_allowed",
        "subprocess_field_not_allowed",
        "secret_field_not_allowed",
        "token_field_not_allowed",
        "password_field_not_allowed",
        "api_key_field_not_allowed",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5e_documents_outputs_audit_rejections() -> None:
    text = _doc_text()

    required_terms = (
        "unsupported_output_format",
        "zip_output_not_allowed",
        "artifact_write_not_allowed",
        "report_only_required",
        "database_write_not_allowed",
        "operator_visible_report_required",
        "automatic_execution_escalation_not_allowed",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5e_documents_deterministic_rejection_behavior() -> None:
    text = _doc_text()

    required_terms = (
        "deterministic rejection reasons",
        "stable rejection order",
        "accepted_for_preview_only",
        "execution not_started",
        "artifacts_created false",
        "network_performed false",
        "database_written false",
        "accepted dry-run manifest does not mean real execution",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5e_documents_next_phase_options() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5f operator approval record design only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
