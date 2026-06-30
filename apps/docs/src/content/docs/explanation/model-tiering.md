---
title: "Why Phases Are Tiered to Models"
description: "How V4 Flash, V4 Pro, and Qwen 3.7+ [Thinking] map to specific phases by cost, frequency, and cognitive demand — and what was given up to make the assignment work."
doc_type: explanation
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-005
---

# Why Phases Are Tiered to Models

A self-driving LLM pipeline makes a sequence of decisions that vary wildly in cost and consequence: writing a failing test for a list-comprehension helper is a one-shot, locally-verifiable call, while producing a research document that a human reviews at HITL Gate 1 is a rare, high-stakes call. DeviaTDD's constitution names this variation as policy rather than letting it emerge from the framework's defaults. The Model Tiering principle pins three tiers — V4 Flash, V4 Pro, and Qwen 3.7+ [Thinking] — to specific phases by cost, frequency, and cognitive demand, and the Config-Driven Model Routing principle declares the surface for that policy: the `[models]` table in `.deviate/config.toml`. This page is about why those specific tiers map to those specific phases, and what the framework gives up by being explicit about the assignment rather than letting each phase pick its own model at call time.

## Context

The mapping itself is short enough to fit in a single table from `AGENTS.md`. V4 Flash, the low-cost tier, handles `explore`, `red`, `green`, and `refactor` — the phases that run dozens of times per feature and whose output is locally verifiable (a test fails or passes; a refactor preserves the test outcome). V4 Pro, the cached/compliance tier, handles `plan`, `tasks`, `yellow`, and `judge` — the phases whose output is consumed downstream by a HITL gate or by a later phase that does not re-derive it. Qwen 3.7+ [Thinking], the reasoning tier, handles `research`, `prd`, `shard`, and `adhoc` — the phases that run once per feature and that emit artifacts whose mistakes propagate through every downstream task. The table is policy-level guidance, not an enforcement mechanism; operators override per phase by setting `[models].<phase>` in `.deviate/config.toml`, and the runtime resolves the override at agent-dispatch time via `resolve_phase_model` in `src/deviate/state/config.py`.

The mechanism that surfaces the assignment is the `[models]` table. The keys of that table are phase names, case-insensitive; the value of the reserved `default` key is the fallback for any phase that does not have an explicit entry. The `DeviateConfig` Pydantic model validates the table at load time (`src/deviate/state/config.py:115`), and `resolve_phase_model(phase, models)` returns the first match in a fixed order: a phase-specific key, the `default` key, or `None` to signal that the backend should fall back to its native default. Two of the three supported agent backends — `opencode` and `droid` — accept a `--model` flag that the runtime injects based on the resolved value; the third, `claude`, ignores the resolved value silently. The result is a routing surface that is uniform across the supported backends at the configuration level, but uneven at the wire level — a constraint the model tiering design acknowledges but does not paper over.

The tiering cannot be read in isolation. The constitution's Session Continuity principle says that micro-layer tasks reuse a single LLM session across RED → GREEN → REFACTOR phases, and that "Model switching mid-task is prohibited." That rule converts the tier boundary from a per-phase decision into a per-session decision: the moment a session is opened in a tier, every phase that runs in that session uses the same tier, even if those phases are normally tiered differently. YELLOW is the canonical example — the GREEN agent encounters a Tamper Guard breach, and the system spawns YELLOW to adjudicate; the YELLOW phase reuses whatever model GREEN was running under, not the V4 Pro tier that the AGENTS.md table nominally assigns to YELLOW. The tiering is policy for the *first* phase of a session; Session Continuity is policy for the *rest*.

## Rationale

The pairing between tiers and phases is driven by three independent cost/risk dimensions, and the framework uses the same three dimensions to defend the assignment. The first is *frequency*. The micro layer runs RED, GREEN, and REFACTOR for every task in every issue in every feature; a feature that produces fifteen issues with five tasks each triggers forty-five RED→GREEN→REFACTOR cycles, each of which pays the cost of a model invocation. Routing those phases to a high-cost tier multiplies the per-task cost by an order of magnitude relative to V4 Flash, with no commensurate quality gain — a test written by a more expensive model is not materially better than a test written by a cheaper one when the test's correctness is gated by the local test suite rather than by judgment. The tier boundary is set so that the highest-frequency phases get the cheapest tier that produces verifiably correct output, and the policy accepts the trade-off that "verifiably correct" is a weaker bar than "judgmentally excellent."

The second dimension is *gate-bearing*. JUDGE, YELLOW, PLAN, and TASKS produce artifacts that either trigger a HITL gate (JUDGE → Gate 3 audit, YELLOW → Tamper Guard adjudication) or are consumed by a later phase that does not re-derive them (PLAN's `risk_register` and `workstation_map` are consumed verbatim by TASK decomposition, which in turn produces rows consumed verbatim by the micro cycle). A wrong judgment at JUDGE is not locally verifiable the way a wrong test is; it is a constitutional evaluation that depends on the model reading `specs/constitution.md` and the diff and reaching a defensible verdict. V4 Pro is the cheapest tier that consistently produces constitutionally-aware judgment; routing JUDGE to V4 Flash would produce verdicts that pass a structural check (the verdict has the right shape) but that miss substantive compliance. The cost increase is justified by the gate's role as a structural invariant, not by the per-invocation quality of the model on a representative prompt.

The third dimension is *cognitive demand*. The architecture phases (RESEARCH, PRD, SHARD, ADHOC) produce artifacts whose downstream consumers are dozens of issues, hundreds of tasks, and thousands of micro cycles. A design error in RESEARCH propagates through every Functional Requirement in the PRD, every sharded issue, every task, and every micro cycle that consumes those tasks — a multiplier that is roughly quadratic in feature size. The reasoning tier (Qwen 3.7+ [Thinking]) is the only one of the three that has the chain-of-thought depth to evaluate multi-clause constitutional alignment, design tradeoffs across a non-trivial search space, and the Gherkin acceptance-criteria derivation that SHARD needs. V4 Pro would produce a competent-looking design; Qwen 3.7+ [Thinking] produces a design whose reasoning chain can be audited. The cost increase is justified by the downstream multiplier, not by the per-invocation quality, and the policy accepts that most architecture-tier invocations pay for a thinking budget that the output does not always consume.

The choice to make the tiering declarative in `.deviate/config.toml` rather than hard-coded in the agent-invocation layer is itself a design decision with trade-offs. Declarative routing means a `deviate` operator can promote JUDGE from V4 Pro to a different model by editing one line of TOML, without modifying the CLI source. It also means the routing is auditable: the inspect commands can read `.deviate/config.toml` and report which model is currently bound to which phase, which makes "did this run use the right model?" a queryable property of the workspace rather than a property of the runtime. The cost is that the routing is now a config surface that operators must understand — a complexity the framework accepts because the alternative (silent, per-call model selection by the agent backend) is unauditable and would make HITL Gate 3 unable to verify constitutional alignment against a specific model version.

```
# .deviate/config.toml (excerpt)
[models]
default = "deepseek/deepseek-v4-flash"   # V4 Flash — RED, GREEN, REFACTOR, /explore
plan     = "deepseek/deepseek-v4-pro"    # V4 Pro — plan, tasks, yellow, judge
research = "qwen/qwen3.7-thinking"        # Qwen 3.7+ [Thinking] — research, prd, shard, adhoc
```

## Mental Model

Picture the pipeline as a railway with three classes of locomotive: a high-frequency commuter line (V4 Flash), a long-haul express line (V4 Pro), and a single-car luxury line that runs only on architecture routes (Qwen 3.7+ [Thinking]). Every phase is assigned to exactly one line, and the assignment is fixed by a schedule (`AGENTS.md`'s "Model Tiering" table) that the operator can override by editing the timetable (`.deviate/config.toml`'s `[models]` table). The schedule is the policy; the resolution algorithm is the dispatcher; the backend is the engine that actually pulls the cars.

A more concrete picture: when a phase is about to run, the dispatcher reads `.deviate/config.toml`, looks up the phase name in `[models]`, and resolves to either a phase-specific key, the `default` key, or `None`. If the resolved value is not `None` and the backend supports `--model`, the dispatcher injects the flag into the agent's command line. If the resolved value is `None` or the backend does not support the flag, the dispatcher does not inject anything — the agent uses its session default. The model is not "chosen" at runtime by the framework; the model is declared at config-load time, resolved at phase-dispatch time, and forwarded at agent-spawn time. The phase→model binding is a static property of the workspace, not a dynamic property of the session.

```
   .deviate/config.toml [models]
   ┌────────────────────────────────────────────────────┐
   │ default = "deepseek/deepseek-v4-flash"             │
   │ plan     = "deepseek/deepseek-v4-pro"              │
   │ research = "qwen/qwen3.7-thinking"                 │
   └────────────────────────────────────────────────────┘
                            │
                            ▼
              resolve_phase_model(phase, models)
                            │
   ┌── V4 Flash ──────────┐ ┌── V4 Pro ──────────┐ ┌── Qwen 3.7+ [T] ──┐
   │ explore              │ │ plan               │ │ research           │
   │ red                  │ │ tasks              │ │ prd                │
   │ green                │ │ yellow             │ │ shard              │
   │ refactor             │ │ judge              │ │ adhoc              │
   └──────────────────────┘ └────────────────────┘ └────────────────────┘
```

## Trade-Offs

The framework pays three concrete costs to make the tiering explicit. The first is *operator cognitive load*: a contributor must understand three tiers, sixteen phases, and the resolution order to predict which model will run a given phase. The second is *tier migration risk*: when a model is deprecated, the `[models]` table must be updated, and an operator who forgets to do so silently routes phases to a model that may not exist anymore. The third is *backend heterogeneity*: the `claude` backend ignores model config, so a workspace whose `[models]` table is rich with overrides will still see `claude` use its own session default — a fact that surfaces only when the operator inspects an unexpected model ID in a JUDGE verdict and traces it back to the silent-ignore behavior. None of these costs is fatal; all three are the price of an auditable, config-driven routing surface.

Rejected alternatives.

- **One-model-for-all-phases.** A single high-quality model for every phase would have eliminated the cognitive load and the tier-migration risk. It was rejected because the cost multiplier for the high-frequency phases (RED, GREEN, REFACTOR, /explore) is on the order of 5–10× relative to V4 Flash, and the per-invocation quality gain at the locally-verifiable phases is not commensurate with that cost. The framework would still pass constitutional alignment at the gate-bearing phases, but the operator cost per feature would make the pipeline economically unviable for the contribution cadence the framework is designed to support — features that ship every few days, not every few weeks.
- **Per-task operator-chosen model.** Maximum flexibility, with the model specified in `tasks.md` per row. Rejected because it adds an operator decision at exactly the moment in the micro cycle when speed and consistency matter; the model that wrote the test is the model the GREEN phase will reuse (per Session Continuity), so a per-task override would also have to gate the GREEN phase's model, doubling the decision surface. The cost of the extra decision does not pay for itself when the tier table already captures the operator's intent at a coarser granularity, and the per-task knob would create a new failure mode where one task's override contradicts the next task's override within the same session.
- **Auto-routing based on phase-name pattern detection.** A smart router that classifies each phase by its name or context and picks a model. Rejected because the phase is already known declaratively; the routing key is the phase itself, not a derived classification. An auto-router would add a second LLM call (the classification), defeating the cost savings of the tiering, and would also be unauditable: an operator could not verify "did this run use V4 Pro?" without inspecting the router's decision log. The tiering design deliberately keeps the routing key human-readable (a phase name in a TOML table) so that the answer to "which model ran this phase?" is a `grep` away.
- **Cost-only routing (cheapest model that can complete).** Route to the cheapest model that returns a non-error result. Rejected because it ignores the cognitive demand dimension: a cost-only router would route JUDGE to V4 Flash (which can return a verdict-shaped response) even when the verdict's quality is constitutionally inadequate. The framework's compliance posture requires that the judgment-bearing phases be routed to a model whose chain-of-thought depth can evaluate constitutional alignment; cost-only routing cannot express that constraint because the cheapest model that completes is not the cheapest model that completes *correctly* under a judgment bar.

## Implications

The tiering constrains future evolution in two ways. First, any new phase that the framework adds must declare its tier in the AGENTS.md table, and the declaration is policy-level — the runtime does not enforce it. A new phase that the operator forgets to wire into `[models]` will fall through to the `default` key, which is V4 Flash; if the new phase is gate-bearing or architecture-tier, that fallback is a silent degradation. The mitigation is the constitutional review of new phases, which is where the tier assignment is supposed to be made explicit; the cost is that a new phase is a config-surface change, not just a code-surface change, and the new-phase PR must touch both `AGENTS.md` and `.deviate/config.toml`'s example block.

Second, the tiering pairs with Session Continuity in a way that the operator must understand. The constitution prohibits model switching mid-task, which means the tier for RED is also the tier for GREEN and REFACTOR, even if the AGENTS.md table lists those phases as the same tier anyway. The non-obvious case is YELLOW: the constitution and the spec agree that YELLOW reuses whatever model GREEN was running under, not the V4 Pro tier that the table nominally assigns to it. The session-continuity rule overrides the per-phase table when they conflict, and the framework does not warn the operator at the moment of conflict — the resolution is silent, and a YELLOW that runs under V4 Flash because GREEN was running under V4 Flash is the correct behavior, not a bug. The audit story relies on the operator understanding this pairing, because "which model ran YELLOW?" has a non-obvious answer that the ledger does not surface directly.

What becomes easier: cost predictability (the operator can budget a feature by phase count and tier table), model substitution (changing one line in `.deviate/config.toml` is the entire migration), and audit clarity (a Gate 3 review can verify which model produced the diff under review by reading `[models]`). What becomes harder: per-task override (the framework deliberately does not support it), dynamic tier escalation (the framework deliberately does not support a "promote to V4 Pro on failure" rule), and tier-table maintenance (the AGENTS.md table is a manual artifact that must be updated by hand as phases are added or re-tiered, and the framework does not generate it from the codebase).

## See Also

- [How to run a task via the micro dispatcher](/how-to/run) — the how-to where the per-phase model is resolved at dispatch time; the design choice explained here is exercised at the `deviate run` invocation, where `[models]` is read and `--model` is injected for the configured phase.
- [Reference: Model Routing](/reference/model-routing) — the canonical reference for the `[models]` table, the resolution order, the per-backend flag behavior, and the recommended phase tier map that the constitution's Model Tiering principle names by category.
- [Why Three Non-Bypassable Human Gates](/explanation/hitl-gates) — the adjacent process principle; HITL gates and model tiering pair to make gate-bearing decisions both human-reviewed and model-tier-aware, so the model's chain-of-thought depth is itself a structural property of the gate, not an accident of the operator's session.
