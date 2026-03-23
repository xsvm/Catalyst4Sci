from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class PluginMetadata:
    name: str
    description: str
    configured: bool = False
    capabilities: list[str] = field(default_factory=list)
    source: str = "builtin"
