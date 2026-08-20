# Security Policy

## Supported status

Creator Signal Intelligence is currently an Open Alpha. Security fixes are applied to the latest repository state only; no stable release line is maintained yet.

## Reporting a vulnerability

Do not include creator lists, email addresses, handles, profile URLs, campaign details, API tokens, or other sensitive data in a public GitHub issue.

Use GitHub private vulnerability reporting through the repository Security tab when it is available. If private reporting is unavailable, contact the maintainer privately through the GitHub profile associated with this repository before sharing reproduction data.

Provide the smallest possible reproduction:

- affected `kol-signal` version;
- operating system and Python version;
- command stage and exit code;
- synthetic column names or a fully synthetic fixture;
- whether the issue can expose, overwrite, execute, or corrupt data.

Do not send the original creator file.

## Data handling boundary

The current core workflow runs on local CSV/XLSX files and does not call creator-platform APIs, Gmail, Feishu, or external model providers.

Local runs may contain full contact details. Keep `.kol-signal/`, `runs/`, exported workbooks, logs, and diagnostics out of public repositories.

## Known pre-release security limitations

- `kol-signal diagnostics` uses a fixed JSON allowlist and does not read original creator files, but users must still inspect the ZIP before sharing it.
- The project does not scan files for malware, macros, VBA, or hostile archive content.
- Only UTF-8/UTF-8-SIG CSV and unencrypted `.xlsx` are supported.
- R1 has Golden Tests for common damaged XLSX, encoding, Header, worksheet-selection, output-permission, and Formula Injection cases; it is not a complete security audit.

Keep using synthetic or appropriately de-identified files during the controlled Alpha pilot. Do not publish an original creator list when reporting a failure.
