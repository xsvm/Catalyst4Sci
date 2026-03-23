from __future__ import annotations

from catalyst.models.enums import ExperimentRunStatus, RiskLevel
from catalyst.models.planning import NextAction, NextActionDecision
from catalyst.models.research import Decision, ResearchGoal, ResearchState
from catalyst.storage.memory_backend import SQLiteMemoryBackend


class NextActionSelector:
    def __init__(self, memory_backend: SQLiteMemoryBackend) -> None:
        self.memory_backend = memory_backend

    def select(self, goal: ResearchGoal, state: ResearchState, context: dict, *, persist: bool = True) -> NextActionDecision:
        recent_runs = self.memory_backend.list_recent_experiment_runs(state.research_id, limit=3)

        if not recent_runs:
            selected = NextAction(
                action_type="design_experiment",
                title="baseline_experiment",
                description="No experiment runs exist yet. Design and run a baseline experiment first.",
                payload={"reason": "no_runs"},
            )
            alternatives = [
                NextAction(
                    action_type="refine_goal",
                    title="refine_goal",
                    description="Clarify success metrics before any experiment.",
                    payload={"reason": "goal_clarity"},
                )
            ]
            rationale = "No prior experiments are available, so the highest-value next step is to establish a baseline."
            expected_gain = 0.9
            estimated_cost = 0.4
            risk_level = RiskLevel.LOW
        else:
            latest_run = recent_runs[0]
            if latest_run.status in {ExperimentRunStatus.FAILED, ExperimentRunStatus.TIMEOUT, ExperimentRunStatus.CRASH}:
                selected = NextAction(
                    action_type="analyze_failure",
                    title="analyze_latest_failure",
                    description="Inspect the latest failed run and determine whether the command, environment, or idea should change.",
                    payload={"run_id": latest_run.id},
                )
                alternatives = [
                    NextAction(
                        action_type="rerun_experiment",
                        title="rerun_latest",
                        description="Retry the latest failed run if the failure looks transient.",
                        payload={"run_id": latest_run.id},
                    )
                ]
                rationale = "The latest experiment failed, so the first priority is to understand the failure before more iteration."
                expected_gain = 0.7
                estimated_cost = 0.2
                risk_level = RiskLevel.LOW
            else:
                selected = NextAction(
                    action_type="iterate_experiment",
                    title="propose_followup_experiment",
                    description="Use recent experiment results to propose a follow-up experiment that improves or validates the current direction.",
                    payload={"run_id": latest_run.id, "goal_id": goal.id},
                )
                alternatives = [
                    NextAction(
                        action_type="compare_results",
                        title="compare_recent_runs",
                        description="Compare recent experiment outcomes before scheduling the next run.",
                        payload={"run_ids": [item.id for item in recent_runs]},
                    )
                ]
                rationale = "At least one recent experiment succeeded, so the next step should build on observed results instead of restarting from scratch."
                expected_gain = 0.8
                estimated_cost = 0.5
                risk_level = RiskLevel.MEDIUM

        decision = NextActionDecision(
            selected_action=selected,
            alternatives=alternatives,
            rationale=rationale,
            expected_gain=expected_gain,
            estimated_cost=estimated_cost,
            risk_level=risk_level,
        )
        if persist:
            self.memory_backend.save_decision(
                Decision(
                    id=decision.id,
                    research_id=state.research_id,
                    selected_action=selected.action_type,
                    rationale=decision.rationale,
                    alternatives=[item.action_type for item in alternatives],
                    risk_level=decision.risk_level,
                    created_at=decision.created_at,
                )
            )
        return decision
