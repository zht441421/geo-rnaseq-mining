# 验证记录

所有日期使用 Asia/Shanghai 时区。本文档记录阶段验证事实、范围边界、warnings 和未验证内容。

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
