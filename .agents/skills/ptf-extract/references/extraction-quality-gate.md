# Extraction quality gate

Read the active schema before extracting. A source is one standalone
`specs/functions/<apa_article_key>.yaml` file. Its filename stem is the sole
APA-style slug and identifies the generated public module, for example
`cosby1984`.

## Required facts

- Preserve the ordered functions, inputs, outputs, source metadata, units,
  golden and edge cases, documentation, scope, and semantic `implementation`
  fields required by the schema.
- Every record output has an explicit PascalCase `name`.
- Use the formula DSL only in `implementation` expressions. In
  `scientific_notes`, retain source-supported scientific context, derivations
  needed to justify an interpretation, evidence for review decisions, citations,
  and unresolved questions. A formula in the paper's notation may be retained
  when it defines a concept, records a derivation or interpretation, documents a
  deliberately unimplemented model, or is otherwise needed to review the
  extraction. State its purpose. Do not mechanically repeat an implementation
  expression, its intermediate variables, a unit conversion, or generic
  floating-point behaviour without such scientific context.
- Organize `scientific_notes` with concise headings such as `Supported models`,
  `Review decisions`, `Documented limitations`, and `Blockers`. Explain a
  discrepancy precisely enough for a reviewer to trace the choice to the source.
- Omit `generation` for the default generated public module. Use
  `generation.public_python: manual` only for an intentional manual public
  wrapper; native ufunc generation remains required.

## Texture-input adapters

Registered adapters are globally available, but no adapter is applied
automatically. For each function with particle-size or texture-related inputs,
review the source evidence for fraction basis, fine-earth basis, particle-size
boundaries, named classification system, sum-to-100 expectations, and direct
categorical texture predictors.

Verify that:

- every `derived_inputs` application names a registered adapter and a public
  input having that adapter's registered categorical type;
- every bound component and numeric formula symbol is explicit;
- the binding contains meaningful source-backed compatibility evidence;
- roles are never inferred from parameter names;
- a categorical predictor remains categorical unless the source supports a
  representative-fractions transformation;
- adapter lowering does not alter the published PTF formula;
- representative USDA values are not embedded in the PTF source specification;
  and
- missing compatibility evidence does not set an otherwise complete PTF to
  `blocked`.

Compatibility evidence belongs in the structured derived binding. It may also
be explained in `scientific_notes` when additional context helps scientific
review. The extractor records evidence only; it does not convert user data.

## Blockers

Set affected functions to `blocked` and name the missing evidence when a
formula, constant, unit, output mapping, semantic expression, golden value,
numeric policy, or applicability fact is missing or ambiguous. Do not use
`TODO` as a substitute for a structured required value; write it only in an
explicit blocker note. Schema-valid YAML may still be blocked. Missing adapter
evidence blocks only an adapter-backed variant, not the original numeric PTF.

## Statuses

- `blocked`: source evidence is incomplete or ambiguous.
- `ready-for-implementation`: complete, validated draft awaiting human review.
- `implemented`: reserved for `$ptf-generate` after all targets pass.
