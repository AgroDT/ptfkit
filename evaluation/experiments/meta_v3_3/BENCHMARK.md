# ptfkit catalog benchmark

Aggregate snapshot from the 2026-10-26 run. See [replay instructions](README.md) and [the aggregate checkpoint](../../datasets/meta_v3_3.catalog-benchmark-summary.json). The two final runs produced identical SHA-256 for all 25 artifacts. Full private results remain in `local/meta-catalog-final/summary.json`.

Catalog: 146 → 216. Strict executable: 2; exploratory excluding strict: 42.

The dataset is fixed. No manual metadata recovery or new scientific policy is used. Rankings and ensemble selection are descriptive; they do not establish generalization.

Public API discovery is reconciled against source specifications: 172 implemented; 44 public wrappers with another specification status. These wrappers remain in the denominator and pass through the same existing policies.

Newly discovered functions:

- `calc_ptf_bruand1994_bulk_volume_available_water`
- `calc_ptf_bruand1994_bulk_volume_water_retention`
- `calc_ptf_bruand1994_clay_available_water`
- `calc_ptf_bruand1994_clay_water_retention`
- `calc_ptf_dijkerman1988`
- `calc_ptf_dijkerman1988_available_water`
- `calc_ptf_gupta1979`
- `calc_ptf_jabro1992`
- `calc_ptf_kalumba2021_mlr_ksat`
- `calc_ptf_kalumba2021_mlr_pf00`
- `calc_ptf_kalumba2021_mlr_pf10`
- `calc_ptf_kalumba2021_mlr_pf20`
- `calc_ptf_kalumba2021_mlr_pf28`
- `calc_ptf_kalumba2021_mlr_pf34`
- `calc_ptf_kalumba2021_mlr_pf42`
- `calc_ptf_lal1979_group_i_lower_plastic_limit_from_clay`
- `calc_ptf_lal1979_group_i_lower_plastic_limit_from_organic_carbon`
- `calc_ptf_lal1979_group_i_lower_plastic_limit_from_sand`
- `calc_ptf_lal1979_group_i_moisture_equivalent_from_clay`
- `calc_ptf_lal1979_group_i_moisture_equivalent_from_sand`
- `calc_ptf_lal1979_group_i_plasticity_index_from_clay`
- `calc_ptf_lal1979_group_i_plasticity_index_from_organic_carbon`
- `calc_ptf_lal1979_group_i_plasticity_index_from_sand`
- `calc_ptf_lal1979_group_i_upper_plastic_limit_from_clay`
- `calc_ptf_lal1979_group_i_upper_plastic_limit_from_organic_carbon`
- `calc_ptf_lal1979_group_i_water_01bar_from_clay`
- `calc_ptf_lal1979_group_i_water_01bar_from_sand`
- `calc_ptf_lal1979_group_i_water_03bar_from_clay`
- `calc_ptf_lal1979_group_i_water_03bar_from_sand`
- `calc_ptf_lal1979_group_i_water_0bar_from_clay`
- `calc_ptf_lal1979_group_i_water_0bar_from_sand`
- `calc_ptf_lal1979_group_i_water_15bar_from_clay`
- `calc_ptf_lal1979_group_i_water_15bar_from_sand`
- `calc_ptf_lal1979_group_i_water_15bar_from_silt`
- `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_clay`
- `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_sand`
- `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_silt`
- `calc_ptf_lal1979_group_ii_moisture_equivalent_from_clay`
- `calc_ptf_lal1979_group_ii_moisture_equivalent_from_sand`
- `calc_ptf_lal1979_group_ii_moisture_equivalent_from_silt`
- `calc_ptf_lal1979_group_ii_plasticity_index_from_organic_carbon`
- `calc_ptf_lal1979_group_ii_plasticity_index_from_silt`
- `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_clay`
- `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_organic_carbon`
- `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_sand`
- `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_silt`
- `calc_ptf_lal1979_group_ii_water_01bar_from_clay`
- `calc_ptf_lal1979_group_ii_water_01bar_from_sand`
- `calc_ptf_lal1979_group_ii_water_03bar_from_clay`
- `calc_ptf_lal1979_group_ii_water_03bar_from_sand`
- `calc_ptf_lal1979_group_ii_water_03bar_from_water_01bar`
- `calc_ptf_lal1979_group_ii_water_0bar_from_clay`
- `calc_ptf_lal1979_group_ii_water_0bar_from_sand`
- `calc_ptf_lal1979_group_ii_water_15bar_from_clay`
- `calc_ptf_lal1979_group_ii_water_15bar_from_sand`
- `calc_ptf_lal1979_group_ii_water_15bar_from_water_01bar`
- `calc_ptf_saxton1986_calcptf_parameters`
- `calc_ptf_tomasella1998`
- `calc_ptf_wang2022_h2`
- `calc_ptf_wang2022_h3`
- `calc_ptf_weynants2009`
- `calc_ptf_williams1992_function_1`
- `calc_ptf_williams1992_function_2`
- `calc_ptf_williams1992_function_3`
- `calc_ptf_williams1992_function_4`
- `calc_ptf_williams1992_function_5`
- `calc_ptf_williams1992_function_6`
- `calc_ptf_williams1992_function_7`
- `calc_ptf_williams1992_function_8`
- `calc_ptf_williams1992_table5`

| Tier | Executable PTF | Δ from previous |
| --- | ---: | ---: |
| E0 | 2 | 0 |
| E1 | 2 | 0 |
| E2 | 2 | 0 |
| E3 | 4 | 0 |
| E4 | 44 | 1 |

E0 denotes the existing strict policy, including reviewed class coordinates. Higher tiers are cumulative executable-function counts.

| Blocker | Functions |
| --- | ---: |
| target_absent | 137 |
| required_predictor_not_inventoried | 15 |
| target_pressure_unavailable_no_extrapolation | 8 |
| unacceptable_domain_or_unregistered_derivation | 6 |
| unacceptable_physical_semantics | 4 |
| particle_size_predictor_missing | 1 |
| texture_class_unavailable | 1 |

Exact common cohort comparisons:

| Scenario / route / pool | Candidates | Points / samples / profiles / sources | Best atomic RMSE | Best ensemble RMSE | Δ RMSE |
| --- | ---: | --- | ---: | ---: | ---: |
| log_psd / log_pressure_linear_interpolation_v1 / dry_bulk_density | 2 | 6 / 6 / 1 / 1 | 0.0823084 | 0.107695 | +0.0253869 |
| log_psd / log_pressure_linear_interpolation_v1 / gravimetric_water_content:100kPa | 7 | empty common cohort; see pair comparisons | — | — | — |
| log_psd / log_pressure_linear_interpolation_v1 / gravimetric_water_content:1500kPa | 20 | empty common cohort; see pair comparisons | — | — | — |
| log_psd / log_pressure_linear_interpolation_v1 / gravimetric_water_content:33kPa | 19 | empty common cohort; see pair comparisons | — | — | — |
| log_psd / log_pressure_linear_interpolation_v1 / gravimetric_water_content:500kPa | 7 | empty common cohort; see pair comparisons | — | — | — |
| log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:100kPa | 11 | 6 / 6 / 1 / 1 | 0.0147052 | 0.00938146 | -0.00532374 |
| log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:10kPa | 12 | 6 / 6 / 1 / 1 | 0.0289003 | 0.0270111 | -0.00188917 |
| log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:1500kPa | 16 | 6 / 6 / 1 / 1 | 0.0170913 | 0.0154031 | -0.00168822 |
| log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:33kPa | 14 | 6 / 6 / 1 / 1 | 0.0157085 | 0.0150849 | -0.000623613 |
| log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:500kPa | 10 | 6 / 6 / 1 / 1 | 0.0123223 | 0.0122051 | -0.000117212 |
| log_psd / van_genuchten_mualem_v1 / gravimetric_water_content:100kPa | 6 | 2 / 2 / 1 / 1 | 0.0219232 | 0.0444455 | +0.0225223 |
| log_psd / van_genuchten_mualem_v1 / gravimetric_water_content:1500kPa | 19 | 2 / 2 / 1 / 1 | 0.00759809 | 0.00750127 | -9.68263e-05 |
| log_psd / van_genuchten_mualem_v1 / gravimetric_water_content:33kPa | 18 | 2 / 2 / 1 / 1 | 0.0231063 | 0.0222585 | -0.000847793 |
| log_psd / van_genuchten_mualem_v1 / gravimetric_water_content:500kPa | 6 | 2 / 2 / 1 / 1 | 0.0120971 | 0.0415429 | +0.0294457 |
| log_psd / van_genuchten_mualem_v1 / volumetric_water_content:100kPa | 11 | 3 / 3 / 1 / 1 | 0.00823726 | 0.00831408 | +7.68192e-05 |
| log_psd / van_genuchten_mualem_v1 / volumetric_water_content:10kPa | 12 | 3 / 3 / 1 / 1 | 0.0029677 | 0.00282678 | -0.000140925 |
| log_psd / van_genuchten_mualem_v1 / volumetric_water_content:1500kPa | 16 | 3 / 3 / 1 / 1 | 0.00411045 | 0.00425818 | +0.00014773 |
| log_psd / van_genuchten_mualem_v1 / volumetric_water_content:33kPa | 14 | 3 / 3 / 1 / 1 | 0.0182299 | 0.0137021 | -0.00452782 |
| log_psd / van_genuchten_mualem_v1 / volumetric_water_content:500kPa | 10 | 3 / 3 / 1 / 1 | 0.0066173 | 0.00452559 | -0.00209171 |
| reported_boundary_proxy / brooks_corey_v1 / gravimetric_water_content:1500kPa | 3 | 2 / 2 / 0 / 1 | 0.00615882 | 0.00568458 | -0.000474247 |
| reported_boundary_proxy / brooks_corey_v1 / gravimetric_water_content:33kPa | 3 | 2 / 2 / 0 / 1 | 0.0437706 | 0.00106967 | -0.042701 |
| reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:100kPa | 3 | 2 / 2 / 0 / 1 | 0.0139848 | 0.0121945 | -0.00179037 |
| reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:10kPa | 3 | 2 / 2 / 0 / 1 | 0.0503417 | 0.0566794 | +0.00633768 |
| reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:1500kPa | 4 | 2 / 2 / 0 / 1 | 0.00612821 | 0.00894417 | +0.00281597 |
| reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:33kPa | 3 | 2 / 2 / 0 / 1 | 0.0145991 | 0.0226725 | +0.00807345 |
| reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:500kPa | 3 | 2 / 2 / 0 / 1 | 0.0113893 | 0.00865475 | -0.00273459 |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / dry_bulk_density | 2 | 6 / 6 / 1 / 1 | 0.0823084 | 0.107695 | +0.0253869 |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / gravimetric_water_content:100kPa | 7 | empty common cohort; see pair comparisons | — | — | — |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / gravimetric_water_content:1500kPa | 20 | empty common cohort; see pair comparisons | — | — | — |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / gravimetric_water_content:33kPa | 19 | empty common cohort; see pair comparisons | — | — | — |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / gravimetric_water_content:500kPa | 7 | empty common cohort; see pair comparisons | — | — | — |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:100kPa | 11 | 6 / 6 / 1 / 1 | 0.0147052 | 0.00938146 | -0.00532374 |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:10kPa | 12 | 6 / 6 / 1 / 1 | 0.0289003 | 0.0270111 | -0.00188917 |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:1500kPa | 16 | 6 / 6 / 1 / 1 | 0.0170913 | 0.0154031 | -0.00168822 |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:33kPa | 14 | 6 / 6 / 1 / 1 | 0.0157085 | 0.0150849 | -0.000623613 |
| reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:500kPa | 10 | 6 / 6 / 1 / 1 | 0.0123223 | 0.0122051 | -0.000117212 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / gravimetric_water_content:100kPa | 6 | 2 / 2 / 1 / 1 | 0.0219232 | 0.0444455 | +0.0225223 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / gravimetric_water_content:1500kPa | 19 | 2 / 2 / 1 / 1 | 0.00759809 | 0.00750127 | -9.68263e-05 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / gravimetric_water_content:33kPa | 18 | 2 / 2 / 1 / 1 | 0.0231063 | 0.0222585 | -0.000847793 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / gravimetric_water_content:500kPa | 6 | 2 / 2 / 1 / 1 | 0.0120971 | 0.0415429 | +0.0294457 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:100kPa | 11 | 3 / 3 / 1 / 1 | 0.00823726 | 0.00831408 | +7.68192e-05 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:10kPa | 12 | 3 / 3 / 1 / 1 | 0.0029677 | 0.00282678 | -0.000140925 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:1500kPa | 16 | 3 / 3 / 1 / 1 | 0.00411045 | 0.00425818 | +0.00014773 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:33kPa | 14 | 3 / 3 / 1 / 1 | 0.0182299 | 0.0137021 | -0.00452782 |
| reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:500kPa | 10 | 3 / 3 / 1 / 1 | 0.0066173 | 0.00452559 | -0.00209171 |
| strict / strict_observed / curve:volumetric_water_content | 2 | 56 / 6 / 1 / 1 | 0.0227324 | 0.0267555 | +0.0040231 |

Coverage uses the union of executable coordinates within each scenario/route/pool. Dataset sample coverage is also reported against all retained canonical samples. RMSE, MAE and bias weight samples equally; median absolute error and residual Pearson correlations weight points equally. Unknown profile IDs are counted separately.

Ranking sensitivity:

| Comparison | Pools tested | Pools with ordering changes | Changed pair orderings |
| --- | ---: | ---: | ---: |
| psd_scenarios | 15 | 0 | 0 |
| target_routes | 32 | 19 | 60 |

<details><summary>Atomic performance and complementarity</summary>

log_psd / log_pressure_linear_interpolation_v1 / dry_bulk_density

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_saxton2006` | 0.0823084 | 0.0677162 | 0.057588 | 0.0660434 | 0.500 | 0.055 | E3 / E3 |
| 2 | `calc_ptf_wosten2001_loam_clay_table5` | 0.138237 | 0.121174 | 0.121174 | 0.0857764 | 1.000 | 0.110 | E3 / E3 |

Pareto: `calc_ptf_saxton2006`, `calc_ptf_wosten2001_loam_clay_table5`.

Best atomic: `calc_ptf_saxton2006`; best ensemble: equal_weight_mean (calc_ptf_saxton2006, calc_ptf_wosten2001_loam_clay_table5).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_saxton2006` / `calc_ptf_wosten2001_loam_clay_table5`: 0.8374

log_psd / log_pressure_linear_interpolation_v1 / gravimetric_water_content:100kPa

Empty roster common cohort; 20/21 exact pair cohorts are executable. Full pair metrics and ensemble comparisons are retained separately in summary.json. They do not form a shared leaderboard.

log_psd / log_pressure_linear_interpolation_v1 / gravimetric_water_content:1500kPa

Empty roster common cohort; 188/190 exact pair cohorts are executable. Full pair metrics and ensemble comparisons are retained separately in summary.json. They do not form a shared leaderboard.

log_psd / log_pressure_linear_interpolation_v1 / gravimetric_water_content:33kPa

Empty roster common cohort; 170/171 exact pair cohorts are executable. Full pair metrics and ensemble comparisons are retained separately in summary.json. They do not form a shared leaderboard.

log_psd / log_pressure_linear_interpolation_v1 / gravimetric_water_content:500kPa

Empty roster common cohort; 20/21 exact pair cohorts are executable. Full pair metrics and ensemble comparisons are retained separately in summary.json. They do not form a shared leaderboard.

log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:100kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0147052 | 0.0121569 | -0.00356205 | 0.0122248 | 0.500 | 0.055 | E2 / E2 |
| 2 | `calc_ptf_rawls1982_full_wrc` | 0.015411 | 0.014644 | -0.014644 | 0.0143178 | 0.500 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_saxton2006` | 0.0206787 | 0.0179882 | -0.0111154 | 0.0173108 | 0.500 | 0.055 | E4 / E4 |
| 4 | `calc_ptf_vereecken1989` | 0.0213374 | 0.016287 | 0.00376299 | 0.00952958 | 0.500 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_mayr1999` | 0.0221944 | 0.0167631 | 0.0159797 | 0.0154007 | 0.500 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_varallyai1982_meadow` | 0.0265966 | 0.0233694 | 0.0222422 | 0.0235735 | 0.500 | 0.055 | E4 / E4 |
| 7 | `calc_ptf_varallyai1982_chernozem_b` | 0.0277292 | 0.0246883 | -0.0227945 | 0.0246906 | 1.000 | 0.110 | E4 / E4 |
| 8 | `calc_ptf_clapp1978` | 0.0307731 | 0.0272659 | 0.0272659 | 0.0265031 | 0.500 | 0.055 | E2 / E2 |
| 9 | `calc_ptf_varallyai1982_chernozem_a` | 0.0354268 | 0.0320455 | -0.0320455 | 0.03726 | 1.000 | 0.110 | E4 / E4 |
| 10 | `calc_ptf_tomasella1998` | 0.084585 | 0.0833085 | 0.0833085 | 0.0816874 | 0.500 | 0.055 | E4 / E4 |
| 11 | `calc_ptf_varallyai1982_chernozem_c` | 0.0984015 | 0.0912305 | -0.0912305 | 0.0734192 | 1.000 | 0.110 | E4 / E4 |

Pareto: `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_pair (calc_ptf_rawls1982_full_wrc, calc_ptf_varallyai1982_meadow).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: 0.0262
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_vereecken1989`: 0.3620
- `calc_ptf_saxton2006` / `calc_ptf_varallyai1982_chernozem_c`: 0.3745

log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:10kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0289003 | 0.0247246 | -0.00908475 | 0.0264586 | 0.500 | 0.055 | E2 / E2 |
| 2 | `calc_ptf_gunarathna2019_vwc10_set1` | 0.0297891 | 0.0238034 | 0.0127145 | 0.0166608 | 0.500 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_rawls1982_full_wrc` | 0.0353025 | 0.0266553 | -0.0148305 | 0.0160801 | 0.500 | 0.055 | E4 / E4 |
| 4 | `calc_ptf_vereecken1989` | 0.0371322 | 0.0249697 | -0.0167244 | 0.0137025 | 0.500 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_clapp1978` | 0.0388219 | 0.0289354 | 0.0274671 | 0.0244057 | 0.500 | 0.055 | E2 / E2 |
| 6 | `calc_ptf_varallyai1982_chernozem_c` | 0.0487327 | 0.0423372 | -0.0351609 | 0.0474419 | 1.000 | 0.110 | E4 / E4 |
| 7 | `calc_ptf_mayr1999` | 0.0501021 | 0.0424276 | -0.0422979 | 0.0356312 | 0.500 | 0.055 | E4 / E4 |
| 8 | `calc_ptf_varallyai1982_chernozem_b` | 0.0712807 | 0.0648594 | -0.0648594 | 0.0793671 | 1.000 | 0.110 | E4 / E4 |
| 9 | `calc_ptf_varallyai1982_chernozem_a` | 0.0733669 | 0.0689948 | -0.0689948 | 0.0675683 | 1.000 | 0.110 | E4 / E4 |
| 10 | `calc_ptf_saxton2006` | 0.0827487 | 0.0724173 | 0.0724173 | 0.0827992 | 0.500 | 0.055 | E4 / E4 |
| 11 | `calc_ptf_varallyai1982_meadow` | 0.0974611 | 0.0930275 | -0.0930275 | 0.0818124 | 0.500 | 0.055 | E4 / E4 |
| 12 | `calc_ptf_tomasella1998` | 0.110493 | 0.107009 | 0.107009 | 0.103775 | 0.500 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_c`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_pair (calc_ptf_gunarathna2019_vwc10_set1, calc_ptf_rawls1982_full_wrc).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_rawls1982_full_wrc` / `calc_ptf_varallyai1982_chernozem_c`: 0.1618
- `calc_ptf_rawls1982_full_wrc` / `calc_ptf_varallyai1982_chernozem_b`: 0.3558
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_vereecken1989`: 0.4465

log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:1500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0170913 | 0.0140458 | 0.00888716 | 0.0156301 | 0.500 | 0.055 | E2 / E2 |
| 2 | `calc_ptf_rawls2003_soc_theta1500_tree` | 0.0194257 | 0.0160458 | -0.0103461 | 0.0159916 | 0.500 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_rawls2003_soc_theta1500_gmdh` | 0.0214464 | 0.0171365 | -0.0119918 | 0.0177554 | 0.500 | 0.055 | E4 / E4 |
| 4 | `calc_ptf_saxton2006` | 0.0234463 | 0.0178939 | -0.0142638 | 0.0182428 | 0.500 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_vereecken1989` | 0.024314 | 0.0193232 | 0.0126863 | 0.0233725 | 0.500 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_varallyai1982_chernozem_b` | 0.0253434 | 0.0199264 | -0.015174 | 0.0218645 | 1.000 | 0.110 | E4 / E4 |
| 7 | `calc_ptf_rawls1982_theta_1500` | 0.0301559 | 0.0251766 | 0.0171707 | 0.0299712 | 1.000 | 0.110 | E4 / E4 |
| 8 | `calc_ptf_varallyai1982_chernozem_a` | 0.0343373 | 0.0289188 | -0.0289188 | 0.0279815 | 1.000 | 0.110 | E4 / E4 |
| 9 | `calc_ptf_clapp1978` | 0.0354262 | 0.0322783 | 0.0322783 | 0.0333185 | 0.500 | 0.055 | E2 / E2 |
| 10 | `calc_ptf_tomasella1998` | 0.043073 | 0.040238 | 0.040238 | 0.039985 | 0.500 | 0.055 | E4 / E4 |
| 11 | `calc_ptf_mayr1999` | 0.0552622 | 0.0532768 | 0.0532768 | 0.0526801 | 0.500 | 0.055 | E4 / E4 |
| 12 | `calc_ptf_varallyai1982_meadow` | 0.0959499 | 0.0935856 | 0.0935856 | 0.0938776 | 0.500 | 0.055 | E4 / E4 |
| 13 | `calc_ptf_varallyai1982_chernozem_c` | 0.105331 | 0.104753 | -0.104753 | 0.10756 | 1.000 | 0.110 | E4 / E4 |
| 14 | `calc_ptf_gunarathna2019_vwc1500_set3` | 0.156701 | 0.155372 | 0.155372 | 0.155619 | 0.500 | 0.055 | E4 / E4 |
| 15 | `calc_ptf_gunarathna2019_vwc1500_set1` | 0.157562 | 0.156844 | 0.156844 | 0.157161 | 0.500 | 0.055 | E4 / E4 |
| 16 | `calc_ptf_gunarathna2019_vwc1500_set4` | 0.167383 | 0.165879 | 0.165879 | 0.169716 | 0.500 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_pair (calc_ptf_cosby1984_univariate, calc_ptf_rawls2003_soc_theta1500_tree).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_chernozem_c`: 0.6783
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: 0.6853
- `calc_ptf_gunarathna2019_vwc1500_set3` / `calc_ptf_varallyai1982_chernozem_c`: 0.7007

log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:33kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_mayr1999` | 0.0157085 | 0.014288 | -0.00196935 | 0.0154875 | 0.500 | 0.055 | E4 / E4 |
| 2 | `calc_ptf_cosby1984_univariate` | 0.017132 | 0.0157695 | -0.00101024 | 0.0138937 | 0.500 | 0.055 | E2 / E2 |
| 3 | `calc_ptf_saxton2006` | 0.0198127 | 0.0173132 | 0.00784871 | 0.0154092 | 0.500 | 0.055 | E4 / E4 |
| 4 | `calc_ptf_rawls2003_soc_theta33_gmdh` | 0.0217168 | 0.0193882 | 0.0102578 | 0.0199628 | 0.500 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_varallyai1982_meadow` | 0.02339 | 0.0192777 | -0.0192777 | 0.0184473 | 0.500 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_vereecken1989` | 0.0237588 | 0.0204174 | 0.0135956 | 0.0189984 | 0.500 | 0.055 | E4 / E4 |
| 7 | `calc_ptf_rawls2003_soc_theta33_tree` | 0.0246398 | 0.0204862 | 0.0166335 | 0.0178552 | 0.500 | 0.055 | E4 / E4 |
| 8 | `calc_ptf_clapp1978` | 0.036968 | 0.0327741 | 0.0327741 | 0.0325403 | 0.500 | 0.055 | E2 / E2 |
| 9 | `calc_ptf_varallyai1982_chernozem_b` | 0.0380917 | 0.0292802 | -0.0292802 | 0.0205557 | 1.000 | 0.110 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_chernozem_a` | 0.0394817 | 0.0356456 | -0.0356456 | 0.0405461 | 1.000 | 0.110 | E4 / E4 |
| 11 | `calc_ptf_rawls1982_theta_33` | 0.0517826 | 0.0477892 | 0.0477892 | 0.0494161 | 0.500 | 0.055 | E4 / E4 |
| 12 | `calc_ptf_gunarathna2019_vwc33_set1` | 0.0666053 | 0.0643553 | 0.0643553 | 0.0632527 | 0.500 | 0.055 | E4 / E4 |
| 13 | `calc_ptf_varallyai1982_chernozem_c` | 0.0692054 | 0.0516193 | -0.0516193 | 0.0253675 | 1.000 | 0.110 | E4 / E4 |
| 14 | `calc_ptf_tomasella1998` | 0.0806787 | 0.0788251 | 0.0788251 | 0.0776416 | 0.500 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_mayr1999`, `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_mayr1999`; best ensemble: equal_weight_pair (calc_ptf_rawls2003_soc_theta33_tree, calc_ptf_varallyai1982_meadow).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: 0.3426
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_vereecken1989`: 0.4223
- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: 0.5007

log_psd / log_pressure_linear_interpolation_v1 / volumetric_water_content:500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0123223 | 0.0101128 | -0.00289413 | 0.00772258 | 0.500 | 0.055 | E2 / E2 |
| 2 | `calc_ptf_vereecken1989` | 0.0199411 | 0.0152989 | -0.00594336 | 0.0117712 | 0.500 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_clapp1978` | 0.0263449 | 0.0234647 | 0.0234647 | 0.0209753 | 0.500 | 0.055 | E2 / E2 |
| 4 | `calc_ptf_varallyai1982_chernozem_b` | 0.0266104 | 0.0232704 | -0.0232704 | 0.023655 | 1.000 | 0.110 | E4 / E4 |
| 5 | `calc_ptf_saxton2006` | 0.0279852 | 0.0240912 | -0.0226735 | 0.0226157 | 0.500 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_mayr1999` | 0.037363 | 0.0347717 | 0.0347717 | 0.0319453 | 0.500 | 0.055 | E4 / E4 |
| 7 | `calc_ptf_varallyai1982_chernozem_a` | 0.0387913 | 0.0360003 | -0.0360003 | 0.0353272 | 1.000 | 0.110 | E4 / E4 |
| 8 | `calc_ptf_tomasella1998` | 0.0660518 | 0.0648426 | 0.0648426 | 0.062692 | 0.500 | 0.055 | E4 / E4 |
| 9 | `calc_ptf_varallyai1982_meadow` | 0.0669893 | 0.0647248 | 0.0647248 | 0.0679246 | 0.500 | 0.055 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_chernozem_c` | 0.120015 | 0.118999 | -0.118999 | 0.117471 | 1.000 | 0.110 | E4 / E4 |

Pareto: `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_pair (calc_ptf_clapp1978, calc_ptf_varallyai1982_chernozem_b).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: -0.0379
- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_chernozem_c`: 0.2065
- `calc_ptf_varallyai1982_chernozem_a` / `calc_ptf_varallyai1982_chernozem_c`: 0.2563

log_psd / van_genuchten_mualem_v1 / gravimetric_water_content:100kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_oosterveld1980_retention` | 0.0219232 | 0.0173324 | -0.0134244 | 0.0173324 | 0.667 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_chakraborty2011_eq2` | 0.0962692 | 0.0942303 | 0.0942303 | 0.0942303 | 0.667 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_chakraborty2011_eq5` | 0.139228 | 0.138023 | 0.138023 | 0.138023 | 0.667 | 0.018 | E4 / E4 |
| 4 | `calc_ptf_chakraborty2011_eq4` | 0.140417 | 0.139253 | 0.139253 | 0.139253 | 1.000 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_chakraborty2011_eq1` | 0.142535 | 0.141393 | 0.141393 | 0.141393 | 1.000 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_chakraborty2011_eq3` | 0.153597 | 0.152751 | 0.152751 | 0.152751 | 0.667 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_oosterveld1980_retention`, `calc_ptf_chakraborty2011_eq4`.

Best atomic: `calc_ptf_oosterveld1980_retention`; best ensemble: equal_weight_pair (calc_ptf_chakraborty2011_eq2, calc_ptf_oosterveld1980_retention).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

log_psd / van_genuchten_mualem_v1 / gravimetric_water_content:1500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_beniaich2023_mlr4` | 0.00759809 | 0.00741359 | 0.00166423 | 0.00741359 | 0.375 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_beniaich2023_slr1` | 0.00799482 | 0.00755961 | -0.00260181 | 0.00755961 | 0.375 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_oosterveld1980_wilting_point` | 0.00950095 | 0.00676644 | -0.00666958 | 0.00676644 | 0.250 | 0.018 | E4 / E4 |
| 4 | `calc_ptf_oosterveld1980_retention` | 0.0149221 | 0.013298 | 0.013298 | 0.013298 | 0.250 | 0.018 | E4 / E4 |
| 5 | `calc_ptf_myeni2021_pwp` | 0.0412615 | 0.0405896 | 0.0405896 | 0.0405896 | 0.375 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_beniaich2023_slr4` | 0.0461525 | 0.0456908 | 0.0456908 | 0.0456908 | 0.375 | 0.028 | E4 / E4 |
| 7 | `calc_ptf_chakraborty2011_eq5` | 0.0654851 | 0.0649264 | 0.0649264 | 0.0649264 | 0.250 | 0.018 | E4 / E4 |
| 8 | `calc_ptf_beniaich2023_mlr5` | 0.0657134 | 0.0652939 | 0.0652939 | 0.0652939 | 0.375 | 0.028 | E4 / E4 |
| 9 | `calc_ptf_beniaich2023_mlr1` | 0.0659451 | 0.065527 | 0.065527 | 0.065527 | 0.375 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_beniaich2023_slr5` | 0.0722905 | 0.0719638 | 0.0719638 | 0.0719638 | 0.375 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_chakraborty2011_eq4` | 0.0729132 | 0.0725501 | 0.0725501 | 0.0725501 | 0.375 | 0.028 | E4 / E4 |
| 12 | `calc_ptf_chakraborty2011_eq1` | 0.0745428 | 0.0741909 | 0.0741909 | 0.0741909 | 0.375 | 0.028 | E4 / E4 |
| 13 | `calc_ptf_beniaich2023_slr6` | 0.0750305 | 0.0747291 | 0.0747291 | 0.0747291 | 1.000 | 0.073 | E4 / E4 |
| 14 | `calc_ptf_chakraborty2011_eq3` | 0.0769491 | 0.0766464 | 0.0766464 | 0.0766464 | 0.250 | 0.018 | E4 / E4 |
| 15 | `calc_ptf_chakraborty2011_eq2` | 0.0885298 | 0.0881695 | 0.0881695 | 0.0881695 | 0.250 | 0.018 | E4 / E4 |
| 16 | `calc_ptf_beniaich2023_slr3` | 0.107346 | 0.107093 | 0.107093 | 0.107093 | 0.375 | 0.028 | E4 / E4 |
| 17 | `calc_ptf_beniaich2023_mlr2` | 0.109607 | 0.109365 | 0.109365 | 0.109365 | 0.375 | 0.028 | E4 / E4 |
| 18 | `calc_ptf_beniaich2023_slr2` | 0.139012 | 0.138843 | 0.138843 | 0.138843 | 0.375 | 0.028 | E4 / E4 |
| 19 | `calc_ptf_beniaich2023_mlr3` | 0.14061 | 0.140449 | 0.140449 | 0.140449 | 0.375 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_beniaich2023_mlr4`, `calc_ptf_beniaich2023_slr6`.

Best atomic: `calc_ptf_beniaich2023_mlr4`; best ensemble: equal_weight_pair (calc_ptf_beniaich2023_mlr4, calc_ptf_beniaich2023_slr1).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

log_psd / van_genuchten_mualem_v1 / gravimetric_water_content:33kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_beniaich2023_slr6` | 0.0231063 | 0.0220663 | 0.00685414 | 0.0220663 | 1.000 | 0.110 | E4 / E4 |
| 2 | `calc_ptf_myeni2021_fc` | 0.0233412 | 0.0232232 | 0.00234438 | 0.0232232 | 0.250 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_beniaich2023_slr5` | 0.0243923 | 0.0223559 | -0.00975689 | 0.0223559 | 0.250 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_beniaich2023_mlr5` | 0.0337767 | 0.0248826 | 0.0248826 | 0.0248826 | 0.250 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_beniaich2023_mlr1` | 0.0340576 | 0.0252626 | 0.0252626 | 0.0252626 | 0.250 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_oosterveld1980_retention` | 0.0398914 | 0.0332204 | -0.0332204 | 0.0332204 | 0.167 | 0.018 | E4 / E4 |
| 7 | `calc_ptf_beniaich2023_slr4` | 0.0440961 | 0.038366 | -0.038366 | 0.038366 | 0.250 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_beniaich2023_slr3` | 0.0520992 | 0.0467855 | 0.0467855 | 0.0467855 | 0.250 | 0.028 | E4 / E4 |
| 9 | `calc_ptf_beniaich2023_mlr2` | 0.055245 | 0.0503389 | 0.0503389 | 0.0503389 | 0.250 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_beniaich2023_mlr4` | 0.0780935 | 0.0746785 | -0.0746785 | 0.0746785 | 0.250 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_beniaich2023_slr1` | 0.0841832 | 0.0809622 | -0.0809622 | 0.0809622 | 0.250 | 0.028 | E4 / E4 |
| 12 | `calc_ptf_chakraborty2011_eq2` | 0.102368 | 0.0997744 | 0.0997744 | 0.0997744 | 0.167 | 0.018 | E4 / E4 |
| 13 | `calc_ptf_beniaich2023_slr2` | 0.109071 | 0.106778 | 0.106778 | 0.106778 | 0.250 | 0.028 | E4 / E4 |
| 14 | `calc_ptf_beniaich2023_mlr3` | 0.110217 | 0.107984 | 0.107984 | 0.107984 | 0.250 | 0.028 | E4 / E4 |
| 15 | `calc_ptf_chakraborty2011_eq4` | 0.167574 | 0.166004 | 0.166004 | 0.166004 | 0.250 | 0.028 | E4 / E4 |
| 16 | `calc_ptf_chakraborty2011_eq1` | 0.168958 | 0.167407 | 0.167407 | 0.167407 | 0.250 | 0.028 | E4 / E4 |
| 17 | `calc_ptf_chakraborty2011_eq5` | 0.183572 | 0.182461 | 0.182461 | 0.182461 | 0.167 | 0.018 | E4 / E4 |
| 18 | `calc_ptf_chakraborty2011_eq3` | 0.196149 | 0.195297 | 0.195297 | 0.195297 | 0.167 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_beniaich2023_slr6`, `calc_ptf_myeni2021_fc`.

Best atomic: `calc_ptf_beniaich2023_slr6`; best ensemble: equal_weight_pair (calc_ptf_beniaich2023_slr5, calc_ptf_beniaich2023_slr6).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

log_psd / van_genuchten_mualem_v1 / gravimetric_water_content:500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_oosterveld1980_retention` | 0.0120971 | 0.0102379 | 0.00644401 | 0.0102379 | 0.667 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_chakraborty2011_eq5` | 0.0747168 | 0.0739295 | 0.0739295 | 0.0739295 | 0.667 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_chakraborty2011_eq4` | 0.0748494 | 0.0740514 | 0.0740514 | 0.0740514 | 1.000 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_chakraborty2011_eq1` | 0.0754782 | 0.0746928 | 0.0746928 | 0.0746928 | 1.000 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_chakraborty2011_eq3` | 0.0870427 | 0.0865763 | 0.0865763 | 0.0865763 | 0.667 | 0.018 | E4 / E4 |
| 6 | `calc_ptf_chakraborty2011_eq2` | 0.104388 | 0.103873 | 0.103873 | 0.103873 | 0.667 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_oosterveld1980_retention`, `calc_ptf_chakraborty2011_eq4`, `calc_ptf_chakraborty2011_eq1`.

Best atomic: `calc_ptf_oosterveld1980_retention`; best ensemble: equal_weight_pair (calc_ptf_chakraborty2011_eq5, calc_ptf_oosterveld1980_retention).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

log_psd / van_genuchten_mualem_v1 / volumetric_water_content:100kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_rawls1982_full_wrc` | 0.00823726 | 0.00785633 | -0.00785633 | 0.00823113 | 1.000 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_saxton2006` | 0.0147577 | 0.0113727 | 0.00429214 | 0.0100457 | 1.000 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_cosby1984_univariate` | 0.0154431 | 0.0123282 | 0.00633025 | 0.00899692 | 1.000 | 0.028 | E2 / E2 |
| 4 | `calc_ptf_varallyai1982_chernozem_b` | 0.0241619 | 0.0219419 | -0.0162351 | 0.0242491 | 1.000 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_varallyai1982_chernozem_a` | 0.0242123 | 0.0195175 | -0.0194935 | 0.0244303 | 1.000 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_vereecken1989` | 0.02653 | 0.020241 | 0.020241 | 0.0138316 | 1.000 | 0.028 | E4 / E4 |
| 7 | `calc_ptf_mayr1999` | 0.0306964 | 0.0268332 | 0.0268332 | 0.0233567 | 1.000 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_clapp1978` | 0.0397385 | 0.0371582 | 0.0371582 | 0.0338021 | 1.000 | 0.028 | E2 / E2 |
| 9 | `calc_ptf_varallyai1982_meadow` | 0.0404246 | 0.0399896 | 0.0399896 | 0.0393915 | 1.000 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_tomasella1998` | 0.0948539 | 0.093716 | 0.093716 | 0.0898771 | 1.000 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_varallyai1982_chernozem_c` | 0.110296 | 0.102632 | -0.102632 | 0.116872 | 1.000 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_rawls1982_full_wrc`, `calc_ptf_saxton2006`, `calc_ptf_cosby1984_univariate`.

Best atomic: `calc_ptf_rawls1982_full_wrc`; best ensemble: equal_weight_pair (calc_ptf_cosby1984_univariate, calc_ptf_rawls1982_full_wrc).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: 0.9687
- `calc_ptf_rawls1982_full_wrc` / `calc_ptf_varallyai1982_chernozem_b`: 0.9770
- `calc_ptf_varallyai1982_meadow` / `calc_ptf_vereecken1989`: 0.9809

log_psd / van_genuchten_mualem_v1 / volumetric_water_content:10kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_vereecken1989` | 0.0029677 | 0.002683 | -0.00150248 | 0.00180154 | 1.000 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_rawls1982_full_wrc` | 0.011682 | 0.0102815 | 0.000758818 | 0.0141217 | 1.000 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_cosby1984_univariate` | 0.0125682 | 0.0116217 | -0.00633419 | 0.00855482 | 1.000 | 0.028 | E2 / E2 |
| 4 | `calc_ptf_gunarathna2019_vwc10_set1` | 0.0196899 | 0.0160287 | 0.0160287 | 0.0132878 | 1.000 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_clapp1978` | 0.0321083 | 0.0302176 | 0.0302176 | 0.027997 | 1.000 | 0.028 | E2 / E2 |
| 6 | `calc_ptf_mayr1999` | 0.0347997 | 0.0345312 | -0.0345312 | 0.0337356 | 1.000 | 0.028 | E4 / E4 |
| 7 | `calc_ptf_varallyai1982_chernozem_c` | 0.0566964 | 0.046216 | -0.046216 | 0.0549108 | 1.000 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_varallyai1982_chernozem_a` | 0.062862 | 0.0620178 | -0.0620178 | 0.0648277 | 1.000 | 0.028 | E4 / E4 |
| 9 | `calc_ptf_varallyai1982_chernozem_b` | 0.075704 | 0.0719475 | -0.0719475 | 0.0806624 | 1.000 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_meadow` | 0.0813499 | 0.0813322 | -0.0813322 | 0.0803347 | 1.000 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_saxton2006` | 0.0882996 | 0.0878175 | 0.0878175 | 0.0840879 | 1.000 | 0.028 | E4 / E4 |
| 12 | `calc_ptf_tomasella1998` | 0.110602 | 0.110009 | 0.110009 | 0.107469 | 1.000 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_vereecken1989`, `calc_ptf_rawls1982_full_wrc`, `calc_ptf_cosby1984_univariate`.

Best atomic: `calc_ptf_vereecken1989`; best ensemble: equal_weight_pair (calc_ptf_cosby1984_univariate, calc_ptf_rawls1982_full_wrc).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_saxton2006` / `calc_ptf_varallyai1982_meadow`: 0.7531
- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: 0.7696
- `calc_ptf_varallyai1982_chernozem_a` / `calc_ptf_varallyai1982_meadow`: 0.8124

log_psd / van_genuchten_mualem_v1 / volumetric_water_content:1500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_a` | 0.00411045 | 0.00362306 | -0.00362306 | 0.00307974 | 1.000 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_saxton2006` | 0.011235 | 0.0106338 | 0.0106338 | 0.0093847 | 1.000 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_rawls2003_soc_theta1500_gmdh` | 0.0126598 | 0.0121484 | 0.0121484 | 0.0107398 | 1.000 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_varallyai1982_chernozem_b` | 0.0129284 | 0.0117561 | 0.0117561 | 0.00881907 | 1.000 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_rawls2003_soc_theta1500_tree` | 0.0130538 | 0.0127034 | 0.0127034 | 0.0108384 | 1.000 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_cosby1984_univariate` | 0.030087 | 0.0299366 | 0.0299366 | 0.0280716 | 1.000 | 0.028 | E2 / E2 |
| 7 | `calc_ptf_vereecken1989` | 0.0393385 | 0.0389901 | 0.0389901 | 0.0365334 | 1.000 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_rawls1982_theta_1500` | 0.0471746 | 0.0470563 | 0.0470563 | 0.0472705 | 1.000 | 0.028 | E4 / E4 |
| 9 | `calc_ptf_clapp1978` | 0.0534122 | 0.0533277 | 0.0533277 | 0.0514627 | 1.000 | 0.028 | E2 / E2 |
| 10 | `calc_ptf_tomasella1998` | 0.0622634 | 0.0621555 | 0.0621555 | 0.0600841 | 1.000 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_mayr1999` | 0.0732458 | 0.0727776 | 0.0727776 | 0.0683227 | 1.000 | 0.028 | E4 / E4 |
| 12 | `calc_ptf_varallyai1982_chernozem_c` | 0.0898145 | 0.0893357 | -0.0893357 | 0.0945366 | 1.000 | 0.028 | E4 / E4 |
| 13 | `calc_ptf_varallyai1982_meadow` | 0.12124 | 0.121172 | 0.121172 | 0.121008 | 1.000 | 0.028 | E4 / E4 |
| 14 | `calc_ptf_gunarathna2019_vwc1500_set1` | 0.178385 | 0.17835 | 0.17835 | 0.176171 | 1.000 | 0.028 | E4 / E4 |
| 15 | `calc_ptf_gunarathna2019_vwc1500_set3` | 0.182331 | 0.182293 | 0.182293 | 0.18125 | 1.000 | 0.028 | E4 / E4 |
| 16 | `calc_ptf_gunarathna2019_vwc1500_set4` | 0.193727 | 0.193705 | 0.193705 | 0.193947 | 1.000 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_a`, `calc_ptf_cosby1984_univariate`.

Best atomic: `calc_ptf_varallyai1982_chernozem_a`; best ensemble: equal_weight_pair (calc_ptf_saxton2006, calc_ptf_varallyai1982_chernozem_a).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_mayr1999` / `calc_ptf_varallyai1982_chernozem_a`: 0.0664
- `calc_ptf_gunarathna2019_vwc1500_set4` / `calc_ptf_varallyai1982_chernozem_b`: -0.0683
- `calc_ptf_rawls1982_theta_1500` / `calc_ptf_varallyai1982_chernozem_b`: -0.0818

log_psd / van_genuchten_mualem_v1 / volumetric_water_content:33kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_mayr1999` | 0.0182299 | 0.0165947 | -0.00869339 | 0.011852 | 1.000 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_saxton2006` | 0.0186166 | 0.0144965 | 0.0046332 | 0.0147949 | 1.000 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_rawls2003_soc_theta33_gmdh` | 0.0188557 | 0.0151264 | 0.0071897 | 0.011905 | 1.000 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_cosby1984_univariate` | 0.0210012 | 0.0193125 | -0.0103688 | 0.0135412 | 1.000 | 0.028 | E2 / E2 |
| 5 | `calc_ptf_vereecken1989` | 0.0215637 | 0.0166644 | 0.0132367 | 0.00895917 | 1.000 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_varallyai1982_meadow` | 0.022389 | 0.0202494 | -0.0202494 | 0.0204397 | 1.000 | 0.028 | E4 / E4 |
| 7 | `calc_ptf_rawls2003_soc_theta33_tree` | 0.0235964 | 0.0187218 | 0.0149416 | 0.0117691 | 1.000 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_clapp1978` | 0.0296956 | 0.0234156 | 0.0234156 | 0.0202431 | 1.000 | 0.028 | E2 / E2 |
| 9 | `calc_ptf_rawls1982_theta_33` | 0.0412101 | 0.0386235 | 0.0386235 | 0.0357614 | 1.000 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_chernozem_a` | 0.0463562 | 0.0423009 | -0.0423009 | 0.0469942 | 1.000 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_varallyai1982_chernozem_b` | 0.0532821 | 0.045939 | -0.045939 | 0.0551766 | 1.000 | 0.028 | E4 / E4 |
| 12 | `calc_ptf_gunarathna2019_vwc33_set1` | 0.0586275 | 0.0555299 | 0.0555299 | 0.0518653 | 1.000 | 0.028 | E4 / E4 |
| 13 | `calc_ptf_tomasella1998` | 0.0725621 | 0.0700583 | 0.0700583 | 0.0663308 | 1.000 | 0.028 | E4 / E4 |
| 14 | `calc_ptf_varallyai1982_chernozem_c` | 0.0974946 | 0.0841596 | -0.0841596 | 0.0988675 | 1.000 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_mayr1999`, `calc_ptf_saxton2006`, `calc_ptf_cosby1984_univariate`.

Best atomic: `calc_ptf_mayr1999`; best ensemble: equal_weight_pair (calc_ptf_varallyai1982_meadow, calc_ptf_vereecken1989).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: 0.9736
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: 0.9803
- `calc_ptf_saxton2006` / `calc_ptf_varallyai1982_meadow`: 0.9861

log_psd / van_genuchten_mualem_v1 / volumetric_water_content:500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_a` | 0.0066173 | 0.00602348 | -0.00455789 | 0.00740128 | 1.000 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_varallyai1982_chernozem_b` | 0.00834504 | 0.00727585 | 0.00727585 | 0.00753751 | 1.000 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_saxton2006` | 0.0116746 | 0.00960759 | 0.00960759 | 0.00509547 | 1.000 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_cosby1984_univariate` | 0.0256454 | 0.0248762 | 0.0248762 | 0.0217985 | 1.000 | 0.028 | E2 / E2 |
| 5 | `calc_ptf_vereecken1989` | 0.0288458 | 0.0272094 | 0.0272094 | 0.0210424 | 1.000 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_clapp1978` | 0.0516129 | 0.0512351 | 0.0512351 | 0.0481573 | 1.000 | 0.028 | E2 / E2 |
| 7 | `calc_ptf_mayr1999` | 0.0626202 | 0.0617884 | 0.0617884 | 0.0572513 | 1.000 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_tomasella1998` | 0.0935225 | 0.0932737 | 0.0932737 | 0.0896271 | 1.000 | 0.028 | E4 / E4 |
| 9 | `calc_ptf_varallyai1982_meadow` | 0.0995759 | 0.0995666 | 0.0995666 | 0.0989193 | 1.000 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_chernozem_c` | 0.10386 | 0.102136 | -0.102136 | 0.110771 | 1.000 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_a`, `calc_ptf_cosby1984_univariate`.

Best atomic: `calc_ptf_varallyai1982_chernozem_a`; best ensemble: equal_weight_pair (calc_ptf_varallyai1982_chernozem_a, calc_ptf_varallyai1982_chernozem_b).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: -0.1347
- `calc_ptf_varallyai1982_chernozem_a` / `calc_ptf_varallyai1982_meadow`: -0.5752
- `calc_ptf_saxton2006` / `calc_ptf_varallyai1982_meadow`: -0.6637

reported_boundary_proxy / brooks_corey_v1 / gravimetric_water_content:1500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_beniaich2023_slr1` | 0.00615882 | 0.00607638 | -0.00100434 | 0.00607638 | 0.500 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_beniaich2023_mlr4` | 0.00670863 | 0.00486794 | 0.00486794 | 0.00486794 | 0.500 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_beniaich2023_slr6` | 0.091119 | 0.0908556 | 0.0908556 | 0.0908556 | 1.000 | 0.037 | E4 / E4 |

Pareto: `calc_ptf_beniaich2023_slr1`, `calc_ptf_beniaich2023_slr6`.

Best atomic: `calc_ptf_beniaich2023_slr1`; best ensemble: equal_weight_pair (calc_ptf_beniaich2023_mlr4, calc_ptf_beniaich2023_slr1).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / brooks_corey_v1 / gravimetric_water_content:33kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_beniaich2023_mlr4` | 0.0437706 | 0.0435654 | -0.0435654 | 0.0435654 | 0.400 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_beniaich2023_slr1` | 0.0527108 | 0.0523119 | -0.0523119 | 0.0523119 | 0.400 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_beniaich2023_slr6` | 0.0530552 | 0.0523517 | 0.0523517 | 0.0523517 | 1.000 | 0.046 | E4 / E4 |

Pareto: `calc_ptf_beniaich2023_mlr4`, `calc_ptf_beniaich2023_slr6`.

Best atomic: `calc_ptf_beniaich2023_mlr4`; best ensemble: equal_weight_pair (calc_ptf_beniaich2023_slr1, calc_ptf_beniaich2023_slr6).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:100kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_b` | 0.0139848 | 0.010941 | 0.010941 | 0.010941 | 1.000 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_varallyai1982_chernozem_a` | 0.0159733 | 0.0150377 | -0.00538646 | 0.0150377 | 1.000 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_varallyai1982_chernozem_c` | 0.0510106 | 0.0496252 | -0.0496252 | 0.0496252 | 1.000 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_b`, `calc_ptf_varallyai1982_chernozem_a`.

Best atomic: `calc_ptf_varallyai1982_chernozem_b`; best ensemble: equal_weight_pair (calc_ptf_varallyai1982_chernozem_a, calc_ptf_varallyai1982_chernozem_b).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:10kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_c` | 0.0503417 | 0.0364083 | -0.0364083 | 0.0364083 | 1.000 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_varallyai1982_chernozem_b` | 0.0651679 | 0.0606986 | -0.0606986 | 0.0606986 | 1.000 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_varallyai1982_chernozem_a` | 0.0856154 | 0.0793722 | -0.0793722 | 0.0793722 | 1.000 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_c`.

Best atomic: `calc_ptf_varallyai1982_chernozem_c`; best ensemble: equal_weight_pair (calc_ptf_varallyai1982_chernozem_b, calc_ptf_varallyai1982_chernozem_c).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:1500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_b` | 0.00612821 | 0.00592459 | 0.00156658 | 0.00592459 | 1.000 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_varallyai1982_chernozem_a` | 0.014786 | 0.0120482 | -0.0120482 | 0.0120482 | 1.000 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_rawls1982_theta_1500` | 0.0443461 | 0.0436838 | 0.0436838 | 0.0436838 | 1.000 | 0.018 | E4 / E4 |
| 4 | `calc_ptf_varallyai1982_chernozem_c` | 0.0718527 | 0.0718034 | -0.0718034 | 0.0718034 | 1.000 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_varallyai1982_chernozem_b`; best ensemble: median (calc_ptf_rawls1982_theta_1500, calc_ptf_varallyai1982_chernozem_a, calc_ptf_varallyai1982_chernozem_b, calc_ptf_varallyai1982_chernozem_c).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:33kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_b` | 0.0145991 | 0.0129407 | -0.00675811 | 0.0129407 | 1.000 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_varallyai1982_chernozem_a` | 0.0314597 | 0.02385 | -0.02385 | 0.02385 | 1.000 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_varallyai1982_chernozem_c` | 0.036614 | 0.0282346 | -0.0282346 | 0.0282346 | 1.000 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_varallyai1982_chernozem_b`; best ensemble: equal_weight_pair (calc_ptf_varallyai1982_chernozem_a, calc_ptf_varallyai1982_chernozem_b).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / brooks_corey_v1 / volumetric_water_content:500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_b` | 0.0113893 | 0.00941129 | 0.00941129 | 0.00941129 | 1.000 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_varallyai1982_chernozem_a` | 0.0119092 | 0.0104821 | -0.00565284 | 0.0104821 | 1.000 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_varallyai1982_chernozem_c` | 0.0712435 | 0.0712433 | -0.0712433 | 0.0712433 | 1.000 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_b`, `calc_ptf_varallyai1982_chernozem_a`.

Best atomic: `calc_ptf_varallyai1982_chernozem_b`; best ensemble: equal_weight_pair (calc_ptf_varallyai1982_chernozem_a, calc_ptf_varallyai1982_chernozem_b).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / dry_bulk_density

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_saxton2006` | 0.0823084 | 0.0677162 | 0.057588 | 0.0660434 | 0.353 | 0.055 | E3 / E3 |
| 2 | `calc_ptf_wosten2001_loam_clay_table5` | 0.138237 | 0.121174 | 0.121174 | 0.0857764 | 1.000 | 0.156 | E3 / E3 |

Pareto: `calc_ptf_saxton2006`, `calc_ptf_wosten2001_loam_clay_table5`.

Best atomic: `calc_ptf_saxton2006`; best ensemble: equal_weight_mean (calc_ptf_saxton2006, calc_ptf_wosten2001_loam_clay_table5).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_saxton2006` / `calc_ptf_wosten2001_loam_clay_table5`: 0.8374

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / gravimetric_water_content:100kPa

Empty roster common cohort; 20/21 exact pair cohorts are executable. Full pair metrics and ensemble comparisons are retained separately in summary.json. They do not form a shared leaderboard.

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / gravimetric_water_content:1500kPa

Empty roster common cohort; 188/190 exact pair cohorts are executable. Full pair metrics and ensemble comparisons are retained separately in summary.json. They do not form a shared leaderboard.

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / gravimetric_water_content:33kPa

Empty roster common cohort; 170/171 exact pair cohorts are executable. Full pair metrics and ensemble comparisons are retained separately in summary.json. They do not form a shared leaderboard.

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / gravimetric_water_content:500kPa

Empty roster common cohort; 20/21 exact pair cohorts are executable. Full pair metrics and ensemble comparisons are retained separately in summary.json. They do not form a shared leaderboard.

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:100kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0147052 | 0.0121569 | -0.00356205 | 0.0122248 | 0.333 | 0.055 | E2 / E2 |
| 2 | `calc_ptf_rawls1982_full_wrc` | 0.015411 | 0.014644 | -0.014644 | 0.0143178 | 0.333 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_saxton2006` | 0.0206787 | 0.0179882 | -0.0111154 | 0.0173108 | 0.333 | 0.055 | E4 / E4 |
| 4 | `calc_ptf_vereecken1989` | 0.0213374 | 0.016287 | 0.00376299 | 0.00952958 | 0.333 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_mayr1999` | 0.0221944 | 0.0167631 | 0.0159797 | 0.0154007 | 0.333 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_varallyai1982_meadow` | 0.0265966 | 0.0233694 | 0.0222422 | 0.0235735 | 0.333 | 0.055 | E4 / E4 |
| 7 | `calc_ptf_varallyai1982_chernozem_b` | 0.0277292 | 0.0246883 | -0.0227945 | 0.0246906 | 1.000 | 0.165 | E4 / E4 |
| 8 | `calc_ptf_clapp1978` | 0.0307731 | 0.0272659 | 0.0272659 | 0.0265031 | 0.333 | 0.055 | E2 / E2 |
| 9 | `calc_ptf_varallyai1982_chernozem_a` | 0.0354268 | 0.0320455 | -0.0320455 | 0.03726 | 1.000 | 0.165 | E4 / E4 |
| 10 | `calc_ptf_tomasella1998` | 0.084585 | 0.0833085 | 0.0833085 | 0.0816874 | 0.333 | 0.055 | E4 / E4 |
| 11 | `calc_ptf_varallyai1982_chernozem_c` | 0.0984015 | 0.0912305 | -0.0912305 | 0.0734192 | 1.000 | 0.165 | E4 / E4 |

Pareto: `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_pair (calc_ptf_rawls1982_full_wrc, calc_ptf_varallyai1982_meadow).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: 0.0262
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_vereecken1989`: 0.3620
- `calc_ptf_saxton2006` / `calc_ptf_varallyai1982_chernozem_c`: 0.3745

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:10kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0289003 | 0.0247246 | -0.00908475 | 0.0264586 | 0.333 | 0.055 | E2 / E2 |
| 2 | `calc_ptf_gunarathna2019_vwc10_set1` | 0.0297891 | 0.0238034 | 0.0127145 | 0.0166608 | 0.333 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_rawls1982_full_wrc` | 0.0353025 | 0.0266553 | -0.0148305 | 0.0160801 | 0.333 | 0.055 | E4 / E4 |
| 4 | `calc_ptf_vereecken1989` | 0.0371322 | 0.0249697 | -0.0167244 | 0.0137025 | 0.333 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_clapp1978` | 0.0388219 | 0.0289354 | 0.0274671 | 0.0244057 | 0.333 | 0.055 | E2 / E2 |
| 6 | `calc_ptf_varallyai1982_chernozem_c` | 0.0487327 | 0.0423372 | -0.0351609 | 0.0474419 | 1.000 | 0.165 | E4 / E4 |
| 7 | `calc_ptf_mayr1999` | 0.0501021 | 0.0424276 | -0.0422979 | 0.0356312 | 0.333 | 0.055 | E4 / E4 |
| 8 | `calc_ptf_varallyai1982_chernozem_b` | 0.0712807 | 0.0648594 | -0.0648594 | 0.0793671 | 1.000 | 0.165 | E4 / E4 |
| 9 | `calc_ptf_varallyai1982_chernozem_a` | 0.0733669 | 0.0689948 | -0.0689948 | 0.0675683 | 1.000 | 0.165 | E4 / E4 |
| 10 | `calc_ptf_saxton2006` | 0.0827487 | 0.0724173 | 0.0724173 | 0.0827992 | 0.333 | 0.055 | E4 / E4 |
| 11 | `calc_ptf_varallyai1982_meadow` | 0.0974611 | 0.0930275 | -0.0930275 | 0.0818124 | 0.333 | 0.055 | E4 / E4 |
| 12 | `calc_ptf_tomasella1998` | 0.110493 | 0.107009 | 0.107009 | 0.103775 | 0.333 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_c`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_pair (calc_ptf_gunarathna2019_vwc10_set1, calc_ptf_rawls1982_full_wrc).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_rawls1982_full_wrc` / `calc_ptf_varallyai1982_chernozem_c`: 0.1618
- `calc_ptf_rawls1982_full_wrc` / `calc_ptf_varallyai1982_chernozem_b`: 0.3558
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_vereecken1989`: 0.4465

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:1500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0170913 | 0.0140458 | 0.00888716 | 0.0156301 | 0.333 | 0.055 | E2 / E2 |
| 2 | `calc_ptf_rawls2003_soc_theta1500_tree` | 0.0194257 | 0.0160458 | -0.0103461 | 0.0159916 | 0.333 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_rawls2003_soc_theta1500_gmdh` | 0.0214464 | 0.0171365 | -0.0119918 | 0.0177554 | 0.333 | 0.055 | E4 / E4 |
| 4 | `calc_ptf_saxton2006` | 0.0234463 | 0.0178939 | -0.0142638 | 0.0182428 | 0.333 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_vereecken1989` | 0.024314 | 0.0193232 | 0.0126863 | 0.0233725 | 0.333 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_varallyai1982_chernozem_b` | 0.0253434 | 0.0199264 | -0.015174 | 0.0218645 | 1.000 | 0.165 | E4 / E4 |
| 7 | `calc_ptf_rawls1982_theta_1500` | 0.0301559 | 0.0251766 | 0.0171707 | 0.0299712 | 0.944 | 0.156 | E4 / E4 |
| 8 | `calc_ptf_varallyai1982_chernozem_a` | 0.0343373 | 0.0289188 | -0.0289188 | 0.0279815 | 1.000 | 0.165 | E4 / E4 |
| 9 | `calc_ptf_clapp1978` | 0.0354262 | 0.0322783 | 0.0322783 | 0.0333185 | 0.333 | 0.055 | E2 / E2 |
| 10 | `calc_ptf_tomasella1998` | 0.043073 | 0.040238 | 0.040238 | 0.039985 | 0.333 | 0.055 | E4 / E4 |
| 11 | `calc_ptf_mayr1999` | 0.0552622 | 0.0532768 | 0.0532768 | 0.0526801 | 0.333 | 0.055 | E4 / E4 |
| 12 | `calc_ptf_varallyai1982_meadow` | 0.0959499 | 0.0935856 | 0.0935856 | 0.0938776 | 0.333 | 0.055 | E4 / E4 |
| 13 | `calc_ptf_varallyai1982_chernozem_c` | 0.105331 | 0.104753 | -0.104753 | 0.10756 | 1.000 | 0.165 | E4 / E4 |
| 14 | `calc_ptf_gunarathna2019_vwc1500_set3` | 0.156701 | 0.155372 | 0.155372 | 0.155619 | 0.333 | 0.055 | E4 / E4 |
| 15 | `calc_ptf_gunarathna2019_vwc1500_set1` | 0.157562 | 0.156844 | 0.156844 | 0.157161 | 0.333 | 0.055 | E4 / E4 |
| 16 | `calc_ptf_gunarathna2019_vwc1500_set4` | 0.167383 | 0.165879 | 0.165879 | 0.169716 | 0.333 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_pair (calc_ptf_cosby1984_univariate, calc_ptf_rawls2003_soc_theta1500_tree).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_chernozem_c`: 0.6783
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: 0.6853
- `calc_ptf_gunarathna2019_vwc1500_set3` / `calc_ptf_varallyai1982_chernozem_c`: 0.7007

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:33kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_mayr1999` | 0.0157085 | 0.014288 | -0.00196935 | 0.0154875 | 0.333 | 0.055 | E4 / E4 |
| 2 | `calc_ptf_cosby1984_univariate` | 0.017132 | 0.0157695 | -0.00101024 | 0.0138937 | 0.333 | 0.055 | E2 / E2 |
| 3 | `calc_ptf_saxton2006` | 0.0198127 | 0.0173132 | 0.00784871 | 0.0154092 | 0.333 | 0.055 | E4 / E4 |
| 4 | `calc_ptf_rawls2003_soc_theta33_gmdh` | 0.0217168 | 0.0193882 | 0.0102578 | 0.0199628 | 0.333 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_varallyai1982_meadow` | 0.02339 | 0.0192777 | -0.0192777 | 0.0184473 | 0.333 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_vereecken1989` | 0.0237588 | 0.0204174 | 0.0135956 | 0.0189984 | 0.333 | 0.055 | E4 / E4 |
| 7 | `calc_ptf_rawls2003_soc_theta33_tree` | 0.0246398 | 0.0204862 | 0.0166335 | 0.0178552 | 0.333 | 0.055 | E4 / E4 |
| 8 | `calc_ptf_clapp1978` | 0.036968 | 0.0327741 | 0.0327741 | 0.0325403 | 0.333 | 0.055 | E2 / E2 |
| 9 | `calc_ptf_varallyai1982_chernozem_b` | 0.0380917 | 0.0292802 | -0.0292802 | 0.0205557 | 1.000 | 0.165 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_chernozem_a` | 0.0394817 | 0.0356456 | -0.0356456 | 0.0405461 | 1.000 | 0.165 | E4 / E4 |
| 11 | `calc_ptf_rawls1982_theta_33` | 0.0517826 | 0.0477892 | 0.0477892 | 0.0494161 | 0.333 | 0.055 | E4 / E4 |
| 12 | `calc_ptf_gunarathna2019_vwc33_set1` | 0.0666053 | 0.0643553 | 0.0643553 | 0.0632527 | 0.333 | 0.055 | E4 / E4 |
| 13 | `calc_ptf_varallyai1982_chernozem_c` | 0.0692054 | 0.0516193 | -0.0516193 | 0.0253675 | 1.000 | 0.165 | E4 / E4 |
| 14 | `calc_ptf_tomasella1998` | 0.0806787 | 0.0788251 | 0.0788251 | 0.0776416 | 0.333 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_mayr1999`, `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_mayr1999`; best ensemble: equal_weight_pair (calc_ptf_rawls2003_soc_theta33_tree, calc_ptf_varallyai1982_meadow).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: 0.3426
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_vereecken1989`: 0.4223
- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: 0.5007

reported_boundary_proxy / log_pressure_linear_interpolation_v1 / volumetric_water_content:500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0123223 | 0.0101128 | -0.00289413 | 0.00772258 | 0.333 | 0.055 | E2 / E2 |
| 2 | `calc_ptf_vereecken1989` | 0.0199411 | 0.0152989 | -0.00594336 | 0.0117712 | 0.333 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_clapp1978` | 0.0263449 | 0.0234647 | 0.0234647 | 0.0209753 | 0.333 | 0.055 | E2 / E2 |
| 4 | `calc_ptf_varallyai1982_chernozem_b` | 0.0266104 | 0.0232704 | -0.0232704 | 0.023655 | 1.000 | 0.165 | E4 / E4 |
| 5 | `calc_ptf_saxton2006` | 0.0279852 | 0.0240912 | -0.0226735 | 0.0226157 | 0.333 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_mayr1999` | 0.037363 | 0.0347717 | 0.0347717 | 0.0319453 | 0.333 | 0.055 | E4 / E4 |
| 7 | `calc_ptf_varallyai1982_chernozem_a` | 0.0387913 | 0.0360003 | -0.0360003 | 0.0353272 | 1.000 | 0.165 | E4 / E4 |
| 8 | `calc_ptf_tomasella1998` | 0.0660518 | 0.0648426 | 0.0648426 | 0.062692 | 0.333 | 0.055 | E4 / E4 |
| 9 | `calc_ptf_varallyai1982_meadow` | 0.0669893 | 0.0647248 | 0.0647248 | 0.0679246 | 0.333 | 0.055 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_chernozem_c` | 0.120015 | 0.118999 | -0.118999 | 0.117471 | 1.000 | 0.165 | E4 / E4 |

Pareto: `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_pair (calc_ptf_clapp1978, calc_ptf_varallyai1982_chernozem_b).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: -0.0379
- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_chernozem_c`: 0.2065
- `calc_ptf_varallyai1982_chernozem_a` / `calc_ptf_varallyai1982_chernozem_c`: 0.2563

reported_boundary_proxy / van_genuchten_mualem_v1 / gravimetric_water_content:100kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_oosterveld1980_retention` | 0.0219232 | 0.0173324 | -0.0134244 | 0.0173324 | 0.667 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_chakraborty2011_eq2` | 0.0962692 | 0.0942303 | 0.0942303 | 0.0942303 | 0.667 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_chakraborty2011_eq5` | 0.139228 | 0.138023 | 0.138023 | 0.138023 | 0.667 | 0.018 | E4 / E4 |
| 4 | `calc_ptf_chakraborty2011_eq4` | 0.140417 | 0.139253 | 0.139253 | 0.139253 | 1.000 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_chakraborty2011_eq1` | 0.142535 | 0.141393 | 0.141393 | 0.141393 | 1.000 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_chakraborty2011_eq3` | 0.153597 | 0.152751 | 0.152751 | 0.152751 | 0.667 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_oosterveld1980_retention`, `calc_ptf_chakraborty2011_eq4`.

Best atomic: `calc_ptf_oosterveld1980_retention`; best ensemble: equal_weight_pair (calc_ptf_chakraborty2011_eq2, calc_ptf_oosterveld1980_retention).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / van_genuchten_mualem_v1 / gravimetric_water_content:1500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_beniaich2023_mlr4` | 0.00759809 | 0.00741359 | 0.00166423 | 0.00741359 | 0.750 | 0.055 | E4 / E4 |
| 2 | `calc_ptf_beniaich2023_slr1` | 0.00799482 | 0.00755961 | -0.00260181 | 0.00755961 | 0.750 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_oosterveld1980_wilting_point` | 0.00950095 | 0.00676644 | -0.00666958 | 0.00676644 | 0.250 | 0.018 | E4 / E4 |
| 4 | `calc_ptf_oosterveld1980_retention` | 0.0149221 | 0.013298 | 0.013298 | 0.013298 | 0.250 | 0.018 | E4 / E4 |
| 5 | `calc_ptf_myeni2021_pwp` | 0.0412615 | 0.0405896 | 0.0405896 | 0.0405896 | 0.375 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_beniaich2023_slr4` | 0.0461525 | 0.0456908 | 0.0456908 | 0.0456908 | 0.375 | 0.028 | E4 / E4 |
| 7 | `calc_ptf_chakraborty2011_eq5` | 0.0654851 | 0.0649264 | 0.0649264 | 0.0649264 | 0.250 | 0.018 | E4 / E4 |
| 8 | `calc_ptf_beniaich2023_mlr5` | 0.0657134 | 0.0652939 | 0.0652939 | 0.0652939 | 0.375 | 0.028 | E4 / E4 |
| 9 | `calc_ptf_beniaich2023_mlr1` | 0.0659451 | 0.065527 | 0.065527 | 0.065527 | 0.375 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_beniaich2023_slr5` | 0.0722905 | 0.0719638 | 0.0719638 | 0.0719638 | 0.375 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_chakraborty2011_eq4` | 0.0729132 | 0.0725501 | 0.0725501 | 0.0725501 | 0.375 | 0.028 | E4 / E4 |
| 12 | `calc_ptf_chakraborty2011_eq1` | 0.0745428 | 0.0741909 | 0.0741909 | 0.0741909 | 0.375 | 0.028 | E4 / E4 |
| 13 | `calc_ptf_beniaich2023_slr6` | 0.0750305 | 0.0747291 | 0.0747291 | 0.0747291 | 1.000 | 0.073 | E4 / E4 |
| 14 | `calc_ptf_chakraborty2011_eq3` | 0.0769491 | 0.0766464 | 0.0766464 | 0.0766464 | 0.250 | 0.018 | E4 / E4 |
| 15 | `calc_ptf_chakraborty2011_eq2` | 0.0885298 | 0.0881695 | 0.0881695 | 0.0881695 | 0.250 | 0.018 | E4 / E4 |
| 16 | `calc_ptf_beniaich2023_slr3` | 0.107346 | 0.107093 | 0.107093 | 0.107093 | 0.375 | 0.028 | E4 / E4 |
| 17 | `calc_ptf_beniaich2023_mlr2` | 0.109607 | 0.109365 | 0.109365 | 0.109365 | 0.375 | 0.028 | E4 / E4 |
| 18 | `calc_ptf_beniaich2023_slr2` | 0.139012 | 0.138843 | 0.138843 | 0.138843 | 0.375 | 0.028 | E4 / E4 |
| 19 | `calc_ptf_beniaich2023_mlr3` | 0.14061 | 0.140449 | 0.140449 | 0.140449 | 0.375 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_beniaich2023_mlr4`, `calc_ptf_beniaich2023_slr6`.

Best atomic: `calc_ptf_beniaich2023_mlr4`; best ensemble: equal_weight_pair (calc_ptf_beniaich2023_mlr4, calc_ptf_beniaich2023_slr1).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / van_genuchten_mualem_v1 / gravimetric_water_content:33kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_beniaich2023_slr6` | 0.0231063 | 0.0220663 | 0.00685414 | 0.0220663 | 1.000 | 0.110 | E4 / E4 |
| 2 | `calc_ptf_myeni2021_fc` | 0.0233412 | 0.0232232 | 0.00234438 | 0.0232232 | 0.250 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_beniaich2023_slr5` | 0.0243923 | 0.0223559 | -0.00975689 | 0.0223559 | 0.250 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_beniaich2023_mlr5` | 0.0337767 | 0.0248826 | 0.0248826 | 0.0248826 | 0.250 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_beniaich2023_mlr1` | 0.0340576 | 0.0252626 | 0.0252626 | 0.0252626 | 0.250 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_oosterveld1980_retention` | 0.0398914 | 0.0332204 | -0.0332204 | 0.0332204 | 0.167 | 0.018 | E4 / E4 |
| 7 | `calc_ptf_beniaich2023_slr4` | 0.0440961 | 0.038366 | -0.038366 | 0.038366 | 0.250 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_beniaich2023_slr3` | 0.0520992 | 0.0467855 | 0.0467855 | 0.0467855 | 0.250 | 0.028 | E4 / E4 |
| 9 | `calc_ptf_beniaich2023_mlr2` | 0.055245 | 0.0503389 | 0.0503389 | 0.0503389 | 0.250 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_beniaich2023_mlr4` | 0.0780935 | 0.0746785 | -0.0746785 | 0.0746785 | 0.500 | 0.055 | E4 / E4 |
| 11 | `calc_ptf_beniaich2023_slr1` | 0.0841832 | 0.0809622 | -0.0809622 | 0.0809622 | 0.500 | 0.055 | E4 / E4 |
| 12 | `calc_ptf_chakraborty2011_eq2` | 0.102368 | 0.0997744 | 0.0997744 | 0.0997744 | 0.167 | 0.018 | E4 / E4 |
| 13 | `calc_ptf_beniaich2023_slr2` | 0.109071 | 0.106778 | 0.106778 | 0.106778 | 0.250 | 0.028 | E4 / E4 |
| 14 | `calc_ptf_beniaich2023_mlr3` | 0.110217 | 0.107984 | 0.107984 | 0.107984 | 0.250 | 0.028 | E4 / E4 |
| 15 | `calc_ptf_chakraborty2011_eq4` | 0.167574 | 0.166004 | 0.166004 | 0.166004 | 0.250 | 0.028 | E4 / E4 |
| 16 | `calc_ptf_chakraborty2011_eq1` | 0.168958 | 0.167407 | 0.167407 | 0.167407 | 0.250 | 0.028 | E4 / E4 |
| 17 | `calc_ptf_chakraborty2011_eq5` | 0.183572 | 0.182461 | 0.182461 | 0.182461 | 0.167 | 0.018 | E4 / E4 |
| 18 | `calc_ptf_chakraborty2011_eq3` | 0.196149 | 0.195297 | 0.195297 | 0.195297 | 0.167 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_beniaich2023_slr6`, `calc_ptf_myeni2021_fc`.

Best atomic: `calc_ptf_beniaich2023_slr6`; best ensemble: equal_weight_pair (calc_ptf_beniaich2023_slr5, calc_ptf_beniaich2023_slr6).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / van_genuchten_mualem_v1 / gravimetric_water_content:500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_oosterveld1980_retention` | 0.0120971 | 0.0102379 | 0.00644401 | 0.0102379 | 0.667 | 0.018 | E4 / E4 |
| 2 | `calc_ptf_chakraborty2011_eq5` | 0.0747168 | 0.0739295 | 0.0739295 | 0.0739295 | 0.667 | 0.018 | E4 / E4 |
| 3 | `calc_ptf_chakraborty2011_eq4` | 0.0748494 | 0.0740514 | 0.0740514 | 0.0740514 | 1.000 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_chakraborty2011_eq1` | 0.0754782 | 0.0746928 | 0.0746928 | 0.0746928 | 1.000 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_chakraborty2011_eq3` | 0.0870427 | 0.0865763 | 0.0865763 | 0.0865763 | 0.667 | 0.018 | E4 / E4 |
| 6 | `calc_ptf_chakraborty2011_eq2` | 0.104388 | 0.103873 | 0.103873 | 0.103873 | 0.667 | 0.018 | E4 / E4 |

Pareto: `calc_ptf_oosterveld1980_retention`, `calc_ptf_chakraborty2011_eq4`, `calc_ptf_chakraborty2011_eq1`.

Best atomic: `calc_ptf_oosterveld1980_retention`; best ensemble: equal_weight_pair (calc_ptf_chakraborty2011_eq5, calc_ptf_oosterveld1980_retention).

Lowest absolute residual correlations (descriptive):

Insufficient points or constant residuals.

reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:100kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_rawls1982_full_wrc` | 0.00823726 | 0.00785633 | -0.00785633 | 0.00823113 | 0.500 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_saxton2006` | 0.0147577 | 0.0113727 | 0.00429214 | 0.0100457 | 0.500 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_cosby1984_univariate` | 0.0154431 | 0.0123282 | 0.00633025 | 0.00899692 | 0.500 | 0.028 | E2 / E2 |
| 4 | `calc_ptf_varallyai1982_chernozem_b` | 0.0241619 | 0.0219419 | -0.0162351 | 0.0242491 | 1.000 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_varallyai1982_chernozem_a` | 0.0242123 | 0.0195175 | -0.0194935 | 0.0244303 | 1.000 | 0.055 | E4 / E4 |
| 6 | `calc_ptf_vereecken1989` | 0.02653 | 0.020241 | 0.020241 | 0.0138316 | 0.500 | 0.028 | E4 / E4 |
| 7 | `calc_ptf_mayr1999` | 0.0306964 | 0.0268332 | 0.0268332 | 0.0233567 | 0.500 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_clapp1978` | 0.0397385 | 0.0371582 | 0.0371582 | 0.0338021 | 0.500 | 0.028 | E2 / E2 |
| 9 | `calc_ptf_varallyai1982_meadow` | 0.0404246 | 0.0399896 | 0.0399896 | 0.0393915 | 0.500 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_tomasella1998` | 0.0948539 | 0.093716 | 0.093716 | 0.0898771 | 0.500 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_varallyai1982_chernozem_c` | 0.110296 | 0.102632 | -0.102632 | 0.116872 | 1.000 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_rawls1982_full_wrc`, `calc_ptf_saxton2006`, `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_b`.

Best atomic: `calc_ptf_rawls1982_full_wrc`; best ensemble: equal_weight_pair (calc_ptf_cosby1984_univariate, calc_ptf_rawls1982_full_wrc).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: 0.9687
- `calc_ptf_rawls1982_full_wrc` / `calc_ptf_varallyai1982_chernozem_b`: 0.9770
- `calc_ptf_varallyai1982_meadow` / `calc_ptf_vereecken1989`: 0.9809

reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:10kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_vereecken1989` | 0.0029677 | 0.002683 | -0.00150248 | 0.00180154 | 0.500 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_rawls1982_full_wrc` | 0.011682 | 0.0102815 | 0.000758818 | 0.0141217 | 0.500 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_cosby1984_univariate` | 0.0125682 | 0.0116217 | -0.00633419 | 0.00855482 | 0.500 | 0.028 | E2 / E2 |
| 4 | `calc_ptf_gunarathna2019_vwc10_set1` | 0.0196899 | 0.0160287 | 0.0160287 | 0.0132878 | 0.500 | 0.028 | E4 / E4 |
| 5 | `calc_ptf_clapp1978` | 0.0321083 | 0.0302176 | 0.0302176 | 0.027997 | 0.500 | 0.028 | E2 / E2 |
| 6 | `calc_ptf_mayr1999` | 0.0347997 | 0.0345312 | -0.0345312 | 0.0337356 | 0.500 | 0.028 | E4 / E4 |
| 7 | `calc_ptf_varallyai1982_chernozem_c` | 0.0566964 | 0.046216 | -0.046216 | 0.0549108 | 1.000 | 0.055 | E4 / E4 |
| 8 | `calc_ptf_varallyai1982_chernozem_a` | 0.062862 | 0.0620178 | -0.0620178 | 0.0648277 | 1.000 | 0.055 | E4 / E4 |
| 9 | `calc_ptf_varallyai1982_chernozem_b` | 0.075704 | 0.0719475 | -0.0719475 | 0.0806624 | 1.000 | 0.055 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_meadow` | 0.0813499 | 0.0813322 | -0.0813322 | 0.0803347 | 0.500 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_saxton2006` | 0.0882996 | 0.0878175 | 0.0878175 | 0.0840879 | 0.500 | 0.028 | E4 / E4 |
| 12 | `calc_ptf_tomasella1998` | 0.110602 | 0.110009 | 0.110009 | 0.107469 | 0.500 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_vereecken1989`, `calc_ptf_rawls1982_full_wrc`, `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_c`.

Best atomic: `calc_ptf_vereecken1989`; best ensemble: equal_weight_pair (calc_ptf_cosby1984_univariate, calc_ptf_rawls1982_full_wrc).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_saxton2006` / `calc_ptf_varallyai1982_meadow`: 0.7531
- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: 0.7696
- `calc_ptf_varallyai1982_chernozem_a` / `calc_ptf_varallyai1982_meadow`: 0.8124

reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:1500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_a` | 0.00411045 | 0.00362306 | -0.00362306 | 0.00307974 | 1.000 | 0.055 | E4 / E4 |
| 2 | `calc_ptf_saxton2006` | 0.011235 | 0.0106338 | 0.0106338 | 0.0093847 | 0.500 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_rawls2003_soc_theta1500_gmdh` | 0.0126598 | 0.0121484 | 0.0121484 | 0.0107398 | 0.500 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_varallyai1982_chernozem_b` | 0.0129284 | 0.0117561 | 0.0117561 | 0.00881907 | 1.000 | 0.055 | E4 / E4 |
| 5 | `calc_ptf_rawls2003_soc_theta1500_tree` | 0.0130538 | 0.0127034 | 0.0127034 | 0.0108384 | 0.500 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_cosby1984_univariate` | 0.030087 | 0.0299366 | 0.0299366 | 0.0280716 | 0.500 | 0.028 | E2 / E2 |
| 7 | `calc_ptf_vereecken1989` | 0.0393385 | 0.0389901 | 0.0389901 | 0.0365334 | 0.500 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_rawls1982_theta_1500` | 0.0471746 | 0.0470563 | 0.0470563 | 0.0472705 | 1.000 | 0.055 | E4 / E4 |
| 9 | `calc_ptf_clapp1978` | 0.0534122 | 0.0533277 | 0.0533277 | 0.0514627 | 0.500 | 0.028 | E2 / E2 |
| 10 | `calc_ptf_tomasella1998` | 0.0622634 | 0.0621555 | 0.0621555 | 0.0600841 | 0.500 | 0.028 | E4 / E4 |
| 11 | `calc_ptf_mayr1999` | 0.0732458 | 0.0727776 | 0.0727776 | 0.0683227 | 0.500 | 0.028 | E4 / E4 |
| 12 | `calc_ptf_varallyai1982_chernozem_c` | 0.0898145 | 0.0893357 | -0.0893357 | 0.0945366 | 1.000 | 0.055 | E4 / E4 |
| 13 | `calc_ptf_varallyai1982_meadow` | 0.12124 | 0.121172 | 0.121172 | 0.121008 | 0.500 | 0.028 | E4 / E4 |
| 14 | `calc_ptf_gunarathna2019_vwc1500_set1` | 0.178385 | 0.17835 | 0.17835 | 0.176171 | 0.500 | 0.028 | E4 / E4 |
| 15 | `calc_ptf_gunarathna2019_vwc1500_set3` | 0.182331 | 0.182293 | 0.182293 | 0.18125 | 0.500 | 0.028 | E4 / E4 |
| 16 | `calc_ptf_gunarathna2019_vwc1500_set4` | 0.193727 | 0.193705 | 0.193705 | 0.193947 | 0.500 | 0.028 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_a`, `calc_ptf_cosby1984_univariate`.

Best atomic: `calc_ptf_varallyai1982_chernozem_a`; best ensemble: equal_weight_pair (calc_ptf_saxton2006, calc_ptf_varallyai1982_chernozem_a).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_mayr1999` / `calc_ptf_varallyai1982_chernozem_a`: 0.0664
- `calc_ptf_gunarathna2019_vwc1500_set4` / `calc_ptf_varallyai1982_chernozem_b`: -0.0683
- `calc_ptf_rawls1982_theta_1500` / `calc_ptf_varallyai1982_chernozem_b`: -0.0818

reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:33kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_mayr1999` | 0.0182299 | 0.0165947 | -0.00869339 | 0.011852 | 0.500 | 0.028 | E4 / E4 |
| 2 | `calc_ptf_saxton2006` | 0.0186166 | 0.0144965 | 0.0046332 | 0.0147949 | 0.500 | 0.028 | E4 / E4 |
| 3 | `calc_ptf_rawls2003_soc_theta33_gmdh` | 0.0188557 | 0.0151264 | 0.0071897 | 0.011905 | 0.500 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_cosby1984_univariate` | 0.0210012 | 0.0193125 | -0.0103688 | 0.0135412 | 0.500 | 0.028 | E2 / E2 |
| 5 | `calc_ptf_vereecken1989` | 0.0215637 | 0.0166644 | 0.0132367 | 0.00895917 | 0.500 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_varallyai1982_meadow` | 0.022389 | 0.0202494 | -0.0202494 | 0.0204397 | 0.500 | 0.028 | E4 / E4 |
| 7 | `calc_ptf_rawls2003_soc_theta33_tree` | 0.0235964 | 0.0187218 | 0.0149416 | 0.0117691 | 0.500 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_clapp1978` | 0.0296956 | 0.0234156 | 0.0234156 | 0.0202431 | 0.500 | 0.028 | E2 / E2 |
| 9 | `calc_ptf_rawls1982_theta_33` | 0.0412101 | 0.0386235 | 0.0386235 | 0.0357614 | 0.500 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_chernozem_a` | 0.0463562 | 0.0423009 | -0.0423009 | 0.0469942 | 1.000 | 0.055 | E4 / E4 |
| 11 | `calc_ptf_varallyai1982_chernozem_b` | 0.0532821 | 0.045939 | -0.045939 | 0.0551766 | 1.000 | 0.055 | E4 / E4 |
| 12 | `calc_ptf_gunarathna2019_vwc33_set1` | 0.0586275 | 0.0555299 | 0.0555299 | 0.0518653 | 0.500 | 0.028 | E4 / E4 |
| 13 | `calc_ptf_tomasella1998` | 0.0725621 | 0.0700583 | 0.0700583 | 0.0663308 | 0.500 | 0.028 | E4 / E4 |
| 14 | `calc_ptf_varallyai1982_chernozem_c` | 0.0974946 | 0.0841596 | -0.0841596 | 0.0988675 | 1.000 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_mayr1999`, `calc_ptf_saxton2006`, `calc_ptf_cosby1984_univariate`, `calc_ptf_varallyai1982_chernozem_a`.

Best atomic: `calc_ptf_mayr1999`; best ensemble: equal_weight_pair (calc_ptf_varallyai1982_meadow, calc_ptf_vereecken1989).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: 0.9736
- `calc_ptf_varallyai1982_chernozem_c` / `calc_ptf_varallyai1982_meadow`: 0.9803
- `calc_ptf_saxton2006` / `calc_ptf_varallyai1982_meadow`: 0.9861

reported_boundary_proxy / van_genuchten_mualem_v1 / volumetric_water_content:500kPa

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_varallyai1982_chernozem_a` | 0.0066173 | 0.00602348 | -0.00455789 | 0.00740128 | 1.000 | 0.055 | E4 / E4 |
| 2 | `calc_ptf_varallyai1982_chernozem_b` | 0.00834504 | 0.00727585 | 0.00727585 | 0.00753751 | 1.000 | 0.055 | E4 / E4 |
| 3 | `calc_ptf_saxton2006` | 0.0116746 | 0.00960759 | 0.00960759 | 0.00509547 | 0.500 | 0.028 | E4 / E4 |
| 4 | `calc_ptf_cosby1984_univariate` | 0.0256454 | 0.0248762 | 0.0248762 | 0.0217985 | 0.500 | 0.028 | E2 / E2 |
| 5 | `calc_ptf_vereecken1989` | 0.0288458 | 0.0272094 | 0.0272094 | 0.0210424 | 0.500 | 0.028 | E4 / E4 |
| 6 | `calc_ptf_clapp1978` | 0.0516129 | 0.0512351 | 0.0512351 | 0.0481573 | 0.500 | 0.028 | E2 / E2 |
| 7 | `calc_ptf_mayr1999` | 0.0626202 | 0.0617884 | 0.0617884 | 0.0572513 | 0.500 | 0.028 | E4 / E4 |
| 8 | `calc_ptf_tomasella1998` | 0.0935225 | 0.0932737 | 0.0932737 | 0.0896271 | 0.500 | 0.028 | E4 / E4 |
| 9 | `calc_ptf_varallyai1982_meadow` | 0.0995759 | 0.0995666 | 0.0995666 | 0.0989193 | 0.500 | 0.028 | E4 / E4 |
| 10 | `calc_ptf_varallyai1982_chernozem_c` | 0.10386 | 0.102136 | -0.102136 | 0.110771 | 1.000 | 0.055 | E4 / E4 |

Pareto: `calc_ptf_varallyai1982_chernozem_a`, `calc_ptf_cosby1984_univariate`.

Best atomic: `calc_ptf_varallyai1982_chernozem_a`; best ensemble: equal_weight_pair (calc_ptf_varallyai1982_chernozem_a, calc_ptf_varallyai1982_chernozem_b).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_varallyai1982_chernozem_b` / `calc_ptf_varallyai1982_meadow`: -0.1347
- `calc_ptf_varallyai1982_chernozem_a` / `calc_ptf_varallyai1982_meadow`: -0.5752
- `calc_ptf_saxton2006` / `calc_ptf_varallyai1982_meadow`: -0.6637

strict / strict_observed / curve:volumetric_water_content

| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | Dataset sample coverage | Min / required tier |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `calc_ptf_cosby1984_univariate` | 0.0227324 | 0.01843 | 0.00551921 | 0.0162775 | 1.000 | 0.055 | E0 / E0 |
| 2 | `calc_ptf_clapp1978` | 0.0350361 | 0.0305542 | 0.0288498 | 0.0322273 | 1.000 | 0.055 | E0 / E0 |

Pareto: `calc_ptf_cosby1984_univariate`.

Best atomic: `calc_ptf_cosby1984_univariate`; best ensemble: equal_weight_mean (calc_ptf_clapp1978, calc_ptf_cosby1984_univariate).

Lowest absolute residual correlations (descriptive):

- `calc_ptf_clapp1978` / `calc_ptf_cosby1984_univariate`: 0.9121

</details>

<details><summary>Rank changes</summary>

target_routes: gravimetric_water_content:1500kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 2 common points.

`calc_ptf_beniaich2023_slr1`: -1, `calc_ptf_oosterveld1980_retention`: +2, `calc_ptf_oosterveld1980_wilting_point`: -1

Changed pair orderings: 2; full pairs are retained in summary.json.

target_routes: gravimetric_water_content:33kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 2 common points.

`calc_ptf_beniaich2023_slr5`: +2, `calc_ptf_beniaich2023_slr6`: -2

Changed pair orderings: 3; full pairs are retained in summary.json.

target_routes: volumetric_water_content:100kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_clapp1978`: -1, `calc_ptf_cosby1984_univariate`: +1, `calc_ptf_mayr1999`: +2, `calc_ptf_saxton2006`: -1, `calc_ptf_varallyai1982_chernozem_a`: -2, `calc_ptf_varallyai1982_chernozem_b`: -2, `calc_ptf_varallyai1982_meadow`: +1, `calc_ptf_vereecken1989`: +2

Changed pair orderings: 6; full pairs are retained in summary.json.

target_routes: volumetric_water_content:10kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_cosby1984_univariate`: +1, `calc_ptf_rawls1982_full_wrc`: -1

Changed pair orderings: 1; full pairs are retained in summary.json.

target_routes: volumetric_water_content:1500kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_rawls2003_soc_theta1500_gmdh`: +1, `calc_ptf_rawls2003_soc_theta1500_tree`: +2, `calc_ptf_saxton2006`: +1, `calc_ptf_varallyai1982_chernozem_a`: -4

Changed pair orderings: 5; full pairs are retained in summary.json.

target_routes: volumetric_water_content:33kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_cosby1984_univariate`: +1, `calc_ptf_rawls2003_soc_theta33_gmdh`: -2, `calc_ptf_varallyai1982_meadow`: +2, `calc_ptf_vereecken1989`: -1

Changed pair orderings: 3; full pairs are retained in summary.json.

target_routes: volumetric_water_content:500kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_cosby1984_univariate`: +3, `calc_ptf_varallyai1982_chernozem_a`: -4, `calc_ptf_vereecken1989`: +1

Changed pair orderings: 6; full pairs are retained in summary.json.

target_routes: gravimetric_water_content:1500kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 2 common points.

`calc_ptf_beniaich2023_slr1`: -1, `calc_ptf_oosterveld1980_retention`: +2, `calc_ptf_oosterveld1980_wilting_point`: -1

Changed pair orderings: 2; full pairs are retained in summary.json.

target_routes: gravimetric_water_content:33kPa; ['brooks_corey_v1', 'log_pressure_linear_interpolation_v1']; 2 common points.

`calc_ptf_beniaich2023_mlr4`: +1, `calc_ptf_beniaich2023_slr1`: +1, `calc_ptf_beniaich2023_slr6`: -2

Changed pair orderings: 2; full pairs are retained in summary.json.

target_routes: gravimetric_water_content:33kPa; ['brooks_corey_v1', 'van_genuchten_mualem_v1']; 2 common points.

`calc_ptf_beniaich2023_mlr4`: +1, `calc_ptf_beniaich2023_slr1`: +1, `calc_ptf_beniaich2023_slr6`: -2

Changed pair orderings: 2; full pairs are retained in summary.json.

target_routes: gravimetric_water_content:33kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 2 common points.

`calc_ptf_beniaich2023_slr5`: +2, `calc_ptf_beniaich2023_slr6`: -2

Changed pair orderings: 3; full pairs are retained in summary.json.

target_routes: volumetric_water_content:100kPa; ['brooks_corey_v1', 'van_genuchten_mualem_v1']; 2 common points.

`calc_ptf_varallyai1982_chernozem_a`: -1, `calc_ptf_varallyai1982_chernozem_b`: +1

Changed pair orderings: 1; full pairs are retained in summary.json.

target_routes: volumetric_water_content:100kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_clapp1978`: -1, `calc_ptf_cosby1984_univariate`: +1, `calc_ptf_mayr1999`: +2, `calc_ptf_saxton2006`: -1, `calc_ptf_varallyai1982_chernozem_a`: -2, `calc_ptf_varallyai1982_chernozem_b`: -2, `calc_ptf_varallyai1982_meadow`: +1, `calc_ptf_vereecken1989`: +2

Changed pair orderings: 6; full pairs are retained in summary.json.

target_routes: volumetric_water_content:10kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_cosby1984_univariate`: +1, `calc_ptf_rawls1982_full_wrc`: -1

Changed pair orderings: 1; full pairs are retained in summary.json.

target_routes: volumetric_water_content:1500kPa; ['brooks_corey_v1', 'van_genuchten_mualem_v1']; 2 common points.

`calc_ptf_rawls1982_theta_1500`: +1, `calc_ptf_varallyai1982_chernozem_a`: -1, `calc_ptf_varallyai1982_chernozem_b`: +1, `calc_ptf_varallyai1982_chernozem_c`: -1

Changed pair orderings: 2; full pairs are retained in summary.json.

target_routes: volumetric_water_content:1500kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_rawls2003_soc_theta1500_gmdh`: +1, `calc_ptf_rawls2003_soc_theta1500_tree`: +2, `calc_ptf_saxton2006`: +1, `calc_ptf_varallyai1982_chernozem_a`: -4

Changed pair orderings: 5; full pairs are retained in summary.json.

target_routes: volumetric_water_content:33kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_cosby1984_univariate`: +1, `calc_ptf_rawls2003_soc_theta33_gmdh`: -2, `calc_ptf_varallyai1982_meadow`: +2, `calc_ptf_vereecken1989`: -1

Changed pair orderings: 3; full pairs are retained in summary.json.

target_routes: volumetric_water_content:500kPa; ['brooks_corey_v1', 'van_genuchten_mualem_v1']; 2 common points.

`calc_ptf_varallyai1982_chernozem_a`: -1, `calc_ptf_varallyai1982_chernozem_b`: +1

Changed pair orderings: 1; full pairs are retained in summary.json.

target_routes: volumetric_water_content:500kPa; ['log_pressure_linear_interpolation_v1', 'van_genuchten_mualem_v1']; 3 common points.

`calc_ptf_cosby1984_univariate`: +3, `calc_ptf_varallyai1982_chernozem_a`: -4, `calc_ptf_vereecken1989`: +1

Changed pair orderings: 6; full pairs are retained in summary.json.

</details>

Primary target strata: 2601 interpolated; 0 exact observed; 41 direct-property executions. Each stratum has separate common-cohort metrics and PSD sensitivity in `summary.json` → `target_evidence_diagnostics`. Errors from different target strata are never ranked against each other.


Target-route comparisons keep coordinates fixed and score each route against its own declared targets. Accepted-fit routes remain diagnostics. Interpolation never extrapolates.

The reduced ensemble selects candidates at or below median atomic RMSE with absolute residual correlation below 0.8. Selection uses this cohort and is descriptive only. Learned convex pairs retain the existing grouped evidence gates in `summary.json` → `ensembles`.

Pareto comparisons use common-cohort RMSE, absolute bias, maximal coverage and the highest required tier on the cohort. A 1% relative error tolerance prevents negligible improvements from dominating a model with lower assumption burden.

Full metrics, ranks, residual correlations, Pareto members, exact coordinates, rank changes, pair ordering changes and per-function predictor/blocker audits: `summary.json` → `comparative_benchmark`, `ranking_robustness`, `function_audit`. Predictions and eligibility decisions are retained in separate JSON artifacts.
