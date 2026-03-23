# Execution Guidelines

## Run Discipline

1. Prefer one clear experiment command per run.
2. Always record timeout and exit code.
3. Do not silently rerun the same command without recording why.

## Failure Handling

1. Treat timeout as a separate failure class from non-zero exit.
2. For repeated failures, hand control back to the main agent with a diagnosis instead of looping blindly.
3. If logs are missing or incomplete, report that explicitly.
