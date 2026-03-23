---
name: result-compare
description: Use this skill when the task requires comparing recent experiment runs, extracting patterns, and summarizing which result should influence the next research step.
category: analysis
recommended_for:
  - compare_recent_runs
  - summarize_results
tools:
  - read
risk_level: low
---

# Result Compare

Use this skill when the current task is to compare recent runs, identify which change mattered, or summarize the strongest pattern before the next action.

## Workflow

1. Gather the smallest set of runs needed for comparison.
2. Compare key metrics, failure status, and notable configuration differences.
3. Highlight the strongest pattern that can influence the next step.
4. Avoid over-claiming if there are too few runs to support a conclusion.

## Output

Return a concise comparison that includes:

1. Which runs were compared
2. Which run looks strongest and why
3. What signal is still uncertain
4. What next action the main agent should consider

## References

- For comparison heuristics, read [references/comparison-heuristics.md](references/comparison-heuristics.md).
