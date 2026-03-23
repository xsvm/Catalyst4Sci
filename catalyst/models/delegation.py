from __future__ import annotations

from dataclasses import dataclass, field

from catalyst.models.common import make_id, utc_now
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


@dataclass(slots=True)
class SubagentTask:
    title: str
    objective: str
    template_name: str
    role: str
    context: dict
    expected_output: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    id: str = field(default_factory=lambda: make_id("subtask"))


@dataclass(slots=True)
class DelegationDecision:
    should_delegate: bool
    delegation_mode: str
    rationale: str
    tasks: list[SubagentTask] = field(default_factory=list)
    id: str = field(default_factory=lambda: make_id("delegate"))
    created_at: str = field(default_factory=utc_now)
