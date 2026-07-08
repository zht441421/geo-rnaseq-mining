from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-6b-sandbox-boundary-design.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_6b_documents_scope_and_no_go_decision() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.6b",
        "sandbox boundary design",
        "docs/tests only",
        "not implementation",
        "not ready for sandbox implementation",
        "sandbox implementation is not approved",
        "sandbox directory creation is not approved",
        "artifact writer is not approved",
        "artifact persistence is not approved",
        "database persistence is not approved",
        "network boundary implementation is not approved",
        "runtime execution is not approved",
        "runtime api handler integration is not approved",
        "worker / queue / scheduler is not approved",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6b_documents_boundary_principles() -> None:
    text = _doc_text()

    required_terms = (
        "fail-closed by default",
        "report-only",
        "no implicit filesystem writes",
        "no absolute local paths",
        "no path traversal",
        "no user-controlled output root",
        "no writing outside approved sandbox root",
        "no artifact overwrite by default",
        "no symlink traversal",
        "no hidden network side effects",
        "no database persistence side effects",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6b_documents_sandbox_id_rules() -> None:
    text = _doc_text()

    required_terms = (
        "sandbox_id required before any future artifact write",
        "sandbox_id must be safe identifier only",
        "sandbox_id",
        "sandbox_id_required",
        "unsafe_sandbox_id",
        "path_separator_not_allowed",
        "drive_letter_not_allowed",
        "colon_not_allowed",
        "path_traversal_not_allowed",
        "absolute_local_path_not_allowed",
        "output_path_outside_sandbox_not_allowed",
        "symlink_traversal_not_allowed",
        "unc_path_not_allowed",
        "control_character_not_allowed",
        "null_byte_not_allowed",
        "artifact_overwrite_not_allowed",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6b_documents_root_policy_and_enforcement() -> None:
    text = _doc_text()

    required_terms = (
        "sandbox root must be configured by trusted operator configuration",
        "sandbox root must not come from request body",
        "sandbox root must not come from manifest",
        "sandbox root must not be repository root",
        "sandbox root must be outside source code tree",
        "normalize requested sandbox path",
        "verify final output path stays inside approved sandbox root",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6b_documents_write_cleanup_and_audit_boundaries() -> None:
    text = _doc_text()

    required_terms = (
        "write_artifacts must remain false",
        "accepted dry-run does not permit writes",
        "accepted approval record does not permit writes",
        "cleanup policy required",
        "rollback policy required",
        "audit trail required",
        "operator-visible sandbox report required",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_6b_documents_preview_schema_and_next_options() -> None:
    text = _doc_text()

    required_terms = (
        "directories_created\": false",
        "files_written\": false",
        "artifacts_created\": false",
        "database_written\": false",
        "network_performed\": false",
        "approved_for_implementation\": false",
        "sandbox_implementation_not_approved",
        "artifact_write_not_allowed",
        "phase 1.6c artifact persistence boundary design docs/tests only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
