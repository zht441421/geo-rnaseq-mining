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
- `output_format`：白名单枚举，只允许 `json`、`html` 或 `zip`。
- `requested_by`：普通用户标识字符串。
- `notes`：可选说明文本，不参与执行。

不接受未知字段。因此诸如 `command`、`shell`、`input_path`、`workdir`、`snakefile` 等字段都会被拒绝。

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
