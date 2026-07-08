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

            self._send_error(
                404,
                "NOT_FOUND",
                "Unknown endpoint.",
                details={"path": self.path},
            )

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

            self._send_error(
                404,
                "NOT_FOUND",
                "Unknown endpoint.",
                details={"path": self.path},
            )

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
                response = call()
                self._send_json(
                    _success_status_for_response(response, success_status),
                    response,
                )
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
                self._send_error(
                    409,
                    "JOB_NOT_CANCELLABLE",
                    str(exc),
                    details={"reason": str(exc)},
                )
            except ValueError as exc:
                self._send_error(
                    400,
                    "INVALID_REQUEST",
                    str(exc),
                    details={"reason": str(exc)},
                )

        def _read_json_body(self) -> dict[str, Any] | None:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.lower().startswith("application/json"):
                self._send_error(
                    415,
                    "UNSUPPORTED_MEDIA_TYPE",
                    "Content-Type must be application/json.",
                    details={"content_type": content_type or None},
                )
                return None

            length_header = self.headers.get("Content-Length", "0")
            try:
                length = int(length_header)
            except ValueError:
                self._send_error(
                    400,
                    "INVALID_JSON",
                    "Invalid Content-Length.",
                    details={"header": "Content-Length"},
                )
                return None

            if length > MAX_REQUEST_BYTES:
                self._send_error(
                    413,
                    "REQUEST_TOO_LARGE",
                    "Request body is too large.",
                    details={"max_request_bytes": MAX_REQUEST_BYTES},
                )
                return None

            raw_body = self.rfile.read(length)
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_error(
                    400,
                    "INVALID_JSON",
                    "Request body must be valid JSON.",
                    details={"body": "invalid_json"},
                )
                return None

            if not isinstance(payload, dict):
                self._send_error(
                    400,
                    "INVALID_JSON",
                    "Request JSON must be an object.",
                    details={"expected": "object"},
                )
                return None

            return payload

        def _send_schema_error(self, exc: SchemaValidationError) -> None:
            message = str(exc)
            self._send_error(
                400,
                exc.code,
                message,
                details=exc.details,
                field_errors=exc.field_errors,
            )

        def _send_error(
            self,
            status: int,
            code: str,
            message: str,
            details: dict[str, Any] | None = None,
            field_errors: dict[str, list[str]] | None = None,
            retryable: bool = False,
        ) -> None:
            error: dict[str, Any] = {
                "code": code,
                "message": message,
                "retryable": retryable,
            }
            if details is not None:
                error["details"] = details
            if field_errors:
                error["field_errors"] = field_errors
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


def _success_status_for_response(
    response: dict[str, Any], default_status: int
) -> int:
    if response.get("mode") == "dry_run" and "validation" in response:
        return 200
    return default_status


if __name__ == "__main__":
    main()
