# Tweet Thread: Introducing DeviaTDD

*12 tweets, ready to paste as a single thread. Each is under 280 chars. Numbers in brackets are tweet numbers.*

---

**\[1/12\]**

I'm building in public with my own framework.

It's called DeviaTDD.

It's a CLI that wraps spec-driven development + TDD into a single deterministic state machine for LLM coding agents.

It's not a methodology paper. It enforces the loop.

🧵 on why spec-kit wasn't enough ↓

---

**\[2/12\]**

The premise:

LLMs are probabilistic, optimization-seeking actors.

If you hand them a spec and ask them to implement it, they will optimize for "task appears complete." They will rewrite tests. They will drift.

You don't align an optimization-seeking actor with prose. You contain it with infrastructure.

---

**\[3/12\]**

DeviaTDD is three layers, each with its own discipline:

→ Macro: scope a feature (explore → research → prd → shard)
→ Meso: engineer an issue (plan → tasks → pr)
→ Micro: TDD loop (RED → GREEN → JUDGE → REFACTOR)

Between them: 3 non-bypassable human gates.

---

**\[4/12\]**

Macro layer is where a business goal becomes structured work.

`/deviate-explore` (cheap V4 Flash) scans the codebase.
`/deviate-research` (Qwen 3.7+) produces design.md + data-model.md.
`/deviate-prd` turns design into immutable FRs.
`/deviate-shard` decomposes into vertical-slice issue files with full Gherkin AC.

---

**\[5/12\]**

After research: **Gate 1** — human approves design before PRD starts.

After shard: **Gate 2** — human approves every spec-enriched issue before per-issue planning.

These aren't prompt suggestions. They're session state transitions. No approval flag → no phase advance.

Spec errors caught here save the entire downstream cascade.

---

**\[6/12\]**

Meso layer turns an issue into an execution plan.

`/deviate-plan` does per-issue localized research — re-scans the codebase as it exists *now*, not at epic-explore time. Solves the stale-context problem.

`/deviate-tasks` decomposes into 4-8 tasks with DAG deps, mock boundaries, and execution types (tdd | direct | e2e).

---

**\[7/12\]**

Micro layer is where DeviaTDD diverges from spec-kit hardest.

Every TDD task runs a fixed state machine:

RED → GREEN → [YELLOW?] → JUDGE → REFACTOR

Every transition is an atomic git commit. Every commit message is conventional. Every phase has machine verification.

The agent can't skip phases. The CLI refuses.

---

**\[8/12\]**

The keystone is the **Tamper Guard**.

During GREEN, the agent is only granted write access to `src/**/*.py`.

If it tries to edit a test to make it pass, `git checkout HEAD -- <test_file>` reverts it before evaluation.

The framework treats test files as immutable contracts during implementation. They are.

---

**\[9/12\]**

**JUDGE** runs in an isolated V4 Pro session — no shared history, no recursive subjectivity.

It diffs the GREEN commit against `spec.md` invariants.

PASS → REFACTOR.
VIOLATION → Train rollback (`git revert --no-edit <green_sha>`), feedback injected, retry GREEN. Max 3 retries.

The framework throws bad implementations away. Precisely.

---

**\[10/12\]**

**YELLOW** is a conditional branch, not a fixed phase.

It only triggers when Tamper Guard catches test tampering during GREEN.

Then an isolated judge reviews the amendment:
- APPROVED → commit + proceed to JUDGE (rare: the test was wrong)
- REJECTED → restore + back to GREEN (common: the agent was cheating)

One place where the agent is allowed to argue with the test.

---

**\[11/12\]**

State isn't markdown files. It's **append-only JSONL ledgers**:

- `specs/issues.jsonl` — global issue registry
- `specs/{epic}/{issue}/tasks.jsonl` — task transitions

Agents can't edit status fields. Only the CLI appends.

Concurrent branches merging into `issues.jsonl` use `merge=union` via `.gitattributes`. No conflicts when two PRs each add a line.

---

**\[12/12\]**

Repo: github.com/wbisschoff13/deviatdd
Building in public starts now. Next post: cost profile of one feature shipped end-to-end.