# Extraction quality gate

Read the active schema before extracting. A source is one standalone
`specs/functions/<apa_article_key>.yaml` file. Its filename stem is the sole
APA-style slug and identifies the generated public module, for example
`cosby1984`.

## Required facts

- Preserve the ordered functions, inputs, outputs, source metadata, units,
  verification and edge cases, documentation, scope, and semantic `implementation`
  fields required by the schema.
- Every record output has an explicit PascalCase `name`.
- Every scalar output and record field has a stable `quantity` whose exact unit
  exists in `specs/quantities.yaml`. Registry tolerances are reviewed project
  policy, not claims of measurement uncertainty or model predictive accuracy.
- When the source uses a finite categorical predictor, represent its reusable
  type as an enum in `$defs` and bind it to each function-local argument with
  `name` plus `$ref`. The enum owns its type description and admissible values;
  the binding description, when present, explains only that argument's role.
- When the source publishes a table selected by a category, model it as a typed
  lookup from the enum to a record in `$defs`. Preserve one row per enum member
  and one numeric value per output-record field. Use enum member names in lookup
  keys and verification-case inputs, not canonical textual values or target ordinals.
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

## Verification cases

Every computationally complete function needs at least one verification case.
Use only these provenance kinds:

- `published` when a complete input-output pair appears in the paper,
  supplementary material, official author software, or another authoritative
  source. Preserve its location in `source_location`.
- `calculated` when no complete published pair exists. Select an input and
  independently calculate the expected output from the published computational
  contract, fix the result in YAML, and explain the input choice in `rationale`.

Prefer calculated inputs in this order: a complete published predictor row,
published predictor means or medians, an interior point of the documented
domain, then an expert-selected typical physically valid soil. Keep values away
from boundaries, use the stated units and scales, preserve texture sums and
positive logarithm arguments, and respect physical relations such as
`theta_1500 <= theta_33 <= theta_s`. Do not combine unrelated marginal extrema.
For piecewise models and trees, cover every material computational branch with
a published case where available and a calculated case otherwise.

For record outputs, `expected` contains every output field. Verification cases
contain provenance but no tolerance or precision fields. Generated tests use
the resolved function-output policy from `specs/quantities.yaml` or an explicit
function-level `verification_tolerances` override with `source_location`.

The lack of a published case is not an extraction or release blocker.

## Blockers

Set affected functions to `blocked` and name the missing evidence when a
formula, constant, unit, output mapping, preprocessing step, transform, branch,
fitted payload, or applicability fact is missing or ambiguous. Do not use
`TODO` as a substitute for a structured required value; write it only in an
explicit blocker note. The absence of a published example, row-level dataset,
supplement, or author calculator is not a blocker when the computational
contract is complete enough to create a calculated case. Rights and licensing
remain a separate release gate and do not change scientific extraction status.

## Statuses

- `blocked`: source evidence is incomplete or ambiguous.
- `ready-for-implementation`: complete, validated draft awaiting human review.
- `implemented`: reserved for `$ptf-generate` after all targets pass.
