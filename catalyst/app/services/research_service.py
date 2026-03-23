from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from catalyst.agents.local_command import LocalCommandAgentAdapter
from catalyst.experiments.runner import ExperimentRunner
from catalyst.models.enums import ResearchStatus
from catalyst.orchestrator.context_builder import ContextBuilder
from catalyst.orchestrator.delegation_planner import DelegationPlanner
from catalyst.orchestrator.loop_engine import LoopEngine
from catalyst.orchestrator.next_action_selector import NextActionSelector
from catalyst.orchestrator.prompt_registry import PromptRegistry
from catalyst.models.research import ExperimentSpec, ResearchGoal
from catalyst.prompts.loader import render_research_agent_system_prompt
from catalyst.skills.registry import SkillRegistry
from catalyst.orchestrator.checkpoint_manager import CheckpointManager
from catalyst.orchestrator.state_manager import StateManager
from catalyst.storage.file_store import FileArtifactStore
from catalyst.storage.memory_backend import SQLiteMemoryBackend
from catalyst.storage.sqlite import SQLiteStore
from catalyst.app.services.workspace_service import WorkspaceService


class ResearchService:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.workspace_service = WorkspaceService(self.workspace)
        self.workspace_manifest = self.workspace_service.ensure_manifest()
        self.file_store = FileArtifactStore(self.workspace)
        self.file_store.initialize()
        self.sqlite_store = SQLiteStore(self.file_store.db_path)
        self.sqlite_store.initialize()
        self.memory = SQLiteMemoryBackend(self.sqlite_store)
        self.state_manager = StateManager(self.file_store, self.memory)
        self.checkpoints = CheckpointManager(self.file_store, self.memory)
        self.experiment_runner = ExperimentRunner(self.file_store, LocalCommandAgentAdapter())
        self.context_builder = ContextBuilder(self.memory)
        self.next_action_selector = NextActionSelector(self.memory)
        self.prompt_registry = PromptRegistry()
        self.delegation_planner = DelegationPlanner(self.memory, self.prompt_registry)
        self.skill_registry = SkillRegistry(external_dir=self.workspace / ".catalyst" / "skills")
        self.loop_engine = LoopEngine(
            workspace=self.workspace,
            memory=self.memory,
            state_manager=self.state_manager,
            checkpoints=self.checkpoints,
            prompt_registry=self.prompt_registry,
        )

    def start_research(self, title: str, description: str, success_metrics: list[str]) -> dict:
        goal = ResearchGoal(
            title=title,
            description=description,
            workspace=str(self.workspace),
            success_metrics=success_metrics,
        )
        state = self.state_manager.initialize_research(goal)
        checkpoint = self.checkpoints.create_checkpoint(state, goal, "Initial checkpoint.")
        self.state_manager.save_state(state, goal)
        return {"goal": asdict(goal), "state": asdict(state), "checkpoint": asdict(checkpoint)}

    def load_current(self) -> tuple[ResearchGoal, object]:
        state_payload = self.file_store.read_json(self.file_store.state_file)
        goal = self.memory.load_goal(state_payload["goal"]["id"])
        state = self.memory.load_state(state_payload["state"]["research_id"])
        if goal is None or state is None:
            raise FileNotFoundError("Current research state is incomplete.")
        return goal, state

    def status(self) -> dict:
        goal, state = self.load_current()
        checkpoint = None
        if state.latest_checkpoint_id:
            checkpoint = self.memory.load_latest_checkpoint(state.research_id)
        return {
            "goal": asdict(goal),
            "state": asdict(state),
            "checkpoint": asdict(checkpoint) if checkpoint else None,
        }

    def pause(self) -> dict:
        goal, state = self.load_current()
        self.state_manager.set_status(state, ResearchStatus.PAUSED)
        self.state_manager.save_state(state, goal)
        checkpoint = self.checkpoints.create_checkpoint(state, goal, "Paused by user.")
        return {"state": asdict(state), "checkpoint": asdict(checkpoint)}

    def resume(self) -> dict:
        goal, state = self.load_current()
        self.state_manager.set_status(state, ResearchStatus.RUNNING)
        self.state_manager.save_state(state, goal)
        checkpoint = self.checkpoints.create_checkpoint(state, goal, "Resumed by user.")
        return {"state": asdict(state), "checkpoint": asdict(checkpoint)}

    def report(self) -> Path:
        goal, state = self.load_current()
        checkpoint = self.memory.load_latest_checkpoint(state.research_id)
        lines = [
            "# Catalyst4Sci Research Report",
            "",
            f"- Goal: {goal.title}",
            f"- Description: {goal.description}",
            f"- Workspace: {goal.workspace}",
            f"- Phase: {state.phase.value}",
            f"- Status: {state.status.value}",
            f"- Updated At: {state.updated_at}",
        ]
        if goal.success_metrics:
            lines.append(f"- Success Metrics: {', '.join(goal.success_metrics)}")
        if checkpoint:
            lines.append(f"- Latest Checkpoint: {checkpoint.id}")
            lines.append(f"- Checkpoint Summary: {checkpoint.summary}")
        report_path = self.file_store.reports_dir / "latest-report.md"
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return report_path

    def run_experiment(
        self,
        title: str,
        objective: str,
        command: str,
        timeout_seconds: int,
        expected_metrics: list[str],
    ) -> dict:
        goal, state = self.load_current()
        spec = ExperimentSpec(
            research_id=state.research_id,
            title=title,
            objective=objective,
            command=command,
            workspace=str(self.workspace),
            timeout_seconds=timeout_seconds,
            expected_metrics=expected_metrics,
        )
        self.memory.save_experiment_spec(spec)
        run = self.experiment_runner.run(spec)
        self.memory.save_experiment_run(run)
        state.summary = f"Last experiment {run.id} finished with status {run.status.value}."
        self.state_manager.save_state(state, goal)
        checkpoint = self.checkpoints.create_checkpoint(state, goal, f"Experiment {run.id} completed.")
        return {"spec": asdict(spec), "run": asdict(run), "checkpoint": asdict(checkpoint)}

    def suggest_next_action(self) -> dict:
        goal, state = self.load_current()
        context = self.context_builder.build(goal, state)
        decision = self.next_action_selector.select(goal, state, context)
        return {"context": context, "decision": asdict(decision)}

    def render_system_prompt(self) -> dict:
        goal, state = self.load_current()
        context = self.context_builder.build(goal, state)
        decision = self.next_action_selector.select(goal, state, context, persist=False)
        prompt = render_research_agent_system_prompt(
            goal,
            state,
            context,
            decision,
            self.skill_registry.catalog_lines(),
        )
        return {
            "prompt": prompt,
            "decision": asdict(decision),
            "context": context,
        }

    def list_prompt_templates(self) -> dict:
        templates = [asdict(item) for item in self.prompt_registry.list_templates()]
        return {"templates": templates}

    def plan_delegation(self) -> dict:
        goal, state = self.load_current()
        decision = self.delegation_planner.plan(goal, state)
        return {"delegation": asdict(decision)}

    def list_skills(self) -> dict:
        skills = [asdict(item) for item in self.skill_registry.list_skills()]
        return {"skills": skills}

    def workspace_status(self) -> dict:
        return self.workspace_service.status()

    def loop_once(self) -> dict:
        goal, state = self.load_current()
        return self.loop_engine.run_once(goal, state)

    def auto_run(self, iterations: int) -> dict:
        goal, state = self.load_current()
        return self.loop_engine.run_auto(goal, state, iterations)
