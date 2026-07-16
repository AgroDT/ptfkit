# calc_ptf_jabro1992

## Status

- spec_version: 1
- status: ready-for-implementation
- generated_by: ptf-spec-ingest
- generated_at: 2026-07-16

## Identity

- function_name: calc_ptf_jabro1992
- source_key: jabro1992
- public_module: ptfkit.jabro1992
- public_function: calc_ptf_jabro1992
- rust_function: calc_ptf_jabro1992
- result_type: scalar
- result_class: null

## Reference

- citation_apa: Jabro, J. D. (1992). Estimation of saturated hydraulic conductivity of soils from particle size distribution and bulk density data. Transactions of the ASAE, 35(2), 557-560.
- doi: 10.13031/2013.28633
- source_notes: Extracted from `specs/papers/1992_Jabro_Estimation_of_saturated_hydraulic_conductivity_of_soils.md`. Formula is equation (3).

## Scope

- territory: USA
- dataset: Southern Cooperation Series Bulletins, 350 samples; validation on Duffield silt loam data.
- h_theta_model: not applicable
- k_h_model: saturated hydraulic conductivity
- prediction_target: saturated hydraulic conductivity from silt, clay, and bulk density.

## Inputs

| name | symbol | type | units | valid_range | required | description |
| --- | --- | --- | --- | --- | --- | --- |
| silt | Si | float | % | > 0 | yes | Silt content. |
| clay | C | float | % | > 0 | yes | Clay content. |
| bulk_density | Bd | float | g/cm^3 | > 0 | yes | Bulk density. |

## Outputs

| name | symbol | type | units | valid_range | description |
| --- | --- | --- | --- | --- | --- |
| k_sat | Ks | float | m/s | >= 0 | Saturated hydraulic conductivity. |

## Constants

| name | value | units | description |
| --- | --- | --- | --- |
| CM_PER_HOUR_TO_M_PER_SEC | 0.000002777777777777778 | (m/s)/(cm/h) | Convert cm/h to m/s. |

## Formula

```text
log10_k_sat_cm_per_hour = 9.56 - 0.81 * log10(silt) - 1.09 * log10(clay) - 4.64 * bulk_density
k_sat_cm_per_hour = 10 ** log10_k_sat_cm_per_hour
k_sat = k_sat_cm_per_hour * CM_PER_HOUR_TO_M_PER_SEC
```

## Intermediates

| name | units | formula_reference | description |
| --- | --- | --- | --- |
| log10_k_sat_cm_per_hour | log10(cm/h) | equation (3) | Base-10 logarithm of saturated hydraulic conductivity. |
| k_sat_cm_per_hour | cm/h | equation (3) | Saturated hydraulic conductivity before unit conversion. |

## Units Policy

- input_units: silt and clay are percentages; bulk density is g/cm^3.
- output_units: k_sat is returned in m/s.
- conversions: cm/h to m/s using `CM_PER_HOUR_TO_M_PER_SEC`.

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
- public_doc_summary: Estimate saturated hydraulic conductivity from silt, clay, and bulk density.

## Golden Tests

| case_id | inputs_json | expected_json | rtol | atol | notes |
| --- | --- | --- | --- | --- | --- |
| loamy_sand_min_bd | {"silt": 10.0, "clay": 5.0, "bulk_density": 1.26} | {"k_sat": 0.0003849640675896946} | 1e-8 | 1e-12 | Calculated from equation (3) and unit conversion. |
| loam | {"silt": 38.72, "clay": 11.05, "bulk_density": 1.42} | {"k_sat": 9.804037952717678e-06} | 1e-8 | 1e-12 | Calculated from equation (3) and unit conversion. |
| silty_clay_loam_max_silt | {"silt": 52.0, "clay": 30.0, "bulk_density": 1.97} | {"k_sat": 7.292435947882127e-09} | 1e-8 | 1e-12 | Calculated from equation (3) and unit conversion. |
| sandy_clay_min_silt_max_clay | {"silt": 0.2, "clay": 44.0, "bulk_density": 1.61} | {"k_sat": 2.032824027706267e-05} | 1e-8 | 1e-12 | Calculated from equation (3) and unit conversion. |

## Edge Cases

| case_id | inputs_json | expected_behavior | notes |
| --- | --- | --- | --- |
| non_positive_silt_or_clay | {"silt": 0.0, "clay": 5.0, "bulk_density": 1.26} | numpy-compatible logarithm domain behavior | Formula uses log10(silt) and log10(clay). |

## Implementation Notes

- Do not use sand; the source model excludes it.
