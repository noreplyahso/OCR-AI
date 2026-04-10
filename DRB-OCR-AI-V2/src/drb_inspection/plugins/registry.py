from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PluginRegistry:
    plugins: dict[str, object] = field(default_factory=dict)

    def get(self, name: str) -> object:
        try:
            return self.plugins[name]
        except KeyError as exc:
            available = ", ".join(sorted(self.plugins)) or "<empty>"
            raise KeyError(f"Plugin '{name}' is not registered. Available: {available}") from exc

    def register(self, name: str, plugin: object) -> None:
        self.plugins[name] = plugin
