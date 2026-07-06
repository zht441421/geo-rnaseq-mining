import http.client
import inspect
import json
import threading
import unittest

from api import JobStatus, MockJobService
from api.http_server import build_server
import api.http_server as http_server_module


VALID_PAYLOAD = {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "notes": "HTTP mock contract test",
}


class ApiHttpServerTests(unittest.TestCase):
    def setUp(self):
        self.service = MockJobService()
        self.server = build_server("127.0.0.1", 0, self.service)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def request(self, method, path, body=None):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        headers = {}
        if body is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(body)
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        connection.close()
        return response.status, json.loads(raw)

    def raw_request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        raw = response.read().decode("utf-8")
        connection.close()
        return response.status, json.loads(raw)

    def test_health_endpoint(self):
        status, payload = self.request("GET", "/health")

        self.assertEqual(200, status)
        self.assertEqual({"mock": True, "status": "ok"}, payload)

    def test_submit_status_result_and_cancel_shape(self):
        status, created = self.request("POST", "/jobs", VALID_PAYLOAD)

        self.assertEqual(201, status)
        job_id = created["job_id"]
        self.assertEqual("queued", created["status"])

        status, current = self.request("GET", f"/jobs/{job_id}")
        self.assertEqual(200, status)
        self.assertEqual("queued", current["status"])

        status, result = self.request("GET", f"/jobs/{job_id}/result")
        self.assertEqual(409, status)
        self.assertEqual("JOB_NOT_READY", result["error"]["code"])

        status, cancelled = self.request("POST", f"/jobs/{job_id}/cancel")
        self.assertEqual(200, status)
        self.assertEqual("cancelled", cancelled["status"])

    def test_completed_job_returns_mock_result(self):
        job_id = self.service.submit_job(VALID_PAYLOAD)["job_id"]
        for status in (
            JobStatus.VALIDATING,
            JobStatus.READY,
            JobStatus.RUNNING,
            JobStatus.SUMMARIZING,
            JobStatus.COMPLETED,
        ):
            self.service.advance_job(job_id, status)

        status, result = self.request("GET", f"/jobs/{job_id}/result")

        self.assertEqual(200, status)
        self.assertTrue(result["ready"])
        self.assertEqual("completed", result["status"])
        self.assertTrue(result["mock"])

    def test_unknown_path_returns_404(self):
        status, payload = self.request("GET", "/unknown")

        self.assertEqual(404, status)
        self.assertEqual("NOT_FOUND", payload["error"]["code"])

    def test_invalid_json_returns_400(self):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=5)
        connection.request(
            "POST",
            "/jobs",
            body="{not-json",
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        connection.close()

        self.assertEqual(400, response.status)
        self.assertEqual("INVALID_JSON", payload["error"]["code"])
        self.assertIn("details", payload["error"])

    def test_missing_content_type_returns_415(self):
        status, payload = self.raw_request(
            "POST",
            "/jobs",
            body=json.dumps(VALID_PAYLOAD),
        )

        self.assertEqual(415, status)
        self.assertEqual("UNSUPPORTED_MEDIA_TYPE", payload["error"]["code"])
        self.assertIn("details", payload["error"])

    def test_wrong_content_type_returns_415(self):
        status, payload = self.raw_request(
            "POST",
            "/jobs",
            body=json.dumps(VALID_PAYLOAD),
            headers={"Content-Type": "text/plain"},
        )

        self.assertEqual(415, status)
        self.assertEqual("UNSUPPORTED_MEDIA_TYPE", payload["error"]["code"])
        self.assertEqual("text/plain", payload["error"]["details"]["content_type"])

    def test_schema_error_returns_400(self):
        payload = dict(VALID_PAYLOAD, analysis_type="shell")

        status, response = self.request("POST", "/jobs", payload)

        self.assertEqual(400, status)
        self.assertEqual("INVALID_ANALYSIS_TYPE", response["error"]["code"])
        self.assertIn("analysis_type", response["error"]["field_errors"])

    def test_markdown_output_format_is_accepted(self):
        payload = dict(VALID_PAYLOAD, output_format="markdown")

        status, response = self.request("POST", "/jobs", payload)

        self.assertEqual(201, status)
        self.assertEqual("markdown", response["request"]["output_format"])

    def test_zip_output_format_is_rejected(self):
        self.assert_invalid_output_format("zip")

    def test_invalid_output_formats_are_rejected(self):
        for output_format in ("pdf", "txt", "MARKDOWN", ""):
            with self.subTest(output_format=output_format):
                self.assert_invalid_output_format(output_format)

    def assert_invalid_output_format(self, output_format):
        payload = dict(VALID_PAYLOAD, output_format=output_format)

        status, response = self.request("POST", "/jobs", payload)

        self.assertEqual(400, status)
        self.assertEqual("INVALID_OUTPUT_FORMAT", response["error"]["code"])
        self.assertIn("output_format", response["error"]["field_errors"])
        self.assertEqual(
            ["json", "markdown", "html"],
            response["error"]["details"]["allowed_values"],
        )

    def test_missing_required_fields_return_field_errors(self):
        for field_name in ("accession", "analysis_type", "output_format"):
            with self.subTest(field=field_name):
                payload = dict(VALID_PAYLOAD)
                del payload[field_name]

                status, response = self.request("POST", "/jobs", payload)

                self.assertEqual(400, status)
                self.assertIn(field_name, response["error"]["field_errors"])
                self.assertEqual([field_name], response["error"]["details"]["fields"])

    def test_empty_required_fields_return_field_errors(self):
        for field_name in ("accession", "output_format"):
            with self.subTest(field=field_name):
                payload = dict(VALID_PAYLOAD, **{field_name: ""})

                status, response = self.request("POST", "/jobs", payload)

                self.assertEqual(400, status)
                self.assertIn(field_name, response["error"]["field_errors"])

    def test_job_not_found_returns_404(self):
        status, payload = self.request("GET", "/jobs/missing-job")

        self.assertEqual(404, status)
        self.assertEqual("JOB_NOT_FOUND", payload["error"]["code"])
        self.assertEqual("missing-job", payload["error"]["details"]["job_id"])

    def test_completed_job_is_not_cancellable(self):
        job_id = self.service.submit_job(VALID_PAYLOAD)["job_id"]
        for status in (
            JobStatus.VALIDATING,
            JobStatus.READY,
            JobStatus.RUNNING,
            JobStatus.SUMMARIZING,
            JobStatus.COMPLETED,
        ):
            self.service.advance_job(job_id, status)

        status, payload = self.request("POST", f"/jobs/{job_id}/cancel")

        self.assertEqual(409, status)
        self.assertEqual("JOB_NOT_CANCELLABLE", payload["error"]["code"])
        self.assertIn("details", payload["error"])

    def test_http_module_contains_no_disallowed_runtime_primitives(self):
        source = inspect.getsource(http_server_module)
        forbidden_tokens = (
            "subprocess",
            "os.system",
            "shell=True",
            "os.environ",
            "getenv",
            "requests",
            "curl",
            "wget",
            "git clone",
        )

        for token in forbidden_tokens:
            with self.subTest(token=token):
                self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
