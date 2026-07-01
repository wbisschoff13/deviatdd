---
title: "Run Your First DeviaTDD Task"
description: "How to pick up a queued task from `specs/issues.jsonl` and drive it through the red → green → refactor micro-cycle."
doc_type: how-to
status: draft
last_verified_at: 2026-07-01
verified_sha: c533ead
related_issues: []
---

This guide walks you through picking up a queued task from the issue ledger and driving it through one full micro-cycle. Use it when you are about to write code against an existing task in `specs/**/tasks.jsonl`.

## Prerequisites

- DeviaTDD installed: `uv tool install deviatdd` (or `pipx install deviatdd`)
- The repo initialised: `deviate setup` has been run
- A queued task in `specs/**/tasks.jsonl` with `status: pending`

## Steps

1. **List the next runnable task.** Run `deviate tasks --next`. The CLI reads the most recent ledger entry whose `status` is `pending` and prints its ID plus a one-line summary.

   Expected result: one line like `ISS-042 / task-3: red — add failing test for parser.py:42` and an exit code of `0`.

2. **Open a feature worktree.** Run `deviate feature start ISS-042`. The CLI creates a worktree under `.worktrees/ISS-042/`, branches from the ledger-anchored SHA, and prints the worktree path.

   Expected result: a path like `.worktrees/ISS-042/`, a branch named `feature/ISS-042`, and a clean `git status` inside the worktree.

3. **Run the red step.** Run `deviate red --task task-3`. The micro-cycle agent writes a failing test under `tests/`, runs the test suite, and commits the failing test (the "red" commit) when the test fails for the right reason.

   Expected result: a new file under `tests/` named after the task, a pytest run that fails with the expected assertion error, and one new commit on the feature branch.

## Verification

Re-run `deviate tasks --next` from the worktree root. The task row's `status` is now `red` and a new `green` row has been pre-queued. The full micro-cycle is complete when both `red` and `green` rows show `status: done` and the `judge` row has a `verdict: pass` line.
