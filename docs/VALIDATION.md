# 验证记录

所有日期使用 Asia/Shanghai 时区。本文档记录阶段验证事实、范围边界、warnings 和未验证内容。

## 2026-07-04 — Environment Solve all-env dry-run coverage verification

### GitHub Actions run

| 检查项 | 结果 | 说明 |
|---|---|---|
| Workflow 识别 | 通过 | `Environment Solve` |
| Run | 通过 | `ci(envs): add high-risk env solve dry runs #9` |
| Trigger | 通过 | `push` |
| Branch | 通过 | `123` |
| Commit | 通过 | `2bd80d9` |
| Total duration | 通过 | 1m 57s |
| Artifacts | 通过 | 无 |
| Linux env solve dry-run | 通过 | 1m 53s |
| Linux high-risk env solve dry-run | 通过 | 1m 16s |

### Env dry-run 结果

| env | 结果 |
|---|---|
| `metadata.yaml` | 通过 |
| `bulk.yaml` | 通过 |
| `base.yaml` | 通过 |
| `data-entry.yaml` | 通过 |
| `bulk-fastqc.yaml` | 通过 |
| `bulk-salmon.yaml` | 通过 |
| `bulk-star-featurecounts.yaml` | 通过 |
| `r-bulk.yaml` | 通过 |
| `report.yaml` | 通过 |
| `scrna.yaml` | 通过 |
| `sra-tools.yaml` | 通过 |
| `r-bulk-analysis.yaml` | 通过 |
| `python-single-cell.yaml` | 通过 |

### Commits

- `ec832de` medium-risk env expansion
- `2bd80d9` high-risk env expansion

### 已验证范围

- GitHub Actions workflow 可由 `push` 触发。
- GitHub Actions runner 可完成 checkout。
- Miniforge/Mamba setup 可运行。
- Root `.github/workflows/env-solve.yml` 覆盖全部 13 个 env yaml 的 `mamba env create --dry-run`。
- 稳定基线 job 和 high-risk job 均成功。

### Warnings

GitHub Actions run 有 10 个 warnings，但 jobs 成功。本阶段只记录，不修复；后续作为 P2/P3 优化候选。

- Node.js 20 deprecation warning for `actions/checkout@v4` and `setup-miniconda@v3` forced onto Node.js 24。
- `auto-activate-base` is deprecated；后续可考虑 `auto-activate`。
- `defaults` channel may have been added implicitly；后续可考虑显式 channels 或 `conda-remove-defaults: true`。

### 未验证内容

- env 实际创建未验证。
- Snakemake production jobs 未运行。
- GEO/SRA 下载未验证。
- 真实生产数据分析未验证。

### 边界说明

- 本阶段只是 dry-run solve。
- 本阶段不等于实际环境创建成功。
- 本阶段不等于生产 pipeline 可用。
- 下一阶段唯一任务是只读规划从 env solve dry-run 进入实际环境创建验证的最小安全路径。
- 下一阶段重点判断是否先对低风险 env 做 `mamba env create` 实际创建测试，是否拆独立 workflow/job，如何控制缓存、耗时、磁盘空间，以及如何避免 production jobs、GEO/SRA 下载和真实数据分析。

## 2026-07-04 — Environment Solve medium-risk env dry-run expansion verification

### GitHub Actions run

| 检查项 | 结果 | 说明 |
|---|---|---|
| Workflow 识别 | 通过 | `Environment Solve` |
| Run | 通过 | `ci(envs): add medium-risk env solve dry runs #7` |
| Trigger | 通过 | `push` |
| Branch | 通过 | `123` |
| Commit | 通过 | `ec832de` |
| Job | 通过 | `Linux env solve dry-run` |
| Total duration | 通过 | 1m 51s |
| Job duration | 通过 | 1m 48s |
| Artifacts | 通过 | 无 |
| `metadata.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `bulk.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `base.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `data-entry.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `bulk-fastqc.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `bulk-salmon.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `bulk-star-featurecounts.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `r-bulk.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `report.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `scrna.yaml` dry-run | 通过 | `mamba env create --dry-run` |

### Commits

- `0ab2186` low-risk env expansion
- `ec832de` medium-risk env expansion

### 已验证范围

- GitHub Actions workflow 可由 `push` 触发。
- GitHub Actions runner 可完成 checkout。
- Miniforge/Mamba setup 可运行。
- 以下 env 可执行 `mamba env create --dry-run`：
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

### Warnings

以下 warnings 不影响本次 job 成功。本阶段只记录，不修复。

- Node.js 20 deprecation warning for `actions/checkout@v4` and `setup-miniconda@v3` forced onto Node.js 24。
- `auto-activate-base` is deprecated；后续可考虑 `auto-activate`。
- `defaults` channel may have been added implicitly；后续可考虑显式 channels 或 `conda-remove-defaults: true`。

### 未验证内容

- 剩余 3 个 env yaml 未验证：
  - `geo-rnaseq-mining/workflow/envs/sra-tools.yaml`
  - `geo-rnaseq-mining/workflow/envs/r-bulk-analysis.yaml`
  - `geo-rnaseq-mining/workflow/envs/python-single-cell.yaml`
- env 实际创建未验证。
- Snakemake production jobs 未运行。
- GEO/SRA 下载未验证。
- 真实生产数据分析未验证。

### 边界说明

- 本阶段只是 dry-run solve。
- 本阶段不等于生产 pipeline 可用。
- 本阶段不等于所有环境可解。
- 下一阶段唯一任务是只读规划剩余高风险/特殊 env dry-run 覆盖范围。
- 下一阶段只读规划候选为 `sra-tools.yaml`、`r-bulk-analysis.yaml`、`python-single-cell.yaml`。
- 下一阶段不直接修改 workflow，重点判断是否需要拆分独立 job、是否允许失败不阻断主 env solve、是否需要更长 timeout，以及如何确保不运行 SRA 下载或生产任务。

## 2026-07-04 — Environment Solve low-risk env dry-run expansion verification

### GitHub Actions run

| 检查项 | 结果 | 说明 |
|---|---|---|
| Workflow 识别 | 通过 | `Environment Solve` |
| Run | 通过 | `ci(envs): add low-risk env solve dry runs #5` |
| Trigger | 通过 | `push` |
| Branch | 通过 | `123` |
| Commit | 通过 | `0ab2186` |
| Job | 通过 | `Linux env solve dry-run` |
| Total duration | 通过 | 1m 32s |
| Job duration | 通过 | 1m 27s |
| Artifacts | 通过 | 无 |
| `metadata.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `bulk.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `base.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `data-entry.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `bulk-fastqc.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `bulk-salmon.yaml` dry-run | 通过 | `mamba env create --dry-run` |

### Commits

- `133e740` minimal dry-run restore
- `0ab2186` low-risk env expansion

### 已验证范围

- GitHub Actions workflow 可由 `push` 触发。
- GitHub Actions runner 可完成 checkout。
- Miniforge/Mamba setup 可运行。
- `geo-rnaseq-mining/workflow/envs/metadata.yaml` 可执行 `mamba env create --dry-run`。
- `geo-rnaseq-mining/workflow/envs/bulk.yaml` 可执行 `mamba env create --dry-run`。
- `geo-rnaseq-mining/workflow/envs/base.yaml` 可执行 `mamba env create --dry-run`。
- `geo-rnaseq-mining/workflow/envs/data-entry.yaml` 可执行 `mamba env create --dry-run`。
- `geo-rnaseq-mining/workflow/envs/bulk-fastqc.yaml` 可执行 `mamba env create --dry-run`。
- `geo-rnaseq-mining/workflow/envs/bulk-salmon.yaml` 可执行 `mamba env create --dry-run`。

### Warnings

以下 warnings 不影响本次 job 成功。本阶段只记录，不修复。

- Node.js 20 deprecation warning for `actions/checkout@v4` and `setup-miniconda@v3` forced onto Node.js 24。
- `auto-activate-base` is deprecated；后续可考虑 `auto-activate`。
- `defaults` channel may have been added implicitly；后续可考虑显式 channels 或 `conda-remove-defaults: true`。

### 未验证内容

- 全部 env yaml 未验证。
- env 实际创建未验证。
- Snakemake production jobs 未运行。
- GEO/SRA 下载未验证。
- 真实生产数据分析未验证。

### 边界说明

- 本阶段只是 dry-run solve。
- 本阶段不等于生产 pipeline 可用。
- 本阶段不等于所有环境可解。
- 下一阶段唯一任务是只读规划第二批中风险 env dry-run 覆盖范围。
- 下一阶段只读规划候选为 `bulk-star-featurecounts.yaml`、`r-bulk.yaml`、`report.yaml`、`scrna.yaml`。
- 下一阶段不直接修改 workflow，不加入 `sra-tools.yaml`、`r-bulk-analysis.yaml`、`python-single-cell.yaml`，等待用户确认。

## 2026-07-04 — Environment Solve minimal dry-run restore verification

### GitHub Actions run

| 检查项 | 结果 | 说明 |
|---|---|---|
| Workflow 识别 | 通过 | `Environment Solve` |
| Run | 通过 | `ci(envs): restore minimal env solve dry run #3` |
| Trigger | 通过 | `push` |
| Branch | 通过 | `123` |
| Commit | 通过 | `133e740` |
| Job | 通过 | `Linux env solve dry-run` |
| Total duration | 通过 | 55s |
| Job duration | 通过 | 51s |
| Artifacts | 通过 | 无 |
| `metadata.yaml` dry-run | 通过 | `mamba env create --dry-run` |
| `bulk.yaml` dry-run | 通过 | `mamba env create --dry-run` |

### Commits

- `77dbea8` trigger recognition
- `133e740` minimal dry-run restore

### 已验证范围

- Root `.github/workflows/env-solve.yml` 可被 GitHub Actions 识别。
- Workflow 可由 `push` 触发。
- GitHub Actions runner 可完成 checkout。
- Miniforge/Mamba setup 可运行。
- `geo-rnaseq-mining/workflow/envs/metadata.yaml` 可执行 `mamba env create --dry-run`。
- `geo-rnaseq-mining/workflow/envs/bulk.yaml` 可执行 `mamba env create --dry-run`。

### Warnings

以下 warnings 不影响本次 job 成功。本阶段只记录，不修复。

- Node.js 20 deprecation warning for `actions/checkout@v4` and `setup-miniconda@v3` forced onto Node.js 24。
- `auto-activate-base` is deprecated；后续可考虑 `auto-activate`。
- `defaults` channel may have been added implicitly；后续可考虑显式 channels 或 `conda-remove-defaults: true`。

### 未验证内容

- 全部 env yaml 未验证。
- env 实际创建未验证。
- Snakemake production jobs 未运行。
- GEO/SRA 下载未验证。
- 真实生产数据分析未验证。

### 边界说明

- 本阶段只是 minimal dry-run solve。
- 本阶段不等于生产 pipeline 可用。
- 本阶段不等于所有环境可解。
- 下一阶段唯一任务是只读规划是否逐步扩大 Environment Solve env yaml 覆盖范围，不得直接扩大到全部 env。
