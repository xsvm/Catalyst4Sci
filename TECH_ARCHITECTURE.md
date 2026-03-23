# Catalyst4Sci 技术架构设计 v0.1

## 1. 目标

本文档定义 Catalyst4Sci 的技术架构，目标是将通用 agent 升级为可持续、自主、可恢复、可审计的科研 agent 运行系统。

技术架构需要满足以下要求：

1. 支持在 CLI 和后续 IDE 环境中启动长期研究任务。
2. 支持 agent 在没有用户持续输入的情况下自动推进下一步。
3. 支持文献调研、假设生成、实验执行、结果分析的统一编排。
4. 支持状态持久化、checkpoint、恢复和人工接管。
5. 支持基于 skill 协议扩展多种研究动作。

## 2. 总体架构

系统采用“编排内核 + 适配层 + 状态存储 + 执行组件”的分层结构。

```text
CLI / IDE
    |
    v
Application Layer
    |
    v
Research Orchestrator
    |------ Next Action Selector
    |------ Research State Manager
    |------ Skill Orchestrator
    |------ Checkpoint Manager
    |
    +------ Agent Runner Adapter Layer
    |           |------ Codex Adapter
    |           |------ Claude Code Adapter
    |
    +------ Tool / Skill Execution Layer
    |           |------ Literature Skills
    |           |------ Experiment Skills
    |           |------ Code Skills
    |           |------ Reporting Skills
    |
    +------ Persistence Layer
                |------ State Store
                |------ Evidence Store
                |------ Run Log Store
                |------ Artifact Index
```

## 3. 核心设计原则

### 3.1 显式状态优先

系统不能依赖聊天上下文作为真实状态来源。所有研究进度都必须落在结构化状态中。

### 3.2 编排与执行分离

研究决策和具体执行必须解耦。

1. 决策由 Orchestrator 和 Next Action Selector 负责。
2. 执行由 Agent Runner 或 Skill Executor 负责。

### 3.3 长时任务优先

所有架构设计必须围绕长期运行任务构建，而不是围绕一次性请求。

### 3.4 可恢复性优先

每一轮研究循环都必须可以恢复，不允许核心状态只存在内存中。

### 3.5 可审计性优先

所有关键动作必须可追踪到：

1. 输入
2. 决策理由
3. 执行结果
4. 状态变化

## 4. 核心模块

## 4.1 Application Layer

Application Layer 对外提供统一入口。

职责：

1. 接收用户输入的研究目标与运行命令。
2. 启动或恢复研究任务。
3. 提供状态查询、暂停、恢复、终止和报告导出能力。

接口示例：

```text
catalyst research start
catalyst research status
catalyst research pause
catalyst research resume
catalyst research report
```

在 v1 中，Application Layer 以 CLI 为主；IDE 面板后续通过调用相同应用服务接入。

## 4.2 Research Orchestrator

Research Orchestrator 是系统核心，负责驱动自治研究循环。

职责：

1. 加载研究状态。
2. 校验当前状态是否可执行。
3. 调用 Next Action Selector 生成下一步。
4. 根据动作类型分发给 Agent Runner 或 Skill Orchestrator。
5. 接收执行结果并进行评估。
6. 更新状态和记忆。
7. 创建 checkpoint。
8. 判断是否继续、暂停、等待人工或终止。

建议主循环：

```text
load_state
-> validate_state
-> select_next_action
-> dispatch_action
-> collect_result
-> evaluate_result
-> update_state
-> checkpoint
-> decide_continue
```

## 4.3 Research State Manager

Research State Manager 负责维护显式研究状态。

职责：

1. 读取与写入 `ResearchState`
2. 管理阶段切换
3. 管理待执行队列
4. 校验状态完整性
5. 与 Checkpoint Manager 协同恢复任务

核心状态对象建议如下：

```ts
interface ResearchState {
  research_id: string;
  goal: ResearchGoal;
  phase: ResearchPhase;
  status: "idle" | "running" | "blocked" | "waiting_human" | "finished" | "failed";
  current_plan: ResearchPlan | null;
  hypotheses: Hypothesis[];
  queued_actions: QueuedAction[];
  completed_runs: ExperimentRun[];
  evidence_items: Evidence[];
  decisions: Decision[];
  open_questions: OpenQuestion[];
  budget: BudgetState;
  latest_checkpoint_id: string | null;
  updated_at: string;
}
```

## 4.4 Next Action Selector

Next Action Selector 负责回答一个核心问题：

**当前这一轮结束后，系统下一步应该做什么。**

职责：

1. 基于状态生成候选动作。
2. 对候选动作进行排序。
3. 选择一个动作执行。
4. 记录决策理由和未选动作。

### 候选动作来源

候选动作可以来自：

1. 当前阶段模板
2. 未完成任务队列
3. 实验失败后的补救策略
4. 文献与证据缺口
5. 预算约束变化

### 决策方法

v1 推荐使用规则驱动评分模型，不直接依赖黑盒 planning。

评分维度：

1. 信息增益
2. 目标相关性
3. 成本
4. 风险
5. 重复度
6. 阶段匹配度

可解释评分公式示例：

```text
score = expected_gain
      + phase_match
      - estimated_cost
      - risk_penalty
      - repetition_penalty
```

### 决策输出

```ts
interface NextActionDecision {
  selected_action: NextAction;
  alternatives: NextAction[];
  rationale: string;
  evidence_refs: string[];
  expected_gain: number;
  estimated_cost: number;
  risk_level: "low" | "medium" | "high";
}
```

## 4.5 Agent Runner Adapter Layer

该层负责把不同 agent 统一抽象成可调用执行单元。

职责：

1. 启动 agent 进程或 API 调用
2. 注入上下文、限制和任务说明
3. 收集结构化输出、工具调用日志和错误信息
4. 处理超时、中断、恢复和取消

建议抽象接口：

```ts
interface AgentAdapter {
  name(): string;
  supportsTools(): boolean;
  supportsStreaming(): boolean;
  run(input: AgentInvocation): Promise<AgentInvocationResult>;
  resume(runId: string): Promise<AgentInvocationResult>;
  cancel(runId: string): Promise<void>;
}
```

首批建议支持：

1. Codex CLI Adapter
2. Claude Code Adapter

### 适配层边界

适配层只负责执行，不负责：

1. 决定研究方向
2. 选择实验策略
3. 更新核心状态

## 4.6 Skill Orchestrator

Skill Orchestrator 负责统一调用不同 skill。

职责：

1. 根据 action 选择 skill
2. 解析 skill 输入输出
3. 控制 skill 执行生命周期
4. 把 skill 结果标准化返回给 Orchestrator

### skill 协议建议

```ts
interface SkillDefinition {
  id: string;
  name: string;
  description: string;
  input_schema: object;
  output_schema: object;
  execution_mode: "agent" | "script" | "tool" | "hybrid";
  side_effects: string[];
  risk_level: "low" | "medium" | "high";
}
```

### 推荐 skill 分类

1. `literature.search`
2. `literature.read`
3. `literature.extract_evidence`
4. `hypothesis.propose`
5. `experiment.design`
6. `experiment.run`
7. `experiment.evaluate`
8. `code.modify`
9. `report.generate`

## 4.7 Experiment Execution Layer

Experiment Execution Layer 负责标准化实验任务。

职责：

1. 接收实验配置
2. 启动实验进程
3. 采集日志
4. 提取关键指标
5. 输出统一实验结果对象

建议结构：

```ts
interface ExperimentSpec {
  id: string;
  title: string;
  objective: string;
  command: string;
  env: Record<string, string>;
  expected_metrics: string[];
  timeout_seconds: number;
  workspace: string;
}

interface ExperimentRun {
  id: string;
  spec_id: string;
  status: "success" | "failed" | "timeout" | "crash";
  metrics: Record<string, number>;
  stdout_path: string;
  stderr_path: string;
  started_at: string;
  finished_at: string;
}
```

## 4.8 Memory & Evidence Store

Memory & Evidence Store 负责保存长期研究记忆。

职责：

1. 保存文献摘要
2. 保存证据片段
3. 保存实验观察
4. 保存决策记录
5. 保存阶段性结论
6. 支持检索和摘要重建

### 存储原则

1. 区分事实、假设、推断
2. 每条证据必须可追溯来源
3. 决策必须关联证据
4. 不把原始聊天记录当成唯一记忆载体

建议对象：

```ts
interface Evidence {
  id: string;
  type: "paper" | "experiment" | "observation" | "derived";
  summary: string;
  source: string;
  source_ref: string;
  relevance_score: number;
}

interface Hypothesis {
  id: string;
  statement: string;
  source_refs: string[];
  status: "active" | "supported" | "rejected" | "stalled";
  confidence: number;
}

interface Decision {
  id: string;
  timestamp: string;
  selected_action: string;
  rationale: string;
  evidence_refs: string[];
  alternatives: string[];
}
```

## 4.9 Checkpoint Manager

Checkpoint Manager 负责长时任务恢复。

职责：

1. 在关键节点写入 checkpoint
2. 支持列出可恢复点
3. 支持从指定 checkpoint 恢复
4. 确保状态和工作区一致性

每个 checkpoint 建议包含：

1. `ResearchState` 快照
2. 最近决策
3. 最近执行结果
4. 当前待执行队列
5. 工作区摘要
6. artifact 索引

## 5. 存储架构

v1 建议使用“本地文件 + SQLite”的混合持久化方案。

### 5.1 文件存储

用于保存：

1. 文档型 artifact
2. 原始日志
3. 报告
4. 研究快照 JSON

### 5.2 SQLite

用于保存：

1. 研究状态索引
2. 实验记录索引
3. 决策记录索引
4. checkpoint 元数据
5. 证据元数据

### 5.3 建议目录结构

```text
project-root/
  .catalyst/
    state/
      research.json
      checkpoints/
    runs/
      run-001/
        stdout.log
        stderr.log
        result.json
    evidence/
      papers/
      experiments/
    reports/
    catalyst.db
```

这样做的优点：

1. 简单直接
2. 易于调试
3. 易于迁移
4. 不依赖外部数据库

## 6. 运行流程

## 6.1 启动流程

```text
User CLI Input
-> Create ResearchGoal
-> Initialize ResearchState
-> Create Initial Checkpoint
-> Enter Orchestrator Loop
```

## 6.2 单轮循环

```text
Load State
-> Generate Candidate Actions
-> Select Action
-> Execute via Agent/Skill
-> Parse Outputs
-> Evaluate Result
-> Update State
-> Save Checkpoint
-> Decide Continue / Pause / Stop
```

## 6.3 恢复流程

```text
Load Latest Checkpoint
-> Validate Workspace
-> Rehydrate ResearchState
-> Resume Loop
```

## 7. CLI 架构

v1 以 CLI 为主要交互形式。

建议命令：

```bash
catalyst research start --goal "..." --workspace "./workspace"
catalyst research status --id "<research_id>"
catalyst research pause --id "<research_id>"
catalyst research resume --id "<research_id>"
catalyst research report --id "<research_id>"
```

CLI 层应尽量薄，只负责：

1. 参数解析
2. 调用应用服务
3. 输出状态与结果

不在 CLI 内写核心编排逻辑。

## 8. IDE 集成架构

IDE 不是核心运行时，而是外层可视化控制入口。

建议能力：

1. 查看当前研究阶段
2. 查看当前任务状态
3. 查看最近实验结果
4. 查看下一步动作
5. 批准高风险操作
6. 暂停与恢复任务

IDE 可通过调用 Application Layer 提供的服务实现。

## 9. 安全与治理

系统必须具备基本治理能力，避免自治循环失控。

### 9.1 风险分级

动作分为：

1. 低风险
2. 中风险
3. 高风险

高风险动作默认需要人工审批。

### 9.2 停止条件

必须支持以下停止条件：

1. 达成目标
2. 预算耗尽
3. 连续无进展
4. 连续失败
5. 风险过高
6. 无有价值下一步动作

### 9.3 预算控制

至少支持：

1. token 预算
2. 时间预算
3. 实验次数预算
4. 资源使用预算

## 10. 与 autoresearch 的关系

autoresearch 提供的启发主要在于：

1. 证明 agent 可在固定闭环中连续开展实验。
2. 证明“自动下一步”需要依赖明确指标和回路，而不是聊天驱动。
3. 证明最小自治系统可以先从单一目标、单一工作区开始。

Catalyst4Sci 与其不同之处在于：

1. 不把循环隐藏在 prompt 中。
2. 不把 git 历史当作主要状态机。
3. 不局限于单文件实验优化。
4. 引入显式状态、记忆、决策与恢复机制。

## 11. 与 OpenViking 的关系

OpenViking 的定位更接近“agent 的上下文数据库/记忆基础设施”，而不是研究编排系统。

对 Catalyst4Sci 的价值主要在以下方面：

1. 其“文件系统范式管理记忆、资源、技能”的思想值得参考。
2. 其“分层上下文加载”适合长时研究任务中的 token 控制。
3. 其“上下文可观测性”对调试研究循环很重要。

但 Catalyst4Sci 不能直接等同于 OpenViking，原因是：

1. OpenViking 更偏上下文存储与检索。
2. Catalyst4Sci 的核心难点是研究循环与下一步决策。
3. 上下文数据库只能解决记忆问题，不能替代编排内核。

因此推荐定位为：

1. Catalyst4Sci 是上层研究自治运行时。
2. OpenViking 这类系统可以作为未来可插拔的记忆/上下文层候选。

## 12. MVP 技术范围

v1 技术实现建议只覆盖以下内容：

1. 单任务 Orchestrator
2. CLI 入口
3. 本地状态存储
4. 单 agent 适配
5. 基础 skill 协议
6. 实验执行与结果采集
7. 决策日志
8. checkpoint 恢复

不进入 v1 的内容：

1. 多 agent 协作调度
2. 分布式执行平台
3. 复杂 UI 系统
4. 高级知识图谱
5. 复杂上下文数据库接入

## 13. 推荐代码结构

建议未来代码目录结构如下：

```text
Catalyst4Sci/
  catalyst/
    app/
      cli/
      services/
    orchestrator/
      loop_engine.py
      next_action_selector.py
      state_manager.py
      checkpoint_manager.py
    agents/
      base.py
      codex_adapter.py
      claude_code_adapter.py
    skills/
      base.py
      orchestrator.py
      literature/
      experiment/
      reporting/
    storage/
      state_store.py
      evidence_store.py
      run_store.py
      sqlite.py
    models/
      research.py
      experiment.py
      decision.py
      evidence.py
    governance/
      risk.py
      budget.py
      approval.py
  docs/
    PRD.md
    TECH_ARCHITECTURE.md
```

## 14. 结论

Catalyst4Sci 的技术核心不是“调用大模型”，而是：

**把科研任务建模为一个可持续运行的研究状态机，并通过编排、记忆、执行与恢复机制把 agent 真正变成自治研究者。**

从工程角度看，最先要做稳的是四件事：

1. 显式状态
2. 下一步决策
3. 持久化与恢复
4. 统一执行适配层

只要这四件事没有成立，系统就仍然只是一个高级聊天代理。反之，一旦这四件事成立，Catalyst4Sci 才真正具备成为科研 agent 平台的基础。
