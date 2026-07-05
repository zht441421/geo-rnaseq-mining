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


class AnalysisType(str, Enum):
    BULK = "bulk"
    SCRNA = "scrna"


class OutputFormat(str, Enum):
    JSON = "json"
    HTML = "html"
    ZIP = "zip"


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
            raise SchemaValidationError("submit job payload must be an object")

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
                "unsupported field(s): " + ", ".join(unknown)
            )

        missing = sorted(required - set(payload))
        if missing:
            raise SchemaValidationError(
                "missing required field(s): " + ", ".join(missing)
            )

        accession = _validate_plain_string(
            "accession", payload["accession"], _ACCESSION_RE
        )
        species = _validate_plain_string("species", payload["species"], _SAFE_TEXT_RE)
        requested_by = _validate_plain_string(
            "requested_by", payload["requested_by"], _REQUESTED_BY_RE
        )
        notes = _validate_notes(payload.get("notes", ""))

        try:
            analysis_type = AnalysisType(payload["analysis_type"])
        except ValueError as exc:
            allowed_values = ", ".join(item.value for item in AnalysisType)
            raise SchemaValidationError(
                f"analysis_type must be one of: {allowed_values}"
            ) from exc

        try:
            output_format = OutputFormat(payload["output_format"])
        except ValueError as exc:
            allowed_values = ", ".join(item.value for item in OutputFormat)
            raise SchemaValidationError(
                f"output_format must be one of: {allowed_values}"
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
    if not isinstance(value, str):
        raise SchemaValidationError(f"{field_name} must be a string")
    if not value:
        raise SchemaValidationError(f"{field_name} must not be empty")
    if any(marker in value for marker in _DISALLOWED_PATH_MARKERS):
        raise SchemaValidationError(f"{field_name} must not contain path markers")
    if ".." in value:
        raise SchemaValidationError(f"{field_name} must not contain path traversal")
    if not pattern.fullmatch(value):
        raise SchemaValidationError(f"{field_name} contains unsupported characters")
    return value


def _validate_notes(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SchemaValidationError("notes must be a string")
    if len(value) > 1000:
        raise SchemaValidationError("notes must be at most 1000 characters")
    if "\x00" in value:
        raise SchemaValidationError("notes must not contain null bytes")
    return value
