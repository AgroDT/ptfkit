# Exploratory sensitivity benchmark

This optional experiment implements the user's explicit decision to keep
unresolved units, material/mass basis and analytical comparability outside the
main benchmark while allowing separately labelled approximate scenarios.

```powershell
uv run --project targets/ptfkit-eval --no-sync python -B -m evaluation.experiments.meta_v3_3.exploratory --benchmark local/meta-benchmark-ensemble-final-20261025 --harmonized local/meta-harmonized-complete-20261025 --workbook local/meta_v3.3.xlsx --output local/meta-exploratory-new
```

The output directory must be new and outside both main benchmark directories.
Both main artifact inventories are verified before and after execution; the
supplied harmonized run must refer to the supplied strict run. The workbook
checksum must match the strict benchmark. Predictor identities are joined
through the existing audited master-sheet keys and checked against the literal
workbook source and sample identifier. No alias or profile identity is guessed.

## Registered assumptions

`exploratory-policies.json` is copied into the output before execution. It fixes
two scenarios independently of their errors:

- `reported_boundary_proxy` uses reported clay and silt as limiting USDA
  boundary proxies. A below-1-micrometre fraction does not become measured
  below-2-micrometre clay. Source-local below-2-micrometre overrides already
  present in the mapping are retained.
- `log_psd` reconstructs the below-2-micrometre cumulative fraction between
  adjacent available diameter boundaries in log10 diameter space. It uses the
  reported below-10-micrometre point when available, otherwise the below-50
  cumulative mass. It never extrapolates a missing lower tail. The result
  remains approximate because the underlying basis and method are assumed.

Both scenarios explicitly assume dry-mass fine-earth texture percentages and
analytical comparability. Complementary fractions require an assumed closed
partition. Complete texture triples may be normalized only within a registered
one-percentage-point closure residual; larger inconsistencies are rejected.
Original values, source cells, normalization and interpolation formulas remain
in the trace.

Column Q is interpreted as dry bulk density in g/cm3, R as OC mass percent and
S as an OM proxy. A missing OC/OM counterpart can use the registered factor
1.724; available reported values are retained. These material and analytical
assumptions are attached to each value, rather than presented as confirmed
measurement descriptors. Native joint constraints and declared computational
domains remain enforced.

Water reconstruction happens in the original experimental water basis. A
cross-basis target conversion then requires the same sample's column-Q density
and the explicitly assumed water density of 1 g/cm3. Missing density blocks the
combination; no average or other sample's density is substituted. Converted
targets retain the original experimental parent and cannot be called measured.
Impossible volumetric conversions are rejected instead of clipped. Target
material comparability is separately labelled approximate when required.

Cosby class coordinates remain restricted to the existing reviewed derivation.
An unavailable predictor, a missing public measurement contract, an unsupported
operational target or an unregistered target adapter is not invented through an
approximation. Main-eligible combinations are recorded as references and are
not counted as exploratory executions.

## Outputs and interpretation

The experiment emits policies, the complete 146-function matrix for each
scenario, prediction and provenance records, a count/error summary, a report
and a final artifact hash inventory. The summary contains no private
sample-level exports and can be retained under `evaluation/datasets`.
Sample-level matrices and predictions remain local.

The initial real-data run scored eleven additional functions from Beniaich
(2023) in each scenario. Main atomic coverage remains two functions. These
counts represent conditional approximate evaluations, not additional validated
PTFs or independent source publications. Many volume-target functions remain
blocked because the available mass-basis samples lack density.

Errors are stratified by physical target pool. Paired sensitivity compares the
same function on exactly shared source/sample/pressure coordinates, so a change
in coverage is not silently treated as a change in performance. The experiment
does not choose a winner, alter the main leaderboard, train a new ensemble or
produce a final recommendation. Every prediction has
`recommendation_eligible: false`; the summary has
`main_leaderboard_eligible: false` and `recommendation: null`.

Tests use independent published-regression arithmetic, a hand-computed PSD
boundary example, explicit mass/volume conversion arithmetic and a common-cohort
counterexample. They also reject missing-density execution, changed identities,
impossible volumetric targets and accidental exploratory duplication of
main-eligible cases.
