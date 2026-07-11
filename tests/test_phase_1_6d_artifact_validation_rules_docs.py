from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-6d-artifact-validation-rules.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_6d_documents_scope_and_readiness() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.6d",
        "artifact validation rules docs/tests only",
        "not implementation",
        "not ready for artifact validator runtime implementation",
        "report-only until future runtime approval",
        "validation success does not authorize write",
        "validation success does not authorize execution",
        "approval record cannot bypass validation",
    )

    assert [term for term in required_terms if term not in text] == []


def test_phase_1_6d_documents_required_sections() -> None:
    text = _doc_text()

    required_terms = (
        "validation trust model",
        "fail-closed validation sequence",
        "artifact type allowlist",
        "filename safety rules",
        "extension and output-format consistency",
        "required metadata and relationship checks",
        "size boundary concepts",
        "sandbox and path assumptions",
        "overwrite policy",
        "network and hidden persistence prohibition",
        "validation result schema design",
        "rejection-code catalog",
        "auditability and redaction",
        "explicit no-go decision",
    )

    assert [term for term in required_terms if term not in text] == []


def test_phase_1_6d_documents_type_filename_and_format_rules() -> None:
    text = _doc_text()

    required_terms = (
        "narrow trusted allowlist",
        "filename only, never a path",
        "no user-controlled artifact paths",
        "path separators",
        "path traversal",
        "absolute local paths",
        "unc paths",
        "control characters and null bytes",
        "json",
        "markdown",
        "html",
        "zip remains not allowed",
        "extension must match the allowed `output_format`",
    )

    assert [term for term in required_terms if term not in text] == []


def test_phase_1_6d_documents_metadata_size_and_sandbox_rules() -> None:
    text = _doc_text()

    required_terms = (
        "artifact_id",
        "request_id",
        "manifest_id",
        "preview_id",
        "approval_record_id",
        "sandbox_id",
        "retention_policy_id",
        "cleanup_policy_id",
        "metadata_relationship_mismatch",
        "per-artifact size limit",
        "aggregate per-request size limit",
        "no file inspection",
        "no size computation",
        "approved sandbox root",
        "inside the approved sandbox root",
        "does not configure a sandbox root",
    )

    assert [term for term in required_terms if term not in text] == []


def test_phase_1_6d_documents_rejection_codes() -> None:
    text = _doc_text()

    required_terms = (
        "artifact_validation_not_approved",
        "invalid_artifact_type",
        "invalid_filename",
        "path_escape_attempt",
        "unsafe_extension",
        "missing_metadata",
        "size_limit_exceeded",
        "write_not_approved",
        "network_upload_not_allowed",
        "hidden_database_persistence_not_allowed",
        "execution_not_approved",
        "artifact_overwrite_not_allowed",
    )

    assert [term for term in required_terms if term not in text] == []


def test_phase_1_6d_documents_preview_is_side_effect_free() -> None:
    text = _doc_text()

    required_terms = (
        '"valid": false',
        '"report_only": true',
        '"files_inspected": false',
        '"paths_resolved": false',
        '"directories_created": false',
        '"files_written": false',
        '"artifacts_created": false',
        '"database_written": false',
        '"network_performed": false',
        '"write_approved": false',
        '"execution_approved": false',
        '"approved_for_implementation": false',
        "stable rejection-code ordering",
    )

    assert [term for term in required_terms if term not in text] == []


def test_phase_1_6d_documents_no_go_decisions() -> None:
    text = _doc_text()

    required_terms = (
        "validator runtime is not approved",
        "artifact writer is not approved",
        "artifact persistence is not approved",
        "artifact registry is not approved",
        "database persistence is not approved",
        "storage backend is not approved",
        "sandbox implementation is not approved",
        "filesystem inspection is not approved",
        "path resolver is not approved",
        "runtime api handler integration is not approved",
        "worker / queue / scheduler integration is not approved",
        "geo downloader is not approved",
        "snakemake wrapper is not approved",
        "real coze client is not approved",
        "do not directly enter real runtime implementation",
    )

    assert [term for term in required_terms if term not in text] == []
