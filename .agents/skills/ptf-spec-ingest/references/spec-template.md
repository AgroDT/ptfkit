# Valid PTF Function Spec Template

Store function-level specs at `specs/functions/<apa_article_key>.md`.

Use `apa_article_key = <first_author_surname_lowercase><year>`, for example
`cosby1984`. If the same first author has multiple papers in the same year,
append `a`, `b`, etc. using local metadata order. Do not use internet lookup to
construct this key. Keep public Python and Rust function names in the identity
section.

```markdown
# calc_ptf_authorYEAR_extra

## Status

- spec_version: 1
- status: ready-for-implementation
- generated_by: external-spec-app
- generated_at: YYYY-MM-DD

## Identity

- function_name: calc_ptf_authorYEAR_extra
- source_key: authorYEAR_extra
- public_module: ptfkit.authorYEAR
- public_function: calc_ptf_authorYEAR_extra
- rust_function: calc_ptf_authorYEAR_extra
- result_type: scalar | namedtuple
- result_class: AuthorYEARPTFResult | null

## Reference

- citation_apa: Author, A. (YEAR). Title. Journal, volume(issue), pages.
- doi: https://doi.org/...
- source_notes: Short note from the external spec app.

## Scope

- territory: Region or "not specified"
- dataset: Dataset description or "not specified"
- h_theta_model: Model name or "not applicable"
- k_h_model: Model name or "not applicable"
- prediction_target: Short description of computed property.

## Inputs

| name | symbol | type | units | valid_range | required | description |
| --- | --- | --- | --- | --- | --- | --- |
| sand | S | float | % | 0 <= sand <= 100 | yes | Sand content. |

## Outputs

| name | symbol | type | units | valid_range | description |
| --- | --- | --- | --- | --- | --- |
| k_sat | Ks | float | m/s | >= 0 | Saturated hydraulic conductivity. |

## Constants

| name | value | units | description |
| --- | --- | --- | --- |
| CM_PER_HOUR_TO_M_PER_SEC | 0.000002777777777777778 | (m/s)/(cm/h) | Unit conversion. |

## Formula

Use plain text or fenced math. Every variable must be declared as an input,
constant, intermediate, or output.

```text
intermediate = ...
k_sat = ...
```

## Intermediates

| name | units | formula_reference | description |
| --- | --- | --- | --- |

## Units Policy

- input_units: Inputs are accepted exactly as listed above.
- output_units: Outputs are returned exactly as listed above.
- conversions: List every conversion used by the formula.

## Numeric Policy

- precision: f64
- rounding: none
- nan_policy: propagate
- domain_errors: numpy-compatible
- invalid_input_policy: document-only | raise | return_nan

## Vectorization Contract

- supports_scalar: true
- supports_numpy_arrays: true
- broadcasting: numpy
- supports_out: true

## Python API Contract

- keyword_only: true
- return_kind: scalar | namedtuple
- result_fields: [field1, field2]
- existing_api_compatibility: new | must-match-existing
- public_doc_summary: One sentence.

## Golden Tests

| case_id | inputs_json | expected_json | rtol | atol | notes |
| --- | --- | --- | --- | --- | --- |
| scalar_001 | {"sand": 58.0} | {"k_sat": 1.23e-6} | 1e-10 | 1e-12 | External spec app. |

## Edge Cases

| case_id | inputs_json | expected_behavior | notes |
| --- | --- | --- | --- |

## Implementation Notes

- Optional notes that do not override formulas, units, or API contract.
```
