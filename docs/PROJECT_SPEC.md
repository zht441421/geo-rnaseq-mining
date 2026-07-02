# 项目长期规范

## 文档地位

本文档保存项目长期有效的目标、架构和分析约束，是聊天上下文之外的持久规范。
除非用户明确要求修改，否则任何会话、程序或自动化代理均不得改变本文档的核心原则。

新会话开始时必须依次读取：

1. `docs/PROJECT_SPEC.md`
2. `docs/DECISIONS.md`
3. `docs/CURRENT_STATE.md`
4. `docs/NEXT_TASK.md`
5. `docs/CHANGELOG.md`

每次任务完成时必须更新 `CURRENT_STATE.md`、`CHANGELOG.md` 和
`NEXT_TASK.md`；如果产生或改变用户决策，还必须更新 `DECISIONS.md`。关键状态不得
只保存在聊天回复中。

## 项目目标

建立一个面向 GEO bulk RNA-seq、scRNA-seq 和 snRNA-seq 数据挖掘的可复现
Snakemake 工作流。工作流应支持元数据获取、人工审核、数据入口验证、单数据集分析、
多数据集策略、独立验证、Meta 分析和可审计报告，同时确保程序建议永远不能替代用户
对样本、分组、受试者、对比和合并策略的确认。

## 总体架构

项目采用分层、门控式架构：

1. **来源层**：保存 GEO/SRA 原始元数据、补充文件索引和来源记录；原始内容不可原地
   修改。
2. **建议层**：程序可生成候选分组、冲突、未映射记录和审核报告，但不得写入正式分析
   决策。
3. **人工权威层**：由用户审核 `sample_manifest.tsv`、`contrasts.tsv`、
   `dataset_plan.tsv` 和 `celltype_ontology.tsv`。
4. **验证门层**：在分析前验证身份、文件、计数矩阵、设计矩阵、配对、数据集角色、
   数据兼容性和单细胞 donor/cell type 充分性；严重问题必须阻断分析。
5. **分析层**：bulk、单细胞、pseudobulk、多数据集和 Meta 分析只能消费通过验证的
   人工权威输入。
6. **报告与溯源层**：保存日志、benchmark、软件与数据库版本、随机种子、输入校验和、
   参数、设计和结果。

当前代码位于 `geo-rnaseq-mining/`，外层 `docs/` 保存跨会话项目治理文件。

## 人工决策优先原则

人工确认值的优先级高于配置默认值、程序建议和 GEO/SRA 来源字段。程序只能提示、
验证和阻断，不得擅自推断、填充、纠正、反转、合并或覆盖下列人工决策：

- 样本是否纳入；
- 正式分组；
- `subject_id`；
- 技术重复和生物重复关系；
- contrast 方向和模型；
- 数据集角色；
- 数据集合并策略；
- cell type 映射。

来源字段必须保留原值。发生冲突时，应输出可审计错误或警告并交由用户处理。

## reviewed manifest 的唯一权威地位

`geo-rnaseq-mining/metadata/reviewed/sample_manifest.tsv` 是样本级事实和分析纳入状态的
唯一权威来源。正式分析不得直接使用 suggested manifest、GEO 标题、关键词推断、
SRA 映射或配置默认值替代其中的正式字段。

必须遵守：

- 每个正式分析样本具有唯一 `sample_id`；
- `include=true` 的样本必须由用户确认且 `review_status=confirmed`；
- 被排除样本仍保留在 manifest 中，并设置 `include=false`；
- `group`、`subject_id`、配对关系和输入路径均由用户确认；
- 程序衍生列可以追加，但不得覆盖用户列；
- `validated_manifest.tsv` 是验证结果，不是新的人工权威来源。

## `contrasts.tsv` 职责

`geo-rnaseq-mining/config/contrasts.tsv` 是差异比较定义的唯一权威来源，负责记录：

- contrast 标识和所属 `analysis_id`；
- 分析范围；
- numerator 与 denominator 的明确方向；
- 子集条件；
- 设计公式；
- 是否配对；
- 最低生物学重复数；
- 是否启用。

程序不得自动交换 numerator/denominator、从组名猜测对比、自动删除协变量或自动修改
配对设定。无法估计的 contrast 必须报告并阻断对应分析。

## `dataset_plan.tsv` 职责

`geo-rnaseq-mining/config/dataset_plan.tsv` 是数据集级角色和组合策略的唯一权威来源，
负责记录：

- 数据集是否纳入；
- discovery、validation 或其他明确角色；
- merge group；
- `separate`、`joint_model`、`meta` 等人工确认策略；
- reference dataset；
- 策略说明。

程序不得因为数据类型相同或基因空间相似而默认合并数据集，也不得把 validation 数据
加入 discovery 模型的参数估计。

## `celltype_ontology.tsv` 职责

`geo-rnaseq-mining/config/celltype_ontology.tsv` 是作者 cell type 标签向项目层级本体映射
的唯一权威来源，负责保存：

- 数据集与作者原始标签；
- harmonized level 1/2/3；
- 映射方法、置信度和审核状态；
- 人工说明。

作者原始标签必须原样保留。程序不得用自动注释结果静默覆盖作者标签，不得在一对多
冲突未解决时进行跨数据集 cell type 合并。

## bulk 分析原则

- 差异表达的统计单位必须是独立生物学样本或受试者，不得把技术重复当作独立重复。
- DESeq2 等 count-based 模型只能使用原始非负整数 counts；TPM、FPKM、CPM、
  log-transformed 或标准化表达矩阵不得作为其输入。
- FASTQ 定量、现成 count matrix 和探索性表达矩阵必须分别记录入口类型与验证状态。
- 技术重复的合并必须依据用户确认的身份关系，并保留合并前后溯源。
- 设计公式、协变量、批次、配对关系和 contrast 必须来自人工权威文件。
- 设计矩阵不满秩、dataset 与 group 完全混杂或关键协变量严重缺失时不得继续拟合。
- QC、离群值和低表达过滤必须输出依据；不得自动删除样本并修改 manifest。
- 发现集与验证集必须分离，验证集不得参与发现模型的参数估计或阈值选择。

## 单细胞分析原则

- scRNA-seq 与 snRNA-seq 的联合分析必须由用户明确批准，不得默认合并。
- 保留原始 counts、原始 barcode、原始 sample/donor 身份和作者 cell type 标签。
- QC 阈值、双细胞处理、环境 RNA 处理、归一化、降维、批次整合和注释方法必须记录。
- 批次整合用于表示和可视化时，不得被视为已消除设计混杂，也不得替代原始 counts 的
  统计建模。
- 细胞不得作为独立生物学重复。
- 差异表达默认采用 subject-level pseudobulk；任何偏离必须由用户明确确认并记录。
- cell type 的跨数据集比较必须先通过人工 ontology 映射和 donor/cell 数充分性验证。

## 多数据集合并原则

- 多个 GSE 不得默认按样本或表达矩阵直接拼接。
- 每个数据集先独立完成身份、平台、物种、参考基因组、gene ID、数据类型、批次和设计
  可估计性检查。
- 合并策略必须由 `dataset_plan.tsv` 明确指定。
- joint model 仅在数据集间具有可识别的组别结构、兼容的表达空间和可估计设计时使用。
- dataset 与 group 完全混杂时禁止 joint model；不得以批次校正掩盖该问题。
- 标准化和 QC 应在适当的数据集层级完成，任何跨数据集变换都必须保留参数和中间结果。
- 不兼容数据应分别分析，必要时在效应量层面进行 Meta 分析。

## pseudobulk 原则

- 聚合层级固定为人工确认的 `subject_id`，并按 dataset、subject、condition 和 cell type
  等设计所需维度聚合。
- 聚合输入必须为原始 counts，不得聚合已归一化或整合后的表达值作为 count 模型输入。
- 必须输出每个 pseudobulk 样本的细胞数、donor 身份、组别、cell type 和聚合审计表。
- donor 数和每个 donor-cell type 的细胞数必须达到配置并经验证的最低要求。
- 同一 subject 的多个样本或时间点不得在未确认设计前自动合并。
- 下游差异模型以 donor/subject 为重复单位，并使用人工定义的 contrast 和设计公式。

## Meta 分析原则

- Meta 分析在每个数据集独立估计方向一致的 contrast 后进行，不以样本级拼接替代。
- 每个数据集必须能独立估计目标效应，并记录效应量、标准误、方向和样本量。
- 必须报告数据集间异质性、单数据集影响和方向一致性。
- 不得自动把无法 joint model 的数据降级为 Meta；策略变化需要用户确认并更新
  `dataset_plan.tsv` 与 `DECISIONS.md`。
- discovery 与 validation 的结果应分层报告，不得通过合并使验证集反向影响发现模型。

## 数据验证要求

正式分析前必须执行 fail-closed 验证，至少覆盖：

- 权威文件 schema、列、类型、枚举和唯一性；
- 样本/GSM/SRR 身份冲突；
- included、confirmed、group 和 `subject_id` 一致性；
- 文件存在性、格式、大小与校验和；
- FASTQ 配对完整性和矩阵样本列匹配；
- count matrix 非负整数要求；
- contrast 中组别存在性、方向、重复数和配对完整性；
- 设计公式变量、缺失率、零方差和满秩性；
- dataset role、merge strategy、物种、参考基因组和 gene ID 兼容性；
- validation 数据隔离；
- 单细胞 donor、cell type、细胞数和 ontology 映射；
- dataset-group 完全混杂。

验证报告必须给出严重级别、影响对象、原因和用户可执行的修复建议。critical 问题阻断
全局流程，analysis-specific error 阻断对应 `analysis_id`，warning 不得静默改值。

## 禁止事项

禁止：

- 从标题、关键词或表达模式自动确认正式 group、include、`subject_id` 或 contrast；
- 覆盖、删除或重排人工确认值以使流程“通过”；
- 删除 excluded 样本行来隐藏排除记录；
- 将细胞、barcode、测序 run 或技术重复作为生物学重复；
- 用 TPM/FPKM/CPM/log 表达执行原始 count 差异模型；
- 在 discovery 模型中使用 validation 数据；
- 默认拼接多个 GSE；
- 在 dataset 与 group 完全混杂时使用 joint model；
- 用批次校正声称解决不可识别设计；
- 自动反转 contrast；
- 自动从 joint model 切换为 Meta 分析；
- 原地修改来源数据或把衍生文件冒充人工权威文件；
- 跳过验证门直接运行正式分析；
- 在日志、配置或产物中写入密钥和访问令牌。

## 输出目录规范

代码目录内使用以下约定：

- `metadata/raw/`：不可变来源元数据和抓取事件；
- `metadata/suggested/`：程序建议、冲突和人工审核报告；
- `metadata/reviewed/`：用户审核的 sample manifest；
- `config/`：人工权威设计文件和运行配置；
- `data/raw/`、`data/sra/`、`data/fastq/`、`data/matrices/`、
  `data/objects/`、`data/references/`：按入口类型保存数据；
- `results/compatibility/`：验证和入口盘点结果；
- `results/per_dataset/{dataset_id}/bulk/`：单数据集 bulk 正式分析结果；
- `results/<module>/<analysis_id>/`：其他正式分析结果；
- `resources/cache/`：可再生成缓存；
- `resources/provenance/<analysis_id>/`：参数、版本、校验和和运行记录；
- `logs/<module>/`：规则日志；
- `benchmarks/<module>/`：运行资源统计；
- `docs/`：外层工作区的长期上下文与交接文档。

输出路径不得依赖机器专属绝对路径。缓存、临时文件、正式结果和人工权威输入必须分离。

## 可复现性要求

- 使用 Snakemake 声明输入、输出和依赖；
- 每个可执行规则声明 log、benchmark、threads、memory、runtime 和 disk；
- 通过 Conda 环境文件固定主要运行时与依赖；
- 记录随机种子、软件版本、数据库版本、参考基因组、注释版本和参数；
- 对来源文件和关键中间文件记录 SHA-256；
- 保留每次分析所消费的权威文件快照或校验和；
- 网络抓取采用重试、速率限制、成功缓存和事件日志；
- 原始数据和人工输入不得被脚本原地修改；
- 相同输入、配置和环境应能重建相同的确定性产物；
- 非确定性算法必须固定随机种子并记录实现版本。

## 测试要求

- 每次代码任务至少运行与改动直接相关的测试。
- 完成任务前运行全部离线单元测试；当前基线命令为
  `python -m unittest discover -s tests/unit -p "test_*.py" -v`。
- 数据入口变化需运行离线集成测试
  `python -m unittest discover -s tests/integration -p "test_data_entry_pipeline.py" -v`。
- schema、人工决策隔离、验证门、设计混杂、validation 隔离和 pseudobulk donor 层级
  必须有回归测试。
- 网络测试和大型数据测试必须显式 opt-in，不得成为默认离线测试的前提。
- 新增分析模块必须同时提供最小合成 fixture、预期结果和失败路径测试。
- 不得通过降低验证等级、删除断言或改写人工输入来使测试通过。
- 测试命令、时间、结果和未运行原因必须写入 `CURRENT_STATE.md`。
