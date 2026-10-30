# meta_v3.3 workbook benchmark

The current v1.0 handoff uses **all predictable experimental WRC points**.
Predictor-defined testing datasets are described in
[PREDICTOR-SUBSETS.md](final_results/PREDICTOR-SUBSETS.md). Exact availability
signatures and overlapping input-requirement pools retain reported versus E5
predictors separately. Rebuild them with
`python -B -m evaluation.experiments.meta_v3_3.predictor_subsets` in the prepared
ptfkit-eval environment. Private memberships and datasets are under
`local/meta-predictor-subsets-v1_0/`.

Read [FINAL-RESULTS.md](final_results/FINAL-RESULTS.md),
[the accuracy/coverage table](final_results/wrc_accuracy_coverage.csv),
[the Pareto figure](final_results/wrc_accuracy_coverage.png), and
[the PNG audit](final_results/PNG-AUDIT.md). The Russian presentation is
[ptfkit_benchmark_summary_RU_v1.0.pptx](final_results/ptfkit_benchmark_summary_RU_v1.0.pptx).
The cohort-based reports below and `expanded_selection.json` retain historical
analyses; they are not the current primary WRC ranking.

The ledger has 1701 experimental coordinates: 1069 volumetric points in 77
samples and 632 gravimetric points in 65 samples, across 19 sources. Each route
uses every compatible coordinate with available predictors, without a minimum
number of observations per sample. No fitted value or interpolated target is
counted as an independent experimental observation. Fixed-pressure secondary
diagnostics explicitly distinguish reconstructed target pairs from directly
observed coordinates. Sample-balanced RMSE is the primary ranking metric;
pointwise metrics and coverage of the complete basis-specific ledger accompany
every model. Ensembles select their members inside each leave-one-source-out
training fold and use only available selected members at each held-out point.
Ksat retains its separate log metrics and block sensitivity, without ensembles.

To reproduce from the pinned local workbook and persisted source review:

```sh
uv run --no-sync --project targets/ptfkit-eval python -B \
  -m evaluation.experiments.meta_v3_3.replay_diagnostic_predictions
uv run --no-sync --project targets/ptfkit-eval python -B \
  -m evaluation.experiments.meta_v3_3.expanded_participation
uv run --no-sync --project targets/ptfkit-eval python -B \
  -m evaluation.experiments.meta_v3_3.final_approximation
uv run --no-sync --project targets/ptfkit-eval --with matplotlib --with python-pptx \
  python -B -m evaluation.experiments.meta_v3_3.publish_pointwise_wrc
```

The first step requires a new `local/meta-diagnostic-replay` directory; omit it
when reusing an already validated replay. The final step can be repeated and
regenerates every PNG from the saved forecasts and fits. It validates workbook
fingerprints, measured coordinates, fit targets and image integrity before
completing the package. The private ledger, `wrc_pointwise_predictions.csv`,
complete `diagnostic_index.csv`, diagnostic README and PNG ZIP are written to
`local/meta-final-v1_0-pointwise/`. Aggregate tables, reports, figures and the
presentation are under `final_results/`. Private sample data must remain in
ignored local storage.

The model-selection entry point audits original WRC/Ksat coordinates, preserves
separate water bases and compares exact common cohorts. Read
[MODEL-SELECTION.md](MODEL-SELECTION.md) for dataset-specific recommendations,
ensemble evidence, block sensitivity and limitations.

```sh
mise run eval:model-selection local/meta-catalog-resource \
  local/meta-catalog-harmonized local/meta_v3.3.xlsx local/meta-model-selection
```

The output directory must be new. The run writes a private observation ledger,
all-sheet target audit, catalog decisions, predictions, full cohort analyses,
an aggregate checkpoint and a final SHA256 inventory. Repeat with another output
directory and compare `artifact-hashes.json` byte for byte. The direct command is:

```sh
uv run --no-sync --project targets/ptfkit-eval python -B \
  -m evaluation.experiments.meta_v3_3.model_selection \
  --benchmark local/meta-catalog-resource \
  --harmonized local/meta-catalog-harmonized \
  --workbook local/meta_v3.3.xlsx --output local/meta-model-selection
```

Frozen strict/harmonized input inventories and workbook bytes are verified;
no atomic PTF is fitted to benchmark observations. E5 target assumptions are
retained alongside a reviewed-target-only sensitivity analysis.

The committed aggregate checkpoint is
[meta_v3_3.model-selection-summary.json](../../datasets/meta_v3_3.model-selection-summary.json).
Its two private runs produced identical artifact inventories and verified file
hashes. Validation passed 1,090 ptfkit-eval tests, including 33 focused selection
and workbook-semantic tests, plus Ruff lint/format and type checks. Removing the
Cosby midpoint-preservation fix makes its regression test fail on the mixed
measured/class clay coordinate; the fix was restored before the final checks.

The completed coverage-first exploratory checkpoint is the separate
[E5 workbook semantic benchmark](WORKBOOK-SEMANTIC.md). It preserves the frozen
strict and E0-E4 runs and records workbook assumptions without requiring a
complete laboratory or original-table provenance contract. The three hard
rules remain physical quantity compatibility, exact sample identity and no
invented missing values.

```sh
mise run eval:workbook-semantic local/meta-deep-unlock-audited \
  local/meta-catalog-resource local/meta-catalog-harmonized \
  local/meta_v3.3.xlsx local/meta-workbook-semantic-v1
```

The output directory must be new. See the E5 report for the direct Python
command, coverage attribution, remaining physical ambiguities and replay checks.
The historical benchmark and evidence-review instructions below retain their
original policies and results.

The standard run discovers the current public Python catalog, reconciles it
with source specifications and reapplies the existing strict and E1-E4 policies
to the fixed dataset. It performs exact common cohort comparisons, ranking
sensitivity, residual correlation, fixed ensemble comparisons and Pareto analysis.
It does not continue the manual source-unlocking campaign.

See [the current compact benchmark](BENCHMARK.md) for results. The sections below
the replay instructions retain historical scientific context; their catalog
counts describe those historical runs, not the current denominator.

The underlying resource builder reconciles the existing source-reviewed normalization,
implemented-function inventory, predictor audit, native Panina check and
measured-curve fitting in one reproducible run. It adds no inference method,
model family, density conversion or texture crosswalk.

From the repository root in the prepared project environment:

```sh
mise run eval:benchmark local/meta_v3.3.xlsx local/source-review/panina2015.pdf local/meta-benchmark
```

The equivalent direct command, also usable without Mise, is:

```sh
uv run --no-sync --project targets/ptfkit-eval python -B -m evaluation.experiments.meta_v3_3.catalog_benchmark \
  --workbook local/meta_v3.3.xlsx --paper local/source-review/panina2015.pdf \
  --output local/meta-benchmark
```

The output directory must be new. The command builds `resource/`, `harmonized/`
and `comparison/`. Read `comparison/benchmark.md` for the compact report and
`comparison/summary.json` for full metrics, exact cohorts, per-function audit,
rank changes, pair ordering changes, correlations and Pareto members. All
artifacts are hashed after successful completion. Private measurements, sample
identities, predictions and fits stay in ignored local storage.

The reviewed PDF must match its pinned checksum. The run never changes dataset
metadata or scientific policies. Public wrappers whose specifications have a
status other than `implemented` are included and flagged; a missing wrapper or
unaccounted public function fails the API reconciliation. If the native extension
is stale, rebuild it with `uv sync --frozen --all-groups --reinstall-package ptfkit`
from `targets/ptfkit-eval` before running.

The default previous benchmark is the committed historical campaign checkpoint.
Pass `--previous <completed-comparison/summary.json>` to measure changes against
a later run. To reuse the exact resource and fits without rebuilding them:

```sh
uv run --no-sync --project targets/ptfkit-eval python -B -m evaluation.experiments.meta_v3_3.campaign \
  --benchmark local/meta-benchmark/resource --harmonized local/meta-benchmark/harmonized \
  --workbook local/meta_v3.3.xlsx --output local/meta-comparison-replay
```

This compatibility entry point reapplies policies automatically; it performs no
manual source recovery. New generated public PTFs enter discovery, requirements,
strict eligibility, all policy stages, target pools and blocker decisions without
a registration list. Functions lacking supported targets remain explicitly
unbenchmarkable on this fixed dataset. Empty roster intersections retain separate
exact pair comparisons; those cohorts never form a pooled leaderboard.

RMSE, MAE and bias weight samples equally; median absolute error and residual
Pearson correlations weight points equally. Coverage includes both executable
pool-coordinate coverage and maximal sample coverage against all retained
canonical samples. The minimum tier and highest tier required by the comparison
are both recorded. The Pareto analysis uses a 1% relative error tolerance to
avoid preferring greater assumption burden for negligible error improvement.
Reduced ensemble membership uses the same observed cohort, so its apparent gain
is descriptive and subject to selection optimism. Learned blends retain the
existing grouped validation gates. Accepted-fit targets remain diagnostic.

The legacy strict-only resource builder remains available as the `benchmark`
module; its optional `--checkpoint` exports the original count-only format.

## Current scientific status

The separate [deep unlock audit](DEEP-UNLOCK.md) revisits the frozen 216-function,
44-executable snapshot in `BENCHMARK.md`. Confirmed generic mappings increase
exploratory coverage to 64 functions; strict coverage remains two. The frozen
benchmark files are retained as the baseline. The current campaign code applies
the registered mappings, including source-specific pressure units, explicitly
defined water-content differences and explicit retention-model conventions.

Reproduce discovery before running a new comparison:

```sh
mise run eval:deep-unlock local/meta-catalog-final local/meta-catalog-resource \
  local/meta-catalog-harmonized local/meta_v3.3.xlsx local/meta-unlock-discovery

uv run --no-sync --project targets/ptfkit-eval python -B -m evaluation.experiments.meta_v3_3.campaign \
  --benchmark local/meta-catalog-resource --harmonized local/meta-catalog-harmonized \
  --workbook local/meta_v3.3.xlsx --previous local/meta-catalog-final/summary.json \
  --output local/meta-unlock-comparison

uv run --no-sync --project targets/ptfkit-eval python -B -m evaluation.experiments.meta_v3_3.deep_unlock \
  --baseline local/meta-catalog-final --benchmark local/meta-catalog-resource \
  --harmonized local/meta-catalog-harmonized --workbook local/meta_v3.3.xlsx \
  --comparison local/meta-unlock-comparison --output local/meta-unlock-final-audit
```

The final audit includes `aggregate-summary.json` for publication and a Markdown
report. Its complete workbook cell scan, cached formulas, candidate inventory,
per-sample pressure gaps, predictions and evidence remain private. The aggregate
checkpoint is [stored separately](../../datasets/meta_v3_3.deep-unlock-summary.json).
Ksat and particle-density candidates are inventoried but require scientific
contract review before binding. Unspecified operational FC/PWP and model variants
remain unresolved. Fixed-pressure outputs are parsed from the specification;
the five reference coordinates used for curve comparisons do not restrict them.

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

## Ksat and predictor evidence review

The [workbook evidence audit](WORKBOOK-EVIDENCE.md) supersedes the historical
deep-unlock candidate classifications without rewriting frozen run artifacts.
Its [review registry](workbook-evidence-review.json) records block-specific units,
primary-source locators, measurement/origin limitations and predictor decisions.
The [aggregate checkpoint](../../datasets/meta_v3_3.workbook-evidence-summary.json)
contains all function decisions and source-specific candidate counts; individual
measurements and sample identities remain in ignored local artifacts.

Use the matching frozen 64-function campaign and deep-unlock scan:

```sh
mise run eval:workbook-evidence local/meta-deep-unlock-audited \
  local/meta-deep-unlock-report local/meta-catalog-resource \
  local/meta-catalog-harmonized local/meta_v3.3.xlsx local/source-review \
  local/meta-workbook-evidence-reviewed
```

The equivalent direct invocation is:

```sh
targets/ptfkit-eval/.venv/Scripts/python.exe -B \
  -m evaluation.experiments.meta_v3_3.workbook_evidence \
  --baseline local/meta-deep-unlock-audited \
  --discovery local/meta-deep-unlock-report \
  --benchmark local/meta-catalog-resource \
  --harmonized local/meta-catalog-harmonized \
  --workbook local/meta_v3.3.xlsx --sources local/source-review \
  --output local/meta-workbook-evidence-reviewed
```

The source directory must contain the four original document downloads named by
`references.*.local_file` in the registry, retrieved from their corresponding
`url` fields. Their SHA256 fingerprints are recorded in the checkpoint. Do not
substitute an HTML landing page for a PDF. Document interpretation is the
explicit versioned review, not an automatic inference from a filename or label.

Replay into a second new output directory with identical arguments except
`--output`. Compare the two `artifact-hashes.json` files byte for byte. Each run
also verifies frozen input inventories before and after execution, recomputes
strict predictions and requires both strict and exploratory prediction bytes
to match the completed campaign. Consequently the previous scored metrics remain
applicable; this evidence-only review does not recompute unchanged ensembles or
ablations. A newly approved target or changed prediction requires a new scored
campaign before publication.

Private outputs include the complete 36-row Ksat identity map, the automatically
selected Ksat catalog matrix, full per-sample catalog decisions, predictions,
strict predictions, source fingerprints, report and final artifact inventory.
No target pool is created until quantity, identity, units, method, origin and
material are confirmed. A future release must keep method-specific Ksat pools
and explicitly define logarithmic output transforms and reference units.
