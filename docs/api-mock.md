# Phase 1 本地 API Mock

本文档描述 `geo-rnaseq-mining` 产品化 Phase 1 的本地 API mock。该 mock 只用于验证 Coze 后续接入所需的数据结构、job schema、状态机和接口形态。

## 范围

Phase 1 只实现内存 mock：

- 不运行 Snakemake。
- 不运行 Conda 或 env create。
- 不下载 GEO/SRA。
- 不访问外部服务。
- 不执行 shell 命令。
- 不处理真实生产数据。
- 不引入 secrets。
- 不修改 GitHub Actions。
- 不修改 env YAML。
- 不修改现有分析代码。

当前实现位于：

- `api/job_schema.py`
- `api/state_machine.py`
- `api/mock_service.py`

测试位于：

- `tests/test_api_mock.py`

## 接口形态

Phase 1 暂不要求启动真实 HTTP 服务。`MockJobService` 提供与目标 API 对应的方法：

| 目标 API | Phase 1 mock 方法 |
|---|---|
| `POST /jobs` | `MockJobService.submit_job(payload)` |
| `GET /jobs/{job_id}` | `MockJobService.get_job(job_id)` |
| `GET /jobs/{job_id}/result` | `MockJobService.get_job_result(job_id)` |
| `POST /jobs/{job_id}/cancel` | `MockJobService.cancel_job(job_id)` |

另有 `advance_job(job_id, next_status)` 仅用于测试和前台原型验证，它不会启动 worker，也不会执行任何生产任务。

## Operator And Handoff Boundaries

The API mock is a contract and handoff tool only. It is responsible for:

- validating structured request fields;
- returning stable `job_id`, `status`, `message`, and `mock` fields;
- echoing the accepted `request`;
- exposing deterministic in-memory status transitions for tests;
- returning synthetic result metadata after a mock job reaches `completed`.

It is not responsible for:

- running Snakemake;
- creating or solving Conda environments;
- downloading GEO/SRA data;
- running a real RNA-seq pipeline;
- generating real Markdown or HTML reports;
- cancelling real operating-system processes;
- storing durable job state.

`output_format` is only an enum value in Phase 1. The mock echoes `json`,
`markdown`, or `html` in `request.output_format` and completed
`result_summary.output_format`. `markdown` and `html` do not cause report
rendering.

`result_summary`, `artifacts`, and `limitations` are mock placeholders.
Artifact URIs use `mock://` and are not local file paths, production paths, or
download URLs.

`cancel_job` only changes in-memory mock status to `cancelled`. It does not
terminate a worker, shell command, Snakemake run, Conda process, or RNA-seq
pipeline.

## Submit Job Schema

`POST /jobs` mock 接受以下字段：

```json
{
  "accession": "GSE123456",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "html",
  "requested_by": "coze-user@example.com",
  "notes": "Optional free text note"
}
```

字段约束：

- `accession`：普通 accession 字符串，不接受路径符号或路径穿越。
- `analysis_type`：白名单枚举，只允许 `bulk` 或 `scrna`。
- `species`：普通物种字符串，不接受路径符号。
- `output_format`：白名单枚举，只允许 `json`、`markdown` 或 `html`。
- `requested_by`：普通用户标识字符串。
- `notes`：可选说明文本，不参与执行。

不接受未知字段。因此诸如 `command`、`shell`、`input_path`、`workdir`、`snakefile` 等字段都会被拒绝。

## Coze-Facing Example Fixtures

The canonical minimal request that Coze can send in Phase 1 is:

```json
{
  "accession": "GSEMOCK001",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "json",
  "requested_by": "mock-coze-user"
}
```

This request intentionally omits optional `notes`. The mock response fills
`request.notes` with an empty string. The request does not include download
URLs, local paths, secrets, shell commands, or real production data access
instructions.

Additional valid `output_format` examples for contract tests:

- `markdown`
- `html`

Phase 1 only echoes these values. It does not generate real Markdown or HTML
reports.

Canonical invalid request examples:

```json
{
  "accession": "GSEMOCK001",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "zip",
  "requested_by": "mock-coze-user"
}
```

```json
{
  "accession": "GSEMOCK001",
  "analysis_type": "bulk",
  "species": "Homo sapiens",
  "output_format": "json"
}
```

The first request fails with `INVALID_OUTPUT_FORMAT` and field-level location
at `output_format`. The second fails with `INVALID_REQUEST` and field-level
location at `requested_by`.

## Negative Request Contract

Schema validation errors are stable enough for Coze-facing contract tests. The
in-memory mock raises `SchemaValidationError` with:

- `code`
- `message`
- `details`
- `field_errors`

Examples:

```json
{
  "code": "INVALID_OUTPUT_FORMAT",
  "message": "output_format must be one of: json, markdown, html",
  "details": {
    "allowed_values": ["json", "markdown", "html"]
  },
  "field_errors": {
    "output_format": ["must be one of: json, markdown, html"]
  }
}
```

Required fields are strict. Missing `accession`, `analysis_type`,
`output_format`, `species`, or `requested_by` is rejected and identifies the
missing field in `field_errors`.

Invalid `output_format` examples:

- `zip`
- `pdf`
- `txt`
- `MARKDOWN`
- empty string

Legal values remain:

- `json`
- `markdown`
- `html`

`markdown` and `html` are mock format values only. Phase 1 does not generate
real Markdown or HTML reports.

## Happy-Path Response Contract

Successful `submit_job`, `get_job`, and `cancel_job` calls return the same
status response shape:

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

Stable top-level fields:

- `job_id`
- `status`
- `request`
- `created_at`
- `updated_at`
- `events`
- `mock`
- `message`

Stable `request` fields:

- `accession`
- `analysis_type`
- `species`
- `output_format`
- `requested_by`
- `notes`

Each event contains:

- `status`
- `timestamp`
- `message`

`get_job_result` returns a not-ready shape until the job reaches `completed`:

```json
{
  "job_id": "mock-job-000001",
  "status": "queued",
  "ready": false,
  "mock": true,
  "message": "Mock result is only available after completed status."
}
```

Completed mock results expose these stable top-level fields:

- `job_id`
- `status`
- `ready`
- `mock`
- `result_summary`
- `artifacts`
- `limitations`

`result_summary` echoes `accession`, `analysis_type`, `species`, and
`output_format`. Artifacts remain synthetic `mock://` references; they are not
filesystem paths and do not represent generated production reports.

## Job 状态机

状态集合：

- `queued`
- `validating`
- `ready`
- `running`
- `summarizing`
- `completed`
- `failed`
- `cancelled`

允许的正向状态迁移：

```text
queued -> validating -> ready -> running -> summarizing -> completed
```

各非终态均可转为：

```text
failed
cancelled
```

终态：

- `completed`
- `failed`
- `cancelled`

终态不允许继续迁移。

## 安全边界

安全边界在 schema 和 service 层体现：

- `analysis_type` 使用枚举白名单。
- `output_format` 使用枚举白名单。
- request 不接受任意路径字段。
- request 不接受任意命令字段。
- `accession` 只是普通字符串，不拼接 shell 命令。
- service 不调用 `subprocess`、`os.system`、Snakemake、Conda、Mamba 或网络服务。
- mock result 使用 `mock://` URI，不暴露真实文件路径。
- 所有状态变化均为内存对象变更。

## 示例

```python
from api import JobStatus, MockJobService

service = MockJobService()

created = service.submit_job(
    {
        "accession": "GSE123456",
        "analysis_type": "bulk",
        "species": "Homo sapiens",
        "output_format": "html",
        "requested_by": "coze-user@example.com",
        "notes": "Phase 1 mock only",
    }
)

job_id = created["job_id"]
service.advance_job(job_id, JobStatus.VALIDATING)
service.advance_job(job_id, JobStatus.READY)
service.advance_job(job_id, JobStatus.RUNNING)
service.advance_job(job_id, JobStatus.SUMMARIZING)
service.advance_job(job_id, JobStatus.COMPLETED)

result = service.get_job_result(job_id)
```

## 测试

运行 Phase 1 mock 测试：

```bash
python -m unittest tests.test_api_mock -v
```

该测试只验证标准库内存 mock，不运行 Snakemake、Conda、env create、GEO/SRA 下载或任何生产任务。
