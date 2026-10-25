# First additional real-data scoring: Cosby1984

Review date: 2026-10-25. Branch: `feat/ptfkit-eval`.

## Evidence and minimal contract

The initial checkpoint has 60,152 function/master-row/target records:
60,146 unresolved and six evaluated Clapp1978 combinations. The ranked blocker
table's largest category is missing public measurement contracts (49,028
records); these are outside a source-only repair. The largest source-review
ceiling is Shvarov 2008 (567 combinations across 21 rows), but existing reviewed
materials do not identify absolute retention measurements. Matching historical
difference vectors cannot authorize their release.

The minimal-contract audit exposes a cheaper path requiring no new measurement
contract, adapter, PSD boundary conversion or external publication retrieval:

1. `meta_v3_3.clapp-source-review.json` already authorizes six Panina horizons,
   their exact workbook identities, mineral material and published USDA classes.
   Its PDF and canonical-dataset checksums remain enforced by `build_subset`.
2. Panina Table 17 (printed p. 88) supplies these categorical classes. No class
   is inferred from Russian particle-size fractions or reused water values.
3. The existing `cosby1984_table2_class_midpoint_v1` derivation maps a reviewed
   class to the source's representative sand/silt/clay coordinates. These are
   explicitly `derived`, refer to the same categorical feature and retain its
   source lineage; they are not measured sample fractions.
4. The existing Cosby dry adapter and input-derivation verifier enforce the
   Table 2 coordinates and reject unsupported wet predictions. All 56 retained
   Panina points happen to lie in the supported dry branch. No wet plateau,
   saturation replacement or pressure interpolation is introduced.
5. Both candidates pass the normal execution, exact-coordinate cohort and
   checksum-verified artifact reader. Raw predictor-audit decisions remain
   unchanged; only executed, reviewed combinations are promoted in the matrix.

The all-function table is regenerated in `function-priorities.json` and the
benchmark report. It includes every one of the 146 implemented functions,
required predictor names, supported observed-row ceilings, primary blocker
and review-cost labels. Source priorities include the operational ratio of
conditional combinations to distinct unresolved blocker types. Neither ceiling
nor ratio is a compatibility claim or an evaluation metric.

## Result and limits

| Measure | Before | After | Gain |
| --- | ---: | ---: | ---: |
| Unresolved function/sample/target combinations | 60,146 | 60,140 | -6 |
| Eligible and evaluated combinations | 6 | 12 | +6 |
| Evaluated atomic PTF | 1 | 2 | +1 |
| Independent reviewed profiles | 1 | 1 | 0 |
| Independent reviewed sources | 1 | 1 | 0 |

The new PTF is `calc_ptf_cosby1984_univariate`: six horizons and 56 newly
scored function/observation points. Milestone A is reached. No new observations,
sources or profiles are claimed. Each sample/target counts once regardless of
the number of points or the repeated maximal/common reporting.

Maximal and exact common cohorts coincide for both candidates: six samples,
one source, one profile and 56 observations, with 100% coverage of this reviewed
subset. Pressure support spans 6.7845441909621895 to 257941.17602720842 kPa.
The latter is the source-normalized very-dry support, not a fitted endpoint.

| Candidate | Cohorts | RMSE | MAE | ME (prediction minus observation) |
| --- | --- | ---: | ---: | ---: |
| Clapp1978 | maximal and common | 0.0350360985 | 0.0305541769 | 0.0288498422 |
| Cosby1984 | maximal and common | 0.0227324258 | 0.0184300468 | 0.0055192141 |

Errors are volume fractions with equal total weight per sample. Per-candidate,
per-cohort wet/intermediate/dry diagnostics, exact pressure support and coverage
are retained in `native-class-comparison/summary.json`. Full input traces,
predictions, point decisions and exclusions remain in local run artifacts.

The following region results apply to both maximal and common cohorts. Each
region includes all six horizons. Descriptive region names use the fixed kPa
thresholds; they are independent of the adapter's sample-specific dry-branch
boundary.

| Candidate | Region (kPa) | Points | RMSE | MAE | ME |
| --- | --- | ---: | ---: | ---: | ---: |
| Clapp1978 | wet [0,10) | 6 | 0.0478061500 | 0.0405732325 | 0.0290863642 |
| Cosby1984 | wet [0,10) | 6 | 0.0379416991 | 0.0307439687 | -0.0004014273 |
| Clapp1978 | intermediate [10,1500) | 18 | 0.0357298200 | 0.0306342126 | 0.0289434041 |
| Cosby1984 | intermediate [10,1500) | 18 | 0.0219996261 | 0.0181287510 | -0.0052784752 |
| Clapp1978 | dry [1500,infinity) | 32 | 0.0331009101 | 0.0300726350 | 0.0300726350 |
| Cosby1984 | dry [1500,infinity) | 32 | 0.0196889143 | 0.0168685272 | 0.0141547656 |

Applicability is external evaluation of reviewed classes, not regional
validation. Population uncertainty and final atomic/ensemble selection remain
`insufficient_evidence`: a second candidate does not create independent groups.
The existing minimum-five-profile bootstrap gate is unchanged.

## Remaining work queue

Closed for these six combinations: missing Cosby input bindings and the
source-target protocol review, through the already reviewed categorical evidence
and registered derivation. Other functions remain independently unresolved.
No additional blocker was declared evidence-exhausted in this iteration.
The existing restricted-dissertation and missing-definition findings remain
negative evidence; this scoring gain does not resolve them.

After recalculation the largest global blocker remains missing public
measurement contracts. Among source-only reviews Shvarov 2008 remains first
with a conditional ceiling of 567 combinations (five distinct blocker types;
operational ratio 113.4). The minimum next action is obtaining the original
2008 absolute-retention table and matching exact sample identifiers, units and
pressure definitions before any canonical release. Existing publisher previews
and earlier difference curves are insufficient. If that original table cannot
be retrieved, record that access-specific result and advance to Gumatov 1991
(513 conditional combinations), without revisiting Nikulina/Medko/Fomin solely
because their vectors resemble existing observations.

The next low-input function opportunities also remain explicit: Wosten requires
the original Staring class rather than a USDA crosswalk; Saxton requires its
three predictor contracts; fixed-pressure functions require an exact observed
coordinate. Their missing evidence is not waived by the Cosby result.
