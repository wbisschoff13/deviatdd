---
title: "Why Append-Only Ledgers"
description: "How `specs/issues.jsonl` and `specs/**/tasks.jsonl` use git's `merge=union` so concurrent feature branches can append events without conflict markers."
doc_type: explanation
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues: []
---

# Why Append-Only Ledgers

Why does DeviaTDD's source of truth for issues and tasks live in plain JSONL files instead of a database, and why do two engineers on parallel feature branches never see conflict markers when they each append to the same ledger? The answer is a deliberate pairing: an *append-only* event model on top of git's *union-merge* driver. Each choice enables the other, and the trade-offs they accept together are the shape of every phase boundary in the system.

## Context

The constitution names five architectural principles that govern how state is captured, isolated, and audited: the Three-Layer Architecture, the Append-Only Ledger Protocol, the Git Isolation Principle, the Tamper Guard, and the Human-in-the-Loop gates. Of these, the ledger protocol is the one the rest quietly depend on. Every phase transition — `SHARD` producing an issue, `TASKS` decomposing it into rows, `RED → GREEN → JUDGE → REFACTOR` cycling through the micro sandbox — emits a new event to one of two JSONL files. The ledger is the audit trail; it is what the Tamper Guard reads to verify that no prior record was mutated, and it is what the inspect commands query to derive the canonical state of any issue.

The constraint that makes this design non-obvious is the absence of a database runtime. The constitution's tech-stack standards are explicit: there is no Postgres, no SQLite, no Redis. State is JSONL ledgers, TOML config, and JSON session files. The question is therefore not "which database?" but "how does a flat file behave correctly when two branches both append to it?" That question has an answer in git's built-in merge drivers, and the answer costs the system something specific — which is what this page is about.

## Rationale

Three decisions stack on top of each other. First, the ledgers are *append-only*: no existing line is ever modified or overwritten. A task that moves from `PENDING` to `GREEN` does not get its row updated; a second row is appended with the new status. The canonical state of any record is derived by sequential parsing of the ledger and applying a "last entry per `id` wins" rule — enforced by the read-side helpers in `src/deviate/state/ledger.py` (`_append_record`, `append_task_transition`, the compound-key idempotency guard). Agents cannot edit status fields directly; only the CLI may append events. This separation is what keeps the ledger trustworthy as an audit trail.

Second, the ledgers are JSONL rather than a single JSON document or a YAML file. JSONL is line-oriented: each event is exactly one line, terminated by a newline. That property matters because git's default merge driver works line-by-line. If two branches each append a new line to the same file, git's three-way merge sees those appends as non-overlapping hunks and combines them automatically. A single JSON document would have produced structural conflicts at every concurrent edit; a YAML document would have done the same and worse, with the additional cost of anchor normalization.

Third, and this is the operational layer, the `.gitattributes` file at the repo root declares `merge=union` for both `specs/issues.jsonl` and `specs/**/tasks.jsonl`. The constant `DEVIATE_GITATTRIBUTES_SEED` in `src/deviate/cli/__init__.py` carries the exact text; `_ensure_root_gitattributes` provisions the file idempotently on every `deviate setup` and `deviate init pre` run. Git's `merge=union` driver is a line-wise union: when two branches both add lines, the result keeps every unique line from both sides and emits no conflict markers. It does not attempt to deduplicate by content — that is the CLI's job at read time, via the compound-key idempotency check on `(issue_id, status)` or `(task_id, status)`.

```
# .gitattributes (excerpt, sourced from DEVIATE_GITATTRIBUTES_SEED)
specs/issues.jsonl merge=union
specs/**/tasks.jsonl merge=union
```

## Mental Model

Picture the ledger as a write-ahead log that happens to be committed to git. Each `deviate shard pre` call appends a single line; each `deviate tasks post` call appends a line per task; each micro-phase transition appends one more. Two engineers on two branches do not contend on the file — there is no row-level lock, no transactional abort, no merge conflict to resolve. When the branches merge, git's union driver concatenates the unique lines, and the CLI's read helpers walk the result top-to-bottom and apply last-wins semantics.

```
         feat/A:  ISS-001-005  SHARDED  t=2026-06-26T10:00  ← appended on branch A
         feat/B:  ISS-001-006  SHARDED  t=2026-06-26T10:05  ← appended on branch B
                            │
                            ▼   git merge main..feat/A..feat/B
                            │
         main+union: ISS-001-005  SHARDED  t=2026-06-26T10:00  ← kept from A
                     ISS-001-006  SHARDED  t=2026-06-26T10:05  ← kept from B
```

The semantic-duplicate case — two branches both appending the *same* logical event — is not git's problem. The CLI's compound-key guard rejects it at write time on a single branch, and on a cross-branch merge the union driver simply preserves both lines until read-time canonical-state resolution collapses them to one. The point is that the conflict is deferred from the merge moment to the read moment, where the system is in a better position to resolve it deterministically.

## Trade-Offs

The pairing earns two properties that no database would have given as cheaply: zero-runtime state (no Postgres to provision, no SQLite file to back up, no schema migrations to coordinate across branches) and zero-ceremony branching (an engineer opens a PR from a worktree without coordinating with anyone). It also gives up three things, and being honest about them is part of why the design is the way it is.

What was given up. The ledger has no transactional integrity across branches. If branch A creates issue `ISS-X` and branch B independently creates issue `ISS-Y`, and both branches then transition those issues through phase boundaries before merging, the resulting merged ledger is the union of every append from both branches — the system cannot prove that the transitions happened in any particular order, only that all of them happened. For DeviaTDD's purposes this is acceptable because the phases are designed to be causally independent (each branch owns its own issue scope), but it is not a general-purpose database model. Second, deduplication is read-time, not write-time. The CLI rejects a duplicate `(id, status)` append on the same branch via `fcntl.flock`, but cross-branch duplicates survive the merge and collapse later. Third, schema evolution is append-only in the strict sense: renaming or removing a field is forbidden, because the ledger still contains old records with the old shape. New fields may be added; old ones may be deprecated by convention but not by deletion.

Rejected alternatives. Three were considered and turned down.

- **A SQLite database with WAL mode** would have given cross-branch transactional semantics via merge-time schema checks, but at the cost of a runtime dependency, a binary file format that does not diff cleanly, and a backup story that JSONL-on-git gives for free.
- **An advisory-lock service** (e.g., a Redis-backed lock the CLI takes before every append) would have serialized concurrent appends but would also have introduced a network dependency and a single point of failure — incompatible with the no-runtime design constraint.
- **Branch serialization via a merge queue** would have prevented concurrent appends in the first place, but it would have collapsed the parallel-work story that the constitution's Git Isolation Principle is explicitly trying to preserve.

Each alternative would have solved the conflict-on-merge problem; none would have preserved the "no runtime, no ceremony" property. The union-merge approach is the only one that keeps both.

## Implications

The ledger protocol is the reason the read-side code in `src/deviate/state/ledger.py` looks the way it does. `resolve_issue_record()` does not "look up" an issue; it walks the entire file top-to-bottom and returns the last entry matching the requested `issue_id`. The pending-task filter returns every record whose status is `PENDING`, including stale entries from completed tasks — the read-side canonicalization is responsible for filtering those out. Any new feature that reads from the ledger must adopt the same sequential-parse discipline; treating the file as a "current state" snapshot is a category error and will surface bugs the moment two branches have merged.

The protocol also constrains how the system can evolve. Schema changes to `IssueRecord` and `TaskRecord` are additive: new optional fields can land without coordination, but removing or renaming a field requires either a migration script or a coordinated cutover across every outstanding branch — neither of which the current tooling supports. The growth-rate question (how big can `specs/issues.jsonl` get before the sequential-parse cost dominates?) is the one piece of long-term risk the design papered over; the constitution version history flags it as a v0.2.0-era risk, and the operational mitigations (log rotation, archive-to-cold-storage) remain an open task.

What becomes easier: parallel feature work without coordination overhead, an audit trail that *is* the git history, and a debug story where `git log -p specs/issues.jsonl` is a usable interface. What becomes harder: anything that needs a global view across branches in real time, and any feature that wants to depend on ledger state being globally consistent at all moments.

## See Also

- [How-To: bootstrap a DeviaTDD workspace](/how-to/setup) — the operator task that provisions the union-merge rules via `_ensure_root_gitattributes`; the design choice explained here is exercised at this step.
- [Reference: starter config](/reference/starter-config) — the canonical `.gitattributes` shape written by `deviate setup`, where the two `merge=union` rules are exposed as a configurable surface.