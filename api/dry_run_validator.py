"""Pure dry-run execution request validator for Phase 1.4d.

This module validates request intent only. It does not start jobs, touch the
network, run workflow tools, write artifacts, persist state, or schedule work.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


ALLOWED_OUTPUT_FORMATS = {"json", "markdown", "html"}

REJECTION_REASON_ORDER = (
    "REAL_EXECUTION_NOT_ALLOWED",
    "NETWORK_ACCESS_NOT_ALLOWED",
    "PIPELINE_EXECUTION_NOT_ALLOWED",
    "SNAKEMAKE_NOT_ALLOWED",
    "REAL_COZE_CALL_NOT_ALLOWED",
    "OPERATOR_APPROVAL_NOT_ACTIVE_IN_THIS_PHASE",
    "UNSUPPORTED_OUTPUT_FORMAT",
    "UNSAFE_DATASET_ACCESSION",
    "COMMAND_FIELD_NOT_ALLOWED",
    "SECRET_FIELD_NOT_ALLOWED",
    "ARTIFACT_WRITE_NOT_ALLOWED",
    "DATABASE_WRITE_NOT_ALLOWED",
    "BACKGROUND_EXECUTION_NOT_ALLOWED",
)

_FALSE_ONLY_FIELDS = {
    "allow_network": "NETWORK_ACCESS_NOT_ALLOWED",
    "allow_pipeline_execution": "PIPELINE_EXECUTION_NOT_ALLOWED",
    "allow_snakemake": "SNAKEMAKE_NOT_ALLOWED",
    "allow_real_coze_call": "REAL_COZE_CALL_NOT_ALLOWED",
}

_COMMAND_FIELD_NAMES = {"command", "shell", "subprocess"}
_SNAKEMAKE_FIELD_NAMES = {"snakefile", "snakemake"}
_SECRET_FIELD_MARKERS = ("secret", "token", "password", "api_key", "apikey")
_ARTIFACT_FIELD_MARKERS = ("artifact", "artifacts", "output_path", "write_file")
_DATABASE_FIELD_MARKERS = ("database", "db_", "db.", "persist", "persistence")
_BACKGROUND_FIELD_MARKERS = ("background", "queue", "worker", "scheduler")
_UNSAFE_ACCESSION_MARKERS = (
    "://",
    "/",
    "\\",
    ":",
    ";",
    "&&",
    "|",
    "`",
    "$(",
    ">",
    "<",
)


def validate_dry_run_request(request: Mapping[str, Any]) -> dict[str, Any]:
    """Validate dry-run request intent without performing external effects."""

    reasons: list[str] = []
    if not isinstance(request, Mapping):
        return _result(["REAL_EXECUTION_NOT_ALLOWED"])

    normalized = _normalize_mapping(request)

    mode = _as_lower_text(normalized.get("mode", "dry_run"))
    if mode != "dry_run":
        reasons.append("REAL_EXECUTION_NOT_ALLOWED")

    for field_name, reason in _FALSE_ONLY_FIELDS.items():
        if _is_true(normalized.get(field_name, False)):
            reasons.append(reason)

    if _is_true(normalized.get("operator_approved", False)):
        reasons.append("OPERATOR_APPROVAL_NOT_ACTIVE_IN_THIS_PHASE")

    output_format = normalized.get("output_format")
    if output_format is not None:
        if _as_lower_text(output_format) not in ALLOWED_OUTPUT_FORMATS:
            reasons.append("UNSUPPORTED_OUTPUT_FORMAT")

    dataset_accession = normalized.get("dataset_accession")
    if dataset_accession is not None and _is_unsafe_accession(dataset_accession):
        reasons.append("UNSAFE_DATASET_ACCESSION")

    for field_name, value in normalized.items():
        if field_name in _COMMAND_FIELD_NAMES:
            reasons.append("COMMAND_FIELD_NOT_ALLOWED")
        if field_name in _SNAKEMAKE_FIELD_NAMES:
            reasons.append("SNAKEMAKE_NOT_ALLOWED")
        if any(marker in field_name for marker in _SECRET_FIELD_MARKERS):
            reasons.append("SECRET_FIELD_NOT_ALLOWED")
        if any(marker in field_name for marker in _ARTIFACT_FIELD_MARKERS):
            reasons.append("ARTIFACT_WRITE_NOT_ALLOWED")
        if any(marker in field_name for marker in _DATABASE_FIELD_MARKERS):
            reasons.append("DATABASE_WRITE_NOT_ALLOWED")
        if any(marker in field_name for marker in _BACKGROUND_FIELD_MARKERS):
            reasons.append("BACKGROUND_EXECUTION_NOT_ALLOWED")

        text_value = _as_lower_text(value)
        if "snakemake" in text_value:
            reasons.append("SNAKEMAKE_NOT_ALLOWED")
        if any(marker in text_value for marker in ("secret=", "token=", "password=")):
            reasons.append("SECRET_FIELD_NOT_ALLOWED")

    return _result(reasons)


def _result(reasons: list[str]) -> dict[str, Any]:
    ordered_reasons = [
        reason for reason in REJECTION_REASON_ORDER if reason in set(reasons)
    ]
    return {
        "accepted": not ordered_reasons,
        "mode": "dry_run",
        "rejection_reasons": ordered_reasons,
        "warnings": [],
    }


def _normalize_mapping(request: Mapping[str, Any]) -> dict[str, Any]:
    return {str(field_name).lower(): value for field_name, value in request.items()}


def _as_lower_text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip().lower()
    return ""


def _is_true(value: Any) -> bool:
    return value is True


def _is_unsafe_accession(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return True
    accession = value.strip()
    lowered = accession.lower()
    if lowered.startswith(("http://", "https://")):
        return True
    if ".." in accession:
        return True
    return any(marker in accession for marker in _UNSAFE_ACCESSION_MARKERS)
