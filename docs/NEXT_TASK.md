# 下一阶段任务

- **task_id**：ENV-ACTUAL-CREATE-READONLY-PLAN-001
- **状态**：not_started；只读规划，等待用户明确启动
- **最后复核**：2026-07-04；Environment Solve 全部 13 个 env dry-run 覆盖已由 GitHub Actions 验证通过

## 当前目标

只读规划从 env solve dry-run 进入实际环境创建验证的最小安全路径。

下一阶段不得直接修改 workflow、env yaml、schema、CI、测试或代码，也不得直接运行实际 `mamba env create`。只允许读取现状、复核 workflow 和 env 依赖，提出是否先对低风险 env 做实际创建测试、是否拆独立 workflow/job、如何控制缓存/耗时/磁盘空间，以及如何避免 production jobs、GEO/SRA 下载和真实数据分析。

## 已知基线

- Root `.github/workflows/env-solve.yml` 已覆盖全部 13 个 env yaml dry-run。
- GitHub Actions run `ci(envs): add high-risk env solve dry runs #9` 成功。
- Branch：`123`。
- Commit：`2bd80d9`。
- Total duration：1m 57s。
- Artifacts：无。
- 稳定基线 job `Linux env solve dry-run` 成功，1m 53s。
- high-risk job `Linux high-risk env solve dry-run` 成功，1m 16s。
- medium-risk env expansion commit：`ec832de`。
- high-risk env expansion commit：`2bd80d9`。
- 已验证 dry-run solve：
  - `geo-rnaseq-mining/workflow/envs/metadata.yaml`
  - `geo-rnaseq-mining/workflow/envs/bulk.yaml`
  - `geo-rnaseq-mining/workflow/envs/base.yaml`
  - `geo-rnaseq-mining/workflow/envs/data-entry.yaml`
  - `geo-rnaseq-mining/workflow/envs/bulk-fastqc.yaml`
  - `geo-rnaseq-mining/workflow/envs/bulk-salmon.yaml`
  - `geo-rnaseq-mining/workflow/envs/bulk-star-featurecounts.yaml`
  - `geo-rnaseq-mining/workflow/envs/r-bulk.yaml`
  - `geo-rnaseq-mining/workflow/envs/report.yaml`
  - `geo-rnaseq-mining/workflow/envs/scrna.yaml`
  - `geo-rnaseq-mining/workflow/envs/sra-tools.yaml`
  - `geo-rnaseq-mining/workflow/envs/r-bulk-analysis.yaml`
  - `geo-rnaseq-mining/workflow/envs/python-single-cell.yaml`

## 下一步具体任务

1. 读取 `AGENTS.md`、`docs/CURRENT_STATE.md`、`docs/NEXT_TASK.md`、`docs/CHANGELOG.md`、`docs/VALIDATION.md`、`docs/DECISIONS.md`。
2. 只读查看 `.github/workflows/env-solve.yml`，确认当前 dry-run solve 覆盖范围和 job 拆分方式。
3. 只读查看 `geo-rnaseq-mining/workflow/envs/`，按依赖体量、工具链复杂度和预期磁盘占用对 13 个 env 分组。
4. 判断是否应先选择低风险 env 做 `mamba env create` 实际创建测试，并说明候选顺序和退出条件。
5. 判断实际创建验证是否应拆成独立 workflow/job，如何设置 timeout、并发、缓存策略和磁盘空间清理策略。
6. 明确保护边界：不得触发 Snakemake production jobs，不得下载 GEO/SRA，不得运行真实生产数据分析，不得把实际创建成功外推为生产 pipeline 可用。
7. 输出实际环境创建验证的最小安全路径规划后停止，等待用户确认；不得直接修改 workflow 或开始实施。

## 禁止事项

- 不得修改 `.github/workflows/env-solve.yml`。
- 不得修改 `geo-rnaseq-mining/workflow/envs/*.yaml`。
- 不得修改 workflow、schema、CI、测试或代码文件。
- 不得运行真实 env 创建。
- 不得启动 Snakemake production jobs。
- 不得下载 GEO/SRA。
- 不得声明实际 env 创建已经验证。
- 不得声明生产 pipeline 可用。
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
