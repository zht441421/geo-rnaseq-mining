"""Schema validation for the Phase 1 local API mock.

The mock deliberately accepts only structured values. It does not accept file
paths, shell fragments, arbitrary commands, or pipeline names from callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Mapping


class SchemaValidationError(ValueError):
    """Raised when a mock API request does not match the accepted schema."""

    def __init__(
        self,
        message: str,
        code: str = "INVALID_REQUEST",
        field_errors: dict[str, list[str]] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.field_errors = field_errors or {}
        self.details = details or {}


class AnalysisType(str, Enum):
    BULK = "bulk"
    SCRNA = "scrna"


class OutputFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


_ACCESSION_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
_SAFE_TEXT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 _.-]{0,79}$")
_REQUESTED_BY_RE = re.compile(r"^[A-Za-z0-9_.@-]{1,120}$")
_DISALLOWED_PATH_MARKERS = ("/", "\\", ":", "~")


@dataclass(frozen=True)
class JobSubmitRequest:
    accession: str
    analysis_type: AnalysisType
    species: str
    output_format: OutputFormat
    requested_by: str
    notes: str = ""

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "JobSubmitRequest":
        if not isinstance(payload, Mapping):
            raise SchemaValidationError(
                "submit job payload must be an object",
                details={"expected": "object"},
            )

        required = {
            "accession",
            "analysis_type",
            "species",
            "output_format",
            "requested_by",
        }
        optional = {"notes"}
        allowed = required | optional

        unknown = sorted(set(payload) - allowed)
        if unknown:
            raise SchemaValidationError(
                "unsupported field(s): " + ", ".join(unknown),
                code="UNKNOWN_FIELD",
                field_errors={
                    field_name: ["unsupported field"] for field_name in unknown
                },
                details={"fields": unknown},
            )

        missing = sorted(required - set(payload))
        if missing:
            raise SchemaValidationError(
                "missing required field(s): " + ", ".join(missing),
                field_errors={
                    field_name: ["missing required field"] for field_name in missing
                },
                details={"fields": missing},
            )

        accession = _validate_plain_string(
            "accession", payload["accession"], _ACCESSION_RE
        )
        species = _validate_plain_string("species", payload["species"], _SAFE_TEXT_RE)
        requested_by = _validate_plain_string(
            "requested_by", payload["requested_by"], _REQUESTED_BY_RE
        )
        notes = _validate_notes(payload.get("notes", ""))

        analysis_value = payload["analysis_type"]
        allowed_analysis_types = [item.value for item in AnalysisType]
        if not isinstance(analysis_value, str) or not analysis_value:
            allowed_values = ", ".join(allowed_analysis_types)
            raise SchemaValidationError(
                f"analysis_type must be one of: {allowed_values}",
                code="INVALID_ANALYSIS_TYPE",
                field_errors={
                    "analysis_type": [
                        "must be one of: " + ", ".join(allowed_analysis_types)
                    ]
                },
                details={"allowed_values": allowed_analysis_types},
            )
        try:
            analysis_type = AnalysisType(analysis_value)
        except ValueError as exc:
            allowed_values = ", ".join(allowed_analysis_types)
            raise SchemaValidationError(
                f"analysis_type must be one of: {allowed_values}",
                code="INVALID_ANALYSIS_TYPE",
                field_errors={
                    "analysis_type": [
                        "must be one of: " + ", ".join(allowed_analysis_types)
                    ]
                },
                details={"allowed_values": allowed_analysis_types},
            ) from exc

        output_value = payload["output_format"]
        allowed_output_formats = [item.value for item in OutputFormat]
        if not isinstance(output_value, str) or not output_value:
            allowed_values = ", ".join(allowed_output_formats)
            raise SchemaValidationError(
                f"output_format must be one of: {allowed_values}",
                code="INVALID_OUTPUT_FORMAT",
                field_errors={
                    "output_format": [
                        "must be one of: " + ", ".join(allowed_output_formats)
                    ]
                },
                details={"allowed_values": allowed_output_formats},
            )
        try:
            output_format = OutputFormat(output_value)
        except ValueError as exc:
            allowed_values = ", ".join(allowed_output_formats)
            raise SchemaValidationError(
                f"output_format must be one of: {allowed_values}",
                code="INVALID_OUTPUT_FORMAT",
                field_errors={
                    "output_format": [
                        "must be one of: " + ", ".join(allowed_output_formats)
                    ]
                },
                details={"allowed_values": allowed_output_formats},
            ) from exc

        return cls(
            accession=accession,
            analysis_type=analysis_type,
            species=species,
            output_format=output_format,
            requested_by=requested_by,
            notes=notes,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "accession": self.accession,
            "analysis_type": self.analysis_type.value,
            "species": self.species,
            "output_format": self.output_format.value,
            "requested_by": self.requested_by,
            "notes": self.notes,
        }


def _validate_plain_string(
    field_name: str, value: Any, pattern: re.Pattern[str]
) -> str:
    code = "INVALID_ACCESSION" if field_name == "accession" else "INVALID_REQUEST"
    if not isinstance(value, str):
        raise SchemaValidationError(
            f"{field_name} must be a string",
            code=code,
            field_errors={field_name: ["must be a string"]},
        )
    if not value:
        raise SchemaValidationError(
            f"{field_name} must not be empty",
            code=code,
            field_errors={field_name: ["must not be empty"]},
        )
    if any(marker in value for marker in _DISALLOWED_PATH_MARKERS):
        raise SchemaValidationError(
            f"{field_name} must not contain path markers",
            code=code,
            field_errors={field_name: ["must not contain path markers"]},
        )
    if ".." in value:
        raise SchemaValidationError(
            f"{field_name} must not contain path traversal",
            code=code,
            field_errors={field_name: ["must not contain path traversal"]},
        )
    if not pattern.fullmatch(value):
        raise SchemaValidationError(
            f"{field_name} contains unsupported characters",
            code=code,
            field_errors={field_name: ["contains unsupported characters"]},
        )
    return value


def _validate_notes(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SchemaValidationError(
            "notes must be a string",
            field_errors={"notes": ["must be a string"]},
        )
    if len(value) > 1000:
        raise SchemaValidationError(
            "notes must be at most 1000 characters",
            field_errors={"notes": ["must be at most 1000 characters"]},
        )
    if "\x00" in value:
        raise SchemaValidationError(
            "notes must not contain null bytes",
            field_errors={"notes": ["must not contain null bytes"]},
        )
    return value
