from __future__ import annotations

import json
from dataclasses import asdict
from typing import Protocol

from catalyst.models.enums import ExperimentRunStatus, ResearchPhase, ResearchStatus, RiskLevel
from catalyst.models.research import Checkpoint, Decision, ExperimentRun, ExperimentSpec, ResearchGoal, ResearchState
from catalyst.storage.sqlite import SQLiteStore


class MemoryBackend(Protocol):
    def save_goal(self, goal: ResearchGoal) -> None: ...

    def load_goal(self, goal_id: str) -> ResearchGoal | None: ...

    def save_state(self, state: ResearchState) -> None: ...

    def load_state(self, research_id: str) -> ResearchState | None: ...

    def save_checkpoint(self, checkpoint: Checkpoint) -> None: ...

    def load_latest_checkpoint(self, research_id: str) -> Checkpoint | None: ...

    def save_experiment_spec(self, spec: ExperimentSpec) -> None: ...

    def save_experiment_run(self, run: ExperimentRun) -> None: ...

    def list_recent_experiment_runs(self, research_id: str, limit: int = 3) -> list[ExperimentRun]: ...

    def save_decision(self, decision: Decision) -> None: ...

    def list_recent_decisions(self, research_id: str, limit: int = 3) -> list[Decision]: ...

    def log_retrieval(
        self,
        research_id: str,
        query_type: str,
        query_payload: dict,
        selected_items: dict,
        discarded_items: list,
    ) -> None: ...


class SQLiteMemoryBackend:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def save_goal(self, goal: ResearchGoal) -> None:
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO research_goals
                (id, title, description, success_metrics_json, constraints_json, workspace, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    goal.id,
                    goal.title,
                    goal.description,
                    json.dumps(goal.success_metrics),
                    json.dumps(goal.constraints),
                    goal.workspace,
                    goal.created_at,
                    goal.updated_at,
                ),
            )
            conn.commit()

    def load_goal(self, goal_id: str) -> ResearchGoal | None:
        with self.store.connect() as conn:
            row = conn.execute("SELECT * FROM research_goals WHERE id = ?", (goal_id,)).fetchone()
        if row is None:
            return None
        return ResearchGoal(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            success_metrics=json.loads(row["success_metrics_json"]),
            constraints=json.loads(row["constraints_json"]),
            workspace=row["workspace"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def save_state(self, state: ResearchState) -> None:
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO research_states
                (research_id, goal_id, phase, status, current_plan_id, latest_checkpoint_id, budget_snapshot_json, summary, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.research_id,
                    state.goal_id,
                    state.phase.value,
                    state.status.value,
                    state.current_plan_id,
                    state.latest_checkpoint_id,
                    json.dumps(state.budget_snapshot),
                    state.summary,
                    state.updated_at,
                ),
            )
            conn.commit()

    def load_state(self, research_id: str) -> ResearchState | None:
        with self.store.connect() as conn:
            row = conn.execute("SELECT * FROM research_states WHERE research_id = ?", (research_id,)).fetchone()
        if row is None:
            return None
        return ResearchState(
            research_id=row["research_id"],
            goal_id=row["goal_id"],
            phase=ResearchPhase(row["phase"]),
            status=ResearchStatus(row["status"]),
            current_plan_id=row["current_plan_id"],
            latest_checkpoint_id=row["latest_checkpoint_id"],
            budget_snapshot=json.loads(row["budget_snapshot_json"]),
            summary=row["summary"],
            updated_at=row["updated_at"],
        )

    def save_checkpoint(self, checkpoint: Checkpoint) -> None:
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO checkpoints
                (id, research_id, state_path, summary, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.id,
                    checkpoint.research_id,
                    checkpoint.state_path,
                    checkpoint.summary,
                    checkpoint.created_at,
                ),
            )
            conn.commit()

    def load_latest_checkpoint(self, research_id: str) -> Checkpoint | None:
        with self.store.connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM checkpoints
                WHERE research_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (research_id,),
            ).fetchone()
        if row is None:
            return None
        return Checkpoint(
            id=row["id"],
            research_id=row["research_id"],
            state_path=row["state_path"],
            summary=row["summary"],
            created_at=row["created_at"],
        )

    def save_experiment_spec(self, spec: ExperimentSpec) -> None:
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO experiment_specs
                (id, research_id, title, objective, command, workspace, timeout_seconds, expected_metrics_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    spec.id,
                    spec.research_id,
                    spec.title,
                    spec.objective,
                    spec.command,
                    spec.workspace,
                    spec.timeout_seconds,
                    json.dumps(spec.expected_metrics),
                    spec.created_at,
                ),
            )
            conn.commit()

    def save_experiment_run(self, run: ExperimentRun) -> None:
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO experiment_runs
                (id, spec_id, research_id, status, metrics_json, stdout_path, stderr_path, result_path, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.spec_id,
                    run.research_id,
                    run.status.value if isinstance(run.status, ExperimentRunStatus) else str(run.status),
                    json.dumps(run.metrics),
                    run.stdout_path,
                    run.stderr_path,
                    run.result_path,
                    run.started_at,
                    run.finished_at,
                ),
            )
            conn.commit()

    def list_recent_experiment_runs(self, research_id: str, limit: int = 3) -> list[ExperimentRun]:
        with self.store.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM experiment_runs
                WHERE research_id = ?
                ORDER BY finished_at DESC
                LIMIT ?
                """,
                (research_id, limit),
            ).fetchall()
        return [
            ExperimentRun(
                id=row["id"],
                spec_id=row["spec_id"],
                research_id=row["research_id"],
                status=ExperimentRunStatus(row["status"]),
                metrics=json.loads(row["metrics_json"]),
                stdout_path=row["stdout_path"],
                stderr_path=row["stderr_path"],
                result_path=row["result_path"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
            )
            for row in rows
        ]

    def save_decision(self, decision: Decision) -> None:
        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO decisions
                (id, research_id, selected_action, rationale, alternatives_json, risk_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.id,
                    decision.research_id,
                    decision.selected_action,
                    decision.rationale,
                    json.dumps(decision.alternatives),
                    decision.risk_level.value if isinstance(decision.risk_level, RiskLevel) else str(decision.risk_level),
                    decision.created_at,
                ),
            )
            conn.commit()

    def list_recent_decisions(self, research_id: str, limit: int = 3) -> list[Decision]:
        with self.store.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM decisions
                WHERE research_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (research_id, limit),
            ).fetchall()
        return [
            Decision(
                id=row["id"],
                research_id=row["research_id"],
                selected_action=row["selected_action"],
                rationale=row["rationale"],
                alternatives=json.loads(row["alternatives_json"]),
                risk_level=RiskLevel(row["risk_level"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def log_retrieval(
        self,
        research_id: str,
        query_type: str,
        query_payload: dict,
        selected_items: dict,
        discarded_items: list,
    ) -> None:
        from catalyst.models.common import make_id, utc_now

        with self.store.connect() as conn:
            conn.execute(
                """
                INSERT INTO retrieval_logs
                (id, research_id, query_type, query_payload_json, selected_items_json, discarded_items_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    make_id("retrieval"),
                    research_id,
                    query_type,
                    json.dumps(query_payload),
                    json.dumps(selected_items),
                    json.dumps(discarded_items),
                    utc_now(),
                ),
            )
            conn.commit()

    @staticmethod
    def snapshot_payload(state: ResearchState, goal: ResearchGoal) -> dict:
        return {
            "goal": asdict(goal),
            "state": asdict(state),
        }
