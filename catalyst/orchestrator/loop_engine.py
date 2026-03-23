from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from catalyst.agents.codex_cli import CodexCLIAdapter
from catalyst.models.enums import ResearchStatus
from catalyst.models.research import ResearchGoal, ResearchState
from catalyst.orchestrator.checkpoint_manager import CheckpointManager
from catalyst.orchestrator.context_builder import ContextBuilder
from catalyst.orchestrator.delegation_planner import DelegationPlanner
from catalyst.orchestrator.next_action_selector import NextActionSelector
from catalyst.orchestrator.prompt_registry import PromptRegistry
from catalyst.orchestrator.state_manager import StateManager
from catalyst.orchestrator.subagent_executor import SubagentExecutor
from catalyst.storage.memory_backend import SQLiteMemoryBackend


class LoopEngine:
    def __init__(
        self,
        workspace: Path,
        memory: SQLiteMemoryBackend,
        state_manager: StateManager,
        checkpoints: CheckpointManager,
        prompt_registry: PromptRegistry,
    ) -> None:
        self.workspace = workspace
        self.memory = memory
        self.state_manager = state_manager
        self.checkpoints = checkpoints
        self.context_builder = ContextBuilder(memory)
        self.selector = NextActionSelector(memory)
        self.delegation_planner = DelegationPlanner(memory, prompt_registry)
        self.subagent_executor = SubagentExecutor(
            workspace=workspace,
            prompt_registry=prompt_registry,
            agent_adapter=CodexCLIAdapter(workspace / ".catalyst" / "subagents" / "outputs"),
        )

    def run_once(self, goal: ResearchGoal, state: ResearchState) -> dict:
        context = self.context_builder.build(goal, state)
        next_action = self.selector.select(goal, state, context)
        delegation = self.delegation_planner.plan(goal, state)
        subagent_results: list[dict] = []
        if delegation.should_delegate:
            for task in delegation.tasks:
                subagent_results.append(self.subagent_executor.execute(task))
        state.status = ResearchStatus.RUNNING
        if subagent_results:
            task_titles = ", ".join(item["task"]["title"] for item in subagent_results)
            state.summary = f"Executed delegation tasks: {task_titles}"
        else:
            state.summary = f"Planned next action: {next_action.selected_action.action_type}"
        self.state_manager.save_state(state, goal)
        checkpoint = self.checkpoints.create_checkpoint(state, goal, "Loop iteration completed.")
        return {
            "next_action": asdict(next_action),
            "delegation": asdict(delegation),
            "subagent_results": subagent_results,
            "checkpoint": asdict(checkpoint),
        }

    def run_auto(self, goal: ResearchGoal, state: ResearchState, iterations: int) -> dict:
        results = []
        for _ in range(iterations):
            if state.status == ResearchStatus.PAUSED:
                break
            results.append(self.run_once(goal, state))
        return {"iterations": len(results), "results": results}
