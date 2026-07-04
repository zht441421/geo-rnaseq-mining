# 当前项目状态

最后更新：2026-07-04（Asia/Shanghai）；Environment Solve low-risk env dry-run expansion verification 已完成。

本文档只记录已从代码、实际文件、命令验证或本次用户提供的 GitHub Actions 结果中确认的事实。当前阶段只覆盖 6 个指定 env yaml 的 dry-run solve，不代表全部环境、实际环境创建或生产分析可用。

## 当前阶段

Environment Solve low-risk env dry-run expansion verification。

Root `.github/workflows/env-solve.yml` 已扩展第一批低风险 env dry-run，并已由 GitHub Actions 成功运行。

## 已完成内容

- Root `.github/workflows/env-solve.yml` 扩展第一批低风险 env dry-run。
- GitHub Actions workflow `Environment Solve` 已由 `push` 触发并成功完成。
- `checkout` 和 Miniforge/Mamba setup 已运行成功。
- 当前已有 6 个 env yaml 通过 `mamba env create --dry-run`。
- minimal dry-run restore commit：`133e740`。
- low-risk env expansion commit：`0ab2186`。

## GitHub Actions 验证

| 字段 | 结果 |
|---|---|
| Workflow | `Environment Solve` |
| Run | `ci(envs): add low-risk env solve dry runs #5` |
| Trigger | `push` |
| Branch | `123` |
| Commit | `0ab2186` |
| Status | Success |
| Total duration | 1m 32s |
| Job | `Linux env solve dry-run` |
| Job status | Success |
| Job duration | 1m 27s |
| Artifacts | 无 |

## 已验证 env dry-runs

以下 env 均已通过 `mamba env create --dry-run`：

- `geo-rnaseq-mining/workflow/envs/metadata.yaml`
- `geo-rnaseq-mining/workflow/envs/bulk.yaml`
- `geo-rnaseq-mining/workflow/envs/base.yaml`
- `geo-rnaseq-mining/workflow/envs/data-entry.yaml`
- `geo-rnaseq-mining/workflow/envs/bulk-fastqc.yaml`
- `geo-rnaseq-mining/workflow/envs/bulk-salmon.yaml`

## Warnings 记录

以下 warnings 出现在 GitHub Actions run 中，但 job 成功。当前阶段只记录，不修复；后续作为 P2/P3 优化候选。

- Node.js 20 deprecation warning for `actions/checkout@v4` and `setup-miniconda@v3` forced onto Node.js 24。
- `auto-activate-base` is deprecated；后续可考虑 `auto-activate`。
- `defaults` channel may have been added implicitly；后续可考虑显式 channels 或 `conda-remove-defaults: true`。

## 未验证内容

- 全部 env yaml 未验证。
- env 实际创建未验证。
- Snakemake production jobs 未运行。
- GEO/SRA 下载未验证。
- 真实生产数据分析未验证。

## 已知边界

- 本阶段只是 dry-run solve。
- 本阶段只验证 GitHub Actions workflow 可由 push 触发、checkout / Miniforge-Mamba setup 可运行，并可对 6 个指定 env yaml 执行 `mamba env create --dry-run`。
- 本阶段不等于生产 pipeline 可用。
- 本阶段不等于所有环境可解。
- 本阶段不声明任何真实 GEO/SRA 下载、正式 Snakemake job、真实 FASTQ 定量或真实分析结果已经通过。

## 修改文件

本阶段实现与交接涉及：

- `.github/workflows/env-solve.yml`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`
- `docs/VALIDATION.md`

本次交接操作只更新 Markdown 文档，未继续修改 workflow、schema、CI、env yaml、测试或代码文件。

## 当前 Git 状态记录

- 当前验证分支：`123`。
- GitHub Actions 验证 commit：`0ab2186`。
- 相关历史 commit：
  - `133e740` minimal dry-run restore
  - `0ab2186` low-risk env expansion

## 下一步应该执行的任务

只读规划第二批中风险 env dry-run 覆盖范围。

候选 env 包括：

- `bulk-star-featurecounts.yaml`
- `r-bulk.yaml`
- `report.yaml`
- `scrna.yaml`

下一阶段只做只读规划，不直接修改 workflow，不加入 `sra-tools.yaml`、`r-bulk-analysis.yaml`、`python-single-cell.yaml`，等待用户确认。

## 下一会话应首先读取的文件

- `AGENTS.md`
- `docs/CURRENT_STATE.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`
- `docs/VALIDATION.md`
- `docs/DECISIONS.md`
- `.github/workflows/env-solve.yml`
- `geo-rnaseq-mining/workflow/envs/`
