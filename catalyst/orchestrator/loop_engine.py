from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from catalyst.agents.codex_cli import CodexCLIAdapter
from catalyst.agents.base import AgentInvocation
from catalyst.models.enums import ResearchStatus
from catalyst.models.research import ResearchGoal, ResearchState
from catalyst.orchestrator.checkpoint_manager import CheckpointManager
from catalyst.orchestrator.context_builder import ContextBuilder
from catalyst.orchestrator.next_action_selector import NextActionSelector
from catalyst.orchestrator.prompt_registry import PromptRegistry
from catalyst.orchestrator.state_manager import StateManager
from catalyst.prompts.loader import render_research_agent_system_prompt
from catalyst.skills.registry import SkillRegistry
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
        self.prompt_registry = prompt_registry
        self.context_builder = ContextBuilder(memory)
        self.selector = NextActionSelector(memory)
        self.skill_registry = SkillRegistry(external_dir=workspace / ".catalyst" / "skills")
        self.main_agent = CodexCLIAdapter(workspace / ".catalyst" / "main-agent" / "outputs")

    def run_once(self, goal: ResearchGoal, state: ResearchState) -> dict:
        context = self.context_builder.build(goal, state)
        next_action = self.selector.select(goal, state, context)
        prompt = render_research_agent_system_prompt(
            goal=goal,
            state=state,
            context=context,
            decision=next_action,
            skill_catalog=self.skill_registry.catalog_lines(),
            prompt_catalog=self._prompt_catalog_lines(),
        )
        agent_result = self.main_agent.run(
            AgentInvocation(
                command=prompt,
                workspace=str(self.workspace),
                timeout_seconds=300,
            )
        )
        state.status = ResearchStatus.RUNNING
        if agent_result.stdout.strip():
            state.summary = self._summarize_agent_output(agent_result.stdout)
        else:
            state.summary = f"Planned next action: {next_action.selected_action.action_type}"
        self.state_manager.save_state(state, goal)
        checkpoint = self.checkpoints.create_checkpoint(state, goal, "Loop iteration completed.")
        return {
            "next_action": asdict(next_action),
            "main_agent_result": asdict(agent_result),
            "checkpoint": asdict(checkpoint),
        }

    def run_auto(self, goal: ResearchGoal, state: ResearchState, iterations: int) -> dict:
        results = []
        for _ in range(iterations):
            if state.status == ResearchStatus.PAUSED:
                break
            results.append(self.run_once(goal, state))
        return {"iterations": len(results), "results": results}

    def _prompt_catalog_lines(self) -> list[str]:
        return [
            f"- {template.name}: {template.description} | role={template.role} | recommended_for={', '.join(template.recommended_for) or 'none'}"
            for template in self.prompt_registry.list_templates()
            if template.role == "subagent"
        ]

    @staticmethod
    def _summarize_agent_output(output: str) -> str:
        first_line = next((line.strip() for line in output.splitlines() if line.strip()), "")
        if not first_line:
            return "Codex main agent completed a loop iteration."
        return f"Codex main agent: {first_line[:140]}"
