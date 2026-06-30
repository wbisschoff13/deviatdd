---
title: "Open the PR for the active worktree"
description: "Run /deviate-pr — the final meso-layer gate that creates a GitHub PR from the active issue's worktree, appends COMPLETED to specs/issues.jsonl, and unblocks dependents."
doc_type: how-to
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-002
---

# Open the PR for the active worktree

This how-to covers `/deviate-pr` — the final gate of the meso layer that turns an in-progress issue branch into a GitHub pull request and, on successful creation, records a `COMPLETED` event in the append-only ledger at `specs/issues.jsonl` (`src/deviate/cli/meso.py::pr`, lines 1669-1687; prompt template at `src/deviate/prompts/commands/deviate-pr.md`). The slash command runs after [`/deviate-tasks`](/how-to/tasks) has staged every TDD task in `tasks.md` and after every Red-Green-Refactor loop has landed its commits on the per-issue worktree branch — i.e. the work is done locally and ready to ship. The ledger update is the load-bearing side effect: once `COMPLETED` is appended, the existing `blocked_by` logic (`specs/issues.jsonl` `merge=union` driver, seeded by `deviate setup`) natively unblocks every dependent issue for the next round of `deviate meso run`.

The slash command is slash-command-driven — the reader does **not** type `deviate pr pre` / `deviate pr run` as primary actions. They run `/deviate-pr`, which orchestrates both phases internally; CLI invocations appear only as verification actions (re-running the pre-script to inspect the JSON contract, or checking ledger/branch state).

## Prerequisites

- **`/deviate-tasks` completed and every TDD loop merged** — the slash command expects a clean, pushable branch whose commit log already encodes the work from `tasks.md`. `_pr_pre` reads the active session's `active_issue_id` (`src/deviate/cli/meso.py:1042-1052`), resolves the issue record in the ledger, and inspects `git log <base>..HEAD --oneline` and `git diff <base>...HEAD --stat` — if the branch is empty or the diff is meaningless (e.g. nothing was committed), the JSON contract will surface that and the slash command halts.
- **An active session with `current_phase` ∈ {`TASKS`, `IDLE`} and an `active_issue_id`** — `_load_session_accept()` (`src/deviate/cli/meso.py:1042`, `src/deviate/cli/meso.py:1225`) accepts those two phases only. If the session has reset to `IDLE` between tasks and PR, the issue is still claimable through `deviate meso run --issue <ISS-NNN-NNN>`, but for the PR phase the agent must first re-anchor `active_issue_id` — easiest path is to run `deviate tasks post` against the same issue (no-op if already committed) to surface `active_issue_id` again, or pass `--force` to the slash command to bypass the phase gate.
- **GitHub CLI (`gh`) on `PATH` and authenticated** — `_run_gh_pr_create` (`src/deviate/cli/meso.py:1198-1217`) shells out to `gh pr create`. When Graphite is configured (`graphite = true` in `.deviate/config.toml`), `_run_gt_submit` (`src/deviate/cli/meso.py:1137-1158`) shells out to `gt submit --stack --no-edit` instead and `gh` is only used by `_update_gt_prs` (`src/deviate/cli/meso.py:1162-1195`) to amend the PR title/body post-submit. Either tool is acceptable; missing both halts the run with `GT_SUBMIT_FAILED` or `PR_CREATE_FAILED`.
- **Push access to the upstream remote** — `_pr_run` runs `git push -u origin HEAD` (`src/deviate/cli/meso.py:1298-1315`) before invoking `gh pr create` / `gt submit`. If the branch has no upstream yet, the push creates it; if the branch has been deleted on the remote (e.g. a previous merge), `_pr_run` swallows the `BRANCH_DELETED` warning and continues.
- **A working tree with the PR body file staged or writeable** — the slash command generates `pr_descriptions/<branch>.md` and writes it to disk (`src/deviate/prompts/commands/deviate-pr.md` execution step 2). If the file path is read-only or the directory does not exist, the slash command fails before calling `deviate pr run`. Generate the body in a normal worktree, not a CI sandbox that strips write access.
- **`specs/constitution.md` matching the active repository** — soft requirement; only needed if your `deviate.toml` references constitution-derived merge rules. The slash command reads from the worktree's `specs/` directory, so a constitution that was edited on a different branch but not merged back will silently be missing — re-anchor before running `/deviate-pr` if the workflow depends on it.

## Steps

### 1. Confirm the active issue, the worktree, and the base branch

Before invoking the slash command, verify the three pieces of state that `_pr_pre` reads: the session's `active_issue_id`, the current worktree branch, and the diff against the base branch. The pre-script halts with `NO_ACTIVE_ISSUE` or `ISSUE_NOT_FOUND` if either is wrong (`src/deviate/cli/meso.py:1045-1052`), and a manual pre-flight catches these faster than a slash-command round-trip.

```bash
# Session has an active issue; if missing, advance via `deviate tasks post` or pass --force
cat .deviate/session.json | python -c "import json,sys; s=json.load(sys.stdin); print('issue:', s.get('active_issue_id')); print('phase:', s.get('current_phase'))"

# Issue is registered in the ledger and still in_progress (not yet COMPLETED)
jq -r 'select(.issue_id=="ISS-NNN-NNN") | {status: .status, source_file: .source_file, blocked_by: .blocked_by}' specs/issues.jsonl

# cwd is the per-issue worktree branch, not the orchestrator root
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD

# Base branch exists locally and is reachable from HEAD
git rev-parse --verify main
git log --oneline main..HEAD | head
```

If the `active_issue_id` does not match the ledger row you intend to ship, halt and re-run `deviate tasks post --issue <ISS-NNN-NNN>` against the right issue (or close the worktree and run `deviate meso run --issue <ISS-NNN-NNN>` to re-anchor).

### 2. Inspect the pre-script's JSON contract on demand

`/deviate-pr` runs the pre-script internally before any PR-side effects. If you want to inspect the contract that drives body generation — branch, base, commit titles, changed files, diff summary, derived PR title and body — invoke `deviate pr pre` directly. The contract is the same one the slash command reads; if the contract looks wrong, fix it before step 3.

```bash
deviate pr pre
```

Expected output (abridged):

```json
{
  "status": "READY",
  "phase": "pr_pre",
  "issue_id": "ISS-001-002",
  "branch_name": "feat/001-tome-docs/tome-write-how-to",
  "base_branch": "main",
  "pr_title": "feat(ISS-001-002): Tome write how-to subsystem",
  "pr_body": "## Summary\n...",
  "issue_title": "Tome write how-to subsystem",
  "commit_titles": "feat(ISS-001-002): add writer skeleton|docs(ISS-001-002): seed how-to quadrant",
  "changed_files": "apps/docs/src/content/docs/how-to/pr.md,src/deviate/tome/writers/how_to.py",
  "diff_summary": "2 files changed, 184 insertions(+), 12 deletions(-)"
}
```

If the contract reports `status: FAILURE` or any field is empty, the slash command will halt — do not proceed to step 3 until the contract is `READY` with non-empty `commit_titles`, `changed_files`, and `pr_body`.

### 3. Generate the PR body via the slash command

Run the slash command with the same problem statement (or epic slug) you threaded through `/deviate-explore` → `/deviate-research` → `/deviate-prd` → `/deviate-shard` → `/deviate-plan` → `/deviate-tasks`. The orchestrator reads the contract from step 2, drafts the PR body per the `<pr_body_format>` block (`src/deviate/prompts/commands/deviate-pr.md`: Summary → Changes → Closes), commits the body to `pr_descriptions/<branch>.md`, and pushes the commit. It then prompts the stakeholder with the HITL confirmation question.

```bash
/deviate-pr <your-problem-statement>
```

If you know the issue ID and want to skip auto-discovery (the slash command picks the session's `active_issue_id` by default):

```bash
/deviate-pr --issue ISS-NNN-NNN <your-problem-statement>
```

The HITL prompt offers two outcomes depending on whether a PR already exists on the branch:

- **No PR yet** — "Create PR for issue {issue_id} on branch {branch_name}?" plus the generated body for review.
- **PR exists** — "PR #{number} exists. Merge and mark issue COMPLETED?"

Approve the creation; the slash command writes the body file and queues step 4.

### 4. Run the run-script to create (and optionally merge) the PR

After HITL approval, the slash command invokes `deviate pr run` with the generated body file. You can invoke the same script directly to drive creation without the slash command's pre-script and HITL framing — useful for re-runs after a body edit or for CI scenarios where HITL has been pre-resolved.

```bash
# Create only (do not merge)
deviate pr run --body-file pr_descriptions/feat-001-tome-docs-tome-write-how-to.md

# Create and merge immediately (requires merge permission on the remote)
deviate pr run --body-file pr_descriptions/feat-001-tome-docs-tome-write-how-to.md --merge

# Create and enable auto-merge on GitHub (PR merges once required checks pass)
deviate pr run --body-file pr_descriptions/feat-001-tome-docs-tome-write-how-to.md --auto-merge
```

The run-script executes five side effects in order (`src/deviate/cli/meso.py::_pr_run`, lines 1220-1328):

1. **Append `COMPLETED` transition to `specs/issues.jsonl`** via `append_issue_transition()`. Idempotent — re-running emits `LEDGER_IDEMPOTENT` if the transition already exists. The append is the load-bearing unblock: every dependent issue whose `blocked_by` list references this `ISS-NNN-NNN` becomes claimable on the next `deviate meso run`.
2. **Stage the ledger and body file, commit with `--no-verify`** as `chore(<issue_id>): mark COMPLETED in ledger`. `--no-verify` is required because the ledger append is mechanical and must not be blocked by upstream hooks.
3. **`git push -u origin HEAD`** to publish the branch.
4. **Invoke `gh pr create` / `gt submit`** depending on `.deviate/config.toml`'s `graphite` setting. For Graphite, `--merge` and `--auto-merge` flags are ignored (`GRAPHITE_MERGE_FLAGS_IGNORED` warning) — Graphite manages the merge flow via `gt submit --stack`.
5. **Save session** at `TASKS` (the next phase boundary).

### 5. Verify the PR, the ledger, and the dependent unblock

Confirm every side effect landed. This is the verification step — every failure mode in troubleshooting below surfaces here first.

```bash
# 1. PR exists on the remote and was created (or merged) by the run
gh pr view --json number,url,state,mergedAt,mergeCommit \
  --jq '{n: .number, url: .url, state: .state, merged: .mergedAt, sha: .mergeCommit.oid}'

# 2. Branch was pushed upstream
git ls-remote --heads origin "$(git rev-parse --abbrev-ref HEAD)"

# 3. Ledger records the COMPLETED transition (the most recent row for this issue)
grep '"ISS-NNN-NNN"' specs/issues.jsonl | tail -1
jq -r 'select(.issue_id=="ISS-NNN-NNN") | {status: .status, ts: .timestamp}' specs/issues.jsonl | tail -1

# 4. Ledger commit is on HEAD
git log --oneline -2

# 5. Dependent issues are now unblocked (none should list this issue_id in their remaining blockers)
for dep in $(jq -r 'select(.blocked_by[]? == "ISS-NNN-NNN") | .issue_id' specs/issues.jsonl); do
  echo "$dep: $(jq -r "select(.issue_id==\"$dep\") | .status" specs/issues.jsonl)"
done

# 6. Session advanced to TASKS (the post-run phase boundary)
cat .deviate/session.json | python -c "import json,sys; print(json.load(sys.stdin)['current_phase'])"
```

Expected: PR `state: OPEN` (or `MERGED` if `--merge` was passed), branch on remote, ledger row with `status: COMPLETED` and a recent `timestamp`, the `chore(...)` commit on HEAD, every dependent issue either `BACKLOG` or already in flight (no dependents stuck `IN_PROGRESS` waiting on this one), session phase `TASKS`.

## Troubleshooting

### Pre-script returns `NO_ACTIVE_ISSUE` or `ISSUE_NOT_FOUND`

The session has no `active_issue_id` (post-`meso run` it has reset to `IDLE`), or the id is set but the issue row is missing from `specs/issues.jsonl`. Re-anchor the session by running `deviate tasks post --issue <ISS-NNN-NNN>` against the issue you want to ship, or open the worktree and re-run `deviate meso run --issue <ISS-NNN-NNN>` to drive the session through `TASKS` again. If the issue row is genuinely missing (someone force-deleted a ledger line), recover from `git log -p specs/issues.jsonl` and append the row back manually — `append_issue_transition()` is idempotent.

### Pre-script reports empty `commit_titles` or `diff_summary`

The branch is empty against the base branch — either the work landed on a different branch, the base is wrong (`_derive_pr_metadata` defaults to `main` but your repo may use `master`), or the commits were squashed/amended away. Confirm with `git log main..HEAD --oneline`; if HEAD and `main` have identical tree, your work is not on this branch and you must `git cherry-pick` it back or rerun `deviate meso run --issue <ISS-NNN-NNN>` from a clean state. If `main` is the wrong base, set the project's default branch in `.deviate/config.toml` and re-run `deviate pr pre`.

### Run-script halts with `MISSING_BODY_FILE`

`deviate pr run` was invoked without `--body-file`, or the body file path was deleted between step 3 and step 4. Re-run step 3 to regenerate `pr_descriptions/<branch>.md`, then re-invoke `deviate pr run --body-file <path>`. The slash command always passes a body file because the pre-script writes one; only direct CLI invocations hit this halt.

### Run-script reports `PR_CREATE_FAILED` with `gh pr create` output

`gh` failed to create the PR — common causes: `gh` not authenticated (`gh auth status` to check), branch already has an open PR (use `gh pr edit` to update, or close the stale PR and re-run), or the remote rejected the push (branch protection on `main` blocking force-pushes, or the repo is archived). The pre-script's `gh pr view` is a faster way to detect the "PR already exists" case than re-running `pr create`.

### Run-script reports `GT_SUBMIT_FAILED`

Graphite is configured (`graphite = true`) but `gt` is either missing or the submit failed. Install from <https://graphite.dev/docs/cli>, then verify `gt stack` shows the branch in the expected position. If `gt submit --stack` keeps failing on merge conflicts, rebase against `main` (`gt rebase main`) and re-run `deviate pr run`.

### `--merge` or `--auto-merge` silently ignored with `GRAPHITE_MERGE_FLAGS_IGNORED`

This is the expected behavior when Graphite is configured (`src/deviate/cli/meso.py:1318-1323`) — Graphite handles the merge flow via `gt submit --stack`, and the explicit merge flags are no-ops. If you wanted `gh pr create --auto-merge`, set `graphite = false` in `.deviate/config.toml` or merge manually with `gt merge`.

### Ledger commit fails with `COMMIT_LEDGER_WARN` but the PR still creates

`_pr_run` continues after the ledger-commit warning because the COMPLETED transition was already appended to the file (the append happens before the commit). The PR creation and the merge unblock proceed; only the bookkeeping commit failed (typically because a pre-commit hook blocks the staged state, or `git config user.email` is unset). If you want the bookkeeping commit on the branch, run `git commit --no-verify -m "chore(ISS-NNN-NNN): mark COMPLETED in ledger"` manually after the PR is created.

### Dependent issues still list `ISS-NNN-NNN` in their `blocked_by` after merge

The `blocked_by` list is read-only — the framework does not auto-strip completed blockers. `select_unblocked_candidates()` (`src/deviate/cli/meso.py:_discover_claimable_issue`) walks `blocked_by` and checks `_is_issue_completed()` for each, so dependents become claimable even though the strings remain. If a dependent still does not surface as claimable, run `jq -r 'select(.issue_id=="ISS-DEP") | .status, .blocked_by' specs/issues.jsonl` and confirm the dep's own status is `BACKLOG` or `IN_PROGRESS`, not `COMPLETED`.

## Next Steps

- [How to run /deviate-tasks](/how-to/tasks) — the prerequisite phase; PR runs after every TDD task on the per-issue worktree has landed.
- [How to run /deviate-shard](/how-to/shard) — the macro phase that registered the issue in `specs/issues.jsonl`; the PR phase appends the `COMPLETED` transition back into the same ledger.
- [Reference: Slash Commands](/reference/slash-commands) — the inventory entry for `deviate-pr`, including its aliases (`pr`, `/deviate-pr`, `tools:pr`) and `deviatdd-meso-layer` category.
- [Explanation: append-only ledger discipline](/explanation/append-only-ledger) — why `specs/issues.jsonl` is append-only with a `merge=union` driver and how the `COMPLETED` transition unblocks dependents without rewriting the `blocked_by` arrays.