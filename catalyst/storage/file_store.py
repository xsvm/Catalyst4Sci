from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileArtifactStore:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.root = self.workspace / ".catalyst"
        self.state_dir = self.root / "state"
        self.checkpoints_dir = self.state_dir / "checkpoints"
        self.runs_dir = self.root / "runs"
        self.evidence_dir = self.root / "evidence"
        self.reports_dir = self.root / "reports"
        self.retrieval_dir = self.root / "retrieval"
        self.workspace_file = self.root / "workspace.json"

    def initialize(self) -> None:
        for path in (
            self.root,
            self.state_dir,
            self.checkpoints_dir,
            self.runs_dir,
            self.evidence_dir / "papers",
            self.evidence_dir / "experiments",
            self.evidence_dir / "observations",
            self.reports_dir,
            self.retrieval_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @property
    def db_path(self) -> Path:
        return self.root / "catalyst.db"

    @property
    def state_file(self) -> Path:
        return self.state_dir / "research.json"

    def checkpoint_file(self, checkpoint_id: str) -> Path:
        return self.checkpoints_dir / f"{checkpoint_id}.json"

    def run_dir(self, run_id: str) -> Path:
        path = self.runs_dir / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
