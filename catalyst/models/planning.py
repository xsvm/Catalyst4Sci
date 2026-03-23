from __future__ import annotations

from dataclasses import dataclass, field

from catalyst.models.common import make_id, utc_now
from catalyst.models.enums import RiskLevel


@dataclass(slots=True)
class NextAction:
    action_type: str
    title: str
    description: str
    payload: dict = field(default_factory=dict)


@dataclass(slots=True)
class NextActionDecision:
    selected_action: NextAction
    alternatives: list[NextAction]
    rationale: str
    evidence_refs: list[str] = field(default_factory=list)
    expected_gain: float = 0.0
    estimated_cost: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    id: str = field(default_factory=lambda: make_id("decision"))
    created_at: str = field(default_factory=utc_now)
