# Phase 1 HTTP Mock Server

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

Successful HTTP responses are stable enough for local Coze integration tests.
They use `Content-Type: application/json; charset=utf-8` and
`Cache-Control: no-store`.

The server must not include Python tracebacks, internal exception objects,
absolute local paths, production paths, or secrets in JSON responses.

### HTTP Status And Header Checklist

Success status codes:

| Endpoint | Status |
|---|---:|
| `GET /health` | `200` |
| `POST /jobs` | `201` |
| `GET /jobs/{job_id}` | `200` |
| `GET /jobs/{job_id}/result` when completed | `200` |
| `POST /jobs/{job_id}/cancel` when cancellable | `200` |

Common error status codes:

| Status | Typical reason |
|---:|---|
| `400` | Invalid JSON, schema validation error, unknown field |
| `404` | Unknown endpoint or missing job |
| `409` | Result not ready or job not cancellable |
| `413` | Request body too large |
| `415` | Missing or non-JSON `Content-Type` for `POST /jobs` |

Response headers for JSON responses:

- `Content-Type: application/json; charset=utf-8`
- `Cache-Control: no-store`

`POST /jobs` requires:

```http
Content-Type: application/json
```

Missing or incorrect content type returns `415`:

```json
{
  "error": {
    "code": "UNSUPPORTED_MEDIA_TYPE",
    "message": "Content-Type must be application/json.",
    "retryable": false,
    "details": {
      "content_type": null
    }
  }
}
```

### Canonical Coze Request Example

The smallest Coze-facing valid request uses only required schema fields:

```json
{
  "accession": "GSEMOCK001",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "json",
  "requested_by": "mock-coze-user"
}
```

The mock accepts `json`, `markdown`, and `html` as `output_format` values.
`zip` remains invalid. Phase 1 only echoes `output_format`; it does not
generate real format-specific reports.

Canonical invalid examples for HTTP contract tests:

- `output_format: "zip"` returns `400` with `INVALID_OUTPUT_FORMAT`.
- Missing `requested_by` returns `400` with `INVALID_REQUEST`.

Both error responses include `error.code`, `error.message`,
`error.retryable`, `error.details`, and `error.field_errors`.

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

Success response fields:

- `job_id`
- `status`
- `request`
- `created_at`
- `updated_at`
- `events`
- `mock`
- `message`

The nested `request` object includes:

- `accession`
- `analysis_type`
- `species`
- `output_format`
- `requested_by`
- `notes`

Each `events` item includes:

- `status`
- `timestamp`
- `message`

### GET /jobs/{job_id}

Returns the current mock job status.

Success status: `200`. The response uses the same status response fields as
`POST /jobs`.

Unknown job status: `404` with `JOB_NOT_FOUND`.

### GET /jobs/{job_id}/result

Completed jobs return `200` and a mock result.

Completed result fields:

- `job_id`
- `status`
- `ready`
- `mock`
- `result_summary`
- `artifacts`
- `limitations`

The `result_summary` object includes `accession`, `analysis_type`, `species`,
and `output_format`. Each artifact includes `name`, `type`, and `mock_uri`.
Artifacts are mock placeholders only. They do not point to local files,
download URLs, or generated production reports.

Incomplete jobs return `409` with `JOB_NOT_READY`.

Unknown jobs return `404` with `JOB_NOT_FOUND`.

### POST /jobs/{job_id}/cancel

Cancellable jobs return `200` and status `cancelled`.

Successful cancellation uses the same status response fields as `POST /jobs`.

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

Schema errors include field-level details:

```json
{
  "error": {
    "code": "INVALID_OUTPUT_FORMAT",
    "message": "output_format must be one of: json, markdown, html",
    "retryable": false,
    "details": {
      "allowed_values": ["json", "markdown", "html"]
    },
    "field_errors": {
      "output_format": ["must be one of: json, markdown, html"]
    }
  }
}
```

Implemented error cases:

- `NOT_FOUND`
- `INVALID_JSON`
- `UNSUPPORTED_MEDIA_TYPE`
- `REQUEST_TOO_LARGE`
- `UNKNOWN_FIELD`
- `INVALID_ACCESSION`
- `INVALID_ANALYSIS_TYPE`
- `INVALID_OUTPUT_FORMAT`
- `INVALID_REQUEST`
- `JOB_NOT_FOUND`
- `JOB_NOT_READY`
- `JOB_NOT_CANCELLABLE`

`POST /jobs` requires `Content-Type: application/json`. Missing or non-JSON
content types return `415` with `UNSUPPORTED_MEDIA_TYPE`.

## Phase 1.4e Dry-Run Validation Reports

`POST /jobs` also accepts dry-run execution request intent for validation
only. Payloads with fields such as `mode`, `dataset_accession`,
`operator_approved`, or `allow_*` are passed to
`validate_dry_run_request(payload)` by the mock service.

Dry-run validation reports return `200` because no job is created:

```json
{
  "status": "accepted",
  "mode": "dry_run",
  "validation": {
    "accepted": true,
    "mode": "dry_run",
    "rejection_reasons": [],
    "warnings": []
  },
  "execution": "not_started",
  "mock": true,
  "message": "Dry-run request accepted for validation only; no real execution has started."
}
```

Rejected dry-run validation reports keep the same shape with
`status: "rejected"` and deterministic `validation.rejection_reasons`.

This path does not allocate `job_id`, start a worker, run Snakemake, run
RNA-seq processing, download GEO data, call real Coze, access external
network services, write artifacts, write a database, or implement a real
execution runner.

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

Run the API mock and HTTP server tests:

```bash
python -m unittest tests.test_api_mock tests.test_api_http_server -v
```

The HTTP tests use an ephemeral loopback port and do not access external
network services.
