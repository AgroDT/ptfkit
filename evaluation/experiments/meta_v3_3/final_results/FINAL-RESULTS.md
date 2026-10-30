# ptfkit v1.0: all experimental WRC points

The ledger contains 1701 experimental points, 142 samples and 19 sources. Volumetric: 1069 points / 77 samples; gravimetric: 632 / 65. Fitted workbook parameters and reconstructed target values are excluded.

Every PTF is evaluated on all compatible experimental coordinates with available predictors and valid pressure support. No minimum number of observed points per sample or common cohort is imposed. Coverage denominators are the complete ledger for the respective water basis. Bias is prediction minus measurement. R squared is descriptive.

Sample-balanced RMSE = sqrt(mean over samples of mean squared point error within each sample). Pointwise RMSE uses equal point weights. Sample-balanced MAE and bias are also supplied. Models have different evaluation subsets; rankings describe this dataset and do not establish causal superiority on a common population.

## volumetric_water_content

**Best accuracy:** `calc_ptf_cosby1984_univariate`: sample-balanced RMSE 0.022732; pointwise RMSE 0.022609; points 56/1069 (5.2%); samples 6/77 (7.8%)

**Best individual at coverage >= 25%:** `calc_ptf_varallyai1982_chernozem_b`: sample-balanced RMSE 0.045390; pointwise RMSE 0.043883; points 608/1069 (56.9%); samples 30/77 (39.0%)

**Best individual at coverage >= 50%:** `calc_ptf_varallyai1982_chernozem_b`: sample-balanced RMSE 0.045390; pointwise RMSE 0.043883; points 608/1069 (56.9%); samples 30/77 (39.0%)

**Best individual at coverage >= 75%:** No eligible model

**Accuracy-coverage compromise:** `calc_ptf_varallyai1982_chernozem_b`: sample-balanced RMSE 0.045390; pointwise RMSE 0.043883; points 608/1069 (56.9%); samples 30/77 (39.0%)

Minimum RMSE on the Pareto frontier at the highest attainable coverage threshold among 75%, 50%, 25%; if none, maximum frontier coverage. Descriptive practical choice, not a uniquely optimal model.

**Best source-held-out ensemble:** `ensemble:median`: sample-balanced RMSE 0.055576; pointwise RMSE 0.051167; points 608/1069 (56.9%); samples 30/77 (39.0%)

| Model | Points predicted / total | Coverage % | Samples predicted / total | Sample coverage % | SB RMSE | RMSE | MAE | Bias |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| calc_ptf_cosby1984_univariate | 56/1069 | 5.24 | 6/77 | 7.79 | 0.022732 | 0.022609 | 0.018181 | +0.005575 |
| calc_ptf_weynants2009 | 56/1069 | 5.24 | 6/77 | 7.79 | 0.026969 | 0.027043 | 0.020011 | +0.007444 |
| calc_ptf_williams1992_function_1 | 56/1069 | 5.24 | 6/77 | 7.79 | 0.036729 | 0.036438 | 0.031321 | +0.016493 |
| calc_ptf_varallyai1982_chernozem_b | 608/1069 | 56.88 | 30/77 | 38.96 | 0.045390 | 0.043883 | 0.035539 | +0.018482 |
| calc_ptf_mayr1999 | 56/1069 | 5.24 | 6/77 | 7.79 | 0.053380 | 0.053581 | 0.047149 | +0.026283 |
| calc_ptf_vereecken1989 | 56/1069 | 5.24 | 6/77 | 7.79 | 0.055469 | 0.055367 | 0.044928 | +0.033822 |
| calc_ptf_saxton2006 | 24/1069 | 2.25 | 6/77 | 7.79 | 0.056010 | 0.056010 | 0.044293 | +0.039548 |
| calc_ptf_varallyai1982_chernozem_a | 608/1069 | 56.88 | 30/77 | 38.96 | 0.056260 | 0.048728 | 0.038443 | +0.003586 |
| calc_ptf_saxton1986_calcptf_parameters | 329/1069 | 30.78 | 8/77 | 10.39 | 0.062269 | 0.060812 | 0.055266 | +0.054672 |
| calc_ptf_varallyai1982_chernozem_c | 608/1069 | 56.88 | 30/77 | 38.96 | 0.066577 | 0.068904 | 0.063014 | +0.037084 |
| calc_ptf_varallyai1982_meadow | 495/1069 | 46.30 | 17/77 | 22.08 | 0.067764 | 0.053990 | 0.047196 | -0.032661 |
| calc_ptf_clapp1978 | 495/1069 | 46.30 | 17/77 | 22.08 | 0.087605 | 0.101707 | 0.091391 | +0.090859 |
| calc_ptf_gupta1979 | 24/1069 | 2.25 | 6/77 | 7.79 | 0.093922 | 0.093922 | 0.088877 | +0.088877 |
| family_gunarathna2019_set1_WRC_volume | 90/1069 | 8.42 | 7/77 | 9.09 | 0.094935 | 0.093571 | 0.090931 | +0.090931 |
| calc_ptf_tomasella1998 | 24/1069 | 2.25 | 6/77 | 7.79 | 0.097937 | 0.097937 | 0.093632 | +0.093632 |
| family_lal1979_group_i_from_clay_WRC_mass | 165/1069 | 15.43 | 26/77 | 33.77 | 0.140599 | 0.114355 | 0.099315 | -0.099315 |
| family_lal1979_group_i_from_sand_WRC_mass | 118/1069 | 11.04 | 9/77 | 11.69 | 0.172430 | 0.170455 | 0.166993 | +0.166993 |
| family_lal1979_group_ii_from_clay_WRC_mass | 165/1069 | 15.43 | 26/77 | 33.77 | 0.176990 | 0.151568 | 0.141682 | -0.141682 |
| family_lal1979_group_ii_from_sand_WRC_mass | 118/1069 | 11.04 | 9/77 | 11.69 | 0.217401 | 0.215445 | 0.211310 | +0.211310 |
| calc_ptf_chakraborty2011_eq2 | 8/1069 | 0.75 | 2/77 | 2.60 | 0.233739 | 0.233739 | 0.233341 | +0.233341 |
| calc_ptf_chakraborty2011_eq5 | 8/1069 | 0.75 | 2/77 | 2.60 | 0.323019 | 0.323019 | 0.321632 | +0.321632 |
| calc_ptf_chakraborty2011_eq3 | 8/1069 | 0.75 | 2/77 | 2.60 | 0.326632 | 0.326632 | 0.325015 | +0.325015 |
| ensemble:median | 608/1069 | 56.88 | 30/77 | 38.96 | 0.055576 | 0.051167 | 0.041782 | +0.012519 |
| ensemble:all_available_mean | 608/1069 | 56.88 | 30/77 | 38.96 | 0.058693 | 0.051424 | 0.040604 | +0.009346 |
| ensemble:top_5 | 608/1069 | 56.88 | 30/77 | 38.96 | 0.059789 | 0.067883 | 0.059175 | +0.040947 |
| ensemble:top_3 | 555/1069 | 51.92 | 23/77 | 29.87 | 0.085176 | 0.099337 | 0.087823 | +0.071736 |

Ensemble comparison with the best individual at highest attained threshold (50%):

- ensemble:median: common-point SB RMSE 0.055576 versus 0.045390; N=608; lower error: False; coverage at least individual: True.
- ensemble:all_available_mean: common-point SB RMSE 0.058693 versus 0.045390; N=608; lower error: False; coverage at least individual: True.
- ensemble:top_5: common-point SB RMSE 0.059789 versus 0.045390; N=608; lower error: False; coverage at least individual: True.
- ensemble:top_3: common-point SB RMSE 0.085176 versus 0.045838; N=555; lower error: False; coverage at least individual: False.

## gravimetric_water_content

**Best accuracy:** `family_lal1979_group_i_from_sand_WRC_mass`: sample-balanced RMSE 0.069892; pointwise RMSE 0.069892; points 40/632 (6.3%); samples 10/65 (15.4%)

**Best individual at coverage >= 25%:** No eligible model

**Best individual at coverage >= 50%:** No eligible model

**Best individual at coverage >= 75%:** No eligible model

**Accuracy-coverage compromise:** `family_lal1979_group_i_from_clay_WRC_mass`: sample-balanced RMSE 0.180691; pointwise RMSE 0.179996; points 69/632 (10.9%); samples 17/65 (26.2%)

Minimum RMSE on the Pareto frontier at the highest attainable coverage threshold among 75%, 50%, 25%; if none, maximum frontier coverage. Descriptive practical choice, not a uniquely optimal model.

**Best source-held-out ensemble:** `ensemble:all_available_mean`: sample-balanced RMSE 0.188362; pointwise RMSE 0.187701; points 69/632 (10.9%); samples 17/65 (26.2%)

| Model | Points predicted / total | Coverage % | Samples predicted / total | Sample coverage % | SB RMSE | RMSE | MAE | Bias |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| family_lal1979_group_i_from_sand_WRC_mass | 40/632 | 6.33 | 10/65 | 15.38 | 0.069892 | 0.069892 | 0.060234 | +0.010509 |
| family_lal1979_group_ii_from_sand_WRC_mass | 40/632 | 6.33 | 10/65 | 15.38 | 0.079074 | 0.079074 | 0.070608 | +0.036888 |
| calc_ptf_chakraborty2011_eq4 | 30/632 | 4.75 | 10/65 | 15.38 | 0.087744 | 0.087744 | 0.072986 | +0.048010 |
| calc_ptf_chakraborty2011_eq1 | 30/632 | 4.75 | 10/65 | 15.38 | 0.088089 | 0.088089 | 0.073213 | +0.049274 |
| calc_ptf_oosterveld1980_retention | 32/632 | 5.06 | 8/65 | 12.31 | 0.142891 | 0.142891 | 0.132346 | -0.132346 |
| family_lal1979_group_i_from_clay_WRC_mass | 69/632 | 10.92 | 17/65 | 26.15 | 0.180691 | 0.179996 | 0.166050 | -0.166050 |
| family_lal1979_group_ii_from_clay_WRC_mass | 69/632 | 10.92 | 17/65 | 26.15 | 0.196230 | 0.195604 | 0.181612 | -0.181612 |
| ensemble:all_available_mean | 69/632 | 10.92 | 17/65 | 26.15 | 0.188362 | 0.187701 | 0.173831 | -0.173831 |
| ensemble:median | 69/632 | 10.92 | 17/65 | 26.15 | 0.188362 | 0.187701 | 0.173831 | -0.173831 |
| ensemble:top_3 | 40/632 | 6.33 | 10/65 | 15.38 | 0.211805 | 0.211805 | 0.202618 | -0.202618 |
| ensemble:top_5 | 40/632 | 6.33 | 10/65 | 15.38 | 0.211805 | 0.211805 | 0.202618 | -0.202618 |

Ensemble comparison with the best individual at maximum available coverage (below 25%):

- ensemble:all_available_mean: common-point SB RMSE 0.188362 versus 0.180691; N=69; lower error: False; coverage at least individual: True.
- ensemble:median: common-point SB RMSE 0.188362 versus 0.180691; N=69; lower error: False; coverage at least individual: True.
- ensemble:top_3: common-point SB RMSE 0.211805 versus 0.205477; N=40; lower error: False; coverage at least individual: False.
- ensemble:top_5: common-point SB RMSE 0.211805 versus 0.205477; N=40; lower error: False; coverage at least individual: False.

## Ksat

Ksat remains a separate benchmark without ensembles. The original common-cohort and maximum-coverage recommendations and source/unit caveats are retained: Ferrer-Julia gleyic cambisol sand on the 30-sample common set; Dane-Puckett on all 39 samples. Per-function log10 RMSE, MAE, bias, factor fractions and block sensitivity are saved in ksat_metrics.json and shown in the regenerated PNG.

## Approximation and artifacts

Four approximation families are fitted separately to each water basis. These are same-data fits, never independent PTF observations. Aggregated PNG use all accepted fits per family, with eligible counts and relaxed/strict success shown explicitly; per-sample curves stay inside observed support.

See wrc_accuracy_coverage.csv, ptf_selection_summary.csv, selection_v1.0.json, PNG-AUDIT.md and wrc_accuracy_coverage.png. Private ledger, predictions, diagnostic_index.csv, all diagnostic PNG and ZIP are in local/meta-final-v1_0-pointwise/. Reproduce with the commands in ../README.md.

| Basis | Approximation family | Accepted / total samples | Median RMSE | Median MAE | Median bias |
|---|---|---:|---:|---:|---:|
| volumetric_water_content | van_genuchten_mualem_v1 | 76/77 | 0.008226 | 0.006779 | +0.000000 |
| volumetric_water_content | van_genuchten_m1_v1 | 76/77 | 0.007472 | 0.006102 | +0.000000 |
| volumetric_water_content | brooks_corey_v1 | 76/77 | 0.010739 | 0.008741 | +0.000000 |
| volumetric_water_content | clapp1978_gradual_air_entry_v1 | 76/77 | 0.011478 | 0.009293 | +0.000000 |
| gravimetric_water_content | van_genuchten_mualem_v1 | 65/65 | 0.011576 | 0.008915 | +0.000353 |
| gravimetric_water_content | van_genuchten_m1_v1 | 65/65 | 0.009073 | 0.007116 | +0.000000 |
| gravimetric_water_content | brooks_corey_v1 | 65/65 | 0.014410 | 0.011688 | +0.000570 |
| gravimetric_water_content | clapp1978_gradual_air_entry_v1 | 65/65 | 0.016585 | 0.013586 | +0.000622 |

Legacy expanded_selection.json and point_target_selection.json retain historical cohort analyses. They are supplementary records, not the current primary WRC ranking.
