---
title: "Config Field Reference"
description: "Reference table of the nine Tome frontmatter fields every page in this site must carry, plus their allowed values."
doc_type: reference
status: draft
last_verified_at: 2026-07-01
verified_sha: c533ead
related_issues: []
---

This page is the reference table for the frontmatter fields every page in this docs site must carry. The fields come from two sources: Starlight's default `docsSchema()` (`title`, `description`, `prev`, `next`) and the five Tome-only fields declared in `src/content.config.ts`'s `extend` block.

## Fields

| Field | Type | Allowed values | Default | Source | Notes |
|---|---|---|---|---|---|
| `title` | string | ≤ 80 chars; verb-driven for tutorial, concept-driven for explanation | (required) | Starlight default | Rendered as the page H1 — the body MUST NOT open with `#` |
| `description` | string | ≤ 160 chars; one-sentence summary | (required) | Starlight default | Used for SEO and sidebar previews |
| `doc_type` | enum | `tutorial` \| `how-to` \| `reference` \| `explanation` | (required) | Tome `extend` | The Diátaxis register the page belongs to |
| `status` | enum | `draft` \| `reviewed` | `draft` | Tome `extend` | `reviewed` requires a sha-anchored verification pass |
| `last_verified_at` | ISO date | `YYYY-MM-DD` | (required) | Tome `extend` | The date a human last checked the page against the source |
| `verified_sha` | string | commit SHA (full or short) | (required) | Tome `extend` | The commit the page was verified against |
| `related_issues` | list of strings | issue IDs (`ISS-XXX`, `ISS-ADH-XXX`) | `[]` | Tome `extend` | The issues the page satisfies or updates |
| `prev` | string (optional) | repo-relative path | (omitted) | Starlight default | OMIT for first-in-theme, quad intros, and root `index.md` |
| `next` | string (optional) | repo-relative path | (omitted) | Starlight default | OMIT for last-in-theme, quad intros, and root `index.md` |

## Allowed frontmatter shape

A page MAY carry up to **nine** frontmatter fields (5 Tome-only + 4 Starlight-default). Pages emit only what they need:

- The four quadrant landing pages (`tutorials/index.md`, `how-to/index.md`, `reference/index.md`, `explanation/index.md`) carry 7 fields and OMIT `prev` / `next`
- The root `apps/docs/src/content/docs/index.md` carries 7 fields and OMITs `prev` / `next`
- Writer-produced pages carry 7 or 9 fields depending on whether they have in-theme neighbours

## See also

- [Reference → Config Schema index](../index.md)
- [How-To → Getting Started → Run Your First DeviaTDD Task](../../how-to/getting-started/starter-first-task.md)
