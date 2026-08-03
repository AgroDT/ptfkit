---
name: ptf-spec-ingest
description: Convert a user-supplied local source file into a validated source-oriented PTF specification in specs/functions/*.md. Use before Rust or Python implementation, or to validate an existing spec. Extract only explicitly stated formulas and preserve ambiguity as blocking issues.
---

# PTF Spec Ingest

## Workflow

1. Read the local source file at the path supplied by the user.
2. Extract only explicitly stated PTF formulas, variables, constants, units,
   references, and candidate outputs from the supplied file.
3. Create or update the source-oriented specification under
   `specs/functions/<apa_article_key>.md` using `references/spec-template.md`.
   Add every function from that publication to its single ordered `functions`
   list and add its matching Markdown section.
4. Validate each generated or existing function-level spec with
   `references/spec-quality-gate.md`.
5. If anything required is missing or ambiguous, mark that function spec blocked.
   Do not invent formulas, constants, units, expected values, output fields, or
   API details.

## Output

Return one of:

- `Ready for implementation`: include the function-level spec path, checklist,
  and non-blocking notes.
- `Blocked`: include blocking questions, missing fields grouped by spec section,
  and the function-level spec path.

## Hard Rules

- Treat the supplied file as extraction input only; the generated
  `specs/functions/*.md` source specification becomes the implementation source
  of truth.
- Do not copy the supplied file into the repository or record its path in
  generated files.
- Use article/APA-style spec filenames and keep public API names inside the
  spec identity section.
- Build `apa_article_key` as `<first_author_surname_lowercase><year>` from local
  metadata, for example `cosby1984`. If needed, append `a`, `b`, etc. for
  same-author same-year collisions. Do not use internet lookup to construct the key.
- Extract only formulas and metadata explicitly present in the supplied file.
- Do not implement code during ingest.
- For missing or ambiguous details, write `TODO` and blocking issues instead of
  filling gaps.
