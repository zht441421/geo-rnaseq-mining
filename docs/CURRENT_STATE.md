# 当前项目状态

最后更新：2026-07-02（Asia/Shanghai）；系统 Snakemake/Git 初始化修复后的阶段交接复核完成。

本文档只记录已从代码、实际文件或命令验证的事实。合成 fixture、单元测试或烟雾测试通过不代表真实 GSE 数据分析已经通过。

## 当前阶段

最终报告、审计和可复现性模块已实现；当前完成的是系统 Snakemake 入口和 Git 初始化修复的阶段交接。

## 已完成内容

- 已实现并接入 `workflow/scripts/final_reporting.py`：
  `collect_provenance`、`collect_software_versions`、`collect_reference_metadata`、
  `build_audit_trail`、`render_analysis_report`、`render_methods_report`、
  `package_results`、`reproducibility_manifest`、`snapshot_parameters`。
- 已实现 `workflow/rules/reporting.smk` 规则链；`reporting.enabled=true` 时目标为
  `results/reports/.complete`。
- 报告输出包括：
  `analysis_report.html`、`methods.md`、`validation_report.html`、`software_versions.tsv`、
  `reference_versions.tsv`、`file_checksums.tsv`、`parameter_snapshot.yaml`、
  `audit_trail.tsv`、`exclusions.tsv`、`warnings.tsv`、`reproducibility_manifest.tsv`。
- `analysis_report.html` 已包含项目目标、输入 GSE、纳入/排除样本、人工确认字段、dataset plan、
  每个 contrast、数据入口、原始文件和 checksum、参考版本、软件版本、参数、QC、异常样本、
  design formula、混杂检查、Bulk、单细胞、Pseudobulk、Meta、leave-one-dataset-out、bulk/scRNA 联合结果、
  warnings、已知限制和完整复现命令。
- 审计记录包含 original value、suggested value、final user value、review status、reviewer note、
  modification timestamp、source file 和 pipeline version。
- 软件版本采集通过 `workflow/scripts/run_rscript.py` 调用 Rscript，避免 Windows/Conda DLL PATH 问题。
- 结果包排除 FASTQ/FQ/FASTQ.GZ/FQ.GZ/SRA/BAM/CRAM，并避免把正在生成的结果包打进自身。
- 本阶段额外修复了审查发现的样本身份保护缺口：
  复合 `srr_id` 拆分查重、FASTQ R1/R2 同文件阻断、FASTQ 跨样本复用阻断、SRA 规则层拆分复合 SRR。
- 系统 Python 已安装并验证 Snakemake 8.30.0；`python -m snakemake --version` 不再因
  `No module named snakemake` 失败。
- 根目录新增 `.gitignore`，忽略本地工具链和生成目录 `work/`、`outputs/`，避免把项目环境或分析产物纳入首个提交。
- 已建立首个 Git commit，仓库不再是 unborn branch。

## 未完成内容

- 未运行真实数据最终报告。
- 未运行真实 bulk/single-cell/pseudobulk/integration 结果的最终审计和打包。
- 未提供真实 gene mapping；没有人工映射时只能 identity/canonicalize 版本号并记录限制。
- 真实 authority 文件仍缺少人工确认内容；程序不得将 suggested 字段当作事实。

## 修改文件

- `geo-rnaseq-mining/workflow/scripts/final_reporting.py`
- `geo-rnaseq-mining/workflow/rules/reporting.smk`
- `geo-rnaseq-mining/tests/unit/test_final_reporting.py`
- `geo-rnaseq-mining/workflow/scripts/validate_manifest.py`
- `geo-rnaseq-mining/workflow/rules/data_entry.smk`
- `geo-rnaseq-mining/tests/unit/test_preanalysis_validation.py`
- `geo-rnaseq-mining/tests/unit/test_project_skeleton.py`
- `.gitignore`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

## 测试结果

```text
python -m py_compile workflow/scripts/final_reporting.py workflow/scripts/validate_manifest.py
exit code 0
```

```text
python -m unittest tests.unit.test_final_reporting -v
Ran 4 tests in 0.110s
OK
```

```text
python -m unittest tests.unit.test_preanalysis_validation -v
Ran 18 tests in 0.194s
OK
```

```text
python -m unittest discover -s tests/unit -p "test_*.py" -v
Ran 118 tests in 10.792s
OK
```

```text
python -m unittest discover -s tests/integration -p "test_data_entry_pipeline.py" -v
Ran 1 test in 0.739s
OK
```

```text
python -m snakemake --snakefile workflow/Snakefile --directory . \
  --configfile config/config.yaml --dry-run --cores 1 --quiet
host: DESKTOP-0CSC9AV
exit code 0
```

```text
final_reporting minimal smoke test
FINAL_REPORT_SMOKE_EXIT=0
```

```text
python -m snakemake --version
8.30.0
exit code 0
```

```text
git check-ignore -v work outputs
.gitignore:2:work/    work
.gitignore:3:outputs/ outputs
exit code 0
```

```text
git ls-files work outputs
exit code 0; no tracked work/ or outputs/ files
```

```text
git rev-parse --short HEAD
b8b0aa3
exit code 0
```

## 仍失败或未运行的测试

- 未运行真实数据最终报告目标；真实 authority、真实 gene mapping 和真实分析结果尚未提供。
- 未运行网络 GEO/SRA 测试、真实 FASTQ 定量、真实 RDS 转换和完整真实数据 Snakemake 执行。
- 未运行 `pytest`；项目 README 指定测试入口为 `unittest`。

## 已知问题

- 真实 authority 文件仍缺少人工确认内容。
- 真实 gene mapping 尚未提供。
- 合成 fixture 和烟雾测试通过不代表真实数据分析通过。

## 不可违反的项目约束

- 不得修改 `docs/PROJECT_SPEC.md`，除非用户明确要求。
- reviewed authority 文件是正式事实来源；不得擅自确认或覆盖 `include`、`group`、`subject_id`、
  ontology、contrast、dataset strategy 或 gene mapping。
- 不得声称未运行的真实数据分析已经通过。
- 不得把 dominant cell type 解释为因果来源，只能解释为潜在主要表达来源。
- 不得把 deconvolution 结果直接解释为细胞迁移、疾病因果或机制。
- 不得自动使用 causal、driver、mechanism 等因果措辞，除非输入证据明确支持。
- 结果包不得包含大型原始 FASTQ/FQ/SRA/BAM/CRAM。
- 当前阶段交接后不得自动继续下一阶段开发。

## 当前 Git 状态

- 仓库根目录：`C:\Users\zht44\Documents\WORK FLOW`
- 当前分支：`master`
- 当前 commit：`b8b0aa3`（`Initialize geo RNA-seq mining workflow`）。
- 工作区状态：`work/` 和 `outputs/` 已由根目录 `.gitignore` 忽略，不纳入版本控制。
- 本次交接文档更新应单独提交；提交后工作区应保持干净。
- 仓库不再是 unborn branch。

## 下一步应该执行的任务

- 等待用户提供真实且人工确认的 manifest、contrasts、dataset_plan、celltype ontology、gene mapping、
  bulk/single-cell/pseudobulk/integration 输出。
- 启用 `reporting.enabled=true` 后，用项目环境运行最终报告 dry-run 和正式目标
  `results/reports/.complete`。
- 审阅 `audit_trail.tsv`、`warnings.tsv`、`file_checksums.tsv`、`reproducibility_manifest.tsv` 和
  `result_package_manifest.tsv`。

## 下一会话应首先读取的文件

- `docs/PROJECT_SPEC.md`
- `docs/DECISIONS.md`
- `docs/CURRENT_STATE.md`
- `docs/NEXT_TASK.md`
- `geo-rnaseq-mining/workflow/scripts/final_reporting.py`
- `geo-rnaseq-mining/workflow/rules/reporting.smk`
- `geo-rnaseq-mining/tests/unit/test_final_reporting.py`
- `geo-rnaseq-mining/workflow/scripts/validate_manifest.py`
