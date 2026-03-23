from __future__ import annotations

from dataclasses import asdict

from catalyst.models.common import to_jsonable
from catalyst.models.research import ResearchGoal, ResearchState
from catalyst.storage.memory_backend import SQLiteMemoryBackend


class ContextBuilder:
    def __init__(self, memory_backend: SQLiteMemoryBackend) -> None:
        self.memory_backend = memory_backend

    def build(self, goal: ResearchGoal, state: ResearchState) -> dict:
        recent_runs = [to_jsonable(asdict(item)) for item in self.memory_backend.list_recent_experiment_runs(state.research_id, limit=3)]
        recent_decisions = [to_jsonable(asdict(item)) for item in self.memory_backend.list_recent_decisions(state.research_id, limit=3)]
        context = {
            "L0": {
                "goal": to_jsonable(asdict(goal)),
                "state": to_jsonable(asdict(state)),
            },
            "L1": {
                "recent_runs": recent_runs,
                "recent_decisions": recent_decisions,
            },
            "L2": {
                "note": "Long-term archive retrieval is not implemented in v1.",
            },
        }
        self.memory_backend.log_retrieval(
            research_id=state.research_id,
            query_type="build_context",
            query_payload={"recent_runs_limit": 3, "recent_decisions_limit": 3},
            selected_items={
                "recent_runs": [item["id"] for item in recent_runs],
                "recent_decisions": [item["id"] for item in recent_decisions],
            },
            discarded_items=[],
        )
        return context
