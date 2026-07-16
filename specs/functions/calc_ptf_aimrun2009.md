# calc_ptf_aimrun2009

## Status

- spec_version: 1
- status: ready-for-implementation
- generated_by: ptf-spec-ingest
- generated_at: 2026-07-16

## Identity

- function_name: calc_ptf_aimrun2009
- source_key: aimrun2009
- public_module: ptfkit.aimrun2009
- public_function: calc_ptf_aimrun2009
- rust_function: calc_ptf_aimrun2009
- result_type: scalar
- result_class: null

## Reference

- citation_apa: Aimrun, W., & Amin, M. S. M. (2009). Pedo-transfer function for saturated hydraulic conductivity of lowland paddy soils. Paddy and Water Environment, 7, 217-225.
- doi: 10.1007/s10333-009-0165-y
- source_notes: Extracted from `specs/papers/2009_aimrun_Pedo_transfer_function_for_saturated_hydraulic_conductivity.md`. Formula is equation (10).

## Scope

- territory: Tanjung Karang Rice Irrigation Project, Malaysia
- dataset: 408 lowland paddy soil samples from Sawah Sempadan rice cultivation area.
- h_theta_model: not applicable
- k_h_model: saturated hydraulic conductivity
- prediction_target: saturated hydraulic conductivity from clay, dry bulk density, organic matter, and geometric mean diameter.

## Inputs

| name | symbol | type | units | valid_range | required | description |
| --- | --- | --- | --- | --- | --- | --- |
| clay | C | float | % | > 0 | yes | Clay content. |
| bulk_density | Db | float | g/cm^3 | > 0 | yes | Dry bulk density. |
| organic_matter | OM | float | % | > 0 | yes | Organic matter content. |
| gmd | GMD | float | mm | > 0 | yes | Geometric mean diameter. |

## Outputs

| name | symbol | type | units | valid_range | description |
| --- | --- | --- | --- | --- | --- |
| k_sat | Ks | float | m/s | >= 0 | Saturated hydraulic conductivity. |

## Constants

| name | value | units | description |
| --- | --- | --- | --- |
| M_PER_DAY_TO_M_PER_SEC | 0.000011574074074074073 | (m/s)/(m/day) | Convert m/day to m/s. |

## Formula

```text
ln_k_sat_m_per_day = -2.368 + 3.846 * bulk_density + 0.091 * organic_matter - 6.203 * ln(bulk_density) - 0.343 * ln(organic_matter) - 2.334 * ln(clay) - 0.411 * ln(gmd)
k_sat_m_per_day = exp(ln_k_sat_m_per_day)
k_sat = k_sat_m_per_day * M_PER_DAY_TO_M_PER_SEC
```

## Intermediates

| name | units | formula_reference | description |
| --- | --- | --- | --- |
| ln_k_sat_m_per_day | ln(m/day) | equation (10) | Natural logarithm of saturated hydraulic conductivity. |
| k_sat_m_per_day | m/day | equation (10) | Saturated hydraulic conductivity before unit conversion. |

## Units Policy

- input_units: clay and organic matter are percentages; bulk density is g/cm^3; gmd is mm.
- output_units: k_sat is returned in m/s.
- conversions: m/day to m/s using `M_PER_DAY_TO_M_PER_SEC`.

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
- return_kind: scalar
- result_fields: [k_sat]
- existing_api_compatibility: must-match-existing
- public_doc_summary: Estimate saturated hydraulic conductivity for lowland paddy soils.

## Golden Tests

| case_id | inputs_json | expected_json | rtol | atol | notes |
| --- | --- | --- | --- | --- | --- |
| mean_topsoil_layer | {"clay": 43.88, "bulk_density": 0.94, "organic_matter": 12.07, "gmd": 0.010} | {"k_sat": 7.358406556179513e-08} | 1e-8 | 1e-12 | Calculated from equation (10) and unit conversion. |
| mean_hardpan_layer | {"clay": 50.21, "bulk_density": 1.19, "organic_matter": 8.55, "gmd": 0.007} | {"k_sat": 3.07872446717209e-08} | 1e-8 | 1e-12 | Calculated from equation (10) and unit conversion. |
| mean_subsoil_layer | {"clay": 58.81, "bulk_density": 1.13, "organic_matter": 5.12, "gmd": 0.005} | {"k_sat": 2.3343051908963327e-08} | 1e-8 | 1e-12 | Calculated from equation (10) and unit conversion. |
| min_organic_matter | {"clay": 47.50, "bulk_density": 1.08, "organic_matter": 1.43, "gmd": 0.008} | {"k_sat": 3.831168764444974e-08} | 1e-8 | 1e-12 | Calculated from equation (10) and unit conversion. |

## Edge Cases

| case_id | inputs_json | expected_behavior | notes |
| --- | --- | --- | --- |
| non_positive_log_input | {"clay": 0.0, "bulk_density": 1.0, "organic_matter": 1.0, "gmd": 0.01} | numpy-compatible logarithm domain behavior | Formula uses natural logarithms of all inputs. |

## Implementation Notes

- Sand and silt are not inputs to the selected final model.
