# CLI workflow contract

Use this reference for commands, outputs, and error handling. Do not copy business rules from application code into the Skill.

## Project root and executable

Run commands from the repository root.

Resolve the executable in this order:

```text
kol-signal
.venv/bin/kol-signal
```

When diagnosing an installed CLI, use `kol-signal doctor`. It does not read
creator files or disclose absolute paths. Skill installation remains optional.

Quote every user-supplied path. Add one `--input` argument per creator-list file.

## Campaign preview

```bash
kol-signal campaign-preview \
  --brief "<campaign.txt>" \
  --format json
```

Use only the returned:

- `parsed_campaign`;
- `recognized_conditions`;
- `unrecognized_conditions`;
- `conflicting_conditions`;
- `warnings`;
- `parser_version`.

Never recreate parsing rules in the Skill. Conflicts require a revised Brief. A blocking unrecognized condition requires explicit user acceptance before creating a confirmed config:

```bash
kol-signal campaign-preview \
  --brief "<campaign.txt>" \
  --confirm \
  --output "<confirmed-campaign.json>" \
  --format json
```

## Mapping preview

```bash
kol-signal mapping-preview \
  --input "<creator-list-1.xlsx>" \
  --input "<creator-list-2.csv>" \
  --format json
```

If an XLSX contains multiple non-empty worksheets, the CLI stops and lists them. Ask the user which worksheet contains the creator list, then repeat the preview with the explicit selection:

```bash
kol-signal mapping-preview \
  --input "<creator-list-1.xlsx>" \
  --sheet "<creator-list-1.xlsx>=<worksheet-name>" \
  --format json
```

Do not select a worksheet for the user.

Use the JSON fields returned by the CLI:

- `input`
- `source`
- `origin`
- `adapter_validation_level`
- `worksheet`
- `fingerprint`
- `requires_confirmation`
- `columns`

When `requires_confirmation` is true, run the audit in an interactive terminal only after the user supplies the mapping choices. The CLI saves confirmed mappings under `.kol-signal/mappings/`.

Do not describe a Native match as verified compatibility. Use
`adapter_validation_level` and the public compatibility matrix. `Not Tested`
means the signature matched a repository pattern but no actual vendor export
has validated it.

## Audit

Unambiguous execution:

```bash
kol-signal run \
  --input "<creator-list-1.xlsx>" \
  --input "<creator-list-2.csv>" \
  --brief "<campaign.txt>" \
  --non-interactive \
  --format json
```

When the user approved a confirmed Campaign config, add:

```text
--campaign-config "<confirmed-campaign.json>"
```

Interactive execution for user-confirmed ambiguous mappings:

```bash
kol-signal run \
  --input "<creator-list-1.xlsx>" \
  --brief "<campaign.txt>" \
  --format json
```

Successful JSON includes:

- `run_id`
- `run_dir`
- `campaign`
- `raw_records`
- `canonical_creators`
- `review_items`
- `outputs`

The Run directory contains:

```text
data_audit.xlsx
creator_shortlist.xlsx
merge_review.xlsx
feedback_template.xlsx
report.md
campaign.json
manifest.json
```

Return user-facing links to the five spreadsheets/report. Treat `campaign.json` and `manifest.json` as internal reproducibility artifacts unless the user asks to inspect Campaign parsing.

## Merge review

Allowed values in `merge_review.xlsx`:

```text
merge
keep_separate
unsure
```

Apply the completed review:

```bash
kol-signal review \
  --run "<RUN_ID>" \
  --input "<completed-merge-review.xlsx>" \
  --format json
```

The command verifies original input hashes and regenerates the selected Run. Do not describe the review as applied unless the command succeeds.

## Feedback import

```bash
kol-signal feedback \
  --run "<RUN_ID>" \
  --input "<completed-feedback-template.xlsx>" \
  --format json
```

Successful output points to:

```text
feedback_report.xlsx
feedback_report.md
```

Explain:

- merge accuracy;
- shortlist acceptance;
- contact accuracy;
- actual contacted count;
- delivery rate;
- reply rate;
- positive reply rate;
- validation warnings and text feedback summary.

Use the reported numerator and denominator. Do not recompute a missing rate as zero.

## Interpretation order

1. Read `report.md`.
2. Use `data_audit.xlsx` for source quality, missing data, staleness, and conflicts.
3. Use `creator_shortlist.xlsx` for creator-level actions and evidence.
4. Use `merge_review.xlsx` only for human identity decisions.
5. Use `feedback_report.md` or `feedback_report.xlsx` for completed outreach outcomes.

If an expected file is missing, report it as missing. Do not reconstruct it from memory.

## Failure handling

- Exit `0`: success.
- Exit `2`: invalid input, mapping, review, or feedback configuration.
- Exit `5`: output write failure.

For a failure, retain successful local artifacts, quote the concise CLI error, and suggest only the next in-scope correction. Never hide the failure behind a narrative summary.
