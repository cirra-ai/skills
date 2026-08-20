<!-- AUTO-GENERATED — DO NOT EDIT.
     Source: cirra-ai/processes/agents/dev/AGENTS-SHARED.md
     Synced by .github/workflows/sync-dev-agents.yml in cirra-ai/processes.
     Edit the source in processes; this copy is overwritten on sync. -->

# Cirra AI — Shared Development Policy

> **Canonical source.** This file lives in `cirra-ai/processes` as
> `agents/dev/AGENTS-SHARED.md`. A GitHub Action syncs it into each consumer
> repo as `AGENTS.shared.md`, which the repo's `AGENTS.md` imports via
> `@AGENTS.shared.md`. **Edit it only in `cirra-ai/processes`** — never edit the
> synced `AGENTS.shared.md` copies.
>
> This is the team-wide policy that applies to every Cirra AI repo and every
> agent (Claude Code, Cursor, Codex, and anything else). Anything
> stack-specific (build commands, deploy targets, framework quirks) belongs in
> the consuming repo's own `AGENTS.md`, not here.
>
> **One policy file.** Do not put rules in `CLAUDE.md`, Cursor-only dumps, or
> Codex forks. If a rule is useful, it goes here. If it applies only to one
> client (or one version of a client), it still goes here, in a subsection
> clearly marked for that client.
>
> Claude Code reads `CLAUDE.md`, not `AGENTS.md`
> ([docs](https://code.claude.com/docs/en/claude-md#agentsmd)). Each repo
> creates its own adapter next to its `AGENTS.md` — a one-line `@AGENTS.md`
> import, or `ln -s AGENTS.md CLAUDE.md`. That adapter is **not** copied from
> this repo. Do not put policy in it.

## ⛔ VERIFY BEFORE ASSERTING — NO GUESSING

Every factual claim about state, code, deploys, vendor behavior, config, or
file contents MUST come from a verified source in the same turn — a `Read`, a
`grep`, a CLI call, a doc URL, a tool result. Plausible inference is not a
source. Training-data recall is not a source. "Usually how X works" is not a
source.

If you cannot verify it: say "I don't know — let me check" or explicitly flag
the uncertainty. **Never present a guess as fact.**

Past failures this rule exists to prevent:
- Asserted "PR is merged to develop but not yet deployed to prod" from a
  typical-pipeline assumption, while the GitHub API + deployment status were
  both one tool call away. The PR had already shipped via a release. Damage:
  lost trust, wasted cycles diagnosing the wrong thing.
- Fabricated UI navigation paths in vendor consoles (see "NEVER GUESS AT
  MANUAL INSTRUCTIONS" below — the specific case of this rule).

Workflow for any factual claim:
1. Identify the source you'd cite if challenged.
2. If you don't have it, fetch it: `Read`, `grep`, GitHub API, WebSearch, ask
   the user. Don't proceed without it.
3. Reference the verified source in the answer.
4. If still uncertain, say so explicitly. Uncertainty is acceptable; false
   confidence is not.

## ⛔ NEVER GUESS AT MANUAL INSTRUCTIONS

When you tell the user to take a manual action in someone else's UI (Vercel,
Neon, GitHub settings, Auth0, AWS, Cloudflare, Stripe, 1Password, Notion,
Linear, GTM, Cookiebot, or any other third-party console), you must give an
**exact navigation path backed by current documentation**, not a
plausible-sounding guess.

**Required shape of any manual instruction:**

> Navigate `A → B → C` (see [exact doc title](https://exact-url)).
> The setting you want is called `<verbatim setting name>`.

**Forbidden shapes:** any sentence with "should be", "might be", "look for",
"around", "somewhere under", or "if available".

**Workflow that produces this kind of instruction:**

1. Before writing manual steps, run `WebSearch` / `WebFetch` against the
   vendor's current docs. Prefer `vendor.com/docs/...` and changelog pages.
   Read what you find. Quote exact setting names.
2. If the docs confirm the path: write it out with the URL inline.
3. If the docs do *not* confirm the path or you can't find them: **say so
   explicitly** — "I can't find current docs for this; the navigation may have
   changed. Here's what I'd try first, but please verify." Never present
   uncertain instructions as confident ones.
4. If the user is in the UI and can paste a screenshot, ask for one rather than
   guess.

Sending the user on a wild goose chase with false confidence is worse than
admitting you can't find the answer.

## ⛔ Know your runtime surface — filesystem, transfer, and tool scope

Three filesystem surfaces, three stories — identify which before any "put the
file at X" instruction.

- **Claude Code remote container** (claude.ai/code, GitHub Actions runs,
  sandboxes): tools work against `/home/user/...`, but that filesystem is
  **yours, not the user's** — ephemeral cloud container they can't reach
  from their browser.
- **Claude Code CLI on the user's own machine**: same tools, but the
  filesystem **is** theirs. Repo paths look like `/Users/<name>/...`,
  `C:\Users\<name>\...`, or `/home/<their-username>/...` — never the literal
  `/home/user/`.
- **Claude Desktop / claude.ai chat**: no tools, no shared filesystem.

**`/home/user/...` is the giveaway for the remote-container case.** Never
tell the user to put a file at that path regardless of which tools are
available — they can't.

Getting **bytes** into the container is harder than it looks. Verified modes:
(a) user commits on the branch (GitHub web UI's "Add file → Upload files"
drag-drop works), then `git pull`; (b) public URL the agent `curl -o`s to
disk. **Pasting an image in chat doesn't work** — it arrives as a multimodal
visual, never lands on the container filesystem, so `Read` / `Bash` can't
access the bytes. Verify a transfer mode delivers bytes before proposing it.

**Check tool scope before promising — and before declaring something
impossible.** MCP servers and permission grants are fixed at session start. Repo
scope is not always: some harnesses expose `add_repo`, which attaches a
repository mid-conversation (verified — `cirra-ai/processes` was attached that
way, cloned, and pushed to). Look at the tool list before either proposing
`add_repo` or telling the user a repository is out of reach; whichever you
assert without checking will be wrong in the other case.

**Availability and pre-approval are different questions, and a repo's
`.claude/settings.json` answers only the second.** A tool the MCP server does
not ship cannot be called at all. A tool it ships that the allowlist omits can
be called — it prompts first, and the prompt renders in the user's UI, not in
your tool output. So never read a gap in an allowlist as proof a capability is
missing, and never read an entry in one as proof it exists. Check the session's
tool list for availability; check `.claude/settings.json` only for whether the
call will interrupt someone. (Which settings file a given surface actually
reads is its own trap — see
[`RUNTIME-CONFIG.md`](https://github.com/cirra-ai/processes/blob/main/agents/dev/RUNTIME-CONFIG.md).)

## ⛔ GitHub access, by surface and channel

Which GitHub channel works depends on the runtime, and agents keep conflating
the two and burning turns on it.

**Detect the runtime with the environment variable, never the git remote.** In a
cloud session the remote is a plain `https://github.com/<org>/<repo>` —
byte-identical to the same repository's remote on a laptop, so it tells you
nothing about which runtime you are in:

```bash
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] && echo cloud || echo local
```

### Cloud sessions (`CLAUDE_CODE_REMOTE=true`)

All GitHub traffic goes through Anthropic's
[GitHub proxy](https://code.claude.com/docs/en/cloud-environments#github-proxy),
which deliberately keeps the real credential outside the VM.

| Channel | Works | Notes |
| --- | --- | --- |
| `mcp__github__*` MCP tools | **Yes** | PR read/write, issues, checks, comments, reviews. The path to use. |
| `git` clone / fetch / push | **Yes** | Proxy injects credentials; `push` only to the session's working branch. Ref **creates and updates** only — deletion is refused, see below |
| PR webhooks into the session | **Yes** | |
| REST via `curl` / `gh api` | **No** | 403 — see below |
| GraphQL (`gh pr view`, `gh pr list`) | **No** | Only a pinned set of PR-review operations is served |

`GH_TOKEN` and `GITHUB_TOKEN` read as the literal string `proxy-injected` — a
placeholder the proxy substitutes on outbound requests, not a credential. **A
script that builds an `Authorization` header from either sends a bogus token.**
`gh` is not pre-installed.

**A cloud session cannot delete a remote branch, by any channel.** `git push
origin --delete <branch>` — and the `:<branch>` refspec form — returns:

```
<= Recv header: HTTP/1.1 403 Forbidden
<= Recv header: Content-Type: application/x-git-receive-pack-result
error: RPC failed; HTTP 403 curl 22 The requested URL returned error: 403
```

on the very remote where a create-or-update push succeeded minutes earlier, so
it is the deletion the proxy refuses, not the push as such. Git then prints
`Everything up-to-date`, which reads like success — confirm with `git ls-remote
--heads origin <branch>` rather than trusting the command's own output. **The
GitHub MCP server ships no branch-deletion tool at all** — its `repos` toolset
has `create_branch` and no `delete_branch` / `delete_ref` counterpart
(<https://github.com/github/github-mcp-server>) — so there is no fallback. This
is a gap in the server, not in any repo's allowlist: no permission entry can
conjure the tool. **Report that the cleanup needs a local checkout, and stop.**
Do not retry, and do not invent a web-UI navigation path you have not verified
against current docs.

Four things that look like fixes and are not, each measured:

- **Installing `gh`** (`apt install -y gh`) — installs cleanly, then 403s
  identically. The missing binary was never the blocker.
- **Passing `-H "Authorization: token $GH_TOKEN"`** — sends the placeholder.
- **Omitting the header** so the proxy injects its own — same 403.
- **Starting a fresh session** — byte-identical 403 in a new container.

### Don't act on the 403's text — and don't write it off as intended

The body reads *"An org admin must connect the Claude GitHub App for this
organization."* **That App is already connected**: PR webhooks arrive and the
MCP tools work, and both depend on it. Sending anyone to connect it again wastes
their time.

It is equally wrong to record this as settled policy, because Anthropic
documents the opposite —
[GitHub proxy](https://code.claude.com/docs/en/cloud-environments#github-proxy):

> **API requests**: requests from the built-in GitHub tools, and from `gh` under
> the `proxy-injected` placeholder, go out with your real credentials
> substituted.
>
> **Repository scope**: GitHub API […] requests reach only repositories attached
> to the session, so […] an unattached repository gets a 403.

So an **unattached** repository returning 403 is expected and correct. An
**attached** one returning 403 contradicts the documentation, and is filed with
Anthropic as a defect. The two cases return different bodies — the unattached
one points at `add_repo` — which is how you tell them apart.

Until it is resolved, use `mcp__github__*` and don't re-measure the 403; it is
deterministic across sessions and containers.

### Local machine

`gh` is authenticated via the OS keyring and works normally, GraphQL included.
Prefer `gh` / `gh api` over hand-rolled `curl`.

**Do not rely on `$GH_TOKEN` locally.** It may be unset, and a stale value
*shadows* working keyring auth because both `gh` and `curl` prefer it over the
keyring. Symptom: `HTTP 401 Bad credentials` while `gh auth status` looks
healthy. Fix: `GH_TOKEN= gh ...`, or remove the dead token from your env config.

### Tooling that shells out to `gh`

It degrades silently in cloud sessions. When a guard cannot run, make it say so
loudly rather than fail open in silence — a guard that skips without a signal is
worse than no guard, because it reads as a pass.

## ⛔ Cite your sources for factual claims about external tools

Whenever you state a fact about a third-party platform, tool, API, library, or
SDK this code depends on (limits, defaults, available fields, behavior, version
support, etc.) — verify it against the vendor's current documentation and
include the source URL in your response, in the code comment, and in the PR
description where relevant. Training-data recollection is not a citation: if you
cannot produce a live source, say so explicitly. Out-of-date numbers in these
codebases have already caused real bugs.

## ⛔ GitHub Actions: latest stable version, pinned by SHA

When adding or updating a step in a workflow file:

1. **Use the most recent stable release** of the action. Check the action's
   GitHub releases page (e.g. `https://github.com/<owner>/<action>/releases`)
   in the same turn — don't copy the version from a sibling workflow, which
   may be months stale and ship a deprecated runtime (the Node.js 20 → 24
   migration on GitHub Actions is the canonical example: an old pin still
   "works" but fires a deprecation warning on every run and will eventually
   fail outright).
2. **Pin by the full 40-character commit SHA**, with the version tag in an
   inline comment so humans can still read it: `uses: owner/action@<sha>  #
   vX.Y.Z`. Tags can be moved silently; a SHA cannot. This is the
   GitHub-recommended supply-chain practice.
3. **Deprecation warnings get their own PR.** When the runner reports an
   action is on a deprecated runtime / input, bump it in a focused PR rather
   than bundling it with feature work, so the upgrade is reviewable on its
   own.

## ⛔ DO NOT HACK

Unless specifically requested, EVERYTHING you do must follow industry best
practices and solid design patterns. This is production code, not a hobby
project or throwaway.

- If you do not feel confident, say so and ask for advice.
- Do not follow what you're asked just because you're asked. Push back if you
  think it's a bad idea.
- When asked for a "proposal" or "advice", provide only that — do not modify
  any code. Only change code when asked to implement / build / develop / create.
- Find the standard, simple solution. If you're considering a hacked approach,
  step back and look for a way to simplify.

## ⛔ MANDATORY checklists

Two separate checklists. Walk through the relevant one **in order** and confirm
each item — if any is N/A, state explicitly **why** in the chat. Never silently
skip an item. (The exact lint / type-check / test / build commands live in the
consuming repo's `AGENTS.md` under "Commands".)

### Pre-push checklist (run before EVERY `git push`, including amends/follow-ups)

This is not the same thing as the PR-completion checklist below. Many pushes
happen during the life of a PR (review fixes, scope changes, follow-ups). On
**every single push** — not just the first one and not just on "declaring done"
— walk this list. The PR description goes stale faster than any other artifact
and reviewers (human and bot) read it on every glance at the PR.

- [ ] All work is on a feature branch — **never** push or commit to a protected
      branch (see "Git Push / Merge Rules"). The repo's default base branch is
      named in its `AGENTS.md`.
- [ ] The current branch was created for *this* task from `origin/<default>`
      (or is the open PR branch for this same change — see "Continuing work on
      an existing PR"). Every staged file is an edit from *this* task — never
      someone else's unrelated WIP on a branch you did not create for this work.
- [ ] No `--no-verify`, `--no-gpg-sign`, or other guardrail-bypassing flag in
      the push or in the commits being pushed.
- [ ] The repo's lint / type-check / test gate passes locally, plus a build when
      app or config code changed. (Exact commands: repo `AGENTS.md`.)
- [ ] No secrets in the diff (`.env`, credentials, API keys, tokens).
- [ ] If the change is UI-affecting: visual proof regenerated and embedded per
      the repo's visual-verification workflow (see "Evidence before done").
- [ ] **Re-read the open PR's current description (`mcp__github__pull_request_read`
      method `get`) and compare it to the new branch state.** If the diff, scope,
      approach, file list, trade-offs, or test plan have drifted in any way —
      even slightly — update the PR body via `mcp__github__update_pull_request` (or `gh pr edit` if GitHub MCP tools aren’t available)
      in the same turn as the push. Do not append a contradictory "Update: …"
      addendum; rewrite the affected sections so the body reads as one coherent
      description of what is on the branch right now. See "PR Description
      Maintenance".
- [ ] Any unresolved review threads from prior pushes either replied to with the
      fix commit SHA, or filed as a follow-up issue if deferred.

### PR-completion checklist (run before declaring done / asking to merge)

Includes everything in the pre-push checklist above, plus:

- [ ] PR is still `draft: true` — auto-merge will ship unreviewed code to the
      base branch if it isn't.
- [ ] Automated review (Bugbot / Copilot) addressed: invoked after
      creating/updating the PR and polled until complete with no remaining
      issues. See "Automated PR Review".
- [ ] If you fixed a defect, you searched for and fixed all other occurrences of
      the same pattern (see "Fix all instances, not just one").
- [ ] If you deferred any reviewer-flagged issue, a follow-up issue exists and
      its URL is in the deferral reply.

## ⛔ Git Push / Merge Rules

**NEVER push directly to a protected branch (e.g. `develop`, `staging`,
`main`). NEVER merge anything into a protected branch without explicit user
approval.** Always work on feature branches; push to feature branches only. When
work is complete, ask before creating a PR or merging.

- **Always create PRs as draft.** There is auto-merge infrastructure — a
  non-draft PR can be merged before the human author has reviewed it, silently
  shipping unreviewed code. Use `draft: true` (`mcp__github__create_pull_request`)
  or `--draft` (`gh`); send `"draft": true` over the REST API. There are no
  exceptions, even for "trivial" changes. If you ever discover you've opened a
  non-draft PR, convert it back to draft and notify the user.
- **Always branch from — and target — the repo's *default* branch.** Never
  assume `main`. Before `git checkout -b` /
  `git worktree add` / opening a PR, confirm the default (`gh repo view --json
  defaultBranchRef`, `git remote show origin | grep "HEAD branch"`, or the
  repo's `AGENTS.md`) and use `origin/<default>` as the base. A feature branch
  cut from `main` when the integration branch is e.g. `staging` is the leading
  cause of phantom merge conflicts and "ghost revert" PRs. Only target a
  non-default branch when the user explicitly says so.
- **Never adopt another person's (or another task's) feature branch for new
  work.** For any new task, create your own branch from `origin/<default>`
  *before* editing. Do not commit, push, stash, amend, or reset on a branch
  you did not create for *this* task — even if the IDE, harness, or a
  "commit-and-push" action names it as the current branch.

  Before every commit or push: verify every staged file is an edit from *this*
  conversation's task. If the working tree only has unrelated WIP, or your
  edits are missing from the current branch, stop — cut a new branch from
  `origin/<default>` (use a separate `git worktree` if needed so you do not
  disturb the other branch's working tree) and apply only your changes there.

  A "branch changed" / session-context note does **not** transfer ownership of
  unrelated local changes. The exception is
  [Continuing work on an existing PR](#continuing-work-on-an-existing-pr): when
  the user asks for follow-ups on an open PR *for that same change*, push to
  that PR's branch.

  Past failure this rule exists to prevent: an agent fixed a one-file bug,
  then a commit-and-push action pointed at an unrelated feature branch with
  someone else's uncommitted WIP; the agent staged that WIP instead of
  creating a clean branch from the default base for its own fix.

## ⛔ No Destructive Git Operations Without Explicit Request

**NEVER run destructive git operations unless the user explicitly asks for them
in the same turn** — even on a feature branch you own. Forbidden without an
explicit request:

- `git push --force` / `-f` / `--force-with-lease` / `--force-if-includes`
  *("safer" only guards the push; the history rewrite is the same)*
- `git reset --hard`, `git restore .` / `git checkout .`, `git clean -fd`
- `git branch -D <branch>` *(use `-d`; let git refuse if unmerged)*
- `git rebase` followed by a force-push *(the rebase is fine; the force-push is
  what makes it destructive)*

When you hit a situation that *seems* to need one of these (commonly: a feature
branch carrying commits that already landed on the base branch via a release,
producing phantom conflicts), the **non-destructive alternative is almost
always `git merge origin/<base>` into the feature branch** — it preserves every
commit SHA and needs no force-push. If a rebase + force-push is genuinely right
(user asked, or the branch was never pushed), proceed. Otherwise **ask first, in
the same message you would have run the destructive op.**

## ⛔ Working copy — do not write in the user's primary checkout

The user's local clone of a repo often has uncommitted work, local config, and
experiments. Writing into it risks losing that work. This has happened.

**Before the first write on a coding task**, work in an isolated checkout:

1. Use the isolated workspace the harness already gave you (Cursor cloud
   agent, Claude Code remote container, a worktree the user pointed you at).
2. Otherwise create a git worktree from `origin/<default>` (see "Git Push /
   Merge Rules"), copy gitignored `.env*` files from the primary clone into
   the worktree, and do all writes there.
3. Multi-repo work: one worktree per repo.

**Exceptions — the primary clone is fine when:** the user explicitly says to
use it; the task is read-only; the harness checkout *is* the isolated copy.

Do not hardcode another developer's home path (`/Users/<someone>/...`) into
commands or docs. Resolve the repo from the current workspace.

## Interacting with user

During an ongoing Q & A session with the user, hold off on running tests and analyzing CI results until all feedback has been received.

Test runs are time consuming and useless until features are fully built.

If in doubt, ask the user if it is OK to start the test run before launching it.

## Use CLIs; don't hand the user a script

When a task can be done with a CLI that is installed and authenticated (`gh`,
`vercel`, `stripe`, package managers, the repo's own scripts), run it. Do not
paste a command for the user to run unless:

- the action needs browser authentication the CLI cannot do
- the CLI is missing or unauthenticated
- the action is destructive and needs explicit confirmation (see below)

**Read and non-production writes are pre-approved.** Production writes are
not: identify the target environment first, and confirm with the user before
changing production.

## Database

**Read** queries to investigate are fine. **Write** operations — inserts,
updates, deletes, and migrations that mutate data — need an explicit user
request in the same turn, for every environment.

## Continuing work on an existing PR

When the user asks for follow-up changes to an open PR, push the new commits
**to that PR's existing branch**. Do not open a second PR, do not create a
parallel feature branch, and do not push to a different branch the harness
happens to suggest in its session-start instructions — the user's intent (a
single PR for one conceptual change) overrides the harness branch name.

**Always verify the PR is still open before pushing.** Use
`mcp__github__pull_request_read` (`method: "get"`) and check `state === "open"`
and `merged === false`. **Never push to a branch linked to a closed or merged
PR** — those commits would be ignored and may silently re-introduce or
contradict shipped changes. If the PR is closed or merged, or its head branch
was deleted, stop and ask how to proceed.

## PR Description Maintenance

**The PR description is part of the PR — keep it accurate on every push.** This
is the single most-violated rule on the team. Reviewers (human and bot) read the
description before the diff; a stale description causes wasted review cycles,
hallucinated complaints about removed code, and merge-time confusion.

**Mandatory: on every `git push` to an open PR, re-read the PR description
(`mcp__github__pull_request_read` method `get`) and compare it to the new branch
state.** The default assumption is that anything past the first push has drifted;
verify, don't assume. Treat auto-generated PR bodies (created by the harness/UI)
as drafts to be immediately rewritten, not as the canonical description.

**Do not** append a contradictory "Update: …" addendum — rewrite the affected
sections so the description reads as one coherent description of what is on the
branch right now. Update via `mcp__github__update_pull_request` **in the same
turn as the push that triggered the change.**

## ⛔ Automated PR Review (Bugbot AND Copilot) — ACT WITHOUT BEING PROMPTED

**Non-negotiable. The moment an automated reviewer (`bugbot` / `cursor[bot]`,
`copilot-pull-request-reviewer[bot]` / `github-copilot[bot]`, or any other
`[bot]`) posts a review or inline comment on a PR you opened — typically
arriving as a `github-webhook-activity` event — you MUST fetch it, triage every
finding, and fix or explicitly defer it in that same turn. Do NOT wait for the
user to say "address the bugbot issues." The bot comment is the trigger.**

On every PR you open or push to:

1. **After creating/updating the PR**, proactively invoke the repo's automated
   review loop (e.g. `/bugbot` / `/address-feedback`) — do not wait for the user.
2. **On every bot-review event**, in the same turn: pull the threads
   (`mcp__github__pull_request_read` with `method: "get_reviews"` /
   `"get_review_comments"`), then for each unresolved finding either fix it (if
   confident and small), ask the user (if ambiguous, architecturally
   significant, or user-visible), or skip with a written reason (duplicate /
   spam / already handled). Reply to the thread per "Responding to PR review
   threads".
3. **Never end a turn on an open bot finding without acting on it.**

**Never change user-visible functionality based solely on bot advice without
checking with the user first.** Bots are good at dead code, type issues, race
conditions, and leaks — accept those freely. But they have no view of the
product spec, so when advice would *remove* a feature, *change a UX flow*, or
*alter visible copy*, escalate via `AskUserQuestion` rather than following it.
When unsure whether a finding is engineering-hygiene or product-behavior,
default to asking — wrong removals are far costlier to detect than wrong
retentions.

## Responding to PR review threads (Bugbot, Copilot, human reviewers)

When you address a review comment from any reviewer, **close the loop on the
thread itself**, not just in the chat. Unanswered threads block merge. In
preference order — never silently drop a thread:

1. **Post the reply via the GitHub MCP tools** when you can
   (`mcp__github__add_reply_to_pull_request_comment` for an inline thread, or
   `mcp__github__add_issue_comment` for a top-level PR comment). Reference the
   fixing commit SHA so the thread is self-explanatory. Then resolve the thread.
2. **If posting fails or is out of scope, paste ready-to-send reply text into
   the chat** for the user to copy — complete and standalone, one block per
   thread, labeled with the thread location (`file:line`).

Do this proactively, in the same turn as the fix commit. Even when a thread is
`is_outdated` after your fix, GitHub does not auto-resolve it — the reviewer
still needs a reply. Keep it tight: one reply per thread naming the fixing commit
and what changed; no long restatements or apologies. Skip only clear spam,
withdrawn duplicates, or purely informational comments (e.g. a deploy-success
note).

## Deferring a reviewer-flagged fix → file a tracking issue

If you punt on a legitimate fix flagged by a reviewer (human or bot) —
pre-existing pattern, large blast radius, separate cleanup, etc. —
**immediately create a GitHub issue** (`mcp__github__issue_write`) describing the
problem, the scope, the suggested approach, and a link back to the review
thread. Then reply to the thread with the issue link so the deferral is tracked,
not just deflected. "Out of scope, won't fix here" without an issue is silent
debt — don't do it.

## Fix all instances, not just one

When fixing a problem, search the codebase for other occurrences of the same
pattern or root cause before reporting the fix as done.

- **Mandatory** when other occurrences are defects (bugs, security issues,
  incorrect behavior): fix them all in the same change and call them out.
- **Optional** when other occurrences are nice-to-haves (refactors, style,
  consistency): list them and ask before including them.

Never silently fix one occurrence while others remain. Surface what you found,
what you fixed, and what you left alone.

## Learn from reviewer findings

When Bugbot, Copilot, or a human reviewer flags an issue you should have
caught:

1. Fix it in code.
2. Name the pattern (null safety, missing guard, unused export, …).
3. If the pattern is general, add it to **this file** in the same change —
   not a personal memory file, not `CLAUDE.md`. The next agent only benefits
   if the rule lives here.

A category of finding that repeats is a failure of this loop.

## Evidence before claiming "done"

Never claim a fix works without evidence. Type-check / test passes verify code
correctness, not feature correctness — they are not a substitute for observing
the actual behavior.

- **UI-affecting changes require visual proof** before any "pushed / done /
  ready / fixed" message: regenerate screenshots, inspect them yourself, show
  them inline in the chat, and embed them in the PR body. The exact tooling
  (Playwright, Puppeteer, etc.) and commands live in the consuming repo's
  `AGENTS.md`.
- If a change has **zero rendered output**, say so explicitly ("No UI rendered:
  …") rather than silently skipping the step.

### Embedding visual proof in PR bodies (private-repo rule)

Cirra AI GitHub repos are private. **Never** put `https://raw.githubusercontent.com/...` image (or video) URLs in a PR description or review comment. GitHub's markdown renderer and Camo proxy fetch those URLs unauthenticated, so they 404 even when the file exists on the branch. Committing the PNG does not make that URL work.

Past failure this rule exists to prevent:
- Website PR #200 committed screenshots to `.github/screenshots/<branch>/` and linked them with `raw.githubusercontent.com` in the PR body. Reviewers and Copilot saw broken images. The files were on the branch; Camo could not read a private repo.

**How to embed:**

1. **Capture and store** per the consuming repo's `AGENTS.md` (tooling, viewports, save path). Commit the files when that repo requires it (typical path: `.github/screenshots/<branch-name>/`) so the evidence remains in git.

2. **Cursor Cloud Agents** using `ManagePullRequest`: put HTML `<img>` (or `<video>`) tags in the PR body with **absolute filesystem paths**. The tool uploads the files and rewrites `src` to public `https://cursor.com/artifacts/...` URLs.

   ```html
   <img alt="Desktop after: feature X" src="/workspace/.github/screenshots/<branch-name>/desktop-after.png" />
   ```

   Do **not** wrap those in markdown `![]()`. Do not point `src` at GitHub.

3. **Any other surface** (local Cursor, Claude Code, `gh pr edit`, GitHub MCP `update_pull_request`): those tools do **not** rewrite filesystem paths. Attach the images in the GitHub UI (hosted at `https://github.com/user-attachments/assets/...`) or another public host the renderer can fetch without credentials. Pasting a local path into `gh pr edit` produces a broken image.

**Consuming-repo `AGENTS.md` owns** capture tooling, save location, and measurement rules. It must not instruct agents to use `raw.githubusercontent.com`.

## Review the diff before you push

The checklists above confirm process. This section is about the code.

Read `git diff origin/<base>...HEAD` end-to-end before the first push — not
only the lines you just typed. Adjacent code you did not touch still
interacts with your change. One clean pass beats three "fix the bot"
commits: automated review re-scans the whole diff every time.

For each changed line, check:

- null / undefined / empty / unexpected input
- error paths that return `undefined` where the caller expects a value
- unhandled promises (missing `await` / `.catch()`)
- type assertions (`as Foo`, `!`) that skip a real guard
- user input interpolated into shell, SQL, or HTML
- secrets in client code or logs
- unused imports, leftover exports, `console.log` / debug leftovers
- `useEffect` subscriptions without cleanup; async work not cancelled on unmount
- races: a read then an await then a write; navigation before an in-flight request finishes

Patterns that have already burned review cycles:

- `=== null` when `undefined` is also possible — normalize with `?? null` at the source
- `process.env.X` in `"use client"` components — it needs `NEXT_PUBLIC_` or a `next.config` mapping
- SWR/fetch: guard both `isLoading` **and** data being defined (a failed fetch is `data = undefined, isLoading = false`)
- `key={id || index}` when `id` is required in the type — dead fallback
- `obj ?? {}` passed into a typed function — pass the fields you mean
- `in` on a value that is not an object — `in` throws on null and primitives; guard with `typeof` / `instanceof` first

If you are not confident the code is correct, do not push. Investigate.

If a problem survives more than one test cycle, stop patching symptoms: name
the root cause, list approaches, and debug against evidence.

## Security

- Never interpolate untrusted input into shell commands, SQL, or templates —
  parameterize or escape.
- In GitHub Actions `run:` blocks, never expand `${{ }}` into the script
  text; pass values through `env:` so they cannot inject into the shell.
- Validate at system boundaries. Escape output. Treat path, URL, and command
  construction as injection surfaces.

## Defects

When fixing a defect:

1. Search how the problem is actually solved — do not invent a one-off.
2. If a `defects/` (or equivalent) note exists for this issue, read it
   before retrying a failed approach.
3. After you fix it, search for every other occurrence (see "Fix all
   instances, not just one").

## Promises about future behavior

Never write "won't happen again", "I'll remember that", "next time I'll …", or
any forward-looking commitment about your own behavior **unless you have already
taken a concrete action that makes it true** — a commit to `AGENTS.md`, a hook
in `claude/settings.json`, or another durable artifact. Do not commit to
`AGENTS-SHARED.md` / `AGENTS.shared.md` to satisfy this — that file is synced
from `cirra-ai/processes` (see the canonical-source note at the top of this
file) and individual repos must not edit it. You have no persistent memory
across sessions; an unbacked promise is misleading. If the user points out a
mistake, propose the durable change explicitly and only state the commitment
after it's committed.

## Documentation

- Prefer documenting **how something works now**, **rationale for design
  choices**, and **remaining known issues/limitations**.
- Avoid **changelog-style "what changed"** in repo docs — that belongs in **PR
  descriptions** and **git history**.
- Keep notes focused on the rationale for the chosen solution. Do not document
  the full debugging history or rejected attempts unless explicitly requested.
- When you write a hand-off document make it self-contained and address it to the agent or person doing the follow up work. Do not include any references to the current or prior conversations. Provide hand-off docs as downloadable artifacts, not inline text.

## Chat response style — be concise

Default to short chat replies. For analysis / options questions, answer in this
shape: **Issue** (1-2 sentences) → **Possible fixes** (one sentence each) →
**Pros / cons** (brief) → **Recommendation** (which and why, 1 sentence). If a
topic genuinely needs more detail, expand, then end with a one-line **TLDR**.
This governs chat prose only; it does not relax the mandatory checklists,
PR-description, or evidence rules above.

## Be specific and concrete

Always provide exact names, paths, URLs, and links. Never make the user hunt
around or guess.

- **Files**: full path from repo root.
- **Branches/PRs**: include the branch name and PR number/URL.
- **Worktree / sandbox path**: if you created one, include it so the user can
  find the checkout.
- **Commands**: show the exact command, not a paraphrase.
- **Config locations**: name the exact file, dashboard URL, or UI path.
- **Error references**: quote the exact error message and the file/line.

If you are unsure of the exact path or name, say so explicitly rather than
giving a vague reference.

## Tone

Do not use the word "honest" or synonyms unless you are actually talking about honesty vs. dishonesty. You should be honest by default, you do not need to say it.

## Claude Code

This subsection is **Claude Code specific** (the CLI, Desktop app, and
claude.ai/code). The git and review rules it refers to are the same rules
above; this names the Claude Code mechanism so every agent can see it.

Claude Code reads `CLAUDE.md`, not `AGENTS.md`
([CLAUDE.md → AGENTS.md](https://code.claude.com/docs/en/claude-md#agentsmd)).
Each repo needs a **local adapter** so Claude Code loads that repo's
`AGENTS.md` (which imports this file):

```markdown
@AGENTS.md
```

or `ln -s AGENTS.md CLAUDE.md`. Create it in that repo. Do not copy a
policy `CLAUDE.md` from `cirra-ai/processes`. Put Claude-specific rules in
this subsection, not in the adapter. On Windows, use the `@AGENTS.md`
import — a symlink needs Developer Mode or Administrator
([same docs](https://code.claude.com/docs/en/claude-md#agentsmd)).

### Hooks

On a developer machine, `claude/deploy.py` in `cirra-ai/processes` installs
PreToolUse hooks at `$HOME/.claude/hooks/`. They enforce the git rules
already in this file and **reject the Bash call** when violated:

| Hook | Rejects |
| --- | --- |
| `block-force-push.sh` | `git push` with `--force`, `-f`, `--force-with-lease`, or `--force-if-includes` |
| `pre-git-push.sh` | push to a merged or closed PR; runs `git fetch` first |
| `pre-branch-create.sh` | `git worktree add` / `checkout -b` / `switch -c` without `origin/<base>` |

Do not bypass them (`--no-verify` on the hook is not a thing — they are
Claude Code PreToolUse hooks, not git hooks). Follow the git rules so the
hooks never have to fire.

These scripts are **not** present in Claude Code cloud sessions unless an
environment setup script installs them. Cloud sessions still follow the same
git rules; they just are not hook-enforced. See
[`RUNTIME-CONFIG.md`](https://github.com/cirra-ai/processes/blob/main/agents/dev/RUNTIME-CONFIG.md).

### Settings

Team permissions and plugin allowlists live in
`cirra-ai/processes/claude/settings.json` and are applied in three places:

- **Local machines:** `claude/deploy.py` unions them into
  `~/.claude/settings.json`.
- **Org-wide:** `claude/deploy.py --print-org` for
  [server-managed settings](https://code.claude.com/docs/en/server-managed-settings).
- **Each consumer repo:** the same deploy script's `--merge-project` path,
  run by `.github/workflows/sync-dev-agents.yml`, unions team allow/deny
  into that repo's `.claude/settings.json`. Repo-specific hooks and Bash
  allow rules stay. `Bash(*)` is not copied — each repo keeps its own
  Bash allowlist. Team deny rules (including Bash denials) do copy.

A gap in that allowlist is not proof a tool is missing — see "Know your
runtime surface" above.

