import inspect
import unittest

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


class ApiMockTests(unittest.TestCase):
    def test_submit_job_creates_queued_mock_job(self):
        service = MockJobService()

        response = service.submit_job(VALID_PAYLOAD)

        self.assertEqual("mock-job-000001", response["job_id"])
        self.assertEqual("queued", response["status"])
        self.assertTrue(response["mock"])
        self.assertEqual("GSE123456", response["request"]["accession"])

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
        service = MockJobService()
        payload = dict(VALID_PAYLOAD, output_format="zip")

        with self.assertRaises(SchemaValidationError):
            service.submit_job(payload)

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
