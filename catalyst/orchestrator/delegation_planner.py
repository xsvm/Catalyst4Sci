from __future__ import annotations

from catalyst.models.delegation import DelegationDecision
from catalyst.models.enums import ExperimentRunStatus
from catalyst.models.research import ResearchGoal, ResearchState
from catalyst.orchestrator.prompt_registry import PromptRegistry
from catalyst.orchestrator.subagent_context_builder import SubagentContextBuilder
from catalyst.storage.memory_backend import SQLiteMemoryBackend


class DelegationPlanner:
    def __init__(self, memory_backend: SQLiteMemoryBackend, prompt_registry: PromptRegistry) -> None:
        self.memory_backend = memory_backend
        self.prompt_registry = prompt_registry
        self.context_builder = SubagentContextBuilder(memory_backend)

    def plan(self, goal: ResearchGoal, state: ResearchState) -> DelegationDecision:
        recent_runs = self.memory_backend.list_recent_experiment_runs(state.research_id, limit=1)
        available_templates = {template.name: template for template in self.prompt_registry.list_templates()}

        if not recent_runs:
            template = available_templates.get("experiment_planner")
            if template is None:
                return DelegationDecision(
                    should_delegate=False,
                    delegation_mode="none",
                    rationale="No experiment history exists, but no experiment_planner prompt template is registered yet.",
                )
            task = self.context_builder.build_task(
                goal=goal,
                state=state,
                template=template,
                title="plan_initial_experiment",
                objective="Design the first baseline experiment for the current research goal.",
                expected_output=["experiment proposal", "success metric mapping", "risk notes"],
            )
            return DelegationDecision(
                should_delegate=True,
                delegation_mode="single",
                rationale="There is no experiment history, so the main agent should delegate baseline experiment planning to a specialized subagent.",
                tasks=[task],
            )

        latest_run = recent_runs[0]
        if latest_run.status in {ExperimentRunStatus.FAILED, ExperimentRunStatus.TIMEOUT, ExperimentRunStatus.CRASH}:
            template = available_templates.get("failure_analyzer")
            if template is None:
                return DelegationDecision(
                    should_delegate=False,
                    delegation_mode="none",
                    rationale="A failure was detected, but no failure_analyzer prompt template is registered yet.",
                )
            task = self.context_builder.build_task(
                goal=goal,
                state=state,
                template=template,
                title="analyze_failed_run",
                objective=f"Analyze the latest failed experiment run {latest_run.id} and propose the smallest viable fix.",
                expected_output=["failure diagnosis", "root cause", "repair proposal"],
            )
            return DelegationDecision(
                should_delegate=True,
                delegation_mode="single",
                rationale="The latest experiment failed, so the main agent should delegate targeted failure analysis before planning the next run.",
                tasks=[task],
            )

        planner = available_templates.get("experiment_planner")
        summarizer = available_templates.get("result_summarizer")
        tasks = []
        if planner is not None:
            tasks.append(
                self.context_builder.build_task(
                    goal=goal,
                    state=state,
                    template=planner,
                    title="plan_followup_experiment",
                    objective=f"Use the latest successful run {latest_run.id} to propose a follow-up experiment.",
                    expected_output=["next experiment", "expected benefit", "rollback plan"],
                )
            )
        if summarizer is not None:
            tasks.append(
                self.context_builder.build_task(
                    goal=goal,
                    state=state,
                    template=summarizer,
                    title="summarize_recent_results",
                    objective="Summarize recent experiment outcomes and highlight the most actionable pattern.",
                    expected_output=["result summary", "key pattern", "recommended action"],
                )
            )
        if not tasks:
            return DelegationDecision(
                should_delegate=False,
                delegation_mode="none",
                rationale="Delegation is appropriate, but no matching prompt templates are currently registered.",
            )
        mode = "parallel" if len(tasks) > 1 else "single"
        return DelegationDecision(
            should_delegate=True,
            delegation_mode=mode,
            rationale="Recent successful execution means the main agent should gather both result interpretation and follow-up planning through specialized subagents.",
            tasks=tasks,
        )
