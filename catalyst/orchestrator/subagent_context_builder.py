from __future__ import annotations

from dataclasses import asdict

from catalyst.models.common import to_jsonable
from catalyst.models.delegation import PromptTemplateMetadata, SubagentTask
from catalyst.models.research import ResearchGoal, ResearchState
from catalyst.storage.memory_backend import SQLiteMemoryBackend


class SubagentContextBuilder:
    def __init__(self, memory_backend: SQLiteMemoryBackend) -> None:
        self.memory_backend = memory_backend

    def build(
        self,
        goal: ResearchGoal,
        state: ResearchState,
        template: PromptTemplateMetadata,
        objective: str,
    ) -> dict:
        recent_runs = [to_jsonable(asdict(item)) for item in self.memory_backend.list_recent_experiment_runs(state.research_id, limit=3)]
        recent_decisions = [to_jsonable(asdict(item)) for item in self.memory_backend.list_recent_decisions(state.research_id, limit=3)]
        context = {
            "goal": to_jsonable(asdict(goal)),
            "state": to_jsonable(asdict(state)),
            "template": {
                "name": template.name,
                "description": template.description,
                "role": template.role,
                "recommended_for": template.recommended_for,
                "tools": template.tools,
                "risk_level": template.risk_level.value,
            },
            "objective": objective,
            "recent_runs": recent_runs,
            "recent_decisions": recent_decisions,
        }
        self.memory_backend.log_retrieval(
            research_id=state.research_id,
            query_type="build_subagent_context",
            query_payload={"template_name": template.name, "objective": objective},
            selected_items={
                "recent_runs": [item["id"] for item in recent_runs],
                "recent_decisions": [item["id"] for item in recent_decisions],
            },
            discarded_items=[],
        )
        return context

    def build_task(
        self,
        goal: ResearchGoal,
        state: ResearchState,
        template: PromptTemplateMetadata,
        title: str,
        objective: str,
        expected_output: list[str],
    ) -> SubagentTask:
        return SubagentTask(
            title=title,
            objective=objective,
            template_name=template.name,
            role=template.role,
            context=self.build(goal, state, template, objective),
            expected_output=expected_output,
            risk_level=template.risk_level,
        )
