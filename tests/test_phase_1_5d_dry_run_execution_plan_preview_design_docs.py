from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = (
        repo_root
        / "docs"
        / "phase-1-5d-dry-run-execution-plan-preview-design.md"
    )

    assert doc_path.exists()
    return doc_path.read_text(encoding="utf-8").lower()


def test_phase_1_5d_documents_design_only_boundary() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5d",
        "dry-run execution plan preview design only",
        "not implementation",
        "no execution planner",
        "no runtime planner",
        "no plan generator",
        "no api handler integration",
        "no real execution runner",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5d_documents_required_preview_fields() -> None:
    text = _doc_text()

    required_terms = (
        "preview_id",
        "request_id",
        "manifest_id",
        "mode",
        "status",
        "plan_summary",
        "planned_steps",
        "blocked_actions",
        "safety_assessment",
        "operator_review",
        "sandbox_preview",
        "audit_report",
        "next_allowed_actions",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5d_documents_preview_defaults() -> None:
    text = _doc_text()

    required_terms = (
        "mode dry_run",
        "status preview_only / blocked / rejected",
        "no execution_started true",
        "no artifact_created true",
        "no network_performed true",
        "no database_written true",
        "no worker_started true",
        "report_only true",
        "approval_required true",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5d_documents_planned_steps() -> None:
    text = _doc_text()

    required_terms = (
        "validate_runtime_request",
        "validate_input_manifest",
        "assess_safety_flags",
        "prepare_output_sandbox_placeholder",
        "generate_operator_visible_report",
        "wait_for_future_operator_approval",
        "planned steps are descriptive only",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5d_documents_blocked_actions() -> None:
    text = _doc_text()

    required_terms = (
        "real_geo_download",
        "real_rnaseq_pipeline",
        "snakemake_execution",
        "real_coze_call",
        "external_network_access",
        "shell_command_execution",
        "subprocess_execution",
        "artifact_write",
        "database_write",
        "worker_start",
        "scheduler_start",
        "queue_enqueue",
        "long_running_server",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5d_documents_safety_assessment() -> None:
    text = _doc_text()

    required_terms = (
        "allow_network false",
        "allow_pipeline_execution false",
        "allow_snakemake false",
        "allow_real_coze_call false",
        "allow_artifact_write false",
        "allow_database_write false",
        "allow_background_execution false",
        "fail_closed true",
        "deterministic_rejection_reasons true",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5d_documents_operator_review_and_sandbox() -> None:
    text = _doc_text()

    required_terms = (
        "approval_required true",
        "approved false",
        "operator_visible true",
        "no automatic escalation to execution",
        "sandbox_path not a real path",
        "directories_created false",
        "files_written false",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5d_documents_audit_report() -> None:
    text = _doc_text()

    required_terms = (
        "report_only true",
        "include_blocked_actions true",
        "include_rejection_reasons true",
        "database_persisted false",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []


def test_phase_1_5d_documents_next_phase_options() -> None:
    text = _doc_text()

    required_terms = (
        "phase 1.5e manifest validation rules docs/tests only",
        "do not directly enter real execution implementation",
    )

    missing_terms = [term for term in required_terms if term not in text]

    assert missing_terms == []
