# Public Error Code Catalog

> Applies to `kol-signal` 0.5.0a1 Open Alpha.

CLI errors use a stable public code followed by a user-readable message. The code identifies the failure family; the message contains the specific local reason.

| Code | Meaning | Exit code |
|---|---|---:|
| [`KS_PIPELINE_001`](KS_PIPELINE_001.md) | Input, Mapping, Campaign, Review, or Feedback pipeline error | 2 |
| [`KS_OUTPUT_001`](KS_OUTPUT_001.md) | Output could not be created safely | 5 |
| [`KS_DIAGNOSTICS_001`](KS_DIAGNOSTICS_001.md) | Diagnostics Run or Manifest is unavailable or unsafe | 2 |

Do not publish an original list, Run folder, Campaign file, screenshot with creator data, or Python Traceback. Use:

```bash
kol-signal doctor
kol-signal diagnostics --run RUN_ID --output diagnostics.zip
```

Inspect `diagnostics.zip` before attaching it to a GitHub Issue.
