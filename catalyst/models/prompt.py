from __future__ import annotations

from dataclasses import dataclass, field

from catalyst.models.enums import RiskLevel


@dataclass(slots=True)
class PromptTemplateMetadata:
    name: str
    description: str
    role: str = "subagent"
    recommended_for: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    path: str = ""
