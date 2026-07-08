import http.client
import json
import threading

import pytest

import api.mock_service as mock_service_module
from api.http_server import build_server
from api.job_schema import SchemaValidationError
from api.mock_service import MockJobService


DRY_RUN_REQUEST = {
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

VALID_JOB_REQUEST = {
    "accession": "GSEMOCK001",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "json",
    "requested_by": "mock-coze-user",
}


def test_mock_api_calls_dry_run_validator(monkeypatch) -> None:
    calls = []

    def fake_validator(payload):
        calls.append(payload)
        return {
            "accepted": True,
            "mode": "dry_run",
            "rejection_reasons": [],
            "warnings": [],
        }

    monkeypatch.setattr(
        mock_service_module,
        "validate_dry_run_request",
        fake_validator,
    )

    response = mock_service_module.MockJobService().submit_job({"mode": "dry_run"})

    assert calls == [{"mode": "dry_run"}]
    assert response["status"] == "accepted"
    assert response["validation"]["accepted"] is True


def test_accepted_dry_run_request_returns_validation_report_without_job() -> None:
    service = MockJobService()

    response = service.submit_job(DRY_RUN_REQUEST)

    assert response == {
        "status": "accepted",
        "mode": "dry_run",
        "validation": {
            "accepted": True,
            "mode": "dry_run",
            "rejection_reasons": [],
            "warnings": [],
        },
        "execution": "not_started",
        "mock": True,
        "message": (
            "Dry-run request accepted for validation only; "
            "no real execution has started."
        ),
    }

    created = service.submit_job(VALID_JOB_REQUEST)
    assert created["job_id"] == "mock-job-000001"


def test_rejected_mode_run_returns_real_execution_not_allowed() -> None:
    response = MockJobService().submit_job(dict(DRY_RUN_REQUEST, mode="run"))

    assert response["status"] == "rejected"
    assert response["execution"] == "not_started"
    assert response["validation"]["accepted"] is False
    assert response["validation"]["rejection_reasons"] == [
        "REAL_EXECUTION_NOT_ALLOWED"
    ]


@pytest.mark.parametrize(
    ("field_name", "reason"),
    (
        ("allow_network", "NETWORK_ACCESS_NOT_ALLOWED"),
        ("allow_pipeline_execution", "PIPELINE_EXECUTION_NOT_ALLOWED"),
        ("allow_snakemake", "SNAKEMAKE_NOT_ALLOWED"),
        ("allow_real_coze_call", "REAL_COZE_CALL_NOT_ALLOWED"),
    ),
)
def test_rejected_execution_flags_return_deterministic_reasons(
    field_name, reason
) -> None:
    response = MockJobService().submit_job(dict(DRY_RUN_REQUEST, **{field_name: True}))

    assert response["status"] == "rejected"
    assert response["validation"]["accepted"] is False
    assert response["validation"]["rejection_reasons"] == [reason]
    assert response["message"].endswith("no real execution has started.")


def test_zip_output_format_remains_unsupported_for_dry_run_and_job_schema() -> None:
    dry_run_response = MockJobService().submit_job(
        dict(DRY_RUN_REQUEST, output_format="zip")
    )

    assert dry_run_response["status"] == "rejected"
    assert dry_run_response["validation"]["rejection_reasons"] == [
        "UNSUPPORTED_OUTPUT_FORMAT"
    ]

    with pytest.raises(SchemaValidationError) as context:
        MockJobService().submit_job(dict(VALID_JOB_REQUEST, output_format="zip"))
    assert context.value.code == "INVALID_OUTPUT_FORMAT"
    assert context.value.details == {"allowed_values": ["json", "markdown", "html"]}


def test_unsafe_dataset_accession_is_rejected() -> None:
    response = MockJobService().submit_job(
        dict(DRY_RUN_REQUEST, dataset_accession="../GSE123456")
    )

    assert response["status"] == "rejected"
    assert response["validation"]["rejection_reasons"] == [
        "UNSAFE_DATASET_ACCESSION"
    ]


def test_dry_run_validation_result_is_deterministic() -> None:
    payload = dict(
        DRY_RUN_REQUEST,
        mode="run",
        allow_network=True,
        allow_snakemake=True,
        output_format="zip",
    )

    first = MockJobService().submit_job(payload)
    second = MockJobService().submit_job(payload)

    assert first == second
    assert first["validation"]["rejection_reasons"] == [
        "REAL_EXECUTION_NOT_ALLOWED",
        "NETWORK_ACCESS_NOT_ALLOWED",
        "SNAKEMAKE_NOT_ALLOWED",
        "UNSUPPORTED_OUTPUT_FORMAT",
    ]


def test_existing_happy_path_and_negative_path_contracts_still_hold() -> None:
    service = MockJobService()

    created = service.submit_job(VALID_JOB_REQUEST)

    assert {
        "job_id",
        "status",
        "request",
        "created_at",
        "updated_at",
        "events",
        "mock",
        "message",
    } == set(created)
    assert created["status"] == "queued"
    assert created["request"]["output_format"] == "json"

    for output_format in ("json", "markdown", "html"):
        response = MockJobService().submit_job(
            dict(VALID_JOB_REQUEST, output_format=output_format)
        )
        assert response["request"]["output_format"] == output_format

    with pytest.raises(SchemaValidationError) as context:
        service.submit_job(dict(VALID_JOB_REQUEST, command="echo unsafe"))
    assert context.value.code == "UNKNOWN_FIELD"
    assert "command" in context.value.field_errors


def test_http_mock_returns_dry_run_validation_report_on_loopback() -> None:
    service = MockJobService()
    server = build_server("127.0.0.1", 0, service)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    host, port = server.server_address

    try:
        connection = http.client.HTTPConnection(host, port, timeout=5)
        connection.request(
            "POST",
            "/jobs",
            body=json.dumps(DRY_RUN_REQUEST),
            headers={"Content-Type": "application/json"},
        )
        http_response = connection.getresponse()
        payload = json.loads(http_response.read().decode("utf-8"))
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert http_response.status == 200
    assert payload["status"] == "accepted"
    assert payload["mode"] == "dry_run"
    assert payload["execution"] == "not_started"
    assert payload["validation"]["accepted"] is True
