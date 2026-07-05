"""Standard-library HTTP entrypoint for the local API mock.

The module exposes a handler factory and an explicit ``main`` entrypoint. It
does not bind a port when imported.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from typing import Any

from .job_schema import SchemaValidationError
from .mock_service import JobNotFoundError, MockJobService
from .state_machine import JobStateError


MAX_REQUEST_BYTES = 64 * 1024


def make_handler(service: MockJobService | None = None) -> type[BaseHTTPRequestHandler]:
    """Create a request handler class bound to an in-memory mock service."""

    job_service = service or MockJobService()

    class MockApiHandler(BaseHTTPRequestHandler):
        server_version = "GeoRnaseqMockApi/0.1"

        def do_GET(self) -> None:
            parts = _path_parts(self.path)
            if parts == ["health"]:
                self._send_json(200, {"status": "ok", "mock": True})
                return

            if len(parts) == 2 and parts[0] == "jobs":
                self._handle_service_call(lambda: job_service.get_job(parts[1]))
                return

            if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "result":
                self._handle_result(parts[1])
                return

            self._send_error(404, "NOT_FOUND", "Unknown endpoint.")

        def do_POST(self) -> None:
            parts = _path_parts(self.path)
            if parts == ["jobs"]:
                payload = self._read_json_body()
                if payload is None:
                    return
                self._handle_service_call(
                    lambda: job_service.submit_job(payload),
                    success_status=201,
                )
                return

            if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "cancel":
                self._handle_service_call(lambda: job_service.cancel_job(parts[1]))
                return

            self._send_error(404, "NOT_FOUND", "Unknown endpoint.")

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _handle_result(self, job_id: str) -> None:
            try:
                result = job_service.get_job_result(job_id)
            except JobNotFoundError:
                self._send_error(
                    404,
                    "JOB_NOT_FOUND",
                    f"No job exists for job_id {job_id}.",
                    {"job_id": job_id},
                )
                return

            if not result.get("ready", False):
                self._send_error(
                    409,
                    "JOB_NOT_READY",
                    "Mock result is only available after completed status.",
                    {"job_id": job_id, "status": result.get("status")},
                    retryable=True,
                )
                return

            self._send_json(200, result)

        def _handle_service_call(
            self, call: Any, success_status: int = 200
        ) -> None:
            try:
                self._send_json(success_status, call())
            except SchemaValidationError as exc:
                self._send_schema_error(exc)
            except JobNotFoundError as exc:
                job_id = str(exc.args[0]) if exc.args else ""
                self._send_error(
                    404,
                    "JOB_NOT_FOUND",
                    f"No job exists for job_id {job_id}.",
                    {"job_id": job_id},
                )
            except JobStateError as exc:
                self._send_error(409, "JOB_NOT_CANCELLABLE", str(exc))
            except ValueError as exc:
                self._send_error(400, "INVALID_REQUEST", str(exc))

        def _read_json_body(self) -> dict[str, Any] | None:
            length_header = self.headers.get("Content-Length", "0")
            try:
                length = int(length_header)
            except ValueError:
                self._send_error(400, "INVALID_JSON", "Invalid Content-Length.")
                return None

            if length > MAX_REQUEST_BYTES:
                self._send_error(413, "REQUEST_TOO_LARGE", "Request body is too large.")
                return None

            raw_body = self.rfile.read(length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_error(400, "INVALID_JSON", "Request body must be valid JSON.")
                return None

            if not isinstance(payload, dict):
                self._send_error(400, "INVALID_JSON", "Request JSON must be an object.")
                return None

            return payload

        def _send_schema_error(self, exc: SchemaValidationError) -> None:
            message = str(exc)
            if message.startswith("unsupported field"):
                code = "UNKNOWN_FIELD"
            elif message.startswith("analysis_type"):
                code = "INVALID_ANALYSIS_TYPE"
            elif message.startswith("output_format"):
                code = "INVALID_OUTPUT_FORMAT"
            elif message.startswith("accession"):
                code = "INVALID_ACCESSION"
            else:
                code = "INVALID_REQUEST"
            self._send_error(400, code, message)

        def _send_error(
            self,
            status: int,
            code: str,
            message: str,
            details: dict[str, Any] | None = None,
            retryable: bool = False,
        ) -> None:
            error: dict[str, Any] = {
                "code": code,
                "message": message,
                "retryable": retryable,
            }
            if details:
                error["details"] = details
            self._send_json(status, {"error": error})

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return MockApiHandler


def build_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    service: MockJobService | None = None,
) -> ThreadingHTTPServer:
    """Build a local mock server without starting its serve loop."""

    return ThreadingHTTPServer((host, port), make_handler(service))


def main() -> None:
    server = build_server()
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _path_parts(raw_path: str) -> list[str]:
    clean_path = raw_path.split("?", 1)[0].strip("/")
    if not clean_path:
        return []
    return [part for part in clean_path.split("/") if part]


if __name__ == "__main__":
    main()
