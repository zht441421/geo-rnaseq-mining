import inspect

from api import dry_run_validator
from api.dry_run_validator import validate_dry_run_request


def test_accepts_safe_dry_run_request() -> None:
    result = validate_dry_run_request(
        {
            "mode": "dry_run",
            "dataset_accession": "GSE123456",
            "analysis_type": "rnaseq_placeholder",
            "output_format": "json",
            "allow_network": False,
            "allow_pipeline_execution": False,
            "allow_snakemake": False,
            "allow_real_coze_call": False,
            "operator_approved": False,
        }
    )

    assert result == {
        "accepted": True,
        "mode": "dry_run",
        "rejection_reasons": [],
        "warnings": [],
    }


def test_missing_execution_flags_default_to_safe_false() -> None:
    result = validate_dry_run_request(
        {
            "dataset_accession": "GSE123456",
            "analysis_type": "rnaseq_placeholder",
            "output_format": "markdown",
        }
    )

    assert result["accepted"] is True
    assert result["mode"] == "dry_run"
    assert result["rejection_reasons"] == []


def test_rejects_real_execution_modes_and_operator_approval() -> None:
    result = validate_dry_run_request(
        {
            "mode": "execute",
            "operator_approved": True,
        }
    )

    assert result["accepted"] is False
    assert result["rejection_reasons"] == [
        "REAL_EXECUTION_NOT_ALLOWED",
        "OPERATOR_APPROVAL_NOT_ACTIVE_IN_THIS_PHASE",
    ]


def test_rejects_true_execution_flags() -> None:
    result = validate_dry_run_request(
        {
            "mode": "dry_run",
            "allow_network": True,
            "allow_pipeline_execution": True,
            "allow_snakemake": True,
            "allow_real_coze_call": True,
        }
    )

    assert result["accepted"] is False
    assert result["rejection_reasons"] == [
        "NETWORK_ACCESS_NOT_ALLOWED",
        "PIPELINE_EXECUTION_NOT_ALLOWED",
        "SNAKEMAKE_NOT_ALLOWED",
        "REAL_COZE_CALL_NOT_ALLOWED",
    ]


def test_rejects_unsafe_accession_and_output_format() -> None:
    result = validate_dry_run_request(
        {
            "mode": "dry_run",
            "dataset_accession": "https://example.invalid/GSE123456",
            "output_format": "zip",
        }
    )

    assert result["accepted"] is False
    assert result["rejection_reasons"] == [
        "UNSUPPORTED_OUTPUT_FORMAT",
        "UNSAFE_DATASET_ACCESSION",
    ]


def test_rejects_command_secret_artifact_database_and_background_fields() -> None:
    result = validate_dry_run_request(
        {
            "mode": "dry_run",
            "command": "snakemake --cores 8",
            "token": "REDACTED_EXAMPLE_ONLY",
            "artifact_path": "report.html",
            "database_url": "sqlite:///example.db",
            "worker": True,
        }
    )

    assert result["accepted"] is False
    assert result["rejection_reasons"] == [
        "SNAKEMAKE_NOT_ALLOWED",
        "COMMAND_FIELD_NOT_ALLOWED",
        "SECRET_FIELD_NOT_ALLOWED",
        "ARTIFACT_WRITE_NOT_ALLOWED",
        "DATABASE_WRITE_NOT_ALLOWED",
        "BACKGROUND_EXECUTION_NOT_ALLOWED",
    ]


def test_validator_module_contains_no_runtime_execution_primitives() -> None:
    source = inspect.getsource(dry_run_validator).lower()

    forbidden_primitives = (
        "subprocess.",
        "requests.",
        "httpx.",
        "urllib.",
        "socket.",
        "os.system",
        "popen(",
        "run(",
        "open(",
        "write(",
    )

    leaked_primitives = [
        primitive for primitive in forbidden_primitives if primitive in source
    ]

    assert leaked_primitives == []
