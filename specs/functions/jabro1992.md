---
schema_version: 1
source:
  key: jabro1992
  summary: Jabro (1992), United States.
  citation_apa: >-
    Jabro, J. D. (1992). Estimation of saturated hydraulic conductivity of soils
    from particle size distribution and bulk density data. Transactions of the
    ASAE, 35(2), 557-560.
  doi: {identifier: 10.13031/2013.28633, url: https://doi.org/10.13031/2013.28633}
scope:
  territory: USA
  dataset: Southern Cooperation Series Bulletins (Dan et al., 1983; Nofziger et al., 1983; Quisenberry et al., 1987), 350 samples; validation on Duffield silt loam data.
functions:
  - name: calc_ptf_jabro1992
    status: ready-for-implementation
    public_api:
      name: calc_ptf_jabro1992
      result_class: null
      summary: Estimate saturated hydraulic conductivity from silt, clay, and bulk density.
    scope:
      prediction_target: Saturated hydraulic conductivity from silt, clay, and bulk density.
      models: {h_theta: null, k_h: Saturated hydraulic conductivity}
    inputs:
      - {name: silt, symbol: Si, unit: "%", domain: "value > 0", description: "Silt content, 0.002-0.05 mm."}
      - {name: clay, symbol: C, unit: "%", domain: "value > 0", description: "Clay content, <0.002 mm."}
      - {name: bulk_density, symbol: Bd, unit: g/cm^3, domain: "value > 0", description: Bulk density.}
    outputs:
      - {name: k_sat, symbol: Ks, unit: m/s, domain: "value >= 0", description: Saturated hydraulic conductivity.}
    golden_tests:
      - {id: loamy_sand_min_bd, inputs: {silt: 10.0, clay: 5.0, bulk_density: 1.26}, expected: {k_sat: 0.0003849640675896946}, rtol: 1.0e-8, atol: 1.0e-12, notes: Calculated from equation (3) and unit conversion.}
      - {id: loam, inputs: {silt: 38.72, clay: 11.05, bulk_density: 1.42}, expected: {k_sat: 9.804037952717678e-06}, rtol: 1.0e-8, atol: 1.0e-12, notes: Calculated from equation (3) and unit conversion.}
      - {id: silty_clay_loam_max_silt, inputs: {silt: 52.0, clay: 30.0, bulk_density: 1.97}, expected: {k_sat: 7.292435947882127e-09}, rtol: 1.0e-8, atol: 1.0e-12, notes: Calculated from equation (3) and unit conversion.}
      - {id: sandy_clay_min_silt_max_clay, inputs: {silt: 0.2, clay: 44.0, bulk_density: 1.61}, expected: {k_sat: 2.032824027706267e-05}, rtol: 1.0e-8, atol: 1.0e-12, notes: Calculated from equation (3) and unit conversion.}
    edge_cases:
      - {id: non_positive_silt_or_clay, inputs: {silt: 0.0, clay: 5.0, bulk_density: 1.26}, expected_behavior: NumPy-compatible logarithm-domain behaviour., notes: Formula uses log10(silt) and log10(clay).}
    documentation:
      notes: [Sand is not an input to the model.]
      warnings: [The formula uses base-10 logarithms of silt and clay.]
---

# Jabro (1992)

## `calc_ptf_jabro1992`

### Constants

| name | value | units | description |
| --- | --- | --- | --- |
| CM_PER_HOUR_TO_M_PER_SEC | 0.000002777777777777778 | (m/s)/(cm/h) | Convert cm/h to m/s. |

### Formula

```text
log10_k_sat_cm_per_hour = 9.56 - 0.81 * log10(silt) - 1.09 * log10(clay) - 4.64 * bulk_density
k_sat_cm_per_hour = 10 ** log10_k_sat_cm_per_hour
k_sat = k_sat_cm_per_hour * CM_PER_HOUR_TO_M_PER_SEC
```

### Intermediates

| name | units | formula_reference | description |
| --- | --- | --- | --- |
| log10_k_sat_cm_per_hour | log10(cm/h) | equation (3) | Base-10 logarithm of saturated hydraulic conductivity. |
| k_sat_cm_per_hour | cm/h | equation (3) | Saturated hydraulic conductivity before unit conversion. |

### Unit conversion

Convert cm/h to m/s using `CM_PER_HOUR_TO_M_PER_SEC`.

### Numeric policy

Use `f64`, do not round, propagate NaN, and retain NumPy-compatible logarithm-domain behaviour.
