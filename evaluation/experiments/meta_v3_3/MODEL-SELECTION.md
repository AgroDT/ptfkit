# meta_v3.3 model selection

Dataset-specific exploratory selection with E0-E5 provenance retained. New workbook-only targets and approximate predictor mappings are explicitly E5; their measurement origin and laboratory protocol are not independently confirmed. No universal best PTF is claimed.

**Best expanded-cohort atomic WRC:** `calc_ptf_varallyai1982_chernozem_b`. **Best pooled WRC blend:** mean; its pooled gain does not establish a robust improvement.

**Maximum-coverage atomic Ksat recommendation:** `calc_ptf_ferrerjulia2004_dane_puckett` on 39 samples, with the block sensitivity below. This differs from the broad-roster winner on a smaller common cohort.

## volumetric_water_content

Exact primary cohort: 17 samples, 495 observations, 2 sources. Pressure range (kPa): [0.060472707225, 257941.17602720842].

| Rank | PTF | RMSE | MAE | Bias | Median AE | Samples | Points | Coverage |
|---|---|---|---|---|---|---|---|---|
| 1 | `calc_ptf_varallyai1982_chernozem_b` | 0.0421222 | 0.0339696 | 0.0112252 | 0.031243 | 17 | 495 | 17/77 |
| 2 | `calc_ptf_varallyai1982_chernozem_a` | 0.0426921 | 0.0360737 | 0.00109464 | 0.0373289 | 17 | 495 | 17/77 |
| 3 | `calc_ptf_varallyai1982_meadow` | 0.0677636 | 0.0574108 | -0.0126922 | 0.047438 | 17 | 495 | 17/77 |
| 4 | `calc_ptf_varallyai1982_chernozem_c` | 0.0687036 | 0.0624736 | 0.0230227 | 0.0641419 | 17 | 495 | 17/77 |
| 5 | `calc_ptf_clapp1978` | 0.087605 | 0.0738511 | 0.0730028 | 0.0922938 | 17 | 495 | 17/77 |

Full executable-roster common points: 24. All closed compatible cohorts and exact pairwise comparisons are in summary.json.

Robustness: source_id. Full rank ranges, best fractions and RMSE distributions are in the aggregate checkpoint.

Best atomic on this exact cohort: `calc_ptf_varallyai1982_chernozem_b`. Median resample rank 2.0; rank range [2, 2]; fraction best 0.0%; RMSE quantiles (min, 2.5%, median, 97.5%, max) [0.041307935291870726, 0.04136462580575551, 0.04244174556956648, 0.043518865333377454, 0.04357555584726224].

| Ensemble | RMSE | Change vs best atomic |
|---|---|---|
| mean | 0.0395031 | -6.22% |
| median | 0.0435734 | +3.45% |
| reduced | 0.0400807 | -4.85% |

Reduced members (descriptive full-data choice): `calc_ptf_varallyai1982_chernozem_b`, `calc_ptf_varallyai1982_chernozem_a`.

Reduced membership is selected again on training groups for outer held-out evaluation; its full-data score alone is selection-biased.

Nested source/profile-held-out reduced-ensemble RMSE: 0.0631245. Membership is selected on training groups; comparison against both training-selected and pooled-best atomic functions is retained.

No ensemble meets the registered robust-improvement rule.

Top-two atomic residual correlation: 0.703097.

| Pressure region | Samples | Best atomic bias | Mean-ensemble bias |
|---|---|---|---|
| wet | 17 | -0.00209368 | 0.00773486 |
| intermediate | 15 | -0.00147014 | -0.00128478 |
| dry | 6 | -0.0126988 | 0.00920261 |

A mean can cancel opposing residual biases on the pooled cohort. Highly correlated errors add little diversity, and a bias cancellation that changes with source does not establish a reliable ensemble gain.

## gravimetric_water_content

Exact primary cohort: 8 samples, 24 observations, 1 sources. Pressure range (kPa): [93.76498221374136, 585.612954873337].

| Rank | PTF | RMSE | MAE | Bias | Median AE | Samples | Points | Coverage |
|---|---|---|---|---|---|---|---|---|
| 1 | `calc_ptf_chakraborty2011_eq4` | 0.089888 | 0.075289 | 0.0441193 | 0.0731159 | 8 | 24 | 8/65 |
| 2 | `calc_ptf_chakraborty2011_eq1` | 0.0900294 | 0.0752097 | 0.0452861 | 0.0722164 | 8 | 24 | 8/65 |
| 3 | `calc_ptf_oosterveld1980_retention` | 0.132764 | 0.122888 | -0.122888 | 0.105893 | 8 | 24 | 8/65 |

Full executable-roster common points: 24. All closed compatible cohorts and exact pairwise comparisons are in summary.json.

Robustness: sample_bootstrap. Full rank ranges, best fractions and RMSE distributions are in the aggregate checkpoint.

Best atomic on this exact cohort: `calc_ptf_chakraborty2011_eq4`. Median resample rank 1.0; rank range [1, 2]; fraction best 54.4%; RMSE quantiles (min, 2.5%, median, 97.5%, max) [0.05917485696687052, 0.06911196082444176, 0.08986817351495459, 0.10726307334364049, 0.11301796380878576].

| Ensemble | RMSE | Change vs best atomic |
|---|---|---|
| mean | 0.0651088 | -27.57% |
| median | 0.0898763 | -0.01% |
| reduced | 0.0706746 | -21.37% |

Reduced members (descriptive full-data choice): `calc_ptf_chakraborty2011_eq4`, `calc_ptf_oosterveld1980_retention`.

Reduced membership is selected again on training groups for outer held-out evaluation; its full-data score alone is selection-biased.

No ensemble meets the registered robust-improvement rule.

Top-two atomic residual correlation: 0.999863.

| Pressure region | Samples | Best atomic bias | Mean-ensemble bias |
|---|---|---|---|
| intermediate | 8 | 0.0441193 | -0.011161 |

A mean can cancel opposing residual biases on the pooled cohort. Highly correlated errors add little diversity, and a bias cancellation that changes with source does not establish a reliable ensemble gain.

## ksat

Exact primary cohort: 30 samples, 30 observations, 2 sources. Pressure range (kPa): None.

| Rank | PTF | RMSE log10 | MAE log10 | Log bias | x2 | x5 | x10 | N | Blocks |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `calc_ptf_ferrerjulia2004_gleyic_cambisol_sand` | 0.270425 | 0.205407 | 0.0619678 | 80.0% | 96.7% | 100.0% | 30 | 2 |
| 2 | `calc_ptf_ferrerjulia2004_chromic_luvisol_sand` | 0.285567 | 0.20214 | 0.0615582 | 73.3% | 96.7% | 100.0% | 30 | 2 |
| 3 | `calc_ptf_ferrerjulia2004_general_sand` | 0.286166 | 0.202747 | 0.0619215 | 73.3% | 96.7% | 100.0% | 30 | 2 |
| 4 | `calc_ptf_ferrerjulia2004_calcic_cambisol_sand` | 0.287461 | 0.23824 | -0.0155086 | 70.0% | 100.0% | 100.0% | 30 | 2 |
| 5 | `calc_ptf_ferrerjulia2004_gleyic_luvisol_sand` | 0.290489 | 0.262099 | -0.092072 | 63.3% | 100.0% | 100.0% | 30 | 2 |
| 6 | `calc_ptf_ferrerjulia2004_orthic_luvisol_sand` | 0.294427 | 0.222688 | 0.0399928 | 73.3% | 100.0% | 100.0% | 30 | 2 |
| 7 | `calc_ptf_ferrerjulia2004_calcaric_fluvisol_sand` | 0.294642 | 0.199649 | 0.106857 | 73.3% | 96.7% | 100.0% | 30 | 2 |
| 8 | `calc_ptf_ferrerjulia2004_eutric_cambisol_sand` | 0.298257 | 0.199854 | 0.109817 | 76.7% | 96.7% | 100.0% | 30 | 2 |
| 9 | `calc_ptf_ferrerjulia2004_dystric_regosol_sand` | 0.298897 | 0.199696 | 0.100734 | 73.3% | 96.7% | 100.0% | 30 | 2 |
| 10 | `calc_ptf_ferrerjulia2004_humic_cambisol_sand` | 0.308072 | 0.243304 | 0.0271015 | 70.0% | 96.7% | 100.0% | 30 | 2 |

Full executable-roster common points: 30. All closed compatible cohorts and exact pairwise comparisons are in summary.json.

Robustness: block. Full rank ranges, best fractions and RMSE distributions are in the aggregate checkpoint.

Best pooled: `calc_ptf_ferrerjulia2004_gleyic_cambisol_sand`. Median predicted/observed ratio 0.9913; within factors 2/5/10: 80.0%/96.7%/100.0%.

Best rank-stable: `calc_ptf_ferrerjulia2004_humic_acrisol_texture_organic_matter` (median rank 10.5, range [2, 19], fraction best 0.0%). Highest coverage example: `calc_ptf_ferrerjulia2004_dane_puckett` (39 samples).

All-block comparison: 39 samples across 4 blocks; best `calc_ptf_ferrerjulia2004_dane_puckett` with log10 RMSE 0.717641. This is a separate exact cohort; its error is not directly ranked against the broader-roster table above.

| Block | Best atomic | RMSE log10 | N |
|---|---|---|---|
| master_cm_day | `calc_ptf_ferrerjulia2004_puckett` | 0.137818 | 3 |
| thesis_cm_day | `calc_ptf_ferrerjulia2004_dane_puckett` | 0.344314 | 1 |
| thesis_cm_min_assumed | `calc_ptf_ferrerjulia2004_dane_puckett` | 0.660217 | 30 |
| thesis_m_day | `calc_ptf_wosten2001_loam_clay_table5` | 0.343962 | 5 |

All-block leave-one-block-out winners: `master_cm_day` -> `calc_ptf_ferrerjulia2004_dane_puckett` (N=36), `thesis_cm_day` -> `calc_ptf_ferrerjulia2004_dane_puckett` (N=38), `thesis_cm_min_assumed` -> `calc_ptf_wosten2001_loam_clay_table5` (N=9), `thesis_m_day` -> `calc_ptf_ferrerjulia2004_dane_puckett` (N=34).

The maximum-coverage recommendation is the all-block pooled winner, with block sensitivity explicitly retained. No single PTF wins after every block omission. The broad-roster pooled leader is dominated by the cm/min-assumed block; removing that block changes its ranking.


Class-specific Ferrer-Julia regressions are tested across workbook soils as an E5 applicability extrapolation; the workbook does not establish their FAO classes. A pooled win is not source-domain validation.

## Reviewed-target sensitivity and residuals

| Basis | Samples | Points | Best atomic | RMSE |
|---|---|---|---|---|
| volumetric_water_content | 19 | 169 | `calc_ptf_varallyai1982_chernozem_b` | 0.0475936 |
| gravimetric_water_content | 8 | 24 | `calc_ptf_chakraborty2011_eq4` | 0.089888 |

These are separate exact cohorts, so their RMSE values do not rank against the expanded-cohort scores. Smaller compatible cohorts retain additional atomic models, including the source-faithful Cosby dry-branch model. Pressure-specific regression curves are interpolated only between at least three native output pressures; their scores do not establish wet-to-dry extrapolation skill.

Top-model residual correlations and fixed wet [0,10), intermediate [10,1500), dry [1500,infinity) kPa biases are in the checkpoint; detailed pressure residuals stay private. Reduced members require complementary residuals, rather than averaging only close variants of one formula.

The extreme low Wosten Table 5 Ksat forecast was independently recalculated from its specification: the large organic-matter proxy drives the exponential to about 1e-138 m/s. The adapter uses the already exponentiated linear cm/day output and converts once to m/s. No sign, double-log or conversion defect was found; no formula was calibrated or clipped.

## Compatible WRC cohorts

| Basis | Models | Samples | Points | Best atomic | Atomic RMSE | Best pooled blend | Blend RMSE |
|---|---|---|---|---|---|---|---|
| volumetric_water_content | 3 | 30 | 608 | `calc_ptf_varallyai1982_chernozem_b` | 0.04539 | reduced | 0.048889 |
| volumetric_water_content | 5 | 17 | 495 | `calc_ptf_varallyai1982_chernozem_b` | 0.0421222 | mean | 0.0395031 |
| volumetric_water_content | 13 | 6 | 24 | `calc_ptf_cosby1984_univariate` | 0.0268864 | mean | 0.0274991 |
| volumetric_water_content | 10 | 6 | 56 | `calc_ptf_cosby1984_univariate` | 0.0227324 | reduced | 0.0239091 |
| gravimetric_water_content | 2 | 10 | 30 | `calc_ptf_chakraborty2011_eq4` | 0.0877439 | mean | 0.0879119 |
| gravimetric_water_content | 3 | 8 | 24 | `calc_ptf_chakraborty2011_eq4` | 0.089888 | mean | 0.0651088 |

Each row uses its own exact common sample/pressure set. Errors must not be ranked across rows. Full atomic rankings, member lists and held-out ensemble comparisons are retained for every cohort.

## Dataset sufficiency

Available WRC ledger: 1701 points, 142 samples, 120 identified sample/horizon records, 19 source labels, 1 explicitly identified profile. 136 samples lack an explicit profile ID. Pressure range [0.0, 9806650.0] kPa. Counts describe workbook records, not independently verified laboratory measurements.

Ksat ledger: 39 observations/samples, 3 source labels, four unit/source blocks; no confirmed profile grouping. Canonical range [9.259259259259259e-07, 4.266666666666667e-05] m/s.

Actual scored union across eligible standalone functions (duplicate function predictions counted once per observation): gravimetric_water_content: 38 points / 10 samples / 1 sources; ksat: 39 points / 39 samples / 3 sources; volumetric_water_content: 608 points / 30 samples / 3 sources.

WRC basis counts: {'volumetric_water_content': 1069, 'gravimetric_water_content': 632}. The new E5 audit contributes 665 additional pairs; ambiguous saturation markers, unresolved derived curves and repeated heads without measurement-level replicate evidence remain excluded. Raw pressure/water cells, original encodings, normalization and origin status are retained in the private ledger.

All used cells rescanned. All interpretable released WRC and explicit eligible conductivity blocks accounted for; unresolved WRC quantity/axis/origin rows remain exclusions, not proof of absent measurements.

WRC basis/axis/provenance exclusions remain explicit. Fitted parameters, copied views and Rosetta-derived Ksat never increase experimental N. Ksat method and origin are unconfirmed under permissive workbook semantics; cm/smin is interpreted as cm/min. The three additional master cm/day values are a separate block.

See model-selection-summary.json for all metrics, coverage, factor errors, block metrics, residual patterns and rank stability. Private ledgers, candidate decisions and predictions are retained only in ignored local storage.

Reproduce from the repository root with `mise run eval:model-selection local/meta-catalog-resource local/meta-catalog-harmonized local/meta_v3.3.xlsx local/meta-model-selection`. The output directory must be new. Repeat with a second new output directory and compare artifact-hashes.json byte for byte. The aggregate checkpoint is evaluation/datasets/meta_v3_3.model-selection-summary.json.
