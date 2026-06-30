---
title: "Why Three Non-Bypassable Human Gates"
description: "How Gate 1, Gate 2, and Gate 3 lock the macro-meso-micro pipeline against autonomous drift — and why no --force can open them."
doc_type: explanation
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Why Three Non-Bypassable Human Gates

A self-driving LLM pipeline has a specific failure mode: when every phase is autonomous, no one is in the loop at the moment a decision becomes irreversible. By the time a wrong design choice becomes visible, it has been PRD-compiled, sharded across dozens of issues, planned, task-decomposed, micro-implemented, and committed to history. The cost of a wrong call grows roughly quadratically with how late it is caught. DeviaTDD's answer is three non-bypassable checkpoints where a human must explicitly sign off before the next phase can begin — and a constitution-level commitment that no CLI flag, no role-based shortcut, and no automation workaround can open those checkpoints from the script side. This page is about why those three checkpoints exist, where they sit in the pipeline, what they each protect, and what the framework pays for the guarantee they provide.

## Context

The constitution names HITL as one of seven architectural principles and then hedges it more carefully than any other: "Three mandatory gates (Design Approval after research, Contract Sign-Off after shard, Final Merge Audit after micro) prevent autonomous drift. No gate may be programmatically bypassed." The phrasing is deliberate. The session state machine has its own monotonic ordering (`_MACRO_TRANSITION_MAP`, `force_transition_to()`), the Tamper Guard has rollback semantics that roll a micro task back to the RED boundary on unauthorized edits, the append-only ledger has compound-key idempotency to keep `issues.jsonl` and `tasks.jsonl` consistent across branches. Each of those mechanisms has a knob for fine-tuning — `--force` bypasses phase validation, `--no-judge` and `--no-refactor` compose profile overrides, `--fast` skips the polish cycle. The HITL gates are the one mechanism that has no knob, because the gates exist precisely to prevent a knob from looking like "approval."

The historical motivation is the cost gradient described in `specs/DeviaTDD-architecture.md` §9.4: a design error caught at Gate 1 saves all the work that would otherwise flow through PRD, shard, plan, tasks, and every per-task RED → GREEN → JUDGE → REFACTOR cycle. A spec error caught at Gate 2 saves all per-issue planning, task decomposition, and Micro cycles. Each gate is a cheap human check — minutes of read-time against an artifact — that prevents expensive LLM-driven work downstream. The framework trades velocity inside a phase for correctness at the boundary between phases. The constitution's "Not an Autonomous, Closed-Loop Software Factory" exclusion makes the same trade-off explicit: DeviaTDD is anchored on structured HITL specification boundaries and contract alignment gates, and that anchor is non-negotiable.

## Rationale

The decision rests on three claims that stack on each other. First, *errors propagate multiplicatively, not additively.* A wrong architectural choice in `design.md` does not just delay one phase — it propagates into every Functional Requirement in the PRD, every sharded issue, every task, and every micro cycle that consumes those tasks. The amount of downstream work shielded by an early human review is a function of how many tasks the shard produces, which for a meaningful feature is "dozens." A wrong spec at Gate 2 costs the same kind of downstream cascade because `deviate plan` and `deviate tasks` consume the spec-enriched issue files without re-litigating scope. A wrong implementation at Gate 3 costs only the recovery work, which is the smallest of the three — and that asymmetry is the entire reason Gate 3 exists, not because audits are fun but because catching errors at their cheapest moment is the entire point of the pipeline.

Second, *a person reviewing is functionally different from a check that passed*. The ledger has tooling that scans for "every Functional Requirement has Gherkin acceptance criteria." That check passes when the criteria are present, regardless of whether they are correct. A human reviewer who reads the criteria brings judgment about whether they describe the *actual* behavior the user wanted, not the nominal behavior that was easy to specify. Tooling cannot substitute for judgment, and the framework does not pretend it can. The HITL gate is the slot where judgment enters the system.

Third, *the gates are non-bypassable specifically because they need to be observable as non-bypassable*. If `--force` opened Gate 1 the way it opens session-phase validation, then any audit of "did this repo go through HITL?" would have to inspect every flag-passed-to-CLI ever issued. By making the gate non-bypassable at the script layer, the audit question collapses to a structural check: "does `design.md`'s `## Pending HITL Decisions` table have any `Status: PENDING` rows at the moment PRD ran?" That question is a single ledger-aware predicate in `_check_pending_hitl_decisions()` (`src/deviate/cli/macro.py:425`), and the answer is durable in git. The non-bypass is what makes the audit cheap.

## Mental Model

Picture the pipeline as a one-way flow with three checkpoints that physically cannot be skipped. Each checkpoint waits for a human signature before opening the next segment. The gates are not arguments to the upstream phase; they are predicates that *block* the downstream phase. The implementation pattern is identical at every gate: a pre-script scans for a structural invariant (zero PENDING rows in the Gate 1 table, each shard reviewed in the Gate 2 review record, all tasks at terminal status for Gate 3), and halts with a named message if the invariant is not satisfied.

```
   ┌──────────────────── MACRO LAYER ────────────────────┐
   │                                                    │
   │  /explore → /research ───[GATE 1]───→ /prd → /shard│
   │                              │ ▲                   │
   │                  zero PENDING rows                 │
   │                  in design.md's                    │
   │                  Pending HITL                      │
   │                  Decisions table                   │
   │                                                    │
   ├──────────────────── MESO LAYER ─────────────────────┤
   │                                                    │
   │                ─────[GATE 2]───→ /plan → /tasks    │
   │                       │ ▲                         │
   │             human review of every                  │
   │             shard issue (scope,                    │
   │             edge cases, Gherkin                    │
   │             AC, vertical-slice                     │
   │             integrity)                            │
   │                                                    │
   ├──────────────────── MICRO LAYER ────────────────────┤
   │                                                    │
   │  RED → GREEN → JUDGE → REFACTOR ─[GATE 3]→ /review │
   │                                          │ ▲      │
   │                              atomic git history,   │
   │                              tests, constitution   │
   │                              drift, PRD alignment  │
   │                              reviewed before merge │
   └────────────────────────────────────────────────────┘
```

The `--force` flag still exists at every phase and is genuinely useful — it bypasses *session-phase validation* (accepting a session in the wrong phase after a manual recovery or skill re-installation), but it does *not* bypass HITL decisions. The distinction is precise: force handles *amnesia* (the session forgot which phase it's in); HITL handles *judgment* (a human looked at the artifact and signed off). Conflating the two is the failure mode the design prevents.

## Gate 1 — Blueprint Approval

### Context

Gate 1 sits between Macro research and Macro PRD. It triggers when the `/deviate-research` slash command has produced both `design.md` and `data-model.md` — the two artifacts that crystallize architectural decisions and data shapes. Before Gate 1, the architectural surface is open to amendment at near-zero cost. After Gate 1, the PRD compiler will read the design and data model and emit Functional Requirements, AC tokens, and a Gherkin behavior contract; downstream work cannot easily undo a decision baked into those tokens.

### Rationale

The gate's mechanism is a single table — `## Pending HITL Decisions` — at the bottom of `design.md`. The research prompt (`src/deviate/prompts/commands/deviate-research.md`) is required to populate that table with every decision that *reverses or deviates from the explore brief*, *rejects a tool or approach explicitly requested during explore*, *introduces architectural changes not anticipated in explore*, or *otherwise requires human judgment*. If no such decisions exist, the table is empty (header + metadata only). `_check_pending_hitl_decisions()` in `src/deviate/cli/macro.py:425` reads the table line-by-line, returns any row where `Status: PENDING`, and the `deviate prd pre` command halts with `HITL GATE 1 — UNRESOLVED DECISIONS` if the list is non-empty. The PRD compiler cannot run until every row is `RESOLVED`. The question-budget rule allows the research agent at most four targeted clarity questions per interaction, so the operator's review is informed rather than guessing.

### Trade-offs

What the gate costs is time — the operator must read `design.md` and answer each pending decision. For a feature where the research agent and the operator already share context (a small greenfield change), this is friction. For a feature where research introduced a non-obvious architectural choice (cache layer where none was requested, dependency swap, schema change), this is the only opportunity to push back before the PRD is written. The asymmetry is the point.

## Gate 2 — Contract Sign-Off

### Context

Gate 2 sits between Meso shard and Meso plan. It triggers when `/deviate-shard` has produced the spec-enriched issue files (`specs/{feature}/issues/{ISS-NNN}-*.md`) containing user stories, Gherkin acceptance criteria, edge cases, and the DAG topology that downstream planning and task decomposition consume. The architecture doc explicitly calls Gate 2 the *primary* gate, and the rationale ("Spec errors are the most expensive to fix downstream") is concrete: a task entry in `tasks.jsonl` is cheap to regenerate — roughly thirty seconds per row — but a mis-specified issue cascades through every plan, every task, and every micro cycle that consumes those tasks. For a feature shard that produces fifteen to thirty tasks, the cost multiplier is the same order as the task count.

### Rationale

The gate's surface is the shard review itself — the human reads each issue file and confirms three properties: vertical-slice integrity (the issue is end-to-end functional, not a thin horizontal slice through the codebase), edge case coverage (the listed edges and failure modes are exhaustive), and architectural alignment (the issue respects the data model and design that Gate 1 approved). The shard post-script (`deviate shard post`) cannot commit the issues to `specs/issues.jsonl` until the review record shows every issue was signed off. Mechanically this is the same pattern as Gate 1 — a structural predicate that a script reads at phase entry — but the predicate is satisfied by a deliberate human action (`Status: REVIEWED` on each issue row in a review ledger), not by a search-and-resolve on a single table. Gate 2 also absorbs an opt-in Gate 2b for complex features (more than seven issues or highly interdependent tasks): after `/deviate-tasks`, the human can review task granularity, DAG dependencies, and implementation hints. Standard features skip 2b.

### Trade-offs

What the gate costs is the most human time of the three — a comprehensive review of every sharded issue, not a focused table scan. For a feature with three trivial issues this is overkill. The framework's answer is "gate the expensive review at the boundary it is most protective": Gate 2 is mandatory because shard is the only phase where the spec contract is finalized; by Gate 3 it is locked into tasks; by Gate 1 it is not yet concrete enough to review. The mandatory-but-bounded cost is what keeps Gate 2 from degrading into a rubber-stamp ritual.

## Gate 3 — Final Merge Audit

### Context

Gate 3 sits at the boundary between successful Micro execution and production deployment. It triggers when every task entry in every issue-scoped `tasks.jsonl` ledger has reached a terminal state (`COMPLETED` or `FAILED`) and every DAG dependency is satisfied — the moment where the constituent work is "done" but the branch is not yet merged. The architecture doc frames this as the "Final Merge Audit"; the how-to reality is that it is executed by the `/deviate-review` slash command, which runs a single-pass V4 Flash scan over the merged diff between the branch and main, looking for ledger integrity issues, cross-task consistency, security surface drift, constitutional alignment, and PRD alignment, then surfaces its findings as a structured chat report.

### Rationale

The gate's purpose is the inverse of Gates 1 and 2. Gates 1 and 2 catch errors *before* expensive work runs. Gate 3 audits the work *after* it has run and confirms that the resulting commit history is safe to merge. The atomic-commit discipline at every phase boundary (`test: [{scope}]: RED phase`, `feat: [{scope}]: GREEN phase`, `refactor({scope}): REFACTOR phase`, see `_commit_phase()` in `src/deviate/cli/micro.py`) makes the audit cheap: `git log` on the branch is the journal; the review agent reads it instead of building narrative from scratch. The review is intentionally surfaced as chat text rather than auto-committed as a report file, because the gate's output is a human decision ("merge now", "request changes", "back out a task") and human decisions should not be auto-baked into the branch.

### Trade-offs

The gate's cost is mostly operational: every feature branch requires a human run of `/deviate-review` before `/deviate-pr` will surface, and the review's V4 Flash single-pass scan takes seconds to read but the human decision-making around it can take longer. The flip side is that bugs caught at this boundary — a constitutional clause drifted out of sync, a security surface exposed by a task, a missed PRD requirement — are caught at the cheapest possible recovery cost, which is only the work of the offending task, not the work of every downstream consumer of that task's interface.

## Trade-offs

The framework rejects four alternatives in this space, and they are worth naming because each represents a tempting shortcut that other agent frameworks have taken.

- **Allowing `--force` to bypass HITL decisions** is rejected by the constitution's "No gate may be programmatically bypassed" rule, because the auditability of "did this branch pass HITL?" collapses to a flag-passed audit if force opens the gates. `--force` still exists for session-phase validation (recovery scenarios where the session state machine lost track), and that is precisely where it belongs.
- **Delegating approval to a role-based system** (e.g., "any tech lead can approve Gate 2") is rejected because it solves an accountability problem the gates do not have: at this codebase's scale, the workflow's bottleneck is the review itself, not the authorization to review. Adding role checks would slow things down without making the gate stronger.
- **Auto-approving with an AI reviewer** is explicitly rejected by the architecture doc's "Not an Autonomous, Closed-Loop Software Factory" exclusion. The gate's purpose is to bring *human judgment* into a system that otherwise runs on LLM judgment, and replacing the human reviewer with another LLM is a category error.
- **Running gates only in interactive mode** (skip them on CI / headless runs) is rejected because the gates are the structural invariant that makes the framework trustworthy on a per-branch basis. CI invocations must also satisfy the gates; the way to make CI work is to have a human sign off in the chat surface first, not to disable the check for non-interactive runs.

What the framework pays for these rejections is operational: a contributor cannot land code without an interactive chat session where the artifacts are reviewed. That is the intended trade-off. The speedup-of-autonomy is given up; the latency-of-attention is spent.

## Implications


The non-bypass design constrains future evolution in three concrete ways. First, any new phase that the framework adds must either be inside an existing HITL-protected segment (no new gate needed) or come with its own gate; "we'll bypass this one for now" is not in the design space. Second, the droid and opencode backends — which would otherwise be candidates for unattended background runs — must preserve the gate semantics at the chat-tool boundary; a backend that "runs to completion without pausing" cannot ship as a HITL-preserving option until it implements the four-questions-then-halt pattern that the question-budget rule enforces. Third, tooling that wants to verify "did this branch pass Gate N?" must do so by reading the ledger and the design/shard review records, not by trusting a CI flag or a branch-protection rule, because the framework's structural invariant is what makes the gate trustworthy. Any audit tooling that reads from a different source of truth will eventually disagree with the ledger.

What becomes easier: parallel branches where each branch can be evaluated for HITL compliance independently (the structural predicates are branch-local), an audit log that is the git history of the artifact files, and a contributor onboarding story where the gates are the only place a new contributor must learn the framework's terminology before they can ship. What becomes harder: any future feature that wants to make LLM-driven decisions *between* gates is forced to either surface those decisions as Gate-N-½ candidates (adopting the non-bypass discipline) or to justify their exemption in the constitution itself; neither is a fast path.

## See Also

- [How to run /deviate-research](/how-to/research) — the prerequisite phase whose `## Pending HITL Decisions` table is the *Gate 1* surface; the gate is enforced at `deviate prd pre` via `_check_pending_hitl_decisions`.
- [How to run /deviate-shard](/how-to/shard) — the phase whose output triggers Gate 2; the shard review step in step 6 *is* Gate 2 in operator terms.
- [How to run /deviate-review](/how-to/review) — Gate 3 in operator terms; runs `deviate review pre` and surfaces findings as chat text.
- [Reference: phase state machine](/reference/phase-state-machine) — the `AWAITING_HITL_GATE_1` and similar session states that name which gate is currently blocking forward progress.
- [Why Append-Only Ledgers](/explanation/append-only-ledger) — the adjacent architectural principle; HITL gates and the ledger protocol are paired (the gate is verified by ledger-aware predicates, the ledger is trusted because tampering is auditable).
