"""In-memory API mock for productization Phase 1.

This service exposes method-level equivalents of the planned API endpoints:

- POST /jobs -> submit_job
- GET /jobs/{job_id} -> get_job
- GET /jobs/{job_id}/result -> get_job_result
- POST /jobs/{job_id}/cancel -> cancel_job

It never invokes Snakemake, Conda, shell commands, network calls, or external
services. State changes are deterministic in-memory operations for contract
testing and Coze API shape validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from .job_schema import JobSubmitRequest
from .state_machine import JobStateError, JobStatus, can_cancel, require_transition


class JobNotFoundError(KeyError):
    """Raised when a requested mock job does not exist."""


@dataclass
class JobRecord:
    job_id: str
    request: JobSubmitRequest
    status: JobStatus = JobStatus.QUEUED
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())
    events: list[dict[str, str]] = field(default_factory=list)

    def to_status_response(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "request": self.request.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "events": list(self.events),
            "mock": True,
            "message": _status_message(self.status),
        }


class MockJobService:
    """Small in-memory service used to validate API contracts.

    The service is intentionally process-local and non-persistent. It is not a
    worker, scheduler, queue, or production execution layer.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._counter = 0

    def submit_job(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        request = JobSubmitRequest.from_mapping(payload)
        self._counter += 1
        job_id = f"mock-job-{self._counter:06d}"
        record = JobRecord(job_id=job_id, request=request)
        record.events.append(
            {
                "status": JobStatus.QUEUED.value,
                "timestamp": record.created_at,
                "message": "Mock job accepted. No execution has started.",
            }
        )
        self._jobs[job_id] = record
        return record.to_status_response()

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._get_record(job_id).to_status_response()

    def get_job_result(self, job_id: str) -> dict[str, Any]:
        record = self._get_record(job_id)
        if record.status is not JobStatus.COMPLETED:
            return {
                "job_id": record.job_id,
                "status": record.status.value,
                "ready": False,
                "mock": True,
                "message": "Mock result is only available after completed status.",
            }

        return {
            "job_id": record.job_id,
            "status": record.status.value,
            "ready": True,
            "mock": True,
            "result_summary": {
                "accession": record.request.accession,
                "analysis_type": record.request.analysis_type.value,
                "species": record.request.species,
                "output_format": record.request.output_format.value,
            },
            "artifacts": [
                {
                    "name": "mock-analysis-report.html",
                    "type": "html_report",
                    "mock_uri": f"mock://{record.job_id}/mock-analysis-report.html",
                },
                {
                    "name": "mock-result-summary.json",
                    "type": "json_summary",
                    "mock_uri": f"mock://{record.job_id}/mock-result-summary.json",
                },
            ],
            "limitations": [
                "Phase 1 mock result only; no Snakemake, Conda, GEO/SRA, or production analysis was run.",
                "No biological conclusion should be made from this mock response.",
            ],
        }

    def cancel_job(self, job_id: str) -> dict[str, Any]:
        record = self._get_record(job_id)
        if not can_cancel(record.status):
            raise JobStateError(f"cannot cancel job in {record.status.value} status")
        self._set_status(record, JobStatus.CANCELLED, "Mock job cancelled.")
        return record.to_status_response()

    def advance_job(self, job_id: str, next_status: JobStatus | str) -> dict[str, Any]:
        """Advance a mock job for tests and local UI prototyping only."""

        record = self._get_record(job_id)
        parsed_status = JobStatus(next_status)
        require_transition(record.status, parsed_status)
        self._set_status(
            record,
            parsed_status,
            f"Mock job moved to {parsed_status.value}. No execution was run.",
        )
        return record.to_status_response()

    def _get_record(self, job_id: str) -> JobRecord:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise JobNotFoundError(job_id) from exc

    def _set_status(
        self, record: JobRecord, next_status: JobStatus, message: str
    ) -> None:
        timestamp = _now_iso()
        record.status = next_status
        record.updated_at = timestamp
        record.events.append(
            {
                "status": next_status.value,
                "timestamp": timestamp,
                "message": message,
            }
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_message(status: JobStatus) -> str:
    messages = {
        JobStatus.QUEUED: "Mock job is queued; no real execution is scheduled.",
        JobStatus.VALIDATING: "Mock validation state; schema-only behavior.",
        JobStatus.READY: "Mock job is ready; no worker will execute it.",
        JobStatus.RUNNING: "Mock running state; no shell or workflow is running.",
        JobStatus.SUMMARIZING: "Mock summarizing state; no report is being rendered.",
        JobStatus.COMPLETED: "Mock job completed with synthetic result metadata.",
        JobStatus.FAILED: "Mock job failed state.",
        JobStatus.CANCELLED: "Mock job was cancelled.",
    }
    return messages[status]
