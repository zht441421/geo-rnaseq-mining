# Local API Mock Server Runbook

This runbook is for local development and pre-Coze manual validation of the
`geo-rnaseq-mining` HTTP mock server.

The server is a mock-only interface. It does not execute real RNA-seq analysis,
does not run Snakemake, does not run Conda or `env create`, does not download
GEO/SRA data, and does not access external services.

## 1. Goal And Scope

Use this document to:

- Start the local HTTP mock server for development checks.
- Call each endpoint with `curl`.
- Inspect normal responses and error responses.
- Confirm the shape Coze will later call.

This document is not a production deployment guide. The current server only
exposes the in-memory mock layer.

Out of scope:

- Real RNA-seq analysis.
- Snakemake execution.
- Conda or Mamba execution.
- GEO/SRA download.
- External service calls.
- Secrets, authentication, persistence, queues, workers, or production storage.

## 2. Current Baseline

- Branch: `123`
- Commit: `38d46269eae872e925f02e9a93c2841d1984d723`
- Environment Solve #30: Success
- Phase 1.2 HTTP mock server is in the repository.
- HTTP mock server has passed local `unittest`.

Relevant files:

- `api/http_server.py`
- `api/mock_service.py`
- `api/job_schema.py`
- `api/state_machine.py`
- `tests/test_api_http_server.py`
- `docs/api-http-server.md`
- `docs/coze-api-contract.md`

## 3. Start The Server

The HTTP mock server uses only Python standard library modules.

Run from the repository root:

```bash
python -m api.http_server
```

PowerShell:

```powershell
python -m api.http_server
```

Default host and port, from `api/http_server.py`:

- Host: `127.0.0.1`
- Port: `8000`

Base URL:

```text
http://127.0.0.1:8000
```

Import behavior:

- Importing `api.http_server` does not listen on a port.
- The module only starts serving when explicitly run through `main()` or
  `python -m api.http_server`.
- `build_server()` creates a server object but does not call `serve_forever()`
  by itself.

Stop the local server with `Ctrl+C` in the terminal running it.

## 4. Health Check

Endpoint:

```http
GET /health
```

PowerShell recommended command:

```powershell
curl.exe -s http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "mock": true,
  "status": "ok"
}
```

Meaning:

- The local process is listening.
- The HTTP handler is responding.
- This does not prove that any production workflow is available.

## 5. Submit A Mock Job

Endpoint:

```http
POST /jobs
Content-Type: application/json
```

PowerShell `curl.exe` example:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/jobs `
  -H "Content-Type: application/json" `
  --data "{\"accession\":\"GSE123456\",\"analysis_type\":\"bulk\",\"species\":\"Homo sapiens\",\"output_format\":\"html\",\"requested_by\":\"coze-user@example.com\",\"notes\":\"Local mock validation\"}"
```

Bash example:

```bash
curl -s -X POST http://127.0.0.1:8000/jobs \
  -H "Content-Type: application/json" \
  --data '{
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "notes": "Local mock validation"
  }'
```

Request JSON:

```json
{
  "accession": "GSE123456",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "html",
  "requested_by": "coze-user@example.com",
  "notes": "Local mock validation"
}
```

Expected response shape:

```json
{
  "created_at": "2026-07-05T12:00:00+00:00",
  "events": [
    {
      "message": "Mock job accepted. No execution has started.",
      "status": "queued",
      "timestamp": "2026-07-05T12:00:00+00:00"
    }
  ],
  "job_id": "mock-job-000001",
  "message": "Mock job is queued; no real execution is scheduled.",
  "mock": true,
  "request": {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "notes": "Local mock validation",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "species": "Homo sapiens"
  },
  "status": "queued",
  "updated_at": "2026-07-05T12:00:00+00:00"
}
```

Field notes:

- `job_id`: in-memory mock identifier for later status/result/cancel calls.
- `status`: current mock status. New jobs start at `queued`.
- `created_at`: UTC timestamp from the mock service.
- `updated_at`: UTC timestamp for the most recent status change.
- `events`: status transition history.
- `mock`: always `true` for this server.

Stable success response fields for submit, status, and successful cancel:

- `job_id`
- `status`
- `request`
- `created_at`
- `updated_at`
- `events`
- `mock`
- `message`

Stable nested `request` fields:

- `accession`
- `analysis_type`
- `species`
- `output_format`
- `requested_by`
- `notes`

Each `events` item contains:

- `status`
- `timestamp`
- `message`

## 6. Query Job Status

Endpoint:

```http
GET /jobs/{job_id}
```

PowerShell:

```powershell
curl.exe -s http://127.0.0.1:8000/jobs/mock-job-000001
```

Expected response example:

```json
{
  "job_id": "mock-job-000001",
  "status": "queued",
  "mock": true,
  "message": "Mock job is queued; no real execution is scheduled.",
  "request": {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "notes": "Local mock validation"
  },
  "events": [
    {
      "status": "queued",
      "timestamp": "2026-07-05T12:00:00+00:00",
      "message": "Mock job accepted. No execution has started."
    }
  ],
  "created_at": "2026-07-05T12:00:00+00:00",
  "updated_at": "2026-07-05T12:00:00+00:00"
}
```

In Phase 1.2, the HTTP server does not run a worker and does not advance jobs
automatically. Jobs submitted over HTTP remain `queued` unless a test or local
Python caller advances the in-memory service.

## 7. Query Job Result

Endpoint:

```http
GET /jobs/{job_id}/result
```

PowerShell:

```powershell
curl.exe -s http://127.0.0.1:8000/jobs/mock-job-000001/result
```

### 7.1 Completed Response Example

A completed job returns HTTP `200`:

```json
{
  "artifacts": [
    {
      "mock_uri": "mock://mock-job-000001/mock-analysis-report.html",
      "name": "mock-analysis-report.html",
      "type": "html_report"
    },
    {
      "mock_uri": "mock://mock-job-000001/mock-result-summary.json",
      "name": "mock-result-summary.json",
      "type": "json_summary"
    }
  ],
  "job_id": "mock-job-000001",
  "limitations": [
    "Phase 1 mock result only; no Snakemake, Conda, GEO/SRA, or production analysis was run.",
    "No biological conclusion should be made from this mock response."
  ],
  "mock": true,
  "ready": true,
  "result_summary": {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "output_format": "html",
    "species": "Homo sapiens"
  },
  "status": "completed"
}
```

Completed result success fields:

- `job_id`
- `status`
- `ready`
- `mock`
- `result_summary`
- `artifacts`
- `limitations`

The `result_summary` object echoes `accession`, `analysis_type`, `species`,
and `output_format`. Each artifact includes `name`, `type`, and `mock_uri`.
Artifact URIs use the synthetic `mock://` scheme and are not filesystem paths.

Note: with the default HTTP-only flow, jobs do not become `completed`
automatically. This response shape is useful for Coze contract design and
unit tests.

### 7.2 Not Ready Response

For a newly submitted job, result lookup returns HTTP `409` with
`JOB_NOT_READY`:

```json
{
  "error": {
    "code": "JOB_NOT_READY",
    "details": {
      "job_id": "mock-job-000001",
      "status": "queued"
    },
    "message": "Mock result is only available after completed status.",
    "retryable": true
  }
}
```

## 8. Cancel Job

Endpoint:

```http
POST /jobs/{job_id}/cancel
```

PowerShell:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/jobs/mock-job-000001/cancel
```

Success response example:

```json
{
  "created_at": "2026-07-05T12:00:00+00:00",
  "updated_at": "2026-07-05T12:01:00+00:00",
  "request": {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "notes": "Local mock validation"
  },
  "job_id": "mock-job-000001",
  "status": "cancelled",
  "mock": true,
  "message": "Mock job was cancelled.",
  "events": [
    {
      "status": "queued",
      "timestamp": "2026-07-05T12:00:00+00:00",
      "message": "Mock job accepted. No execution has started."
    },
    {
      "status": "cancelled",
      "timestamp": "2026-07-05T12:01:00+00:00",
      "message": "Mock job cancelled."
    }
  ]
}
```

Non-cancellable scenario:

- A terminal job cannot be cancelled.
- Terminal statuses are `completed`, `failed`, and `cancelled`.
- The server returns HTTP `409` with `JOB_NOT_CANCELLABLE`.

Example:

```json
{
  "error": {
    "code": "JOB_NOT_CANCELLABLE",
    "details": {
      "reason": "cannot cancel job in completed status"
    },
    "message": "cannot cancel job in completed status",
    "retryable": false
  }
}
```

## 9. Error Scenarios

### 9.1 Invalid JSON

PowerShell:

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/jobs `
  -H "Content-Type: application/json" `
  --data "{not-json"
```

Expected HTTP status: `400`

```json
{
  "error": {
    "code": "INVALID_JSON",
    "details": {
      "body": "invalid_json"
    },
    "message": "Request body must be valid JSON.",
    "retryable": false
  }
}
```

### 9.2 Missing Or Wrong Content-Type

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/jobs `
  --data "{\"accession\":\"GSE123456\",\"analysis_type\":\"bulk\",\"species\":\"Homo sapiens\",\"output_format\":\"html\",\"requested_by\":\"coze-user@example.com\"}"
```

Expected HTTP status: `415`

```json
{
  "error": {
    "code": "UNSUPPORTED_MEDIA_TYPE",
    "details": {
      "content_type": null
    },
    "message": "Content-Type must be application/json.",
    "retryable": false
  }
}
```

### 9.3 Invalid analysis_type

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/jobs `
  -H "Content-Type: application/json" `
  --data "{\"accession\":\"GSE123456\",\"analysis_type\":\"shell\",\"species\":\"Homo sapiens\",\"output_format\":\"html\",\"requested_by\":\"coze-user@example.com\"}"
```

Expected HTTP status: `400`

```json
{
  "error": {
    "code": "INVALID_ANALYSIS_TYPE",
    "details": {
      "allowed_values": ["bulk", "scrna"]
    },
    "field_errors": {
      "analysis_type": ["must be one of: bulk, scrna"]
    },
    "message": "analysis_type must be one of: bulk, scrna",
    "retryable": false
  }
}
```

### 9.4 Invalid output_format

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/jobs `
  -H "Content-Type: application/json" `
  --data "{\"accession\":\"GSE123456\",\"analysis_type\":\"bulk\",\"species\":\"Homo sapiens\",\"output_format\":\"zip\",\"requested_by\":\"coze-user@example.com\"}"
```

Expected HTTP status with current implementation: `400`

```json
{
  "error": {
    "code": "INVALID_OUTPUT_FORMAT",
    "details": {
      "allowed_values": ["json", "markdown", "html"]
    },
    "field_errors": {
      "output_format": ["must be one of: json, markdown, html"]
    },
    "message": "output_format must be one of: json, markdown, html",
    "retryable": false
  }
}
```

Compatibility note:

- Coze contract target whitelist: `json`, `markdown`, `html`.
- Current mock implementation whitelist: `json`, `markdown`, `html`.
- `markdown` is accepted as a mock output format, but no real Markdown report is generated in Phase 1.
- `zip`, `pdf`, `txt`, `MARKDOWN`, and empty string are invalid.

### 9.5 Missing Required Field

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/jobs `
  -H "Content-Type: application/json" `
  --data "{\"accession\":\"GSE123456\",\"analysis_type\":\"bulk\",\"species\":\"Homo sapiens\",\"requested_by\":\"coze-user@example.com\"}"
```

Expected HTTP status: `400`

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "details": {
      "fields": ["output_format"]
    },
    "field_errors": {
      "output_format": ["missing required field"]
    },
    "message": "missing required field(s): output_format",
    "retryable": false
  }
}
```

### 9.6 Unknown Field

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/jobs `
  -H "Content-Type: application/json" `
  --data "{\"accession\":\"GSE123456\",\"analysis_type\":\"bulk\",\"species\":\"Homo sapiens\",\"output_format\":\"html\",\"requested_by\":\"coze-user@example.com\",\"command\":\"snakemake\"}"
```

Expected HTTP status: `400`

```json
{
  "error": {
    "code": "UNKNOWN_FIELD",
    "details": {
      "fields": ["command"]
    },
    "field_errors": {
      "command": ["unsupported field"]
    },
    "message": "unsupported field(s): command",
    "retryable": false
  }
}
```

### 9.7 Job Not Found

```powershell
curl.exe -s http://127.0.0.1:8000/jobs/missing-job
```

Expected HTTP status: `404`

```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "details": {
      "job_id": "missing-job"
    },
    "message": "No job exists for job_id missing-job.",
    "retryable": false
  }
}
```

### 9.8 Result Not Ready

```powershell
curl.exe -s http://127.0.0.1:8000/jobs/mock-job-000001/result
```

Expected HTTP status: `409`

```json
{
  "error": {
    "code": "JOB_NOT_READY",
    "details": {
      "job_id": "mock-job-000001",
      "status": "queued"
    },
    "message": "Mock result is only available after completed status.",
    "retryable": true
  }
}
```

### 9.9 Unknown Path

```powershell
curl.exe -s http://127.0.0.1:8000/not-a-real-endpoint
```

Expected HTTP status: `404`

```json
{
  "error": {
    "code": "NOT_FOUND",
    "details": {
      "path": "/not-a-real-endpoint"
    },
    "message": "Unknown endpoint.",
    "retryable": false
  }
}
```

## 10. Whitelisted Parameters

### analysis_type

Allowed values:

- `bulk`
- `scrna`

### output_format

Coze-facing contract target:

- `json`
- `markdown`
- `html`

Current mock implementation:

- `json`
- `markdown`
- `html`

The implementation and Coze contract now use the same whitelist. Phase 1 only
echoes the requested format in mock responses and does not generate real
format-specific reports.

### Other fields

Current submit schema:

- `accession`: safe accession-like string. It must not contain path separators,
  drive markers, `~`, or path traversal.
- `species`: safe display string.
- `requested_by`: safe caller identifier.
- `notes`: optional string, max 1000 characters.

Unknown fields are rejected.

## 11. Manual Validation Before Coze Integration

Recommended manual flow:

1. Start the server:

   ```powershell
   python -m api.http_server
   ```

2. In a second terminal, run the health check:

   ```powershell
   curl.exe -s http://127.0.0.1:8000/health
   ```

3. Submit a mock job:

   ```powershell
   curl.exe -s -X POST http://127.0.0.1:8000/jobs `
     -H "Content-Type: application/json" `
     --data "{\"accession\":\"GSE123456\",\"analysis_type\":\"bulk\",\"species\":\"Homo sapiens\",\"output_format\":\"html\",\"requested_by\":\"coze-user@example.com\"}"
   ```

4. Copy the returned `job_id`.

5. Poll status:

   ```powershell
   curl.exe -s http://127.0.0.1:8000/jobs/mock-job-000001
   ```

6. Try result:

   ```powershell
   curl.exe -s http://127.0.0.1:8000/jobs/mock-job-000001/result
   ```

   For the normal HTTP-only flow, expect `409 JOB_NOT_READY`.

7. Cancel the job:

   ```powershell
   curl.exe -s -X POST http://127.0.0.1:8000/jobs/mock-job-000001/cancel
   ```

8. Check error responses:

   - invalid JSON
   - missing or wrong `Content-Type`
   - invalid `analysis_type`
   - invalid `output_format`
   - missing required fields
   - unknown field
   - missing job
   - unknown path

9. Stop the server with `Ctrl+C`.

## 12. Safety Boundaries

The local HTTP mock server must remain inside these boundaries:

- It does not execute shell.
- It does not accept arbitrary commands.
- It does not accept arbitrary file paths.
- It does not read secrets.
- It does not access external network services.
- It does not run Snakemake.
- It does not run Conda or Mamba.
- It does not access GEO or SRA.
- It does not perform real computation.
- It only validates and exposes the mock layer.

`accession` is a plain string parameter. It is not a path, command, URL, or
Snakemake target.

## 13. Troubleshooting

### Port Is Already In Use

Symptom:

```text
OSError: [Errno 98] Address already in use
```

or a Windows socket bind error.

Action:

- Stop the process already using `127.0.0.1:8000`.
- Or start the server from Python using `build_server("127.0.0.1", <other_port>)`.
- Do not expose the mock server on a public interface.

### JSON Quote Problems

PowerShell quoting differs from Bash quoting.

Use `curl.exe` rather than `curl` in PowerShell, because `curl` may resolve to
`Invoke-WebRequest`.

For PowerShell, escape JSON quotes:

```powershell
--data "{\"accession\":\"GSE123456\",\"analysis_type\":\"bulk\",\"species\":\"Homo sapiens\",\"output_format\":\"html\",\"requested_by\":\"coze-user@example.com\"}"
```

For Bash, single-quote the JSON block:

```bash
--data '{"accession":"GSE123456","analysis_type":"bulk","species":"Homo sapiens","output_format":"html","requested_by":"coze-user@example.com"}'
```

### PowerShell curl vs curl.exe

In PowerShell:

- `curl` can be an alias for `Invoke-WebRequest`.
- `curl.exe` calls the actual curl executable.

Prefer:

```powershell
curl.exe -s http://127.0.0.1:8000/health
```

### Server Is Not Started

Symptom:

```text
Failed to connect
```

Action:

- Confirm `python -m api.http_server` is running in another terminal.
- Confirm the server is listening on `127.0.0.1:8000`.
- Confirm no firewall or local security tool is blocking loopback connections.

### job_id Does Not Exist

Symptom:

```json
{
  "error": {
    "code": "JOB_NOT_FOUND"
  }
}
```

Action:

- Submit a new job.
- Use the returned `job_id`.
- Remember that jobs are in-memory only. Restarting the server clears them.

### Result Not Ready

Symptom:

```json
{
  "error": {
    "code": "JOB_NOT_READY"
  }
}
```

Action:

- This is expected for jobs submitted only through HTTP in Phase 1.2.
- The server has no worker and does not advance jobs automatically.
- Coze should treat this as a retryable state until a future worker exists.

## 14. Future Migration Notes

Future phases can evaluate a real HTTP framework such as FastAPI, Flask, or
another production-ready service framework. That should happen only after the
mock contract is stable.

Before production use, the project needs:

- Authentication and authorization.
- Persistent job store.
- Task queue.
- Worker service.
- Result storage.
- Audit log.
- Quota and rate limiting.
- Operational logging and monitoring.
- Deployment and rollback plan.

This runbook does not represent a production deployment plan.
