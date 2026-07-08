# geo-rnaseq-mining 项目交接摘要

更新时间：2026-07-08（Asia/Shanghai）

本文件用于快速交接当前项目状态。它总结当前 Git 基线、Phase 1.3a 到 Phase 1.3e 的完成情况、已验证内容、仍然禁止或未支持的边界，以及建议下一步。当前文件是项目交接摘要，不代表生产分析已经可运行。

## 一句话结论

`geo-rnaseq-mining` 已从早期 Snakemake / Conda 环境验证，推进到产品化 Phase 1 的本地 API mock 契约阶段。当前已经完成 API mock 的输出格式对齐、负向错误契约、成功响应契约、Coze-facing 示例、local operator checklist 和 Coze handoff 文档加固。

项目目前仍处于 mock / contract 阶段：

- 未接入真实 Coze。
- 未运行真实 RNA-seq pipeline。
- 未生成真实 Markdown / HTML 报告。
- 未访问真实 GEO / SRA 数据。
- 未运行生产 Snakemake jobs。

## 当前 Git 与验证基线

- 项目名：`geo-rnaseq-mining`
- 当前分支：`123`
- 当前最新确认 commit：`57c0bbf`
- 完整 SHA：`57c0bbf1d4ac35d5f2a1d059117ec12245a338cd`
- 最新提交说明：`Document dry-run execution request contract`
- 最新 CI 验证：Environment Solve #37
- CI 状态：Success
- 当前阶段：Phase 1.4c local dry-run validation matrix prepared
- 长期本地交接文件：`PROJECT_SUMMARY_FOR_USER.md`

## 当前项目定位

项目长期目标仍是建设一个可审计、可复现、人工审核优先的 RNA-seq 数据挖掘工作流，覆盖 GEO / SRA 元数据入口、bulk RNA-seq、scRNA-seq / snRNA-seq、pseudobulk、多数据集整合、结果解释和报告交付。

当前短期目标已经转向产品化前置工作：

- 用标准库实现本地 API mock。
- 固化 job schema、状态机、错误响应、成功响应和 HTTP 契约。
- 为后续 Coze 接入提供稳定字段、示例和操作交接。
- 继续保持不执行真实生产任务的边界。

## Phase 1.3a 到 1.3e 完成情况

### Phase 1.3a：output_format contract alignment

- commit：`ce32720`
- Environment Solve #31：Success
- `output_format` 合法值统一为：
  - `json`
  - `markdown`
  - `html`
- `zip` 已从合法枚举中移除。
- `zip` 仅保留为非法值测试和错误示例。
- `markdown` / `html` 在 Phase 1 仅作为 mock output_format 回显，不生成真实报告。

### Phase 1.3b：API negative-path contract hardening

- commit：`288af3f`
- Environment Solve #32：Success
- 负向错误契约已加固。
- `field_errors` / `details` 已稳定。
- HTTP `Content-Type` 契约已明确。
- 已覆盖并测试：
  - 非法 `output_format`
  - `output_format = zip`
  - 缺失关键字段
  - unknown field
  - invalid JSON
  - missing / wrong `Content-Type`
  - job not found
  - result not ready
  - not cancellable

### Phase 1.3c：API happy-path response contract stability

- commit：`c170514`
- Environment Solve #34：Success
- 成功响应契约已通过测试和文档锁定。
- `submit_job` / `get_job` / `cancel_job` 的稳定字段包括：
  - `job_id`
  - `status`
  - `request`
  - `created_at`
  - `updated_at`
  - `events`
  - `mock`
  - `message`
- `get_job_result` 已区分：
  - not ready：`ready: false`
  - completed：`ready: true`，并包含 `result_summary` / `artifacts` / `limitations`

### Phase 1.3d：Coze-facing schema examples and fixtures

- commit：`fcadcf0`
- Environment Solve #36：Success
- Coze-facing canonical request / response examples 已固化。
- 未新增 JSON fixture 文件，因为项目当前没有 `tests/fixtures`、`docs/examples`、`api/examples` 等 fixture 目录约定。
- Coze 最小请求字段：
  - `accession`
  - `analysis_type`
  - `species`
  - `output_format`
  - `requested_by`
  - `notes` 可选
- Canonical invalid examples 已包含：
  - `output_format = zip`
  - 缺失 `requested_by`
- 文档已明确：
  - Coze 应保存 `job_id`
  - Coze 应读取 `status`、`message`、`request.output_format`
  - `field_errors` 只用于失败响应

### Phase 1.3e：local API operator checklist / handoff hardening

- commit：`9b2292f`
- Environment Solve #37：Success
- local API operator checklist 已强化。
- Coze handoff 文档已强化。
- 本阶段是 docs-only change。
- 已明确：
  - 如何启动 local API mock
  - 如何做 health check
  - 如何提交最小合法请求
  - 如何查询 job status
  - 如何查询 result
  - 如何 cancel job
  - 如何处理常见错误响应
  - 哪些操作仍然禁止或未支持

## 当前 API mock / HTTP server 测试状态

最新本地测试命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest tests.test_api_mock tests.test_api_http_server -v
```

最新结果：

```text
Ran 44 tests
OK
```

测试覆盖重点：

- schema 白名单
- output_format 合法 / 非法值
- structured error response
- `field_errors` / `details`
- happy-path response fields
- canonical Coze request examples
- HTTP `Content-Type` contract
- HTTP headers
- mock-only safety boundary

## 当前 CI / warning 状态

最新 Environment Solve：

- Environment Solve #37：Success

已知非阻塞 warnings：

- Node.js 20 deprecated annotations 仍可能出现。
- 当前阶段暂不处理 Node.js 20 warning。
- 这些 warnings 不阻塞 Phase 1.3a 到 Phase 1.3e 的 API mock / docs contract 验证。

## 当前强边界

当前项目仍然不应被描述为生产可用分析系统。

必须保持以下边界：

- 不把 `zip` 作为合法 `output_format`。
- 不承诺真实 Markdown / HTML 报告已经生成。
- 不把 `mock://` artifacts 当成真实文件。
- 不把 mock result 当成真实生物学结论。
- 不让 Coze 执行任意 shell 命令。
- 不在提示词、文档、请求示例或日志中写 secrets。
- 不直接运行真实 Snakemake pipeline。
- 不运行 production jobs。
- 不访问真实 GEO / SRA 数据。
- 不下载真实 RNA-seq 数据。
- 不把 Coze 设计成直接操作仓库或 shell。
- Coze 未来应通过受控后端 API 调用，而不是直接执行命令。

## 关键文件阅读顺序

建议接手人按以下顺序阅读：

1. `PROJECT_SUMMARY_FOR_USER.md`
2. `docs/productization-plan.md`
3. `docs/api-mock.md`
4. `docs/api-http-server.md`
5. `docs/coze-api-contract.md`
6. `docs/local-api-runbook.md`
7. `api/job_schema.py`
8. `api/state_machine.py`
9. `api/mock_service.py`
10. `api/http_server.py`
11. `tests/test_api_mock.py`
12. `tests/test_api_http_server.py`

## 建议下一步

可选下一阶段方向：

1. Phase 1.4 planning：从 mock API 进入受控后端执行设计。
2. Phase 1.3g：API examples final audit，最终审计所有示例、状态码、错误码与测试是否一致。
3. 开始设计 Coze workflow 输入表单、参数收集、错误处理分支和用户提示语。
4. 设计真实后端前置组件，但仅限规划：
   - auth
   - persistent job store
   - queue
   - worker
   - result storage
   - audit log
   - quota / rate limit

以上均尚未完成。不要写成已经接入 Coze，不要写成已经可生产运行真实分析。

## 当前不应该做什么

- 不要启动真实 RNA-seq pipeline。
- 不要运行 Snakemake production jobs。
- 不要下载 GEO / SRA 数据。
- 不要承诺真实报告生成。
- 不要让 Coze 直接执行 shell。
- 不要把 mock artifacts 当交付文件。
- 不要把 fixture 或 mock response 当真实生物学分析结果。
- 不要在没有受控后端设计前接入真实 Coze 执行流。

## 最终判断

Phase 1.3a 到 Phase 1.3e 已经完成了 API mock 面向 Coze 接入前最重要的契约稳定工作。当前最有价值的下一步不是运行真实数据，而是决定是否继续做最终 audit，或进入 Phase 1.4 的受控后端执行设计。

## Phase 1.4a controlled execution boundary

Phase 1.4a adds a local boundary contract for future controlled execution
design. The new reference is
`docs/phase-1-4-controlled-execution-boundary.md`.

This is still a mock / contract / placeholder phase. It does not run real GEO
download, RNA-seq processing, Snakemake, real Coze calls, external network
calls, production workers, schedulers, persistent registries, databases, or
real analysis artifacts.

Future real execution must first define explicit opt-in, dry-run mode, safe
input validation, output sandboxing, no secrets in repo, no background execution
by default, no automatic network calls, an operator checklist, and
audit/report-only behavior.

## Phase 1.4b dry-run execution request contract

Phase 1.4b adds a documentation-only dry-run request contract for future
controlled execution requests. The new reference is
`docs/phase-1-4b-dry-run-execution-request-contract.md`.

The default request mode remains `dry_run`. Real execution is forbidden by
default. A future request must keep `allow_network`, `allow_pipeline_execution`,
`allow_snakemake`, and `allow_real_coze_call` set to `false`, and
`operator_approved` remains `false` until a later operator approval design
exists.

This phase still does not download GEO data, run RNA-seq processing, run
Snakemake, call real Coze, make external network requests, write artifacts,
write a database, or introduce workers or schedulers.

## Phase 1.4c dry-run validation / rejection matrix

Phase 1.4c adds a documentation-level validation / rejection matrix for future
dry-run execution requests. The new reference is
`docs/phase-1-4c-dry-run-validation-rejection-matrix.md`.

The matrix defines accepted dry-run-only conditions, rejected real-execution
intents, and rejection reason codes such as `REAL_EXECUTION_NOT_ALLOWED`,
`NETWORK_ACCESS_NOT_ALLOWED`, `SNAKEMAKE_NOT_ALLOWED`,
`UNSAFE_DATASET_ACCESSION`, `SECRET_FIELD_NOT_ALLOWED`, and
`BACKGROUND_EXECUTION_NOT_ALLOWED`.

This phase does not implement a runtime validator and does not execute real
tasks. Any future validator must preserve dry-run defaults, explicit opt-in,
operator approval, output sandboxing, audit/report-only preview, and the
documented rejection reasons.

## Phase 1.4d dry-run validator skeleton

Phase 1.4d adds a minimal pure-function validator skeleton for dry-run
execution request intent. The new references are `api/dry_run_validator.py`,
`docs/phase-1-4d-dry-run-validator-skeleton.md`, and
`tests/test_phase_1_4d_dry_run_validator.py`.

The validator returns `accepted`, `mode`, `rejection_reasons`, and `warnings`.
It keeps the effective mode at `dry_run`, rejects real-execution intent, and
uses the Phase 1.4c rejection reason codes.

This phase still does not download GEO data, run RNA-seq processing, run
Snakemake, call real Coze, make external network requests, start a long-running
server, write real artifacts, write a database, or introduce a queue, worker,
or scheduler.

## Phase 1.4e API mock dry-run validator integration

Phase 1.4e connects `api.dry_run_validator.validate_dry_run_request` to the
existing mock API submit contract. Dry-run execution request payloads now return
a deterministic validation report with `status`, `mode`, `validation`,
`execution`, `mock`, and `message`.

An accepted dry-run validation report means only that the request shape passed
the mock validator. It does not mean real GEO download, RNA-seq processing,
Snakemake, real Coze calls, external network access, artifact writing,
database writing, worker creation, scheduler creation, or real execution has
started.

Rejected dry-run validation reports return deterministic rejection reasons such
as `REAL_EXECUTION_NOT_ALLOWED`, `NETWORK_ACCESS_NOT_ALLOWED`,
`SNAKEMAKE_NOT_ALLOWED`, `REAL_COZE_CALL_NOT_ALLOWED`,
`UNSUPPORTED_OUTPUT_FORMAT`, and `UNSAFE_DATASET_ACCESSION`.

The existing normal mock job submit contract is preserved: `json`, `markdown`,
and `html` remain allowed `output_format` values, while `zip` remains rejected.

## Phase 1.4f API rejection matrix hardening

Phase 1.4f adds mock API rejection matrix coverage for the Phase 1.4e dry-run
validator integration. The new references are
`tests/test_phase_1_4f_api_rejection_matrix.py` and
`docs/phase-1-4f-api-rejection-matrix-hardening.md`.

The coverage confirms that service-layer and HTTP `/jobs` dry-run validation
reports pass through deterministic rejection reasons for real-execution modes,
execution permission flags, operator approval, unsupported output formats,
unsafe dataset accessions, command-like fields, secret-like fields, artifact
and database write intent, and worker or scheduler intent.

Rejected dry-run validation reports do not return `job_id` and keep
`execution` set to `not_started`. Accepted dry-run validation reports also
remain `not_started`. Ordinary mock job submit remains unchanged and still
returns `201` with a mock `job_id`.

This phase does not change the dry-run validator, run GEO download, run
RNA-seq processing, run Snakemake, call real Coze, make external network
requests, write artifacts, write a database, create a worker or scheduler, or
implement a real execution runner.
