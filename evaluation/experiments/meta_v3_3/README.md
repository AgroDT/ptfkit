# meta_v3.3 workbook benchmark

This experiment reconciles the existing source-reviewed normalization,
implemented-function inventory, predictor audit, native Panina check and
measured-curve fitting in one reproducible run. It adds no inference method,
model family, density conversion or texture crosswalk.

From the repository root in the prepared project environment:

```sh
mise run eval:benchmark local/meta_v3.3.xlsx local/source-review/panina2015.pdf local/meta-benchmark
```

The equivalent direct command, also usable without Mise, is:

```sh
uv run --no-sync --project targets/ptfkit-eval python -m evaluation.experiments.meta_v3_3.benchmark \
  --workbook local/meta_v3.3.xlsx --paper local/source-review/panina2015.pdf \
  --output local/meta-benchmark
```

The output directory must be new. Add `--checkpoint <new-path.json>` to export
the count-only checkpoint represented by
`evaluation/datasets/meta_v3_3.benchmark-summary.json`. It excludes observations,
individual fitted parameters and local sample identities. Measurements, detailed
fits, exact row records and full reports stay in ignored local storage.

## Current scientific status

**Source review remains incomplete.** The historical 27-source retention
mapping is not a complete interpretation of the workbook. The master sheet
contains additional author/year blocks, and other worksheets contain repeated
views and dissertation data. Every populated worksheet row is now visible in
`workbook-scope.json`. Unknown row roles remain unknown: a numeric sample marker,
similar values, or an author/year label does not establish a sample, a pressure
grid, absolute retention observations, or an independent profile.

The 1,847 retention-sheet rows have exactly one disposition: 1,036 normalized
observations, 719 exclusions and 92 stored fitted parameters. Separate canonical
exports retain 549 volumetric observations in 59 series and 487 gravimetric
observations in 50 series. No density conversion is inferred. Some normalized
series are repeated experiments, not independent soil groups.

The current matrix contains 60,152 function/master-row/target records:
146 implemented functions, 206 explicitly declared master rows and two canonical
water quantities. All functions enter automatically from the reconciled
specification/manifest inventory. Registered adapter compatibility is checked
through the existing evaluation-plan validator. Fixed-output pressure support
uses exact converted coordinates, without rounding or interpolation. Functions
omitted from the manifest remain visible with their missing measurement paths.
New raw input readiness cannot bypass source, material or observation-method
review. Unclassified master rows outside this roster have explicit unresolved
dispositions and are not included in sample counts.

The source-reviewed Panina overlay supplies six horizons, 56 observations and
one shared profile. The benchmark executes both Clapp1978 and Cosby1984 using
the existing registered Table 2 class-coordinate derivation and dry adapter.
All 56 measured points satisfy both adapters; maximal and exact common cohorts
coincide. Cosby sample-balanced RMSE is 0.0227324258, MAE 0.0184300468 and bias
0.0055192141 in volume fractions. These class coordinates are derived predictors,
not measured PSD. The [scoring unlock review](scoring-unlock-review.md) records
the evidence chain, before/after counts and next source-review task.
Maximal and common sample-balanced RMSE is 0.0350360985, MAE 0.0305541769 and
prediction-minus-observation bias 0.0288498422, all in volume fractions.
Neither model selection nor population metric intervals are supported by one
profile. Final atomic/ensemble recommendations remain `insufficient_evidence`.
Native candidates, predictor compatibility, material evidence and observed
pressure support are not inferred from numerical executability.

## Catalog expansion and first ensemble

The subsequent [atomic source campaign](atomic-campaign-review.json) supersedes
the actionable interpretation of the discovery ceilings below. Chestnova's
15-function ceiling has no compatible released fixed-pressure or direct-FC
targets, and its predictor definitions are also unresolved. The new review
separates `predictor_status` and `target_status` for all 146 functions.

Reproduce the focused campaign without rerunning fits or ensemble experiments:

```sh
uv run --project targets/ptfkit-eval --no-sync python -m evaluation.experiments.meta_v3_3.atomic_campaign \
  --benchmark local/meta-benchmark-ensemble-final-20261025 \
  --workbook local/meta_v3.3.xlsx --output local/meta-atomic-campaign
```

The command verifies the benchmark inventory, workbook and reviewed paper
checksums, then writes a target availability table, the refreshed function
audit and source/family review decisions. It grants no predictor binding.
The 18 Badenko theta33 measurements are the strongest target-first opportunity,
but all matched quantitative PSD/density/carbon fields are empty, including
the repeated soil worksheet. Original matched predictor records are needed.
The review documents an evidence limit on the current canonical release;
it does not prove that all unclassified workbook cells are unusable.

The benchmark now writes `function-audit.json` and `function-audit.md` for all
146 implemented functions, including resolved predictor definitions, candidate
workbook columns, implementation co-blockers, scientific review needs, shared
input signatures, target pools and source unlock ceilings. Candidate columns
are discovery leads; neither name aliases nor humus values authorize a binding.
An uninventoried predictor is not proof of absence from the whole workbook.

The confirmed Panina profile currently supports two scored functions. No other
function is blocked solely by implementation on this reviewed profile. The
remaining 144 need scientific evidence; missing adapters are recorded separately
and are never used as proof of scientific impossibility. Fixed-pressure pools
remain separate: these six horizons have no exact observations at 10, 33 or
1500 kPa. Class coordinates authorized for Cosby do not authorize measured
particle fractions for other models.

Every compatible atomic pair is registered with fixed weights 0.5/0.5 before
scoring. `ensembles/predictions.json` retains exact common-coordinate forecasts;
`ensembles/summary.json` retains coverage and descriptive metrics. For Clapp
and Cosby, the mean has RMSE 0.0267555247, compared with Cosby's 0.0227324258:
the mean is worse by 0.0040230989. Both cover six horizons and 56 points.
This establishes the first descriptive ensemble benchmark (milestone B),
without increasing the number of scored atomic functions.

The existing nested convex-pair engine receives all sample identities and
groups by profile. It returns `insufficient_evidence` because only one profile
is available. No weights are fitted on the full dataset as a substitute, and
no ensemble recommendation is made. Learned blends require the same independent
training/validation/test evidence and are deferred.

Under the mapped-column discovery policy, Chestnova 2017 has the largest
conditional ceiling for new functions: 15 functions and 150 combinations.
Panina has a ceiling of three additional functions and 42 combinations across
the full mapped source, including horizons outside the current six-horizon
overlay: Rawls1982 theta1500, Rawls2003 theta33 tree, and Wosten2001 loam/clay.
These are review leads requiring predictor definitions, material and pressure
support, public measurement metadata and adapters where missing. They are not
confirmed releases. In particular the ceiling does not supply missing exact
fixed-pressure measurements. Shvarov's earlier combination-only priority does
not establish a gain in new functions under this stricter discovery policy.

All 59 confirmed volumetric series are fitted by the four existing registered
families with the unchanged measured-retention engineering policy. There are
236 sample/family fit attempts and 133 accepted fits: 35 van Genuchten--Mualem,
43 van Genuchten m=1, 21 Brooks--Corey and 34 Clapp gradual air entry. Optimizer
starts are counted separately. The 50 gravimetric series have 200 explicit
unsupported-family-target records; a volumetric family is not fitted to mass
ratios. Fits retain rejection reasons, conditioning and boundary diagnostics,
parameters, mean-curve intervals and conditional prediction intervals. Local
Student-t intervals remain conditional on unvalidated residual assumptions and
are never clipped to physical or fit bounds.

Descriptive pressure-region diagnostics use the fixed policy
`wrc_pressure_regions_kpa_v1`: wet [0,10), intermediate [10,1500), dry
[1500,infinity) kPa. Boundaries belong to the region on their right. Existing
sample-balanced metrics are reused; regions do not change selection loss.

## Source follow-up

The [priority reconstruction review](reconstruction-review.md) records the
2026-10-25 Nikulina, Medko and Fomin audit. Literal cross-sheet identity and
scientific eligibility are separate claims. The local priority-source audit
retains the exact 78 row crosswalks, separate particle-size cells and water-vector
reuse diagnostics. This review releases no additional observations.

The report includes ranked blocker impact and source-review ceilings, with
co-blockers and sole-gap counts. Source priorities exclude combinations needing
new public measurement contracts or adapters. These are conditional ceilings,
not expected gains. `scientific_status` distinguishes eligible, unresolved and
confirmed incompatible combinations independently of execution status. No
permanent structural impossibility is inferred from incomplete review.

`source-followup.json` records follow-up decisions for the 15 still-blocked
retention sources, plus targeted review of additional master blocks. Confirmed
physical and identity evidence remains in the existing mapping. A publication
lead is kept separate from a confirmed source/sample/measurement contract.

The newly inspected Fomin 2023 paper reports the Daryino site and a detailed
wetting/drying experiment. It explicitly uses a graphical pF marker for full
saturation. Exact workbook core/depth identity, water scale and the first
coordinate remain unresolved; the related source does not authorize conversion
of that marker into an experimental finite suction.

The primary library access records explicitly restrict the full Nikulina and
Medko dissertations. Cross-sheet transfer identities are now established, while
source-specific water scales and experimental coordinate binding remain
unresolved. Repeated Nikulina coordinates cannot be averaged. Medko's available
abstract describes both measurements and reconstruction, requiring a point-level
provenance distinction before export.

## Artifacts and integrity

The run creates:

- `workbook-scope.json`, `row-accounting.json`, `source-readiness.json` and
  `source-followup.json`;
- separate canonical volume/mass datasets and a full predictor audit;
- implemented-function inventory, registered adapter support, eligibility matrix
  and exclusions;
- `native-clapp/artifacts/` with checksum-verified predictions, point decisions,
  maximal/common cohorts, metrics and registered bootstrap evidence status;
- `native-class-comparison/artifacts/` with both candidates, exact common
  coordinates, derived-input lineage and dry-branch exclusions;
- `native-class-comparison/summary.json` with candidate coverage, pressure
  support, per-cohort wet/intermediate/dry metrics and uncertainty status;
- `function-priorities.json` with all 146 minimal predictor lists, conditional
  observed-row ceilings and operational review-cost labels;
- approximation fits, per-sample/family summaries and unsupported target records;
- pressure-region diagnostics, selection and uncertainty status artifacts;
- `summary.json`, a Markdown report and a final `artifact-hashes.json` inventory.

The final hash inventory is written only after the report succeeds. Its absence
means the run is incomplete. Input, mapping, manifest, source follow-up and
experiment implementation hashes preserve the interpretation used by each run;
historical experiment artifacts are not rewritten.

The opt-in [harmonized benchmark](HARMONIZED.md) adds registered evidence tiers,
in-range fixed-pressure reconstruction, a full catalog matrix and separate
target-pool ensembles alongside these strict artifacts. Its current META run
retains two scored atomic functions; the requested larger-coverage milestone
remains open because numerical predictor contracts are unresolved.

The [catalog exploratory campaign](CAMPAIGN.md) expands coverage through shared,
versioned reconstruction and approximation policies. It revisits every function
after each policy stage, retains a concrete blocker for every unexecuted function,
and compares candidates only on identical scenario/cohort observations. Its
results remain separate from the main leaderboard and recommendations.
