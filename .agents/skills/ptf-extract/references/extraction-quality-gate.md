# Extraction quality gate

Read the active schema before extracting. A source is one standalone
`specs/functions/<apa_article_key>.yaml` file. Its filename stem is the sole
APA-style slug and identifies the generated public module, for example
`cosby1984`.

## Required facts

- Preserve the ordered functions, inputs, outputs, source metadata, units,
  golden and edge cases, documentation, scope, and semantic `implementation`
  fields required by the schema.
- Use the formula DSL only in `implementation` expressions. Retain scientific
  derivations, citations, rationale, and unresolved questions in
  `scientific_notes`.
- Omit `generation` for the default generated public module. Use
  `generation.public_python: manual` only for an intentional manual public
  wrapper; native ufunc generation remains required.

## Blockers

Set affected functions to `blocked` and name the missing evidence when a
formula, constant, unit, output mapping, semantic expression, golden value,
numeric policy, or applicability fact is missing or ambiguous. Do not use
`TODO` as a substitute for a structured required value; write it only in an
explicit blocker note. Schema-valid YAML may still be blocked.

## Statuses

- `blocked`: source evidence is incomplete or ambiguous.
- `ready-for-implementation`: complete, validated draft awaiting human review.
- `implemented`: reserved for `$ptf-generate` after all targets pass.
