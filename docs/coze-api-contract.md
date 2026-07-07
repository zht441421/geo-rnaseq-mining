# Coze API Contract Draft

This document defines the Phase 1.1 contract draft between a Coze front end and the `geo-rnaseq-mining` backend API layer.

The current API remains a mock contract. It validates request and response shapes for later integration work, but it does not run real analysis. It does not run Snakemake, Conda, GEO, SRA, shell commands, downloads, or production jobs.

## 1. Goal

The goal is to give Coze and backend developers a shared, stable contract for the Phase 1 local API mock:

- Coze can collect structured job parameters.
- Coze can submit a mock job.
- Coze can poll job status.
- Coze can fetch a mock result after completion.
- Coze can request cancellation for cancellable jobs.
- The backend can reject unsupported fields, invalid enum values, invalid accessions, and unsafe path-like inputs.

This contract is intentionally narrow. It is not a real production execution API yet.

## 2. Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/jobs` | Submit a mock job |
| `GET` | `/jobs/{job_id}` | Get mock job status |
| `GET` | `/jobs/{job_id}/result` | Get mock job result |
| `POST` | `/jobs/{job_id}/cancel` | Cancel a cancellable mock job |

## 3. Request And Response Examples

### 3.0 Canonical Coze Fixture Examples

These examples are the smallest Coze-facing fixtures for Phase 1 contract
checks. They are inline examples only; no real Coze call is made.

Minimal valid job request:

```json
{
  "accession": "GSEMOCK001",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "json",
  "requested_by": "mock-coze-user"
}
```

Coze should send only structured fields. It should not send shell commands,
file paths, download URLs, secrets, or pipeline-specific execution arguments.
`notes` is optional and defaults to an empty string in the mock response.

Invalid request with unsupported `output_format`:

```json
{
  "accession": "GSEMOCK001",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "zip",
  "requested_by": "mock-coze-user"
}
```

Expected error shape:

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

Invalid request missing `requested_by`:

```json
{
  "accession": "GSEMOCK001",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "json"
}
```

Expected error shape:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "missing required field(s): requested_by",
    "retryable": false,
    "details": {
      "fields": ["requested_by"]
    },
    "field_errors": {
      "requested_by": ["missing required field"]
    }
  }
}
```

`field_errors` appears only in failure responses. Successful responses use the
status/result shapes below.

### 3.1 Submit Job Request

```http
POST /jobs
Content-Type: application/json
```

```json
{
  "accession": "GSE123456",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "html",
  "requested_by": "coze-user@example.com",
  "notes": "Phase 1 mock only"
}
```

### 3.2 Submit Job Response

```json
{
  "job_id": "mock-job-000001",
  "status": "queued",
  "request": {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "notes": "Phase 1 mock only"
  },
  "created_at": "2026-07-05T06:00:00+00:00",
  "updated_at": "2026-07-05T06:00:00+00:00",
  "events": [
    {
      "status": "queued",
      "timestamp": "2026-07-05T06:00:00+00:00",
      "message": "Mock job accepted. No execution has started."
    }
  ],
  "mock": true,
  "message": "Mock job is queued; no real execution is scheduled."
}
```

### 3.3 Status Response

```http
GET /jobs/mock-job-000001
```

```json
{
  "job_id": "mock-job-000001",
  "status": "running",
  "request": {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "notes": "Phase 1 mock only"
  },
  "created_at": "2026-07-05T06:00:00+00:00",
  "updated_at": "2026-07-05T06:02:00+00:00",
  "events": [
    {
      "status": "queued",
      "timestamp": "2026-07-05T06:00:00+00:00",
      "message": "Mock job accepted. No execution has started."
    },
    {
      "status": "running",
      "timestamp": "2026-07-05T06:02:00+00:00",
      "message": "Mock job moved to running. No execution was run."
    }
  ],
  "mock": true,
  "message": "Mock running state; no shell or workflow is running."
}
```

### 3.4 Result Response

```http
GET /jobs/mock-job-000001/result
```

```json
{
  "job_id": "mock-job-000001",
  "status": "completed",
  "ready": true,
  "mock": true,
  "result_summary": {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html"
  },
  "artifacts": [
    {
      "name": "mock-analysis-report.html",
      "type": "html_report",
      "mock_uri": "mock://mock-job-000001/mock-analysis-report.html"
    },
    {
      "name": "mock-result-summary.json",
      "type": "json_summary",
      "mock_uri": "mock://mock-job-000001/mock-result-summary.json"
    }
  ],
  "limitations": [
    "Phase 1 mock result only; no Snakemake, Conda, GEO/SRA, or production analysis was run.",
    "No biological conclusion should be made from this mock response."
  ]
}
```

If the job is not completed, the result endpoint returns:

```json
{
  "job_id": "mock-job-000001",
  "status": "running",
  "ready": false,
  "mock": true,
  "message": "Mock result is only available after completed status."
}
```

### 3.5 Cancel Response

```http
POST /jobs/mock-job-000001/cancel
```

```json
{
  "job_id": "mock-job-000001",
  "status": "cancelled",
  "request": {
    "accession": "GSE123456",
    "analysis_type": "bulk",
    "species": "Homo sapiens",
    "output_format": "html",
    "requested_by": "coze-user@example.com",
    "notes": "Phase 1 mock only"
  },
  "created_at": "2026-07-05T06:00:00+00:00",
  "updated_at": "2026-07-05T06:01:00+00:00",
  "events": [
    {
      "status": "queued",
      "timestamp": "2026-07-05T06:00:00+00:00",
      "message": "Mock job accepted. No execution has started."
    },
    {
      "status": "cancelled",
      "timestamp": "2026-07-05T06:01:00+00:00",
      "message": "Mock job cancelled."
    }
  ],
  "mock": true,
  "message": "Mock job was cancelled."
}
```

### 3.6 Happy-Path Field Stability

Coze callers can treat the following success fields as stable in Phase 1.

`POST /jobs`, `GET /jobs/{job_id}`, and successful
`POST /jobs/{job_id}/cancel` responses use the same status response shape:

- `job_id`
- `status`
- `request`
- `created_at`
- `updated_at`
- `events`
- `mock`
- `message`

The nested `request` object always includes:

- `accession`
- `analysis_type`
- `species`
- `output_format`
- `requested_by`
- `notes`

Each item in `events` includes:

- `status`
- `timestamp`
- `message`

The completed result response uses these top-level fields:

- `job_id`
- `status`
- `ready`
- `mock`
- `result_summary`
- `artifacts`
- `limitations`

The `result_summary` object echoes `accession`, `analysis_type`, `species`, and
`output_format`. Artifact objects include `name`, `type`, and `mock_uri`.

Expected success HTTP status codes:

- `POST /jobs`: `201`
- `GET /jobs/{job_id}`: `200`
- `GET /jobs/{job_id}/result` when completed: `200`
- `POST /jobs/{job_id}/cancel` when cancellable: `200`

All Phase 1 success responses include `mock: true`. `markdown` and `html`
remain mock output values only; no real Markdown or HTML report is generated.
Coze should save `job_id` after `POST /jobs`, read `status` and `message` from
status responses, and read the echoed `output_format` from
`request.output_format` or completed `result_summary.output_format`.

### 3.7 Error Response

```json
{
  "error": {
    "code": "INVALID_ANALYSIS_TYPE",
    "message": "analysis_type must be one of: bulk, scrna",
    "retryable": false,
    "details": {
      "allowed_values": ["bulk", "scrna"]
    },
    "field_errors": {
      "analysis_type": ["must be one of: bulk, scrna"]
    }
  }
}
```

Recommended common error envelope:

```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "No job exists for job_id mock-job-999999.",
    "retryable": false,
    "details": {
      "job_id": "mock-job-999999"
    }
  }
}
```

## 4. Job Schema

| Field | Type | Required | Description |
|---|---|---:|---|
| `accession` | string | yes | GEO-style accession or other safe accession-like identifier |
| `analysis_type` | string enum | yes | Analysis mode whitelist |
| `species` | string | yes | Species display name |
| `output_format` | string enum | yes | Preferred mock result format |
| `requested_by` | string | yes | Coze user or caller identifier |
| `notes` | string | no | Optional free text note |

Example schema:

```json
{
  "accession": "GSE123456",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "html",
  "requested_by": "coze-user@example.com",
  "notes": "Optional note"
}
```

## 5. Whitelist Constraints

### 5.1 analysis_type

Allowed values:

- `bulk`
- `scrna`

Rejected examples:

- `snakemake`
- `shell`
- `custom`
- `../../bulk`

### 5.2 output_format

Allowed values for the Coze contract:

- `json`
- `markdown`
- `html`

Current Phase 1 mock implementation supports `json`, `markdown`, and `html`. The mock only echoes the requested `output_format`; it does not generate a real Markdown report.

Rejected examples:

- `pdf; rm -rf`
- `C:/temp/output`
- `custom_script`

## 6. Job Statuses

| Status | Meaning |
|---|---|
| `queued` | Job accepted and waiting in the mock queue |
| `validating` | Mock validation state |
| `ready` | Mock job is valid and ready for a future worker |
| `running` | Mock running state; no real execution is running |
| `summarizing` | Mock summarization state |
| `completed` | Mock job completed and mock result is available |
| `failed` | Mock job failed |
| `cancelled` | Mock job was cancelled |

Expected happy path:

```text
queued -> validating -> ready -> running -> summarizing -> completed
```

Terminal statuses:

- `completed`
- `failed`
- `cancelled`

Coze should stop polling once a terminal status is reached.

## 7. Error Codes

| Code | Meaning | Retryable |
|---|---|---:|
| `INVALID_ACCESSION` | `accession` is missing, malformed, or path-like | no |
| `INVALID_ANALYSIS_TYPE` | `analysis_type` is not one of the whitelist values | no |
| `INVALID_OUTPUT_FORMAT` | `output_format` is not one of the whitelist values | no |
| `UNKNOWN_FIELD` | Request contains unsupported fields | no |
| `JOB_NOT_FOUND` | Requested `job_id` does not exist | no |
| `JOB_NOT_READY` | Result requested before job completion | yes |
| `JOB_NOT_CANCELLABLE` | Cancel requested for terminal or non-cancellable status | no |
| `UNSUPPORTED_MEDIA_TYPE` | JSON body endpoint received a missing or non-JSON `Content-Type` | no |
| `INTERNAL_ERROR` | Unexpected backend error | maybe |

Schema-style request errors should include field-level information when a
specific field caused the error:

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

Coze should treat `field_errors` as the preferred source for telling the user
which input needs correction. `details` is for structured metadata such as
allowed values, missing fields, unknown fields, paths, or job IDs.

## 8. Coze Calling Recommendations

Recommended Coze flow:

1. Collect parameters from the user.
2. Validate obvious missing values in the Coze prompt flow.
3. Call `POST /jobs`.
4. Store the returned `job_id`.
5. Poll `GET /jobs/{job_id}` with a conservative interval.
6. If status is `queued`, `validating`, `ready`, `running`, or `summarizing`, continue polling.
7. If status is `completed`, call `GET /jobs/{job_id}/result`.
8. If status is `failed`, explain the failure message and ask the user whether to revise inputs.
9. If status is `cancelled`, tell the user the mock job was cancelled and no result is available.
10. Do not invent biological conclusions from mock results.

Suggested user-facing language:

- For `queued`: "Your mock analysis request has been accepted and is waiting."
- For `running`: "The mock job is in a running-like state. No real analysis is being executed in Phase 1."
- For `completed`: "The mock job completed and a synthetic result is available."
- For `failed`: "The request failed validation or mock processing. Please review the error."
- For `cancelled`: "The mock job was cancelled. No result was produced."

## 9. Coze Handoff Handling Rules

These rules are for future Coze prompt-flow or tool-call wiring. The current
repository has not connected to a real Coze service.

### Success Responses

After `POST /jobs`, Coze must save `job_id`. All later status, result, and
cancel calls use that value.

For user-facing progress messages, Coze should read:

- `status`
- `message`
- `request.output_format`

For completed results, Coze may also read:

- `result_summary.output_format`
- `artifacts`
- `limitations`

Successful responses do not include `field_errors`. Coze should not try to read
`field_errors` unless the response contains an `error` object.

### Failure Responses

When a response contains `error`, Coze should read:

- `error.code`
- `error.message`
- `error.retryable`
- `error.field_errors`, when present
- `error.details`, when present

Use `field_errors` first for user-correctable input problems. For example,
`output_format` errors should prompt the user to choose one of `json`,
`markdown`, or `html`.

If `error.retryable` is `false`, Coze should ask the user to correct the input
instead of automatically retrying the same request.

If `error.retryable` is `true`, Coze may retry conservatively or tell the user
that the mock state is not ready yet. In Phase 1, `JOB_NOT_READY` is expected
for jobs that have not reached `completed`.

### Output Format Rules

Legal values remain:

- `json`
- `markdown`
- `html`

Rejected values include:

- `zip`
- `pdf`
- `txt`
- `MARKDOWN`
- empty string

`markdown` and `html` are Phase 1 mock output values only. The mock echoes
them in `request.output_format` and `result_summary.output_format`; it does
not generate real Markdown or HTML reports.

### Mock Result Rules

`result_summary`, `artifacts`, and `limitations` are mock placeholders.
Artifact URIs use the synthetic `mock://` scheme. They are not filesystem
paths, signed URLs, download links, or production report locations.

Coze should not claim that a biological result, real report, GEO/SRA download,
Snakemake run, Conda run, or RNA-seq pipeline execution has happened.

### Current Non-Production Boundaries

- No real Coze integration is active.
- No real RNA-seq pipeline is run.
- No real GEO/SRA data is downloaded.
- No shell command is accepted from Coze.
- No secrets are exposed to Coze.

## 10. Security Boundaries

Security boundaries for Coze and backend integration:

- Coze does not directly execute shell.
- The API does not accept arbitrary commands.
- The API does not accept arbitrary file paths.
- The API does not expose secrets.
- The API does not download external data.
- The API does not run Snakemake.
- The API does not run Conda or Mamba.
- The API does not query GEO or SRA.
- The current contract only connects to the mock layer.
- `accession` is treated as a plain string parameter, not as a command, URL, or path.
- `analysis_type` and `output_format` must be enums.
- Unknown fields should be rejected rather than ignored.

## 11. Migration Points From Mock To Real Backend

Before moving from mock to real backend execution, the following pieces must be designed and implemented:

- `auth`: caller authentication, service tokens, user identity mapping, and token rotation.
- `persistent job store`: durable job metadata, state transitions, request snapshots, and result metadata.
- `task queue`: async dispatch, retry policy, cancellation, concurrency limits, and worker leases.
- `worker`: isolated execution service that can run only whitelisted pipelines.
- `result storage`: artifact registry, report URLs, retention policy, and access control.
- `audit log`: immutable job events, input hashes, config snapshots, software versions, and operator actions.
- `quota / rate limit`: per-user and per-project limits for submissions, runtime, storage, and concurrent jobs.

Real execution migration must preserve the Phase 1 safety contract: no arbitrary commands, no arbitrary paths, no Coze-side secrets, and no direct shell execution from Coze.
