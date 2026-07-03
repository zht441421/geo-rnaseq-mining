# Bulk 多数据集联合分析与 Meta 分析

## 权威输入

- `metadata/reviewed/dataset_plan.tsv` 是策略、dataset role 和纳入状态的唯一来源。
- `metadata/reviewed/contrasts.tsv` 是比较方向和 design formula 的唯一来源。
- 程序只评估技术可行性，不会把 `joint_model` 自动改成 Meta，也不会反向修改权威文件。
- 每个纳入 GSE 必须先完成 `results/per_dataset/{dataset_id}/bulk/.complete`。

支持的 `analysis_strategy`：

- `joint_model`
- `per_dataset_meta`
- `stratified_validation`
- `independent_only`

## 配置

```yaml
multi_dataset:
  enabled: true
  dataset_plan_file: metadata/reviewed/dataset_plan.tsv
  default_strategy: null
  prohibit_joint_model_when_dataset_group_confounded: true
  validation_datasets_in_discovery_model: false
  joint_model:
    allow_author_counts: false
    combat_seq:
      enabled: false
  meta:
    method: random_effects
    alpha: 0.05
    min_studies: 2
    loo_effect_change_threshold: 0.5
  stratified_validation:
    replication_alpha: 0.05
    require_same_direction: true
```

`meta.method` 可取 `fixed_effect`、`random_effects`、`fisher`、
`weighted_stouffer` 或 `robust_rank_aggregation`。

若 joint model 使用作者提供的整数 count，必须由用户明确将
`multi_dataset.joint_model.allow_author_counts` 设为 `true`，或在
`validation.dataset_compatibility.{dataset_id}` 中逐数据集批准，并为所有
dataset记录一致的 `quantification_source`。

## 兼容性评估

目标：

```bash
snakemake --profile profiles/local \
  results/compatibility/dataset_compatibility.tsv
```

评估包括物种、组织、数据类型、平台、文库策略/layout、参考、注释、
gene ID、count 来源、组内样本数、样本身份重叠、dataset/group 混杂和
样本量主导。评估结果不会修改 `analysis_strategy`。

## Joint Model

目标：

```bash
snakemake --profile profiles/local \
  results/merged_analysis/bulk/<analysis_id>/joint_model/.complete
```

硬门禁：

- 全部输入必须是已独立验证的非负整数 raw counts。
- gene ID及其顺序、样本名及其顺序必须一致。
- 验证集不得进入模型。
- dataset 与 group 不得完全混杂。
- 每个 dataset 内必须能估计每个 contrast。
- design matrix 必须满秩。
- 不得存在跨数据集重复/重叠样本。
- 样本量主导会被明确标记。

实际 formula 从 `contrasts.tsv` 读取。普通 ComBat 永不执行。
ComBat-seq 默认关闭；启用时仍不能修复完全混杂，并单独保存调整后矩阵，
不会覆盖原始 counts。

## Per-dataset Meta

目标：

```bash
snakemake --profile profiles/local \
  results/meta_analysis/bulk/<analysis_id>/per_dataset_meta/.complete
```

每个 GSE 的 DESeq2 结果以 `log2FoldChange`、`lfcSE`、`pvalue` 和
`sample_count` 汇总。所有模型同时保留效应方向和 dataset-specific effects；
Fisher、Stouffer 或 RRA 的 combined p-value 不会脱离效应方向解释。

LODO 稳定性结果位于：

```text
results/consensus/bulk/<analysis_id>/per_dataset_meta/<contrast_id>/
```

## Stratified Validation

目标：

```bash
snakemake --profile profiles/local \
  results/meta_analysis/bulk/<analysis_id>/stratified_validation/.complete
```

候选筛选、阈值、特征选择和 discovery effect 仅使用 role 为 `discovery`
的数据集。role 为 `validation` 的数据集只用于计算 validation effect、
方向一致性、validation p-value 和 replication status。

## 输出

- `results/compatibility/dataset_compatibility.tsv`
- `results/merged_analysis/bulk/`
- `results/meta_analysis/bulk/`
- `results/consensus/bulk/`

`independent_only` 只生成策略状态文件，不创建联合或 Meta 结果。
