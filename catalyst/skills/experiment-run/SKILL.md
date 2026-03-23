---
name: experiment-run
description: Use this skill when the task requires executing a local experiment command, capturing logs, recording structured results, and updating Catalyst4Sci experiment state.
category: experiment
recommended_for:
  - run_experiment
  - baseline_experiment
tools:
  - bash
  - read
risk_level: medium
---

# Experiment Run

Use this skill when the current task is to run a baseline experiment, execute a follow-up experiment, or reproduce a prior run.

## Workflow

1. Confirm the experiment objective, command, workspace, timeout, and expected metrics.
2. Run the experiment through the project execution path instead of inventing an ad hoc shell workflow.
3. Capture stdout, stderr, exit code, timeout status, and result artifact paths.
4. Update the structured experiment record and checkpoint after execution.
5. If the run fails, classify whether the failure is environmental, command-related, or idea-related before retrying.

## Output

Return a concise execution summary that includes:

1. What command ran
2. Whether it succeeded, failed, or timed out
3. Where logs and result artifacts were written
4. Which metric or signal should influence the next action

## References

- For execution discipline and failure handling, read [references/execution-guidelines.md](references/execution-guidelines.md).
