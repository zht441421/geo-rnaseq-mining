# geo-rnaseq-mining 项目交接摘要

更新时间：2026-07-09（Asia/Shanghai）

本文件用于快速交接当前项目状态。它总结当前 Git 基线、Phase 1.3a 到 Phase 1.6c 的完成情况、已验证内容、仍然禁止或未支持的边界，以及建议下一步。当前文件是项目交接摘要，不代表生产分析已经可运行。

## 一句话结论

`geo-rnaseq-mining` 已从早期 Snakemake / Conda 环境验证，推进到产品化 Phase 1 的本地 API mock 契约阶段，并完成 Phase 1.5 design-only completion baseline / operator handoff、Phase 1.6a runtime implementation readiness audit、Phase 1.6b sandbox boundary design 和 Phase 1.6c artifact persistence boundary design。当前已经完成 API mock 的输出格式对齐、负向错误契约、成功响应契约、Coze-facing 示例、local operator checklist、Coze handoff 文档加固，以及 Phase 1.5a 到 Phase 1.5f 的设计文档链路。

项目目前仍处于 mock / contract / design-only baseline / readiness-audit 阶段：

- 未接入真实 Coze。
- 未运行真实 RNA-seq pipeline。
- 未生成真实 Markdown / HTML 报告。
- 未访问真实 GEO / SRA 数据。
- 未运行生产 Snakemake jobs。
- 未实现 runtime execution / parser / validator / planner / runner / approval system / API integration / sandbox implementation / sandbox directory creation / artifact writer / artifact directory creation / artifact registry / artifact/database/network boundary。

## 当前 Git 与验证基线

- 项目名：`geo-rnaseq-mining`
- 当前分支：`123`
- 当前 HEAD baseline：`3f63b30`
- 完整 SHA：`3f63b30d83ac436f1b2199e6773f738631e68248`
- 最新提交说明：`Document sandbox boundary design`
- 最新 CI 验证：Environment Solve #37
- CI 状态：Success
- 当前阶段：Phase 1.6c artifact persistence boundary design（docs/tests only）
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

## Phase 1.4g completion baseline / operator handoff

Phase 1.4g records the completion baseline for Phase 1.4a through Phase 1.4f
and adds an operator handoff for the next decision point. The current baseline
commit is `e2ffee42e6bf72e4a3e1a72445a357ed19924ad1` (`e2ffee4`) on branch
`123`.

The new baseline reference is
`docs/phase-1-4-completion-baseline.md`, with coverage in
`tests/test_phase_1_4_completion_baseline_docs.py`.

The baseline summarizes the completed chain:
controlled execution boundary -> dry-run execution request contract ->
validation / rejection matrix -> pure dry-run validator skeleton -> API mock
integration -> API rejection matrix hardening.

The operator handoff lists safe tests, tests that must not be added without
review, safety-boundary violation signals, and controls required before any
future real runtime execution: explicit opt-in, operator approval, validated
input manifest, output sandbox, audit/report-only preview, no automatic
network calls, controlled runner / worker design, persistence boundary design,
and secrets management outside repo.

Phase 1.4g is docs and documentation tests only. It still does not implement a
real execution runner, run GEO download, run RNA-seq processing, run
Snakemake, call real Coze, make external network requests, write artifacts,
write a database, or create a worker or scheduler.

## Phase 1.5a runtime execution design audit

Phase 1.5a starts after the Phase 1.4 completion baseline. The current HEAD
baseline is `5fb0b328fb7e1d52e991c62223a15c3348b944c5` (`5fb0b32`) on branch
`123`.

The new design audit reference is
`docs/phase-1-5a-runtime-execution-design-audit.md`, with coverage in
`tests/test_phase_1_5a_runtime_execution_design_audit_docs.py`.

Phase 1.5a is design audit only, not implementation. It documents required
preconditions, runtime execution boundary layers, forbidden default behavior,
failure protections, interface design questions, and safe next phase options
before any controlled runtime execution can be proposed.

The audit explicitly keeps runtime work out of scope: no real execution runner,
no worker / scheduler / queue, no pipeline executor, no Snakemake wrapper, no
GEO downloader, no Coze real client, no artifact writer, and no database
persistence.

## Phase 1.5b runtime request schema design only

Phase 1.5b starts from the current HEAD baseline
`244043eb52e08614719d99cb338c40792ffd5c63` (`244043e`) on branch `123`.

The new schema design reference is
`docs/phase-1-5b-runtime-request-schema-design.md`, with coverage in
`tests/test_phase_1_5b_runtime_request_schema_design_docs.py`.

Phase 1.5b is schema design only, not implementation. It documents a future
runtime request shape with required top-level fields such as `mode`,
`request_id`, `dataset_accession`, `analysis_type`, `output_format`,
`execution_intent`, `operator_approval`, `input_manifest`, `sandbox`, `audit`,
and `safety_flags`.

The design keeps dry-run safety defaults: `mode` remains `dry_run`, real
execution intent remains false, network and pipeline permissions remain false,
operator approval remains false, artifact writing remains false, and audit
behavior remains report-only.

Phase 1.5b explicitly does not implement a runtime parser, runtime validator,
API handler integration, real execution runner, worker, queue, scheduler,
pipeline executor, Snakemake wrapper, GEO downloader, Coze real client,
artifact writer, or database persistence.

## Phase 1.5c input manifest schema design docs/tests only

Phase 1.5c starts from the current HEAD baseline
`244043eb52e08614719d99cb338c40792ffd5c63` (`244043e`) on branch `123`.

The new manifest schema design reference is
`docs/phase-1-5c-input-manifest-schema-design.md`, with coverage in
`tests/test_phase_1_5c_input_manifest_schema_design_docs.py`.

Phase 1.5c is manifest schema docs/tests only, not implementation. It documents
a future input manifest shape with required top-level fields such as
`manifest_id`, `manifest_version`, `dataset`, `samples`, `analysis`, `inputs`,
`outputs`, `provenance`, `safety`, and `audit`.

The design keeps the manifest metadata-only and report-only: dataset accessions
remain accession-like placeholders, samples do not require real FASTQ / BAM /
count matrix paths, analysis remains `rnaseq_placeholder`, outputs keep
`output_format` limited to `json`, `markdown`, and `html`, `write_artifacts`
remains false, and `report_only` remains true.

Phase 1.5c explicitly does not implement a manifest parser, manifest validator,
JSON schema file, Pydantic model, API handler integration, runtime execution
runner, worker, queue, scheduler, pipeline executor, Snakemake wrapper, GEO
downloader, Coze real client, artifact writer, or database persistence.

## Phase 1.5d dry-run execution plan preview design only

Phase 1.5d starts from the current HEAD baseline
`50227fb2c54612fe26db984e7eb6bce74cdcf921` (`50227fb`) on branch `123`.

The new preview design reference is
`docs/phase-1-5d-dry-run-execution-plan-preview-design.md`, with coverage in
`tests/test_phase_1_5d_dry_run_execution_plan_preview_design_docs.py`.

Phase 1.5d is dry-run execution plan preview design only, not implementation.
It documents a future operator-visible preview shape with required top-level
fields such as `preview_id`, `request_id`, `manifest_id`, `mode`, `status`,
`plan_summary`, `planned_steps`, `blocked_actions`, `safety_assessment`,
`operator_review`, `sandbox_preview`, `audit_report`, and
`next_allowed_actions`.

The design keeps preview behavior dry-run-only: `mode` remains `dry_run`,
`status` is limited to `preview_only`, `blocked`, or `rejected`, planned steps
are descriptive only, blocked actions list real execution attempts that were
not performed, sandbox information remains a placeholder, and audit behavior
remains report-only.

Phase 1.5d explicitly does not implement an execution planner, runtime planner,
plan generator, runtime parser, manifest parser, manifest validator, API
handler integration, runtime execution runner, worker, queue, scheduler,
pipeline executor, Snakemake wrapper, GEO downloader, Coze real client,
artifact writer, or database persistence.

## Phase 1.5e manifest validation rules docs/tests only

Phase 1.5e starts from the current HEAD baseline
`3c42f268b80d782b5a08eb1f44bc12515f6f88df` (`3c42f26`) on branch `123`.

The new validation rules design reference is
`docs/phase-1-5e-manifest-validation-rules-design.md`, with coverage in
`tests/test_phase_1_5e_manifest_validation_rules_design_docs.py`.

Phase 1.5e is manifest validation rules docs/tests only, not implementation.
It documents future rule categories and rejection reasons for required
manifest sections, identifier safety, dataset placeholders, metadata-only
samples, documentation-only analysis, placeholder-only inputs, report-only
outputs, provenance, safety flags, audit behavior, deterministic rejection
behavior, and accepted-for-preview-only outcomes.

The design keeps validation dry-run-only: accepted manifests are accepted for
preview only, rejected manifests stay `not_started`, artifacts are not created,
network is not performed, databases are not written, and operator-visible
report-only behavior remains required.

Phase 1.5e explicitly does not implement a manifest validator, manifest parser,
runtime validator, JSON schema file, Pydantic model, API handler integration,
execution planner, plan generator, runtime execution runner, worker, queue,
scheduler, pipeline executor, Snakemake wrapper, GEO downloader, Coze real
client, artifact writer, or database persistence.

## Phase 1.5f operator approval record design only

Phase 1.5f starts from the current HEAD baseline
`b530098e7d5343b7a4e80274bdba5655881a4826` (`b530098`) on branch `123`.

The new approval record design reference is
`docs/phase-1-5f-operator-approval-record-design.md`, with coverage in
`tests/test_phase_1_5f_operator_approval_record_design_docs.py`.

Phase 1.5f is operator approval record design only, not implementation. It
documents future approval record fields, non-executing decision values,
approved and denied scopes, safety override rules, audit requirements,
revocation and expiration placeholders, automatic escalation prevention,
forbidden content, accepted-for-future-review-only conditions, and safe
approval outcome examples.

The design keeps approval report-only and fail-closed: approval records do not
trigger execution, do not override dry-run safety flags, do not grant network
or pipeline permissions, do not grant artifact/database writes, and do not
start worker, queue, or scheduler work.

Phase 1.5f explicitly does not implement an approval system, approval API,
approval database, approval UI, authentication, authorization, runtime
validator, manifest validator, JSON schema file, Pydantic model, API handler
integration, execution planner, plan generator, runtime execution runner,
worker, queue, scheduler, pipeline executor, Snakemake wrapper, GEO downloader,
Coze real client, artifact writer, or database persistence.

## Phase 1.5g completion baseline / operator handoff

Phase 1.5g starts from the current HEAD baseline
`19d6965fb2fcdcadcdc2614eaddda75b546d15c0` (`19d6965`) on branch `123`.

The new completion baseline reference is
`docs/phase-1-5-completion-baseline.md`, with coverage in
`tests/test_phase_1_5_completion_baseline_docs.py`.

Phase 1.5g records Phase 1.5 as a design-only completion baseline and operator
handoff. Phase 1.5a through Phase 1.5f are complete as design records:
runtime execution design audit, runtime request schema design, input manifest
schema design, dry-run execution plan preview design, manifest validation
rules design, and operator approval record design.

The baseline remains documentation and documentation tests only. It still does
not implement runtime execution, runtime parser, runtime validator, manifest
parser, manifest validator, execution planner, plan generator, real execution
runner, approval system, approval API, approval database, approval UI,
authentication, authorization, API handler integration, worker, queue,
scheduler, GEO downloader, Snakemake wrapper, Coze real client, artifact
writer, or database persistence.

Recommended next phases remain design-only or documentation-test-only, such as
Phase 1.6a runtime implementation readiness audit docs/tests only, sandbox
boundary design docs/tests only, artifact persistence boundary design
docs/tests only, or network boundary design docs/tests only. Do not directly
enter real execution implementation.

## Phase 1.6a runtime implementation readiness audit docs/tests only

Phase 1.6a starts from the current HEAD baseline
`282fe0f132d1ce08f5200bf402f1e3392a220e90` (`282fe0f`) on branch `123`.

The new readiness audit reference is
`docs/phase-1-6a-runtime-implementation-readiness-audit.md`, with coverage in
`tests/test_phase_1_6a_runtime_implementation_readiness_audit_docs.py`.

Phase 1.6a is a readiness audit docs/tests only phase. It does not approve or
implement real runtime work. The conclusion is: not ready for real runtime
implementation.

The audit confirms that Phase 1.5 created a design-only safety baseline, but
that baseline is not implementation readiness approval. Runtime request,
manifest, dry-run preview, and operator approval designs exist, while the
runtime parser, runtime validator, manifest parser, manifest validator,
execution planner, plan generator, approval system, approval API/database/UI,
authentication, authorization, and runtime API handler integration remain
missing by design.

The audit also marks sandbox, artifact persistence, database persistence,
network boundary, secrets management, threat model, resource lifecycle, and
runtime API integration as not ready. These areas need separate docs/tests-only
design phases before any implementation can be considered.

Phase 1.6a explicitly does not implement runtime execution, parser, validator,
planner, runner, approval system, API integration, sandbox implementation,
artifact writer, database persistence, network boundary implementation,
worker, queue, scheduler, GEO downloader, Snakemake wrapper, or Coze real
client.

## Phase 1.6b sandbox boundary design docs/tests only

Phase 1.6b starts from the current HEAD baseline
`4814bef608d2cc89d04a3f53c3c06025ecbc317a` (`4814bef`) on branch `123`.

The new sandbox boundary design reference is
`docs/phase-1-6b-sandbox-boundary-design.md`, with coverage in
`tests/test_phase_1_6b_sandbox_boundary_design_docs.py`.

Phase 1.6b is sandbox boundary design docs/tests only. It does not approve or
implement sandbox code, sandbox directory creation, filesystem writes,
artifact writing, database persistence, network boundary implementation,
runtime execution, API integration, or worker / queue / scheduler behavior.

The conclusion is: not ready for sandbox implementation. Sandbox path policy,
path normalization/enforcement, artifact write boundary, cleanup policy,
rollback policy, and audit policy remain design-only gaps. Runtime execution,
artifact writing, database side effects, network side effects, and worker
side effects remain not approved.

The design records fail-closed sandbox principles, future sandbox_id rules,
trusted-operator sandbox root policy, future path normalization and
inside-root enforcement, artifact write preconditions, cleanup / rollback /
audit requirements, a report-only sandbox preview schema, explicit no-go
decisions, and safe Phase 1.6c docs/tests-only next options.

Phase 1.6b explicitly does not create a real sandbox directory, write real
artifacts, write a database, run a pipeline, run Snakemake, download GEO data,
call real Coze, perform external network access, start a long-running server,
or implement sandbox implementation, artifact writer, runtime execution,
runtime parser, runtime validator, manifest parser, manifest validator,
execution planner, plan generator, approval system, API handler integration,
worker, queue, scheduler, GEO downloader, Snakemake wrapper, or Coze real
client.

## Phase 1.6c artifact persistence boundary design docs/tests only

Phase 1.6c starts from the current HEAD baseline
`3f63b30d83ac436f1b2199e6773f738631e68248` (`3f63b30`) on branch `123`.

The new artifact persistence boundary design reference is
`docs/phase-1-6c-artifact-persistence-boundary-design.md`, with coverage in
`tests/test_phase_1_6c_artifact_persistence_boundary_design_docs.py`.

Phase 1.6c is artifact persistence boundary design docs/tests only. It does
not approve or implement artifact writer, artifact directory creation,
artifact file creation, artifact registry, database persistence, sandbox
implementation, runtime execution, API integration, network upload, or worker
/ queue / scheduler behavior.

The conclusion is: not ready for artifact persistence implementation.
Artifact naming policy, retention policy, overwrite policy, audit metadata,
privacy/leakage rules, and cleanup/rollback policy remain design-only gaps.
Sandbox implementation, database persistence, runtime execution, and artifact
writer remain not approved.

The design records fail-closed artifact persistence principles, future
artifact identity and naming rules, storage policy rooted in an approved
sandbox root, overwrite / retention / cleanup policy, artifact audit metadata,
privacy / leakage boundaries, a report-only artifact persistence preview
schema, explicit no-go decisions, and safe Phase 1.6d docs/tests-only next
options.

Phase 1.6c explicitly does not create artifact directories, write artifact
files, write a database, create a real sandbox directory, run a pipeline, run
Snakemake, download GEO data, call real Coze, perform external network access,
start a long-running server, or implement artifact writer, artifact
persistence, artifact registry, sandbox implementation, database persistence,
network boundary implementation, runtime execution, runtime parser, runtime
validator, manifest parser, manifest validator, execution planner, plan
generator, approval system, API handler integration, worker, queue, scheduler,
GEO downloader, Snakemake wrapper, or Coze real client.

## Phase 1.6d artifact validation rules docs/tests only

Phase 1.6d starts from HEAD baseline
`493d891252a1205acb20c94b05ee8b63e1ae6991` (`493d891`) on branch `123`.

The artifact validation rules design reference is
`docs/phase-1-6d-artifact-validation-rules.md`, with documentation-only
coverage in `tests/test_phase_1_6d_artifact_validation_rules_docs.py`.

Phase 1.6d defines future fail-closed artifact type, filename, format,
metadata, size, sandbox/path, overwrite, audit, redaction, and rejection-code
rules. Validation remains report-only until future runtime approval.
Validation success does not authorize write or execution, and an approval
record cannot bypass validation.

The conclusion is: not ready for artifact validator runtime implementation.
Phase 1.6d does not implement a validator runtime, artifact writer,
persistence layer, registry, database, storage backend, sandbox, filesystem
inspection, path resolver, API integration, worker / queue / scheduler,
network request, GEO downloader, Snakemake wrapper, or real Coze client.

## Phase 1.7 Cross-Boundary Security Threat Model docs/tests only

Phase 1.7 starts from HEAD baseline
`364c9ee1de98f49daa3cb99bc7e0260b0282c842` (`364c9ee`) on branch `123`.

The threat-model design reference is
`docs/phase-1-7-cross-boundary-security-threat-model.md`, with documentation-
only coverage in
`tests/test_phase_1_7_cross_boundary_security_threat_model_docs.py`.

Phase 1.7 documents assets, actors, trust boundaries, STRIDE categories,
specific cross-boundary threats, existing design controls, remaining risks,
future prerequisites, a control-mapping matrix, and a report-only threat
assessment schema design. Design controls are not actually enforced controls,
and the threat model does not authorize implementation.

The single recommended next topic is Phase 1.8 secrets management and
redaction boundary design docs/tests only. Phase 1.7 does not implement runtime
security enforcement, authentication or authorization, secrets management,
database/storage, network controls, sandboxing, artifact persistence, audit
storage, API integration, workers, GEO download, Snakemake execution, or Coze
integration.

## Phase 1.8 Secrets Management and Redaction Boundary Design docs/tests only

Phase 1.8 starts from HEAD baseline
`5a5ae6e20b93df32ee7d6ea18ba660c86b4f0539` (`5a5ae6e`) on branch `123`.

The design reference is
`docs/phase-1-8-secrets-management-redaction-boundary.md`, with documentation-
only coverage in
`tests/test_phase_1_8_secrets_management_redaction_boundary_docs.py`.

Phase 1.8 documents secret classification, credential and trust boundaries,
the source-to-discard lifecycle, redaction rules, least-privilege concepts,
leakage threat mapping, rejection-code vocabulary, and a report-only assessment
schema. Validation does not access secret, approval does not authorize secret
disclosure, and design controls do not equal enforced controls.

Secrets implementation remains not approved. Phase 1.8 does not create a
secret system, loader, provider, storage, cache, runtime redactor, log
interceptor, artifact scanner, audit persistence, network client, API handler,
authentication/authorization implementation, or worker credential delegation.

## Phase 1.9 Task Lifecycle and State Machine Boundary Design docs/tests only

Phase 1.9 starts from HEAD baseline
`53e5f394f41a004e9cd29659142981e2d1654196` (`53e5f39`) on branch `123`.

The design reference is
`docs/phase-1-9-task-lifecycle-state-machine-boundary-design.md`, with
documentation-only coverage in
`tests/test_phase_1_9_task_lifecycle_state_machine_boundary_design_docs.py`.

Phase 1.9 is Platform Design Baseline convergence, docs/tests-only,
design-only, report-only, and not runtime lifecycle implementation. It records
future state vocabulary, allowed and blocked transitions, succeeded gates,
cancellation and cleanup semantics, failure taxonomy, retry, idempotency,
replay, concurrency, authoritative-state, transition audit, and Scientific
Pilot boundaries.

The existing in-memory mock state machine remains unchanged and is not promoted
to a future runtime contract. No executable state machine, database state
store, queue, worker, scheduler, runner, cancellation signal, retry engine,
audit persistence, runtime API integration, real task, pipeline, Snakemake,
GEO/SRA, Coze, network, credential, artifact, or sandbox behavior is added.

The conclusion is: not ready for runtime lifecycle implementation. The next
recommended stage remains Platform Design Baseline Completion / Go-No-Go Audit;
Scientific Pilot Readiness Planning may follow only after that separately
authorized audit.
