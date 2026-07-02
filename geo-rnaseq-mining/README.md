# geo-rnaseq-mining

`geo-rnaseq-mining` 是用于 GEO bulk RNA-seq、scRNA-seq 和 snRNA-seq
数据挖掘的可复现 Snakemake 工作流。当前已实现 GEO/SRA 元数据、人工审核、
预分析验证、数据入口盘点，以及按 GSE 独立运行的 bulk RNA-seq QC、定量、
DESeq2 和基础富集分析。

## 人工决策边界

正式分析只能使用以下人工确认文件：

- `metadata/reviewed/sample_manifest.tsv`
- `config/contrasts.tsv`
- `config/dataset_plan.tsv`
- `config/celltype_ontology.tsv`

优先级固定为：人工确认文件 > `config/config.yaml` > 程序建议值 >
GEO/SRA 原始字段。

本阶段输出不包含正式 `group`、`subject_id` 或 `include` 字段。程序不会根据
标题、characteristics 或多个 GSM 记录推断病例对照、受试者或重复关系。

建议清单中的正式字段保持空白，仅 `review_status` 默认为 `pending`。病例和
对照关键词只会产生 `case_candidate`、`control_candidate` 或 `conflict`，
不会形成正式分组。

## 已实现

- `fetch_geo_metadata`：使用 R GEOquery 获取 GSE、GSM 和 GPL。
- `fetch_geo_supplementary_index`：索引 supplementary 文件引用，可选 HEAD
  请求文件大小，不下载文件内容。
- `fetch_sra_runinfo`：通过 NCBI RunInfo 获取 GSM-SRX-SRR 映射，保留
  一个 GSM 对应的全部 SRR。
- `prepare_raw_metadata`：合并事件日志并生成 SHA-256。
- `prepare_manifest`：生成候选提示、冲突表和未映射记录。
- `generate_metadata_review_report`：生成独立 HTML 人工审核报告。
- 网络重试、成功响应缓存、明确缺失值和离线模拟测试。
- bulk 原始 gene-level count 矩阵严格校验。
- FastQC、MultiQC、Salmon + tximport，以及可选 STAR + featureCounts。
- 按 dataset 独立的样本级 QC、outlier 标记和 DESeq2 多 contrast 分析。
- GO、Reactome/KEGG GMT 富集、GSEA 和 DEG 方向/效应量汇总。

GEO 和 SRA 的完整来源字段分别保存在 `raw_metadata_json` 与
`raw_runinfo_json`。投影字段只用于检索，不覆盖来源字段。

## 初始化

```bash
cd geo-rnaseq-mining
mamba env create -f workflow/envs/base.yaml
conda activate geo-rnaseq-mining
```

R/GEOquery 环境由 Snakemake 按规则从 `workflow/envs/r-bulk.yaml` 创建。

## 配置与运行

在 `config/config.yaml` 中填写一个或多个 GSE：

```yaml
geo:
  accessions:
    - GSE100
```

校验四个人工确认文件：

```bash
snakemake --profile profiles/local \
  resources/validation/authority_config.validation.json
```

字段定义、合法值和错误示例见
`resources/AUTHORITY_CONFIG_DICTIONARY.md`。合法示例位于
`resources/examples/authority_config/`，不得直接视为当前项目的确认结果。

本地 dry-run：

```bash
snakemake --profile profiles/local --dry-run --printshellcmds
```

抓取原始元数据：

```bash
snakemake --profile profiles/local metadata/raw/metadata_checksums.sha256
```

SLURM dry-run：

```bash
snakemake --profile profiles/slurm --dry-run --printshellcmds
```

## 输出

- `metadata/raw/geo_series_raw.tsv`
- `metadata/raw/geo_samples_raw.tsv`
- `metadata/raw/geo_platforms_raw.tsv`
- `metadata/raw/sra_runinfo_raw.tsv`
- `metadata/raw/supplementary_files_raw.tsv`
- `metadata/raw/metadata_fetch_log.tsv`
- `metadata/raw/metadata_checksums.sha256`
- `metadata/suggested/sample_manifest_suggested.tsv`
- `metadata/suggested/metadata_conflicts.tsv`
- `metadata/suggested/unmapped_runs.tsv`
- `metadata/suggested/metadata_review_report.html`
- `results/compatibility/validated_manifest.tsv`
- `results/compatibility/manifest_errors.tsv`
- `results/compatibility/manifest_warnings.tsv`
- `results/compatibility/contrast_validation.tsv`
- `results/compatibility/dataset_plan_validation.tsv`
- `results/compatibility/design_matrix_validation.tsv`
- `results/compatibility/dataset_group_crosstab.tsv`
- `results/compatibility/sample_identity_conflicts.tsv`
- `results/compatibility/celltype_ontology_validation.tsv`
- `results/compatibility/validation_report.html`
- `results/compatibility/data_inventory.tsv`

正式分析前校验：

```bash
snakemake --profile profiles/local results/compatibility/validation_report.html
snakemake --profile profiles/local resources/validation/.preanalysis_validation_passed
```

启用 bulk 后运行单个数据集：

```bash
snakemake --profile profiles/local \
  results/per_dataset/<dataset_id>/bulk/.complete
```

bulk 入口、参考配置、输出和 Windows/Linux 环境说明见
`resources/BULK_ANALYSIS.md`。

错误等级、检查代码和修复方法见
`resources/PREANALYSIS_VALIDATION.md`。

表达数据入口盘点：

```bash
snakemake --profile profiles/local results/compatibility/data_inventory.tsv
```

下载默认关闭。入口识别、exploratory 限制、SRA 缓存与可选集成测试见
`resources/DATA_ENTRY.md`。

缓存位于 `resources/cache/metadata/`。原始输出不会被脚本原地修改；Snakemake
仅在目标缺失或依赖变化时重新生成。

## 测试

离线单元测试：

```bash
python -m unittest discover -s tests/unit -p "test_*.py" -v
```

可选真实 GEO 集成测试：

```bash
RUN_GEO_NETWORK_TESTS=1 python -m unittest discover \
  -s tests/integration -p "test_real_geo_optional.py" -v
```

可通过 `GEO_TEST_ACCESSION` 替换默认的 `GSE100`。集成测试要求当前环境已安装
R、GEOquery、jsonlite 和 optparse。

## 日志与资源规范

- 日志：`logs/{module}/{rule}.log`
- benchmark：`benchmarks/{module}/{rule}.tsv`
- 规则资源：显式声明 `threads`、`mem_mb`、`runtime_min` 和 `disk_mb`
- 网络事件：汇总到 `metadata/raw/metadata_fetch_log.tsv`
- 成功缓存：`resources/cache/metadata/`

详细要求见 `resources/RESOURCE_POLICY.md`。

## 当前能力与边界

- bulk 单数据集支持 count 矩阵、FASTQ 定量、样本 QC、DESeq2、富集和可选扩展模块
- bulk 多数据集支持兼容性评估、joint model、per-dataset Meta、分层验证和 LODO 稳定性分析
- scRNA-seq/snRNA-seq 支持每数据集 QC、人工映射细胞类型、subject-level pseudobulk 和细胞比例分析
- 可生成带输入哈希、权威配置哈希和验证状态的项目级 HTML 报告
- 大型 supplementary 与 SRA 下载默认关闭，必须由配置显式启用
- bulk 与单细胞结果的跨模态联合解释尚未实现
- 真实数据运行仍要求用户完成 reviewed manifest、contrasts、dataset plan 和 cell-type ontology

## 许可证

`LICENSE` 是保守占位文件。项目所有者需明确选择许可证后再发布。
