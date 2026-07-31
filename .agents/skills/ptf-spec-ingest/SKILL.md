---
name: ptf-spec-ingest
description: Convert ptfkit article-level paper Markdown from specs/papers/*.md into function-level specs in specs/functions/*.md, validate generated or existing PTF specs, and prepare implementation and validation handoff tasks. Use before Rust or Python implementation. Extract only formulas explicitly present in the MD and preserve ambiguity as blocking issues.
---

# PTF Spec Ingest

## Workflow

1. If the input is a paper extraction, read it from `specs/papers/*.md`.
2. Extract only explicitly stated PTF formulas, variables, constants, units,
   references, and candidate outputs from the provided MD.
3. For each concrete PTF function, create or update a function-level spec under
   `specs/functions/<apa_article_key>.md` using `references/spec-template.md`.
4. Create an ingest report and implementation/validation tasks using
   `references/paper-ingest-report-template.md`.
5. Validate each generated or existing function-level spec with
   `references/spec-quality-gate.md`.
6. If anything required is missing or ambiguous, mark that function spec blocked.
   Do not invent formulas, constants, units, expected values, output fields, or
   API details.

## Output

Return one of:

- `Ready for implementation`: include the checklist and non-blocking notes.
- `Blocked`: include blocking questions, missing fields grouped by spec section,
  and implementation/validation handoff tasks.
- `Paper ingested`: include generated function-level spec paths, ingest report
  path, ready functions, and blocked functions.

## Hard Rules

- Treat the MD spec as the source of truth.
- Treat `specs/papers/*.md` as extraction input only; generated
  `specs/functions/*.md` files become the implementation source of truth.
- Use article/APA-style spec filenames and keep public API names inside the
  spec identity section.
- Build `apa_article_key` as `<first_author_surname_lowercase><year>` from local
  metadata, for example `cosby1984`. If needed, append `a`, `b`, etc. for
  same-author same-year collisions. Do not use internet lookup to construct the key.
- Extract only formulas and metadata explicitly present in the paper MD.
- Do not implement code during ingest.
- For missing or ambiguous details, write `TODO` and blocking issues instead of
  filling gaps.
- Do not edit project files unless the user explicitly asks for checklist files to be written.
