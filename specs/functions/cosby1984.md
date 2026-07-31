# calc_ptf_cosby1984_univariate

## Status

- spec_version: 1
- status: ready-for-implementation
- generated_by: ptf-spec-ingest
- generated_at: 2026-07-13

## Identity

- function_name: calc_ptf_cosby1984_univariate
- source_key: cosby1984_univariate
- public_module: ptfkit.cosby1984
- public_function: calc_ptf_cosby1984_univariate
- rust_function: calc_ptf_cosby1984_univariate
- result_type: namedtuple
- result_class: Cosby1984UnivariatePTFResult

## Reference

- citation_apa: Cosby, B. J., Hornberger, G. M., Clapp, R. B., & Ginn, T. R. (1984). A statistical exploration of the relationships of soil moisture characteristics to the physical properties of soils. Water Resources Research, 20(6), 682-690.
- doi: not specified
- source_notes: Extracted from the provided article-level Markdown in `specs/papers/1984_Cosby_A_Statistical_Exploration_of_the_Relationships_of_Soil_Moisture_Characteristics_to_the_Physical_Properties_of_Soils.md`. Formulas are from Table 5, univariate regressions.

## Scope

- territory: United States
- dataset: 1448 soil samples from Holtan et al. (1968) and Rawls et al. (1976), as described in the provided paper MD.
- h_theta_model: power function moisture characteristic
- k_h_model: saturated hydraulic conductivity parameter statistics
- prediction_target: mean and standard deviation estimates for hydraulic parameters from sand, silt, and clay percentages.

## Inputs

| name | symbol | type | units | valid_range | required | description |
| --- | --- | --- | --- | --- | --- | --- |
| sand | sand | float | % | 0 <= sand <= 100 | yes | Sand content. |
| silt | silt | float | % | 0 <= silt <= 100 | yes | Silt content. |
| clay | clay | float | % | 0 <= clay <= 100 | yes | Clay content. |

## Outputs

| name | symbol | type | units | valid_range | description |
| --- | --- | --- | --- | --- | --- |
| mean_b | b | float | dimensionless | not specified | Mean slope of the moisture characteristic. |
| mean_log_psi_s | log_psi_s | float | reported log value | not specified | Mean log saturation matric potential; underlying potential is in cm H2O. |
| mean_log_k_sat | log_k_sat | float | reported log value | not specified | Mean log saturated hydraulic conductivity; underlying conductivity is in inches per hour. |
| mean_theta_s | theta_s | float | % volume/volume | not specified | Mean saturated water content. |
| sd_b | b | float | dimensionless | not specified | Standard deviation of b. |
| sd_log_k_sat | log_k_sat | float | reported log value | not specified | Standard deviation of log saturated hydraulic conductivity. |
| sd_theta_s | theta_s | float | % volume/volume | not specified | Standard deviation of saturated water content. |

## Constants

| name | value | units | description |
| --- | --- | --- | --- |

## Formula

Formulas extracted from Table 5 in the provided paper MD.

```text
mean_b = 2.91 + 0.159 * clay
mean_log_psi_s = 1.88 - 0.0131 * sand
mean_log_k_sat = -0.884 + 0.0153 * sand
mean_theta_s = 48.9 - 0.126 * sand
sd_b = 1.34 + 0.0500 * clay
sd_log_k_sat = 0.459 + 0.00321 * silt
sd_theta_s = 7.73 - 0.0730 * clay
```

Excluded from this pilot:

```text
sd_log_psi_s
```

Table 5 reports no significant univariate regression for `sd_log_psi_s`.

## Intermediates

| name | units | formula_reference | description |
| --- | --- | --- | --- |

## Units Policy

- input_units: sand, silt, and clay are percentages.
- output_units: Outputs are returned in the units listed in `Outputs`.
- conversions: none

## Numeric Policy

- precision: f64
- rounding: none
- nan_policy: propagate
- domain_errors: numpy-compatible
- invalid_input_policy: document-only

## Vectorization Contract

- supports_scalar: true
- supports_numpy_arrays: true
- broadcasting: numpy
- supports_out: true

## Python API Contract

- keyword_only: true
- return_kind: namedtuple
- result_fields: [mean_b, mean_log_psi_s, mean_log_k_sat, mean_theta_s, sd_b, sd_log_k_sat, sd_theta_s]
- existing_api_compatibility: new
- public_doc_summary: Estimate Cosby et al. (1984) univariate hydraulic parameter statistics from soil texture.

## Golden Tests

| case_id | inputs_json | expected_json | rtol | atol | notes |
| --- | --- | --- | --- | --- | --- |
| scalar_mid_texture | {"sand": 50.0, "silt": 30.0, "clay": 20.0} | {"mean_b": 6.09, "mean_log_psi_s": 1.225, "mean_log_k_sat": -0.119, "mean_theta_s": 42.6, "sd_b": 2.34, "sd_log_k_sat": 0.5553, "sd_theta_s": 6.27} | 1e-12 | 1e-12 | Calculated directly from Table 5 formulas for pilot testing. |
| scalar_sandy_texture | {"sand": 80.0, "silt": 15.0, "clay": 5.0} | {"mean_b": 3.705, "mean_log_psi_s": 0.832, "mean_log_k_sat": 0.34, "mean_theta_s": 38.82, "sd_b": 1.59, "sd_log_k_sat": 0.50715, "sd_theta_s": 7.365} | 1e-12 | 1e-12 | Calculated directly from Table 5 formulas for pilot testing. |

## Edge Cases

| case_id | inputs_json | expected_behavior | notes |
| --- | --- | --- | --- |
| nan_input | {"sand": "NaN", "silt": 30.0, "clay": 20.0} | propagate NaN in outputs that depend on sand | Pilot policy. |

## Resolved Pilot Decisions

- `sd_log_psi_s` is excluded from this pilot because Table 5 reports no significant univariate regression.
- `mean_log_psi_s` and `mean_log_k_sat` are returned as regression log values exactly as reported; no back-transform is performed.
- Public API names are provisional for pilot testing.

## Remaining Notes

- DOI is not specified in this pilot spec and should be filled before publication-quality docs.
- Log-transformed output units use the pilot contract `reported log value`.

## Implementation Task

- Implement only this function as a pilot candidate.
- Preserve the declared output field order.

## Validation Task

- Add tests from the golden cases above.
- Include at least one scalar case and one NumPy vectorized case.
- Include `out` behavior for each output field.

## Implementation Notes

- This spec was generated from article-level MD and is approved for a test pilot only.
- Do not use the paper MD directly during implementation.
