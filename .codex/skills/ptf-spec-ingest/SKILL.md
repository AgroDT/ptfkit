---
name: ptf-spec-ingest
description: Validate ptfkit PTF function Markdown specs from specs/functions/*.md before implementation. Use when Codex receives a ready-made external MD spec, needs to check completeness, detect blocking issues, create an implementation checklist, or decide whether work may proceed. Do not extract or infer formulas from papers.
---

# PTF Spec Ingest

## Workflow

1. Read the target `specs/functions/<function_name>.md` file.
2. If the input is article-level material outside `specs/functions/`, mark it blocked and request a function-level spec.
3. Load `references/spec-template.md` and `references/spec-quality-gate.md`.
4. Validate identity, formulas, variables, units, outputs, Python API contract, numeric policy, and golden tests.
5. Produce an implementation checklist from `references/implementation-checklist-template.md`.
6. If anything required is missing or ambiguous, stop. Do not invent formulas, constants, units, expected values, or API details.

## Output

Return one of:

- `Ready for implementation`: include the checklist and non-blocking notes.
- `Blocked`: include blocking questions and missing fields grouped by spec section.

## Hard Rules

- Treat the MD spec as the source of truth.
- Do not extract formulas from articles or surrounding prose.
- Do not implement code during ingest.
- Do not edit project files unless the user explicitly asks for checklist files to be written.
