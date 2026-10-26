# E5 workbook semantic exploratory benchmark

The coverage-first exploratory ceiling is **129 of 216 public PTFs**, up from
64 at frozen E4. There are 107 functions with fresh E5 executions and 65 new
functions beyond E4. The other 22 functions retain their historical E4 results;
they are not presented as newly executed E5 functions.

| Tier | Executable PTF |
|---|---:|
| E0 | 2 |
| E1 | 2 |
| E2 | 2 |
| E3 | 4 |
| E4 | 64 |
| E5, cumulative | 129 |

All 216 functions receive explicit execution or blocker decisions. Automatic
conductivity discovery considers 70 functions, including linear and explicitly
defined logarithmic outputs, rather than the historical list of 55. Standard
deviations, infiltration, capillary/noncapillary components and matrix matching
conductivity do not become whole-soil Ksat observations.

The versioned protocol is `workbook_semantic_exploratory_v1`. Its implementation
is [workbook_semantic.py](workbook_semantic.py), and the aggregate checkpoint is
[meta_v3_3.workbook-semantic-summary.json](../../datasets/meta_v3_3.workbook-semantic-summary.json).
Strict and frozen E0-E4 artifacts remain unchanged. E5 is descriptive exploration,
with no strict/harmonized leaderboard or recommendation.

## Actual data consumption

The run produces 6,312 scored executions, 2,497 distinct function/sample pairs
and 239 distinct sample identities. Repeated predictions do not increase the
original-observation count:

- 409 original WRC observations contribute to targets;
- 370 original WRC observations contribute to predictors;
- their union contains 546 original WRC observations;
- all 36 numeric Ksat cells are used;
- 14 distinct AF/AG value cells contribute to plasticity targets;
- 50 reported porosity cells contribute to explicitly porosity-defined outputs.

There are 4,426 distinct target-lineage cells and 4,064 predictor-lineage cells.
Lineage cells can include pressure coordinates, repeated worksheet views and
conversion parents. These cell counts are not counts of independent physical
measurements, and predictor and target sets can overlap. Reconstructed targets
are not additional measured observations.

Continuous WRC outputs use every observed pressure for the same sample, alongside
the existing anchor coordinates. Scalar outputs retain their source-defined
pressures. Inverse WRC uses original water coordinates and explicit midpoints
between adjacent measured water contents, interpolates in log pressure and
rejects extrapolation, nonmonotone curves and nonunique plateau inverses.

## Coverage attribution

| Mechanism | New PTF using mechanism |
|---|---:|
| Permissive Ksat | 41 |
| Plasticity targets | 12 |
| pH | 0 |
| Particle density / porosity | 1 |
| FC/PWP/AWC approximations | 8 |
| Inverse WRC | 1 |
| PSD aliases | 62 |
| Other | 3 |

These groups overlap: a conductivity execution can require both a Ksat target
and a PSD approximation. The counts must not be summed. All 65 newly executable
functions and their successful evidence chains are retained in the checkpoint
and private predictions.

The other mechanisms include reciprocal-density bulk volume, explicit
water-volume/dry-mass conversion with the registered water density, and existing
direct-property adapters. The clod preparation contract for reciprocal-density
bulk volume remains approximate, with the measured density retained in provenance.

## Assumptions and hard boundaries

The three accepted Ksat blocks retain original values and literal workbook unit
labels. E5 normalizes m/day, cm/min and cm/day to m/s. For the middle block,
`original_unit_label = cm/smin`, `interpreted_unit = cm/min` and
`interpretation_status = workbook_semantic_assumption` are explicit. Measurement
method remains `unknown_or_not_recorded`. These rows form a separate cohort and
do not need retained WRC observations.

AF/AG are interpreted as lower/plastic and upper/liquid limits in mass percent.
Their difference is used only when both same-row values exist and upper is at
least lower. Source-table crosswalk and laboratory protocol are not blockers.
Lal1979 moisture equivalent remains a different quantity and is not replaced
with an arbitrary WRC coordinate.

E5 uses explicitly labeled row-level pH, particle density and porosity candidates.
The inventory contains 68 pH, 126 particle-density and 215 porosity row candidates
across retained workbook views; these are not independent-sample counts. pH
method is unknown and method-specific input mappings are marked approximate.
No complete scored pH-dependent combination exists: missing co-predictors or
same-sample targets remain necessary blockers. Numeric availability is not
claimed as a successful execution. Missing CEC and nitrogen are not invented.

Particle density is interpreted in g/cm3 from workbook context. Excel dates and
errors are rejected. Porosity values at or below one are interpreted as fractions,
and larger percentage-scale values are divided by 100. Density-derived porosity
requires two actual same-row densities and records `1 - bulk / particle`; there
is no assumed particle density of 2.65. Effective porosity stays separate.

The additional Saxton1986 comparison uses a reported porosity target because the
output explicitly represents soil porosity. It occupies a separate
`porosity_parameter` pool. Generic theta_s is not automatically equated with
porosity, and a density-derived target is not substituted into this pool merely
to reproduce the defining input formula.

PSD approximations retain the original cutoffs. They include observed detailed
bins, log-diameter interpolation inside bins, explicit mass closure, below-1 or
below-10 micrometre clay proxies, and the complement of measured physical clay
as an above-10 micrometre sand proxy. The latter is an explicit approximation to
above-50 micrometre sand, not an equivalent measurement. Original bin limits,
source cells, missing-bin derivations and requested intervals are preserved.
No new class-lattice mean predictors are generated; frozen E4 class imputations
remain historical E4 evidence.

Generic operational FC, PWP and AWC use theta33, theta1500 and their difference.
Explicit alternative pressure/protocol definitions keep their own contracts.
Mass/volume water-basis conversions require actual same-sample bulk density.
Matching source/sample keys and noncontradictory horizon/depth metadata are
required when associating a workbook row with canonical WRC observations.

## Physical definitions needing a decision

Dharumarajan2019 does not establish whether its output percentages are
gravimetric or volumetric. E5 does not guess between physically different water
bases. The checkpoint's `needs_user_decision` entries quantify both alternatives:

| Functions | Gravimetric interpretation | Volumetric interpretation |
|---|---:|---:|
| Northern and Southern clay-only variants | Potential +2 PTF total | Potential +2 PTF total |
| Northern and Southern CEC variants | +0 with current predictors | +0 with current predictors |

The alternatives overlap and are not scored or included in the 129-function
ceiling. Other functions continue regardless of these decisions.

## Reproduction and validation

From the repository root, using a new output directory:

```sh
mise run eval:workbook-semantic local/meta-deep-unlock-audited \
  local/meta-catalog-resource local/meta-catalog-harmonized \
  local/meta_v3.3.xlsx local/meta-workbook-semantic-v1
```

The equivalent direct command in the prepared environment is:

```sh
targets/ptfkit-eval/.venv/Scripts/python.exe -B \
  -m evaluation.experiments.meta_v3_3.workbook_semantic \
  --baseline local/meta-deep-unlock-audited \
  --benchmark local/meta-catalog-resource \
  --harmonized local/meta-catalog-harmonized \
  --workbook local/meta_v3.3.xlsx \
  --output local/meta-workbook-semantic-v1
```

Repeat with `--output local/meta-workbook-semantic-v1-replay` and compare
`artifact-hashes.json` byte for byte. Both runs verify frozen baseline,
strict-resource and harmonized inventories before and after execution.
Workbook, specification, manifest, implementation and native-extension hashes
are retained. Public aggregate data contain no sample identities or measurements.

Private outputs contain the full function/sample matrix, scored predictions,
normalized workbook properties, policy and literal header registry, sample-balanced
RMSE/MAE/bias by function/target kind/worksheet scenario, the full report and final
artifact inventory. Different target quantities and the porosity-parameter pool
are kept separate. Different model cohorts are not treated as a common leaderboard.

Validation includes the complete eval suite (1,072 tests at the broad checkpoint),
the expanded E5 regression suite (22 tests), component Ruff/format/ty checks and
standalone experiment Ruff/format checks. Regression tests protect SI conversion,
same-sample identity, source-cell lineage, original PSD cutoffs, density ratios,
WRC support, explicit pressure retention, original-observation deduplication and
separation of physically different targets.
