import http.client
import json
import threading
from collections.abc import Iterator

import pytest

from api.mock_service import MockJobService
from api.http_server import build_server


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


def _rejected_response(payload: dict[str, object]) -> dict[str, object]:
    response = MockJobService().submit_job(payload)

    assert response["status"] == "rejected"
    assert response["mode"] == "dry_run"
    assert response["execution"] == "not_started"
    assert response["mock"] is True
    assert response["validation"]["accepted"] is False
    assert "job_id" not in response
    return response


@pytest.mark.parametrize("mode", ("run", "execute"))
def test_service_rejects_real_execution_modes(mode) -> None:
    response = _rejected_response(dict(DRY_RUN_REQUEST, mode=mode))

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
        ("operator_approved", "OPERATOR_APPROVAL_NOT_ACTIVE_IN_THIS_PHASE"),
    ),
)
def test_service_rejects_enabled_execution_flags(field_name, reason) -> None:
    response = _rejected_response(dict(DRY_RUN_REQUEST, **{field_name: True}))

    assert response["validation"]["rejection_reasons"] == [reason]


def test_service_rejects_unsupported_output_format() -> None:
    response = _rejected_response(dict(DRY_RUN_REQUEST, output_format="zip"))

    assert response["validation"]["rejection_reasons"] == [
        "UNSUPPORTED_OUTPUT_FORMAT"
    ]


@pytest.mark.parametrize(
    "dataset_accession",
    (
        "https://example.invalid/GSE123456",
        "GSE123456;blocked",
    ),
)
def test_service_rejects_unsafe_dataset_accessions(dataset_accession) -> None:
    response = _rejected_response(
        dict(DRY_RUN_REQUEST, dataset_accession=dataset_accession)
    )

    assert response["validation"]["rejection_reasons"] == [
        "UNSAFE_DATASET_ACCESSION"
    ]


@pytest.mark.parametrize(
    ("field_name", "reason"),
    (
        ("command", "COMMAND_FIELD_NOT_ALLOWED"),
        ("shell", "COMMAND_FIELD_NOT_ALLOWED"),
        ("subprocess", "COMMAND_FIELD_NOT_ALLOWED"),
        ("snakemake", "SNAKEMAKE_NOT_ALLOWED"),
        ("snakefile", "SNAKEMAKE_NOT_ALLOWED"),
    ),
)
def test_service_rejects_command_and_workflow_fields(field_name, reason) -> None:
    response = _rejected_response(dict(DRY_RUN_REQUEST, **{field_name: "blocked"}))

    assert response["validation"]["rejection_reasons"] == [reason]


@pytest.mark.parametrize("field_name", ("secret_note", "token", "password", "api_key"))
def test_service_rejects_secret_like_fields(field_name) -> None:
    response = _rejected_response(dict(DRY_RUN_REQUEST, **{field_name: "redacted"}))

    assert response["validation"]["rejection_reasons"] == [
        "SECRET_FIELD_NOT_ALLOWED"
    ]


@pytest.mark.parametrize(
    ("field_name", "reason"),
    (
        ("artifact_path", "ARTIFACT_WRITE_NOT_ALLOWED"),
        ("database", "DATABASE_WRITE_NOT_ALLOWED"),
        ("worker", "BACKGROUND_EXECUTION_NOT_ALLOWED"),
        ("scheduler", "BACKGROUND_EXECUTION_NOT_ALLOWED"),
    ),
)
def test_service_rejects_persistence_and_background_intent(field_name, reason) -> None:
    response = _rejected_response(dict(DRY_RUN_REQUEST, **{field_name: "blocked"}))

    assert response["validation"]["rejection_reasons"] == [reason]


def test_service_returns_multiple_rejection_reasons_in_deterministic_order() -> None:
    payload = dict(
        DRY_RUN_REQUEST,
        mode="execute",
        allow_network=True,
        allow_pipeline_execution=True,
        allow_snakemake=True,
        allow_real_coze_call=True,
        operator_approved=True,
        output_format="zip",
        dataset_accession="GSE123456;blocked",
        command="blocked",
        token="redacted",
        artifact_path="blocked",
        database="blocked",
        worker="blocked",
    )

    first = MockJobService().submit_job(payload)
    second = MockJobService().submit_job(payload)

    assert first == second
    assert first["status"] == "rejected"
    assert "job_id" not in first
    assert first["execution"] == "not_started"
    assert first["validation"]["rejection_reasons"] == [
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
    ]


def test_service_dry_run_validation_reports_do_not_allocate_job_ids() -> None:
    service = MockJobService()

    rejected = service.submit_job(dict(DRY_RUN_REQUEST, mode="run"))
    accepted = service.submit_job(DRY_RUN_REQUEST)
    created = service.submit_job(VALID_JOB_REQUEST)

    assert rejected["status"] == "rejected"
    assert accepted["status"] == "accepted"
    assert rejected["execution"] == "not_started"
    assert accepted["execution"] == "not_started"
    assert "job_id" not in rejected
    assert "job_id" not in accepted
    assert created["job_id"] == "mock-job-000001"


@pytest.fixture
def http_client() -> Iterator[tuple[str, int]]:
    service = MockJobService()
    server = build_server("127.0.0.1", 0, service)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()

    try:
        yield server.server_address
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _post_json(host: str, port: int, path: str, payload: dict[str, object]):
    connection = http.client.HTTPConnection(host, port, timeout=5)
    connection.request(
        "POST",
        path,
        body=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    body = json.loads(response.read().decode("utf-8"))
    connection.close()
    return response.status, body


def test_http_rejected_dry_run_returns_validation_reasons(http_client) -> None:
    host, port = http_client

    status, payload = _post_json(
        host,
        port,
        "/jobs",
        dict(DRY_RUN_REQUEST, allow_network=True, output_format="zip"),
    )

    assert status == 200
    assert payload["status"] == "rejected"
    assert payload["validation"]["accepted"] is False
    assert payload["validation"]["rejection_reasons"] == [
        "NETWORK_ACCESS_NOT_ALLOWED",
        "UNSUPPORTED_OUTPUT_FORMAT",
    ]
    assert payload["execution"] == "not_started"
    assert "job_id" not in payload


def test_http_accepted_dry_run_remains_not_started(http_client) -> None:
    host, port = http_client

    status, payload = _post_json(host, port, "/jobs", DRY_RUN_REQUEST)

    assert status == 200
    assert payload["status"] == "accepted"
    assert payload["validation"]["accepted"] is True
    assert payload["execution"] == "not_started"
    assert "no real execution has started" in payload["message"]
    assert "job_id" not in payload


def test_http_ordinary_mock_job_still_returns_created_job(http_client) -> None:
    host, port = http_client

    status, payload = _post_json(host, port, "/jobs", VALID_JOB_REQUEST)

    assert status == 201
    assert payload["status"] == "queued"
    assert payload["job_id"] == "mock-job-000001"
    assert payload["request"]["output_format"] == "json"
