import inspect
import unittest
from datetime import datetime

from api import JobStatus, MockJobService
from api.job_schema import SchemaValidationError
from api.mock_service import JobNotFoundError
from api.state_machine import JobStateError, require_transition
import api.mock_service as mock_service_module


VALID_PAYLOAD = {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "notes": "Phase 1 mock only",
}

COZE_VALID_JOB_REQUEST = {
    "accession": "GSEMOCK001",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "json",
    "requested_by": "mock-coze-user",
}
COZE_MARKDOWN_JOB_REQUEST = dict(COZE_VALID_JOB_REQUEST, output_format="markdown")
COZE_HTML_JOB_REQUEST = dict(COZE_VALID_JOB_REQUEST, output_format="html")
COZE_INVALID_OUTPUT_FORMAT_REQUEST = dict(
    COZE_VALID_JOB_REQUEST, output_format="zip"
)
COZE_MISSING_REQUESTED_BY_REQUEST = {
    "accession": "GSEMOCK001",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "json",
}

STATUS_RESPONSE_KEYS = {
    "job_id",
    "status",
    "request",
    "created_at",
    "updated_at",
    "events",
    "mock",
    "message",
}
REQUEST_KEYS = {
    "accession",
    "analysis_type",
    "species",
    "output_format",
    "requested_by",
    "notes",
}
EVENT_KEYS = {"status", "timestamp", "message"}
NOT_READY_RESULT_KEYS = {"job_id", "status", "ready", "mock", "message"}
COMPLETED_RESULT_KEYS = {
    "job_id",
    "status",
    "ready",
    "mock",
    "result_summary",
    "artifacts",
    "limitations",
}
RESULT_SUMMARY_KEYS = {"accession", "analysis_type", "species", "output_format"}
ARTIFACT_KEYS = {"name", "type", "mock_uri"}


class ApiMockTests(unittest.TestCase):
    def assert_schema_field_error(self, payload, field_name, code=None):
        service = MockJobService()
        with self.assertRaises(SchemaValidationError) as context:
            service.submit_job(payload)

        error = context.exception
        self.assertIn(field_name, error.field_errors)
        if code is not None:
            self.assertEqual(code, error.code)
        return error

    def assert_iso_timestamp(self, value):
        parsed = datetime.fromisoformat(value)
        self.assertIsNotNone(parsed.tzinfo)

    def assert_status_response_contract(
        self, response, expected_status, expected_request=None
    ):
        if expected_request is None:
            expected_request = VALID_PAYLOAD

        self.assertEqual(STATUS_RESPONSE_KEYS, set(response))
        self.assertEqual(expected_status, response["status"])
        self.assertTrue(response["mock"])
        self.assertRegex(response["job_id"], r"^mock-job-\d{6}$")
        self.assertEqual(REQUEST_KEYS, set(response["request"]))
        self.assertEqual(expected_request, response["request"])
        self.assert_iso_timestamp(response["created_at"])
        self.assert_iso_timestamp(response["updated_at"])
        self.assertIsInstance(response["events"], list)
        self.assertGreaterEqual(len(response["events"]), 1)
        for event in response["events"]:
            self.assertEqual(EVENT_KEYS, set(event))
            self.assertIn(
                event["status"],
                {
                    "queued",
                    "validating",
                    "ready",
                    "running",
                    "summarizing",
                    "completed",
                    "failed",
                    "cancelled",
                },
            )
            self.assert_iso_timestamp(event["timestamp"])
            self.assertIsInstance(event["message"], str)
            self.assertTrue(event["message"])
        self.assertIsInstance(response["message"], str)
        self.assertTrue(response["message"])

    def test_submit_job_creates_queued_mock_job(self):
        service = MockJobService()

        response = service.submit_job(VALID_PAYLOAD)

        self.assertEqual("mock-job-000001", response["job_id"])
        self.assertEqual("queued", response["status"])
        self.assertTrue(response["mock"])
        self.assertEqual("GSE123456", response["request"]["accession"])

    def test_coze_valid_request_example_submits_with_default_notes(self):
        service = MockJobService()

        response = service.submit_job(COZE_VALID_JOB_REQUEST)

        expected_request = dict(COZE_VALID_JOB_REQUEST, notes="")
        self.assert_status_response_contract(response, "queued", expected_request)
        self.assertEqual("json", response["request"]["output_format"])

    def test_coze_valid_request_examples_cover_allowed_output_formats(self):
        service = MockJobService()

        for payload in (
            COZE_VALID_JOB_REQUEST,
            COZE_MARKDOWN_JOB_REQUEST,
            COZE_HTML_JOB_REQUEST,
        ):
            with self.subTest(output_format=payload["output_format"]):
                response = service.submit_job(payload)

                self.assertEqual(
                    payload["output_format"],
                    response["request"]["output_format"],
                )
                self.assertEqual(dict(payload, notes=""), response["request"])

    def test_coze_invalid_request_examples_return_structured_errors(self):
        cases = (
            (
                COZE_INVALID_OUTPUT_FORMAT_REQUEST,
                "INVALID_OUTPUT_FORMAT",
                "output_format",
                {"allowed_values": ["json", "markdown", "html"]},
            ),
            (
                COZE_MISSING_REQUESTED_BY_REQUEST,
                "INVALID_REQUEST",
                "requested_by",
                {"fields": ["requested_by"]},
            ),
        )

        for payload, code, field_name, details in cases:
            with self.subTest(field=field_name):
                error = self.assert_schema_field_error(payload, field_name, code)

                self.assertEqual(details, error.details)

    def test_submit_job_success_response_contract_is_stable(self):
        service = MockJobService()

        response = service.submit_job(VALID_PAYLOAD)

        self.assert_status_response_contract(response, "queued")
        self.assertEqual(
            {
                "status": "queued",
                "timestamp": response["created_at"],
                "message": "Mock job accepted. No execution has started.",
            },
            response["events"][0],
        )

    def test_get_job_success_response_contract_is_stable(self):
        service = MockJobService()
        job_id = service.submit_job(VALID_PAYLOAD)["job_id"]

        response = service.get_job(job_id)

        self.assert_status_response_contract(response, "queued")

    def test_cancel_success_response_contract_is_stable(self):
        service = MockJobService()
        job_id = service.submit_job(VALID_PAYLOAD)["job_id"]

        response = service.cancel_job(job_id)

        self.assert_status_response_contract(response, "cancelled")
        self.assertEqual("cancelled", response["events"][-1]["status"])
        self.assertEqual("Mock job cancelled.", response["events"][-1]["message"])

    def test_submit_job_rejects_non_whitelisted_analysis_type(self):
        service = MockJobService()
        payload = dict(VALID_PAYLOAD, analysis_type="shell")

        with self.assertRaises(SchemaValidationError):
            service.submit_job(payload)

    def test_submit_job_accepts_markdown_output_format(self):
        service = MockJobService()
        payload = dict(VALID_PAYLOAD, output_format="markdown")

        response = service.submit_job(payload)

        self.assertEqual("markdown", response["request"]["output_format"])

    def test_submit_job_rejects_removed_zip_output_format(self):
        payload = dict(VALID_PAYLOAD, output_format="zip")

        self.assert_schema_field_error(
            payload, "output_format", "INVALID_OUTPUT_FORMAT"
        )

    def test_submit_job_rejects_invalid_output_formats(self):
        for output_format in ("pdf", "txt", "MARKDOWN", ""):
            with self.subTest(output_format=output_format):
                payload = dict(VALID_PAYLOAD, output_format=output_format)
                error = self.assert_schema_field_error(
                    payload, "output_format", "INVALID_OUTPUT_FORMAT"
                )
                self.assertEqual(
                    {"allowed_values": ["json", "markdown", "html"]},
                    error.details,
                )

    def test_submit_job_requires_output_format(self):
        payload = dict(VALID_PAYLOAD)
        del payload["output_format"]

        error = self.assert_schema_field_error(payload, "output_format")

        self.assertEqual({"fields": ["output_format"]}, error.details)

    def test_submit_job_rejects_missing_required_fields(self):
        for field_name in ("accession", "analysis_type", "requested_by"):
            with self.subTest(field=field_name):
                payload = dict(VALID_PAYLOAD)
                del payload[field_name]
                error = self.assert_schema_field_error(payload, field_name)
                self.assertEqual({"fields": [field_name]}, error.details)

    def test_submit_job_rejects_empty_required_fields(self):
        expected_codes = {
            "accession": "INVALID_ACCESSION",
            "analysis_type": "INVALID_ANALYSIS_TYPE",
            "output_format": "INVALID_OUTPUT_FORMAT",
            "requested_by": "INVALID_REQUEST",
        }
        for field_name, code in expected_codes.items():
            with self.subTest(field=field_name):
                payload = dict(VALID_PAYLOAD, **{field_name: ""})
                self.assert_schema_field_error(payload, field_name, code)

    def test_submit_job_rejects_wrong_type_required_fields(self):
        cases = {
            "accession": (["GSE123456"], "INVALID_ACCESSION"),
            "analysis_type": (["bulk"], "INVALID_ANALYSIS_TYPE"),
            "output_format": (["html"], "INVALID_OUTPUT_FORMAT"),
            "requested_by": (None, "INVALID_REQUEST"),
        }
        for field_name, (value, code) in cases.items():
            with self.subTest(field=field_name):
                payload = dict(VALID_PAYLOAD, **{field_name: value})
                self.assert_schema_field_error(payload, field_name, code)

    def test_submit_job_rejects_unknown_path_or_command_fields(self):
        service = MockJobService()

        for field_name in ("input_path", "command", "workdir", "snakefile"):
            with self.subTest(field=field_name):
                payload = dict(VALID_PAYLOAD)
                payload[field_name] = "C:/unsafe/path"
                with self.assertRaises(SchemaValidationError):
                    service.submit_job(payload)

    def test_submit_job_rejects_path_like_accession(self):
        service = MockJobService()

        for accession in ("../GSE123", "C:/GSE123", "folder/GSE123"):
            with self.subTest(accession=accession):
                payload = dict(VALID_PAYLOAD, accession=accession)
                with self.assertRaises(SchemaValidationError):
                    service.submit_job(payload)

    def test_status_machine_allows_expected_happy_path(self):
        service = MockJobService()
        job_id = service.submit_job(VALID_PAYLOAD)["job_id"]

        for status in (
            JobStatus.VALIDATING,
            JobStatus.READY,
            JobStatus.RUNNING,
            JobStatus.SUMMARIZING,
            JobStatus.COMPLETED,
        ):
            response = service.advance_job(job_id, status)

        self.assertEqual("completed", response["status"])

    def test_result_is_mock_only_and_available_after_completed(self):
        service = MockJobService()
        job_id = service.submit_job(VALID_PAYLOAD)["job_id"]

        not_ready = service.get_job_result(job_id)
        self.assertFalse(not_ready["ready"])

        for status in (
            JobStatus.VALIDATING,
            JobStatus.READY,
            JobStatus.RUNNING,
            JobStatus.SUMMARIZING,
            JobStatus.COMPLETED,
        ):
            service.advance_job(job_id, status)

        result = service.get_job_result(job_id)
        self.assertTrue(result["ready"])
        self.assertEqual("completed", result["status"])
        self.assertTrue(result["mock"])
        self.assertIn("artifacts", result)
        self.assertIn("no Snakemake", result["limitations"][0])

    def test_not_ready_result_response_contract_is_stable(self):
        service = MockJobService()
        job_id = service.submit_job(VALID_PAYLOAD)["job_id"]

        result = service.get_job_result(job_id)

        self.assertEqual(NOT_READY_RESULT_KEYS, set(result))
        self.assertEqual(job_id, result["job_id"])
        self.assertEqual("queued", result["status"])
        self.assertFalse(result["ready"])
        self.assertTrue(result["mock"])
        self.assertEqual(
            "Mock result is only available after completed status.",
            result["message"],
        )

    def test_completed_result_response_contract_is_stable(self):
        service = MockJobService()
        job_id = service.submit_job(VALID_PAYLOAD)["job_id"]
        for status in (
            JobStatus.VALIDATING,
            JobStatus.READY,
            JobStatus.RUNNING,
            JobStatus.SUMMARIZING,
            JobStatus.COMPLETED,
        ):
            service.advance_job(job_id, status)

        result = service.get_job_result(job_id)

        self.assertEqual(COMPLETED_RESULT_KEYS, set(result))
        self.assertEqual(job_id, result["job_id"])
        self.assertEqual("completed", result["status"])
        self.assertTrue(result["ready"])
        self.assertTrue(result["mock"])
        self.assertEqual(RESULT_SUMMARY_KEYS, set(result["result_summary"]))
        self.assertEqual(
            {
                "accession": "GSE123456",
                "analysis_type": "bulk",
                "species": "Homo sapiens",
                "output_format": "html",
            },
            result["result_summary"],
        )
        self.assertIsInstance(result["artifacts"], list)
        self.assertGreaterEqual(len(result["artifacts"]), 1)
        for artifact in result["artifacts"]:
            self.assertEqual(ARTIFACT_KEYS, set(artifact))
            self.assertTrue(artifact["mock_uri"].startswith(f"mock://{job_id}/"))
        self.assertIsInstance(result["limitations"], list)
        self.assertIn("no Snakemake", result["limitations"][0])

    def test_cancel_marks_cancellable_jobs_cancelled(self):
        service = MockJobService()
        job_id = service.submit_job(VALID_PAYLOAD)["job_id"]

        response = service.cancel_job(job_id)

        self.assertEqual("cancelled", response["status"])

    def test_terminal_jobs_cannot_be_cancelled_or_advanced(self):
        service = MockJobService()
        job_id = service.submit_job(VALID_PAYLOAD)["job_id"]
        for status in (
            JobStatus.VALIDATING,
            JobStatus.READY,
            JobStatus.RUNNING,
            JobStatus.SUMMARIZING,
            JobStatus.COMPLETED,
        ):
            service.advance_job(job_id, status)

        with self.assertRaises(JobStateError):
            service.cancel_job(job_id)
        with self.assertRaises(JobStateError):
            service.advance_job(job_id, JobStatus.FAILED)

    def test_invalid_state_transition_is_rejected(self):
        with self.assertRaises(JobStateError):
            require_transition(JobStatus.QUEUED, JobStatus.RUNNING)

    def test_unknown_job_is_rejected(self):
        service = MockJobService()

        with self.assertRaises(JobNotFoundError):
            service.get_job("missing-job")

    def test_mock_service_contains_no_execution_primitives(self):
        source = inspect.getsource(mock_service_module)
        forbidden_tokens = (
            "subprocess",
            "os.system",
            "shell=True",
            "snakemake",
            "conda env",
            "mamba env",
        )

        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
