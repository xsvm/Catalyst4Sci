from __future__ import annotations

import os
import subprocess
from pathlib import Path

from catalyst.agents.base import AgentAdapter, AgentInvocation, AgentInvocationResult
from catalyst.models.common import utc_now


class CodexCLIAdapter(AgentAdapter):
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def name(self) -> str:
        return "codex_cli"

    def run(self, invocation: AgentInvocation) -> AgentInvocationResult:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / f"{invocation.id}.txt"
        started_at = utc_now()
        env = os.environ.copy()
        env.update(invocation.env)
        command = self._build_command(invocation, output_file)
        try:
            completed = subprocess.run(
                command,
                cwd=invocation.workspace,
                env=env,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                input=invocation.command,
                timeout=invocation.timeout_seconds,
            )
            stdout = completed.stdout
            if output_file.exists():
                stdout = output_file.read_text(encoding="utf-8")
            return AgentInvocationResult(
                invocation_id=invocation.id,
                adapter_name=self.name(),
                exit_code=completed.returncode,
                stdout=stdout,
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

    @staticmethod
    def _build_command(invocation: AgentInvocation, output_file: Path) -> str:
        parts = [
            "codex exec",
            f'-C "{invocation.workspace}"',
            "--skip-git-repo-check",
            "--full-auto",
            f'--output-last-message "{output_file}"',
            "-",
        ]
        return " ".join(parts)
