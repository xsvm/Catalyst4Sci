from enum import StrEnum


class ResearchPhase(StrEnum):
    PROBLEM_FRAMING = "problem_framing"
    LITERATURE_REVIEW = "literature_review"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    EXPERIMENT_DESIGN = "experiment_design"
    EXECUTION = "execution"
    ANALYSIS = "analysis"
    DECISION = "decision"
    REPORTING = "reporting"


class ResearchStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    BLOCKED = "blocked"
    WAITING_HUMAN = "waiting_human"
    FINISHED = "finished"
    FAILED = "failed"
    PAUSED = "paused"


class HypothesisStatus(StrEnum):
    ACTIVE = "active"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    STALLED = "stalled"


class EvidenceType(StrEnum):
    PAPER = "paper"
    EXPERIMENT = "experiment"
    OBSERVATION = "observation"
    DERIVED = "derived"


class ExperimentRunStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CRASH = "crash"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
