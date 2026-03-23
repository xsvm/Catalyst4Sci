from __future__ import annotations

import argparse
import json
from pathlib import Path

from catalyst.app.services.research_service import ResearchService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="catalyst", description="Catalyst4Sci CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    research = subparsers.add_parser("research", help="Research task commands")
    research_subparsers = research.add_subparsers(dest="research_command", required=True)

    workspace_parser = subparsers.add_parser("workspace", help="Workspace commands")
    workspace_subparsers = workspace_parser.add_subparsers(dest="workspace_command", required=True)
    workspace_status = workspace_subparsers.add_parser("status", help="Show workspace manifest status")
    workspace_status.add_argument("--workspace", default=".", help="Workspace path")

    start = research_subparsers.add_parser("start", help="Start a new research task")
    start.add_argument("--goal", required=True, help="Research goal title")
    start.add_argument("--description", default="", help="Research goal description")
    start.add_argument("--workspace", default=".", help="Workspace path")
    start.add_argument("--metric", action="append", default=[], help="Success metric; repeatable")

    run_experiment = research_subparsers.add_parser("run-experiment", help="Run a local experiment command")
    run_experiment.add_argument("--workspace", default=".", help="Workspace path")
    run_experiment.add_argument("--title", required=True, help="Experiment title")
    run_experiment.add_argument("--objective", default="", help="Experiment objective")
    run_experiment.add_argument("--shell-command", required=True, dest="shell_command", help="Shell command to execute")
    run_experiment.add_argument("--timeout", type=int, default=300, help="Timeout seconds")
    run_experiment.add_argument("--metric", action="append", default=[], help="Expected metric; repeatable")

    auto_run = research_subparsers.add_parser("auto-run", help="Run multiple autonomous loop iterations")
    auto_run.add_argument("--workspace", default=".", help="Workspace path")
    auto_run.add_argument("--iterations", type=int, default=1, help="Number of loop iterations")

    for name, help_text in (
        ("status", "Show current research status"),
        ("pause", "Pause current research task"),
        ("resume", "Resume current research task"),
        ("report", "Generate a simple report"),
        ("next-action", "Suggest the next action using rule-based selection"),
        ("prompt", "Render the current research system prompt"),
        ("prompts", "List available prompt templates"),
        ("skills", "List available skills without loading full skill bodies"),
        ("plan-delegation", "Plan subagent delegation for the current state"),
        ("loop-once", "Run one autonomous research loop iteration"),
    ):
        sub = research_subparsers.add_parser(name, help=help_text)
        sub.add_argument("--workspace", default=".", help="Workspace path")

    return parser


def print_json(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    workspace = Path(args.workspace).resolve()
    service = ResearchService(workspace)

    if args.command == "workspace" and args.workspace_command == "status":
        print_json(service.workspace_status())
        return 0

    if args.command == "research" and args.research_command == "start":
        result = service.start_research(
            title=args.goal,
            description=args.description or args.goal,
            success_metrics=args.metric,
        )
        print_json(result)
        return 0

    if args.command == "research" and args.research_command == "status":
        print_json(service.status())
        return 0

    if args.command == "research" and args.research_command == "pause":
        print_json(service.pause())
        return 0

    if args.command == "research" and args.research_command == "resume":
        print_json(service.resume())
        return 0

    if args.command == "research" and args.research_command == "report":
        report_path = service.report()
        print_json({"report_path": str(report_path)})
        return 0

    if args.command == "research" and args.research_command == "next-action":
        print_json(service.suggest_next_action())
        return 0

    if args.command == "research" and args.research_command == "prompt":
        print_json(service.render_system_prompt())
        return 0

    if args.command == "research" and args.research_command == "prompts":
        print_json(service.list_prompt_templates())
        return 0

    if args.command == "research" and args.research_command == "skills":
        print_json(service.list_skills())
        return 0

    if args.command == "research" and args.research_command == "plan-delegation":
        print_json(service.plan_delegation())
        return 0

    if args.command == "research" and args.research_command == "loop-once":
        print_json(service.loop_once())
        return 0

    if args.command == "research" and args.research_command == "auto-run":
        print_json(service.auto_run(args.iterations))
        return 0

    if args.command == "research" and args.research_command == "run-experiment":
        result = service.run_experiment(
            title=args.title,
            objective=args.objective or args.title,
            command=args.shell_command,
            timeout_seconds=args.timeout,
            expected_metrics=args.metric,
        )
        print_json(result)
        return 0

    parser.error("Unsupported command.")
    return 2
