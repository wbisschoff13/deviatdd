# Short-Form Tweet Variants

*Standalone tweets for non-thread use. Each under 280 chars. Pick the one that fits the slot.*

---

**Variant A — Lead with the problem**

spec-kit gives your agent a spec and hopes.

DeviaTDD gives your agent a sandbox and verifies every step.

RED → GREEN → JUDGE → REFACTOR. Atomic git commits at every phase. Tests are read-only during GREEN.

If you don't trust the agent to enforce TDD — make the CLI enforce it.

---

**Variant B — Lead with the hook**

I shipped a framework where the LLM is forbidden by infrastructure from rewriting the tests.

It's called DeviaTDD. It's a CLI that wraps spec-driven dev + TDD into a deterministic state machine for agents.

Tamper Guard during GREEN. Isolated JUDGE session. Train rollback on violation.

---

**Variant C — Lead with the comparison**

spec-kit: write a spec, ask the agent nicely.

DeviaTDD: write a spec, then make the agent mechanically unable to deviate from it.

3 layers. 3 HITL gates. Append-only ledgers. TDD enforced by the runtime, not by prompts.

The framework, not the prompt, is the contract.

---

**Variant D — Lead with the bold claim**

The hardest problem in agentic coding isn't getting the agent to write good code.

It's getting the agent to not rewrite your tests.

DeviaTDD solves this with a Tamper Guard: micro agents can only write to `src/**/*.py`. Tests are immutable. The CLI checks.

`git checkout HEAD -- <test_file>` is your friend.

---

**Variant E — Lead with the visual**

DeviaTDD, end to end:

```
Macro:  explore → research → prd → shard
              ↓ Gate 1
Meso:   plan → tasks → pr
              ↓ Gate 2
Micro:  RED → GREEN → [YELLOW?] → JUDGE → REFACTOR
              ↓ Gate 3
         main
```

Every box = `deviate <phase> pre/post`.
Every arrow = atomic git commit OR human gate.

No programmatic bypass. Build with me ↓

---

**Variant F — Lead with the cost**

~85% of LLM turns in DeviaTDD run on V4 Flash at cache-hit rates ($0.0028/M tokens).

JUDGE/YELLOW/plan run on V4 Pro ($0.003625/M cached).

`/plan` + `/tasks` share a session per issue → 90%+ KV cache hit rate.

Multi-stage verification doesn't have to be expensive. It has to be engineered.

---

**Variant G — Lead with the build-in-public tease**

I'm starting build-in-public with my own framework.

DeviaTDD — a CLI that orchestrates LLM agents through a strict spec-driven + TDD state machine.

Every project I ship from now on will go through it. Every Gate 3 audit will be public.

If you've been burned by spec-kit + agent drift, watch this thread.

---

**Variant H — Lead with the contrarian take**

The spec-driven AI coding discourse is missing the point.

Prompting the agent harder won't make it follow the spec. Spec-kit won't either.

You need infrastructure that makes drift mechanically impossible:

- Append-only ledgers
- Atomic phase commits
- Tests the agent can't edit
- Isolated judges with rollback authority

That's what DeviaTDD is.

---

**Variant I — Quote-tweet bait (for responding to spec-kit launches)**

spec-kit is a great first step.

But a spec is just markdown. The agent can edit it. The agent can disagree with it. The agent can rewrite the tests to match the implementation.

What you actually want is spec-as-infrastructure. Specs that the runtime enforces, not prompts the agent follows.

That's the gap DeviaTDD closes.

---

**Variant J — Lead with the developer pain**

Every dev who has used spec-kit has hit the same wall:

The spec is perfect. The agent agrees. The implementation lands. The tests pass.

Then you read the diff and realize the agent quietly rewrote half the assertions and "completed" the wrong thing.

DeviaTDD makes this structurally impossible.

Tests are read-only during GREEN. JUDGE checks the diff in an isolated session.

---

**Variant K — Punchy one-liner**

DeviaTDD: spec-driven + TDD, where the LLM is the executor and the CLI is the compliance officer.

Three layers. Three gates. One tamper-proof test suite.

---

**Variant L — Architecture-flavored**

DeviaTDD's micro layer is essentially a state machine interpreter for TDD:

- RED: classify pytest outcome → must be AssertionError
- GREEN: tamper-guard → must be returncode 0
- JUDGE: isolated diff review → COMPLIANCE_PASS or Train rollback
- REFACTOR: regression gate → git restore on failure

The agent is the operand. The CLI is the verifier.

---

## Posting notes

- **Best opening tweets (highest hook density):** Variant D ("forbidden by infrastructure") and Variant B ("sandbox and verifies every step")
- **Best for technical audience (X/Twitter dev crowd):** Variants F, K, L
- **Best for build-in-public arc:** Variants E, G
- **Best for replying to spec-kit posts:** Variant I
- **Avoid double-posting:** pick one variant per day, don't spam