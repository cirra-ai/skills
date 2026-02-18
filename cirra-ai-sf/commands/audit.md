---
name: audit
description: Run a full Salesforce org audit across Apex, Flows, and data. Coordinates collection, scoring, and report generation using audit_runner.py.
---

Run a full Salesforce org audit using the `audit_runner.py` orchestrator script.

## Locating the script

```python
import os
plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", ".")
script = f"{plugin_root}/hooks/scripts/audit_runner.py"
```

## Running the audit

```bash
# Start (or resume) a full audit
python3 audit_runner.py --output-dir ./audit_output --generate-queries

# Check progress on a running audit
python3 audit_runner.py --output-dir ./audit_output --status

# Reset and start over
python3 audit_runner.py --output-dir ./audit_output --reset
```

If the user doesn't specify `--output-dir`, default to `./audit_output` and tell them where output will be written.

## Audit phases

| Phase | Description |
|---|---|
| 0 | Plugin discovery |
| 1 | Initialize Cirra AI (`cirra_ai_init()`) |
| 2 | Count components |
| 3 | Collect Apex data (paginated) |
| 4 | Collect Flow data |
| 5 | Score Apex classes (150-pt rubric) |
| 6 | Score Flows (110-pt rubric) |
| 7–9 | Generate Word, Excel, and HTML reports |
| 10 | Validate reports |

## Output layout

All files go under `--output-dir` — never scatter files into the working directory.

```
{output_dir}/
├── intermediate/          # Batch data, progress checkpoints, raw scores
│   ├── apex_batch_*.json
│   ├── flow_batch_*.json
│   ├── apex_scoring_progress.json
│   └── flow_scoring_progress.json
├── scripts/               # Audit scripts copied here for portability
├── Salesforce_Org_Audit_Report.docx
├── Salesforce_Org_Audit_Scores.xlsx
└── Salesforce_Org_Audit_Report.html
```

## Prerequisites

Call `cirra_ai_init()` before starting. The script handles this in Phase 1, but confirm the org is accessible first.
