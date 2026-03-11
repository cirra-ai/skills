# BugBot rules

When doing a review: do your best to report all issues at once. It's very time consuming to fix issues in batches.

So look carefully through all the modified code and report all issues that you can identify as soon as they are apparent from the code.

## Excluded paths

The `plugins/` directory contains **auto-generated mirror copies** of files
from `skills/`. A post-merge CI workflow (`scripts/sync-plugin-skills.sh`)
keeps them in sync. Do not review or flag changes in `plugins/` — only
review changes in `skills/`.
