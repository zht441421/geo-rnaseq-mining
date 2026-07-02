# SESSION HANDOFF 模板

任务完成后，使用本模板生成会话交接。详细事实必须先写入对应项目文档；聊天中的
SESSION HANDOFF 只能是简短索引，不能替代文件更新。

## 项目目标

用一至两句话说明项目长期目标。必须与 `PROJECT_SPEC.md` 一致。

## 当前阶段

- 阶段名称：
- 阶段状态：not_started / in_progress / blocked / completed
- 事实来源：相关文件或命令

## 本次完成内容

- 已完成：
- 已验证：
- 已生成产物：

## 未完成内容

- 未完成项：
- 未完成原因：
- 是否阻塞下一步：

## 修改文件

- 新增：
- 修改：
- 删除：

## 关键接口

- 命令或入口：
- 输入：
- 输出：
- 行为或 schema 变化：

## 用户确认决策

- 新增 decision_id：
- 沿用 decision_id：
- 被替代 decision_id：

若无新决策，明确写“无”；不得把程序选择伪装成用户决策。

## 不可违反约束

- reviewed manifest 是样本级事实和纳入状态的唯一权威来源。
- group、include、`subject_id`、contrast 和 dataset strategy 由用户确认。
- validation 数据不得进入 discovery 模型。
- 单细胞差异分析采用 subject-level pseudobulk。
- 多 GSE 不得默认拼接。
- dataset 与 group 完全混杂时不得使用 joint model。
- 其余约束见 `PROJECT_SPEC.md` 和 `DECISIONS.md`。

## 测试结果

- 命令：
- 结果：
- 通过数：
- 失败数：
- 跳过数：
- 未运行测试及原因：

## 当前错误

- 错误：
- 影响范围：
- 已确认原因：
- 临时规避：

没有已知错误时明确写“无已确认错误”，不要省略本节。

## 下一步

- `task_id`：
- 唯一下一目标：
- 首个动作：
- 所需用户输入：

具体范围、禁止项和验收标准以 `NEXT_TASK.md` 为准。

## 推荐给下一会话的启动指令

```text
请先依次读取 docs/PROJECT_SPEC.md、docs/DECISIONS.md、
docs/CURRENT_STATE.md、docs/NEXT_TASK.md 和 docs/CHANGELOG.md。
严格遵守 PROJECT_SPEC 与已确认决策，只执行 NEXT_TASK 中的当前任务；
开始前核对实际代码和 Git 状态，完成后更新 CURRENT_STATE、必要时更新
DECISIONS、更新 CHANGELOG 与 NEXT_TASK，并在回复末尾提供简短
SESSION HANDOFF 摘要。
```

## 聊天回复中的简短格式

```text
SESSION HANDOFF
- 当前阶段：
- 本次完成：
- 测试：
- 当前阻塞：
- 下一任务：
- 必读文件：docs/PROJECT_SPEC.md、docs/DECISIONS.md、
  docs/CURRENT_STATE.md、docs/NEXT_TASK.md
```
