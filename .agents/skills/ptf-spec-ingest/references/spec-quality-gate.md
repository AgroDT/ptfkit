# PTF Specification Quality Gate

## Required location and format

- A source specification is a Markdown file under `specs/functions/` named
  `<source.key>.md`.
- It starts with YAML front matter conforming to
  [`specs/schema/ptf-spec-v1.schema.json`](../../../specs/schema/ptf-spec-v1.schema.json).
- The `functions` list is ordered and non-empty. Each entry has complete local
  inputs and outputs in public order.
- The top level records a source summary of at most 100 characters, complete
  APA citation, DOI identifier and URL (or `null`), and complete source scope.

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
- `source.summary` is hand-authored, includes short APA attribution and short
  territory, and is not derived from citation or scope fields.
- Top-level `scope.territory` describes the source and public module. A function
  declares `scope.territory` only for a narrower or different territory; the
  fields are independent and never inherit or override one another.
- The spec filename and `source.key` identify exactly one public Python module.
  Omitted top-level `python_generation` means it is generated; a manual module
  needs `python_generation: manual` at the top level.

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
