from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from catalyst.models.plugin import PluginMetadata


@dataclass(slots=True)
class PluginResponse:
    plugin: str
    operation: str
    payload: dict


class Plugin(Protocol):
    def metadata(self) -> PluginMetadata: ...
