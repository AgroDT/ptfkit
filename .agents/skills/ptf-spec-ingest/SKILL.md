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
   `references/spec-quality-gate.md` and
   `cargo run -p ptfkit-codegen -- validate`.
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
- Record `source.summary` as a hand-authored public summary no longer than 100
  characters. It includes a short APA attribution and short territory; do not
  derive it from other fields.
- Record `source.citation_apa` as the complete citation. For a DOI, record both
  its identifier and its source-provided URL; use `null` only when no DOI exists.
- Do not implement code during ingest.
- Omit top-level `python_generation` for the default generated public Python
  module. Set `python_generation: manual` only as a deliberate module-wide
  opt-out.
- Record the source's complete territory in top-level `scope.territory`. Add
  `functions[].scope.territory` only for a function with a narrower or different
  territory; the two fields are independent and never inherit.
- For missing or ambiguous details, write `TODO` and blocking issues instead of
  filling gaps.
