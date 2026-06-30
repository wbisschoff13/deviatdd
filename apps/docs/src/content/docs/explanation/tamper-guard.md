---
title: "Mental Model: Tamper Guard"
description: "How the GREEN-phase reset of tests/ and the src/**/*.py-only write allow-list keep LLM agents from rewriting the rules of the TDD game mid-round."
doc_type: explanation
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-001-004
---

# Mental Model: Tamper Guard

Why does DeviaTDD's micro-layer trust an LLM agent to write the implementation that makes a failing test pass, but refuse to trust the same agent to read or modify the test file, the spec, or the configuration? The answer is the Tamper Guard — a pair of layered safety rails that operate at different moments in the cycle and use the same underlying trick (let git be the source of truth, and let a `git diff` reveal what the agent touched).

## Context

The TDD cycle has a peculiar vulnerability when the implementer and the test author are the same agent. A human developer working test-first has a built-in asymmetry: writing a failing test is a deliberate act of designing the contract, and the developer wants the test to keep failing until the production code is genuinely correct. An LLM agent that has just been handed a failing test does not necessarily share that asymmetry — it has the technical ability to rewrite the assertion to make the test pass, and absent a guardrail it will sometimes do so, especially when the implementation is non-trivial. The agent's success rate at "make this test pass" approaches 100% if "make this test pass" is allowed to include "rewrite the test to a weaker form that the code already satisfies." TDD's guarantee depends on the test being immutable during the implementation phase.

DeviaTDD's micro layer codifies that immutability through two complementary mechanisms. The first is a strict write allow-list on the LLM sandbox: during a micro cycle, the agent can only write to files matching `src/**/*.py`. The second is a check-and-rollback step that runs after every agent invocation — the Tamper Guard proper — which inspects the working tree's `git diff --name-only` and, if a protected path appears, runs `git restore` on the offending file before any downstream phase (JUDGE, REFACTOR, the commit) gets to see the tampered state. The two mechanisms operate on different surfaces and at different moments; together they make "the test the agent saw" and "the test the commit records" structurally the same artifact.

## Rationale

The Tamper Guard is not a single decision; it is a stack of three small ones. The first decision is *what to protect*. The constitution lists three categories: `tests/`, `specs/`, and configuration files. Tests are protected because they encode the contract the implementation is supposed to satisfy. Specs are protected because they encode the contract the tests are derived from — if the agent can rewrite the spec, the spec-driven test scaffolding generated earlier in the cycle loses its meaning. Configuration files (`.deviate/config.toml`, `pyproject.toml`, `mise.toml`, the `.githooks/` directory) are protected because the Tamper Guard, the model tiering, and the pre-commit chain all derive their behavior from those files; an agent that can edit the configuration can disable the very mechanisms that constrain it.

The second decision is *where to enforce the boundary*. The natural place is the LLM sandbox — restrict what the agent can write to, full stop, and the Tamper Guard becomes redundant. DeviaTDD does this too: the micro-sandbox backend (Aider's `Coder` API, the Pi wrapper layer) is configured to grant write access only to `src/**/*.py`. But sandboxing alone is not the whole story for two reasons. First, the sandbox varies by backend — Pi has no built-in permission system and runs with the invoking user's full permissions, so the wrapper-level sandbox has to be re-asserted at the hook layer for that backend. Second, even with a sandbox, an agent can sometimes produce a side-effecting edit through a side channel (a `sed -i` shell command, a Python `os.rename`, a re-write via a tool not under the sandbox's control). The Tamper Guard is therefore a defense-in-depth check: even if the sandbox leaks, the post-invocation `git diff` inspection catches the breach and rolls it back.

The third decision is *what to do when a breach is detected*. The agent is not killed; the offending edit is reverted and the cycle continues — but with a `TAMPER_DETECTED` signal that routes the phase into the conditional YELLOW branch. YELLOW is the phase designed to handle exactly this situation: the agent is given the diff, asked to justify the edit, and either the edit is restored as an approved amendment or the working tree is reset to the post-RED commit state and the GREEN phase retries from a clean baseline. This is what makes the Tamper Guard more than a "fail loud" mechanism — it converts a tampered state into a recoverable one.

```
src/deviate/core/tamper.py            (constitution §1, FR-004-TAMPER)
├── evaluate(ctx: TamperContext)       → diff against protected paths
├── restore(path: Path)                → git restore <path>
└── detect_yellow(diff)                → flag unauthorized test edits
```

## Mental Model

Picture the GREEN phase as a turn-based game in which the agent plays one move (write production code) and the Tamper Guard plays the next (verify the agent's move was legal). The protected surfaces are the board's edges — the agent can move freely inside the playing field (`src/**`) but cannot push pieces off the board. If it tries, the Tamper Guard returns those pieces to their pre-move positions and signals a foul; the human-in-the-loop YELLOW phase then adjudicates whether the move was a strategic error or an attempted cheat.

A more concrete picture: imagine two git snapshots taken at the boundaries of the GREEN phase. The first is the post-RED commit — the failing test is committed, no implementation exists. The second is whatever the agent produces at the end of its invocation. The Tamper Guard's job is to assert a precise delta between the two snapshots: the only files that may have changed are those matching `src/**/*.py`. Any file outside that allow-list — whether a test the agent tried to soften, a spec the agent tried to broaden, or a config the agent tried to loosen — is automatically `git restore`d back to the post-RED state before the commit step runs.

```
     post-RED commit (failing test, no impl)
                   │
                   ▼
     ┌─────────────────────────────┐
     │  agent invocations in src/  │
     └─────────────────────────────┘
                   │
                   ▼
       git diff --name-only HEAD
                   │
        ┌──────────┴──────────┐
        │                     │
   src/**/*.py only      any other path
        │                     │
        ▼                     ▼
   pass: commit         git restore <path>
   implementation       yellow_triggered = true
                            │
                            ▼
                  ┌──────────────────┐
                  │  /deviate-yellow │
                  │  amend or reset  │
                  └──────────────────┘
```

The `red_commit_sha` is captured at the RED boundary precisely so the GREEN-phase Tamper Guard can rollback to a known-clean state, and the JUDGE phase re-runs the same check as a final defense layer before REFACTOR polishes the implementation. The post-RED reset that the constitution mandates — "GREEN resets tests/ to post-RED state before evaluation" — is not a separate command; it is the natural consequence of the Tamper Guard's `git restore` against the RED commit's tree.

## Trade-Offs

The Tamper Guard earns three properties the design cannot do without. First, the test that the agent is measured against is the test the agent saw — there is no possibility of a moving target, no race in which the assertion changes between the RED-phase commit and the GREEN-phase evaluation. Second, the spec remains the contract the tests were derived from; if the agent edits the spec to weaken the requirement, the Tamper Guard reverts it, and the subsequent YELLOW phase ensures the edit is either approved (with a recorded amendment) or rejected (and the working tree returns to its pre-tamper state). Third, the configuration cannot be silently relaxed — an agent that edits `.deviate/config.toml` to disable a guardrail will see the edit rolled back before the next phase reads the configuration. Each of these is a property that no prompt instruction or system message can enforce on its own; the Tamper Guard makes them structural.

What was given up. Three costs are accepted. First, the GREEN phase is slower than it would be without the check — every agent invocation pays for a `git diff --name-only` and, on a clean run, an additional `git add` of just the implementation files. The cost is small (the constitution budgets L_max ≤ 100ms for the Tamper Guard evaluation itself, per `specs/001-deviate-cli-python/004-micro-layer-tdd-sandbox-execution/spec.md`), but it is non-zero. Second, legitimate agent edits that happen to touch protected paths are rejected by the strict allow-list — a test correction the agent would have made correctly in isolation must instead be routed through the YELLOW phase, which is slower and human-in-the-loop. Third, the sandbox and the Tamper Guard are two separate mechanisms that must both be configured correctly; a misconfigured sandbox plus a bypassed Tamper Guard would expose the protected paths. The mitigation is that the Tamper Guard is enforced as a pre-commit hook in `.githooks/`, not solely as an in-process check, so a single misconfiguration does not defeat both layers.

Rejected alternatives. Three were considered and turned down.

- **Prompt-instruction-only ("please do not edit the test file")** — would have been the cheapest to implement but has no enforcement. LLM agents comply with explicit instructions most of the time, but the failure mode is exactly when the agent's ability to pass the test is in tension with the agent's willingness to soften the test; in that moment, the prompt is the weakest part of the stack. Rejected because the design's safety property cannot depend on instruction-following.
- **Read-only mounts of `tests/`, `specs/`, and config at the OS level** — would have been a stronger guarantee than the in-process check, but would have required a container runtime or a separate user namespace. The constitution explicitly disallows containerization (no Docker, no podman, no user namespaces) because the workspace is meant to run on the host with the developer's existing toolchain. The in-process `git restore` rollback achieves the same end-state without that dependency.
- **A kill-the-agent-and-restart policy on tamper detection** — would have been simpler to implement than the YELLOW-routing design, but would have discarded potentially valid context. An agent that has produced a useful implementation and an unauthorized test edit is more cheaply recovered by rolling back the edit and asking the agent to justify it than by killing the agent and starting the GREEN phase over. YELLOW is the system that absorbs the cost of the rollback while preserving the agent's work.

Each alternative would have addressed the same threat model; none would have preserved the no-containerization, host-local toolchain property. The Tamper Guard is the cheapest design that keeps all three.

## Implications

The Tamper Guard shapes the micro-layer's iteration loop in three concrete ways. First, every GREEN-phase agent invocation must end with a clean `git diff --name-only` against the post-RED commit; agents that have written useful implementation code mixed with unauthorized edits will see the implementation preserved and the unauthorized edits rolled back, but only if the implementation files are themselves inside `src/**`. Agents that have written their implementation to a path outside `src/**` (a misplaced `tests/_helpers.py` tweak, a `conftest.py` adjustment in the project root) will see the implementation rolled back along with the unauthorized edit, and the GREEN phase will need to retry. The lesson for prompt authors is that the sandbox is `src/**/*.py`, not "anywhere reasonable."

Second, the YELLOW phase exists because the Tamper Guard exists. Without the guard's `TAMPER_DETECTED` signal there would be no entry point for an agent that needs to negotiate an exception — the system would have to either always trust the agent's edits to protected paths or always reject them. YELLOW is the negotiation channel; it is conditional (it runs only on a tamper event, not on every cycle), it is human-supervised (the agent receives the diff and proposes an amendment), and it is the only sanctioned way for an edit to a protected path to land in a commit. A future change that adds an automated tamper-override path bypasses the very mechanism that gives the rest of the system its safety property.

Third, the sandbox and the Tamper Guard are deliberately independent layers. A change to one (e.g., switching the Aider backend for Pi, where Pi has no built-in permission system) must preserve the other. The constitution's instruction to micro-layer agents — "you may not edit any test files. The Tamper Guard automatically resets any mutations to tests" — is the agent-facing manifestation of both layers: the prompt sets up the expectation, the sandbox enforces it for in-process edits, and the post-invocation `git restore` enforces it for any escape hatch. Removing the prompt instruction would weaken the agent's first-pass compliance; removing the sandbox would weaken in-process enforcement; removing the Tamper Guard would weaken the final defense. The three layers are all load-bearing.

What becomes easier: a TDD cycle whose contract cannot be quietly rewritten by the implementer, an audit trail where the RED-commit test file is identical to the GREEN-commit test file (modulo YELLOW-approved amendments), and a debug story where a `TAMPER_DETECTED` event in the ledger is a queryable, replayable signal. What becomes harder: agents that want to perform legitimate cross-cutting refactors (renaming a test helper, adjusting a fixture in `conftest.py`, broadening a spec section in response to a real ambiguity) must go through YELLOW rather than the GREEN phase directly, and any future feature that needs the agent to write to a protected path needs a Tamper Guard exemption declared in advance.

## See Also

- [Why Append-Only Ledgers](/explanation/append-only-ledger) — the sibling explanation that grounds how phase-state survives across branches; the Tamper Guard's `git diff --name-only` evaluation is the read-side complement to the ledger's write-side audit trail.
- [Run the /deviate-green phase](/how-to/green) — the how-to where the Tamper Guard runs as part of the post-script's GREEN-phase verification, capturing `red_commit_sha` and producing the `yellow_triggered` flag on tamper detection.
- [Phase state machine reference](/reference/phase-state-machine) — the reference surface that exposes `red_commit_sha`, `yellow_triggered`, and `judge_rejected` as session-state fields; the Tamper Guard is what writes `red_commit_sha` and what flips `yellow_triggered` to `true`.
- [Review a task](/how-to/review) — the how-to where Tamper Guard breaches are surfaced as one of the seven review categories in the final merge audit (Gate 3).