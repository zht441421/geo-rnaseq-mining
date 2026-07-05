# geo-rnaseq-mining 产品化方案

本文档描述 `geo-rnaseq-mining` 从可复现科研工作流走向产品化服务的下一阶段方案。本文只用于规划，不代表已经接入 Coze、后端 API、任务队列或生产执行服务；本文不触发、不运行、也不声明任何生产任务已经完成。

## 1. 当前 CI / env 验证基线

当前稳定基线：

- 分支：`123`
- 提交：`de0ea939728305ef18a91b505a80127f5d050d33`
- 本地 `HEAD` 与 `origin/123` 完全一致
- 工作区无已跟踪文件改动
- `Environment Create Smoke #13`：成功
- `Environment Create Smoke #13`：13 个 jobs 全部完成
- `auto-activate-base` warning 已清理
- `defaults` channel implicit warning 已清理
- `actions/checkout` 已升级到 Node.js 24 runtime 版本
- `conda-incubator/setup-miniconda@v3` 仍可能产生 Node.js 20 deprecated warning，等待上游提供明确稳定的 Node.js 24 runtime 版本

当前验证范围边界：

- 已验证 workflow 层面的 Conda environment create smoke。
- 已验证 13 个环境在 GitHub Actions runner 上可完成 smoke 检查。
- 不等于真实 GEO/SRA 生产下载已经验证。
- 不等于真实 FASTQ 定量、R/Bioconductor/DESeq2 或真实生产数据端到端分析已经验证。
- 不等于产品化 API、队列、权限、任务隔离或多用户并发已经实现。

## 2. 产品化目标

下一阶段目标是把当前 Snakemake/Conda 科研工作流包装为受控的任务服务，使用户可以通过 Coze 前台提交标准化分析请求，由后端 API 进行参数校验、任务排队、执行调度和结果交付。

产品化原则：

- Coze 只作为用户交互入口，不直接执行 shell。
- 后端只允许白名单 pipeline。
- 后端不接受任意命令。
- 后端不接受任意文件系统路径。
- secrets、tokens、云存储凭据和执行权限只放在后端。
- 所有任务都有可审计的 `job_id`、输入快照、配置快照、日志、状态迁移和结果清单。
- 正式生物学分析仍必须遵守人工审核优先原则，不能由系统自动推断 case/control、subject、contrast、dataset 合并策略或 cell type 映射。

## 3. 总体架构

```text
Coze 前台
  |
  | HTTPS / signed API call
  v
后端 API 服务
  |
  | validate / persist / enqueue
  v
任务队列
  |
  | job lease / retry policy / cancel signal
  v
执行服务
  |
  | whitelist pipeline adapter
  v
Snakemake / Conda 执行层
  |
  | logs / artifacts / reports / status events
  v
结果存储与交付
```

### 3.1 Coze 前台

职责：

- 收集用户意图和结构化输入。
- 展示任务创建、状态查询、取消和结果领取入口。
- 展示后端返回的参数错误、运行状态、失败原因和结果链接。
- 引导用户完成人工审核文件准备，但不替用户决定正式分组和分析策略。

禁止：

- 不直接执行 shell。
- 不拼接命令行。
- 不持有后端 secrets。
- 不传递任意本地路径。

### 3.2 后端 API 服务

职责：

- 提供任务提交、状态查询、结果查询和取消接口。
- 验证输入 schema。
- 将用户输入规范化为内部 job spec。
- 只允许白名单 pipeline。
- 为每个任务创建隔离工作目录。
- 写入参数快照、输入清单和审计记录。
- 将任务投递到队列。

建议初始技术形态：

- `FastAPI` 或等价轻量 HTTP API。
- `SQLite` 或 `PostgreSQL` 保存 job 元数据。
- 本地文件系统或对象存储保存结果包。
- Phase 1 可使用内存队列或 SQLite-backed mock queue。

### 3.3 任务队列

职责：

- 管理 job 排队、领取、运行、取消和失败重试。
- 限制并发数量。
- 记录状态迁移事件。
- 避免 API 请求线程直接执行长任务。

建议演进：

- Phase 1：本地 mock queue。
- Phase 2：`Redis + RQ`、`Celery` 或等价队列。
- Phase 3：增加队列可观测性和取消信号。
- Phase 4：按用户、项目、资源规格做限流。

### 3.4 Snakemake / Conda 执行层

职责：

- 只通过后端白名单 adapter 启动。
- 使用固定入口，例如 `geo-rnaseq-mining/workflow/Snakefile`。
- 使用受控 config 模板生成任务配置。
- 在隔离工作目录运行。
- 记录 stdout、stderr、Snakemake log、软件版本、参数快照和产物清单。
- 将报告、表格、日志和压缩结果包交付给后端存储。

禁止：

- 不接受用户传入任意 shell 片段。
- 不接受用户传入任意 Snakemake target。
- 不接受用户指定任意 `--snakefile` 或任意工作目录。
- 不允许越过任务沙箱读取或写入路径。

## 4. MVP 用户流程

1. 用户在 Coze 中选择分析入口，例如“创建 GEO RNA-seq 挖掘任务”。
2. Coze 询问必要字段：pipeline 类型、GEO accession、数据类型、是否只做 metadata review、是否已有人工审核文件。
3. Coze 调用后端 `submit job` API。
4. 后端验证参数，生成 `job_id`，返回任务已受理状态。
5. 用户通过 Coze 查询 `job status`。
6. 队列 worker 领取任务，创建隔离目录，生成配置快照。
7. 执行服务运行白名单 pipeline 的受控步骤。
8. 后端持续更新状态、日志摘要和产物索引。
9. 任务完成后，用户通过 Coze 获取 `job result`。
10. 如果任务失败，用户看到明确失败阶段、错误类别和可操作的下一步建议。
11. 如果用户取消任务，后端发出取消信号，worker 尽力停止任务并记录最终状态。

MVP 不自动做的事情：

- 不自动推断正式 case/control。
- 不自动推断 subject 身份或配对关系。
- 不自动合并多个 GSE。
- 不自动删除 outlier。
- 不把 suggested metadata 当作正式 authority。

## 5. API 草案

### 5.1 Submit Job

```http
POST /api/v1/jobs
Content-Type: application/json
Authorization: Bearer <backend-issued-token>
```

请求示例：

```json
{
  "pipeline": "geo_rnaseq_mvp",
  "mode": "metadata_review",
  "project_name": "lung_fibrosis_geo_review",
  "geo_accessions": ["GSE000000"],
  "data_modalities": ["bulk_rnaseq"],
  "authority_files": {
    "sample_manifest_id": null,
    "contrasts_id": null,
    "dataset_plan_id": null,
    "celltype_ontology_id": null
  },
  "options": {
    "allow_network_fetch": false,
    "run_production_analysis": false,
    "max_runtime_minutes": 60
  },
  "client_context": {
    "source": "coze",
    "conversation_id": "optional-coze-conversation-id"
  }
}
```

响应示例：

```json
{
  "job_id": "job_20260705_000001",
  "status": "queued",
  "created_at": "2026-07-05T00:00:00+08:00",
  "message": "Job accepted and queued."
}
```

### 5.2 Get Job Status

```http
GET /api/v1/jobs/{job_id}
Authorization: Bearer <backend-issued-token>
```

响应示例：

```json
{
  "job_id": "job_20260705_000001",
  "status": "running",
  "phase": "validate_inputs",
  "progress": {
    "current_step": "schema_validation",
    "completed_steps": 2,
    "total_steps": 8
  },
  "timestamps": {
    "created_at": "2026-07-05T00:00:00+08:00",
    "started_at": "2026-07-05T00:01:00+08:00",
    "updated_at": "2026-07-05T00:02:00+08:00"
  },
  "message": "Input validation is running."
}
```

### 5.3 Get Job Result

```http
GET /api/v1/jobs/{job_id}/result
Authorization: Bearer <backend-issued-token>
```

响应示例：

```json
{
  "job_id": "job_20260705_000001",
  "status": "succeeded",
  "result_summary": {
    "pipeline": "geo_rnaseq_mvp",
    "mode": "metadata_review",
    "completed_at": "2026-07-05T00:30:00+08:00"
  },
  "artifacts": [
    {
      "name": "analysis_report.html",
      "type": "html_report",
      "url": "https://backend.example.local/artifacts/job_20260705_000001/analysis_report.html"
    },
    {
      "name": "result_bundle.zip",
      "type": "archive",
      "url": "https://backend.example.local/artifacts/job_20260705_000001/result_bundle.zip"
    },
    {
      "name": "audit_trail.tsv",
      "type": "audit_table",
      "url": "https://backend.example.local/artifacts/job_20260705_000001/audit_trail.tsv"
    }
  ],
  "warnings": [],
  "limitations": [
    "This result is not a formal production biological conclusion unless authority files were reviewed and approved."
  ]
}
```

### 5.4 Cancel Job

```http
POST /api/v1/jobs/{job_id}/cancel
Authorization: Bearer <backend-issued-token>
```

请求示例：

```json
{
  "reason": "User requested cancellation from Coze."
}
```

响应示例：

```json
{
  "job_id": "job_20260705_000001",
  "status": "cancel_requested",
  "message": "Cancellation signal recorded. Worker will stop at the next safe checkpoint."
}
```

## 6. Job 状态机

```text
created
  -> queued
  -> running
  -> succeeded

created
  -> rejected

queued
  -> cancel_requested
  -> cancelled

running
  -> cancel_requested
  -> cancelling
  -> cancelled

running
  -> failed

failed
  -> retry_queued
  -> running
```

状态定义：

- `created`：后端收到请求，但尚未完成输入验证。
- `rejected`：输入 schema、权限、白名单或配额检查失败，任务未入队。
- `queued`：任务已持久化并等待 worker。
- `running`：worker 已领取任务并开始执行。
- `cancel_requested`：用户或系统请求取消。
- `cancelling`：worker 正在执行安全停止。
- `cancelled`：任务已停止，结果不完整。
- `failed`：任务失败并记录失败阶段、错误类型和日志摘要。
- `retry_queued`：符合重试策略的任务重新入队。
- `succeeded`：任务完成并生成结果清单。

建议错误分类：

- `input_schema_error`
- `authority_review_required`
- `pipeline_not_allowed`
- `resource_limit_exceeded`
- `execution_failed`
- `cancelled_by_user`
- `internal_error`

## 7. 输入参数 schema 草案

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GeoRnaseqJobSubmit",
  "type": "object",
  "required": ["pipeline", "mode", "project_name", "geo_accessions", "data_modalities", "options"],
  "additionalProperties": false,
  "properties": {
    "pipeline": {
      "type": "string",
      "enum": ["geo_rnaseq_mvp"]
    },
    "mode": {
      "type": "string",
      "enum": ["metadata_review", "validation_only", "fixture_smoke", "production_candidate"]
    },
    "project_name": {
      "type": "string",
      "minLength": 3,
      "maxLength": 80,
      "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]*$"
    },
    "geo_accessions": {
      "type": "array",
      "minItems": 0,
      "maxItems": 20,
      "items": {
        "type": "string",
        "pattern": "^GSE[0-9]+$"
      }
    },
    "data_modalities": {
      "type": "array",
      "minItems": 1,
      "uniqueItems": true,
      "items": {
        "type": "string",
        "enum": ["bulk_rnaseq", "scrna_seq", "snrna_seq"]
      }
    },
    "authority_files": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "sample_manifest_id": {
          "type": ["string", "null"]
        },
        "contrasts_id": {
          "type": ["string", "null"]
        },
        "dataset_plan_id": {
          "type": ["string", "null"]
        },
        "celltype_ontology_id": {
          "type": ["string", "null"]
        }
      }
    },
    "options": {
      "type": "object",
      "required": ["allow_network_fetch", "run_production_analysis", "max_runtime_minutes"],
      "additionalProperties": false,
      "properties": {
        "allow_network_fetch": {
          "type": "boolean",
          "default": false
        },
        "run_production_analysis": {
          "type": "boolean",
          "default": false
        },
        "max_runtime_minutes": {
          "type": "integer",
          "minimum": 1,
          "maximum": 1440
        },
        "requested_outputs": {
          "type": "array",
          "uniqueItems": true,
          "items": {
            "type": "string",
            "enum": ["html_report", "methods", "audit", "tables", "logs", "result_bundle"]
          }
        }
      }
    },
    "client_context": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "source": {
          "type": "string",
          "enum": ["coze", "api", "internal"]
        },
        "conversation_id": {
          "type": ["string", "null"],
          "maxLength": 200
        },
        "user_visible_label": {
          "type": ["string", "null"],
          "maxLength": 200
        }
      }
    }
  }
}
```

输入约束：

- `pipeline` 必须是白名单值。
- `project_name` 只能用于生成安全 slug，不能作为任意路径。
- `geo_accessions` 只能是 accession，不允许 URL、shell、路径或通配符。
- `authority_files` 只能引用后端已登记的文件 ID，不接受任意本地路径。
- `run_production_analysis=true` 必须要求 authority 文件完整且人工确认。
- `allow_network_fetch=true` 必须由后端策略、用户权限和 pipeline 模式共同授权。

## 8. 安全边界

强制边界：

- Coze 不直接执行 shell。
- Coze 不持有执行服务器 secrets。
- Coze 不传递任意 shell 命令。
- Coze 不传递任意本地路径。
- 后端只允许白名单 pipeline。
- 后端不允许任意命令。
- 后端不允许任意路径。
- 后端只接受文件 ID、accession、枚举值和受控参数。
- secrets 只放后端。
- 每个 job 使用独立运行目录。
- 所有运行目录必须位于后端配置的 job workspace root 下。
- 所有结果读取必须通过 artifact registry。
- 取消任务必须走后端 job 状态机，不允许用户直接 kill 任意进程。

白名单 pipeline 初始建议：

- `geo_rnaseq_mvp.metadata_review`
- `geo_rnaseq_mvp.validation_only`
- `geo_rnaseq_mvp.fixture_smoke`
- `geo_rnaseq_mvp.production_candidate`

其中 `production_candidate` 默认关闭，需要后端管理员和项目级策略显式启用。

## 9. 结果交付格式

MVP 结果建议包括：

- `analysis_report.html`：用户阅读入口。
- `methods.md`：方法、参数和限制说明。
- `validation_report.html`：输入验证和门禁结果。
- `audit_trail.tsv`：任务、输入、配置和状态迁移审计。
- `software_versions.tsv`：运行时工具版本。
- `parameter_snapshot.yaml`：参数快照。
- `input_manifest_snapshot.tsv`：输入清单快照。
- `warnings.tsv`：warnings 与非阻断问题。
- `limitations.md`：结果解释边界。
- `result_bundle.zip`：可下载结果包。
- `logs/`：分阶段日志，只暴露脱敏后的用户可见日志。

API 返回格式：

- JSON summary 用于 Coze 展示。
- artifact URLs 用于下载。
- report URL 用于打开 HTML。
- warnings 和 limitations 直接返回简短摘要。
- 失败任务返回失败阶段、错误类型、日志摘要和建议动作。

## 10. 分阶段路线

### Phase 1: 本地 API mock

目标：

- 在本地实现 API skeleton。
- 不运行真实生产 Snakemake job。
- 用 mock executor 返回固定状态和示例结果。
- 验证 Coze 所需 API 形状、字段命名和错误返回。

交付：

- `POST /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs/{job_id}/result`
- `POST /api/v1/jobs/{job_id}/cancel`
- JSON schema validation。
- 本地 job metadata store。

验收：

- Coze 可以提交 mock job。
- Coze 可以查询状态。
- Coze 可以展示 mock 结果。
- Coze 无法传入任意命令或任意路径。

### Phase 2: 队列和执行服务

目标：

- 引入任务队列和单 worker 执行服务。
- 建立 job workspace 隔离。
- 建立白名单 pipeline adapter。
- 支持 `validation_only` 或 `fixture_smoke` 等低风险执行模式。

交付：

- Queue worker。
- Job state transition log。
- Artifact registry。
- Cancel signal。
- Resource limit 和 timeout。
- Worker 日志脱敏策略。

验收：

- API 请求不会阻塞在长任务执行中。
- 队列能串行执行任务。
- 取消任务能进入 `cancel_requested` / `cancelled`。
- 执行层不能越过白名单 pipeline。

### Phase 3: Coze 接入

目标：

- 将 Coze 前台接入后端 API。
- 用 Coze 引导用户填写结构化参数。
- 用 Coze 展示状态和结果摘要。

交付：

- Coze submit job action。
- Coze get status action。
- Coze get result action。
- Coze cancel job action。
- 用户可读的错误说明模板。

验收：

- Coze 不直接执行 shell。
- Coze 不持有 secrets。
- Coze 不能提交任意路径。
- Coze 能展示 job_id、状态、结果链接和限制说明。

### Phase 4: 报告解释和交付

目标：

- 强化结果解释层。
- 将报告、methods、audit 和 limitations 以用户可读方式交付。
- 保留严格边界：系统解释运行结果，不自动生成未经人工确认的生物学结论。

交付：

- HTML report 入口。
- 结果摘要 JSON。
- warnings / limitations 摘要。
- 下载包。
- 面向 Coze 的自然语言解释模板。

验收：

- 用户能从 Coze 打开报告和下载结果。
- 用户能看到哪些内容已验证、哪些内容未验证。
- 对真实分析的结论要求仍由人工审核和项目策略控制。

## 11. 当前不执行事项

本文档生成阶段不执行以下事项：

- 不运行生产任务。
- 不运行 env create。
- 不运行 env solve。
- 不运行 Snakemake。
- 不下载 GEO/SRA。
- 不触发 GitHub Actions。
- 不接入 Coze。
- 不创建后端服务。
- 不启动队列。
- 不处理 secrets。
- 不修改 workflow、env yaml、代码、测试或配置。

## 12. 下一步建议

建议下一步只做 Phase 1 的接口设计落地评审：

1. 冻结 MVP API 字段。
2. 冻结白名单 pipeline 名称。
3. 冻结 job 状态机。
4. 冻结 artifact 类型。
5. 决定本地 mock API 技术栈。
6. 决定后端 job metadata 存储位置。

完成这些决策后，再进入 Phase 1 本地 API mock 实现。
