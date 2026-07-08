from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = repo_root / "docs" / "phase-1-5f-operator-approval-record-design.md"

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_5f_documents_design_only_boundary() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5f",
        "operator approval record design only",
        "not implementation",
        "no approval system",
        "no approval api",
        "no approval database",
        "no approval ui",
        "no authentication",
        "no authorization",
        "no api handler integration",
        "no real execution runner",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5f_documents_required_fields() -> None:
    text = _doc_text()

    required_terms = (
        "approval_record_id",
        "request_id",
        "manifest_id",
        "preview_id",
        "operator_id",
        "operator_role",
        "decision",
        "decision_reason",
        "reviewed_at_placeholder",
        "reviewed_preview_version",
        "reviewed_manifest_version",
        "reviewed_rejection_reasons",
        "approved_scope",
        "denied_scope",
        "safety_overrides",
        "expiration",
        "revocation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5f_documents_decision_values_and_scope() -> None:
    text = _doc_text()

    required_terms = (
        "approved_for_future_runtime_review",
        "rejected",
        "needs_revision",
        "not execute_now",
        "not run_pipeline",
        "safety_overrides must be empty",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5f_documents_safety_override_rejections() -> None:
    text = _doc_text()

    required_terms = (
        "approval_cannot_enable_network",
        "approval_cannot_enable_pipeline_execution",
        "approval_cannot_enable_snakemake",
        "approval_cannot_enable_real_coze_call",
        "approval_cannot_enable_artifact_write",
        "approval_cannot_enable_database_write",
        "approval_cannot_enable_background_execution",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5f_documents_audit_revocation_expiration() -> None:
    text = _doc_text()

    required_terms = (
        "operator_visible",
        "report_only",
        "no database persistence",
        "no external audit service",
        "revoked approval cannot be used",
        "expired approval cannot be used",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5f_documents_no_automatic_escalation() -> None:
    text = _doc_text()

    required_terms = (
        "no automatic escalation to execution",
        "no enqueue job",
        "no schedule job",
        "no worker",
        "no geo download",
        "no snakemake execution",
        "no rna-seq pipeline",
        "no real coze call",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5f_documents_forbidden_content() -> None:
    text = _doc_text()

    required_terms = (
        "secret / token / password / api_key not allowed",
        "command / shell / subprocess not allowed",
        "skip_validation not allowed",
        "disable_safety_checks not allowed",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5f_documents_safe_outcomes() -> None:
    text = _doc_text()

    required_terms = (
        "accepted_for_future_runtime_review_only",
        "execution not_started",
        "network_performed false",
        "artifacts_created false",
        "database_written false",
        "worker_started false",
        "safety_overrides_applied false",
        "accepted approval record does not mean real execution",
        "accepted approval record does not bypass future validation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5f_documents_next_phase_options() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5g dry-run preview test fixtures docs only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
