---
name: address-feedback
plugin: cirra-ai-sf
description: >
  Address all automated review feedback on the current PR — this includes Bugbot, GitHub Copilot,
  and any other automated reviewers. Gathers comments, fixes issues, replies, resolves threads,
  and polls until all feedback is resolved and checks pass.
  Usage: /address-feedback
---

# Address Automated PR Feedback

Address all automated review feedback on the current PR — this includes **Bugbot**, **GitHub Copilot**, and any other automated reviewers. Run in a loop until all feedback is resolved and checks pass.

## Phase 1: Gather feedback

1. Fetch all review comments on the PR using the GitHub MCP tools:
   - Use `mcp__github__pull_request_read` to get PR details and reviews
   - Use the GitHub API via MCP to list all review comments
2. Identify comments from automated reviewers — look for authors like:
   - `bugbot` / `bugbot[bot]` / `cursor[bot]` — Bugbot
   - `copilot` / `github-copilot[bot]` / `copilot-pull-request-reviewer[bot]` — GitHub Copilot
   - Any other `[bot]` author that left review feedback
   - Human reviewers who left comments
3. Categorize each comment by source (bot vs human) and severity

## Phase 2: Address each comment

For each unresolved review comment:

1. **Read the comment carefully** — understand what the reviewer is flagging
2. **Read the relevant code** in context (not just the flagged line — read the surrounding function/file)
3. **Fix the issue** if it's a valid concern. Common categories:
   - **Bugbot**: unused code, dead methods, null safety, broad catch blocks, type assertions, missing error handling, version mismatches, incorrect paths
   - **Copilot**: code quality suggestions, potential bugs, security concerns, performance issues, best practice violations, readability improvements
4. **If it's a false positive**: document why it's not an issue (e.g., the code path is guarded elsewhere, the type is guaranteed by the caller)

## Phase 3: Reply and resolve

After addressing each comment:

1. **Reply to the comment** explaining what you did:
   - If fixed: reference the specific change (e.g., "Fixed — added null check before accessing `user.email`")
   - If false positive: explain why with evidence (e.g., "This is a false positive — `user` is guaranteed non-null by the guard on line 42")
2. **Resolve the comment thread** using `mcp__github__resolve_review_thread`

## Phase 4: Proactive scan

After addressing all existing comments, proactively scan the PR diff for issues that automated reviewers are likely to flag next:

```bash
git diff origin/<base>...HEAD
```

Look for:

- Unused imports, variables, or dead code
- Missing null/undefined checks
- Broad `catch` blocks swallowing errors silently
- Type assertions (`as`, `!`) bypassing safety
- Missing error handling on async operations
- Security issues (unsanitized input, exposed secrets)
- Performance concerns (unnecessary re-renders, missing memoization, N+1 queries)
- Inconsistent naming or style violations

Fix these preemptively before the next review cycle.

## Phase 5: Verify and push

1. Run all project checks (lint, format, build, tests) and fix any failures
2. Stage, commit, and push the fixes

## Phase 6: Poll until fully resolved

After pushing, enter a polling loop. Repeat the following every 60 seconds until the PR is fully clean (max 5 iterations — if still failing after 5 attempts, report status and stop):

1. **Wait 60 seconds** for CI and automated reviewers to process the push
2. **Check CI status** using GitHub MCP tools to fetch check runs for the latest commit:
   - If any required checks are still `queued` or `in_progress`, keep waiting
   - If any checks have `conclusion: failure`, go to step 4
3. **Check for new review feedback** using GitHub MCP tools:
   - Look for unresolved comments from automated reviewers
   - If new unresolved feedback exists, go to step 4
4. **If fixes are needed**: address the new feedback or failures (same as Phases 2-5), commit, push, and **restart this loop from step 1**
5. **If all checks pass AND no unresolved bot feedback remains**: exit the loop

### Exit criteria — ALL must be true:

- Lint passes
- Formatting passes
- Build succeeds
- Tests pass
- No unresolved Bugbot or Copilot comment threads
- CI check runs are all green (or no required checks are failing)

Report the final status of every check and confirm the PR is clean.
