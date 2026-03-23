from __future__ import annotations

from dataclasses import asdict

from catalyst.models.common import make_id, utc_now
from catalyst.models.enums import ResearchPhase, ResearchStatus
from catalyst.models.research import ResearchGoal, ResearchState
from catalyst.storage.file_store import FileArtifactStore
from catalyst.storage.memory_backend import SQLiteMemoryBackend


class StateManager:
    def __init__(self, file_store: FileArtifactStore, memory_backend: SQLiteMemoryBackend) -> None:
        self.file_store = file_store
        self.memory_backend = memory_backend

    def initialize_research(self, goal: ResearchGoal) -> ResearchState:
        state = ResearchState(
            research_id=make_id("research"),
            goal_id=goal.id,
            phase=ResearchPhase.PROBLEM_FRAMING,
            status=ResearchStatus.RUNNING,
            budget_snapshot={},
            summary="Research initialized.",
            updated_at=utc_now(),
        )
        self.memory_backend.save_goal(goal)
        self.memory_backend.save_state(state)
        self.file_store.write_json(self.file_store.state_file, {"goal": asdict(goal), "state": asdict(state)})
        return state

    def save_state(self, state: ResearchState, goal: ResearchGoal | None = None) -> None:
        state.updated_at = utc_now()
        self.memory_backend.save_state(state)
        payload = {"state": asdict(state)}
        if goal is not None:
            payload["goal"] = asdict(goal)
        self.file_store.write_json(self.file_store.state_file, payload)

    def set_status(self, state: ResearchState, status: ResearchStatus) -> ResearchState:
        state.status = status
        state.updated_at = utc_now()
        self.memory_backend.save_state(state)
        return state
