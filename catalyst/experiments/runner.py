from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from catalyst.agents.base import AgentAdapter, AgentInvocation
from catalyst.models.enums import ExperimentRunStatus
from catalyst.models.research import ExperimentRun, ExperimentSpec
from catalyst.storage.file_store import FileArtifactStore


class ExperimentRunner:
    def __init__(self, file_store: FileArtifactStore, agent_adapter: AgentAdapter) -> None:
        self.file_store = file_store
        self.agent_adapter = agent_adapter

    def run(self, spec: ExperimentSpec) -> ExperimentRun:
        run = ExperimentRun(
            spec_id=spec.id,
            research_id=spec.research_id,
            status=ExperimentRunStatus.SUCCESS,
        )
        run_dir = self.file_store.run_dir(run.id)
        stdout_path = run_dir / "stdout.log"
        stderr_path = run_dir / "stderr.log"
        result_path = run_dir / "result.json"

        invocation = AgentInvocation(
            command=spec.command,
            workspace=spec.workspace,
            timeout_seconds=spec.timeout_seconds,
        )
        result = self.agent_adapter.run(invocation)

        run.stdout_path = str(stdout_path)
        run.stderr_path = str(stderr_path)
        run.result_path = str(result_path)
        run.started_at = result.started_at
        run.finished_at = result.finished_at
        run.metrics = {
            "exit_code": -1 if result.exit_code is None else result.exit_code,
            "stdout_chars": len(result.stdout),
            "stderr_chars": len(result.stderr),
        }
        if result.timed_out:
            run.status = ExperimentRunStatus.TIMEOUT
        elif result.exit_code and result.exit_code != 0:
            run.status = ExperimentRunStatus.FAILED

        stdout_path.write_text(result.stdout, encoding="utf-8")
        stderr_path.write_text(result.stderr, encoding="utf-8")
        result_path.write_text(
            json.dumps(
                {
                    "spec": asdict(spec),
                    "run": asdict(run),
                    "agent_result": asdict(result),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return run
