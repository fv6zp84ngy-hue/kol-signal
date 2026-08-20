---
name: creator-signal-intelligence
description: Guide a local Creator Signal Intelligence workflow for auditing one or more creator-list CSV/XLSX files, collecting a natural-language Campaign brief, running the kol-signal CLI, explaining audit and shortlist outputs, handling merge-review decisions, and importing outreach feedback. Use when a user asks to compare KOL lists, audit creator data, prioritize outreach candidates, review suspected duplicates, or summarize feedback from a completed KOL outreach round.
---

# Creator Signal Intelligence

Use the existing `kol-signal` CLI as the source of truth. Act as a thin interaction layer: collect inputs, run commands, explain evidence, pause for human decisions, and return local output files.

Do not reproduce or override identity, freshness, conflict, filtering, or scoring rules in this Skill. Those rules belong in application code and configuration.

Read [references/cli-workflow.md](references/cli-workflow.md) before running a command or interpreting its outputs.

## Guardrails

- Keep creator files and run artifacts in the local workspace.
- Do not call web search, external APIs, connectors, Gmail, or Feishu for this workflow.
- Do not inspect or quote raw creator rows unless required to resolve a user-approved mapping question.
- Do not infer missing Campaign criteria. Treat omitted criteria as unset.
- Do not decide an ambiguous field mapping or identity merge for the user.
- Do not calculate, alter, or explain a score using rules not present in generated reports.
- Do not modify input spreadsheets or automatically send outreach.
- Do not add competitor analysis, content analysis, A/B experiments, automatic weight tuning, or SaaS behavior.

## Workflow

### 1. Locate the CLI

Work from the project root containing `pyproject.toml` and `kol_signal/`.

Prefer `kol-signal` when available. Otherwise use the repository-local `.venv/bin/kol-signal`. If neither exists, explain the installation blocker and stop; do not install dependencies without user approval.

### 2. Collect creator files

Accept one or more `.csv` or `.xlsx` files. Reuse attached or workspace files; do not ask the user to copy their rows into chat.

If no file is available, ask the user to upload or identify the files. Confirm the resolved filenames before running the audit.

### 3. Collect the Campaign brief

If the user has not already supplied a usable brief, ask one concise question covering:

- brand or product;
- target market and language;
- preferred creator size;
- activity requirement;
- whether a business contact path is required;
- explicit exclusions, if any.

Preserve the user's meaning in a UTF-8 text file. Do not enrich it with guessed requirements. The CLI, not the Skill, determines which conditions are recognized.

### 4. Preview and confirm Campaign conditions

Run `kol-signal campaign-preview` before the first audit. Show the CLI's recognized, unrecognized, conflicting, and warning fields without reinterpreting them.

If the CLI reports conflicting conditions, ask the user to revise the Brief and preview again. If it reports a blocking unrecognized condition, explain that the condition will not participate in filtering or scoring. Only create a confirmed Campaign config after the user explicitly accepts that limitation.

Do not reproduce Campaign parsing aliases, patterns, or conflict rules in this Skill.

### 5. Preview field mappings

Run the mapping preview before the first audit.

Show the CLI's `adapter_validation_level`. A Native match is a deterministic
schema match, not proof of third-party compatibility. Never translate `Not
Tested` into "supported" or "verified."

If every input uses a native, reused, or unambiguous mapping, continue. If the CLI reports ambiguous columns:

1. Show the source column, suggested target, confidence, examples, and alternatives returned by the CLI.
2. Ask the user to confirm the target or choose `skip`.
3. Pass only the user's decision to the interactive CLI.

Do not choose based on column semantics yourself.

### 6. Run the audit

Run `kol-signal run` with every confirmed input and the Campaign brief. Request JSON output when practical so paths and counts are not inferred from console prose.

On success, read `report.md` and return the generated output files. On failure, report the command stage, exit code, and CLI error without inventing partial results.

### 7. Explain results

Lead with the action outcome:

- raw records versus canonical creators;
- pending merge-review count;
- Priority, Verify, Hold, and Excluded distribution;
- important missing, stale, invalid, or conflicting data;
- where the shortlist and review files are located.

Explain recommendations only with evidence written in `report.md` or the exported workbooks. State that reference scores are Open Alpha hypotheses rather than validated business outcomes.

### 8. Guide merge review

When review items exist, direct the user to `merge_review.xlsx`. Explain the three allowed decisions: `merge`, `keep_separate`, and `unsure`.

Wait for the user to edit or explicitly decide each row. Then run `kol-signal review`, explain what changed, and return the regenerated audit, shortlist, review, feedback template, and report.

### 9. Guide feedback import

After outreach, direct the user to `feedback_template.xlsx`. When the completed file is available, run `kol-signal feedback`.

Report every rate with its numerator and denominator. Preserve `null` when the denominator is zero. Describe the results as small-sample, descriptive evidence; do not claim causality or modify scoring weights.

### 10. Stop at the P0 boundary

Finish after returning local files and the next human action. Do not extend the workflow into outreach drafting, sending, external synchronization, live enrichment, or automatic learning.
