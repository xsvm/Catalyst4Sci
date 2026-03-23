# Catalyst4Sci 记忆系统设计 v0.1

## 1. 目标

Catalyst4Sci 的记忆系统负责支撑长时研究任务中的状态持久化、证据沉淀、决策回溯、上下文构造与任务恢复。

第一版设计目标如下：

1. 不依赖向量模型、embedding 或向量数据库。
2. 保证记忆结构可解释、可调试、可恢复。
3. 支撑自治研究循环中的规则检索和上下文组装。
4. 支撑 CLI 场景下的本地持久化与恢复。
5. 为未来引入语义检索保留扩展空间，但不作为当前依赖。

## 2. 设计原则

### 2.1 显式对象优先

记忆系统存储的不是“聊天记录”，而是结构化研究对象。

必须明确区分：

1. 研究目标
2. 假设
3. 文献证据
4. 实验记录
5. 决策记录
6. 开放问题
7. checkpoint

### 2.2 文件存内容，SQLite 存关系

文件系统负责保存原始内容和大对象：

1. 原始日志
2. 原始实验结果
3. 文献摘要文件
4. 报告
5. checkpoint JSON

SQLite 负责保存结构化索引和对象关系：

1. 当前状态索引
2. 假设、证据、实验、决策的元数据
3. 对象之间的关联关系
4. 检索和恢复所需索引

### 2.3 分层上下文加载

上下文不应一次性全部注入 agent，而应按层次装配：

1. `L0` 当前轮必需上下文
2. `L1` 当前任务工作记忆
3. `L2` 长期档案记忆

### 2.4 检索过程可观测

系统必须记录“为什么把这些记忆注入当前上下文”，便于调试与审计。

### 2.5 为语义增强预留接口

第一版不使用 embedding，但应保留未来接入语义后端的扩展点。

## 3. 记忆系统在整体架构中的位置

```text
Research Orchestrator
    |
    +------ State Manager
    +------ Next Action Selector
    +------ Skill Orchestrator
    |
    +------ Memory System
              |------ File Store
              |------ SQLite Index Store
              |------ Context Builder
              |------ Retrieval Logger
              |------ Checkpoint Manager
```

Memory System 不负责研究决策，但负责为决策提供：

1. 当前状态
2. 历史证据
3. 最近实验
4. 活跃假设
5. 上下文候选

## 4. 记忆对象模型

第一版建议使用以下核心对象。

## 4.1 ResearchGoal

```ts
interface ResearchGoal {
  id: string;
  title: string;
  description: string;
  success_metrics: string[];
  constraints: GoalConstraint[];
  workspace: string;
  created_at: string;
  updated_at: string;
}
```

## 4.2 ResearchState

```ts
interface ResearchState {
  research_id: string;
  goal_id: string;
  phase: ResearchPhase;
  status: "idle" | "running" | "blocked" | "waiting_human" | "finished" | "failed";
  current_plan_id: string | null;
  latest_checkpoint_id: string | null;
  budget_snapshot: BudgetState;
  summary: string;
  updated_at: string;
}
```

## 4.3 Hypothesis

```ts
interface Hypothesis {
  id: string;
  research_id: string;
  statement: string;
  rationale: string;
  status: "active" | "supported" | "rejected" | "stalled";
  confidence: number;
  created_at: string;
  updated_at: string;
}
```

## 4.4 Evidence

```ts
interface Evidence {
  id: string;
  research_id: string;
  type: "paper" | "experiment" | "observation" | "derived";
  title: string;
  summary: string;
  source: string;
  source_ref: string;
  relevance_score: number;
  created_at: string;
}
```

## 4.5 ExperimentSpec

```ts
interface ExperimentSpec {
  id: string;
  research_id: string;
  title: string;
  objective: string;
  command: string;
  workspace: string;
  timeout_seconds: number;
  expected_metrics: string[];
  created_at: string;
}
```

## 4.6 ExperimentRun

```ts
interface ExperimentRun {
  id: string;
  spec_id: string;
  research_id: string;
  status: "success" | "failed" | "timeout" | "crash";
  metrics: Record<string, number>;
  stdout_path: string;
  stderr_path: string;
  result_path: string;
  started_at: string;
  finished_at: string;
}
```

## 4.7 Decision

```ts
interface Decision {
  id: string;
  research_id: string;
  selected_action: string;
  rationale: string;
  alternatives: string[];
  risk_level: "low" | "medium" | "high";
  created_at: string;
}
```

## 4.8 OpenQuestion

```ts
interface OpenQuestion {
  id: string;
  research_id: string;
  question: string;
  status: "open" | "resolved" | "deferred";
  created_at: string;
  updated_at: string;
}
```

## 4.9 Checkpoint

```ts
interface Checkpoint {
  id: string;
  research_id: string;
  state_path: string;
  summary: string;
  created_at: string;
}
```

## 5. 目录结构设计

第一版建议使用如下目录结构：

```text
project-root/
  .catalyst/
    state/
      research.json
      checkpoints/
        cp-0001.json
        cp-0002.json
    runs/
      run-0001/
        stdout.log
        stderr.log
        result.json
      run-0002/
        stdout.log
        stderr.log
        result.json
    evidence/
      papers/
        paper-0001.md
        paper-0002.md
      experiments/
        exp-0001.md
      observations/
        obs-0001.md
    reports/
      summary-0001.md
      final-report.md
    retrieval/
      retrieval-0001.json
      retrieval-0002.json
    catalyst.db
```

### 5.1 各目录职责

`state/`

1. 保存当前研究状态快照
2. 保存 checkpoint 文件

`runs/`

1. 保存每次实验运行的原始输出
2. 保存结构化结果

`evidence/`

1. 保存人工可读的证据文档
2. 区分 papers、experiments、observations

`reports/`

1. 保存阶段性总结
2. 保存最终报告

`retrieval/`

1. 保存每次上下文检索日志
2. 用于后续调试和审计

`catalyst.db`

1. 保存所有结构化索引
2. 保存关系和元数据

## 6. SQLite 表设计

第一版建议使用 SQLite 作为结构化记忆索引数据库。

## 6.1 research_goals

```sql
CREATE TABLE research_goals (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  success_metrics_json TEXT NOT NULL,
  constraints_json TEXT NOT NULL,
  workspace TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## 6.2 research_states

```sql
CREATE TABLE research_states (
  research_id TEXT PRIMARY KEY,
  goal_id TEXT NOT NULL,
  phase TEXT NOT NULL,
  status TEXT NOT NULL,
  current_plan_id TEXT,
  latest_checkpoint_id TEXT,
  budget_snapshot_json TEXT NOT NULL,
  summary TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## 6.3 hypotheses

```sql
CREATE TABLE hypotheses (
  id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  statement TEXT NOT NULL,
  rationale TEXT NOT NULL,
  status TEXT NOT NULL,
  confidence REAL NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## 6.4 evidence_items

```sql
CREATE TABLE evidence_items (
  id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  source TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  relevance_score REAL NOT NULL,
  file_path TEXT,
  created_at TEXT NOT NULL
);
```

## 6.5 experiment_specs

```sql
CREATE TABLE experiment_specs (
  id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  title TEXT NOT NULL,
  objective TEXT NOT NULL,
  command TEXT NOT NULL,
  workspace TEXT NOT NULL,
  timeout_seconds INTEGER NOT NULL,
  expected_metrics_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## 6.6 experiment_runs

```sql
CREATE TABLE experiment_runs (
  id TEXT PRIMARY KEY,
  spec_id TEXT NOT NULL,
  research_id TEXT NOT NULL,
  status TEXT NOT NULL,
  metrics_json TEXT NOT NULL,
  stdout_path TEXT NOT NULL,
  stderr_path TEXT NOT NULL,
  result_path TEXT NOT NULL,
  started_at TEXT NOT NULL,
  finished_at TEXT NOT NULL
);
```

## 6.7 decisions

```sql
CREATE TABLE decisions (
  id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  selected_action TEXT NOT NULL,
  rationale TEXT NOT NULL,
  alternatives_json TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## 6.8 open_questions

```sql
CREATE TABLE open_questions (
  id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  question TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## 6.9 checkpoints

```sql
CREATE TABLE checkpoints (
  id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  state_path TEXT NOT NULL,
  summary TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## 6.10 object_links

该表用于表达多对多关系，是第一版非常关键的一张表。

```sql
CREATE TABLE object_links (
  id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  src_type TEXT NOT NULL,
  src_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  dst_type TEXT NOT NULL,
  dst_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

### 典型关系示例

1. `hypothesis -> supported_by -> evidence`
2. `hypothesis -> rejected_by -> experiment_run`
3. `decision -> based_on -> evidence`
4. `decision -> triggered -> experiment_spec`
5. `report -> summarizes -> experiment_run`

## 6.11 retrieval_logs

```sql
CREATE TABLE retrieval_logs (
  id TEXT PRIMARY KEY,
  research_id TEXT NOT NULL,
  query_type TEXT NOT NULL,
  query_payload_json TEXT NOT NULL,
  selected_items_json TEXT NOT NULL,
  discarded_items_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## 7. 检索设计

第一版采用“规则检索 + 元数据过滤 + 对象关系遍历”。

## 7.1 为什么不采用向量检索

第一版优先级是：

1. 可解释
2. 可调试
3. 可恢复
4. 易于本地实现

相比之下，向量检索会引入：

1. embedding 模型依赖
2. 语义误召回调试难度
3. 额外部署复杂度

因此 v1 明确不采用向量模型。

## 7.2 检索输入类型

检索主要由以下场景触发：

1. 构建当前轮上下文
2. 决策前读取最近实验
3. 决策前读取当前活跃假设
4. 报告生成前聚合关键证据
5. 恢复任务时重建状态摘要

## 7.3 规则检索方法

第一版可使用以下方法组合：

1. 按 `research_id` 过滤
2. 按 `phase` 过滤
3. 按 `status` 过滤
4. 按时间排序
5. 按对象关联关系追溯
6. 按固定标签或类型过滤
7. 按最近访问优先

## 7.4 检索示例

### 示例一：给当前轮实验设计提供上下文

步骤：

1. 读取当前 `ResearchState`
2. 读取最近 3 次 `ExperimentRun`
3. 读取所有 `active` 状态的 `Hypothesis`
4. 读取当前 phase 相关的 `Evidence`
5. 组合为 `L0 + L1` 上下文

### 示例二：给结果分析提供上下文

步骤：

1. 读取当前 `ExperimentRun`
2. 找到关联的 `ExperimentSpec`
3. 查询该 `spec` 关联的 `Hypothesis`
4. 查询该 `Hypothesis` 关联的 `Evidence`
5. 构造结果分析上下文

## 8. 分层上下文加载设计

## 8.1 L0 当前轮必需上下文

包括：

1. 当前目标摘要
2. 当前 phase
3. 当前 status
4. 最近一次决策
5. 当前待执行动作
6. 当前最佳实验摘要

特点：

1. 总是加载
2. 内容短小
3. 与下一步直接相关

## 8.2 L1 当前任务工作记忆

包括：

1. 近期实验摘要
2. 活跃假设
3. 当前关键 evidence
4. 当前开放问题
5. 最近失败模式

特点：

1. 按需加载
2. 面向当前阶段
3. 用于提升行动质量

## 8.3 L2 长期档案记忆

包括：

1. 完整实验历史
2. 历史报告
3. 已淘汰方案
4. 较早期的 papers 和 observations

特点：

1. 默认不加载
2. 仅在需要回溯时访问
3. 用于避免遗忘长期信息

## 9. 检索可观测性设计

每次检索都需要记录一条 retrieval log。

至少记录：

1. 谁发起了检索
2. 检索目的
3. 输入条件
4. 命中项列表
5. 最终选中项
6. 被丢弃项及原因

### retrieval log JSON 示例

```json
{
  "id": "retrieval-0003",
  "research_id": "research-001",
  "query_type": "build_context_for_experiment_design",
  "query_payload": {
    "phase": "experiment_design",
    "max_runs": 3,
    "hypothesis_status": "active"
  },
  "candidates": [
    { "type": "experiment_run", "id": "run-0012", "reason": "recent_success" },
    { "type": "hypothesis", "id": "hyp-0002", "reason": "active" }
  ],
  "selected_items": [
    { "type": "experiment_run", "id": "run-0012" },
    { "type": "hypothesis", "id": "hyp-0002" }
  ],
  "discarded_items": [
    { "type": "experiment_run", "id": "run-0003", "reason": "too_old" }
  ]
}
```

## 10. Checkpoint 设计

Checkpoint 是长时自治任务恢复的关键。

## 10.1 checkpoint 触发时机

建议在以下时机创建：

1. 每轮循环结束后
2. 每次关键决策后
3. 每次实验完成后
4. 人工接管前后
5. 任务结束前

## 10.2 checkpoint 内容

每个 checkpoint 至少包含：

1. 当前 `ResearchState`
2. 当前活跃假设摘要
3. 最近决策摘要
4. 最近实验摘要
5. 当前待执行动作队列
6. 当前 budget 快照

### checkpoint JSON 示例

```json
{
  "id": "cp-0005",
  "research_id": "research-001",
  "phase": "analysis",
  "status": "running",
  "latest_decision_id": "decision-0012",
  "latest_run_id": "run-0014",
  "queued_actions": [
    { "type": "compare_results", "run_ids": ["run-0012", "run-0014"] }
  ],
  "budget_snapshot": {
    "remaining_iterations": 12,
    "remaining_time_minutes": 180
  },
  "summary": "latest run improved validation metric by 0.8%"
}
```

## 11. Memory API 设计

为了与具体后端实现解耦，建议定义抽象接口。

```ts
interface MemoryBackend {
  saveGoal(goal: ResearchGoal): Promise<void>;
  loadGoal(goalId: string): Promise<ResearchGoal | null>;

  saveState(state: ResearchState): Promise<void>;
  loadState(researchId: string): Promise<ResearchState | null>;

  saveHypothesis(item: Hypothesis): Promise<void>;
  listHypotheses(researchId: string, filter?: object): Promise<Hypothesis[]>;

  saveEvidence(item: Evidence): Promise<void>;
  listEvidence(researchId: string, filter?: object): Promise<Evidence[]>;

  saveExperimentSpec(item: ExperimentSpec): Promise<void>;
  saveExperimentRun(item: ExperimentRun): Promise<void>;
  listExperimentRuns(researchId: string, filter?: object): Promise<ExperimentRun[]>;

  saveDecision(item: Decision): Promise<void>;
  listDecisions(researchId: string, filter?: object): Promise<Decision[]>;

  createLink(link: ObjectLink): Promise<void>;
  listLinks(researchId: string, srcId?: string, dstId?: string): Promise<ObjectLink[]>;

  saveCheckpoint(item: Checkpoint): Promise<void>;
  loadLatestCheckpoint(researchId: string): Promise<Checkpoint | null>;

  logRetrieval(item: RetrievalLog): Promise<void>;
}
```

第一版建议实现：

1. `SQLiteMemoryBackend`
2. `FileArtifactStore`

未来可以增加：

1. `OpenVikingMemoryBackend`
2. `VectorMemoryBackend`

## 12. 与 OpenViking 的关系

OpenViking 提供的核心启发有三点：

1. 记忆应采用分层上下文加载，而不是一股脑塞给模型。
2. 记忆组织应具备文件系统式结构和强可观察性。
3. 检索过程本身应该是可调试对象。

Catalyst4Sci 第一版借鉴这些思想，但不直接采用其重语义实现路线。

具体策略：

1. 借鉴分层上下文设计
2. 借鉴检索轨迹记录
3. 不引入 embedding 作为前置依赖
4. 先完成可解释的规则检索

## 13. 未来演进方向

在基础对象模型稳定后，可以考虑加入语义增强层：

1. 为 `Evidence.summary`、`Hypothesis.statement` 建立 embedding
2. 支持相似实验召回
3. 支持相似论文观点召回
4. 支持长期记忆聚类
5. 支持对历史研究轨迹做语义摘要

但这些都应该建立在第一版的稳定结构化记忆基础上，而不是替代它。

## 14. 结论

Catalyst4Sci 第一版记忆系统的核心策略是：

1. 用结构化对象替代聊天式记忆
2. 用文件系统保存内容
3. 用 SQLite 保存状态、索引和关系
4. 用分层上下文加载控制注入规模
5. 用规则检索和可观测日志支撑决策与恢复

这套设计的优势在于：

1. 易于实现
2. 易于调试
3. 易于恢复
4. 易于扩展

在此基础上，未来再考虑接入 OpenViking 或向量检索后端，会更加稳妥。
