---
schema_version: 1
source:
  key: beniaich2023
  summary: Beniaich et al. (2023), soil-water PTFs for four Moroccan regions.
  citation_apa: >-
    Beniaich, A., Otten, W., Shin, H.-C., Cooper, H. V., Rickson, J.,
    Soulaimani, A., & El Gharous, M. (2023). Evaluation of pedotransfer
    functions to estimate some of soil hydraulic characteristics in North
    Africa: A case study from Morocco. Frontiers in Environmental Science, 11,
    1090688.
  doi:
    identifier: 10.3389/fenvs.2023.1090688
    url: https://doi.org/10.3389/fenvs.2023.1090688
scope:
  territory: Agricultural topsoils in Doukkala, Gharb-Loukouss, Moulouya, and Tadla, Morocco
  dataset: 331 disturbed topsoil samples collected at 0-20 cm from 2019 to 2022; random 50% calibration and 50% validation subsets.
functions:
  - name: calc_ptf_beniaich2023_slr1
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_slr1, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from clay.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs: [{name: clay, symbol: Clay, unit: "%", domain: "0 <= value <= 100", description: Clay content by mass.}]
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {clay: 20.0}, expected: {water_saturation: 0.57427, water_field_capacity: 0.17577, water_wilting_point: 0.09621}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 5 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_slr2
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_slr2, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from silt.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs: [{name: silt, symbol: Silt, unit: "%", domain: "0 <= value <= 100", description: Silt content by mass.}]
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {silt: 30.0}, expected: {water_saturation: 0.68478, water_field_capacity: 0.24878, water_wilting_point: 0.16131}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 5 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_slr3
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_slr3, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from sand.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs: [{name: sand, symbol: Sand, unit: "%", domain: "0 <= value <= 100", description: Sand content by mass.}]
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {sand: 50.0}, expected: {water_saturation: 0.60070, water_field_capacity: 0.18480, water_wilting_point: 0.11077}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 5 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_slr4
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_slr4, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from clay plus silt.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs:
      - {name: clay, symbol: Clay, unit: "%", domain: "0 <= value <= 100", description: Clay content by mass.}
      - {name: silt, symbol: Silt, unit: "%", domain: "0 <= value <= 100", description: Silt content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {clay: 20.0, silt: 30.0}, expected: {water_saturation: 0.74501, water_field_capacity: 0.30678, water_wilting_point: 0.19915}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 5 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_slr5
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_slr5, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from the clay-to-silt ratio.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs:
      - {name: clay, symbol: Clay, unit: "%", domain: "0 <= value <= 100", description: Clay content by mass.}
      - {name: silt, symbol: Silt, unit: "%", domain: "0 < value <= 100", description: Silt content by mass and denominator of the clay-to-silt ratio.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {clay: 20.0, silt: 40.0}, expected: {water_saturation: 0.68578, water_field_capacity: 0.241875, water_wilting_point: 0.16176}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 5 and divided by 100.}]
    edge_cases: [{id: zero_silt, inputs: {clay: 20.0, silt: 0.0}, expected_behavior: IEEE 754 division-by-zero behavior is propagated., notes: The predictor is Clay/Silt.}]
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_slr6
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_slr6, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from soil organic matter.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs: [{name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}]
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {soil_organic_matter: 2.0}, expected: {water_saturation: 0.66749, water_field_capacity: 0.24009, water_wilting_point: 0.15562}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 5 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_mlr1
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_mlr1, result_class: Beniaich2023PTFResult, summary: "Estimate three gravimetric water contents from silt, sand, and organic matter."}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs:
      - {name: silt, symbol: Silt, unit: "%", domain: "0 <= value <= 100", description: Silt content by mass.}
      - {name: sand, symbol: Sand, unit: "%", domain: "0 <= value <= 100", description: Sand content by mass.}
      - {name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {silt: 30.0, sand: 50.0, soil_organic_matter: 2.0}, expected: {water_saturation: 0.56266, water_field_capacity: 0.17238, water_wilting_point: 0.09366}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 6 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_mlr2
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_mlr2, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from sand and organic matter.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs:
      - {name: sand, symbol: Sand, unit: "%", domain: "0 <= value <= 100", description: Sand content by mass.}
      - {name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {sand: 50.0, soil_organic_matter: 2.0}, expected: {water_saturation: 0.58954, water_field_capacity: 0.18025, water_wilting_point: 0.10825}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 6 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_mlr3
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_mlr3, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from silt and organic matter.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs:
      - {name: silt, symbol: Silt, unit: "%", domain: "0 <= value <= 100", description: Silt content by mass.}
      - {name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {silt: 30.0, soil_organic_matter: 2.0}, expected: {water_saturation: 0.67031, water_field_capacity: 0.24275, water_wilting_point: 0.15755}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 6 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_mlr4
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_mlr4, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents from clay and organic matter.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs:
      - {name: clay, symbol: Clay, unit: "%", domain: "0 <= value <= 100", description: Clay content by mass.}
      - {name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {clay: 20.0, soil_organic_matter: 2.0}, expected: {water_saturation: 0.55890, water_field_capacity: 0.16859, water_wilting_point: 0.09157}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 6 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_mlr5
    status: implemented
    public_api: {name: calc_ptf_beniaich2023_mlr5, result_class: Beniaich2023PTFResult, summary: "Estimate three gravimetric water contents from clay, silt, and organic matter."}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three point estimates, k_h: null}}
    inputs:
      - {name: clay, symbol: Clay, unit: "%", domain: "0 <= value <= 100", description: Clay content by mass.}
      - {name: silt, symbol: Silt, unit: "%", domain: "0 <= value <= 100", description: Silt content by mass.}
      - {name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: [{id: representative_case, inputs: {clay: 20.0, silt: 30.0, soil_organic_matter: 2.0}, expected: {water_saturation: 0.56229, water_field_capacity: 0.17200, water_wilting_point: 0.09379}, rtol: 1.0e-12, atol: 1.0e-12, notes: Calculated from Table 6 and divided by 100.}]
    edge_cases: []
    documentation: {notes: [Source regressions operate in percentage points; outputs are divided by 100 to return g/g.], warnings: [Developed from Moroccan agricultural topsoils and not independently validated outside the source territory.]}
  - name: calc_ptf_beniaich2023_regression_tree
    status: blocked
    public_api: {name: calc_ptf_beniaich2023_regression_tree, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents with the fitted regression trees.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three fitted regression-tree point estimates, k_h: null}}
    inputs:
      - {name: clay, symbol: Clay, unit: "%", domain: "0 <= value <= 100", description: Clay content by mass.}
      - {name: silt, symbol: Silt, unit: "%", domain: "0 <= value <= 100", description: Silt content by mass.}
      - {name: sand, symbol: Sand, unit: "%", domain: "0 <= value <= 100", description: Sand content by mass.}
      - {name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: []
    edge_cases: []
    documentation: {notes: [The source gives minsplit = 50.], warnings: [TODO - fitted tree splits and terminal predictions are not published.]}
  - name: calc_ptf_beniaich2023_cubist
    status: blocked
    public_api: {name: calc_ptf_beniaich2023_cubist, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents with the fitted Cubist models.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three fitted Cubist point estimates, k_h: null}}
    inputs:
      - {name: clay, symbol: Clay, unit: "%", domain: "0 <= value <= 100", description: Clay content by mass.}
      - {name: silt, symbol: Silt, unit: "%", domain: "0 <= value <= 100", description: Silt content by mass.}
      - {name: sand, symbol: Sand, unit: "%", domain: "0 <= value <= 100", description: Sand content by mass.}
      - {name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: []
    edge_cases: []
    documentation: {notes: [The source gives rules = 5, extrapolation = 5, and committees = 1.], warnings: [TODO - fitted Cubist rules and linear models are not published.]}
  - name: calc_ptf_beniaich2023_random_forest
    status: blocked
    public_api: {name: calc_ptf_beniaich2023_random_forest, result_class: Beniaich2023PTFResult, summary: Estimate three gravimetric water contents with the fitted random forests.}
    scope: {prediction_target: "Gravimetric water content at saturation, -33 kPa, and -1,500 kPa.", models: {h_theta: Three fitted random-forest point estimates, k_h: null}}
    inputs:
      - {name: clay, symbol: Clay, unit: "%", domain: "0 <= value <= 100", description: Clay content by mass.}
      - {name: silt, symbol: Silt, unit: "%", domain: "0 <= value <= 100", description: Silt content by mass.}
      - {name: sand, symbol: Sand, unit: "%", domain: "0 <= value <= 100", description: Sand content by mass.}
      - {name: soil_organic_matter, symbol: SOM, unit: "%", domain: "value >= 0", description: Soil organic matter content by mass.}
    outputs:
      - {name: water_saturation, symbol: w_0, unit: g/g, domain: null, description: Gravimetric water content at saturation.}
      - {name: water_field_capacity, symbol: w_330, unit: g/g, domain: null, description: Gravimetric water content at -33 kPa.}
      - {name: water_wilting_point, symbol: w_15000, unit: g/g, domain: null, description: "Gravimetric water content at -1,500 kPa."}
    golden_tests: []
    edge_cases: []
    documentation: {notes: [The source gives ntrees = 1000, node size = 10, and mtry = 2.], warnings: [TODO - fitted trees, training data, and random seed are not published.]}
---

# Beniaich et al. (2023)

For every linear model below, `Clay`, `Silt`, `Sand`, and `SOM` are mass
percentages. The table regressions produce gravimetric percentage points; each
raw prediction is divided by 100 to return the source-stated `g/g` unit. Use
`f64`, do not round, and propagate NaN and infinities.

## `calc_ptf_beniaich2023_slr1`

### Formula
`w_0 = (46.307 + 0.556*Clay)/100`; `w_330 = (10.277 + 0.365*Clay)/100`;
`w_15000 = (3.081 + 0.327*Clay)/100`.

## `calc_ptf_beniaich2023_slr2`

### Formula
`w_0 = (59.508 + 0.299*Silt)/100`; `w_330 = (16.178 + 0.290*Silt)/100`;
`w_15000 = (10.521 + 0.187*Silt)/100`.

## `calc_ptf_beniaich2023_slr3`

### Formula
`w_0 = (81.420 - 0.427*Sand)/100`; `w_330 = (34.680 - 0.324*Sand)/100`;
`w_15000 = (23.927 - 0.257*Sand)/100`.

## `calc_ptf_beniaich2023_slr4`

### Formula
`ClaySilt = Clay + Silt`; `w_0 = (89.401 - 0.298*ClaySilt)/100`;
`w_330 = (45.178 - 0.290*ClaySilt)/100`;
`w_15000 = (29.265 - 0.187*ClaySilt)/100`.

## `calc_ptf_beniaich2023_slr5`

### Formula
`ClaySiltRatio = Clay/Silt`; `w_0 = (68.851 - 0.546*ClaySiltRatio)/100`;
`w_330 = (23.278 + 1.819*ClaySiltRatio)/100`;
`w_15000 = (16.298 - 0.244*ClaySiltRatio)/100`.

## `calc_ptf_beniaich2023_slr6`

### Formula
`w_0 = (61.163 + 2.793*SOM)/100`; `w_330 = (21.331 + 1.339*SOM)/100`;
`w_15000 = (13.758 + 0.902*SOM)/100`.

## `calc_ptf_beniaich2023_mlr1`

### Formula
`w_0 = (87.342 - 0.281*Silt - 0.548*Sand + 2.377*SOM)/100`;
`w_330 = (35.844 - 0.085*Silt - 0.359*Sand + 0.947*SOM)/100`;
`w_15000 = (28.734 - 0.148*Silt - 0.324*Sand + 0.636*SOM)/100`.

## `calc_ptf_beniaich2023_mlr2`

### Formula
`w_0 = (75.366 - 0.417*Sand + 2.219*SOM)/100`;
`w_330 = (32.227 - 0.320*Sand + 0.899*SOM)/100`;
`w_15000 = (22.421 - 0.254*Sand + 0.552*SOM)/100`.

## `calc_ptf_beniaich2023_mlr3`

### Formula
`w_0 = (53.777 + 0.278*Silt + 2.457*SOM)/100`;
`w_330 = (13.847 + 0.281*Silt + 0.999*SOM)/100`;
`w_15000 = (8.929 + 0.182*Silt + 0.683*SOM)/100`.

## `calc_ptf_beniaich2023_mlr4`

### Formula
`w_0 = (39.432 + 0.553*Clay + 2.699*SOM)/100`;
`w_330 = (7.023 + 0.364*Clay + 1.278*SOM)/100`;
`w_15000 = (0.923 + 0.327*Clay + 0.847*SOM)/100`.

## `calc_ptf_beniaich2023_mlr5`

### Formula
`w_0 = (32.505 + 0.548*Clay + 0.267*Silt + 2.377*SOM)/100`;
`w_330 = (-0.094 + 0.359*Clay + 0.274*Silt + 0.947*SOM)/100`;
`w_15000 = (-3.623 + 0.324*Clay + 0.175*Silt + 0.636*SOM)/100`.

## `calc_ptf_beniaich2023_regression_tree`

### Formula
TODO: the publication does not provide the fitted splits or terminal values.

## `calc_ptf_beniaich2023_cubist`

### Formula
TODO: the publication does not provide the fitted rules or linear models.

## `calc_ptf_beniaich2023_random_forest`

### Formula
TODO: the publication does not provide the fitted trees, training data, or
random seed.
