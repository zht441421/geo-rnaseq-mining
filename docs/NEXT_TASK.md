# 下一阶段任务

- **task_id**：ENV-SOLVE-MEDIUM-RISK-COVERAGE-PLAN-001
- **状态**：not_started；只读规划，等待用户明确启动
- **最后复核**：2026-07-04；Environment Solve 第一批低风险 env dry-run 扩展已由 GitHub Actions 验证通过

## 当前目标

只读规划第二批中风险 env dry-run 覆盖范围。

下一阶段不得直接修改 workflow，也不得加入高风险或网络相关 env。只允许读取现状、复核候选 env 依赖和 workflow 当前覆盖范围，并提出第二批中风险 env 的逐步 dry-run solve 计划，等待用户确认后再实施。

## 已知基线

- Root `.github/workflows/env-solve.yml` 已扩展第一批低风险 env dry-run。
- GitHub Actions run `ci(envs): add low-risk env solve dry runs #5` 成功。
- minimal dry-run restore commit：`133e740`。
- low-risk env expansion commit：`0ab2186`。
- 已验证 dry-run solve：
  - `geo-rnaseq-mining/workflow/envs/metadata.yaml`
  - `geo-rnaseq-mining/workflow/envs/bulk.yaml`
  - `geo-rnaseq-mining/workflow/envs/base.yaml`
  - `geo-rnaseq-mining/workflow/envs/data-entry.yaml`
  - `geo-rnaseq-mining/workflow/envs/bulk-fastqc.yaml`
  - `geo-rnaseq-mining/workflow/envs/bulk-salmon.yaml`

## 第二批只读规划候选

- `bulk-star-featurecounts.yaml`
- `r-bulk.yaml`
- `report.yaml`
- `scrna.yaml`

## 明确暂不纳入的 env

- `sra-tools.yaml`
- `r-bulk-analysis.yaml`
- `python-single-cell.yaml`

## 下一步具体任务

1. 读取 `AGENTS.md`、`docs/CURRENT_STATE.md`、`docs/NEXT_TASK.md`、`docs/CHANGELOG.md`、`docs/VALIDATION.md`、`docs/DECISIONS.md`。
2. 只读查看 `.github/workflows/env-solve.yml`，确认当前已覆盖 6 个 env dry-run。
3. 只读查看 `geo-rnaseq-mining/workflow/envs/` 中第二批候选 env 的依赖。
4. 对 `bulk-star-featurecounts.yaml`、`r-bulk.yaml`、`report.yaml`、`scrna.yaml` 分析 solve 风险、预期耗时和是否应分批或单独 step。
5. 明确不把 `sra-tools.yaml`、`r-bulk-analysis.yaml`、`python-single-cell.yaml` 纳入本轮计划。
6. 输出第二批中风险 env dry-run 覆盖计划后停止，等待用户确认；不得直接修改 workflow。

## 禁止事项

- 不得修改 `.github/workflows/env-solve.yml`。
- 不得修改 `geo-rnaseq-mining/workflow/envs/*.yaml`。
- 不得修改 workflow、schema、CI、测试或代码文件。
- 不得加入 `sra-tools.yaml`、`r-bulk-analysis.yaml`、`python-single-cell.yaml`。
- 不得运行真实 env 创建。
- 不得启动 Snakemake production jobs。
- 不得下载 GEO/SRA。
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
