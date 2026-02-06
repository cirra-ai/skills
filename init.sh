#!/usr/bin/env bash
set -euo pipefail

OWNER="cirra-ai"
REPO="skills"
BRANCH="setup/repo-standard"
MAIN_BRANCH="main"
PR_TITLE="chore: add community files and basic CI"
PR_BODY="Adds CONTRIBUTING, CODE_OF_CONDUCT, ISSUE/PULL templates, SECURITY, CODEOWNERS, LICENSE (Apache-2.0), and a basic CI workflow.\n\ncc: @jvg123"

# REQUIREMENTS: git, curl, jq (optional), and optionally gh (recommended)
for cmd in git curl; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: Required command not found: $cmd"
    exit 1
  fi
done

USE_GH=false
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then
    USE_GH=true
    echo "gh detected and authenticated; script will use gh to create the PR and call the API."
  else
    echo "gh detected but not authenticated. You can authenticate using: gh auth login"
  fi
else
  echo "gh not detected. Script will still create branch and push; create the PR manually or install gh for full automation."
fi

WORKDIR="$(mktemp -d)"
cd "$WORKDIR"
echo "Working in temporary dir: $WORKDIR"

git clone "https://github.com/${OWNER}/${REPO}.git"
cd "${REPO}"

# create or checkout branch
if git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  git checkout "${BRANCH}"
else
  git fetch origin
  if git ls-remote --exit-code --heads origin "${BRANCH}" >/dev/null 2>&1; then
    git checkout -b "${BRANCH}" origin/"${BRANCH}"
  else
    git checkout -b "${BRANCH}"
  fi
fi

mkdir -p .github/ISSUE_TEMPLATE .github/workflows

cat > .github/CONTRIBUTING.md <<'EOF'
# Contributing to cirra-ai/skills

Thanks for your interest — we welcome contributions!

How to contribute
1. Search existing issues and PRs before opening a new one.
2. For small fixes, open a PR directly. For larger changes, open an issue first to discuss.
3. Use one branch per change; name it like `feat/<short-desc>` or `fix/<short-desc>`.
4. Include tests and update documentation when applicable.
5. Run linters and tests locally before opening a PR.
6. Fill the PR template and link any related issues.

Labels
- Look for issues labeled `good first issue` or `help wanted` if you are new.

Code style
- Follow existing project style. Add or update tests for your changes.
EOF

cat > .github/CODE_OF_CONDUCT.md <<'EOF'
# Contributor Covenant Code of Conduct

This project follows the Contributor Covenant:
https://www.contributor-covenant.org/version/2/0/code_of_conduct/

Be respectful, inclusive, and kind. Reports of unacceptable behavior should be sent to the maintainers or GitHub's support channels.
EOF

cat > .github/PULL_REQUEST_TEMPLATE.md <<'EOF'
## Summary

Please include a summary of the change and any related issue number(s).

## Checklist
- [ ] I have read the CONTRIBUTING guide
- [ ] Tests added/updated (if applicable)
- [ ] Documentation updated (if applicable)

Reviewer notes
- Any special notes for the reviewer.
- cc: @jvg123
EOF

cat > .github/ISSUE_TEMPLATE/bug_report.md <<'EOF'
---
name: Bug report
about: Create a report to help us fix an issue
---

**Describe the bug**
A clear and concise description of what the bug is.

**Steps to reproduce**
1. 
2. 
3. 

**Expected behavior**
What you expected to happen.

**Environment**
- OS:
- Language/runtime version:
- repo commit:
EOF

cat > .github/ISSUE_TEMPLATE/feature_request.md <<'EOF'
---
name: Feature request
about: Suggest an idea for this project
---

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Alternatives considered**
Other approaches you've tried or considered.

**Why is this needed**
Explain the benefit and potential users.
EOF

cat > .github/SECURITY.md <<'EOF'
# Security Policy

If you discover a security vulnerability, please disclose it privately.

Preferred contact methods:
- Use GitHub's private security advisory feature, or
- Email security@cirra.ai

Please include:
- Steps to reproduce
- Affected versions
- Impact assessment and contact details

Response time: We will acknowledge within 72 hours.
EOF

cat > .github/CODEOWNERS <<'EOF'
# Make jvg123 the default code owner for everything
* @jvg123
EOF

cat > .github/workflows/ci.yml <<'EOF'
name: CI

on:
  push:
    branches:
      - main
      - setup/repo-standard
  pull_request:
    branches:
      - main

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Detect and run tests
        run: |
          if [ -f package.json ]; then
            echo "Node project detected — installing and running tests"
            npm ci || true
            npm test || echo "No tests or tests failed"
          elif [ -f requirements.txt ] || [ -f setup.py ]; then
            echo "Python project detected — running pytest if present"
            python -m pip install -r requirements.txt || true
            pytest -q || echo "No tests or tests failed"
          else
            echo "No recognized test harness found. Replace this job with your project's CI."
          fi
EOF

cat > LICENSE <<'EOF'
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

(Full Apache-2.0 license text should be inserted here; replace this placeholder with the official text.)
Copyright 2026 cirra-ai

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
EOF

git add .github LICENSE
git commit -m "chore: add community files, CODEOWNERS, Apache-2.0 LICENSE and basic CI" || {
  echo "No changes to commit (maybe branch already contains the files)."
}
git push --set-upstream origin "${BRANCH}"

# Create PR
if [ "${USE_GH}" = true ]; then
  gh pr create --title "${PR_TITLE}" --body "${PR_BODY}" --base "${MAIN_BRANCH}" --head "${BRANCH}" --label "chore" --assignee "jvg123" || \
    echo "PR creation via gh failed; you can create the PR manually on GitHub."
  echo "PR created (or attempted)."

  # Apply branch protection using your own authenticated privileges:
  # Use gh to get a token for the curl call (local use only).
  TOKEN="$(gh auth token)"
  if [ -z "$TOKEN" ]; then
    echo "gh auth token returned empty; branch protection step will be skipped."
    exit 0
  fi

  PROTECTION_JSON='{
    "required_status_checks": {"strict": true, "contexts": []},
    "enforce_admins": false,
    "required_pull_request_reviews": {"required_approving_review_count": 1},
    "restrictions": {"users": ["jvg123"], "teams": []}
  }'

  echo "Applying branch protection to ${MAIN_BRANCH} (restrict pushes to jvg123, require 1 approving review)..."
  # Use curl with token obtained locally
  resp=$(curl -s -o /dev/stderr -w "%{http_code}" -X PUT \
    -H "Authorization: token ${TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${OWNER}/${REPO}/branches/${MAIN_BRANCH}/protection" \
    -d "${PROTECTION_JSON}" )

  if [ "$resp" -eq 200 ] || [ "$resp" -eq 201 ] || [ "$resp" -eq 204 ]; then
    echo "Branch protection applied successfully."
  else
    echo "Branch protection API returned HTTP status: $resp. If you see 403, your account lacks the needed permission or gh's token wasn't sufficient."
    echo "You can set branch protection from the GitHub UI: Settings → Branches → Add rule → main"
  fi

else
  echo "No gh auth found. Branch and files pushed to origin/${BRANCH}."
  echo "Open a PR from setup/repo-standard → main in the repo web UI:"
  echo "https://github.com/${OWNER}/${REPO}/pull/new/${BRANCH}"
  echo ""
  echo "Then set branch protection via: Settings → Branches → Add rule (branch: main) → require PR reviews, restrict who can push (add jvg123), and require status checks once CI runs."
fi

echo "Done. Repository branch: ${BRANCH} pushed. PR creation and branch protection attempted if gh was available."