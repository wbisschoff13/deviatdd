---
title: "Explanations: understanding the why"
description: "Design rationale, mental models, and trade-offs behind DeviaTDD's architecture, data model, and process choices — for readers who already know how to use the system."
doc_type: explanation
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-011
---

# Explanations: understanding the why

This quadrant is for readers who are comfortable with DeviaTDD — you have completed at least one tutorial and a few how-tos — and are now asking *why* the system is shaped the way it is. The pages here discuss rationale, mental models, and the trade-offs behind architectural decisions. They are discursive rather than actionable: no step-by-step instructions, no flag tables, no learning narrative. If you want to *do* something, link out to a how-to; if you want to *look something up*, link out to reference; if you want to *learn the system from scratch*, link out to a tutorial.

## Reading order

Explanations are independent essays — there is no required sequence. The suggested starting points are the architecture and data-model pieces, which ground the phase-design and process explanations:
1. [How the Tome Subsystem Emerges](/explanation/tome-subsystem) — why documentation is curated by a seven-component subsystem (C1..C7) across seven flows (FLOW-04..FLOW-10), with strict quadrant discipline, a prompt-only v1, and a frontmatter schema declared in two places; read first if you want context for how the docs themselves are produced.
2. [Why Append-Only Ledgers](/explanation/append-only-ledger) — how `specs/issues.jsonl` and `specs/**/tasks.jsonl` survive concurrent feature branches via git's `merge=union` driver, and what is given up in exchange for the no-database runtime.
3. [Why a Python-Only Prompt Runtime](/explanation/python-only-architecture) — slash commands are Python package resources loaded via `importlib.resources`, agent platforms receive a generated read-only mirror, and every `mise run` dispatch flows through `uv run`; the cost is that prompts and code share a single release.
4. [Why Three Non-Bypassable Human Gates](/explanation/hitl-gates) — the constitution-level rule that Gate 1 (Blueprint), Gate 2 (Contract Sign-Off), and Gate 3 (Final Merge Audit) cannot be opened by a `--force` flag, and what the framework pays for that auditability.
5. [Mental Model: Tamper Guard](/explanation/tamper-guard) — how the GREEN-phase `git restore` rollback and the `src/**/*.py` write allow-list keep an LLM agent from rewriting the test, spec, or config during the implementation phase.
6. [Why Phases Are Tiered to Models](/explanation/model-tiering) — why V4 Flash handles RED/GREEN/REFACTOR/explore, V4 Pro handles JUDGE/YELLOW/plan/tasks, and Qwen 3.7+ [Thinking] handles research/prd/shard/adhoc, and how Session Continuity pins the tier at the session boundary rather than the phase boundary.
More pages will be added as the codebase evolves. If you finish an essay and want to *act* on its design, the **See Also** section at the bottom of each page points at the relevant how-to and reference.

## Architecture

- [How the Tome Subsystem Emerges](/explanation/tome-subsystem) — the umbrella explanation for the docs curation subsystem itself: seven components (C1 classifier, C2–C5 writers, C6 verifier, C7 setup), seven flows (FLOW-04..FLOW-10), strict quadrant discipline, and the duplicated frontmatter schema; the structural seam every other architecture decision in this quadrant assumes.
- [Why Append-Only Ledgers](/explanation/append-only-ledger) — the constitution-level protocol that makes JSONL event ledgers cross-branch mergeable without conflict markers or a database runtime.
- [How the Setup Scaffold Emerges](/explanation/starter-architecture) — the file layout and idempotency contract that `deviate setup` lays down (`.deviate/`, the four agent command dirs, root `.gitignore` and `.gitattributes`); the on-disk shape every other architectural decision here assumes.
- [Why a Python-Only Prompt Runtime](/explanation/python-only-architecture) — why slash commands live as Python package resources loaded via `importlib.resources`, why the agent-platform skills directory is a generated read-only mirror, and why every `mise run` dispatch is `uv run`-prefixed; the cost is that prompts and code share a single release.

## Process

- [Why Three Non-Bypassable Human Gates](/explanation/hitl-gates) — where Gate 1 (research → PRD), Gate 2 (shard → plan), and Gate 3 (micro-to-merge) sit in the pipeline, why each exists, and what rejected alternatives (a `--force` bypass, role-based delegation, AI auto-approval, headless-CI exemption) would have lost.
- [Mental Model: Tamper Guard](/explanation/tamper-guard) — the layered `git diff --name-only` check, `git restore` rollback, and YELLOW-routing negotiation that make the micro-layer's contract (test, spec, config) structurally immutable across RED → GREEN → REFACTOR.
- [Why Phases Are Tiered to Models](/explanation/model-tiering) — the three-tier cost/frequency/cognitive-demand pairing (V4 Flash, V4 Pro, Qwen 3.7+ [Thinking]) declared in `AGENTS.md` and surfaced as the `[models]` table in `.deviate/config.toml`; the rejected alternatives (one-model-for-all, per-task override, auto-routing, cost-only routing) the framework weighed against declarative per-phase routing.
## Cross-Quadrant Links

- [`Tutorials: a guided tour`](/tutorials/intro) — beginner walkthroughs that build context before an explanation.
- [`How-To: accomplish a specific task`](/how-to/intro) — operator and contributor task guides.
- [`Reference: look something up`](/reference/intro) — flag tables, schema details, and lookup material for already-running commands.
- [`Explanation: understand the why`](/explanation/intro) — this quadrant.

## See Also

- [How the Tome Subsystem Emerges](/explanation/tome-subsystem) — the umbrella architecture explanation for the docs curation subsystem; read this first if you want context for the docs system itself before diving into the runtime explanations below.
- [How the Setup Scaffold Emerges](/explanation/starter-architecture) — the workspace-bootstrap explanation; pairs with the append-only-ledger page to cover the data-model half plus the file-provisioning half of the same architectural decision.
- [Why Append-Only Ledgers](/explanation/append-only-ledger) — the first concrete explanation, foundational to all phase-state and ledger-related design decisions documented elsewhere.
- [Why Three Non-Bypassable Human Gates](/explanation/hitl-gates) — the second explanation; pairs with the append-only-ledger page to cover the governance-mechanism pair the constitution calls out by name.
- [Mental Model: Tamper Guard](/explanation/tamper-guard) — the process-safety explanation that grounds why GREEN-phase agents are sandboxed to `src/**/*.py` and why a tamper event routes through YELLOW rather than aborting the cycle.
- [Why a Python-Only Prompt Runtime](/explanation/python-only-architecture) — the third architecture explanation; explains why prompts live inside the Python package, why the agent-platform skills directory is a generated read-only mirror, and why every `mise run` dispatch is `uv run`-prefixed.
- [Reference: starter config](/reference/starter-config) — the canonical `.gitattributes` shape provisioned by `deviate setup`, where the union-merge rules are exposed as a configurable surface.
- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — the operator task that seeds the union-merge rules and mirrors the command library into every agent directory.
