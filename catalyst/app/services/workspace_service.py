from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from catalyst.models.common import utc_now
from catalyst.models.workspace import WorkspaceManifest
from catalyst.storage.file_store import FileArtifactStore


class WorkspaceService:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.file_store = FileArtifactStore(self.workspace)
        self.file_store.initialize()

    def ensure_manifest(self) -> WorkspaceManifest:
        if self.file_store.workspace_file.exists():
            payload = self.file_store.read_json(self.file_store.workspace_file)
            return WorkspaceManifest(**payload)
        manifest = WorkspaceManifest(
            root=str(self.workspace),
            name=self.workspace.name,
            skill_roots=[
                str(self.workspace / "catalyst" / "skills"),
                str(self.workspace / ".catalyst" / "skills"),
            ],
        )
        self.file_store.write_json(self.file_store.workspace_file, asdict(manifest))
        return manifest

    def status(self) -> dict:
        manifest = self.ensure_manifest()
        manifest.updated_at = utc_now()
        self.file_store.write_json(self.file_store.workspace_file, asdict(manifest))
        return {"workspace": asdict(manifest)}
