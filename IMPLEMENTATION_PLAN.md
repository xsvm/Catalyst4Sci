# Catalyst4Sci MVP 实施计划 v0.1

## 1. 目标

本文档定义 Catalyst4Sci 第一阶段 MVP 的实施计划，将 PRD 和技术架构收敛为可执行开发任务。

实施目标：

1. 在不依赖向量模型的前提下，完成最小可闭环科研 agent 运行时。
2. 打通从研究目标创建到多轮自治执行、状态持久化、checkpoint 恢复和报告输出的主链路。
3. 优先支持 CLI 运行方式。
4. 优先支持单研究任务、单工作区、单 agent 适配。

## 2. MVP 范围确认

MVP 必须覆盖：

1. 单研究任务管理
2. CLI 启动、状态查看、暂停、恢复、报告导出
3. 研究状态模型与持久化
4. 文件系统 + SQLite 记忆系统
5. 基础 checkpoint 恢复
6. Next Action 规则引擎
7. 单 agent 适配层
8. 基础 skill 协议
9. 实验执行与结果采集
10. 研究报告输出

MVP 不覆盖：

1. 向量检索
2. 多 agent 协作
3. IDE 图形化面板
4. 分布式执行
5. 复杂权限系统

## 3. 开发原则

### 3.1 先主链路后增强

优先实现从 `start -> loop -> checkpoint -> resume -> report` 的闭环，不先做高级优化。

### 3.2 先单机后扩展

优先完成本地 CLI 模式，确保状态、执行和恢复稳定。

### 3.3 先结构化再智能化

优先实现显式对象模型和规则决策，不先做语义检索和复杂 planner。

## 4. 里程碑划分

建议将 MVP 拆为 5 个里程碑。

### M1 基础骨架

目标：

1. 建立项目目录结构
2. 建立基础数据模型
3. 建立 SQLite schema
4. 建立 CLI 基础框架

### M2 记忆与状态

目标：

1. 实现文件系统 + SQLite 记忆后端
2. 实现 ResearchState 读写
3. 实现 checkpoint 存取
4. 实现基础查询能力

### M3 执行与实验

目标：

1. 实现 agent 适配器抽象
2. 实现第一个 agent adapter
3. 实现实验执行器
4. 打通运行日志与结果采集

### M4 自治循环

目标：

1. 实现 Next Action Selector
2. 实现 Loop Engine
3. 实现暂停、恢复与停止逻辑
4. 打通单任务自治循环

### M5 报告与收尾

目标：

1. 实现阶段性总结和最终报告
2. 完善检索日志和审计记录
3. 补充测试和错误处理
4. 完成 MVP 验收

## 5. 模块任务拆解

## 5.1 项目骨架与基础设施

优先级：`P0`

### 任务 5.1.1 建立项目目录结构

内容：

1. 创建 `catalyst/` 主包
2. 创建 `app/`、`orchestrator/`、`agents/`、`skills/`、`storage/`、`models/`、`governance/`
3. 创建 `docs/` 或保留当前根目录文档策略

产出：

1. 基本目录结构
2. 包初始化文件

验收标准：

1. 项目结构与技术架构文档一致
2. 模块边界清晰

### 任务 5.1.2 建立项目配置和依赖管理

内容：

1. 选择 Python 版本与包管理方式
2. 建立 `pyproject.toml`
3. 配置基础开发工具

产出：

1. 最小可运行项目

验收标准：

1. 本地可创建虚拟环境
2. CLI 可运行空命令

### 任务 5.1.3 建立统一 ID 生成与时间工具

内容：

1. 定义各类对象 ID 规则
2. 定义 UTC 时间格式工具

验收标准：

1. 各核心对象 ID 生成一致
2. 时间序列化格式统一

## 5.2 数据模型

优先级：`P0`

### 任务 5.2.1 实现核心数据模型

内容：

1. 实现 `ResearchGoal`
2. 实现 `ResearchState`
3. 实现 `Hypothesis`
4. 实现 `Evidence`
5. 实现 `ExperimentSpec`
6. 实现 `ExperimentRun`
7. 实现 `Decision`
8. 实现 `OpenQuestion`
9. 实现 `Checkpoint`

建议：

1. 使用 dataclass 或 Pydantic
2. 统一 JSON 序列化策略

验收标准：

1. 所有模型可序列化和反序列化
2. 所有模型具备稳定 ID 和基础校验

### 任务 5.2.2 定义枚举和状态常量

内容：

1. 定义 `ResearchPhase`
2. 定义 `ResearchStatus`
3. 定义 `RiskLevel`
4. 定义 `ExperimentRunStatus`

验收标准：

1. 不在业务代码中硬编码状态字符串

## 5.3 存储层

优先级：`P0`

### 任务 5.3.1 实现 SQLite schema 初始化

内容：

1. 创建 `catalyst.db`
2. 初始化所有核心表
3. 初始化必要索引

验收标准：

1. 项目启动时可自动初始化数据库
2. 重复初始化不会破坏已有数据

### 任务 5.3.2 实现 FileArtifactStore

内容：

1. 创建 `.catalyst/` 目录
2. 保存 runs、evidence、reports、state、retrieval
3. 提供统一路径生成接口

验收标准：

1. 所有 artifact 路径稳定可预测
2. 目录结构符合文档设计

### 任务 5.3.3 实现 SQLiteMemoryBackend

内容：

1. 封装 goal/state/hypothesis/evidence/decision/run/checkpoint 的 CRUD
2. 封装 object_links
3. 封装 retrieval_logs

验收标准：

1. 各对象可完整读写
2. 基础查询可工作
3. 能按 research_id 做隔离

### 任务 5.3.4 实现对象关系查询接口

内容：

1. 查询 hypothesis 关联 evidence
2. 查询 decision 关联 evidence
3. 查询 experiment_run 关联 hypothesis
4. 查询 checkpoint 对应状态

验收标准：

1. 能支撑 Next Action Selector 的主要查询场景

## 5.4 状态与 checkpoint

优先级：`P0`

### 任务 5.4.1 实现 StateManager

内容：

1. 读取当前 `ResearchState`
2. 更新 phase/status/summary
3. 写入状态快照

验收标准：

1. 可以正确追踪任务进度
2. 状态写入具备一致性

### 任务 5.4.2 实现 CheckpointManager

内容：

1. 创建 checkpoint JSON
2. 在 SQLite 中登记 checkpoint 元数据
3. 提供 `load_latest_checkpoint`
4. 提供恢复前一致性校验

验收标准：

1. 中断后可以恢复到最近 checkpoint
2. checkpoint 文件与数据库记录一致

## 5.5 CLI 层

优先级：`P0`

### 任务 5.5.1 实现 CLI 基础命令

内容：

1. `research start`
2. `research status`
3. `research pause`
4. `research resume`
5. `research report`

验收标准：

1. 命令行参数可用
2. 每个命令能输出明确结果

### 任务 5.5.2 实现任务初始化流程

内容：

1. 创建研究目标
2. 初始化 `ResearchState`
3. 初始化 `.catalyst/`
4. 创建初始 checkpoint

验收标准：

1. 新任务可以一键启动

## 5.6 Agent 适配层

优先级：`P1`

### 任务 5.6.1 定义 AgentAdapter 抽象

内容：

1. 定义 `run`
2. 定义 `resume`
3. 定义 `cancel`

验收标准：

1. Orchestrator 不依赖具体 agent 实现

### 任务 5.6.2 实现第一个 Agent Adapter

建议：

1. 首先选定一个当前最容易接入的宿主环境
2. 保持接口最小化

验收标准：

1. 能从 orchestrator 发起一次 agent 执行
2. 能收集输出和失败信息

### 任务 5.6.3 实现 Agent 运行日志记录

内容：

1. 保存输入摘要
2. 保存输出摘要
3. 保存运行状态

验收标准：

1. 单次 agent 调用可追踪

## 5.7 Skill 协议与调度

优先级：`P1`

### 任务 5.7.1 定义 SkillDefinition 和 SkillExecutor 接口

内容：

1. 定义输入输出 schema
2. 定义执行模式
3. 定义风险等级

验收标准：

1. 新 skill 可通过统一接口接入

### 任务 5.7.2 实现 SkillOrchestrator

内容：

1. 根据 action 路由 skill
2. 执行 skill
3. 标准化输出

验收标准：

1. Loop Engine 可统一调用 skill

### 任务 5.7.3 实现首批基础 skill

建议首批：

1. `experiment.run`
2. `experiment.evaluate`
3. `report.generate`

验收标准：

1. 至少打通一个实验场景

## 5.8 实验执行层

优先级：`P1`

### 任务 5.8.1 实现 ExperimentRunner

内容：

1. 接收 `ExperimentSpec`
2. 启动子进程
3. 控制超时
4. 写入 stdout/stderr

验收标准：

1. 能稳定执行本地实验命令
2. 超时和失败可正确处理

### 任务 5.8.2 实现结果解析器

内容：

1. 解析结构化指标
2. 生成 `ExperimentRun`
3. 写入 SQLite 与 result.json

验收标准：

1. 指标可读
2. 失败运行也有完整记录

## 5.9 Next Action Selector

优先级：`P1`

### 任务 5.9.1 定义 NextAction 与 Decision 模型

内容：

1. 定义候选动作结构
2. 定义决策输出结构

验收标准：

1. 各动作类型具备统一表达

### 任务 5.9.2 实现候选动作生成器

内容：

1. 根据 phase 生成动作
2. 根据 open questions 生成动作
3. 根据实验结果生成动作

验收标准：

1. 在不同 phase 下能生成合理候选

### 任务 5.9.3 实现规则评分器

内容：

1. 基于 gain/cost/risk/repetition 排序
2. 输出 rationale

验收标准：

1. 决策过程可解释
2. 能避免明显重复动作

## 5.10 上下文构造与检索

优先级：`P1`

### 任务 5.10.1 实现 ContextBuilder

内容：

1. 组装 `L0`
2. 组装 `L1`
3. 条件性检索 `L2`

验收标准：

1. 当前轮上下文能稳定生成

### 任务 5.10.2 实现 RetrievalLogger

内容：

1. 记录查询条件
2. 记录命中项和排序结果
3. 落盘 retrieval JSON
4. 写入 SQLite 检索日志

验收标准：

1. 每次关键上下文构造都可追溯

## 5.11 自治循环

优先级：`P1`

### 任务 5.11.1 实现 LoopEngine

内容：

1. load_state
2. select_next_action
3. dispatch_action
4. collect_result
5. update_state
6. checkpoint

验收标准：

1. 完成至少 2-3 轮连续自治执行

### 任务 5.11.2 实现暂停、恢复与停止逻辑

内容：

1. 支持 pause 标记
2. 支持 resume
3. 支持 stop 条件

验收标准：

1. 任务不会因为单次中断失去状态

## 5.12 报告输出

优先级：`P2`

### 任务 5.12.1 实现阶段性总结生成

内容：

1. 汇总近期实验
2. 汇总近期决策
3. 汇总关键 evidence

验收标准：

1. 能输出当前状态摘要

### 任务 5.12.2 实现最终报告生成

内容：

1. 输出 goal
2. 输出主要实验
3. 输出主要结论
4. 输出未解决问题
5. 输出后续建议

验收标准：

1. 任务结束时能生成结构化 Markdown 报告

## 5.13 测试与稳定性

优先级：`P1`

### 任务 5.13.1 单元测试

覆盖：

1. 数据模型序列化
2. SQLiteMemoryBackend
3. StateManager
4. CheckpointManager
5. Next Action Selector

### 任务 5.13.2 集成测试

覆盖：

1. `research start`
2. `research resume`
3. 单次 experiment run
4. 两轮自治循环

### 任务 5.13.3 故障恢复测试

覆盖：

1. 中途崩溃恢复
2. 实验失败恢复
3. 检索日志缺失时的降级策略

## 6. 优先级汇总

### P0 必须先完成

1. 项目骨架
2. 数据模型
3. SQLite schema
4. FileArtifactStore
5. SQLiteMemoryBackend
6. StateManager
7. CheckpointManager
8. CLI 基础命令

### P1 MVP 主链路必做

1. AgentAdapter 抽象
2. 首个 Agent Adapter
3. Skill 协议
4. ExperimentRunner
5. 结果解析器
6. Next Action Selector
7. ContextBuilder
8. RetrievalLogger
9. LoopEngine
10. 基础测试

### P2 可以在主链路跑通后补齐

1. 最终报告优化
2. 审计输出增强
3. 更细的错误分类
4. 更多 skill

## 7. 推荐开发顺序

建议严格按以下顺序推进：

### 第 1 阶段

1. 建项目骨架
2. 建数据模型
3. 建 SQLite schema
4. 建 FileArtifactStore
5. 建 SQLiteMemoryBackend

### 第 2 阶段

1. 建 StateManager
2. 建 CheckpointManager
3. 建 CLI start/status/resume
4. 打通任务初始化

### 第 3 阶段

1. 建 AgentAdapter 抽象
2. 建首个 adapter
3. 建 ExperimentRunner
4. 建结果解析器

### 第 4 阶段

1. 建 Next Action Selector
2. 建 ContextBuilder
3. 建 RetrievalLogger
4. 建 LoopEngine

### 第 5 阶段

1. 建报告输出
2. 建测试
3. 做恢复和异常打磨

## 8. 每阶段验收标准

## 8.1 M1 验收

1. 可以运行 CLI 空命令
2. 数据模型和 schema 可初始化
3. `.catalyst/` 可被创建

## 8.2 M2 验收

1. 可以创建研究任务
2. 可以写入和读取 `ResearchState`
3. 可以创建和读取 checkpoint

## 8.3 M3 验收

1. 可以执行一次实验命令
2. 可以采集 stdout/stderr
3. 可以写入 `ExperimentRun`

## 8.4 M4 验收

1. 可以连续跑 2-3 轮自治循环
2. 可以基于规则选择不同下一步动作
3. 可以暂停并恢复

## 8.5 M5 验收

1. 可以输出 Markdown 报告
2. 检索日志可检查
3. 基础集成测试通过

## 9. 风险与缓解

### 风险 9.1 主循环过早复杂化

缓解：

1. v1 只用规则驱动
2. 不引入多 agent 协作

### 风险 9.2 存储层过度设计

缓解：

1. 第一版只实现文档已列出的核心表
2. 不引入外部数据库

### 风险 9.3 适配器层耦合过深

缓解：

1. 先锁定统一 `AgentAdapter` 接口
2. 把宿主细节限制在 adapter 内部

### 风险 9.4 检索逻辑失控

缓解：

1. 强制记录 retrieval log
2. 强制区分 L0/L1/L2

### 风险 9.5 过早引入语义依赖

缓解：

1. 明确 v1 不接入 embedding
2. 先用结构化对象模型证明闭环成立

## 10. 建议的首个端到端演示场景

建议首个 demo 场景：

1. 用户通过 CLI 创建研究目标
2. 系统初始化 `.catalyst/`
3. 系统生成初始状态
4. 系统运行一个实验命令
5. 系统记录结果
6. 系统基于规则生成下一步
7. 系统再运行第二轮
8. 系统暂停
9. 用户恢复任务
10. 系统输出总结报告

这个 demo 不要求文献调研一定上线，但必须证明：

1. 状态可持续
2. 循环可自驱
3. 记忆可恢复
4. 报告可输出

## 11. 结论

Catalyst4Sci MVP 的实施重点不在“多做功能”，而在“先把自治研究闭环做通”。

最重要的开发顺序是：

1. 先把状态和记忆系统做稳
2. 再把执行和实验链路打通
3. 再把自动下一步决策接上
4. 最后补齐报告和测试

只要这条主链路成立，后续无论接 OpenViking、向量检索、更多 agent 还是更复杂的科研场景，都会容易很多。
