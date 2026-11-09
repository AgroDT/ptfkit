# ptfkit deep unlock audit

Historical 44-to-64 snapshot. The subsequent [workbook evidence review](WORKBOOK-EVIDENCE.md)
corrects the nitrogen, plasticity and ambiguous Ksat-unit candidate classifications
below. Frozen campaign artifacts remain unchanged.

Aggregate audit from 2026-10-26. The complete catalog benchmark was rerun in `local/meta-deep-unlock-audited`; its private observations and predictions are not redistributed. See the [aggregate checkpoint](../../datasets/meta_v3_3.deep-unlock-summary.json) and [reproduction instructions](README.md).

All 1050 evaluation tests passed. Independent NumPy checks verified 1191 cohorts, 2782 atomic metric rows, 3380 correlations and 6948 ensemble metric rows. All input/output inventories and implementation hashes passed integrity checks; strict predictions are byte-identical to the frozen baseline. Lint, formatting and type checks used installed Ruff 0.16.5 and ty 0.0.78; the pinned Mise runner and newer pinned versions were unavailable.

The three other unlocks are two retention-predictor terminology mappings and one explicit VG-Mualem model signature. Williams1992 Function 1 also requires the generic source-interval parser; attribution assigns it to pressure mapping. Named and joint numeric source bounds are enforced before native execution.

Catalog: 216. Confirmed execution: **44 → 64**.

Discovery used all workbook sheets and used cells independently of the mapped schema. Candidate labels never authorize a binding. The frozen baseline and strict benchmark remain unchanged. The maximum across unreviewed workbook evidence remains unresolved.

## Decisions

| Decision | Functions |
| --- | ---: |
| candidate_requiring_workbook_evidence | 79 |
| current_executable | 44 |
| genuinely_target_absent_in_audited_workbook | 24 |
| physically_incompatible_or_unresolved | 4 |
| predictor_or_support_unresolved | 21 |
| target_contract_or_workbook_evidence_unresolved | 24 |
| unlockable_after_generic_semantic_mapping | 20 |

## Unlock attribution

| Mechanism | New functions |
| --- | ---: |
| generalized pressure mapping | 16 |
| compound target derivation | 1 |
| other | 3 |
| newly inventoried workbook target | 0 |
| newly inventoried predictor | 0 |
| partial-sample eligibility | 0 |

## Original target_absent decomposition

Families overlap for multi-output functions. Potential means a target route exists; predictors and physical contracts may still block execution. Definitely absent denotes experimental plasticity, moisture-equivalent, infiltration or unsaturated-conductivity targets with no corresponding populated measurement block in the full cell inventory and no deterministic derivation from WRC. It does not denote absence from the literature. All other unresolved definitions remain unresolved.

| Target family | Functions | Potentially derivable from current data | Definitely absent |
| --- | ---: | ---: | ---: |
| water content at specified pressure/suction | 23 | 23 | 0 |
| full water-retention curve | 8 | 8 | 0 |
| retention-model parameters | 22 | 8 | 0 |
| available water / available water capacity | 13 | 3 | 0 |
| field capacity | 5 | 0 | 0 |
| wilting point | 4 | 0 | 0 |
| moisture equivalent | 5 | 0 | 5 |
| saturated hydraulic conductivity | 55 | 0 | 0 |
| unsaturated conductivity | 1 | 0 | 1 |
| infiltration | 1 | 0 | 1 |
| bulk density | 0 | 0 | 0 |
| porosity | 0 | 0 | 0 |
| plasticity properties | 17 | 0 | 17 |
| other | 1 | 0 | 0 |

## Workbook second pass

| Sheet | Used cells visited | Populated/commented | Formulas | Comments | Hidden rows/columns |
| --- | ---: | ---: | ---: | ---: | --- |
| Данные | 72215 | 12012 | 723 | 0 | 0/0 |
| ОГХ | 46200 | 12840 | 3051 | 0 | 0/0 |
| ГС-PSD | 1020 | 560 | 32 | 0 | 0/0 |
| дп | 3870 | 1528 | 90 | 0 | 0/0 |
| ч | 10680 | 3022 | 150 | 0 | 0/0 |
| сл | 2024 | 933 | 45 | 0 | 0/0 |
| диссертации | 18483 | 3701 | 144 | 0 | 0/0 |
| диссертации_ссылки | 93 | 85 | 0 | 0 | 0/0 |

Every cell, cached formula value, comment, merged range, visibility flag and candidate column block is retained in the private scan artifact. Numeric points, sample labels and publication links are not reinterpreted as measurements. Repeated blocks and units embedded below headers remain separate candidates.

The dissertation view contains filled Ksat blocks and particle-density columns. Ksat units change by block (including m/day, an ambiguous cm/min label, and cm/day). Particle density, aggregate properties and porosity need identity, unit, measurement-origin and material review. These candidates invalidate a blanket claim that conductivity or particle density is absent, but release no new targets.

## Reverse predictor search

Names are retained exactly; the private inventory also stores every distinct source contract, so identical names do not imply identical particle-size bounds or protocols.

| Predictor | Functions requiring it | Inventoried evidence? | Candidate workbook locations | Scientific status |
| --- | ---: | --- | --- | --- |
| `sand` | 115 | 40 functions | Данные!L335, Данные!P1, диссертации!S1, дп!P1, сл!P1, ч!P1 | existing_sample_specific_evidence |
| `clay` | 109 | 38 functions | Данные!E150, Данные!E151, Данные!E152, Данные!E153, Данные!E154, Данные!E155, Данные!M1, Данные!N1, Данные!N210, Данные!N412, диссертации!P1, диссертации!Q1, диссертации!Q32, дп!M1, дп!N1, дп!N52, сл!M1, сл!N1, ч!M1, ч!N1 | existing_sample_specific_evidence |
| `silt` | 60 | 24 functions | Данные!O1, диссертации!R1, дп!O1, сл!O1, ч!O1 | existing_sample_specific_evidence |
| `bulk_density` | 43 | 22 functions | Данные!Q1, диссертации!T1, дп!Q1, сл!Q1, ч!Q1 | existing_sample_specific_evidence |
| `organic_matter` | 43 | 7 functions | Данные!E150, Данные!E151, Данные!E152, Данные!E153, Данные!E154, Данные!E155, Данные!E21, Данные!E22, Данные!E23, Данные!E24, Данные!E25, Данные!E26, Данные!E27, Данные!E28, Данные!E286, Данные!E287, Данные!E288, Данные!E289, Данные!E29, Данные!E290, Данные!E291, Данные!E30, Данные!E31, Данные!E32, Данные!E33, Данные!E337, Данные!E338, Данные!E339, Данные!E34, Данные!E340, Данные!E341, Данные!E342, Данные!E35, Данные!E36, Данные!E37, Данные!E38, Данные!E39, Данные!E41, Данные!E63, Данные!E64, Данные!E65, Данные!E66, Данные!E67, Данные!E81, Данные!E82, Данные!E83, Данные!E84, Данные!E85, Данные!E86, Данные!S1, диссертации!V1, дп!S1, сл!E34, сл!E35, сл!E36, сл!E37, сл!E38, сл!E39, сл!S1, ч!E23, ч!E24, ч!E25, ч!E26, ч!E27, ч!S1 | existing_sample_specific_evidence |
| `organic_carbon` | 13 | 8 functions | Данные!R1, диссертации!U1, дп!R1, сл!R1, ч!R1 | existing_sample_specific_evidence |
| `fine_sand` | 9 | 1 functions | none found | existing_sample_specific_evidence |
| `water_potential` | 8 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `electrical_conductivity` | 7 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `nitrogen` | 7 | 0 functions | диссертации!AE1 | candidate_requires_contract_review |
| `soil_organic_matter` | 7 | 7 functions | Данные!E150, Данные!E151, Данные!E152, Данные!E153, Данные!E154, Данные!E155, Данные!E21, Данные!E22, Данные!E23, Данные!E24, Данные!E25, Данные!E26, Данные!E27, Данные!E28, Данные!E286, Данные!E287, Данные!E288, Данные!E289, Данные!E29, Данные!E290, Данные!E291, Данные!E30, Данные!E31, Данные!E32, Данные!E33, Данные!E337, Данные!E338, Данные!E339, Данные!E34, Данные!E340, Данные!E341, Данные!E342, Данные!E35, Данные!E36, Данные!E37, Данные!E38, Данные!E39, Данные!E41, Данные!E63, Данные!E64, Данные!E65, Данные!E66, Данные!E67, Данные!E81, Данные!E82, Данные!E83, Данные!E84, Данные!E85, Данные!E86, Данные!S1, диссертации!V1, дп!S1, сл!E34, сл!E35, сл!E36, сл!E37, сл!E38, сл!E39, сл!S1, ч!E23, ч!E24, ч!E25, ч!E26, ч!E27, ч!S1 | existing_sample_specific_evidence |
| `stoniness` | 7 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `elevation` | 6 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `texture_class` | 6 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `depth` | 5 | 1 functions | Данные!J1, диссертации!M1, дп!AJ52, дп!J1, сл!J1, ч!J1 | existing_sample_specific_evidence |
| `ph` | 5 | 0 functions | Данные!D3, Данные!D4, Данные!D5, Данные!D6, Данные!E10, Данные!E11, Данные!E110, Данные!E111, Данные!E112, Данные!E114, Данные!E116, Данные!E12, Данные!E120, Данные!E122, Данные!E128, Данные!E129, Данные!E13, Данные!E130, Данные!E131, Данные!E132, Данные!E133, Данные!E135, Данные!E137, Данные!E139, Данные!E14, Данные!E141, Данные!E143, Данные!E147, Данные!E148, Данные!E15, Данные!E150, Данные!E151, Данные!E152, Данные!E153, Данные!E154, Данные!E155, Данные!E157, Данные!E158, Данные!E159, Данные!E16, Данные!E160, Данные!E161, Данные!E162, Данные!E163, Данные!E164, Данные!E165, Данные!E166, Данные!E167, Данные!E168, Данные!E169, Данные!E17, Данные!E170, Данные!E171, Данные!E172, Данные!E173, Данные!E174, Данные!E18, Данные!E189, Данные!E19, Данные!E190, Данные!E191, Данные!E192, Данные!E193, Данные!E195, Данные!E196, Данные!E197, Данные!E198, Данные!E199, Данные!E200, Данные!E201, Данные!E202, Данные!E203, Данные!E204, Данные!E206, Данные!E207, Данные!E208, Данные!E209, Данные!E225, Данные!E226, Данные!E228, Данные!E229, Данные!E230, Данные!E231, Данные!E232, Данные!E233, Данные!E234, Данные!E235, Данные!E236, Данные!E237, Данные!E239, Данные!E240, Данные!E241, Данные!E242, Данные!E243, Данные!E244, Данные!E245, Данные!E246, Данные!E247, Данные!E248, Данные!E249, Данные!E256, Данные!E258, Данные!E260, Данные!E262, Данные!E263, Данные!E264, Данные!E265, Данные!E267, Данные!E268, Данные!E269, Данные!E270, Данные!E272, Данные!E273, Данные!E274, Данные!E275, Данные!E276, Данные!E278, Данные!E279, Данные!E280, Данные!E281, Данные!E282, Данные!E283, Данные!E286, Данные!E287, Данные!E288, Данные!E289, Данные!E290, Данные!E291, Данные!E293, Данные!E294, Данные!E295, Данные!E296, Данные!E297, Данные!E298, Данные!E299, Данные!E300, Данные!E301, Данные!E302, Данные!E303, Данные!E304, Данные!E305, Данные!E306, Данные!E307, Данные!E308, Данные!E309, Данные!E310, Данные!E311, Данные!E312, Данные!E333, Данные!E334, Данные!E335, Данные!E337, Данные!E338, Данные!E339, Данные!E340, Данные!E341, Данные!E342, Данные!E357, Данные!E359, Данные!E361, Данные!E363, Данные!E365, Данные!E367, Данные!E369, Данные!E371, Данные!E373, Данные!E375, Данные!E377, Данные!E379, Данные!E381, Данные!E43, Данные!E44, Данные!E45, Данные!E453, Данные!E455, Данные!E50, Данные!E51, Данные!E52, Данные!E524, Данные!E526, Данные!E528, Данные!E53, Данные!E530, Данные!E532, Данные!E534, Данные!E536, Данные!E538, Данные!E54, Данные!E540, Данные!E542, Данные!E544, Данные!E56, Данные!E57, Данные!E58, Данные!E59, Данные!E68, Данные!E69, Данные!E70, Данные!E71, Данные!E72, Данные!E73, Данные!E74, Данные!E75, Данные!E8, Данные!E88, Данные!E89, Данные!E9, Данные!E90, Данные!E94, Данные!E95, Данные!E96, Данные!F10, Данные!F11, Данные!F12, Данные!F13, Данные!F14, Данные!F15, Данные!F16, Данные!F17, Данные!F18, Данные!F19, Данные!F272, Данные!F273, Данные!F274, Данные!F275, Данные!F276, Данные!F286, Данные!F287, Данные!F288, Данные!F289, Данные!F290, Данные!F291, Данные!F337, Данные!F338, Данные!F339, Данные!F340, Данные!F341, Данные!F342, Данные!F524, Данные!F526, Данные!F528, Данные!F530, Данные!F532, Данные!F534, Данные!F536, Данные!F538, Данные!F540, Данные!F542, Данные!F544, Данные!F546, Данные!F548, Данные!F550, Данные!F552, Данные!F554, Данные!F556, Данные!F68, Данные!F69, Данные!F70, Данные!F71, Данные!F72, Данные!F73, Данные!F74, Данные!F75, Данные!F8, Данные!F9, Данные!H111, Данные!T1, диссертации!D32, диссертации!D95, диссертации!F73, диссертации!F75, диссертации!W1, дп!E72, дп!E74, дп!E81, дп!E82, дп!E83, дп!E84, дп!F86, дп!F87, дп!F88, дп!F89, дп!F90, дп!T1, сл!D25, сл!D26, сл!D27, сл!D28, сл!E41, сл!E42, сл!E43, сл!T1, ч!E62, ч!E64, ч!E66, ч!E69, ч!F10, ч!F11, ч!F12, ч!F13, ч!F14, ч!F28, ч!F29, ч!F3, ч!F30, ч!F31, ч!F32, ч!F33, ч!F34, ч!F35, ч!F4, ч!F5, ч!F6, ч!F7, ч!F8, ч!F9, ч!H38, ч!T1 | candidate_requires_contract_review |
| `soil_organic_carbon` | 5 | 5 functions | Данные!R1, диссертации!U1, дп!R1, сл!R1, ч!R1 | existing_sample_specific_evidence |
| `theta_33` | 5 | 1 functions | none found | existing_sample_specific_evidence |
| `theta_s` | 5 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `cation_exchange_capacity` | 4 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `fine_fraction` | 4 | 4 functions | none found | existing_sample_specific_evidence |
| `mean_depth` | 4 | 2 functions | Данные!J1, диссертации!M1, дп!AJ52, дп!J1, сл!J1, ч!J1 | existing_sample_specific_evidence |
| `theta` | 4 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `coarse_sand` | 3 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `saturated_conductivity` | 3 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `structure` | 3 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `theta_1500` | 3 | 2 functions | none found | existing_sample_specific_evidence |
| `altitude` | 2 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `bulk_volume` | 2 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `carbon` | 2 | 2 functions | Данные!R1, диссертации!U1, дп!R1, сл!R1, ч!R1 | existing_sample_specific_evidence |
| `clay_content` | 2 | 0 functions | Данные!E150, Данные!E151, Данные!E152, Данные!E153, Данные!E154, Данные!E155, Данные!M1, Данные!N1, Данные!N210, Данные!N412, диссертации!P1, диссертации!Q1, диссертации!Q32, дп!M1, дп!N1, дп!N52, сл!M1, сл!N1, ч!M1, ч!N1 | candidate_requires_contract_review |
| `esp` | 2 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `median_sand_size` | 2 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `slope` | 2 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `soc` | 2 | 2 functions | Данные!R1, диссертации!U1, дп!R1, сл!R1, ч!R1 | existing_sample_specific_evidence |
| `soil_texture` | 2 | 2 functions | none found | existing_sample_specific_evidence |
| `water_01bar` | 2 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `air_entry_tension` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `alpha` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `alpha_vgm` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `coefficient_b` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `conductivity_lambda` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `conductivity_shape_parameter` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `density_factor` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `effective_porosity` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `emp` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `excm` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `exponent_n` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `fine_sand_fraction` | 1 | 1 functions | none found | existing_sample_specific_evidence |
| `geometric_mean_particle_size` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `geometric_standard_deviation` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `gmd` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `gravel_weight_fraction` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `k_s_vgm` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `matric_density` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `n` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `n_vgm` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `normal_density` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_1000_500` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_100_50` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_10_2` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_2000_1000` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_200_100` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_20_10` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_500_200` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_50_20` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `particle_density` | 1 | 0 functions | Данные!V1, диссертации!Y1, дп!V1, сл!V1, ч!V1 | candidate_requires_contract_review |
| `plant_available_water` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `porosity` | 1 | 1 functions | Данные!U1, Данные!Z421, диссертации!AK41, диссертации!X1, дп!U1, сл!U1, ч!U1 | existing_sample_specific_evidence |
| `precipitation` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `pressure_head_magnitude` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `soil_class` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `soil_group` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `tau_vgm` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `tension` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `theta_r` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `theta_r_vgm` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `theta_s_vgm` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |
| `total_porosity` | 1 | 0 functions | Данные!U1, Данные!Z421, диссертации!AK41, диссертации!X1, дп!U1, сл!U1, ч!U1 | candidate_requires_contract_review |
| `very_fine_sand` | 1 | 0 functions | none found | no_lexical_candidate; not_a_proof_of_absence |

Predictor impact in the frozen baseline (overlapping function sets):

| Predictor | Functions with a missing-input decision | Functions with a sole-input gap on some sample |
| --- | ---: | ---: |
| `sand` | 40 | 17 |
| `silt` | 29 | 10 |
| `clay` | 37 | 4 |
| `bulk_density` | 22 | 3 |
| `fine_fraction` | 4 | 3 |
| `organic_matter` | 7 | 2 |
| `soil_organic_matter` | 7 | 2 |
| `mean_depth` | 2 | 2 |
| `median_sand_size` | 2 | 2 |
| `soil_texture` | 2 | 2 |
| `altitude` | 2 | 1 |
| `slope` | 2 | 1 |
| `bulk_volume` | 1 | 1 |
| `clay_content` | 1 | 1 |
| `fine_sand_fraction` | 1 | 1 |
| `soil_class` | 1 | 1 |
| `organic_carbon` | 8 | 0 |
| `soil_organic_carbon` | 5 | 0 |
| `ph` | 2 | 0 |
| `theta_33` | 2 | 0 |
| `theta_s` | 2 | 0 |
| `cation_exchange_capacity` | 2 | 0 |
| `saturated_conductivity` | 2 | 0 |
| `theta_1500` | 2 | 0 |
| `carbon` | 2 | 0 |
| `soc` | 2 | 0 |
| `fine_sand` | 1 | 0 |
| `depth` | 1 | 0 |
| `esp` | 1 | 0 |
| `alpha` | 1 | 0 |
| `alpha_vgm` | 1 | 0 |
| `conductivity_shape_parameter` | 1 | 0 |
| `density_factor` | 1 | 0 |
| `emp` | 1 | 0 |
| `excm` | 1 | 0 |
| `geometric_mean_particle_size` | 1 | 0 |
| `geometric_standard_deviation` | 1 | 0 |
| `gravel_weight_fraction` | 1 | 0 |
| `k_s_vgm` | 1 | 0 |
| `matric_density` | 1 | 0 |
| `n` | 1 | 0 |
| `n_vgm` | 1 | 0 |
| `normal_density` | 1 | 0 |
| `particle_1000_500` | 1 | 0 |
| `particle_100_50` | 1 | 0 |
| `particle_10_2` | 1 | 0 |
| `particle_2000_1000` | 1 | 0 |
| `particle_200_100` | 1 | 0 |
| `particle_20_10` | 1 | 0 |
| `particle_500_200` | 1 | 0 |
| `particle_50_20` | 1 | 0 |
| `particle_density` | 1 | 0 |
| `plant_available_water` | 1 | 0 |
| `porosity` | 1 | 0 |
| `precipitation` | 1 | 0 |
| `tau_vgm` | 1 | 0 |
| `theta_r` | 1 | 0 |
| `theta_r_vgm` | 1 | 0 |
| `theta_s_vgm` | 1 | 0 |

## Deterministic predictor routes

| Transformation | Disposition |
| --- | --- |
| Depth interval → midpoint | Existing approximate policy; source depth definition still required |
| OC ↔ OM | Existing exploratory factor; empirical relation, not a physical identity |
| Bulk + particle density → porosity | Generic identity 1 − rho_b/rho_s; candidate particle-density binding unconfirmed |
| PSD → USDA class | Existing policy; preserve particle bounds, closure and inherited evidence |
| Complementary PSD fraction | Require common material basis and valid measured closure; never fill incompatible cutoffs |
| WRC → pressure-defined water predictor | General unit mapping; same sample, in-range only, conditional validation |

## Original eight pressure blockers

Each row aggregates the private per-sample support and gap audit. An in-range target does not remove missing predictors. No sample is required to represent the entire source.

| Function | Requested kPa | Observed min–max kPa | In-range samples | Minimum outside gap kPa |
| --- | ---: | --- | ---: | ---: |
| `calc_ptf_lal1979_group_i_water_0bar_from_clay` | 0 | 0–9.80665e+06 | 18 | 0.00980665 |
| `calc_ptf_lal1979_group_i_water_0bar_from_sand` | 0 | 0–9.80665e+06 | 18 | 0.00980665 |
| `calc_ptf_lal1979_group_ii_water_0bar_from_clay` | 0 | 0–9.80665e+06 | 18 | 0.00980665 |
| `calc_ptf_lal1979_group_ii_water_0bar_from_sand` | 0 | 0–9.80665e+06 | 18 | 0.00980665 |
| `calc_ptf_li2007` | 0 | 0–9.80665e+06 | 18 | 0.00980665 |
| `calc_ptf_wang2022_h2` | 0 | 0–9.80665e+06 | 18 | 0.00980665 |
| `calc_ptf_wang2022_h3` | 0 | 0–9.80665e+06 | 18 | 0.00980665 |
| `calc_ptf_weynants2009` | 0 | 0–9.80665e+06 | 18 | 0.00980665 |
| `calc_ptf_weynants2009` | 10 | 0–9.80665e+06 | 108 | 36425.2 |
| `calc_ptf_weynants2009` | 33 | 0–9.80665e+06 | 108 | 36402.2 |
| `calc_ptf_weynants2009` | 100 | 0–9.80665e+06 | 105 | 50.8503 |
| `calc_ptf_weynants2009` | 500 | 0–9.80665e+06 | 105 | 450.85 |
| `calc_ptf_weynants2009` | 1500 | 0–9.80665e+06 | 71 | 124.629 |

## Public wrappers with another specification status

All 44 wrappers remain in the denominator and are evaluated without a status exclusion. Their source specifications contain implementation variables and verification cases; the public wrappers dispatch to native ufuncs. They are callable PTFs. A compound output is identified separately from a convenience wrapper. Ready-for-implementation status is preserved and is not promoted to validated semantics.

| Wrapper assessment | Functions |
| --- | ---: |
| Callable PTF with status other than implemented | 44 |
| Benchmarkable on at least one sample | 17 |
| Compound target | 1 |
| Incomplete implementation contract | 0 |

## All function decisions

Output descriptions are copied from registered specifications. Multiple families and unresolved semantics are retained; a callable wrapper is not scientific validation.

| Function | Specification status / wrapper | Output semantics | Decision | Samples after mapping |
| --- | --- | --- | --- | ---: |
| `calc_ptf_ahuja1984` | implemented / genuine_callable_ptf | k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_aimrun2009` | implemented / genuine_callable_ptf | k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_bai2022` | implemented / genuine_callable_ptf | alpha: Inverse pressure-scale parameter of the van Genuchten model.; n: Pore-size distribution parameter of the van Genuchten model.; theta_r: Residual volumetric soil water content.; theta_s: Saturated volumetric soil water content.; k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_bai2022_bulk_density` | implemented / genuine_callable_ptf | bulk_density: Dry bulk density predicted by Equation 7. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_beniaich2023_mlr1` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 16 |
| `calc_ptf_beniaich2023_mlr2` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 16 |
| `calc_ptf_beniaich2023_mlr3` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 16 |
| `calc_ptf_beniaich2023_mlr4` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 27 |
| `calc_ptf_beniaich2023_mlr5` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 16 |
| `calc_ptf_beniaich2023_slr1` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 28 |
| `calc_ptf_beniaich2023_slr2` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 16 |
| `calc_ptf_beniaich2023_slr3` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 16 |
| `calc_ptf_beniaich2023_slr4` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 16 |
| `calc_ptf_beniaich2023_slr5` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 16 |
| `calc_ptf_beniaich2023_slr6` | implemented / genuine_callable_ptf | water_saturation: Gravimetric water content at saturation.; water_field_capacity: Gravimetric water content at -33 kPa.; water_wilting_point: Gravimetric water content at -1,500 kPa. | current_executable | 51 |
| `calc_ptf_bruand1994_bulk_volume_available_water` | implemented / genuine_callable_ptf | available_water_capacity: Difference between calculated volumetric water contents at -30 and -1500 kPa matric potential. | predictor_or_support_unresolved | 0 |
| `calc_ptf_bruand1994_bulk_volume_water_retention` | implemented / genuine_callable_ptf | water_content_30_kpa: Calculated water volume per dry-soil mass at -30 kPa matric potential.; water_content_1500_kpa: Calculated water volume per dry-soil mass at -1500 kPa matric potential. | predictor_or_support_unresolved | 0 |
| `calc_ptf_bruand1994_clay_available_water` | implemented / genuine_callable_ptf | available_water_capacity: Difference between calculated volumetric water contents at -30 and -1500 kPa matric potential. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_bruand1994_clay_water_retention` | implemented / genuine_callable_ptf | water_content_30_kpa: Calculated water volume per dry-soil mass at -30 kPa matric potential.; water_content_1500_kpa: Calculated water volume per dry-soil mass at -1500 kPa matric potential. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_chakraborty2011_eq1` | implemented / genuine_callable_ptf | water_content_33: Gravimetric water content at -33 kPa matric potential.; water_content_100: Gravimetric water content at -100 kPa matric potential.; water_content_500: Gravimetric water content at -500 kPa matric potential.; water_content_1500: Gravimetric water content at -1500 kPa matric potential. | current_executable | 16 |
| `calc_ptf_chakraborty2011_eq2` | implemented / genuine_callable_ptf | water_content_33: Gravimetric water content at -33 kPa matric potential.; water_content_100: Gravimetric water content at -100 kPa matric potential.; water_content_500: Gravimetric water content at -500 kPa matric potential.; water_content_1500: Gravimetric water content at -1500 kPa matric potential. | current_executable | 5 |
| `calc_ptf_chakraborty2011_eq3` | implemented / genuine_callable_ptf | water_content_33: Gravimetric water content at -33 kPa matric potential.; water_content_100: Gravimetric water content at -100 kPa matric potential.; water_content_500: Gravimetric water content at -500 kPa matric potential.; water_content_1500: Gravimetric water content at -1500 kPa matric potential. | current_executable | 5 |
| `calc_ptf_chakraborty2011_eq4` | implemented / genuine_callable_ptf | water_content_33: Gravimetric water content at -33 kPa matric potential.; water_content_100: Gravimetric water content at -100 kPa matric potential.; water_content_500: Gravimetric water content at -500 kPa matric potential.; water_content_1500: Gravimetric water content at -1500 kPa matric potential. | current_executable | 16 |
| `calc_ptf_chakraborty2011_eq5` | implemented / genuine_callable_ptf | water_content_33: Gravimetric water content at -33 kPa matric potential.; water_content_100: Gravimetric water content at -100 kPa matric potential.; water_content_500: Gravimetric water content at -500 kPa matric potential.; water_content_1500: Gravimetric water content at -1500 kPa matric potential. | current_executable | 5 |
| `calc_ptf_chakraborty2011_eq6` | implemented / genuine_callable_ptf | water_content_33: Gravimetric water content at -33 kPa matric potential.; water_content_100: Gravimetric water content at -100 kPa matric potential.; water_content_500: Gravimetric water content at -500 kPa matric potential.; water_content_1500: Gravimetric water content at -1500 kPa matric potential. | current_executable | 1 |
| `calc_ptf_clapp1978` | implemented / genuine_callable_ptf | b: Mean exponent of the moisture-characteristic power curve.; saturation_suction: Representative saturation suction, calculated as the antilog of the mean logarithm of fitted saturation-suction values.; wetting_front_suction: Representative Green-Ampt wetting-front suction.; saturated_water_content: Mean saturated volumetric water content, taken as total porosity.; saturated_hydraulic_conductivity: Mean saturated hydraulic conductivity reported by Li et al. (1976).; sorptivity: Representative sorptivity for the paper's single initial moisture deficit corresponding to 500-cm initial suction. | current_executable | 6 |
| `calc_ptf_cosby1984_univariate` | implemented / genuine_callable_ptf | mean_b: Mean slope of the moisture characteristic.; mean_log_psi_s: Mean log saturation matric potential; the underlying potential is expressed in cm H2O.; mean_log_k_sat: Mean log saturated hydraulic conductivity; the underlying conductivity is expressed in inches per hour.; mean_theta_s: Mean saturated water content.; sd_b: Standard deviation of b.; sd_log_k_sat: Standard deviation of log saturated hydraulic conductivity.; sd_theta_s: Standard deviation of saturated water content. | current_executable | 6 |
| `calc_ptf_dharumarajan2019_infiltration` | implemented / genuine_callable_ptf | infiltration_rate: Soil infiltration rate measured with a double-ring infiltrometer. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_dharumarajan2019_nkp` | implemented / genuine_callable_ptf | field_capacity: Soil water content at -33 kPa matric potential.; permanent_wilting_point: Soil water content at -1500 kPa matric potential. | physically_incompatible_or_unresolved | 0 |
| `calc_ptf_dharumarajan2019_nkp_clay` | implemented / genuine_callable_ptf | field_capacity: Soil water content at -33 kPa matric potential.; permanent_wilting_point: Soil water content at -1500 kPa matric potential. | physically_incompatible_or_unresolved | 0 |
| `calc_ptf_dharumarajan2019_skp` | implemented / genuine_callable_ptf | field_capacity: Soil water content at -33 kPa matric potential.; permanent_wilting_point: Soil water content at -1500 kPa matric potential. | physically_incompatible_or_unresolved | 0 |
| `calc_ptf_dharumarajan2019_skp_clay` | implemented / genuine_callable_ptf | field_capacity: Soil water content at -33 kPa matric potential.; permanent_wilting_point: Soil water content at -1500 kPa matric potential. | physically_incompatible_or_unresolved | 0 |
| `calc_ptf_dijkerman1988` | ready-for-implementation / genuine_callable_ptf | water_content_15_bar: Gravimetric moisture content at 15 bar, in weight percentage.; water_content_one_third_bar: Gravimetric moisture content at one-third bar, in weight percentage. | unlockable_after_generic_semantic_mapping | 13 |
| `calc_ptf_dijkerman1988_available_water` | ready-for-implementation / genuine_callable_ptf | available_water: Difference in gravimetric moisture contents, in weight percentage points. | unlockable_after_generic_semantic_mapping | 13 |
| `calc_ptf_ferrerjulia2004_calcaric_fluvisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_calcaric_fluvisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_calcaric_regosol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_calcaric_regosol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_calcic_cambisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_calcic_cambisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_calcic_luvisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_calcic_luvisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_campbell_shiozawa` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_chromic_luvisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_chromic_luvisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_cosby` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_dane_puckett` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_dystric_cambisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_dystric_cambisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_dystric_regosol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_dystric_regosol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_eutric_cambisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_eutric_cambisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_eutric_regosol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_eutric_regosol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_general_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_general_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_gleyic_cambisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_gleyic_cambisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_gleyic_luvisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_gleyic_luvisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_gleyic_solonchak_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_gleyic_solonchak_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_humic_acrisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_humic_acrisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_humic_cambisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_humic_cambisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_orthic_luvisol_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_orthic_luvisol_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_puckett` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_ranker_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_ranker_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_rendzina_sand` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_rendzina_texture_organic_matter` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ferrerjulia2004_saxton` | implemented / genuine_callable_ptf | k_sat: Estimated saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_gunarathna2019_vwc10_set1` | implemented / genuine_callable_ptf | theta_10: Volumetric water content at -10 kPa matric potential. | current_executable | 6 |
| `calc_ptf_gunarathna2019_vwc10_set2` | implemented / genuine_callable_ptf | theta_10: Volumetric water content at -10 kPa matric potential. | predictor_or_support_unresolved | 0 |
| `calc_ptf_gunarathna2019_vwc10_set3` | implemented / genuine_callable_ptf | theta_10: Volumetric water content at -10 kPa matric potential. | predictor_or_support_unresolved | 0 |
| `calc_ptf_gunarathna2019_vwc10_set4` | implemented / genuine_callable_ptf | theta_10: Volumetric water content at -10 kPa matric potential. | predictor_or_support_unresolved | 0 |
| `calc_ptf_gunarathna2019_vwc1500_set1` | implemented / genuine_callable_ptf | theta_1500: Volumetric water content at -1500 kPa matric potential. | current_executable | 6 |
| `calc_ptf_gunarathna2019_vwc1500_set3` | implemented / genuine_callable_ptf | theta_1500: Volumetric water content at -1500 kPa matric potential. | current_executable | 6 |
| `calc_ptf_gunarathna2019_vwc1500_set4` | implemented / genuine_callable_ptf | theta_1500: Volumetric water content at -1500 kPa matric potential. | current_executable | 6 |
| `calc_ptf_gunarathna2019_vwc33_set1` | implemented / genuine_callable_ptf | theta_33: Volumetric water content at -33 kPa matric potential. | current_executable | 6 |
| `calc_ptf_gunarathna2019_vwc33_set2` | implemented / genuine_callable_ptf | theta_33: Volumetric water content at -33 kPa matric potential. | predictor_or_support_unresolved | 0 |
| `calc_ptf_gunarathna2019_vwc33_set3` | implemented / genuine_callable_ptf | theta_33: Volumetric water content at -33 kPa matric potential. | predictor_or_support_unresolved | 0 |
| `calc_ptf_gunarathna2019_vwc33_set4` | implemented / genuine_callable_ptf | theta_33: Volumetric water content at -33 kPa matric potential. | predictor_or_support_unresolved | 0 |
| `calc_ptf_gupta1979` | implemented / genuine_callable_ptf | theta_40_cm: Volumetric water content at -0.04 bar matric potential.; theta_70_cm: Volumetric water content at -0.07 bar matric potential.; theta_100_cm: Volumetric water content at -0.10 bar matric potential.; theta_200_cm: Volumetric water content at -0.20 bar matric potential.; theta_330_cm: Volumetric water content at -0.33 bar matric potential.; theta_600_cm: Volumetric water content at -0.60 bar matric potential.; theta_1000_cm: Volumetric water content at -1.0 bar matric potential.; theta_2000_cm: Volumetric water content at -2.0 bar matric potential.; theta_4000_cm: Volumetric water content at -4.0 bar matric potential.; theta_7000_cm: Volumetric water content at -7.0 bar matric potential.; theta_10000_cm: Volumetric water content at -10.0 bar matric potential.; theta_15000_cm: Volumetric water content at -15.0 bar matric potential. | unlockable_after_generic_semantic_mapping | 6 |
| `calc_ptf_hodnett2002` | implemented / genuine_callable_ptf | alpha: Shape parameter of the van Genuchten water-retention model.; n: Shape parameter controlling water-retention curve steepness.; theta_s: Saturated volumetric soil water content.; theta_r: Residual volumetric soil water content. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_jabro1992` | ready-for-implementation / genuine_callable_ptf | k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_kalumba2021_mlr_ksat` | implemented / genuine_callable_ptf | saturated_hydraulic_conductivity: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_kalumba2021_mlr_pf00` | implemented / genuine_callable_ptf | water_content_pf00: Volumetric water content at pF 0.0. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_kalumba2021_mlr_pf10` | implemented / genuine_callable_ptf | water_content_pf10: Volumetric water content at pF 1.0. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_kalumba2021_mlr_pf20` | implemented / genuine_callable_ptf | water_content_pf20: Volumetric water content at pF 2.0. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_kalumba2021_mlr_pf28` | implemented / genuine_callable_ptf | water_content_pf28: Volumetric water content at pF 2.8. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_kalumba2021_mlr_pf34` | implemented / genuine_callable_ptf | water_content_pf34: Volumetric water content at pF 3.4. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_kalumba2021_mlr_pf42` | implemented / genuine_callable_ptf | water_content_pf42: Volumetric water content at pF 4.2. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_lal1979_group_i_lower_plastic_limit_from_clay` | ready-for-implementation / genuine_callable_ptf | lower_plastic_limit: Lower plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_lower_plastic_limit_from_organic_carbon` | ready-for-implementation / genuine_callable_ptf | lower_plastic_limit: Lower plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_lower_plastic_limit_from_sand` | ready-for-implementation / genuine_callable_ptf | lower_plastic_limit: Lower plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_moisture_equivalent_from_clay` | ready-for-implementation / genuine_callable_ptf | moisture_equivalent: Gravimetric moisture equivalent measured at 1000 times gravity expressed per unit dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_moisture_equivalent_from_sand` | ready-for-implementation / genuine_callable_ptf | moisture_equivalent: Gravimetric moisture equivalent measured at 1000 times gravity expressed per unit dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_plasticity_index_from_clay` | ready-for-implementation / genuine_callable_ptf | plasticity_index: Plasticity index (upper minus lower plastic limit) expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_plasticity_index_from_organic_carbon` | ready-for-implementation / genuine_callable_ptf | plasticity_index: Plasticity index (upper minus lower plastic limit) expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_plasticity_index_from_sand` | ready-for-implementation / genuine_callable_ptf | plasticity_index: Plasticity index (upper minus lower plastic limit) expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_upper_plastic_limit_from_clay` | ready-for-implementation / genuine_callable_ptf | upper_plastic_limit: Upper plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_upper_plastic_limit_from_organic_carbon` | ready-for-implementation / genuine_callable_ptf | upper_plastic_limit: Upper plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_i_water_01bar_from_clay` | ready-for-implementation / genuine_callable_ptf | water_01bar: Gravimetric moisture retention at 0.1 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 28 |
| `calc_ptf_lal1979_group_i_water_01bar_from_sand` | ready-for-implementation / genuine_callable_ptf | water_01bar: Gravimetric moisture retention at 0.1 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 16 |
| `calc_ptf_lal1979_group_i_water_03bar_from_clay` | ready-for-implementation / genuine_callable_ptf | water_03bar: Gravimetric moisture retention at 0.3 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 28 |
| `calc_ptf_lal1979_group_i_water_03bar_from_sand` | ready-for-implementation / genuine_callable_ptf | water_03bar: Gravimetric moisture retention at 0.3 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 16 |
| `calc_ptf_lal1979_group_i_water_0bar_from_clay` | ready-for-implementation / genuine_callable_ptf | water_0bar: Gravimetric moisture retention at saturation expressed per unit dry soil mass. | predictor_or_support_unresolved | 0 |
| `calc_ptf_lal1979_group_i_water_0bar_from_sand` | ready-for-implementation / genuine_callable_ptf | water_0bar: Gravimetric moisture retention at saturation expressed per unit dry soil mass. | predictor_or_support_unresolved | 0 |
| `calc_ptf_lal1979_group_i_water_15bar_from_clay` | ready-for-implementation / genuine_callable_ptf | water_15bar: Gravimetric moisture retention at 15 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 28 |
| `calc_ptf_lal1979_group_i_water_15bar_from_sand` | ready-for-implementation / genuine_callable_ptf | water_15bar: Gravimetric moisture retention at 15 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 16 |
| `calc_ptf_lal1979_group_i_water_15bar_from_silt` | ready-for-implementation / genuine_callable_ptf | water_15bar: Gravimetric moisture retention at 15 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 16 |
| `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_clay` | ready-for-implementation / genuine_callable_ptf | lower_plastic_limit: Lower plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_sand` | ready-for-implementation / genuine_callable_ptf | lower_plastic_limit: Lower plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_lower_plastic_limit_from_silt` | ready-for-implementation / genuine_callable_ptf | lower_plastic_limit: Lower plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_moisture_equivalent_from_clay` | ready-for-implementation / genuine_callable_ptf | moisture_equivalent: Gravimetric moisture equivalent measured at 1000 times gravity expressed per unit dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_moisture_equivalent_from_sand` | ready-for-implementation / genuine_callable_ptf | moisture_equivalent: Gravimetric moisture equivalent measured at 1000 times gravity expressed per unit dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_moisture_equivalent_from_silt` | ready-for-implementation / genuine_callable_ptf | moisture_equivalent: Gravimetric moisture equivalent measured at 1000 times gravity expressed per unit dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_plasticity_index_from_organic_carbon` | ready-for-implementation / genuine_callable_ptf | plasticity_index: Plasticity index (upper minus lower plastic limit) expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_plasticity_index_from_silt` | ready-for-implementation / genuine_callable_ptf | plasticity_index: Plasticity index (upper minus lower plastic limit) expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_clay` | ready-for-implementation / genuine_callable_ptf | upper_plastic_limit: Upper plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_organic_carbon` | ready-for-implementation / genuine_callable_ptf | upper_plastic_limit: Upper plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_sand` | ready-for-implementation / genuine_callable_ptf | upper_plastic_limit: Upper plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_upper_plastic_limit_from_silt` | ready-for-implementation / genuine_callable_ptf | upper_plastic_limit: Upper plastic limit expressed as percentage of oven-dry soil mass. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_lal1979_group_ii_water_01bar_from_clay` | ready-for-implementation / genuine_callable_ptf | water_01bar: Gravimetric moisture retention at 0.1 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 28 |
| `calc_ptf_lal1979_group_ii_water_01bar_from_sand` | ready-for-implementation / genuine_callable_ptf | water_01bar: Gravimetric moisture retention at 0.1 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 16 |
| `calc_ptf_lal1979_group_ii_water_03bar_from_clay` | ready-for-implementation / genuine_callable_ptf | water_03bar: Gravimetric moisture retention at 0.3 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 28 |
| `calc_ptf_lal1979_group_ii_water_03bar_from_sand` | ready-for-implementation / genuine_callable_ptf | water_03bar: Gravimetric moisture retention at 0.3 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 16 |
| `calc_ptf_lal1979_group_ii_water_03bar_from_water_01bar` | ready-for-implementation / genuine_callable_ptf | water_03bar: Gravimetric moisture retention at 0.3 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 75 |
| `calc_ptf_lal1979_group_ii_water_0bar_from_clay` | ready-for-implementation / genuine_callable_ptf | water_0bar: Gravimetric moisture retention at saturation expressed per unit dry soil mass. | predictor_or_support_unresolved | 0 |
| `calc_ptf_lal1979_group_ii_water_0bar_from_sand` | ready-for-implementation / genuine_callable_ptf | water_0bar: Gravimetric moisture retention at saturation expressed per unit dry soil mass. | predictor_or_support_unresolved | 0 |
| `calc_ptf_lal1979_group_ii_water_15bar_from_clay` | ready-for-implementation / genuine_callable_ptf | water_15bar: Gravimetric moisture retention at 15 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 28 |
| `calc_ptf_lal1979_group_ii_water_15bar_from_sand` | ready-for-implementation / genuine_callable_ptf | water_15bar: Gravimetric moisture retention at 15 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 16 |
| `calc_ptf_lal1979_group_ii_water_15bar_from_water_01bar` | ready-for-implementation / genuine_callable_ptf | water_15bar: Gravimetric moisture retention at 15 bar suction expressed per unit dry soil mass. | unlockable_after_generic_semantic_mapping | 50 |
| `calc_ptf_li2007` | implemented / genuine_callable_ptf | theta_s: Saturated water content.; a_vg: Van Genuchten alpha parameter, inversely related to air-entry suction.; n_vg: Van Genuchten n parameter that characterizes pore-size distribution.; k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_mayr1999` | implemented / genuine_callable_ptf | a_hc: Hutson-Cass fitting parameter with pressure-head dimensions.; b_hc: Hutson-Cass fitting parameter controlling retention-curve shape.; theta_s: Volumetric soil water content at saturation. | current_executable | 6 |
| `calc_ptf_myeni2021_fc` | implemented / genuine_callable_ptf | fc: Gravimetric soil moisture content at field capacity (-33 kPa). | current_executable | 16 |
| `calc_ptf_myeni2021_pwp` | implemented / genuine_callable_ptf | pwp: Gravimetric soil moisture content at permanent wilting point (-1500 kPa). | current_executable | 16 |
| `calc_ptf_oosterveld1980_available_water` | implemented / genuine_callable_ptf | available_moisture: Predicted field-capacity moisture minus predicted wilting-point moisture, in percentage points by weight. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_oosterveld1980_field_capacity` | implemented / genuine_callable_ptf | field_capacity_moisture: Predicted soil-moisture content at field capacity in percent by weight. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_oosterveld1980_field_capacity_tension` | implemented / genuine_callable_ptf | field_capacity_tension: Predicted tension corresponding to cylinder-method field capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_oosterveld1980_retention` | implemented / genuine_callable_ptf | moisture_content: Predicted soil-moisture content in percent by weight. | current_executable | 10 |
| `calc_ptf_oosterveld1980_wilting_point` | implemented / genuine_callable_ptf | wilting_point_moisture: Predicted soil-moisture content at 1500 kPa in percent by weight. | current_executable | 10 |
| `calc_ptf_ottoni2019_wm330` | implemented / genuine_callable_ptf | k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ottoni2019_wmssc` | implemented / genuine_callable_ptf | k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_ottoni2019_wmsscbd` | implemented / genuine_callable_ptf | k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_pidgeon1972_awc` | implemented / genuine_callable_ptf | available_water_capacity: Available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_awc_coarse_sand` | implemented / genuine_callable_ptf | available_water_capacity: Available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_awc_fine_sand` | implemented / genuine_callable_ptf | available_water_capacity: Available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_awc_sand_organic_matter` | implemented / genuine_callable_ptf | available_water_capacity: Available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_awc_very_fine_sand` | implemented / genuine_callable_ptf | available_water_capacity: Available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_eawc` | implemented / genuine_callable_ptf | extended_available_water_capacity: Extended available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter` | implemented / genuine_callable_ptf | extended_available_water_capacity: Extended available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter` | implemented / genuine_callable_ptf | extended_available_water_capacity: Extended available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_eawc_sand` | implemented / genuine_callable_ptf | extended_available_water_capacity: Extended available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_eawc_sand_organic_matter` | implemented / genuine_callable_ptf | extended_available_water_capacity: Extended available water capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_fc` | implemented / genuine_callable_ptf | field_capacity: Gravimetric field capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_fc_sand` | implemented / genuine_callable_ptf | field_capacity: Gravimetric field capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_fc_sand_organic_matter` | implemented / genuine_callable_ptf | field_capacity: Gravimetric field capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_fc_vol_sand_organic_matter` | implemented / genuine_callable_ptf | field_capacity: Volumetric field capacity. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_pwp` | implemented / genuine_callable_ptf | permanent_wilting_point: Permanent wilting point. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_pwp_sand` | implemented / genuine_callable_ptf | permanent_wilting_point: Permanent wilting point. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_pidgeon1972_pwp_sand_organic_matter` | implemented / genuine_callable_ptf | permanent_wilting_point: Permanent wilting point. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_puckett1985` | implemented / genuine_callable_ptf | theta_0: Volumetric water content at 0 kPa.; theta_1: Volumetric water content at -1 kPa.; theta_5: Volumetric water content at -5 kPa.; theta_10: Volumetric water content at -10 kPa.; theta_30: Volumetric water content at -30 kPa.; theta_60: Volumetric water content at -60 kPa.; theta_100: Volumetric water content at -100 kPa.; theta_500: Volumetric water content at -500 kPa.; theta_1000: Volumetric water content at -1000 kPa.; theta_1500: Volumetric water content at -1500 kPa.; k_sat: Saturated hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_rawls1982_full_wrc` | implemented / genuine_callable_ptf | theta_4: Volumetric water content at -4 kPa.; theta_7: Volumetric water content at -7 kPa.; theta_10: Volumetric water content at -10 kPa.; theta_20: Volumetric water content at -20 kPa.; theta_33: Input volumetric water content at -33 kPa.; theta_60: Volumetric water content at -60 kPa.; theta_100: Volumetric water content at -100 kPa.; theta_200: Volumetric water content at -200 kPa.; theta_400: Volumetric water content at -400 kPa.; theta_700: Volumetric water content at -700 kPa.; theta_1000: Volumetric water content at -1000 kPa.; theta_1500: Input volumetric water content at -1500 kPa. | current_executable | 6 |
| `calc_ptf_rawls1982_theta_1500` | implemented / genuine_callable_ptf | theta_1500: Volumetric soil water content at -1500 kPa. | current_executable | 17 |
| `calc_ptf_rawls1982_theta_33` | implemented / genuine_callable_ptf | theta_33: Volumetric soil water content at -33 kPa. | current_executable | 6 |
| `calc_ptf_rawls2003_soc_theta1500_gmdh` | implemented / genuine_callable_ptf | theta_1500: Volumetric soil water content at -1500 kPa. | current_executable | 6 |
| `calc_ptf_rawls2003_soc_theta1500_tree` | implemented / genuine_callable_ptf | theta_1500: Volumetric soil water content at -1500 kPa. | current_executable | 6 |
| `calc_ptf_rawls2003_soc_theta33_gmdh` | implemented / genuine_callable_ptf | theta_33: Volumetric soil water content at -33 kPa. | current_executable | 6 |
| `calc_ptf_rawls2003_soc_theta33_tree` | implemented / genuine_callable_ptf | theta_33: Volumetric soil water content at -33 kPa. | current_executable | 6 |
| `calc_ptf_saxton1986_calcptf_parameters` | implemented / genuine_callable_ptf | theta_r: Residual volumetric water content fixed to zero.; theta_s: Saturated volumetric water content represented by soil porosity.; alpha: Inverse Brooks-Corey air-entry pressure head.; conductivity_lambda: Brooks-Corey pore-size distribution index. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_saxton2006` | implemented / genuine_callable_ptf | theta_1500: Volumetric water content at 1500 kPa matric tension.; theta_33: Volumetric water content at 33 kPa matric tension.; theta_s: Saturated volumetric water content at normal density.; plant_available_water: Difference between the 33 and 1500 kPa water contents.; air_entry_tension: Air-entry or bubbling-pressure tension.; retention_a: Coefficient A of the dry-range moisture-tension curve.; retention_b: Exponent B of the dry-range moisture-tension curve.; conductivity_lambda: Inverse of retention exponent B.; saturated_conductivity: Saturated hydraulic conductivity of the matric soil.; normal_density: Normal dry bulk density assuming particle density 2.65 g/cm^3. | current_executable | 6 |
| `calc_ptf_saxton2006_conductivity` | implemented / genuine_callable_ptf | conductivity: Unsaturated hydraulic conductivity at the supplied water content. | genuinely_target_absent_in_audited_workbook | 0 |
| `calc_ptf_saxton2006_density` | implemented / genuine_callable_ptf | adjusted_density: Density after applying the density factor.; adjusted_theta_s: Saturated water content after the density adjustment.; adjusted_theta_33: Water content at 33 kPa after the density adjustment.; adjusted_theta_s_minus_33: Density-adjusted difference between saturation and 33 kPa. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_saxton2006_gravel` | implemented / genuine_callable_ptf | gravel_volume_fraction: Gravel volume fraction of the bulk soil.; bulk_density: Dry bulk density of matric soil plus gravel.; bulk_plant_available_water: Plant-available water on a bulk-soil volume basis.; bulk_saturated_conductivity: Saturated conductivity after the gravel reduction. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_saxton2006_salinity` | implemented / genuine_callable_ptf | saturated_osmotic_potential: Osmotic potential at saturation.; osmotic_potential: Osmotic potential at the supplied water content. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_saxton2006_tension_dry` | implemented / genuine_callable_ptf | tension: Matric tension at the supplied water content. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_saxton2006_tension_wet` | implemented / genuine_callable_ptf | tension: Matric tension at the supplied water content. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_tiwary2014_bsr` | implemented / genuine_callable_ptf | w_33: Gravimetric water content at 33 kPa.; w_100: Gravimetric water content at 100 kPa.; w_1500: Gravimetric water content at 1500 kPa.; k_sat: Saturated hydraulic conductivity converted from mm/h. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_tiwary2014_igp` | implemented / genuine_callable_ptf | k_sat: Saturated hydraulic conductivity converted from mm/h. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_tomasella1998` | implemented / genuine_callable_ptf | porosity: Total soil porosity expressed as a volume percentage.; theta_1: Volumetric water content at -1 kPa matric potential.; theta_3: Volumetric water content at -3 kPa matric potential.; theta_6: Volumetric water content at -6 kPa matric potential.; theta_10: Volumetric water content at -10 kPa matric potential.; theta_33: Volumetric water content at -33 kPa matric potential.; theta_100: Volumetric water content at -100 kPa matric potential.; theta_500: Volumetric water content at -500 kPa matric potential.; theta_1500: Volumetric water content at -1500 kPa matric potential. | current_executable | 6 |
| `calc_ptf_varallyai1982_chernozem_a` | implemented / genuine_callable_ptf | theta_0: Upper-asymptote water content parameter of equation (9).; m: Shape parameter of equation (9).; pf_star: Base-10 logarithm of the equation (9) suction-scale parameter psi_*, with suction expressed in centimetres of water. | current_executable | 18 |
| `calc_ptf_varallyai1982_chernozem_b` | implemented / genuine_callable_ptf | theta_0: Upper-asymptote water content parameter of equation (9).; m: Shape parameter of equation (9).; pf_star: Base-10 logarithm of the equation (9) suction-scale parameter psi_*, with suction expressed in centimetres of water. | current_executable | 18 |
| `calc_ptf_varallyai1982_chernozem_c` | implemented / genuine_callable_ptf | theta_0: Upper-asymptote water content parameter of equation (9).; m: Shape parameter of equation (9).; pf_star: Base-10 logarithm of the equation (9) suction-scale parameter psi_*, with suction expressed in centimetres of water. | current_executable | 18 |
| `calc_ptf_varallyai1982_meadow` | implemented / genuine_callable_ptf | theta_0: Upper-asymptote water content parameter of equation (9).; m: Shape parameter of equation (9).; pf_star: Base-10 logarithm of the equation (9) suction-scale parameter psi_*, with suction expressed in centimetres of water. | current_executable | 6 |
| `calc_ptf_vereecken1989` | implemented / genuine_callable_ptf | theta_r: Residual volumetric soil water content.; theta_s: Saturated volumetric soil water content.; alpha: Shape parameter of the van Genuchten moisture-retention model.; n: Shape parameter of the van Genuchten moisture-retention model. | current_executable | 6 |
| `calc_ptf_vereecken1989_detailed` | implemented / genuine_callable_ptf | theta_r: Residual volumetric soil water content.; theta_s: Saturated volumetric soil water content.; alpha: Shape parameter of the van Genuchten moisture-retention model.; n: Shape parameter of the van Genuchten moisture-retention model. | predictor_or_support_unresolved | 0 |
| `calc_ptf_wang2012` | implemented / genuine_callable_ptf | theta_s: Saturated volumetric water content normalized from the regression's volume-percent scale.; theta_fc: Volumetric water content at -33 kPa normalized from the regression's volume-percent scale.; k_sat: Saturated hydraulic conductivity converted from cm/day. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_wang2022_h2` | implemented / genuine_callable_ptf | alpha: van Genuchten inverse pressure-scale parameter.; n: van Genuchten pore-size distribution parameter.; m: van Genuchten retention-curve shape parameter.; theta_s: Saturated volumetric soil water content.; k_sat: Saturated hydraulic conductivity.; sl: Source-defined soil hydraulic slope parameter. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_wang2022_h3` | implemented / genuine_callable_ptf | alpha: van Genuchten inverse pressure-scale parameter.; n: van Genuchten pore-size distribution parameter.; m: van Genuchten retention-curve shape parameter.; theta_s: Saturated volumetric soil water content.; k_sat: Saturated hydraulic conductivity.; sl: Source-defined soil hydraulic slope parameter. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_weber2020` | implemented / genuine_callable_ptf | theta_snc_bw: Saturated water content of the Brunswick noncapillary pore space.; theta_sc_bw: Saturated water content of the Brunswick capillary pore space.; alpha_bw: Brunswick-VGM inverse pressure-head scale parameter.; n_bw: Brunswick-VGM pore-size distribution shape parameter.; tau_bw: Brunswick capillary hydraulic-conductivity shape parameter.; k_sc_bw: Saturated capillary hydraulic conductivity.; k_snc_bw: Saturated noncapillary hydraulic conductivity. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_weynants2009` | implemented / genuine_callable_ptf | theta_r: Residual volumetric soil water content fixed at zero.; theta_s: Saturated volumetric soil water content.; alpha: Inverse pressure-scale parameter of the van Genuchten model.; n: Pore-size distribution parameter of the van Genuchten model.; k0: Matrix matching-point hydraulic conductivity at zero pressure head.; tau: Mualem pore-connectivity and tortuosity parameter. | unlockable_after_generic_semantic_mapping | 6 |
| `calc_ptf_williams1992_function_1` | implemented / genuine_callable_ptf | water_content: Predicted volumetric water content at the supplied water-potential magnitude. | unlockable_after_generic_semantic_mapping | 6 |
| `calc_ptf_williams1992_function_2` | implemented / genuine_callable_ptf | water_content: Predicted volumetric water content at the supplied water-potential magnitude. | predictor_or_support_unresolved | 0 |
| `calc_ptf_williams1992_function_3` | implemented / genuine_callable_ptf | water_content: Predicted volumetric water content at the supplied water-potential magnitude. | predictor_or_support_unresolved | 0 |
| `calc_ptf_williams1992_function_4` | implemented / genuine_callable_ptf | water_content: Predicted volumetric water content at the supplied water-potential magnitude. | predictor_or_support_unresolved | 0 |
| `calc_ptf_williams1992_function_5` | implemented / genuine_callable_ptf | water_content: Predicted volumetric water content at the supplied water-potential magnitude. | predictor_or_support_unresolved | 0 |
| `calc_ptf_williams1992_function_6` | implemented / genuine_callable_ptf | water_content: Predicted volumetric water content at the supplied water-potential magnitude. | predictor_or_support_unresolved | 0 |
| `calc_ptf_williams1992_function_7` | implemented / genuine_callable_ptf | water_content: Predicted volumetric water content at the supplied water-potential magnitude. | predictor_or_support_unresolved | 0 |
| `calc_ptf_williams1992_function_8` | implemented / genuine_callable_ptf | water_content: Predicted volumetric water content at the supplied water-potential magnitude. | predictor_or_support_unresolved | 0 |
| `calc_ptf_williams1992_table5` | implemented / genuine_callable_ptf | b: Campbell moisture-characteristic exponent predicted with Function 7.; air_entry_head: Campbell nominal air-entry pressure-head magnitude predicted with Function 7. | target_contract_or_workbook_evidence_unresolved | 0 |
| `calc_ptf_wosten2001_class_parameters` | implemented / genuine_callable_ptf | theta_r: Residual volumetric water content.; theta_s: Saturated volumetric water content.; saturated_conductivity: Saturated hydraulic conductivity.; alpha: Inverse pressure-head scale of the van Genuchten model.; conductivity_shape_parameter: Mualem hydraulic-conductivity shape parameter.; n: van Genuchten pore-size distribution parameter. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_wosten2001_hydraulic` | implemented / genuine_callable_ptf | water_content: Volumetric water content at the supplied pressure-head magnitude.; conductivity: Hydraulic conductivity at the supplied pressure-head magnitude. | predictor_or_support_unresolved | 0 |
| `calc_ptf_wosten2001_loam_clay_table5` | implemented / genuine_callable_ptf | bulk_density: Dry bulk density predicted through the printed reciprocal-density regression.; theta_s: Saturated volumetric water content predicted by the continuous regression.; saturated_conductivity: Back-transformed saturated hydraulic conductivity.; alpha: Back-transformed van Genuchten inverse pressure-head scale.; conductivity_shape_parameter: Back-transformed Mualem hydraulic-conductivity shape parameter.; n: Back-transformed van Genuchten pore-size distribution parameter. | current_executable | 17 |
| `calc_ptf_wosten2001_sand_subsoil_table5` | implemented / genuine_callable_ptf | bulk_density: Dry bulk density predicted through the printed reciprocal-density regression.; theta_s: Saturated volumetric water content predicted by the continuous regression.; saturated_conductivity: Back-transformed saturated hydraulic conductivity.; alpha: Back-transformed van Genuchten inverse pressure-head scale.; conductivity_shape_parameter: Back-transformed Mualem hydraulic-conductivity shape parameter.; n: Back-transformed van Genuchten pore-size distribution parameter. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_wosten2001_sand_topsoil_table5` | implemented / genuine_callable_ptf | bulk_density: Dry bulk density predicted through the printed reciprocal-density regression.; theta_s: Saturated volumetric water content predicted by the continuous regression.; saturated_conductivity: Back-transformed saturated hydraulic conductivity.; alpha: Back-transformed van Genuchten inverse pressure-head scale.; conductivity_shape_parameter: Back-transformed Mualem hydraulic-conductivity shape parameter.; n: Back-transformed van Genuchten pore-size distribution parameter. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_zhao2016_m2_1` | implemented / genuine_callable_ptf | ks: Saturated hydraulic conductivity, measured by the constant-head method. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_zhao2016_m2_2` | implemented / genuine_callable_ptf | ks: Saturated hydraulic conductivity, measured by the constant-head method. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_zhao2016_m2_3` | implemented / genuine_callable_ptf | ks: Saturated hydraulic conductivity, measured by the constant-head method. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_zhao2016_m2_4` | implemented / genuine_callable_ptf | ks: Saturated hydraulic conductivity, measured by the constant-head method. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_zhao2016_m2_5` | implemented / genuine_callable_ptf | ks: Saturated hydraulic conductivity, measured by the constant-head method. | candidate_requiring_workbook_evidence | 0 |
| `calc_ptf_zhao2016_m2_6` | implemented / genuine_callable_ptf | ks: Saturated hydraulic conductivity, measured by the constant-head method. | candidate_requiring_workbook_evidence | 0 |

## Reproduction and limits

Use `python -m evaluation.experiments.meta_v3_3.deep_unlock --help` in the locked evaluation environment. Run discovery before the isolated campaign; use `--comparison` to attach the completed campaign. Full private outputs retain cell evidence, per-sample support, contracts, function decisions and SHA-256 inventory. No new workbook property is automatically bound. No operational FC/PWP, moisture equivalent, uncertain material basis, or unspecified model variant is inferred.
