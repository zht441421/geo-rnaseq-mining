# 下一阶段任务

- **task_id**：ENV-SOLVE-COVERAGE-PLAN-001
- **状态**：not_started；只读规划，等待用户明确启动
- **最后复核**：2026-07-04；Environment Solve minimal dry-run restore 已由 GitHub Actions 验证通过

## 当前目标

只读规划是否逐步扩大 Environment Solve env yaml 覆盖范围。

下一阶段不得直接扩大到全部 env，也不得修改 workflow、CI、schema、env yaml、测试或代码。只允许读取现状、列出环境文件、按风险和依赖分组，并提出逐步加入 dry-run solve 的计划，等待用户确认后再实施。

## 已知基线

- Root `.github/workflows/env-solve.yml` 已恢复最小 dry-run solve。
- GitHub Actions run `ci(envs): restore minimal env solve dry run #3` 成功。
- trigger recognition commit：`77dbea8`。
- minimal dry-run restore commit：`133e740`。
- 已验证 dry-run solve：
  - `geo-rnaseq-mining/workflow/envs/metadata.yaml`
  - `geo-rnaseq-mining/workflow/envs/bulk.yaml`

## 下一步具体任务

1. 读取 `AGENTS.md`、`docs/CURRENT_STATE.md`、`docs/NEXT_TASK.md`、`docs/CHANGELOG.md`、`docs/VALIDATION.md`、`docs/DECISIONS.md`。
2. 只读查看 `.github/workflows/env-solve.yml`，确认当前 minimal dry-run solve 覆盖范围。
3. 只读列出 `geo-rnaseq-mining/workflow/envs/*.yaml`。
4. 将 env yaml 按风险和依赖分组，例如已验证基线、低风险 Python/metadata、bulk/R/Bioconductor、single-cell 重依赖、integration/reporting 或其他高风险环境。
5. 为每组提出逐步加入 dry-run solve 的顺序、预期风险、回滚点和验证信号。
6. 明确保留 `metadata.yaml` 与 `bulk.yaml` 作为已通过基线。
7. 输出规划后停止，等待用户确认；不得直接扩大 workflow 覆盖范围。

## 禁止事项

- 不得修改 `.github/workflows/env-solve.yml`。
- 不得修改 `geo-rnaseq-mining/workflow/envs/*.yaml`。
- 不得修改 workflow、schema、CI、测试或代码文件。
- 不得直接把全部 env yaml 加入 solve。
- 不得运行真实 env 创建。
- 不得启动 Snakemake production jobs。
- 不得声明未验证 env 已经可解。
- 不得在只读规划阶段修复 warnings。

## 后续 P2/P3 优化候选

以下仅记录，不属于下一阶段唯一任务的实施内容：

- Node.js 20 deprecation warning for `actions/checkout@v4` and `setup-miniconda@v3` forced onto Node.js 24。
- `auto-activate-base` deprecated；可考虑 `auto-activate`。
- `defaults` channel implicitly added；可考虑显式 channels 或 `conda-remove-defaults: true`。

## 下一会话应首先读取的文件

- `AGENTS.md`
- `docs/CURRENT_STATE.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`
- `docs/VALIDATION.md`
- `docs/DECISIONS.md`
- `.github/workflows/env-solve.yml`
- `geo-rnaseq-mining/workflow/envs/`
