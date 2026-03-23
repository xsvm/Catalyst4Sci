from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from catalyst.agents.base import AgentAdapter, AgentInvocation
from catalyst.models.common import make_id, utc_now
from catalyst.models.delegation import SubagentTask
from catalyst.orchestrator.prompt_registry import PromptRegistry


class SubagentExecutor:
    def __init__(self, workspace: Path, prompt_registry: PromptRegistry, agent_adapter: AgentAdapter) -> None:
        self.workspace = workspace
        self.prompt_registry = prompt_registry
        self.agent_adapter = agent_adapter
        self.root = self.workspace / ".catalyst" / "subagents"

    def execute(self, task: SubagentTask) -> dict:
        task_dir = self.root / task.id
        task_dir.mkdir(parents=True, exist_ok=True)
        prompt_body = self.prompt_registry.render(task.template_name, {})
        compiled_prompt = self._compose_prompt(task, prompt_body)
        prompt_file = task_dir / "prompt.md"
        prompt_file.write_text(compiled_prompt, encoding="utf-8")
        invocation = AgentInvocation(
            command=compiled_prompt,
            workspace=str(self.workspace),
            timeout_seconds=600,
        )
        result = self.agent_adapter.run(invocation)
        payload = {
            "task": asdict(task),
            "result": asdict(result),
            "executed_at": utc_now(),
        }
        result_file = task_dir / "result.json"
        result_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def _compose_prompt(self, task: SubagentTask, prompt_body: str) -> str:
        context_json = json.dumps(task.context, ensure_ascii=False, indent=2)
        expected = "\n".join(f"- {item}" for item in task.expected_output) if task.expected_output else "- concise result"
        return f"""# Subagent Task

## Role Template
{prompt_body}

## Objective
{task.objective}

## Context
```json
{context_json}
```

## Expected Output
{expected}

Return a concise structured response suitable for the main agent to read and merge into research memory.
"""
