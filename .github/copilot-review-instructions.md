# Copilot Code Review Instructions

## Excluded paths

The `plugins/` directory contains **auto-generated mirror copies** of files
from `skills/`. A post-merge CI workflow (`scripts/sync-plugin-skills.sh`)
keeps them in sync. Do not flag differences between `skills/` and `plugins/`
— only review changes in `skills/`.
