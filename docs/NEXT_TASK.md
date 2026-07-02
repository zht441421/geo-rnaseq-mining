# 下一阶段任务

- **task_id**：FINAL-REPORT-RUN-001
- **状态**：blocked_external_input；等待真实结果、人工确认 authority 和 gene mapping 后启动
- **最后复核**：2026-07-02；系统 Snakemake/Git 初始化修复已复核，真实报告运行仍等待外部输入

## 当前目标

在真实分析结果和人工确认文件到位后，启用最终报告模块，生成 `results/reports/` 下的报告、审计、
checksum、参数快照、可复现 manifest 和最终结果包。

## 必须准备的输入

- 已人工确认的 `metadata/reviewed/sample_manifest.tsv`
- 已人工确认的 `config/contrasts.tsv`
- 已人工确认的 `config/dataset_plan.tsv`
- 已人工确认的 `config/celltype_ontology.tsv`
- 真实 gene mapping，或用户明确接受 identity/canonicalize 版本号并记录限制
- 真实 bulk 单数据集、joint、Meta、validation/leave-one-dataset-out 结果
- 真实 single-cell marker、cell type 平均表达、表达比例、pseudobulk 和 pseudobulk Meta 结果
- 真实 bulk/single-cell integration 和 consensus 输出
- 可用的 Snakemake 运行环境；系统 Python 和项目环境均已可运行 `python -m snakemake`

## 下一步具体任务

1. 检查真实 authority 文件是否包含人工确认内容；不得把 suggested 字段当作事实。
2. 检查 `config/config.yaml` 中 `reporting.enabled=true` 和 `reporting.output_dir=results/reports`。
3. 使用项目环境运行最终报告 dry-run。
4. 正式运行 `results/reports/.complete`。
5. 审阅 `analysis_report.html`、`methods.md`、`validation_report.html`。
6. 审阅 `audit_trail.tsv`、`warnings.tsv`、`exclusions.tsv`、`file_checksums.tsv`、
   `reproducibility_manifest.tsv` 和 `result_package_manifest.tsv`。
7. 确认结果包不包含大型原始 FASTQ/FQ/SRA/BAM/CRAM。
8. 确认报告没有把未确认信息表述为事实，也没有无证据的因果措辞。
9. 更新阶段交接文档并记录真实运行命令、结果和未运行项。

## 必须运行的测试

```powershell
Set-Location "C:\Users\zht44\Documents\WORK FLOW\geo-rnaseq-mining"
python -m unittest discover -s tests/unit -p "test_*.py" -v
python -m unittest discover -s tests/integration -p "test_data_entry_pipeline.py" -v
```

使用项目环境运行 Snakemake：

```powershell
& "C:\Users\zht44\Documents\WORK FLOW\work\tools\envs\geo-rnaseq-mining\python.exe" `
  -m snakemake --snakefile workflow/Snakefile --directory . `
  --configfile config/config.yaml --dry-run --cores 1 --quiet
```

正式报告运行示例：

```powershell
& "C:\Users\zht44\Documents\WORK FLOW\work\tools\envs\geo-rnaseq-mining\python.exe" `
  -m snakemake --snakefile workflow/Snakefile --directory . `
  --configfile config/config.yaml --use-conda --cores <N> results/reports/.complete
```

## 禁止事项

- 不得修改 `docs/PROJECT_SPEC.md`，除非用户明确要求。
- 不得未经用户确认修改 `include`、`group`、`subject_id`、ontology、contrast、dataset strategy 或 gene mapping。
- 不得声称未运行的真实数据分析已经通过。
- 不得把 dominant cell type 解释为因果来源。
- 不得把 deconvolution 结果解释为细胞迁移、疾病因果或机制。
- 不得在最终结果包中包含大型原始 FASTQ/FQ/SRA/BAM/CRAM。
- 不得在阶段交接过程中自动开始下一阶段开发。

## 当前阻塞与注意事项

- 真实 authority 文件仍缺少人工确认内容。
- 真实 gene mapping 尚未提供。
- 真实联合分析、pseudobulk、Meta 和 integration 输出尚未运行或审阅。
- 本阶段测试使用合成 fixture 和 CLI smoke test，不代表真实数据最终报告已经通过。
- 系统 Python 已安装 Snakemake 8.30.0；项目环境中的 Snakemake 也可用。
- 仓库已建立首个 commit；下一阶段开始前仍应先检查 `git status`，确认是否存在交接文档的未提交修改。
