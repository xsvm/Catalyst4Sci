from __future__ import annotations

from dataclasses import asdict

from catalyst.models.research import Checkpoint, ResearchGoal, ResearchState
from catalyst.storage.file_store import FileArtifactStore
from catalyst.storage.memory_backend import SQLiteMemoryBackend


class CheckpointManager:
    def __init__(self, file_store: FileArtifactStore, memory_backend: SQLiteMemoryBackend) -> None:
        self.file_store = file_store
        self.memory_backend = memory_backend

    def create_checkpoint(self, state: ResearchState, goal: ResearchGoal, summary: str) -> Checkpoint:
        checkpoint = Checkpoint(
            research_id=state.research_id,
            state_path=str(self.file_store.checkpoint_file("pending")),
            summary=summary,
        )
        checkpoint_path = self.file_store.checkpoint_file(checkpoint.id)
        checkpoint.state_path = str(checkpoint_path)
        payload = {
            "checkpoint": asdict(checkpoint),
            "goal": asdict(goal),
            "state": asdict(state),
        }
        self.file_store.write_json(checkpoint_path, payload)
        self.memory_backend.save_checkpoint(checkpoint)
        state.latest_checkpoint_id = checkpoint.id
        self.memory_backend.save_state(state)
        return checkpoint

    def load_latest_checkpoint(self, research_id: str) -> Checkpoint | None:
        return self.memory_backend.load_latest_checkpoint(research_id)
