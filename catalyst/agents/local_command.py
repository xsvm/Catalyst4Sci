from __future__ import annotations

import os
import subprocess

from catalyst.agents.base import AgentAdapter, AgentInvocation, AgentInvocationResult
from catalyst.models.common import utc_now


class LocalCommandAgentAdapter(AgentAdapter):
    def name(self) -> str:
        return "local_command"

    def run(self, invocation: AgentInvocation) -> AgentInvocationResult:
        started_at = utc_now()
        env = os.environ.copy()
        env.update(invocation.env)
        try:
            completed = subprocess.run(
                invocation.command,
                cwd=invocation.workspace,
                env=env,
                shell=True,
                capture_output=True,
                text=True,
                timeout=invocation.timeout_seconds,
            )
            return AgentInvocationResult(
                invocation_id=invocation.id,
                adapter_name=self.name(),
                exit_code=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                timed_out=False,
                started_at=started_at,
                finished_at=utc_now(),
            )
        except subprocess.TimeoutExpired as exc:
            return AgentInvocationResult(
                invocation_id=invocation.id,
                adapter_name=self.name(),
                exit_code=None,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                timed_out=True,
                started_at=started_at,
                finished_at=utc_now(),
            )
