from __future__ import annotations

from dataclasses import dataclass, field

from catalyst.models.common import make_id, utc_now
from catalyst.models.enums import (
    EvidenceType,
    ExperimentRunStatus,
    HypothesisStatus,
    ResearchPhase,
    ResearchStatus,
    RiskLevel,
)


@dataclass(slots=True)
class ResearchGoal:
    title: str
    description: str
    workspace: str
    success_metrics: list[str] = field(default_factory=list)
    constraints: list[dict] = field(default_factory=list)
    id: str = field(default_factory=lambda: make_id("goal"))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class ResearchState:
    research_id: str
    goal_id: str
    phase: ResearchPhase = ResearchPhase.PROBLEM_FRAMING
    status: ResearchStatus = ResearchStatus.IDLE
    current_plan_id: str | None = None
    latest_checkpoint_id: str | None = None
    budget_snapshot: dict = field(default_factory=dict)
    summary: str = ""
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class Hypothesis:
    research_id: str
    statement: str
    rationale: str
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    confidence: float = 0.5
    id: str = field(default_factory=lambda: make_id("hyp"))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class Evidence:
    research_id: str
    title: str
    summary: str
    source: str
    source_ref: str
    type: EvidenceType = EvidenceType.OBSERVATION
    relevance_score: float = 0.0
    id: str = field(default_factory=lambda: make_id("evidence"))
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class ExperimentSpec:
    research_id: str
    title: str
    objective: str
    command: str
    workspace: str
    timeout_seconds: int
    expected_metrics: list[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: make_id("spec"))
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class ExperimentRun:
    spec_id: str
    research_id: str
    metrics: dict = field(default_factory=dict)
    stdout_path: str = ""
    stderr_path: str = ""
    result_path: str = ""
    status: ExperimentRunStatus = ExperimentRunStatus.SUCCESS
    id: str = field(default_factory=lambda: make_id("run"))
    started_at: str = field(default_factory=utc_now)
    finished_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class Decision:
    research_id: str
    selected_action: str
    rationale: str
    alternatives: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    id: str = field(default_factory=lambda: make_id("decision"))
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class OpenQuestion:
    research_id: str
    question: str
    status: str = "open"
    id: str = field(default_factory=lambda: make_id("question"))
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class Checkpoint:
    research_id: str
    state_path: str
    summary: str
    id: str = field(default_factory=lambda: make_id("cp"))
    created_at: str = field(default_factory=utc_now)
