"""Job status machine for the Phase 1 API mock."""

from __future__ import annotations

from enum import Enum


class JobStateError(ValueError):
    """Raised when a requested job status transition is not allowed."""


class JobStatus(str, Enum):
    QUEUED = "queued"
    VALIDATING = "validating"
    READY = "ready"
    RUNNING = "running"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = frozenset(
    {
        JobStatus.COMPLETED,
        JobStatus.FAILED,
        JobStatus.CANCELLED,
    }
)

CANCELLABLE_STATUSES = frozenset(
    {
        JobStatus.QUEUED,
        JobStatus.VALIDATING,
        JobStatus.READY,
        JobStatus.RUNNING,
        JobStatus.SUMMARIZING,
    }
)

ALLOWED_TRANSITIONS = {
    JobStatus.QUEUED: frozenset(
        {JobStatus.VALIDATING, JobStatus.FAILED, JobStatus.CANCELLED}
    ),
    JobStatus.VALIDATING: frozenset(
        {JobStatus.READY, JobStatus.FAILED, JobStatus.CANCELLED}
    ),
    JobStatus.READY: frozenset(
        {JobStatus.RUNNING, JobStatus.FAILED, JobStatus.CANCELLED}
    ),
    JobStatus.RUNNING: frozenset(
        {JobStatus.SUMMARIZING, JobStatus.FAILED, JobStatus.CANCELLED}
    ),
    JobStatus.SUMMARIZING: frozenset(
        {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}
    ),
    JobStatus.COMPLETED: frozenset(),
    JobStatus.FAILED: frozenset(),
    JobStatus.CANCELLED: frozenset(),
}


def require_transition(current: JobStatus, next_status: JobStatus) -> None:
    if next_status not in ALLOWED_TRANSITIONS[current]:
        raise JobStateError(
            f"cannot transition job from {current.value} to {next_status.value}"
        )


def can_cancel(status: JobStatus) -> bool:
    return status in CANCELLABLE_STATUSES
