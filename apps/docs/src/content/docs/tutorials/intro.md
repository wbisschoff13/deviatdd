---
title: "Tutorials: a guided tour of DeviaTDD"
description: "Beginner walkthroughs that take you from a fresh DeviaTDD install to your first complete TDD cycle — your hands on the keyboard for verification only."
doc_type: tutorial
status: draft
last_verified_at: 2026-06-29
verified_sha: 8daa502
related_issues:
  - ISS-ADH-011
---

# Tutorials: a guided tour of DeviaTDD

This quadrant is for readers who have just installed DeviaTDD and want to feel what it does end-to-end before reading how-tos or explanations. Each tutorial walks one happy path: you invoke a small sequence of `/deviate-*` slash commands, your agent does the work, and your hands stay on the keyboard only to read state and verify the result. If you already know what you want to do and just need the steps, link out to a [how-to](/how-to/intro); if you want to understand *why* the system is shaped the way it is, link out to [explanation](/explanation/intro); if you want to look a flag or schema up, link out to [reference](/reference/intro).

## Reading order

Walk through the tutorials in this order. The first stops at the moment your first macro-layer task lands; the second stops at the moment one TDD micro cycle completes.

1. **[Your first DeviaTDD session](/tutorials/starter-first-run)** — bootstrap the workspace with `deviate setup`, open your agent platform, run `/deviate-init`, and trigger your first `/deviate-explore` task end-to-end. *Read this first.*
2. **[Your first RED → GREEN → REFACTOR cycle](/tutorials/first-red-green)** — once the macro layer is initialized and a feature has been explored, walk a single PENDING task through `/deviate-red` → `/deviate-green` → `/deviate-refactor` and verify each phase lands.

More tutorials land as DeviaTDD evolves. If you finish a tutorial and want to act on its design, the **Next Steps** section at the bottom of each page points at the matching how-to or reference entry.

## Cross-Quadrant Links

- [`How-To: accomplish a specific task`](/how-to/intro) — operator and contributor task guides for readers who already know what they want to do.
- [`Reference: look something up`](/reference/intro) — flag tables, schema details, and lookup material for already-running commands.
- [`Explanation: understand the why`](/explanation/intro) — design rationale and architectural context for the choices a how-to exercises.

## Next Steps

- [Your first DeviaTDD session](/tutorials/starter-first-run) — start here for a guided end-to-end walkthrough from `deviate setup` to the first exploration task.
