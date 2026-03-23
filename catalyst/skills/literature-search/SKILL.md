---
name: literature-search
description: Use this skill when the task requires searching for papers, collecting candidate references, extracting evidence, and organizing literature findings for the research loop.
category: literature
recommended_for:
  - literature_review
  - missing_evidence
tools:
  - web
  - read
risk_level: low
---

# Literature Search

Use this skill when the current task is to gather external evidence, identify relevant papers, or fill a missing-evidence gap before experiment planning.

## Workflow

1. Start from a concrete research question or missing evidence gap.
2. Build a small keyword set and search narrowly before broadening.
3. Prefer high-signal sources and record why each source matters.
4. Extract concise evidence summaries instead of copying full paper text.
5. Return only the most relevant findings to the main agent.

## Output

Return a structured literature summary that includes:

1. Search focus
2. Top candidate sources
3. Key evidence snippets in paraphrased form
4. Open questions that remain unresolved

## References

- For search strategy and evidence recording, read [references/search-strategy.md](references/search-strategy.md).
