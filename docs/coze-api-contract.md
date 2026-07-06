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

### 3.6 Error Response

```json
{
  "error": {
    "code": "INVALID_ANALYSIS_TYPE",
    "message": "analysis_type must be one of: bulk, scrna",
    "retryable": false
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
| `INTERNAL_ERROR` | Unexpected backend error | maybe |

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

## 9. Security Boundaries

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

## 10. Migration Points From Mock To Real Backend

Before moving from mock to real backend execution, the following pieces must be designed and implemented:

- `auth`: caller authentication, service tokens, user identity mapping, and token rotation.
- `persistent job store`: durable job metadata, state transitions, request snapshots, and result metadata.
- `task queue`: async dispatch, retry policy, cancellation, concurrency limits, and worker leases.
- `worker`: isolated execution service that can run only whitelisted pipelines.
- `result storage`: artifact registry, report URLs, retention policy, and access control.
- `audit log`: immutable job events, input hashes, config snapshots, software versions, and operator actions.
- `quota / rate limit`: per-user and per-project limits for submissions, runtime, storage, and concurrent jobs.

Real execution migration must preserve the Phase 1 safety contract: no arbitrary commands, no arbitrary paths, no Coze-side secrets, and no direct shell execution from Coze.
