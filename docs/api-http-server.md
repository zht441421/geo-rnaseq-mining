# Phase 1.2 HTTP Mock Server

This document describes the local HTTP entrypoint for the Phase 1 API mock.
It is intended for local development and Coze integration shape checks only.

The server is still a mock. It does not run production analysis, Snakemake,
Conda, GEO, SRA, shell commands, downloads, or external service calls.

## Files

- `api/http_server.py`
- `tests/test_api_http_server.py`

The implementation uses only Python standard library modules:

- `http.server`
- `json`
- `http.client` in tests
- `threading` in tests
- `unittest` in tests

No FastAPI, Flask, uvicorn, or third-party dependency is introduced.

## Import Behavior

Importing `api.http_server` does not listen on a port.

The module exposes:

- `make_handler(service=None)`: create a request handler class bound to a `MockJobService`.
- `build_server(host="127.0.0.1", port=8000, service=None)`: build a server without starting the serve loop.
- `main()`: explicit local development entrypoint.

The server only starts if the caller explicitly invokes `serve_forever()` on a built server or runs the module as a script.

## Endpoints

| Method | Path | Result |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/jobs` | Submit a mock job |
| `GET` | `/jobs/{job_id}` | Fetch mock job status |
| `GET` | `/jobs/{job_id}/result` | Fetch mock result |
| `POST` | `/jobs/{job_id}/cancel` | Cancel cancellable mock job |

All requests and responses use JSON.

## Response Behavior

### GET /health

Returns:

```json
{
  "status": "ok",
  "mock": true
}
```

### POST /jobs

Accepts the existing mock schema:

```json
{
  "accession": "GSE123456",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "html",
  "requested_by": "coze-user@example.com",
  "notes": "HTTP mock only"
}
```

Allowed `output_format` values:

- `json`
- `markdown`
- `html`

Success status: `201`.

### GET /jobs/{job_id}

Returns the current mock job status.

Unknown job status: `404` with `JOB_NOT_FOUND`.

### GET /jobs/{job_id}/result

Completed jobs return `200` and a mock result.

Incomplete jobs return `409` with `JOB_NOT_READY`.

Unknown jobs return `404` with `JOB_NOT_FOUND`.

### POST /jobs/{job_id}/cancel

Cancellable jobs return `200` and status `cancelled`.

Terminal jobs return `409` with `JOB_NOT_CANCELLABLE`.

Unknown jobs return `404` with `JOB_NOT_FOUND`.

## Error Envelope

Errors use this shape:

```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "No job exists for job_id missing-job.",
    "retryable": false,
    "details": {
      "job_id": "missing-job"
    }
  }
}
```

Implemented error cases:

- `NOT_FOUND`
- `INVALID_JSON`
- `REQUEST_TOO_LARGE`
- `UNKNOWN_FIELD`
- `INVALID_ACCESSION`
- `INVALID_ANALYSIS_TYPE`
- `INVALID_OUTPUT_FORMAT`
- `INVALID_REQUEST`
- `JOB_NOT_FOUND`
- `JOB_NOT_READY`
- `JOB_NOT_CANCELLABLE`

## Safety Boundaries

The HTTP server preserves the Phase 1 mock boundaries:

- It only exposes `MockJobService`.
- It does not start on import.
- It does not invoke shell commands.
- It does not call Snakemake, Conda, Mamba, GEO, or SRA.
- It does not download data.
- It does not read secrets.
- It does not accept arbitrary file paths.
- It rejects unknown request fields through the existing schema validation.
- It treats `accession` as a plain string parameter.
- It uses mock result URIs instead of filesystem paths.

## Local Development Example

The module can be started explicitly for local experiments:

```bash
python -m api.http_server
```

This binds to `127.0.0.1:8000` by default. This is for local development only.
Do not expose it as a production service.

## Tests

Run the Phase 1 and Phase 1.2 tests:

```bash
python -m unittest tests.test_api_mock tests.test_api_http_server -v
```

The HTTP tests use an ephemeral loopback port and do not access external
network services.
