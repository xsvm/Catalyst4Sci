from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from catalyst.models.common import make_id, utc_now


@dataclass(slots=True)
class AgentInvocation:
    command: str
    workspace: str
    timeout_seconds: int = 300
    env: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: make_id("invoke"))
    created_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class AgentInvocationResult:
    invocation_id: str
    adapter_name: str
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    started_at: str
    finished_at: str


class AgentAdapter(Protocol):
    def name(self) -> str: ...

    def run(self, invocation: AgentInvocation) -> AgentInvocationResult: ...
