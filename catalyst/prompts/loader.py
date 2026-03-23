from __future__ import annotations

import json
from pathlib import Path

from catalyst.models.planning import NextActionDecision
from catalyst.models.research import ResearchGoal, ResearchState


PROMPTS_DIR = Path(__file__).parent


def render_prompt(template_name: str, variables: dict[str, str]) -> str:
    prompt_file = PROMPTS_DIR / f"{template_name}.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt template '{template_name}' not found at {prompt_file}")
    template = _strip_frontmatter(prompt_file.read_text(encoding="utf-8")).strip()
    return template.format(**variables)


def _strip_frontmatter(content: str) -> str:
    lines = content.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return content
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1 :])
    return content


def render_research_agent_system_prompt(
    goal: ResearchGoal,
    state: ResearchState,
    context: dict,
    decision: NextActionDecision,
    skill_catalog: list[str],
    prompt_catalog: list[str],
) -> str:
    variables = {
        "goal_title": goal.title,
        "goal_description": goal.description,
        "goal_workspace": goal.workspace,
        "success_metrics": ", ".join(goal.success_metrics) if goal.success_metrics else "未定义",
        "research_id": state.research_id,
        "phase": state.phase.value,
        "status": state.status.value,
        "state_summary": state.summary,
        "recent_runs": json.dumps(context["L1"]["recent_runs"], ensure_ascii=False, indent=2),
        "recent_decisions": json.dumps(context["L1"]["recent_decisions"], ensure_ascii=False, indent=2),
        "skill_catalog": "\n".join(skill_catalog) if skill_catalog else "暂无可用技能。",
        "prompt_catalog": "\n".join(prompt_catalog) if prompt_catalog else "暂无可用子代理模板。",
        "selected_action_type": decision.selected_action.action_type,
        "selected_action_title": decision.selected_action.title,
        "selected_action_description": decision.selected_action.description,
        "decision_rationale": decision.rationale,
        "expected_gain": str(decision.expected_gain),
        "estimated_cost": str(decision.estimated_cost),
        "risk_level": decision.risk_level.value,
    }
    return render_prompt("research_agent_system", variables)
