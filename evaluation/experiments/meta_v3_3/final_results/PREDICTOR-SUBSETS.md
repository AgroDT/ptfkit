# ptfkit predictor-defined testing subsets

Every experimental target is assigned once to a predictor record using exact source/sample identity and the existing reviewed record matcher. No cross-row union, imputation or target-based selection is used to construct the reported predictor sets. Missing or ambiguous rows remain an explicit subset. Water retention and Ksat are separate targets.

Exact predictor signatures: 26. Predictor records: 180.

| Basis | Samples | Predictor records | Observations | Sources |
|---|---:|---:|---:|---:|
| volumetric_water_content | 77 | 77 | 1069 | 9 |
| gravimetric_water_content | 65 | 65 | 632 | 10 |
| ksat | 39 | 39 | 39 | 3 |

## Available testing pools

Pools require the named predictors and include records with additional predictors. They overlap. Exact signature subsets are disjoint at the predictor-record level; a physical sample appearing in several target views must remain in the same validation fold.

`reported` uses actual numeric, non-formula workbook cells. `e5_usable` additionally uses existing registered same-record transformations/proxies, with full evidence saved. Derived OC/OM, PSD closure, boundary proxies and density/porosity conversions are not relabelled as measurements. Availability is not proof of a compatible laboratory method or applicability of a specific PTF.

Texture cutoffs are retained in exact signatures (including clay <1 versus <2 micrometres and original PSD bins). Generic texture pools mean availability of the reported components, not verified USDA fractions. Pressure and measured target water contents are not predictors. Specific formulas still require domain, pressure-support, water-basis and native-output checks.

Generic E5 texture availability excludes filling missing fractions with class-average values. Source-specific reviewed class-midpoint inputs, such as the Cosby route, remain model-specific and are assessed in function_input_eligibility.csv. A reported or derived texture class is its own predictor, not three measured fractions.

| Pool | Policy | Basis | Samples | Points |
|---|---|---|---:|---:|
| texture_class | reported | volumetric_water_content | 6 | 56 |
| texture_class | reported | gravimetric_water_content | 0 | 0 |
| texture_class | reported | ksat | 0 | 0 |
| texture_class_bd | reported | volumetric_water_content | 6 | 56 |
| texture_class_bd | reported | gravimetric_water_content | 0 | 0 |
| texture_class_bd | reported | ksat | 0 | 0 |
| clay | reported | volumetric_water_content | 19 | 169 |
| clay | reported | gravimetric_water_content | 17 | 218 |
| clay | reported | ksat | 9 | 9 |
| sand | reported | volumetric_water_content | 0 | 0 |
| sand | reported | gravimetric_water_content | 10 | 130 |
| sand | reported | ksat | 0 | 0 |
| bulk_density | reported | volumetric_water_content | 38 | 732 |
| bulk_density | reported | gravimetric_water_content | 27 | 285 |
| bulk_density | reported | ksat | 39 | 39 |
| organic_carbon | reported | volumetric_water_content | 20 | 206 |
| organic_carbon | reported | gravimetric_water_content | 37 | 428 |
| organic_carbon | reported | ksat | 36 | 36 |
| clay_bd | reported | volumetric_water_content | 19 | 169 |
| clay_bd | reported | gravimetric_water_content | 6 | 76 |
| clay_bd | reported | ksat | 9 | 9 |
| clay_oc | reported | volumetric_water_content | 16 | 150 |
| clay_oc | reported | gravimetric_water_content | 17 | 218 |
| clay_oc | reported | ksat | 6 | 6 |
| clay_bd_oc | reported | volumetric_water_content | 16 | 150 |
| clay_bd_oc | reported | gravimetric_water_content | 6 | 76 |
| clay_bd_oc | reported | ksat | 6 | 6 |
| sand_clay | reported | volumetric_water_content | 0 | 0 |
| sand_clay | reported | gravimetric_water_content | 10 | 130 |
| sand_clay | reported | ksat | 0 | 0 |
| sand_clay_bd | reported | volumetric_water_content | 0 | 0 |
| sand_clay_bd | reported | gravimetric_water_content | 0 | 0 |
| sand_clay_bd | reported | ksat | 0 | 0 |
| sand_clay_oc | reported | volumetric_water_content | 0 | 0 |
| sand_clay_oc | reported | gravimetric_water_content | 10 | 130 |
| sand_clay_oc | reported | ksat | 0 | 0 |
| sand_clay_bd_oc | reported | volumetric_water_content | 0 | 0 |
| sand_clay_bd_oc | reported | gravimetric_water_content | 0 | 0 |
| sand_clay_bd_oc | reported | ksat | 0 | 0 |
| texture | reported | volumetric_water_content | 0 | 0 |
| texture | reported | gravimetric_water_content | 10 | 130 |
| texture | reported | ksat | 0 | 0 |
| texture_bd | reported | volumetric_water_content | 0 | 0 |
| texture_bd | reported | gravimetric_water_content | 0 | 0 |
| texture_bd | reported | ksat | 0 | 0 |
| texture_oc | reported | volumetric_water_content | 0 | 0 |
| texture_oc | reported | gravimetric_water_content | 10 | 130 |
| texture_oc | reported | ksat | 0 | 0 |
| texture_om | reported | volumetric_water_content | 0 | 0 |
| texture_om | reported | gravimetric_water_content | 10 | 130 |
| texture_om | reported | ksat | 0 | 0 |
| texture_bd_oc | reported | volumetric_water_content | 0 | 0 |
| texture_bd_oc | reported | gravimetric_water_content | 0 | 0 |
| texture_bd_oc | reported | ksat | 0 | 0 |
| texture_bd_om | reported | volumetric_water_content | 0 | 0 |
| texture_bd_om | reported | gravimetric_water_content | 0 | 0 |
| texture_bd_om | reported | ksat | 0 | 0 |
| texture_bd_oc_ph | reported | volumetric_water_content | 0 | 0 |
| texture_bd_oc_ph | reported | gravimetric_water_content | 0 | 0 |
| texture_bd_oc_ph | reported | ksat | 0 | 0 |
| texture_bd_oc_pd | reported | volumetric_water_content | 0 | 0 |
| texture_bd_oc_pd | reported | gravimetric_water_content | 0 | 0 |
| texture_bd_oc_pd | reported | ksat | 0 | 0 |
| texture_bd_oc_porosity | reported | volumetric_water_content | 0 | 0 |
| texture_bd_oc_porosity | reported | gravimetric_water_content | 0 | 0 |
| texture_bd_oc_porosity | reported | ksat | 0 | 0 |
| texture_class | e5_usable | volumetric_water_content | 17 | 495 |
| texture_class | e5_usable | gravimetric_water_content | 10 | 130 |
| texture_class | e5_usable | ksat | 0 | 0 |
| texture_class_bd | e5_usable | volumetric_water_content | 17 | 495 |
| texture_class_bd | e5_usable | gravimetric_water_content | 0 | 0 |
| texture_class_bd | e5_usable | ksat | 0 | 0 |
| clay | e5_usable | volumetric_water_content | 30 | 608 |
| clay | e5_usable | gravimetric_water_content | 17 | 218 |
| clay | e5_usable | ksat | 39 | 39 |
| sand | e5_usable | volumetric_water_content | 11 | 439 |
| sand | e5_usable | gravimetric_water_content | 10 | 130 |
| sand | e5_usable | ksat | 33 | 33 |
| bulk_density | e5_usable | volumetric_water_content | 38 | 732 |
| bulk_density | e5_usable | gravimetric_water_content | 27 | 285 |
| bulk_density | e5_usable | ksat | 39 | 39 |
| organic_carbon | e5_usable | volumetric_water_content | 24 | 237 |
| organic_carbon | e5_usable | gravimetric_water_content | 37 | 428 |
| organic_carbon | e5_usable | ksat | 39 | 39 |
| clay_bd | e5_usable | volumetric_water_content | 30 | 608 |
| clay_bd | e5_usable | gravimetric_water_content | 6 | 76 |
| clay_bd | e5_usable | ksat | 39 | 39 |
| clay_oc | e5_usable | volumetric_water_content | 17 | 158 |
| clay_oc | e5_usable | gravimetric_water_content | 17 | 218 |
| clay_oc | e5_usable | ksat | 39 | 39 |
| clay_bd_oc | e5_usable | volumetric_water_content | 17 | 158 |
| clay_bd_oc | e5_usable | gravimetric_water_content | 6 | 76 |
| clay_bd_oc | e5_usable | ksat | 39 | 39 |
| sand_clay | e5_usable | volumetric_water_content | 11 | 439 |
| sand_clay | e5_usable | gravimetric_water_content | 10 | 130 |
| sand_clay | e5_usable | ksat | 33 | 33 |
| sand_clay_bd | e5_usable | volumetric_water_content | 11 | 439 |
| sand_clay_bd | e5_usable | gravimetric_water_content | 0 | 0 |
| sand_clay_bd | e5_usable | ksat | 33 | 33 |
| sand_clay_oc | e5_usable | volumetric_water_content | 0 | 0 |
| sand_clay_oc | e5_usable | gravimetric_water_content | 10 | 130 |
| sand_clay_oc | e5_usable | ksat | 33 | 33 |
| sand_clay_bd_oc | e5_usable | volumetric_water_content | 0 | 0 |
| sand_clay_bd_oc | e5_usable | gravimetric_water_content | 0 | 0 |
| sand_clay_bd_oc | e5_usable | ksat | 33 | 33 |
| texture | e5_usable | volumetric_water_content | 11 | 439 |
| texture | e5_usable | gravimetric_water_content | 10 | 130 |
| texture | e5_usable | ksat | 0 | 0 |
| texture_bd | e5_usable | volumetric_water_content | 11 | 439 |
| texture_bd | e5_usable | gravimetric_water_content | 0 | 0 |
| texture_bd | e5_usable | ksat | 0 | 0 |
| texture_oc | e5_usable | volumetric_water_content | 0 | 0 |
| texture_oc | e5_usable | gravimetric_water_content | 10 | 130 |
| texture_oc | e5_usable | ksat | 0 | 0 |
| texture_om | e5_usable | volumetric_water_content | 0 | 0 |
| texture_om | e5_usable | gravimetric_water_content | 10 | 130 |
| texture_om | e5_usable | ksat | 0 | 0 |
| texture_bd_oc | e5_usable | volumetric_water_content | 0 | 0 |
| texture_bd_oc | e5_usable | gravimetric_water_content | 0 | 0 |
| texture_bd_oc | e5_usable | ksat | 0 | 0 |
| texture_bd_om | e5_usable | volumetric_water_content | 0 | 0 |
| texture_bd_om | e5_usable | gravimetric_water_content | 0 | 0 |
| texture_bd_om | e5_usable | ksat | 0 | 0 |
| texture_bd_oc_ph | e5_usable | volumetric_water_content | 0 | 0 |
| texture_bd_oc_ph | e5_usable | gravimetric_water_content | 0 | 0 |
| texture_bd_oc_ph | e5_usable | ksat | 0 | 0 |
| texture_bd_oc_pd | e5_usable | volumetric_water_content | 0 | 0 |
| texture_bd_oc_pd | e5_usable | gravimetric_water_content | 0 | 0 |
| texture_bd_oc_pd | e5_usable | ksat | 0 | 0 |
| texture_bd_oc_porosity | e5_usable | volumetric_water_content | 0 | 0 |
| texture_bd_oc_porosity | e5_usable | gravimetric_water_content | 0 | 0 |
| texture_bd_oc_porosity | e5_usable | ksat | 0 | 0 |

## Files and testing

- `predictor_subset_summary.csv`: aggregate exact signatures, without private identities.
- `predictor_pool_summary.csv`: aggregate counts for overlapping testing pools.
- `local/meta-predictor-subsets-v1_0/sample_membership.csv`: exact membership and predictor record.
- `local/meta-predictor-subsets-v1_0/predictor-records.json`: reported cells, E5 values, evidence and targets.
- `local/meta-predictor-subsets-v1_0/exact/`: one complete dataset per exact signature and target basis.
- `local/meta-predictor-subsets-v1_0/pools/`: complete datasets for reported and E5 testing pools.
- `local/meta-predictor-subsets-v1_0/function_input_eligibility.csv`: function-specific input/domain checks. Native predictions were not evaluated by this grouping step.

Split by source, or by profile/sample when appropriate, before model selection. Keep every pressure of the same physical sample in the same fold, including water-basis views and memberships in overlapping pools. These are availability subsets, not statistically independent train/test splits.

## Two observations versus two samples

The current primary WRC table has no model scored on only two observations. Its smallest rows are Chakraborty2011 equations 2, 3 and 5: 8 experimental points in 2 samples. Those are different counts. Two samples are weak validation evidence and must be reported with their 0.75% point coverage (8/1069) and 2.60% sample coverage (2/77); a small error on that subset is not evidence for general superiority.

Secondary fixed-pressure functions may define only two native pressure outputs, such as 33 and 1500 kPa. That is the number of model outputs per sample, not the number of independent experimental observations in the primary benchmark. Reconstructed secondary targets remain explicitly separate.

Reproduce: `python -B -m evaluation.experiments.meta_v3_3.predictor_subsets` in the prepared ptfkit-eval environment.
