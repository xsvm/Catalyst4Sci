from __future__ import annotations

from dataclasses import dataclass, field

from catalyst.models.common import make_id, utc_now


@dataclass(slots=True)
class WorkspaceManifest:
    root: str
    name: str
    default_research_id: str | None = None
    skill_roots: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: make_id("ws"))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
