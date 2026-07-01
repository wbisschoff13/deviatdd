import { defineCollection, z } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const collections = {
	docs: defineCollection({
		loader: docsLoader(),
		schema: docsSchema({
			extend: z.object({
				// Tome-only frontmatter fields — MUST match the inline schema the
				// writers (C2-C5) embed in their SKILL.md prompts. Drift is a
				// Starlight-side validation failure surfaced at build time.
				doc_type: z.enum(['tutorial', 'how-to', 'reference', 'explanation']),
				status: z.enum(['draft', 'reviewed']).default('draft'),
				last_verified_at: z.coerce.date(),
				verified_sha: z.string(),
				related_issues: z.array(z.string()).default([]),
			}),
		}),
	}),
};
