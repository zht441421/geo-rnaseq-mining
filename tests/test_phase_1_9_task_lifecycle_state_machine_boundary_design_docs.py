from pathlib import Path


def _doc_text() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    doc_path = (
        repo_root
        / "docs"
        / "phase-1-9-task-lifecycle-state-machine-boundary-design.md"
    )
    return doc_path.read_text(encoding="utf-8").lower()


def _assert_terms(text: str, required_terms: tuple[str, ...]) -> None:
    assert [term for term in required_terms if term not in text] == []


def test_phase_1_9_scope_and_mock_compatibility() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "phase 1.9",
            "platform design baseline convergence",
            "docs/tests-only",
            "design-only",
            "report-only",
            "not runtime lifecycle implementation",
            "not ready for runtime lifecycle implementation",
            "design controls are not enforced runtime controls",
            "a documented transition does not create an executable transition",
            "a status field is not a capability token",
            "queued -> validating -> ready -> running -> summarizing -> completed",
            "in-memory mock and frontend prototype",
            "is not the future platform lifecycle contract",
            "existing mock state machine remains unchanged",
            "validating | validated",
            "ready | approved / planned / queued",
            "completed | succeeded / artifact_validation_failed / cleanup failure",
            "cancelled | cancelling / cancelled after cleanup",
        ),
    )


def test_phase_1_9_state_vocabulary_and_classification() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "state vocabulary and classification",
            "received",
            "rejected",
            "validated",
            "awaiting_review",
            "approved",
            "denied",
            "planned",
            "queued",
            "running",
            "cancelling",
            "cancelled",
            "failed",
            "succeeded",
            "artifact_validation_failed",
            "expired",
            "pre-execution states",
            "active states",
            "terminal states",
            "terminal state classification does not authorize automatic deletion",
        ),
    )


def test_phase_1_9_allowed_and_succeeded_transitions() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "allowed-transition matrix",
            "received -> validated -> awaiting_review -> approved -> planned -> queued -> running -> succeeded",
            "received | rejected",
            "validated | awaiting_review",
            "awaiting_review | approved",
            "approved | planned",
            "planned | queued",
            "queued | running",
            "queued | cancelling",
            "running | artifact_validation_failed",
            "running | succeeded",
            "cancelling | cancelled",
            "cancelling | failed",
            "succeeded gate",
            "execution result is complete",
            "required artifact validation passed",
            "no pending cancellation exists",
            "required cleanup completed",
            "approval remains valid and fresh",
            "execution completion alone must not equal succeeded",
        ),
    )


def test_phase_1_9_blocked_transitions_and_gates() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "blocked-transition matrix",
            "received -> approved",
            "received -> queued",
            "received -> running",
            "validated -> running",
            "awaiting_review -> planned",
            "approved -> running",
            "planned -> running",
            "denied -> approved",
            "rejected -> validated",
            "expired -> approved",
            "succeeded -> running",
            "failed -> running",
            "cancelled -> running",
            "artifact_validation_failed -> succeeded",
            "skipping validation",
            "skipping operator approval",
            "bypassing gates by directly modifying a status field",
            "preview is report-only and does not authorize execution",
            "validation success does not authorize execution",
            "approval does not replace validation",
            "approval does not authorize secret disclosure",
            "approval does not authorize network access",
            "approval does not authorize database access",
            "approval does not authorize artifact writing",
            "approved does not mean planned, queued, or running",
            "approval must bind to the same request, manifest, preview, plan, and policy",
            "state values are not authorization capabilities",
        ),
    )


def test_phase_1_9_rejection_vocabulary_and_cancellation() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "validation_required",
            "operator_approval_required",
            "approval_denied",
            "approval_expired",
            "approval_stale",
            "approval_replay_not_allowed",
            "relationship_mismatch",
            "plan_required",
            "queue_not_approved",
            "execution_not_approved",
            "state_transition_not_allowed",
            "terminal_state_restart_not_allowed",
            "cancellation_requested",
            "cancellation_requested` is an event, not necessarily a state",
            "cancelling` means stop and cleanup are incomplete",
            "worker lease released where applicable",
            "failure_category = cleanup_failed",
            "cancellation must not silently produce",
            "must not automatically delete artifacts",
            "phase 1.9 sends no cancellation signal",
        ),
    )


def test_phase_1_9_failure_retry_and_terminal_rules() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "failure taxonomy",
            "validation_failed",
            "approval_denied",
            "planning_failed",
            "queue_failed",
            "runtime_failed",
            "artifact_validation_failed",
            "cancellation_failed",
            "cleanup_failed",
            "policy_expired",
            "relationship_mismatch",
            "concurrency_conflict",
            "retry is an explicit, human-visible new decision",
            "retry creates a new task_id",
            "the new task begins at received",
            "retry_of_task_id",
            "automatic infinite retry is prohibited",
            "expired approval cannot be reused",
            "terminal states cannot transition back to running",
            "terminal history cannot be overwritten",
            "a new attempt requires a new task identity",
            "cancelled must not be used when cleanup failed",
            "failed must retain a failure category",
        ),
    )


def test_phase_1_9_idempotency_replay_and_concurrency() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "idempotency and duplicate requests",
            "an idempotency key binds to canonical request identity",
            "same key plus same canonical request may return the same task reference",
            "same key plus different payload must be rejected",
            "idempotency does not mean retry",
            "idempotency does not permit approval reuse",
            "no idempotency store is implemented",
            "replay and stale approval",
            "stale approval must be rejected",
            "must not be replayed",
            "terminal-task request replay must not restart the original task",
            "approval freshness must be checked before execution",
            "no replay store",
            "concurrency and toctou",
            "expected_previous_state",
            "expected_version",
            "next_state",
            "state_version_conflict",
            "stale_state_update",
            "concurrent_transition_not_allowed",
            "concurrent updates must fail closed",
            "stale state must not overwrite a newer state",
            "no lock, database transaction, compare-and-swap",
        ),
    )


def test_phase_1_9_authoritative_state_and_audit() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "single authoritative state source",
            "audit event",
            "api response",
            "queue message",
            "worker local state",
            "client-side state",
            "preview output",
            "approval record",
            "transition_id",
            "task_id",
            "actor_type",
            "actor_id_placeholder",
            "occurred_at_placeholder",
            "previous_state",
            "next_state",
            "reason_code",
            "request_id",
            "manifest_id",
            "preview_id",
            "plan_id",
            "approval_record_id",
            "policy_version",
            "expected_state_version",
            "resulting_state_version",
            "audit design does not equal audit persistence implementation",
            "historical transitions must not be overwritten, deleted, or silently rewritten",
        ),
    )


def test_phase_1_9_report_only_schema_and_dependencies() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "report-only lifecycle assessment schema",
            "not a json schema",
            "pydantic model",
            "runtime object",
            "database row",
            "api response",
            "queue message",
            '"states_documented": true',
            '"allowed_transitions_documented": true',
            '"blocked_transitions_documented": true',
            '"database_written": false',
            '"queue_created": false',
            '"worker_started": false',
            '"scheduler_started": false',
            '"cancellation_signal_sent": false',
            '"retry_performed": false',
            '"audit_persisted": false',
            '"runtime_executed": false',
            '"approved_for_implementation": false',
            '"not_ready_for_runtime_lifecycle_implementation"',
            "database state store",
            "cancellation mechanism",
            "retry policy implementation",
            "replay protection store",
            "artifact validation enforcement",
            "sandbox enforcement",
            "network policy enforcement",
        ),
    )


def test_phase_1_9_no_go_and_scientific_pilot_boundary() -> None:
    text = _doc_text()
    _assert_terms(
        text,
        (
            "explicit no-go decision",
            "execution runner",
            "cancellation signal",
            "retry engine",
            "idempotency store",
            "replay store",
            "concurrency lock",
            "audit persistence",
            "background service",
            "runtime api handler",
            "real state-machine integration",
            "artifact writer",
            "artifact registry",
            "network client",
            "secret system",
            "authentication or authorization",
            "real task execution",
            "pipeline execution",
            "snakemake execution",
            "geo/sra download",
            "coze integration",
            "existing mock state machine remains unchanged",
            "scientific pilot relationship",
            "consistent pilot request identity",
            "explicit human review gate",
            "phase 1.9 does not start the scientific pilot",
            "does not convert a pilot into a queue or worker task",
            "scientific pilot execution requires a separate plan and explicit authorization",
            "next recommended stage is platform design baseline completion / go-no-go audit",
            "scientific pilot readiness planning may follow only after that audit",
        ),
    )
