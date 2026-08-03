# PTF Specifications

Each file in `functions/` describes one scientific source. It starts with YAML
front matter defined by [`schema/ptf-spec-v1.schema.json`](./schema/ptf-spec-v1.schema.json),
followed by Markdown containing formulas, derivations, numerical policy, golden
cases, and scientific decisions.

The JSON Schema is the format contract for the front matter. Until automated
validation is introduced, review front matter against that schema and the PTF
specification quality gate before marking a function ready for implementation.

## Package-wide contracts

Unless a future specification explicitly documents a justified exception, the
public Python layer is keyword-only, accepts scalars and NumPy arrays, follows
NumPy broadcasting, supports `out`, and uses `f64` Rust kernels. These
package-wide contracts must not be repeated in individual source specifications.

Function front matter records source-specific public API, ordered inputs and
outputs, golden cases, edge cases, scope, and short documentation notes. For a
single output,
`result_class` is `null`; multiple outputs use the documented result class.

Top-level `scope.territory` and `scope.dataset` apply to functions that omit
those fields. A present non-null function value overrides the common value, and
an explicit `null` says the value is intentionally unavailable or inapplicable.
