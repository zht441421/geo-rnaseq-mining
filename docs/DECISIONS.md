# 已确认决策

本文档只记录用户已经确认的项目决策。程序、自动化代理和后续会话不得擅自更改已确认
决策。若用户明确修改决策，应新增一条决策并引用被替代的 `decision_id`，不得静默
覆盖历史。

## DEC-001：分组由用户人工确认

- **decision_id**：DEC-001
- **日期**：2026-07-01
- **决策内容**：正式 `group` 只能由用户在 reviewed manifest 中人工确认；程序生成的
  case/control candidate 仅用于提示。
- **决策原因**：GEO/SRA 标题、关键词和 characteristics 可能模糊、冲突或缺少实验
  语境，自动分组会直接改变统计问题。
- **影响模块**：元数据建议、manifest 校验、bulk、单细胞、pseudobulk、多数据集分析。
- **是否可逆**：可逆，但只能由用户明确修改。
- **替代方案**：程序自动推断并写入正式分组；已否决。
- **用户确认状态**：已确认。

## DEC-002：样本纳入由用户决定

- **decision_id**：DEC-002
- **日期**：2026-07-01
- **决策内容**：样本 `include` 状态由用户决定；程序可报告问题和阻断，但不得自动纳入、
  排除或删除样本行。
- **决策原因**：纳入排除需要结合研究问题、原始设计、质量证据和外部信息。
- **影响模块**：reviewed manifest、验证门、所有下游分析和报告。
- **是否可逆**：可逆，但只能由用户明确修改。
- **替代方案**：按关键词、缺失值或 QC 阈值自动修改纳入状态；已否决。
- **用户确认状态**：已确认。

## DEC-003：`subject_id` 由用户确认

- **decision_id**：DEC-003
- **日期**：2026-07-01
- **决策内容**：`subject_id`、技术重复、生物重复和配对关系必须由用户确认；程序不得
  根据 GSM/SRR、barcode 或相似名称自动合并。
- **决策原因**：错误的受试者映射会造成伪重复、错误自由度和无效显著性。
- **影响模块**：manifest、配对设计、技术重复处理、单细胞 pseudobulk、差异分析。
- **是否可逆**：可逆，但只能由用户明确修改。
- **替代方案**：按记录名称或 barcode 自动生成 subject；已否决。
- **用户确认状态**：已确认。

## DEC-004：contrast 由用户定义

- **decision_id**：DEC-004
- **日期**：2026-07-01
- **决策内容**：contrast 的 numerator、denominator、subset、设计公式、配对状态、最低
  重复数和启用状态由用户在 `contrasts.tsv` 中定义。
- **决策原因**：contrast 方向和设计公式决定效应解释，不能由程序从组名猜测。
- **影响模块**：contrast 校验、bulk DE、pseudobulk DE、Meta 分析和结果报告。
- **是否可逆**：可逆，但只能由用户明确修改。
- **替代方案**：自动生成所有两两比较或自动反转方向；已否决。
- **用户确认状态**：已确认。

## DEC-005：dataset merge strategy 由用户定义

- **decision_id**：DEC-005
- **日期**：2026-07-01
- **决策内容**：每个数据集的纳入、角色、merge group、analysis strategy 和 reference
  dataset 由用户在 `dataset_plan.tsv` 中定义。
- **决策原因**：合并策略取决于平台、物种、参考、gene ID、设计和研究目的，不能由
  文件格式决定。
- **影响模块**：dataset plan 校验、joint model、Meta、独立验证和联合报告。
- **是否可逆**：可逆，但策略变化必须由用户明确确认。
- **替代方案**：程序根据兼容性检查自动选择 separate/joint/meta；已否决。
- **用户确认状态**：已确认。

## DEC-006：验证集不得进入发现模型

- **decision_id**：DEC-006
- **日期**：2026-07-01
- **决策内容**：标记为 validation 的数据不得参与 discovery 模型的拟合、特征选择、
  阈值选择或参数估计。
- **决策原因**：保持独立验证，避免信息泄漏和过度乐观的性能或显著性。
- **影响模块**：dataset plan 校验、bulk、单细胞、joint model、Meta 和报告。
- **是否可逆**：核心原则不可由程序逆转；若研究角色改变，需用户重新定义数据集角色。
- **替代方案**：将所有数据合并后交叉验证；不等同于独立验证，已否决为默认方案。
- **用户确认状态**：已确认。

## DEC-007：单细胞差异分析采用 subject-level pseudobulk

- **decision_id**：DEC-007
- **日期**：2026-07-01
- **决策内容**：scRNA-seq/snRNA-seq 正式差异表达默认采用
  subject-level pseudobulk，以人工确认的 `subject_id` 作为生物学重复单位。
- **决策原因**：细胞不是独立受试者；按细胞检验会产生伪重复和夸大的统计证据。
- **影响模块**：单细胞聚合、donor/cell type 验证、差异分析和 Meta。
- **是否可逆**：仅用户可明确批准偏离，并记录新决策、统计理由和适用范围。
- **替代方案**：将单细胞作为独立重复进行常规检验；已否决。
- **用户确认状态**：已确认。

## DEC-008：多 GSE 不得默认拼接

- **decision_id**：DEC-008
- **日期**：2026-07-01
- **决策内容**：多个 GSE 不得默认拼接样本或表达矩阵；必须先独立验证并由
  `dataset_plan.tsv` 指定策略。
- **决策原因**：平台、处理、参考、gene ID、构成和设计差异可能产生不可解释偏差。
- **影响模块**：数据入口、标准化、批次处理、joint model、Meta 和可视化。
- **是否可逆**：可在用户确认兼容性和策略后对指定 merge group 合并。
- **替代方案**：发现多个矩阵后自动按共有基因拼接；已否决。
- **用户确认状态**：已确认。

## DEC-009：完全混杂时禁止 joint model

- **decision_id**：DEC-009
- **日期**：2026-07-01
- **决策内容**：dataset 与 group 完全混杂时不得使用 joint model，且不得用批次校正
  作为修复。
- **决策原因**：模型无法区分 dataset 效应与 group 效应，设计不可识别。
- **影响模块**：设计矩阵验证、dataset plan、joint model 和结果解释。
- **是否可逆**：只有新增可打破混杂的数据或用户重新定义可估计设计后才可改变。
- **替代方案**：自动移除 dataset 项、先批次校正再检验、自动改用 Meta；均已否决。
- **用户确认状态**：已确认。

## DEC-010：上下文状态必须持久化到项目文件

- **decision_id**：DEC-010
- **日期**：2026-07-01
- **决策内容**：关键约束、当前事实、已确认决策、下一任务和变更历史必须写入
  `docs/`；每次任务完成都执行状态更新和会话交接。
- **决策原因**：避免聊天上下文自动压缩后丢失项目约束、测试状态和阶段边界。
- **影响模块**：全部项目维护、会话启动和任务收尾流程。
- **是否可逆**：可逆，但只能由用户明确修改。
- **替代方案**：仅依赖聊天记录或临时总结；已否决。
- **用户确认状态**：已确认。

## DEC-011：每个 GSE 必须独立完成 bulk 处理和 QC

- **decision_id**：DEC-011
- **日期**：2026-07-01
- **决策内容**：每个 GSE 必须先独立执行输入校验、定量、样本级 QC 和 DESeq2；即使
  后续 dataset plan 选择合并或 Meta，也不得跳过单数据集阶段。
- **决策原因**：先识别每个数据集自身的技术质量、设计可估计性和效应方向，避免合并
  掩盖数据集特异问题。
- **影响模块**：bulk 输入、FASTQ 定量、样本 QC、DESeq2、多数据集和 Meta。
- **是否可逆**：核心分析原则不可由程序逆转；只有用户明确修改项目规范后可变更。
- **替代方案**：先拼接多个 GSE 再统一 QC；已否决。
- **用户确认状态**：已确认。

## DEC-012：bulk 支持矩阵与 FASTQ 两种互斥入口

- **decision_id**：DEC-012
- **日期**：2026-07-01
- **决策内容**：单个 dataset 必须选择原始 gene-level count matrix 或 FASTQ 之一；
  FASTQ 默认使用 Salmon + tximport，可由配置明确改为 STAR + featureCounts。
- **决策原因**：两类入口具有不同的质量证据和溯源要求，混合入口会造成不可比的计数。
- **影响模块**：manifest 输入路径、数据入口验证、定量、reference 配置和 provenance。
- **是否可逆**：可由用户修改 dataset 的 reviewed 输入或全局定量配置后重新运行。
- **替代方案**：同一 dataset 混用现成矩阵和新定量 FASTQ；已否决。
- **用户确认状态**：已确认。

## DEC-013：bulk outlier 只能标记，不能自动删除

- **decision_id**：DEC-013
- **日期**：2026-07-01
- **决策内容**：library size、detected genes、PCA 距离或 Cook's distance 异常只能写入
  报告；工作流不得自动删除样本，正式排除必须由用户修改 reviewed manifest 后重跑。
- **决策原因**：异常值可能反映真实生物差异，样本排除属于影响推断的人工决策。
- **影响模块**：样本 QC、DESeq2、结果矩阵、报告和 manifest。
- **是否可逆**：不可由程序绕过；用户可明确修改 reviewed manifest。
- **替代方案**：按固定阈值自动删除异常样本；已否决。
- **用户确认状态**：已确认。

## DEC-014：bulk 比较只能来自 `contrasts.tsv`

- **decision_id**：DEC-014
- **日期**：2026-07-01
- **决策内容**：bulk DESeq2 不自动生成比较；所有 numerator、denominator、subset、
  formula、paired 状态和最低重复数均来自 `config/contrasts.tsv`。
- **决策原因**：保证统计问题、方向、配对和协变量均由用户定义并可审计。
- **影响模块**：design validation、DESeq2、多 contrast、富集和结果命名。
- **是否可逆**：可由用户编辑 `contrasts.tsv` 后重新验证和运行。
- **替代方案**：自动执行全部两两比较；已否决。
- **用户确认状态**：已确认。

## DEC-015：阶段交接后不得自动开始下一阶段

- **decision_id**：DEC-015
- **日期**：2026-07-01
- **决策内容**：当前阶段完成后只执行代码核对、测试、文档更新和 SESSION HANDOFF；
  下一阶段任务只写入 `NEXT_TASK.md`，不得在同一交接过程中开始实现或运行。
- **决策原因**：保持阶段边界清晰，确保用户先审核交接状态和下一任务范围。
- **影响模块**：任务收尾、会话交接、`NEXT_TASK.md` 和后续开发启动。
- **是否可逆**：可逆；仅在用户明确要求继续下一阶段时开始。
- **替代方案**：阶段完成后由程序自动推进下一任务；已否决。
- **用户确认状态**：已确认。

## DEC-016：多数据集策略只由 dataset plan 指定

- **decision_id**：DEC-016
- **日期**：2026-07-01
- **决策内容**：每个 analysis 的 `joint_model`、`per_dataset_meta`、
  `stratified_validation` 或 `independent_only` 只由
  `config/dataset_plan.tsv` 指定；程序只评估技术可行性，不得自动改策略。
- **决策原因**：分析策略属于影响统计解释的人工决策。
- **影响模块**：兼容性评估、Snakemake DAG、joint、Meta、验证和报告。
- **是否可逆**：用户可修改 reviewed dataset plan 后重新验证和运行。
- **替代方案**：程序按兼容性自动切换策略；已否决。
- **用户确认状态**：已确认。

## DEC-017：joint model 必须通过硬门禁且不得用批次校正修复完全混杂

- **decision_id**：DEC-017
- **日期**：2026-07-01
- **决策内容**：joint model 只使用统一流程 raw counts，或经用户明确批准的兼容
  作者整数 counts；必须验证gene ID、样本身份、组内contrast、validation隔离、
  满秩和完全混杂。普通 ComBat 禁止，ComBat-seq 默认关闭且不能修复完全混杂。
- **决策原因**：不可识别设计无法通过数值校正恢复生物学效应。
- **影响模块**：兼容性评估、joint输入、DESeq2和provenance。
- **是否可逆**：仅用户可批准作者counts或启用ComBat-seq；完全混杂禁令不可由程序绕过。
- **替代方案**：先ComBat后DESeq2或自动改Meta；已否决。
- **用户确认状态**：已确认。

## DEC-018：Meta 必须联合报告效应量、方向和异质性

- **decision_id**：DEC-018
- **日期**：2026-07-01
- **决策内容**：支持 fixed、random、Fisher、weighted Stouffer 和 RRA；
  默认推荐 random-effects 但以config为准。combined p-value必须伴随效应方向、
  dataset-specific effects、Q和I2，不能单独定义候选。
- **决策原因**：仅合并p值会掩盖方向冲突和数据集异质性。
- **影响模块**：Meta统计、结果表、候选解释和稳定性分析。
- **是否可逆**：用户可在config选择支持的方法，不得移除方向证据。
- **替代方案**：只输出combined p-value；已否决。
- **用户确认状态**：已确认。

## DEC-019：验证集严格隔离于 discovery

- **decision_id**：DEC-019
- **日期**：2026-07-01
- **决策内容**：stratified validation 中，validation datasets 不得参与候选筛选、
  模型训练、阈值确定或特征选择，只用于效应、方向、p值和复制状态评估。
- **决策原因**：避免验证集泄漏导致过度乐观的复制结论。
- **影响模块**：dataset role验证、候选选择、分层验证和输出manifest。
- **是否可逆**：不可由程序逆转；用户若改变角色必须修改dataset plan并重跑。
- **替代方案**：先合并discovery与validation再内部验证；已否决。
- **用户确认状态**：已确认。

## DEC-020：多数据集结论必须包含 leave-one-dataset-out 稳定性

- **decision_id**：DEC-020
- **日期**：2026-07-01
- **决策内容**：Meta和discovery证据必须逐次剔除一个GSE重算，并报告
  `dataset_driven`、`sign_stable`、`significance_stable` 和
  `max_effect_change`。
- **决策原因**：识别由单个GSE驱动或对数据集选择敏感的结论。
- **影响模块**：Meta、stratified validation、consensus输出和报告。
- **是否可逆**：阈值可由config调整；稳定性分析本身不得省略。
- **替代方案**：只报告全数据集汇总；已否决。
- **用户确认状态**：已确认。

## DEC-021：本轮只豁免真实数据与人工决策阻塞

- **decision_id**：DEC-021
- **日期**：2026-07-02
- **决策内容**：回顾既往未解决问题时，必须依赖用户提供真实数据或人工确认的事项
  可保留为阻塞；其余可由代码、配置、环境或测试解决的问题必须完成。
- **决策原因**：区分外部研究输入与项目自身技术债，避免把可修复问题误列为等待用户。
- **影响模块**：缺陷清理、环境验证、单细胞、可选bulk、报告、测试和阶段交接。
- **是否可逆**：可逆；后续任务范围可由用户重新指定。
- **替代方案**：所有未解决项均延期到真实数据到位后；已否决。
- **用户确认状态**：已确认。

## DEC-022：单细胞预处理必须按GSE和样本独立QC

- **decision_id**：DEC-022
- **日期**：2026-07-02
- **决策内容**：scRNA-seq和snRNA-seq在任何跨数据集整合前，必须先按GSE处理，
  并在每个GSE内按`sample_id`分别计算QC阈值、doublet和ambient RNA证据；
  AnnData为主交换格式，原始counts、人工标签和未整合PCA必须保留。
- **决策原因**：不同样本的测序深度、复杂度、核/细胞质量和doublet分布不同，
  统一固定阈值或合并后估计会掩盖样本特异问题并污染后续整合。
- **影响模块**：单细胞输入、barcode命名、AnnData合同、QC、doublet、
  ambient RNA、标准化、聚类、初步注释、pseudobulk和跨数据集整合。
- **是否可逆**：核心原则不可由程序逆转；阈值与方法可由用户通过config调整。
- **替代方案**：合并全部样本后使用统一QC/doublet模型，或用自动注释覆盖作者标签；
  均已否决。
- **用户确认状态**：已确认。

## DEC-023：单细胞差异分析的正式pseudobulk合同

- **decision_id**：DEC-023
- **日期**：2026-07-02
- **决策内容**：单细胞subject-level pseudobulk差异分析必须使用
  `adata.layers["counts"]`中的原始聚合counts，按`dataset_id`、`subject_id`、
  `sample_id`、`cell_type`和用户指定额外分层变量聚合；不得按单个细胞进行病例
  对照统计，不得为了达到阈值合并不同`subject_id`。每个pseudobulk样本必须记录
  subject、sample、dataset、cell type、group、cell count、total UMI、eligibility
  和exclusion reason。资格阈值、design formula、contrast和跨数据集策略分别来自
  config、`contrasts.tsv`和`dataset_plan.tsv`。
- **决策原因**：保证单细胞差异分析以受试者为统计重复单位，保留raw count建模合同，
  并让资格排除、joint/meta/validation策略和效应方向证据可审计。
- **影响模块**：单细胞pseudobulk聚合、DESeq2、combined pseudobulk joint model、
  per-dataset pseudobulk Meta、validation模式、测试和报告。
- **是否可逆**：可逆，但只能由用户明确修改；任何偏离必须记录新的用户确认决策。
- **替代方案**：按细胞检验、用log-normalized矩阵建模、自动合并供体、自动切换策略
  或省略方向冲突证据；均已否决。
- **用户确认状态**：已确认。
