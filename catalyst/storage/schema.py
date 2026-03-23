SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS research_goals (
      id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      description TEXT NOT NULL,
      success_metrics_json TEXT NOT NULL,
      constraints_json TEXT NOT NULL,
      workspace TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS research_states (
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
    """,
    """
    CREATE TABLE IF NOT EXISTS hypotheses (
      id TEXT PRIMARY KEY,
      research_id TEXT NOT NULL,
      statement TEXT NOT NULL,
      rationale TEXT NOT NULL,
      status TEXT NOT NULL,
      confidence REAL NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence_items (
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
    """,
    """
    CREATE TABLE IF NOT EXISTS experiment_specs (
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
    """,
    """
    CREATE TABLE IF NOT EXISTS experiment_runs (
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
    """,
    """
    CREATE TABLE IF NOT EXISTS decisions (
      id TEXT PRIMARY KEY,
      research_id TEXT NOT NULL,
      selected_action TEXT NOT NULL,
      rationale TEXT NOT NULL,
      alternatives_json TEXT NOT NULL,
      risk_level TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS open_questions (
      id TEXT PRIMARY KEY,
      research_id TEXT NOT NULL,
      question TEXT NOT NULL,
      status TEXT NOT NULL,
      created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS checkpoints (
      id TEXT PRIMARY KEY,
      research_id TEXT NOT NULL,
      state_path TEXT NOT NULL,
      summary TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS object_links (
      id TEXT PRIMARY KEY,
      research_id TEXT NOT NULL,
      src_type TEXT NOT NULL,
      src_id TEXT NOT NULL,
      relation_type TEXT NOT NULL,
      dst_type TEXT NOT NULL,
      dst_id TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS retrieval_logs (
      id TEXT PRIMARY KEY,
      research_id TEXT NOT NULL,
      query_type TEXT NOT NULL,
      query_payload_json TEXT NOT NULL,
      selected_items_json TEXT NOT NULL,
      discarded_items_json TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    """,
]


INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_states_goal_id ON research_states(goal_id);",
    "CREATE INDEX IF NOT EXISTS idx_hypotheses_research_id ON hypotheses(research_id);",
    "CREATE INDEX IF NOT EXISTS idx_evidence_research_id ON evidence_items(research_id);",
    "CREATE INDEX IF NOT EXISTS idx_runs_research_id ON experiment_runs(research_id);",
    "CREATE INDEX IF NOT EXISTS idx_decisions_research_id ON decisions(research_id);",
    "CREATE INDEX IF NOT EXISTS idx_checkpoints_research_id ON checkpoints(research_id);",
]
