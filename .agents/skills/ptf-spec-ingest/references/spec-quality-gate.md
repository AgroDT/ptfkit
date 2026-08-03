# PTF Specification Quality Gate

## Required location and format

- A source specification is a Markdown file under `specs/functions/` named
  `<source.key>.md`.
- It starts with YAML front matter conforming to
  [`specs/schema/ptf-spec-v1.schema.json`](../../../specs/schema/ptf-spec-v1.schema.json).
- The `functions` list is ordered and non-empty. Each entry has complete local
  inputs and outputs in public order.
- Publication citation, DOI, source notes, and common scope appear only at the
  top level.

## Required checks

- A function is `ready-for-implementation` only when its formula is complete
  and unambiguous.
- Every function has exactly one Markdown `## \`calc_ptf_...\`` section, in YAML
  order; no Markdown function section is undeclared.
- Every formula symbol is declared as an input, output, constant, or
  intermediate in that function's Markdown section.
- Every input and output has units and complete descriptions.
- Unit conversions and numerical policy remain in Markdown. Ordered golden
  cases and edge cases are structured YAML and are sufficiently explicit to
  implement; their scientific rationale may remain in Markdown.
- Multiple outputs require a result class; a scalar output requires
  `result_class: null`.
- Scope inherits top-level territory/dataset only when the function field is
  omitted; explicit `null` is intentional.

## Blocking issues

- Missing or ambiguous formula, unit, constant, output, or golden expectation.
- A duplicated publication entry or source key.
- A source-oriented filename that does not match `source.key`.
- A duplicate function name or public `(module, name)` pair.
- Duplicate input or output names in one function.
- A Markdown section missing, undeclared, or out of order.
- Formula expressions or long scientific prose placed in YAML.
- `not specified` used where a structured `null` is required.

## Status vocabulary

- `draft`: incomplete, exploratory specification.
- `blocked`: an identified missing or ambiguous source detail prevents work.
- `ready-for-implementation`: complete and reviewed specification.
- `implemented`: a corresponding implementation exists and remains traceable to
  this specification.
