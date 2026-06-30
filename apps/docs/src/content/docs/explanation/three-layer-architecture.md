---
title: "Why a Three-Layer Architecture"
description: "Rationale for the Macro / Meso / Micro partition of DeviaTDD's workflow — what each layer owns, what each layer rejects, and the trade-offs the boundary costs."
doc_type: explanation
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-002
  - ISS-001-003
  - ISS-001-004
  - ISS-001-005
---

# Why a Three-Layer Architecture

DeviaTDD divides every piece of work into three sequential scopes — Macro, Meso, and Micro — and binds each scope to its own model tier, its own artifact contract, and its own human-in-the-loop gate. This essay walks through the rationale for that partition, the responsibilities each layer accepts and the responsibilities it explicitly rejects, and the trade-offs the design accepts in exchange for the structural clarity it provides. The reader who finishes this page should be able to look at any new feature and predict, without consulting the spec, which layer owns which decision and where the gate between them lives.

## Context

Agentic software development is a single agentic loop only when the problem is trivial. As the artifact under construction grows — a new feature, a refactor that touches ten modules, a regulatory surface with audit requirements — the loop accumulates concerns that compete with each other. The agent that scopes the work is not the agent that should implement it; the agent that writes a passing test is not the agent that should approve a thirty-page requirement document. When a single loop carries all of those concerns, the prompt becomes a wall of caveats, the model context becomes a junk drawer, and the audit trail collapses into one undifferentiated transcript that no one can later parse to ask "where did this decision come from?"

The premise from which DeviaTDD begins is the one stated in the architecture spec's opening: LLMs are probabilistic, optimization-seeking actors, and structured infrastructure containment is what makes them reliably correct rather than what makes them trustworthy on their own. Containment takes many forms across this codebase — append-only ledgers, deterministic test verification, git-as-state-machine, the Tamper Guard that reverts unauthorized test edits before a GREEN-phase commit is evaluated, and the isolated JUDGE session that runs in zero-shared-history to break recursive subjectivity. But the most consequential form of containment is **scope isolation**: the Macro layer reads the world, the Micro layer changes the world, and the Meso layer translates between the two. Each layer has its own scope, its own artifact, its own model, its own governance point, and its own audit trail. What it does not have is the artifacts of the others — the spec belongs to the layer that produced it, and downstream layers consume only the contracts that surface them.

The choice of three layers, rather than two or four, is not arbitrary. Two layers collapse scope into a binary — design-then-build — and lose the per-issue planning granularity that catches stale research before task decomposition. Four layers add an artificial middle that the current cognitive partition does not require. Three layers happen to align with three distinct cognitive demands, three model cost profiles, and three natural HITL gate positions. The rest of this essay unpacks that alignment and the trade-offs it encodes.

## Rationale

Each layer accepts a single bounded responsibility and rejects the responsibilities that belong to its neighbors. The Macro layer owns **scope and decomposition**. It reads the codebase, decides whether a task is large enough to need a full epic workflow or small enough to route through the `/deviate-adhoc` fast-path, and emits the spec-enriched issue files that the rest of the system consumes. The Macro layer produces no code, no tests, and no configuration changes. Its artifacts are `explore.md`, `design.md`, `data-model.md`, `prd.md`, and the per-feature issue files under `specs/`. When the Macro layer finishes, the next agent has a complete contract to work from — or, in the case of the Complexity Gate's reject path, no contract at all because the task was misclassified as macro-scope when it was not.

The Meso layer owns **contracts and decomposition into units of execution**. It consumes the spec-enriched issue files produced upstream and emits `plan.md` and `tasks.md` — a per-issue research pass that catches drift since epic-level explore, and a task ledger that breaks the issue into four to eight autonomous units of execution, each with an execution type of `tdd`, `direct`, or `e2e`. The Meso layer produces no implementation, no test code, and no commits to the working tree other than the `docs(...)` artifact commits. Its artifacts are the per-issue plan, the per-issue task ledger, and the issue-level decisions about granularity and DAG ordering. When the Meso layer finishes, the next agent has a list of bounded tasks, each with a clear acceptance criterion and a clear execution type, and the dependency graph that determines which task can be claimed next.

The Micro layer owns **execution and verification**. It consumes a single task from the Meso layer's ledger, runs the RED → GREEN → [YELLOW?] → JUDGE → REFACTOR cycle against that task, and commits the result as an atomic git transaction. The Micro layer produces no specifications, no new issue files, no changes to other tasks, and no edits outside the scope of the single task it was dispatched for — RED writes only to `tests/`, GREEN writes only to `src/` or the targeted module, and the Tamper Guard reverts any unauthorized mutation the agent attempts against the test file before the test suite is evaluated. Its artifacts are the per-task commits, the per-task transitions appended to `tasks.jsonl`, and the `RollbackSnapshot` records that the JUDGE phase emits on compliance violations so the next GREEN attempt can be retrained on prior failure output. When the Micro layer finishes a task, the issue's task count has decreased by one and the system is closer to a releasable surface.

What each layer rejects is as important as what it owns. The Macro layer rejects implementation because the cheap models that do explore well are not the cheap models that should write production code; the trust boundary between "describing what to build" and "building it" deserves its own gate. The Meso layer rejects implementation for the same reason, plus a second reason: the per-issue plan needs fresh codebase context, and that context is too narrow to also be the prompt for code generation. The Micro layer rejects specification changes because the Tamper Guard and the Judge's compliance diff both assume that the spec is a fixed input to the verification step; if the Micro layer could rewrite the spec, the verification step becomes circular and the audit trail collapses. These rejections are not arbitrary policy — they are the boundaries that make the deterministic verification in the Micro layer actually deterministic.

## Mental Model

The three layers are best pictured as three nested scopes with strictly downward information flow. The Macro layer sits at the outside, the Micro layer at the inside, and the Meso layer is the translation seam between them. Work enters at the Macro layer as a problem statement, becomes a set of issue files, then enters the Meso layer as a single claimed issue, then enters the Micro layer as a single dispatched task. Each transition is a one-way write — the upstream layer commits an artifact, the downstream layer reads it. There is no feedback loop from Micro to Macro except through the human gate at Gate 3 (the final merge audit), and there is no feedback loop from Micro to Meso except through the task ledger and the per-issue pull request.

```
problem statement
       │
       ▼
┌─────────────────┐
│  MACRO          │  explore → research → prd → shard
│  scope          │  artifacts: explore/design/prd/issue files
└────────┬────────┘
         │  (HITL Gate 2)
         ▼
┌─────────────────┐
│  MESO           │  plan → tasks
│  contracts      │  artifacts: plan.md, tasks.md
└────────┬────────┘
         │  per-task dispatch
         ▼
┌─────────────────┐
│  MICRO          │  red → green → yellow? → judge → refactor
│  execution      │  artifacts: commits + ledger entries
└─────────────────┘
```

A useful secondary image is **model tier as a function of layer**. The Macro layer runs cheap models because the cognitive demand is structured lookup and design synthesis, not novel code generation; the Meso layer runs more expensive models because per-issue planning requires integrating fresh context with stale research and producing a tight execution blueprint; the Micro layer returns to cheap models for RED, GREEN, and REFACTOR and uses an isolated, expensive model only for JUDGE — the verification step that warrants the cost. The model-tier table in the architecture spec is not a budget spreadsheet; it is the operational expression of which layer is doing which kind of thinking.

## Trade-Offs

The three-layer architecture buys three things at a known cost. **What it buys:** bounded blast radius — a failure at any layer is contained to that layer's scope and does not cascade to the others, because the artifacts are immutable between layers and the gates prevent unannounced promotion. Replaceability — the model tier for a given phase is configurable via the `[models]` section of `.deviate/config.toml`, and swapping a model does not require rethinking the architecture because the artifact contracts are stable. Auditability — every transition is committed and every artifact is parseable, so a postmortem can identify exactly which layer emitted the suspect decision. **What it costs:** coordination overhead between layers, in the form of session boundaries, artifact commitments, and human checkpoints. Latency — multiple model invocations and human approvals per issue, even for trivial work where a single agent would suffice. Context handoff risk — each layer reads only what its predecessor committed, and if that commit is incomplete, downstream layers reason from a thin contract.

Three rejected alternatives are worth naming explicitly.

The **monolithic single-agent loop** was rejected. One agent reads the problem, plans the solution, writes the tests, writes the implementation, runs the verification, and commits. This is the structure of most agentic coding tools, and it is genuinely cheaper per task. DeviaTDD rejected it because the cognitive demands of "what should we build" and "does this code pass the test" do not share a model context profitably — interleaving them muddies the prompt, dilutes the audit trail, and makes HITL placement impossible. The three-layer partition forces the agent to switch contexts at layer boundaries, and that switch is what enables the per-layer governance the framework is built around.

The **pure model-tier partition** was rejected as the primary axis. Imagine routing by model alone — cheap for GREEN, smart for plan, cheap for explore — without the scope isolation, the artifact contracts, or the HITL gates that surround them. This would buy some cost savings but would lose the governance, the auditability, and the deterministic verification that the layers enable. Model tier is a *consequence* of layer responsibility, not the partition itself. The architecture spec's model routing table is a guidance layer over the three-layer structure; it is not the structure.

The **V-model** (sequential waterfall with verification only at the end) was rejected. The V-model consolidates scope decisions at one end and verification at the other, with implementation in between. The problem it does not solve — and the problem DeviaTDD's three-layer model solves explicitly — is **late defect detection**. By the time a V-model implementation reaches its verification gate, the spec errors have already been baked into twenty-five or more task implementations. DeviaTDD's Gate 1 (after research, before prd) and Gate 2 (after shard, before plan) catch spec errors cheaply, before they cascade. The three-layer architecture is, in part, a strategy for pushing verification upstream into the cheapest possible layer.

## Implications

The three-layer architecture constrains future decisions in ways that are not always comfortable. The cost of a new feature is not "one model call" but "one Macro pass, one Meso pass per issue, one Micro pass per task" — which is intentionally more expensive than a single-agent loop, because the extra cost is the auditability and the HITL gates. Anyone proposing to collapse the layers should be aware that they are also proposing to remove the gates and the artifact contracts; the savings would be real but the loss would be structural.

What becomes easier with the partition: **scope containment** — a bug in a Micro-layer implementation cannot leak into the spec that produced it, because the spec is already committed and immutable. **Cost control** — model tier is per-phase and configurable, so the operator can swap a cheaper model for an exploratory phase without touching the verification phase. **HITL placement** — gates live at natural seams (after research, after shard, before merge), not at arbitrary checkpoints. **Incremental rollouts** — each layer can be swapped or upgraded without re-architecting the others, which is why the Pi agent backend could be integrated for the Micro layer without disturbing the Macro layer's slash-command surface. **Postmortem analysis** — a failed issue points at one of three layers unambiguously, and the per-task ledger entries let the operator reconstruct exactly which commit, which transition, and which rationale produced the failure.

What becomes harder: **end-to-end velocity** — the slowest tier sets the floor, and a slow Macro explore blocks every downstream layer. **Cross-layer context** — a research artifact in the Macro layer may go stale before the Meso layer's plan phase consumes it; the per-issue plan phase is the explicit mitigation, but it is itself a cost. **Failure debugging across boundaries** — a JUDGE rejection looks like a Micro-layer failure but may trace back to a Meso-layer task or a Macro-layer spec, and the operator has to follow the artifact chain backwards to find the real cause. **Onboarding cost** — a new contributor must understand all three layers before they can productively change any one of them, because each layer's invariants are defined relative to its neighbors.

The framework explicitly rejects the premise of an autonomous, closed-loop software factory. The three-layer architecture is the structural embodiment of that rejection: every layer's most consequential decisions are upstream of a human checkpoint, and the human is not optional.

## See Also

- [Tutorials: a guided tour](/tutorials/intro) — beginner walkthroughs that build context before this explanation.
- [Run the /deviate-explore phase](/how-to/explore) — exercises the Macro layer's read-only scan.
- [Run the /deviate-research phase](/how-to/research) — exercises the Macro layer's design synthesis, ending at HITL Gate 1.
- [Run the /deviate-shard phase](/how-to/shard) — exercises the Macro layer's spec-enriched issue decomposition, ending at HITL Gate 2.
- [Run the /deviate-tasks phase](/how-to/tasks) — exercises the Meso layer's per-issue execution blueprint.
- [Run the /deviate-red phase](/how-to/red) — exercises the Micro layer's RED step, where the Tamper Guard begins to govern write scope.
- [Run the /deviate-judge phase](/how-to/judge) — exercises the Micro layer's isolated compliance verification and the Green → Judge → Green train loop.
- [Slash Commands](/reference/slash-commands) — the inventory of every slash command mapped to its layer via `src/deviate/prompts/assembly.py::_LAYER_MAP`.
- [Phase State Machine](/reference/phase-state-machine) — the valid `SessionState.current_phase` values and the per-phase artifact map that makes the layer transitions inspectable.
- [Why Append-Only Ledgers](/explanation/append-only-ledger) — the ledgers that the three layers produce and consume; the architecture's data plane.
