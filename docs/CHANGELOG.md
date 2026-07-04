# 变更记录

所有日期使用 Asia/Shanghai 时区。按最新记录在前的顺序维护。

## 2026-07-04 — Environment Solve minimal dry-run restore verification

### 新增与删除文件

- 新增 `docs/VALIDATION.md`，记录 GitHub Actions 验证、warnings、边界和未验证内容。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`
- `docs/VALIDATION.md`

### 接口、配置与决策变化

- Root `.github/workflows/env-solve.yml` 已在本阶段恢复最小真实 env solve dry-run。
- GitHub Actions workflow `Environment Solve` 已成功识别并由 `push` 触发。
- 本次交接只更新 Markdown 文档；未继续修改 workflow、schema、CI、env yaml、测试或代码文件。
- 未产生新的用户确认分析决策；`docs/DECISIONS.md` 保持不变。
- 相关 commits：
  - `77dbea8` trigger recognition
  - `133e740` minimal dry-run restore

### 验证变化

- GitHub Actions run `ci(envs): restore minimal env solve dry run #3` 成功。
- Branch：`123`。
- Commit：`133e740`。
- Job：`Linux env solve dry-run`。
- Total duration：55s；job duration：51s。
- Artifacts：无。
- `geo-rnaseq-mining/workflow/envs/metadata.yaml` 已通过 `mamba env create --dry-run`。
- `geo-rnaseq-mining/workflow/envs/bulk.yaml` 已通过 `mamba env create --dry-run`。

### Warnings 记录

- Node.js 20 deprecation warning for `actions/checkout@v4` and `setup-miniconda@v3` forced onto Node.js 24。
- `auto-activate-base` deprecated；后续可考虑 `auto-activate`。
- `defaults` channel may have been added implicitly；后续可考虑显式 channels 或 `conda-remove-defaults: true`。

### 仍未运行

- 全部 env yaml 未验证。
- env 实际创建未验证。
- Snakemake production jobs 未运行。
- GEO/SRA 下载未验证。
- 真实生产数据分析未验证。

### 下一阶段边界

- 下一阶段唯一任务是只读规划是否逐步扩大 Environment Solve env yaml 覆盖范围。
- 必须先列出 `geo-rnaseq-mining/workflow/envs/*.yaml`，按风险和依赖分组，提出逐步加入 dry-run solve 的计划。
- 不得直接扩大到全部 env，必须等待用户确认。

## 2026-07-02 — Snakemake/Git 修复阶段交接复核

### 新增与删除文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 复核确认系统 Python 可运行 Snakemake 8.30.0。
- 复核确认首个 Git commit 已建立，当前记录的 HEAD 为 `b8b0aa3`。
- 复核确认 `work/` 和 `outputs/` 被根目录 `.gitignore` 忽略且未进入 Git 跟踪。
- 未产生新的用户确认分析决策；`docs/DECISIONS.md` 保持不变。
- 未启动真实数据最终报告或下一阶段开发。

### 测试变化

- 离线单元测试 118 项通过。
- 离线数据入口集成测试 1 项通过。
- 系统 Python Snakemake dry-run 通过。
- `python -m snakemake --version` 通过，返回 `8.30.0`。
- Git 忽略和跟踪检查通过：`work/`、`outputs/` 未被跟踪。

### 仍未运行

- 未运行真实数据最终报告目标；缺少真实人工确认 authority、gene mapping 和真实分析结果。

## 2026-07-02 — 修复系统 Snakemake 入口并初始化 Git 状态

### 新增与删除文件

- 新增根目录 `.gitignore`，忽略本地工具链和生成目录 `work/`、`outputs/`。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 系统 Python 已安装 Snakemake 8.30.0，`python -m snakemake --version` 可直接返回版本号。
- `work/` 和 `outputs/` 明确作为本地环境或生成产物排除出 Git 跟踪。
- 本次不涉及真实数据运行，也不改变用户确认 authority、gene mapping 或分析策略。

### 测试变化

- `python -m snakemake --version` 通过，返回 `8.30.0`。
- `git check-ignore -v work outputs` 通过，确认两个目录由根目录 `.gitignore` 忽略。

### 仍未运行

- 未运行真实数据最终报告目标；缺少真实人工确认 authority、gene mapping 和真实分析结果。

## 2026-07-02 — 最终报告模块阶段交接复核

### 新增与删除文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 本次执行阶段交接复核；未继续开发下一阶段功能。
- 复核确认最终报告实现已包含核心审计表嵌入、methods 软件/参考版本、结果包排除大型原始测序文件。
- 未产生新的用户确认分析决策；`docs/DECISIONS.md` 保持不变。

### 测试变化

- `py_compile` 通过：`final_reporting.py` 和 `validate_manifest.py`。
- final reporting 单元测试 4 项通过。
- preanalysis validation 单元测试 18 项通过。
- 离线单元测试 118 项通过。
- 离线数据入口集成测试 1 项通过。
- 项目环境 Snakemake dry-run 通过。
- final_reporting 最小烟雾测试通过。

### 仍未运行

- 未运行真实数据最终报告目标；缺少真实人工确认 authority、gene mapping 和真实分析结果。
- 系统 Python 的 `python -m snakemake --version` 失败，原因是系统 Python 未安装 Snakemake；项目环境可用。

## 2026-07-02 — 实现最终报告、审计和可复现性模块

### 新增文件

- `geo-rnaseq-mining/workflow/scripts/final_reporting.py`
- `geo-rnaseq-mining/tests/unit/test_final_reporting.py`

### 修改文件

- `geo-rnaseq-mining/workflow/rules/reporting.smk`
- `geo-rnaseq-mining/tests/unit/test_project_skeleton.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- `reporting.smk` 现在注册并串联：
  `collect_provenance`、`collect_software_versions`、`collect_reference_metadata`、
  `build_audit_trail`、`render_analysis_report`、`render_methods_report`、`package_results`。
- 新增报告产物：
  `analysis_report.html`、`methods.md`、`validation_report.html`、`software_versions.tsv`、
  `reference_versions.tsv`、`file_checksums.tsv`、`parameter_snapshot.yaml`、
  `audit_trail.tsv`、`exclusions.tsv`、`warnings.tsv`、`reproducibility_manifest.tsv`。
- `collect_software_versions` 通过 `run_rscript.py` 获取 Rscript 版本，以兼容 Windows/Conda DLL 路径。
- `package_results` 排除大型原始测序文件，并避免把正在生成的结果包打进自身。
- 未产生新的用户确认分析决策；`docs/DECISIONS.md` 保持不变。

### 测试变化

- 新增 3 项 final reporting 单元测试并全部通过。
- 项目离线单元测试从 111 项增至 114 项，全部通过。
- final_reporting CLI 烟雾测试通过，生成临时 `analysis_report.html`、`methods.md` 和
  `software_versions.tsv`。
- Snakemake dry-run 未运行：当前 PowerShell PATH 中没有 `snakemake` 命令。

### 不兼容变化

- 旧的 `generate_project_report` Snakemake 规则不再作为 reporting 主目标；报告阶段改由最终报告规则链驱动。

## 2026-07-02 — bulk/single-cell联合分析阶段交接

### 新增与删除文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 无代码接口或配置变化。
- 本次只执行阶段交接复核；未继续开发下一阶段功能，也未运行真实数据联合分析。
- 未产生新的用户确认决策；`docs/DECISIONS.md`保持不变。

### 测试变化

- Python compileall重新通过。
- 7项bulk/single-cell联合分析指定测试重新运行并全部通过。
- 111项离线单元测试重新运行并全部通过。
- 1项离线数据入口集成测试重新运行并通过。
- 默认Snakemake DAG dry-run重新通过。
- 临时启用`bulk_scrna_integration.enabled=true`时Snakemake DAG dry-run通过。
- bulk/single-cell integration CLI烟雾测试重新通过，输出写入临时目录。

### 仍未运行

- 未运行真实bulk结果与真实single-cell结果的联合分析；仍需用户提供并人工确认真实authority输入、
  gene mapping、ontology、bulk/scRNA结果路径和分析策略。

## 2026-07-02 — 实现bulk RNA-seq与单细胞RNA-seq联合分析模块

### 新增文件

- `geo-rnaseq-mining/workflow/scripts/run_bulk_scrna_integration.py`
- `geo-rnaseq-mining/workflow/rules/integration.smk`
- `geo-rnaseq-mining/tests/unit/test_bulk_scrna_integration.py`

### 修改文件

- `geo-rnaseq-mining/config/config.yaml`
- `geo-rnaseq-mining/workflow/schemas/config.schema.yaml`
- `geo-rnaseq-mining/workflow/Snakefile`
- `geo-rnaseq-mining/workflow/scripts/README.md`
- `geo-rnaseq-mining/tests/unit/test_project_skeleton.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 新增`bulk_scrna_integration`配置块，默认`enabled: false`。
- 新增Snakemake规则`bulk_scrna_integration`，输出根目录为`results/integration/`和`results/consensus/`。
- 新增基因ID统一、unmapped/ambiguous记录、bulk-scRNA concordance、consensus gene、
  candidate score、dataset support和cell type specific effect输出。
- 去卷积接口默认关闭，输出解释限制，明确区分cell fraction change与within-celltype transcription change。
- dominant cell type只作为潜在主要表达来源，不作为因果来源解释。

### 测试变化

- 新增7项bulk/single-cell联合分析单元测试并全部通过。
- Python compileall通过。
- 111项离线单元测试全部通过。
- 1项离线数据入口集成测试通过。
- 默认Snakemake DAG dry-run通过。
- 使用临时配置启用`bulk_scrna_integration.enabled=true`时DAG dry-run通过。
- bulk/single-cell integration CLI烟雾测试通过并生成全部核心输出表和图形数据表。

### 仍未运行

- 未运行真实bulk结果与真实single-cell结果的联合分析；仍需用户提供并人工确认真实authority输入、
  gene mapping、ontology、bulk/scRNA结果路径和分析策略。

## 2026-07-02 — 修复Windows Rscript启动PATH问题

### 新增文件

- `geo-rnaseq-mining/workflow/scripts/run_rscript.py`

### 修改文件

- `geo-rnaseq-mining/workflow/rules/metadata.smk`
- `geo-rnaseq-mining/workflow/rules/bulk.smk`
- `geo-rnaseq-mining/workflow/rules/multi_dataset.smk`
- `geo-rnaseq-mining/workflow/rules/single_cell.smk`
- `geo-rnaseq-mining/workflow/scripts/single_cell_common.py`
- `geo-rnaseq-mining/tests/unit/test_project_skeleton.py`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`

### 接口、配置与决策变化

- 新增R脚本包装器`run_rscript.py`，在Windows下自动为R子进程PATH前置Conda
  `Library/bin`、`Lib/R/bin`和`Scripts`目录。
- Snakemake中所有R规则改为通过`python workflow/scripts/run_rscript.py ...`启动。
- RDS到H5AD转换也改为通过包装器启动R脚本。
- 未修改真实authority文件；reviewed manifest、contrasts、dataset plan和ontology仍需用户人工确认。

### 测试变化

- Python compileall通过。
- `test_project_skeleton.py`通过，新增检查确保工作流R调用使用包装器。
- 103项离线单元测试全部通过。
- 1项离线数据入口集成测试通过。
- 默认Snakemake DAG dry-run通过。
- 在未手动设置R PATH的情况下，`run_rscript.py`成功解析`run_single_cell_pseudobulk_deseq2.R`。
- 最小pseudobulk DESeq2烟雾测试通过，调用链为Python包装器到Rscript。

### 仍未解决

- 真实authority文件仍缺少人工确认内容；这是外部输入阻塞，不能由程序自动填充。

## 2026-07-02 — pseudobulk实现阶段交接

### 新增与删除文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 无代码接口或配置变化。
- 本次只执行阶段交接；未继续开发下一阶段功能，也未运行真实数据分析。
- 未产生新的用户确认决策；`docs/DECISIONS.md`保持不变，继续遵守`DEC-023`。

### 测试变化

- Python compileall重新通过。
- 8项pseudobulk指定回归测试重新运行并全部通过。
- 102项离线单元测试重新运行并全部通过。
- 1项离线数据入口集成测试重新运行并通过。
- config schema验证重新通过。
- 默认Snakemake DAG dry-run重新通过。
- `run_single_cell_pseudobulk_deseq2.R`静态解析重新通过。
- 最小pseudobulk DESeq2烟雾测试重新通过，`.complete`记录`replicate_unit=subject_id`和
  `cell_replication_used=false`。
- 未运行真实单细胞数据、真实RDS转换、网络GEO/SRA和正式真实数据Snakemake执行。

### Git状态

- 当前分支`master`，HEAD仍未建立。
- `docs/`、`geo-rnaseq-mining/`和`work/`仍为未跟踪目录。

## 2026-07-02 — pseudobulk实现阶段交接复核

### 新增与删除文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 无代码接口或配置变化。
- 本次仅执行阶段交接复核，未继续开发下一阶段功能。
- 未产生新的用户确认决策；`docs/DECISIONS.md`保持不变，继续遵守`DEC-023`。

### 测试变化

- Python compileall重新通过。
- 102项离线单元测试重新运行并全部通过。
- 1项离线数据入口集成测试重新运行并通过。
- config schema验证重新通过。
- 默认Snakemake DAG dry-run重新通过。
- `run_single_cell_pseudobulk_deseq2.R`静态解析重新通过。
- 最小pseudobulk DESeq2烟雾测试重新通过，`.complete`记录`replicate_unit=subject_id`和
  `cell_replication_used=false`。
- 未运行真实单细胞数据、真实RDS转换、网络GEO/SRA和正式真实数据Snakemake执行。

### Git状态

- 当前分支`master`，HEAD仍未建立。
- `docs/`、`geo-rnaseq-mining/`和`work/`仍为未跟踪目录。

## 2026-07-02 — 实现完整单细胞subject-level pseudobulk差异分析

### 新增文件

- `geo-rnaseq-mining/workflow/scripts/pseudobulk_common.py`
- `geo-rnaseq-mining/workflow/scripts/prepare_joint_pseudobulk.py`
- `geo-rnaseq-mining/workflow/scripts/run_pseudobulk_meta_analysis.py`
- `geo-rnaseq-mining/tests/unit/test_pseudobulk_de.py`

### 修改文件

- `geo-rnaseq-mining/config/config.yaml`
- `geo-rnaseq-mining/workflow/schemas/config.schema.yaml`
- `geo-rnaseq-mining/workflow/rules/single_cell.smk`
- `geo-rnaseq-mining/workflow/scripts/single_cell_common.py`
- `geo-rnaseq-mining/workflow/scripts/prepare_single_cell_pseudobulk.py`
- `geo-rnaseq-mining/workflow/scripts/run_single_cell_pseudobulk_deseq2.R`
- `geo-rnaseq-mining/resources/SINGLE_CELL_ANALYSIS.md`
- `geo-rnaseq-mining/workflow/scripts/README.md`
- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 新增正式pseudobulk输出树`results/per_dataset/{dataset_id}/pseudobulk/`。
- 新增跨数据集输出树`results/merged_analysis/scrna_pseudobulk/`和
  `results/meta_analysis/scrna_pseudobulk/`。
- pseudobulk聚合现在使用`layers["counts"]`，按dataset、subject、sample、cell type
  和配置的额外分层变量聚合。
- 每个pseudobulk样本输出`cell_type`、`total_UMI`、`detected_genes`、
  `eligibility`和`exclusion_reason`。
- `single_cell.pseudobulk`新增`min_cells_per_pseudobulk`、
  `min_subjects_per_group`、`min_total_counts`、`min_detected_genes`和
  `extra_strata`。
- 支持per-dataset pseudobulk DESeq2、combined pseudobulk joint model、
  per-dataset pseudobulk Meta和stratified validation规则。
- 未产生新的用户决策；继续遵守`DEC-023`。

### Bug修复与防护

- `prepare_single_cell_pseudobulk.py`现在拒绝缺失`subject_id`。
- pseudobulk DESeq2显式拒绝非raw integer aggregated counts。
- combined pseudobulk joint preflight阻断dataset/group完全混杂、设计不满秩、
  每数据集组间比较不可估计和供体数不足。
- 小型合成数据中DESeq2离散度拟合失败时，统计流程回退到gene-wise dispersion；
  可视化变换失败时回退到`log2(normalized_counts + 1)`，不改变DESeq2原始counts输入。

### 测试变化

- 新增8项pseudobulk回归测试并全部通过。
- Python compileall通过。
- config schema验证通过。
- 102项离线单元测试全部通过。
- 1项离线数据入口集成测试通过。
- `run_single_cell_pseudobulk_deseq2.R`静态解析通过。
- 最小pseudobulk DESeq2烟雾测试通过，输出`.complete`且记录
  `cell_replication_used=false`。
- 默认Snakemake DAG dry-run通过。
- 未运行真实单细胞数据、真实RDS转换和正式GSE分析；仍需用户输入与人工确认。

### Git状态

- 当前分支`master`，HEAD仍未建立。
- `docs/`、`geo-rnaseq-mining/`和`work/`仍为未跟踪目录。

### 不兼容变更

- 正式单细胞pseudobulk输出从旧的
  `results/per_dataset/{dataset_id}/single_cell/pseudobulk/`迁移到
  `results/per_dataset/{dataset_id}/pseudobulk/`。
- H5AD/AnnData pseudobulk输入必须显式包含`layers["counts"]`。

## 2026-07-02 — subject-level pseudobulk需求冻结与阶段交接

### 新增与删除文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`
- `docs/DECISIONS.md`

### 接口、配置与决策变化

- 无代码接口或配置变化。
- 未继续实现用户刚提出的pseudobulk下一阶段功能；本次仅执行阶段交接。
- 新增`DEC-023`，记录单细胞subject-level pseudobulk差异分析的已确认要求。
- 下一阶段任务更新为`SC-PSEUDOBULK-DE-001`。

### 测试变化

- Python compileall通过。
- 94项离线单元测试重新运行并全部通过。
- 1项离线数据入口集成测试重新运行并通过。
- 默认Snakemake DAG dry-run通过。
- Rscript当前在本机启动失败，返回`-1073741515`；R脚本解析本次未通过。
- 用户新要求的pseudobulk差异分析测试尚未添加或运行。

### Git状态

- 当前分支`master`，HEAD仍未建立。
- `docs/`、`geo-rnaseq-mining/`和`work/`仍为未跟踪目录。
- 本次交接前未发现已跟踪代码改动；本次只修改`docs/`文档。

### 不兼容变更

- 无代码不兼容变更。

## 2026-07-02 — 单细胞预处理阶段交接复核

### 新增与删除文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 无代码接口或配置变化。
- 未产生新的用户确认决策；继续遵守`DEC-015`和`DEC-022`。
- 本次只执行阶段交接，未开发跨数据集整合或其他下一阶段功能。

### 测试变化

- Python compileall重新通过。
- 94项离线单元测试重新运行并全部通过。
- 1项离线数据入口集成测试重新运行并通过。
- RDS转换脚本重新通过R静态解析。
- 默认DAG和单细胞预处理启用态10-job DAG重新dry-run通过。
- 本次未重跑实现阶段的60细胞端到端和两个doublet后端烟雾测试；
  未运行项已明确写入`CURRENT_STATE.md`。

### Git状态

- 当前分支`master`，HEAD仍未建立。
- `docs/`、`geo-rnaseq-mining/`和`work/`仍为未跟踪目录。

### 不兼容变更

- 无。

## 2026-07-02 — 实现scRNA-seq/snRNA-seq单数据集预处理

### 新增文件

- `geo-rnaseq-mining/workflow/scripts/preprocess_single_cell_dataset.py`
- `geo-rnaseq-mining/workflow/scripts/prepare_single_cell_pseudobulk.py`
- `geo-rnaseq-mining/workflow/scripts/convert_single_cell_rds.R`
- `geo-rnaseq-mining/tests/unit/test_single_cell_preprocessing.py`

### 修改文件

- `geo-rnaseq-mining/workflow/scripts/single_cell_common.py`
- `geo-rnaseq-mining/workflow/rules/single_cell.smk`
- `geo-rnaseq-mining/workflow/scripts/validate_manifest.py`
- `geo-rnaseq-mining/config/config.yaml`
- `geo-rnaseq-mining/workflow/schemas/config.schema.yaml`
- `geo-rnaseq-mining/workflow/envs/python-single-cell.yaml`
- `geo-rnaseq-mining/resources/SINGLE_CELL_ANALYSIS.md`
- `geo-rnaseq-mining/workflow/scripts/README.md`
- `geo-rnaseq-mining/tests/unit/test_project_skeleton.py`
- `docs/CURRENT_STATE.md`
- `docs/DECISIONS.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`

### 删除文件

- 无。

### 接口变化

- 新增预处理目标
  `results/per_dataset/{dataset_id}/single_cell/preprocessing/.complete`。
- 新增pre-QC、post-QC和clustered三个AnnData对象。
- 新增分样本QC阈值、sample summary、doublet/ambient状态、cluster marker、
  样本组成、建议注释和四类图形。
- barcode接口改为`dataset_id:sample_id:original_barcode`。
- 单细胞预处理与pseudobulk下游现在由独立配置开关控制。

### 配置变化

- QC支持`hard`、`mad`和`combined`，并配置MT/ribo/HB、complexity阈值。
- Doublet支持`scrublet`与`doubletdetection`，按样本运行。
- Ambient RNA支持`none`和`low_count_profile`评估。
- 新增HVG、scaling、neighbors、Leiden、marker和marker-set建议参数。
- 单细胞环境新增igraph、leidenalg、DoubletDetection、Seurat、
  SingleCellExperiment和zellkonverter。

### Bug修复与防护

- H5AD缺少counts layer时fail closed，不再把未知`X`猜作raw counts。
- 拒绝重复barcode、非整数counts、缺失subject_id和样本间gene顺序差异。
- 任一样本零细胞保留时阻断而非静默删除整个样本。
- raw counts在normalize、scale、PCA、UMAP和聚类过程中保持不变。
- 自动注释只写`suggested_annotation`，不覆盖author或人工确认标签。
- manifest验证现在接受RDS和Cell Ranger目录。

### 测试变化

- 单元测试从86增至94，全部通过；离线集成测试1项通过。
- 新增用户要求的8类单细胞预处理测试。
- 60细胞、2样本、100基因端到端预处理实际运行通过，18项产物齐全。
- Scrublet和DoubletDetection均完成2样本、120细胞的真实分样本烟雾测试。
- RDS转换脚本通过R静态解析。
- 默认DAG和单细胞预处理启用态10-job DAG dry-run通过。
- 真实10X/Cell Ranger/RDS、真实GEO数据及跨数据集整合未运行。

### 不兼容变更

- H5AD正式输入现在必须明确提供`layers["counts"]`。
- 单细胞默认目标只完成预处理；pseudobulk下游须显式设置
  `single_cell.downstream_analysis_enabled=true`。

## 2026-07-02 — 完成未解决问题阶段交接复核

### 新增与删除文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/CHANGELOG.md`
- `docs/NEXT_TASK.md`

### 接口、配置与决策变化

- 无代码接口或配置变化。
- 未产生新的用户确认分析决策；`DEC-015`继续约束交接后不得自动开发下一阶段。
- 重新核验`docs/`、bulk、多数据集、单细胞和reporting规则均存在。
- Git仍为unborn `master`，`docs/`、`geo-rnaseq-mining/`和`work/`未跟踪。

### 测试变化

- Python compileall通过。
- 86项离线单元测试重新运行并全部通过。
- 1项离线数据入口集成测试重新运行并通过。
- 5个R分析脚本解析及9个R依赖加载通过。
- 默认Snakemake DAG dry-run通过。
- single-cell与reporting启用态DAG dry-run通过，共21 jobs。
- 未重跑真实网络、真实FASTQ、ComBat-seq、正式全流程及实现阶段的模拟R烟雾测试；
  未运行项已明确写入`CURRENT_STATE.md`。

### 不兼容变更

- 无。

## 2026-07-02 — 清理未解决问题并补齐单细胞、可选分析与报告

### 新增文件

- `geo-rnaseq-mining/workflow/scripts/single_cell_common.py`
- `geo-rnaseq-mining/workflow/scripts/prepare_single_cell_dataset.py`
- `geo-rnaseq-mining/workflow/scripts/run_cell_proportion.py`
- `geo-rnaseq-mining/workflow/scripts/run_single_cell_pseudobulk_deseq2.R`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_optional_modules.R`
- `geo-rnaseq-mining/workflow/scripts/generate_project_report.py`
- `geo-rnaseq-mining/resources/SINGLE_CELL_ANALYSIS.md`
- `geo-rnaseq-mining/resources/REPORTING.md`
- `geo-rnaseq-mining/tests/unit/test_single_cell_and_reporting.py`

### 修改文件

- `geo-rnaseq-mining/workflow/rules/single_cell.smk`
- `geo-rnaseq-mining/workflow/rules/reporting.smk`
- `geo-rnaseq-mining/workflow/rules/bulk.smk`
- `geo-rnaseq-mining/workflow/Snakefile`
- `geo-rnaseq-mining/config/config.yaml`
- `geo-rnaseq-mining/workflow/schemas/config.schema.yaml`
- `geo-rnaseq-mining/workflow/envs/python-single-cell.yaml`
- `geo-rnaseq-mining/workflow/envs/r-bulk-analysis.yaml`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_deseq2.R`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_joint_model.R`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_enrichment.R`
- `geo-rnaseq-mining/workflow/scripts/validate_celltype_ontology.py`
- `geo-rnaseq-mining/README.md`
- `geo-rnaseq-mining/resources/BULK_ANALYSIS.md`
- `geo-rnaseq-mining/workflow/scripts/README.md`
- `geo-rnaseq-mining/tests/unit/test_project_skeleton.py`
- `docs/CURRENT_STATE.md`
- `docs/DECISIONS.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`

### 删除文件

- 无。

### 接口与配置变化

- 新增`results/per_dataset/{dataset_id}/single_cell/`分析树。
- 新增subject-level pseudobulk、subject-level cell proportion和单细胞provenance。
- 新增四个默认关闭的bulk可选模块及各自方法参数。
- 新增`results/reports/`项目报告、结果清单和authority哈希。
- 单细胞与reporting配置由schema严格验证。

### Bug修复

- 修复R读取空`subset_column`为`NA`后误判未知筛选列的问题。
- 修复DEG热图注释存在空值或未使用因子水平时`pheatmap`失败的问题。
- survival逐基因Cox模型现在跳过不收敛基因，并在无可估计模型时明确返回状态。
- ontology门禁不再要求尚未生成的derived metrics；运行时准备阶段仍执行严格检查。
- 可选模块状态不再由错误的嵌套配置路径触发。

### 测试变化

- 单元测试从79增至86，全部通过；离线集成测试1项通过。
- 默认DAG dry-run通过（17 jobs）；single-cell与reporting启用态通过（21 jobs）。
- bulk、single-cell pseudobulk和joint DESeq2均用200基因模拟数据真实拟合通过。
- WGCNA-style、NNLS免疫浸润、gene-set z-score和survival同时启用并真实运行通过。
- R脚本静态解析及9个运行依赖加载通过。
- 真实GEO/SRA网络、真实FASTQ、ComBat-seq和正式全流程未运行，原因记录于
  `CURRENT_STATE.md`。

### 不兼容变更

- 无既有authority接口的不兼容变化。
- 单细胞正式分析现在要求可验证的raw count layer和confirmed ontology mapping。

## 2026-07-01 — 实现 bulk 多数据集联合分析与 Meta 分析

### 新增文件

- `geo-rnaseq-mining/workflow/scripts/assess_dataset_compatibility.py`
- `geo-rnaseq-mining/workflow/scripts/multi_dataset_common.py`
- `geo-rnaseq-mining/workflow/scripts/prepare_joint_bulk.py`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_joint_model.R`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_meta_analysis.py`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_stratified_validation.py`
- `geo-rnaseq-mining/resources/MULTI_DATASET_BULK.md`
- `geo-rnaseq-mining/tests/unit/test_multi_dataset_analysis.py`

### 修改文件

- `geo-rnaseq-mining/workflow/rules/multi_dataset.smk`
- `geo-rnaseq-mining/workflow/Snakefile`
- `geo-rnaseq-mining/config/config.yaml`
- `geo-rnaseq-mining/workflow/schemas/config.schema.yaml`
- `geo-rnaseq-mining/workflow/envs/base.yaml`
- `geo-rnaseq-mining/workflow/envs/r-bulk-analysis.yaml`
- `geo-rnaseq-mining/workflow/scripts/README.md`
- `docs/CURRENT_STATE.md`
- `docs/DECISIONS.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`

### 删除文件

- 无。

### 接口变化

- 新增 `results/compatibility/dataset_compatibility.tsv`。
- 新增 joint、per-dataset Meta、stratified validation 和 independent-only
  Snakemake目标。
- 新增 `results/merged_analysis/bulk/`、`results/meta_analysis/bulk/` 和
  `results/consensus/bulk/` 输出树。
- Meta输出新增效应、异质性、方向和dataset-specific effects。
- 新增LODO稳定性summary/details接口。

### 配置变化

- `multi_dataset` 新增 joint授权、ComBat-seq、Meta方法/阈值和分层验证设置。
- Meta默认方法为 `random_effects`。
- ComBat-seq默认关闭；普通ComBat没有配置入口。
- Python环境新增scipy；R分析环境新增sva。

### Bug修复与防护

- 阻止TPM/非整数矩阵、gene ID不一致、跨数据集样本重叠、validation泄漏、
  完全混杂和不满秩设计进入joint model。
- 作者count必须具有用户批准且一致、非未知的定量来源。
- 阻止程序自动改变用户指定的analysis strategy。
- p值合并结果强制保留效应方向。

### 测试变化

- 单元测试从68增至79，全部通过。
- 新增用户要求的8种多数据集场景测试，以及联合输入、Meta产物和分层验证链路测试。
- 1个离线数据入口集成测试通过。
- joint R脚本通过R 4.4.3静态解析。
- 默认DAG dry-run通过（17 jobs）。
- 四策略启用态DAG dry-run通过（65 jobs）。
- 真实DESeq2、ComBat-seq、FASTQ及网络分析未运行。

### 不兼容变更

- joint model现在要求每个GSE先完成独立bulk分析，并通过明确兼容性门禁。
- 作者提供的整数count默认不能进入joint model，除非用户明确批准。

## 2026-07-01 — 单数据集 bulk 阶段交接复核

### 新增文件

- 无。

### 修改文件

- `docs/CURRENT_STATE.md`
- `docs/DECISIONS.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`

### 删除文件

- 无。

### 接口变化

- 无代码接口变化。
- 新增已确认流程决策 DEC-015：阶段交接后不得自动开始下一阶段。
- `BULK-RUN-001` 标记为 `not_started`，等待用户明确启动。

### 配置变化

- 无。

### Bug 修复

- 无代码 bug 修复。
- 修正 `CURRENT_STATE.md` 将已实现的 `bulk.smk` 误写为占位文件的过时描述。

### 测试变化

- 重新运行 68 个离线单元测试：全部通过。
- 重新运行 1 个离线数据入口集成测试：通过。
- Python compileall、config schema 验证和 4 个 R 脚本静态解析：通过。
- 默认、matrix、Salmon/tximport、STAR/featureCounts Snakemake dry-run：全部通过。
- 真实 DESeq2/FASTQ 工具执行及网络测试未运行，原因已写入 `CURRENT_STATE.md`。

### 不兼容变更

- 无。

## 2026-07-01 — 实现单数据集 bulk RNA-seq 分析

### 新增文件

- `geo-rnaseq-mining/resources/BULK_ANALYSIS.md`
- `geo-rnaseq-mining/workflow/scripts/bulk_common.py`
- `geo-rnaseq-mining/workflow/scripts/prepare_bulk_dataset.py`
- `geo-rnaseq-mining/workflow/scripts/collect_bulk_quant_metrics.py`
- `geo-rnaseq-mining/workflow/scripts/normalize_featurecounts.py`
- `geo-rnaseq-mining/workflow/scripts/merge_bulk_counts.py`
- `geo-rnaseq-mining/workflow/scripts/run_tximport.R`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_qc.R`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_deseq2.R`
- `geo-rnaseq-mining/workflow/scripts/run_bulk_enrichment.R`
- `geo-rnaseq-mining/tests/unit/test_bulk_analysis.py`
- bulk 模拟 count、matrix manifest、FASTQ、tx2gene fixtures。

### 修改文件

- `geo-rnaseq-mining/workflow/rules/bulk.smk`
- `geo-rnaseq-mining/workflow/Snakefile`
- `geo-rnaseq-mining/config/config.yaml`
- `geo-rnaseq-mining/workflow/schemas/config.schema.yaml`
- `geo-rnaseq-mining/workflow/scripts/validate_analysis_design.py`
- bulk 相关 Conda 环境文件、README 和测试说明。
- `docs/PROJECT_SPEC.md`，按用户明确要求加入 per-dataset bulk 输出目录。
- `docs/CURRENT_STATE.md`
- `docs/DECISIONS.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`

### 删除文件

- 无。

### 接口变化

- 新增目标 `results/per_dataset/{dataset_id}/bulk/.complete`。
- 新增 matrix 与 FASTQ 两种互斥入口。
- 新增 FastQC/MultiQC、Salmon/tximport、STAR/featureCounts 规则。
- 新增样本 QC、DESeq2 多 contrast、GO/通路 ORA、GSEA 和效应方向汇总。
- design validator 支持派生 `dataset` 别名和纯数值 `age`。

### 配置变化

- `bulk.quantification_method` 限定为 `salmon_tximport` 或
  `star_featurecounts`。
- 新增 Salmon、STAR 和 featureCounts 参数子节。
- config schema 现在验证 bulk 方法、strandedness、阈值和 transformation。
- WGCNA、免疫浸润、GSVA 和生存分析开关保持默认关闭，并输出明确状态。

### Bug 修复

- 无既有 bug 修复。
- 新增严格防护，阻止非整数、负值、重复 gene/sample、样本集合/顺序错误及疑似
  TPM/FPKM/CPM/log 矩阵进入 DESeq2。
- outlier 输出固定保留全部样本，不允许自动删除。

### 测试变化

- 单元测试从 60 增至 68，全部通过。
- 新增模拟 count、非整数拒绝、样本顺序拒绝、不满秩、配对满秩和 outlier 不删除测试。
- 1 个离线数据入口集成测试继续通过。
- 默认、matrix、Salmon/tximport 和 STAR/featureCounts DAG dry-run 全部通过。
- 4 个新增 R 脚本均通过 R 4.4.3 静态解析。

### 不兼容变更

- 正式 bulk matrix 现在要求样本列与 included reviewed manifest 的集合和顺序完全一致。
- 同一 dataset 混用 matrix 与 FASTQ 会被阻断。

## 2026-07-01 — 建立上下文恢复与阶段交接机制

### 新增文件

- `docs/PROJECT_SPEC.md`
- `docs/CURRENT_STATE.md`
- `docs/DECISIONS.md`
- `docs/NEXT_TASK.md`
- `docs/CHANGELOG.md`
- `docs/SESSION_HANDOFF_TEMPLATE.md`

### 修改文件

- 无。

### 删除文件

- 无。

### 接口变化

- 新会话必须按固定顺序读取长期规范、用户决策、当前状态、下一任务和变更记录。
- 每次任务完成必须更新 `CURRENT_STATE.md`、`CHANGELOG.md` 和 `NEXT_TASK.md`。
- 产生或改变用户决策时必须更新 `DECISIONS.md`。
- 每次最终回复末尾必须提供简短 SESSION HANDOFF 摘要。

### 配置变化

- 无。

### Bug 修复

- 无代码 bug 修复。
- 通过持久化文档机制降低聊天上下文自动压缩导致约束和状态丢失的风险。

### 测试变化

- 未修改测试代码。
- 建立测试基线：60 个离线单元测试通过。
- 建立集成基线：1 个离线数据入口集成测试通过。
- 完整 Snakemake 与 R 网络测试因当前 PATH 缺少对应命令而未运行。

### 不兼容变更

- 无代码不兼容变更。
- 流程治理新增强制收尾更新要求；后续会话不得只在聊天中保存关键状态。
