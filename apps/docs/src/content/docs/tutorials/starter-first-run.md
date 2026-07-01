---
title: "Run Your First DeviaTDD Cycle"
description: "A complete end-to-end walkthrough — clone, init, queue a task, run the red → green → refactor micro-cycle, and commit the result."
doc_type: tutorial
status: draft
last_verified_at: 2026-07-01
verified_sha: c533ead
related_issues: []
---

This tutorial walks you through one complete DeviaTDD cycle, from a clean checkout to a green test. It is the place to start when you have never run `deviate` before. By the end, you will have a queued task, a red commit, and a green commit on a feature branch.

## Prerequisites

- A POSIX shell (`bash` or `zsh`)
- Python 3.13, `uv` ≥ 0.4, and `git` ≥ 2.40
- 10 minutes of uninterrupted time

## Step 1 — Bootstrap a new project

Create a new repo and initialise DeviaTDD. This is the moment when C7 (Tome Setup) would also scaffold a Starlight docs site under `apps/docs/`, but for the tutorial we skip docs and focus on the task loop.

```bash
mkdir hello-deviate && cd hello-deviate
git init -b main
uv venv && source .venv/bin/activate
deviate init
```

Expected result: `specs/constitution.md`, `specs/_product/architecture.md`, `specs/issues.jsonl` all exist; `git status` is clean; the `deviate` CLI exits `0` on `--help`.

## Step 2 — Queue your first task

The Macro layer is what produces a queued task; for the tutorial, write one row directly into `specs/issues.jsonl`.

```bash
deviate tasks add --title "parse greeting" --quadrant how-to --group tdd-micro-cycle
```

Expected result: one new JSONL row with `status: pending`, a generated `ISS-001` ID, and a `layer_order: 1` value. Run `deviate tasks --next` to confirm the task is the next runnable row.

## Step 3 — Run the red → green micro-cycle

Open a worktree and drive the task through the micro-cycle.

```bash
deviate feature start ISS-001
cd .worktrees/ISS-001
deviate red --task task-1
deviate green --task task-1
```

Expected result: a failing test under `tests/`, a passing test after the green step, and two new commits on `feature/ISS-001`. The `tasks.jsonl` ledger shows `red: done` and `green: done`.

## Verification

Re-run `deviate tasks --next` from the worktree. The task row's status is `judge-pending`; running `deviate judge --task task-1` emits a verdict line (`verdict: pass`) and writes the final commit.

## Next Steps

- Read [Explanation → Architecture → Why Diátaxis](../../explanation/architecture/starter-architecture.md) to understand why the docs are split into four quadrants
- Read [Reference → Config Schema → Config Field Reference](../../reference/config/starter-config.md) to learn the frontmatter contract every page carries
- Read [How-To → Getting Started → Run Your First DeviaTDD Task](../../how-to/getting-started/starter-first-task.md) for the task-driven recipe version of this tutorial
