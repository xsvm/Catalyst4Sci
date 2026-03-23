from __future__ import annotations

from catalyst.models.plugin import PluginMetadata
from catalyst.plugins.ai4scholar import Ai4ScholarPlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins = {
            "ai4scholar": Ai4ScholarPlugin(),
        }

    def list_plugins(self) -> list[PluginMetadata]:
        return [plugin.metadata() for plugin in self._plugins.values()]

    def get(self, name: str):
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise FileNotFoundError(f"Plugin '{name}' is not registered.") from exc
