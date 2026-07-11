from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = (
        repo_root
        / "docs"
        / "phase-1-6c-artifact-persistence-boundary-design.md"
    )

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_6c_documents_scope_and_no_go_decision() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.6c",
        "artifact persistence boundary design",
        "docs/tests only",
        "not implementation",
        "not ready for artifact persistence implementation",
        "artifact writer is not approved",
        "artifact persistence is not approved",
        "artifact directory creation is not approved",
        "artifact file creation is not approved",
        "artifact registry is not approved",
        "database persistence is not approved",
        "sandbox implementation is not approved",
        "runtime execution is not approved",
        "runtime api handler integration is not approved",
        "worker / queue / scheduler is not approved",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6c_documents_persistence_principles() -> None:
    text = _doc_text()

    required_terms = (
        "fail-closed by default",
        "report-only",
        "no artifact writes by default",
        "write_artifacts must remain false",
        "accepted dry-run does not permit artifact creation",
        "accepted approval record does not permit artifact creation",
        "no writing outside approved sandbox root",
        "no artifact overwrite by default",
        "no user-controlled artifact paths",
        "no absolute local paths",
        "no path traversal",
        "no symlink traversal",
        "no hidden database persistence",
        "no hidden network upload",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6c_documents_identity_naming_and_lifecycle_rules() -> None:
    text = _doc_text()

    required_terms = (
        "artifact_id_required",
        "unsafe_artifact_id",
        "unsupported_artifact_type",
        "unsafe_artifact_filename",
        "unsupported_output_format",
        "zip_output_not_allowed",
        "artifact format allowlist is future policy only",
        "artifact_overwrite_not_allowed",
        "retention_policy_required",
        "cleanup_policy_required",
        "rollback_policy_required",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6c_documents_privacy_and_storage_boundaries() -> None:
    text = _doc_text()

    required_terms = (
        "secret_in_artifact_not_allowed",
        "token_in_artifact_not_allowed",
        "password_in_artifact_not_allowed",
        "api_key_in_artifact_not_allowed",
        "real_credentials_in_artifact_not_allowed",
        "local_path_leak_not_allowed",
        "network_upload_not_allowed",
        "real_coze_upload_not_allowed",
        "no secrets or credentials in artifact metadata",
        "no local path leakage",
        "artifact storage root must be derived from approved sandbox root",
        "artifact storage root must not come from request body",
        "artifact storage root must not come from manifest",
        "artifact storage root must not be repository root",
        "artifact storage root must be outside source code tree",
        "artifact final path must remain inside approved sandbox root",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6c_documents_audit_metadata_and_no_inspection() -> None:
    text = _doc_text()

    required_terms = (
        "artifact audit metadata",
        "artifact_id",
        "request_id",
        "manifest_id",
        "preview_id",
        "approval_record_id",
        "sandbox_id",
        "checksum_placeholder",
        "audit metadata is documentation-only",
        "no checksum calculation",
        "no checksum computation in this phase",
        "no database write in this phase",
        "no file inspection",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6c_documents_preview_schema_and_next_options() -> None:
    text = _doc_text()

    required_terms = (
        "directories_created\": false",
        "files_written\": false",
        "artifacts_created\": false",
        "database_written\": false",
        "network_performed\": false",
        "approved_for_implementation\": false",
        "all write and execution flags are false in the preview schema",
        "artifact_persistence_not_approved",
        "artifact_write_not_allowed",
        "phase 1.6d network boundary design docs/tests only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
