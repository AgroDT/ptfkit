# ptfkit-eval development handoff

## Purpose

This is a living handoff for the ongoing implementation of the
`ptfkit-eval` roadmap. It records completed work, verification evidence,
scientific blockers, and the exact continuation point so that a later session
can resume without reconstructing decisions from chat history.

Last updated: 2026-10-24.

The active implementation goal continues. The latest verified checkpoint is
**740 component tests**, Ruff 0.16.1 lint/format and ty 0.0.71. Read the final
entry in [the progress log](ptfkit-eval-progress.md) for exact verification and
continuation evidence; that log supersedes historical continuation orders and
counts below. Online methodological and PTF publication review resumed; see
[the source review](ptfkit-eval-source-review.md). Primary workbook-source review has enabled eleven source rules and 1,036 normalized
observations; 549 are volumetric and 487 are gravimetric. Remaining sources
retain specific evidence blockers.
The source-review queue lists the missing evidence for all 15 blocked physical
source rules (692 rows). Shvarov 2008 and Shein 2012 together retain a separate
observation-provenance blocker for 149 rows; unit confirmation alone cannot
qualify differences or reconstructed curves as independent measurements.

The user's latest priority is technical implementation rather than further
source recovery. A new public normalization-to-canonical export and `export`
CLI command preserve volumetric observations and cell lineage, explicitly
account for gravimetric omissions, and require a declared material basis.
The private real-workbook replay exports 549 points across 59 records without
predictor or profile inference. Continue with executable real-data fitting
integration; soil-property gates and remaining uncertainty requirements stay
on the roadmap. Source exclusions remain active.

Implemented slices include portable run/CLI artifacts, fixed-pressure outputs,
nested fixed and learned selection, four approximation families, grouped
conformal prediction intervals, training-only empirical domains and error
strata, paired cluster differences, constant convex pairs, finite-grid hard
switches, fitted seam/curve diagnostics and descriptive outer strategy
assessment. Whole-group retraining trajectories preserve original independent
group identities, sample-occurrence weights and failed draws.

Supplied-forecast selection and shared native/forecast occurrence materialization
now support exact mathematical calibration. Equal/unequal group sizes,
informative missing targets and hard-switch identification failures are checked
against independent finite-state risk oracles. Installed-wheel replays reproduce
all five scenarios, including full hard-switch selection/failure evidence.
These are estimand, identification and computability diagnostics. They do not
qualify a complete strategy confidence interval; see the
[inference qualification note](ptfkit-eval-inference.md).

A bounded conditional outer-rule inference API now has a documented
concentration/union-bound derivation, exact equal/unequal-size coverage checks,
actual nested-selector integration tests and four installed-wheel replays.
Its explicit target is the equal-fold mean conditional risk of fitted outer
rules, rather than averaged-over-training risk or a final all-data model.

Native conditional risk registration, complete coverage/provenance validation,
failed-fit reporting and simultaneous allocation across reported strategies are
now integrated. Failed policies remain in the original family size. The new
synthetic conditional-risk example defines an IID binary group population with
prior loss/size bounds and a deterministic generator, rather than inferring
independence from IDs. Its full CLI run and installed-wheel replay are recorded
in the final progress entry.

Independent training-law inference is now implemented as a low-level API with
separate failure probability, successful-risk mass, successful-training risk
and prior-total-learner model risk. Exact multinomial coverage and probability
oracles are verified. Native conditional-risk integrity additionally reconstructs
nested splits and verifies complete in-domain pressure grids.

Native independent blocks now rerun the complete selector, retaining every
original role, inner selection, outer refit and training failure. Independent
and paired risk policies are registered and portable. Finite-grid learned blend
intervals and target-free endpoint diagnostics are implemented. Separate
sample-balanced point MAE/MSE assessment preserves the log-pressure selection
objective; pooled RMSE is explicitly the root of training-average MSE.

Nonlinear pressure-only sigmoid gates and target-free center forecasts are
implemented and qualified on finite mathematical populations. Next: continue
soil-property gating and scientifically justified parameter/remaining metric
uncertainty. Original scientific/real-data
eligibility remains blocked on source evidence. The active goal continues.

## Acceptance target

The package is intended to evaluate every implemented ptfkit function against
every scientifically compatible observation that can be recovered from
`meta_v3.3.xlsx`. It must select atomic functions and registered ensembles only
through leakage-safe grouped validation, and it must fit and report supported
retention approximation families with distinct applicability, confidence,
prediction, and parameter-uncertainty intervals.

The detailed contract and roadmap remain in
`docs/src/contributing/ptfkit-eval-plan.md`.

## Current repository state

The public manifest contains five evaluation-ready contracts:

- `calc_ptf_clapp1978`;
- `calc_ptf_vereecken1989`;
- `calc_ptf_gunarathna2019_vwc10_set1`;
- `calc_ptf_gunarathna2019_vwc33_set1`;
- `calc_ptf_gunarathna2019_vwc1500_set1`.

The evaluator already provides a measurement-aware manifest loader, dataset
mapping schema, workbook inventory, retention profiler, rule-gated
normalization, wide-to-long reconstruction audit, predictor audit, range-gated
curve router, reduced van Genuchten adapter, Clapp-Hornberger adapter, and a
curve execution layer. Descriptive retention metrics now provide per-sample
errors and sample-balanced cohort ME, MAE, RMSE, and median absolute error.
Explicit maximal/common cohorts and whole-cluster percentile confidence
intervals are implemented on top of those metrics.

The real-workbook artifacts are checksum-bound to SHA-256
`1322bf65b1ca0130085015209858a443d1ee82a7e2ae69232321cd8ede361e68`.
The workbook remains external because redistribution rights are unresolved.

## Current dataset evidence

The retention profile accounts for 1,755 observations and 92 fitted van
Genuchten parameter values. Six complete source rules and five partial row reviews emit 1,036 canonical
observations across 109 sample identities. They cover Chestnova 2017 (130), Gumatov 1991
(190), Gumatov 1992 (10), Bolotov 2014 (167), orchard Makarychev 2014 (56),
and arboretum Makarychev 2018 (96), plus Panina 2015 (116), Badenko 2013
(106), Umarova 2008 (81), Sadovnikova 2011 (61), and Moiseev 2018 (23).
Sadovnikova preserves two
experimental repeats of two soils, not four independent samples.
One Bolotov water value remains null.
The other 719 observations remain explicit exclusions: 644 blocked rules,
48 stale cached identities, six ambiguous matches, 17 unreviewed pressures
three table statistics and one null. Complete-curve readiness remains limited to six rules. Predictor compatibility remains blocked.

The predictor cohort contains 206 reviewed sample rows. The current manifest
contracts have the following raw-input coverage:

- Clapp: 89 complete texture values and zero eligible rows;
- each Gunarathna Set 1 function: 51 populated sand values and zero eligible
  rows;
- Vereecken: 34 rows with all four raw inputs and zero eligible rows.

The 51 sand-bearing rows are split across Sapozhnikov 1988 (12), Khaydapova
2001 (6), Shein 2011 (6), Makarychev-1 2014 (5), Makarychev-2 2014 (7),
Chestnova 2017 (10), and the parameter-only Kokareva 2007 block (5).
Thirty-four rows also contain bulk density.

## Sapozhnikov 1988 review

The following claims are now supported directly by workbook structure:

- the long label `1988_сапожников` and master label `1988_Сапожников` identify
  the same source and sample-number namespace;
- all 12 long-sheet sample groups match the 12 complete nine-point master
  curves bijectively;
- `Данные!W7` assigns the wide block the `W` encoding;
- `Данные!W1` defines `W` as mass-based water content, so the physical quantity
  is `gravimetric_water_content`.

The source is still blocked. The workbook does not distinguish percent from
fraction for this block, does not establish the source-specific pF convention,
and does not explain the first-axis `0.01` to `-1` replacement. It also does
not prove the 2,000-micrometre sand upper boundary, fine-earth dry-mass basis,
sieve method, bulk-density unit, or bulk-density method required for scoring.

The mapping, reconstruction audit, documentation, and regression tests encode
this partial review. The primary 1988 article was not recovered during the
initial search; secondary bibliographies identify it as an article in
`Pochvovedenie`, issue 10, pages 67-74.

## Kokareva 2007 search

The 2026-10-23 continuation searched both Kokareva and Kokoreva spellings,
including Cyrillic variants. It did not recover a primary methods record that
establishes the equation, axis, units, and fitting convention of the five
workbook parameter sets. The `fitted_parameter_conventions` blocker remains.

A bibliographic lead is reference 68 in
[Electrical Geophysical Methods in Agriculture](https://landviser.com/wp-content/uploads/2012/05/Electrical_methods_agriculture_2007_China.pdf),
which lists Kokareva, Pozdnyakov, and Smernikov at a 2007 soil-cover conference.
This is a search lead only: it does not identify the workbook parameter sets
or establish their scientific conventions. No source rule was promoted.

## Descriptive metric slice

`summarize_retention_errors()` accepts one already eligible cohort for one
candidate and protocol in canonical kPa and volumetric volume fractions.
Samples are identified by `(source_id, sample_id)`. Distinct pressure points
share a sample's weight equally, and every sample has equal total cohort weight.
RMSE is the square root of mean sample MSE. Median absolute error uses the
same balanced point weights, with exact rational weights to resolve half-weight
boundaries. Per-sample summaries preserve observed pressure extents and counts.

Empty cohorts, duplicate source/sample/pressure keys, nonfinite values, invalid
observations, and overflowing squared errors are rejected. Finite unphysical
predictions remain scored without clipping. This function does not construct
eligibility or implement the future log-pressure-integrated selection loss.
Callers retain measurement contracts and raw-cell/prediction lineage outside
this descriptive summary. Comparisons now carry optional source-local profile
identifiers; summaries count known profiles and samples without profiles.

## Cohorts and clustered confidence intervals

`build_retention_cohorts()` accepts all declared candidates, including empty
ones, under an identical dataset, protocol, and canonical `TargetSpec`.
Maximal cohorts retain each candidate's eligible points. Common cohorts use
the exact source/sample/pressure intersection across every candidate and verify
observed values and profile identity. They retain excluded points with the code
`point_not_shared_by_all_candidates`. Empty common cohorts have no descriptive
summary; they are not represented as zero error. No errors or prediction values
choose cohort membership.

`bootstrap_retention_errors()` implements whole-source or whole-profile
sampling with replacement. Cluster multiplicity and all within-cluster rows
are preserved; each sample occurrence keeps equal total weight. Source-local
profile grouping and optional whole-cohort source fallback are explicit in
`ClusterBootstrapPlan`. The seed and minimum group count are mandatory.
The default confidence level is 95%, the default replicate count is 2,000,
and the default missing-profile policy rejects estimation. Missing profiles,
empty cohorts, and insufficient groups return `insufficient_evidence` with a
machine-readable reason and no intervals. Invalid records fail validation
before the evidence gate.

The method `cluster_percentile_linear_v1` reports equal-tail percentile
confidence bounds for all four metrics with linear interpolation at
`(n_resamples - 1) * probability`. The implementation uses a local seeded
Python `random.Random` instance and canonical ordering, without changing the
global random state. Reproducibility assumes the same Python/package
environment. The registered minimum group count is an evidence gate, not a
coverage guarantee. Prediction intervals, parameter uncertainty, paired
candidate-difference intervals, empirical domains, and nested selection remain
pending. This continuation did not enable real-workbook scoring.

The workbook mapping and count-only artifacts were unchanged; no workbook
artifact regeneration was needed.

## Verification status

The initial continuation baseline had 119 passing tests and a passing ty check.
Remaining lint/format failures were confined to import/export ordering and
boolean argument style in `eligibility.py` and its tests; these are now fixed
without changing behavior or disabling rules.

`mise` was absent from PATH, so equivalent component checks were run directly
from `targets/ptfkit-eval` using the repository-pinned executables:

- Environment: `uv sync --frozen --all-groups` completed successfully.
- Lint: `C:/Users/KT/AppData/Local/mise/installs/ruff/0.16.1/ruff.exe check`
  passed.
- Format: the same Ruff executable with `format --check` passed for 33 files.
- Types: `C:/Users/KT/AppData/Local/mise/installs/ty/0.0.71/ty.exe check` passed.
- Tests: `.venv/Scripts/python.exe -m pytest` passed all 176 tests.
- Whitespace: `git diff --check` passed.

The 16 new metric cases use hand-calculated binary-fraction errors and cover
sample weighting, RMSE aggregation, weighted medians, source-local identifiers,
input-order invariance, unclipped predictions, invalid inputs, duplicate keys,
and empty cohorts. An in-memory mutation replaced per-sample point weights with
uniform point weights; the focused weighting test failed at the expected mean
error assertion. The production file was verified unchanged by that probe.

The cohort/bootstrap continuation adds 41 cases, including one additional
metric-validation case. Synthetic examples protect sample/pressure intersection,
empty-candidate retention, target/protocol consistency, observation and profile
identity, cluster-count evidence gates, explicit whole-cohort fallback, and
seed/order/global-state behavior. An exhaustive AA/AB/BA/BB two-cluster fixture
with unequal sample and pressure counts gives hand-calculated bounds for all
four metrics. A synthetic cohort-to-bootstrap test verifies exclusions are not
reintroduced. In-memory mutations replacing intersection with union and sample
weights with point weights were both detected. Production files were verified
unchanged, and the full unmodified suite subsequently passed.

## Immediate continuation order

1. Continue source-level review of the remaining sand-bearing observation
   sources while retaining the unresolved Sapozhnikov and Kokareva blockers.
   Revisit Kokareva only when a primary methods record becomes available.
2. Persist dataset/protocol/cohort and bootstrap contracts in evaluation plans
   and reproducible run artifacts, retaining upstream observation and prediction
   lineage and full eligibility/exclusion counts. Wire these APIs into a
   synthetic evaluation run before applying them to eligible workbook records.
3. Keep the future selection loss separate from descriptive point-grid metrics;
   its log-pressure weighting must be registered before held-out scoring.
4. Regenerate every affected count-only workbook artifact and update this file,
   the main plan, and the package README.
5. Run the complete relevant verification suite and record exact commands and
   results here.

## Non-negotiable scientific rules

- Never infer units, bases, methods, or particle boundaries from value
  magnitudes alone.
- Never use measured held-out targets to choose a model, ensemble member,
  boundary, blend weight, or approximation family.
- Keep fitted-family approximation error separate from PTF prediction error.
- Keep confidence intervals, prediction intervals, fitted-parameter
  uncertainty, applicability domains, and validated axis ranges separate.
- Preserve raw-cell lineage for every normalized value and prediction.
- Keep ambiguous records visible as exclusions with machine-readable reasons.

## Worktree caution

The 2026-10-23 continuation began with a clean worktree; the earlier Gunarathna
migration and dataset evaluation changes were already committed. Current edits
are the metrics, cohort and bootstrap slices, lint/format fixes, and
corresponding documentation.
Inspect both `git diff` and `git diff --cached` before editing overlapping files.

## Resume checklist

At the beginning of the next session:

1. Read `AGENTS.md`, the development guide, this handoff, and the main plan.
2. Run `git status --short` and preserve the existing worktree.
3. Read the latest verification results in this file.
4. Resume the first unfinished item in **Immediate continuation order**.
5. Update this handoff as decisions and verification results change.


Latest checkpoint: **433 tests**. Read the final progress entry and
`evaluation/experiments/group_ratio/README.md`. The supplied-forecast selection
API and exact equal/unequal-group calibration now work from the installed wheel.
No strategy CI is qualified. Continue with missing-target/parameter-instability
scenarios and a justified training-law inference procedure; the active goal
and deferred scientific requirements remain unfinished.


Latest checkpoint: **443 tests**. Shared native/supplied-forecast group occurrence
materialization and informative missing-target calibration are verified, including
three exact installed-wheel experiment replays. See the last progress entry.
Continue with parameter-instability/boundary scenarios and justified inference;
the active goal and deferred scientific requirements remain unfinished.


## Independent complete-selector training continuation

Native `independent_training_risk` now registers atomic/ensemble policies for
whole-selector repeated training on disjoint original-group blocks. The original
resolved grouping is frozen before allocation. Inner candidate selection and
learned convex/hard-switch refits repeat independently using only each training
block; parent CV choices are unused. Every fit failure and every test membership
is retained. Missing successful-test predictions suppress inference rather than
becoming training failures. One frozen q-strategy confidence family includes all
requested failed policies, separate from conditional outer-risk/metric families.

`independent-training-risk.json` and the report preserve complete input/role,
inner-score, refit, prediction, loss and failure evidence. The portable native
example is `evaluation/examples/synthetic_training_risk/`; with two blocks its
bounds are honestly uninformative. Training size is four groups per block, not
the final full-data size. See the latest progress entry for verification and
installed-wheel replay. Broader scientific qualification, nonlinear/learned-blend
extensions and original workbook-source compatibility remain outstanding.
# Latest technical checkpoint: measured reference fits

Run `evaluation/experiments/measured_retention/fit.py` on the canonical export
for an approximation-only experiment; see its adjacent README. This avoids the
general runner's requirement for a PTF candidate while predictors remain
unavailable. All 236 sample/family results are retained (133 accepted, 103
failed), with input lineage, physical diagnostics, optimizer attempts, and
identifiability. Real artifacts remain ignored under `local/`.

The initial boxes reproduce the synthetic-example engineering policy and were
not tuned to release boundary failures. Exact byte replay, exclusive-output
protection, Ruff, and ty passed. Source-specific bounds and residual uncertainty
assumptions remain unqualified; family acceptance is not external PTF accuracy.
# Latest checkpoint: interval support diagnostics

`diagnose_fit_uncertainty_support` is public and included in the standalone
measured experiment. It flags parameter-box and physical water-content interval
violations without changing fit status or clipping intervals. Failed fits and
unavailable parameter intervals remain explicit. Full verification is now
**741 passing tests**, with Ruff, ty, and byte-identical real-data replay.
See the progress and source review for the overlapping 67/12/44 diagnostic
counts and the official covariance reference. Constrained uncertainty and
source-specific bounds remain future work.
# Latest checkpoint: bounded nuisance profiles

`profile_retention_parameter` and `--profile-saturation-points` in the measured
experiment are implemented. Full verification: **742 tests passed**, Ruff and
ty passed. Exact real-data replay covers 133 saturation profiles / 798 grid
points. Five profiles improve original SSE by more than 1e-10: investigate
optimizer stability before assigning profile confidence thresholds. Neither
profile roots nor statistical coverage are implemented or claimed. Original
fits, parameter bounds, and previously reported local intervals remain intact.
# Latest checkpoint: profile counterexamples and full refits

`assess_profile_optimality` now explicitly flags grid objective improvements.
The measured experiment runs a separate full fit from an interior best-profile
start, preserves the original fit, and records the changed initial values.
All five Brooks--Corey counterexamples produced accepted full refits with
approximately 16--29% smaller SSE. Exact boundary starts are not nudged.
Two full experiment artifacts replay byte-for-byte. Verification is now
**743 passing tests**, with Ruff and ty passing. These findings do not certify
global optimality or statistical coverage; profile confidence endpoints remain
unqualified.
# Latest checkpoint: all-parameter post-refit audit

The measured experiment now records `profile_refit_audit`: every accepted full
refit is profiled across all family parameters, with updated uncertainty support.
The five Brooks--Corey refits produced 20 profiles with no new improvement over
the 1e-10 SSE threshold. Exact replay passed. One parameter-support violation
remains among these five fits, despite no curve-interval support violations.
These are grid diagnostics, not global or statistical coverage guarantees.
Verification: **744 tests passed**, Ruff lint/format and ty passed. Next work
remains justified constrained interval inference and its coverage calibration.
# Latest checkpoint: approximate profile grid regions

`assess_profile_grid_region` applies the single-parameter extra-SSE F threshold
to explicit profile nodes. Profiles now retain original n-p and parameter-box
metadata. Unavailable evidence is withheld; disconnected accepted runs and
contact with either parameter bound are explicit. No continuous endpoints or
calibrated constrained coverage are claimed. All 20 real-data post-refit regions
were assessed at nominal 95%, with two reaching a declared bound; exact replay
passed. Verification: **751 tests passed**, Ruff lint/format and ty passed.
Next: boundary/coverage calibration and justified grid refinement or root
searches, with convergence and missing-evidence safeguards retained.
# Latest checkpoint: Gaussian boundary coverage control

`evaluation/experiments/profile_coverage` now tests the public F-grid region
API on an exact bounded mean SSE profile, with independent unbounded t
classification and separate selected-fit coverage denominators. At nominal
95%, the fixed 4000-repetition run observed 94.9% coverage in the interior
and about 97.5% at either boundary. The half-line boundary reference and
finite-box limitations are documented; these are not retention coverage claims.
Exact replay passed. Verification: **753 tests passed**, Ruff lint/format and
ty passed. Next: nonlinear retention-family coverage with fit failure and
boundary withholding accounted for, plus justified profile-grid refinement.
# Latest checkpoint: nonlinear coverage pilot

`evaluation/experiments/retention_coverage` now exercises all four registered
families at interior and lower-boundary saturation truths. Two full runs replay
byte-for-byte. Among 400 generated samples: 298 accepted fits, 102 boundary
rejections, ten withheld Brooks--Corey lower-objective profile assessments,
and 269 covered truths among 288 assessed regions. These pooled totals are
accounting, not a pooled coverage claim; see the eight-scenario README table.
The 50-repeat scenarios remain an unqualified pilot. Verification:
**755 tests passed**, Ruff lint/format and ty passed. Next: prespecified larger
calibration and a stable Brooks--Corey optimization policy before qualifying
profile uncertainty. Retain all failure and selection denominators.
# Latest checkpoint: optional pressure restart policy

`brooks_corey_pressure_partitions_v1` is available via fit/run plans and profile
nuisance refits. It preserves original starts, bounds, and gates, adding only
pressure-knot/geometric-midpoint air-entry starts. Default policy is unchanged.
Two paired 400-realization replays were byte-identical and used observations
identical to the original pilot. Eighteen of 100 Brooks--Corey fits improved SSE
by >1e-10, but nine profile counterexamples persisted (seven interior, two
boundary-truth). This is not a stability fix or a coverage improvement claim.
Verification: **758 tests passed**, Ruff and ty passed. Next: piecewise
air-entry interval optimization, with failures and all denominators preserved.
# Latest checkpoint: piecewise interval optimization

`brooks_corey_interval_solves_v1` is implemented for full fits, nuisance profiles,
and run plans. It preserves original full-box attempts and adds bounded solves
in every pressure-defined air-entry interval. Attempts retain local interval
limits, separate from scientific bounds. Internal knot solutions do not become
physical boundary failures. Default behavior is unchanged.

On identical pilot observations, 19/100 Brooks--Corey fits improved SSE, and no
profile lower-objective counterexamples remained. Interior coverage was 47/50;
selected-boundary coverage was 21/25, with 25 boundary fit rejections. Therefore
numerical improvement does not qualify nominal coverage. Verification:
**760 tests passed**, plus eight focused tests after final refactoring; Ruff
and ty passed. Next: prespecified larger coverage calibration, especially for
boundary-fit selection and nonsmooth knot uncertainty, without hiding failures.
# Latest checkpoint: expanded study and real-data readiness

The 34-cell prespecified expanded study completed **6800 realizations** with
checksummed resume and Monte Carlo reporting. See
`evaluation/experiments/retention_coverage/EXPANDED.md` and `expanded-summary.json`.
All cells replayed unchanged using archived exact implementation snapshots.
There is one Bonferroni-adjusted undercoverage flag: dense van
Genuchten--Mualem, theta_s=0.3, sigma=0.002, 85/99 covered assessed regions,
p=0.0004174. No F-grid uncertainty method is promoted or declared qualified.

The real-data interval-policy comparison is in
`evaluation/datasets/meta_v3_3.fit-policy-comparison.json`: 21/59 Brooks--Corey
objectives improved, none worsened, 21 fits remained accepted overall, and
profile counterexamples fell from five to zero. Installed-wheel replay matched
the real fitting artifact byte-for-byte.

`meta_v3_3.readiness-summary.json` binds the same workbook, mapping, manifest,
and canonical dataset. All 59 identities match uniquely; no PTF has eligible
predictors. Only Clapp has complete raw inputs on this cohort (24 texture
values), all classification-blocked. Other functions need missing predictors,
and the target material basis is still unspecified. No scientific gates were
relaxed and no scores were fabricated.

Verification: **765 passing tests**, Ruff lint/format and ty passed. Next work
is constrained uncertainty qualification for the flagged case and source-backed
predictor/target readiness; optimization instability is no longer the only or
main blocker. Large raw simulation and measurement artifacts remain local.
# Latest checkpoint: independent boundary follow-up

The original adjusted coverage flag is retained, with a separate prespecified
investigation in `evaluation/experiments/retention_coverage/BOUNDARY-FOLLOWUP.md`.
Analytic audits found no >1e-10 objective improvements in 200 original cases;
linear and nonlinear methods had identical original joint-selected coverage
events (85/99). The independent 2000-realization series gave nonlinear coverage
937/992 = 94.46%, exact 95% interval [92.84%, 95.80%], p=0.2343. A 100000-draw
exact linear control was consistent with nominal coverage. No solver or
threshold change is justified by these findings, and no global or real-data
coverage claim is introduced.

`boundary-followup-summary.json` and its verification command retain provenance,
all paired counts, and a precise replay scope. Large raw block/audit records
remain local. Verification is **767 passing tests**, with strengthened
hand-calculated Jacobian/t-control tests, Ruff and ty passing. Next: practical
coverage tolerances/precision if qualification continues, and source-backed
predictor plus target-material readiness for actual external PTF scoring.
# Latest checkpoint: first source-backed external Clapp check

The 24 texture candidates now have a source audit: six Panina gray forest
horizons supported, six sod-podzolic horizons unsupported by Clapp's class
roster, twelve other-source candidates unresolved. See
`evaluation/datasets/meta_v3_3.clapp-source-review.json` and
`evaluation/experiments/panina_clapp/README.md`.

A separate reviewed canonical overlay produces **56 eligible measured points
across six horizons of one profile**. MAE=0.0305542 and RMSE=0.0350361 volume
fraction. Confidence intervals are correctly withheld (`too_few_groups`).
Global workbook bindings and unreviewed source categories remain unchanged.
This is descriptive external checking, not national or pressure-domain
validation. The count/metric summary is `meta_v3_3.clapp-pilot-summary.json`.

The Windows publication ACL defect is fixed without changing other directories:
published staging inherits destination-parent permissions, with atomic rename
and failure cleanup. Independent-process reads, byte-identical source/wheel
replays, and persisted-plan prediction replay passed. Verification:
**771 tests passed**, plus 13 focused tests; Ruff and ty passed.
# Full-catalog migration checkpoint

The active objective remains full implemented-function evaluation, per-dataset
atomic/ensemble strategy selection and justified van Genuchten/Brooks-Corey
uncertainty and applicability. The Wosten class-parameter function now has a
complete source-reviewed measurement contract and a source-restricted Mualem
retention adapter. Six of 146 implemented functions enter the manifest; 140
remain omitted. Generated computational code and coefficients are unchanged.

`evaluation/experiments/catalog_coverage/matrix.py` produces the complete
146-by-six source-partition raw readiness matrix. Exact replay was
byte-identical. Missing input bindings correctly count as unavailable raw
inputs. The canonical volumetric cohort remains blocked at raw predictor and
material gates; the separate six-horizon Panina Clapp overlay remains the only
reviewed external pilot. Its predictions, cohorts, eligibility and quality
artifacts are byte-identical under the expanded manifest.

Do not rerun old source-hash-pinned simulation studies with the modified
package and claim their historical environment is unchanged. Preserve their
archived wheels and source snapshots. New work should extend canonical
support to the separately normalized gravimetric observations with explicit
basis/unit contracts and volume-only fitting gates, then migrate compatible
fixed-pressure PTF contracts from primary sources.
# Gravimetric evaluation handoff

The canonical dataset reader now supports version 2, including an explicit
mass-fraction/dry-soil-mass target; version 1 remains volume-only. Export's
optional `water_quantity` selects one physical quantity and preserves the
other quantity's omitted row identities. Default volume export still has the
original semantic hash. Mass export has 487 observations, 50 curves, five
source partitions and 20 values above one; no density conversion is involved.
Both exports account for all 1,036 normalized observations. See
`meta_v3_3.canonical-exports-summary.json` and the mass readiness matrix.

Comparison records and metric summaries retain their water quantity. Native
fixed-output execution, cohorts, aggregate cluster bootstrap intervals and
curve quality respect the declared canonical unit and physical bounds. Mixed
quantities and mismatched cohort/comparison targets are rejected. The supplied
approximation families and grouped conformal protocol still reject mass
targets. Do not describe this extension as qualification of gravimetric fitting
or prediction intervals.

The four Dharumarajan retention functions remain omitted from the evaluation
manifest. The original PDF confirms target pressures but leaves the water
denominator unresolved, as existing YAML warnings already state. The review
in `dharumarajan2019.measurement-review.json` records the PDF hash and exact
blockers. Legacy output quantity identifiers are not reviewed measurement
contracts. Continue source migration with explicit denominator evidence; do
not force a gravimetric label because a mass-basis benchmark now exists.
# Beniaich contract and pressure-support handoff

The current manifest includes 17 implemented functions after migration of all
11 Beniaich linear regressions. The remaining 129 functions lack complete
descriptors. The added organic-matter quantity is distinct from carbon; source
methods and input derivation gates remain strict. Saturation has no assumed
zero-pressure condition. The reviewed source PDF and decisions are bound in
`evaluation/datasets/beniaich2023.measurement-review.json`.

Both readiness matrices and the volume readiness summary now use the
17-function manifest. `meta_v3_3.fixed-pressure-support.json` shows that the
mass dataset has no exact observed targets for the 22 new 33/1500-kPa outputs.
The pressure audit is count-only and grants no material/method/input/scoring
permission. Its regression test rejects even a one-ULP pressure snap, and
capillary saturation remains unsupported as a fixed zero-pressure target.

Next implementation should address discrete multi-output candidates or a
prespecified single-pressure selection loss. Existing curve selection requires
two supported pressures; an individual fixed-pressure output cannot be treated
as a continuous function. Joint FC/PWP selection can use explicitly discrete
support without inventing intermediate predictions. Real-data selection still
requires compatible input and observation evidence or a separately justified
approximation-reference protocol. Preserve the full original objective.
# Discrete candidate selection handoff

The previous multi-output dependency is implemented. Evaluation plan v2 adds
`function_points` with `fixed_outputs` and an explicit output-name list.
`FixedPointsPrediction` preserves each manifest pressure and method. Native
execution and target-free forecasting reject unsupported pressures, and
converted pressure duplicates are rejected at resolution and execution.
Every selected output method must match the run protocol. Version-1
evaluation plans remain compatible and reject the new candidate kind.

`evaluation/examples/synthetic_discrete_retention` is a complete reproducible
example with six synthetic profiles and two real Beniaich functions. It
demonstrates native joint FC/PWP scoring, grouped nested atomic selection,
training-only convex weights and unchanged training decisions under outer
target perturbations that favor the opposite atom. It is not an external
benchmark and does not resolve the real mass cohort's missing exact pressure
targets or predictor/method/material blockers.

The full suite passed 829 tests. An isolated wheel passed 14 focused tests and
replayed every example artifact exactly. Source-pinned historical coverage
studies still require their archived wheels; the package source hash changed
with this feature. Next work must continue toward the original complete
catalog/data/strategy/uncertainty objective, including single-pressure
selection and additional source/data compatibility work.

## HYBRAS positive-head data checkpoint

The official archive and manual are in `local/source-review/hybras2018`.
`evaluation/experiments/hybras/build.py` pins source checksums and creates the
canonical positive-head volume cohort with full local provenance. Source review
and count-only summaries are tracked under `evaluation/datasets/hybras_v1.*`.
Use `evaluation/experiments/hybras/README.md` for replay commands and limitations.

Current authoritative inputs are under `local/hybras-positive-head-reviewed`.
`dataset.json` preserves all 7,718 positive-head points, with 664 blocked
because of the source's ambiguous `1atm=1020cm` comments. Use
`fitting-dataset.json` for approximation: 7,054 points and 987 horizons.
The earlier preliminary cohort under `local/hybras-positive-head-first`
contains 7,718
observations from 1,075 horizons and 445 profile IDs. All saturation anchors
are deferred, and 68 nonmonotone curves remain intact with diagnostics.
No predictor bindings, material assumptions or external PTF eligibility have
been added. The source comments matter for future method/calibration review.
The matching evaluator wheel and experiment scripts are archived under
`local/hybras-positive-head-first/reproduction`.

The preliminary 4,300 fits completed. The exact-observation review retains
3,948 independent fits for the reviewed subset; tracked counts are in
`hybras_v1.reference-fit-summary.json`. Accepted fits: Brooks-Corey 91,
van Genuchten Mualem 138, van Genuchten m=1 120, Clapp 109. Most other
fits encounter declared parameter bounds, so these results do not qualify
the boxes or uncertainty for HYBRAS. The following checkpoint adds ordered
parameter support; measured saturation and native predictor/source review
remain outstanding.

## Ordered-water fitting checkpoint

The optional `bounded_trf_ordered_water_multistart_v1` method supports overlapping
water boxes, physical-coordinate covariance and constrained nuisance profiles.
The schema and run loader preserve the method. Default fitting behavior remains
covered by the full 844-test suite; 18 isolated-wheel tests pass.

`evaluation/experiments/hybras/fit_ordered.py` completes 1,974 VG Mualem/BC fits
on the reviewed 987-curve cohort. Original numerical provenance and exact
source/script snapshots are under `local/hybras-ordered-water-first`.
The initial pretty JSON sequence was losslessly reserialized as
`fits.repaired.jsonl`, preserving the original file and recording both hashes.
The current script emits proper compact JSONL. An installed-wheel replay is
under `local/hybras-ordered-water-wheel-replay`, with its matching wheel and
script in `reproduction`. All 1,974 complete fit records match the repaired
first-run stream byte for byte. See the experiment README for commands.

The tracked `hybras_v1.ordered-fit-comparison.json` reports 486 accepted VG and
399 BC fits but explicitly withholds uncertainty qualification. It preserves
27 BC optimizer counterexamples (six locally accepted), numerous intervals
outside boxes/physical support, and six formerly accepted fits now rejected.
Next audit these counterexamples using explicit baseline-informed/restart and
profile policies. Do not claim optimality, calibrated coverage, restored
saturation measurements, broad native eligibility or final ensemble selection.

## BC restart audit checkpoint

The 27 known objective regressions were audited using explicit additional
physical starts, without replacing the original seeded solves. The optional
`additional_starts` field is supported by fit plans, run schema/loading and
parameter profiles. Family registry order determines vector order. Full-suite
validation passed 862 tests; the isolated wheel passed 48 focused tests.

Authoritative numerical runs:
`local/hybras-brooks-corey-restart-audit` and
`local/hybras-brooks-corey-restart-wheel-replay`. All 81 refits, including
20 profiles, and the terminal summaries are byte-identical. Matching wheels
and scripts are under each `reproduction` directory. The experiment README
contains exact commands. `hybras_v1.restart-audit-summary.json` verifies
5,325 converged SSEs against an independent BC equation and records all counts.

All three policies resolve all 27 known objective regressions, while retaining
16 boundary rejections and 11 accepted fits per policy. Of six previously
accepted counterexamples, five remain accepted and one is boundary-rejected.
All 20 profiles find no better objective on their grids; six grid regions
reach parameter bounds and 13 contain only the estimate. No continuous or
empirical-coverage confidence qualification follows. Do not merge this targeted
posthoc audit into full-cohort performance counts.

Return next to native catalog/data coverage and real grouped selection. A
candidate source is Cosby1984 (sand/silt/clay predictors), but full scientific
review remains pending. The publisher confirms
[DOI 10.1029/WR020i006p00682](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/WR020i006p00682).
The publisher PDF endpoint redirected to the abstract and a discovered AMiner
PDF mirror returned 404. No Cosby specification or measurement bindings were
changed from abstract-only evidence. Other source/data work remains available;
this is not a global blocker.


## Saxton2006 native execution checkpoint

The source-reviewed base function now has a complete measurement contract and
uses the corrected DOI `10.2136/sssaj2005.0117`. Regression expressions remain
unchanged. The registered `saxton2006_h_theta` adapter implements the source's
three branches over 0-1500 kPa, recovers saturation from model reference density,
and rejects invalid anchors. Shared native input validation enforces sand and
clay fractions, clay <= 0.60, organic matter <= 8 mass percent, and sand+clay <= 1.
Reference density is not a measured-density conversion of observed water.

The current catalog contains 18 manifest functions out of 146 implemented
functions, with 128 omitted, 340 missing numeric-input descriptors and 234
missing output descriptors. Metadata completeness does not establish dataset
eligibility. Six Saxton helper functions still need contract migration.

On 987 reviewed HYBRAS horizons, raw predictors permit 607 numerical executions:
604 pass the curve preflight, two have negative air entry, and one has negative
wilting-point water with nonfinite derived parameters. Missing predictors exclude
238 horizons and numeric limits exclude 142 more. These diagnostics preserve
invalid outputs; they are not external accuracy scores. Fine-earth target basis,
predictor protocols/origins and normal-density applicability remain unbound.

Authoritative runs are `local/hybras-saxton2006-native-final` and
`local/hybras-saxton2006-native-wheel`. Complete streams and summaries match byte
for byte. Each reproduction directory archives the matching wheel, script,
specification, generated manifest, source review and checksums. Tracked results:
`evaluation/datasets/hybras_v1.saxton-preflight-summary.json`.
Validation passed 888 evaluator tests, 130 generator tests, 21 public Saxton
regression tests and 25 focused installed-wheel tests; Ruff, ty and generated
file checks passed.

Next review HYBRAS horizon/material labels, reported USDA texture classes and
per-row carbon/density methods for compatible Clapp/Vereecken bindings. Do not
infer fine-earth equivalence from a mineral horizon. Run real grouped selection
only after those contracts match. Final function/ensemble selection and empirical
VG/BC uncertainty qualification remain unfinished.


## Next binding review: Clapp and Vereecken

`review_native_bindings.py` inventories the pinned source workbook without
assigning canonical features or granting eligibility. Reproduce into a new path:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/review_native_bindings.py local/source-review/hybras2018/hybras_v1_2020.zip local/hybras-binding-review-new.json
```

Tracked results are `evaluation/datasets/hybras_v1.native-binding-review.json`.
A strict lexical shortlist of single A/B/E horizon designations contains 378
horizons from 144 profiles in the full archive, before joining the reviewed
positive-pressure cohort. This is a review shortlist, not eligible sample counts.
The NRCS Soil Survey Manual identifies these master horizons as mineral; missing,
compound and annotated names remain outside this initial shortlist. Mineral
horizons do not prove fine-earth preparation or absent gravel. The reported
texture classes still require a source-reviewed crosswalk before Clapp scoring.
All density method cells report only a volumetric ring, leaving Vereecken's
required drying temperature, duration and core size unresolved. Carbon assays
also differ and must be matched per row rather than globally equated.


## HYBRAS Clapp external-validation checkpoint

A source-reviewed overlay now binds reported HYBRAS texture classes to
`clapp1978.UsdaTextureClass` and restricts target material to the strict single
A/B/E mineral-horizon subset. The HYBRAS manual Figure 3 (PDF page 16, printed
page 10) was visually inspected; it pairs Portuguese names with the standard
USDA triangle classes. NRCS Soil Survey Manual Chapter 3 identifies these master
horizons as mineral. The overlay checks exact source/sample/profile identities,
retains feature source cells and preserves all selected pressure/water targets.
It does not infer absent gravel or fine-earth preparation. Missing, compound,
transitional and annotated horizon names remain outside this first subset.
The archive contains Brazilian samples, distinct from Clapp's US calibration.
Unknown rocky-soil status and transfer outside that calibration population
remain applicability limitations, not evidence of broad validated support.

The reviewed positive-head subset contains 378 horizons, 144 profiles, 22 source
reference groups and 2,882 observations. All targets execute successfully;
50 observed monotonicity findings remain in the dataset without deletion.
Sample-balanced errors (prediction minus observation, volume fraction):
ME 0.002573254354125888, MAE 0.05631867785092228,
RMSE 0.0737532960617378, median absolute error 0.0465950410852472.
The declared 2,000-replicate profile bootstrap gives a 95% RMSE metric interval
[0.06738509083752754, 0.08060986217917754]. This conditions on represented
studies and does not provide individual prediction intervals, parameter
intervals, empirical coverage qualification or best-model selection.

Authoritative runs: `local/hybras-clapp-reviewed-final` and
`local/hybras-clapp-reviewed-wheel`. All 11 artifact payloads and four input
files match byte for byte. Matching wheel, experiment/verifier scripts,
source specification and checksums are in each `reproduction` directory.
`evaluation/experiments/hybras/summarize_clapp.py` independently verifies all
5,764 duplicated cohort prediction records against source Table 2 and
parabolic/power equations, using bisection for the wet branch, and separately
checks sample-balanced ME/MAE/RMSE. The initial verifier incorrectly used a
plateau; its failure exposed that mistake before any verification claim.
The production adapter already implements gradual air entry correctly.
Tracked output: `evaluation/datasets/hybras_v1.clapp-validation-summary.json`.
Six focused HYBRAS/Panina tests pass, including source/profile mismatch,
unsupported horizon/class exclusions, unchanged targets and an independently
computed wet-branch point. Ruff and ty checks pass. No core runtime code changed
in this checkpoint; the preceding complete evaluator suite passed 888 tests.

Next identify a scientifically compatible second native candidate. Vereecken
remains blocked by density protocol details (all HYBRAS method cells currently
say only volumetric ring); Saxton requires a separately justified fine-earth
binding. Do not use these blocked candidates to manufacture a multi-model
comparison. The larger objective of real grouped function/ensemble selection
and qualified VG/BC uncertainty remains active.


## Explicit controlled-pressure restoration checkpoint

`evaluation/experiments/hybras/restore_pressure_protocols.py` creates a separate
source-reviewed coordinate view. It requires an exact reviewed HYBRAS method
string with a finite list of controlled kPa regimes, a raw comment explicitly
identifying original kPa and the 10.20 conversion factor, a unique matching
three-significant-figure converted head, identical wide/long water values,
and an exact canonical source/sample/profile/observation join. This is not
nearest-pressure snapping, division of every head by a presumed factor or
interpolation. A ranged method, unsupported source unit or merely nearby
head is insufficient. The original rounded-cm datasets remain unchanged.

The view retains 1,465 water observations from 254 horizons, 224 profiles and
four source reference groups. It provides 254 exact original-regime observations
at each of 10, 33 and 1500 kPa. The separate pressure audit reports support for
Gunarathna set-1 outputs and Saxton 33/1500 outputs; zero-head saturation remains
unsupported and available-water differences have no single pressure anchor.
The target material remains unspecified and predictors remain unbound, so
native scoring eligibility is explicitly not granted. In particular, pressure
support alone must not bypass fine-earth or analytical-method requirements.

Authoritative source and isolated-wheel outputs are
`local/hybras-controlled-kpa-first` and `local/hybras-controlled-kpa-wheel`.
All three complete output documents reproduce byte for byte. Each archives
the matching script, pressure-audit script, wheel and checksums in `reproduction`.
Canonical dataset SHA256:
`760f3bfd997264d811fbcffca241bb84a684edd9c33a6f4b327718701d2f5c5b`.
Every retained target record was independently checked equal to its parent
except the explicitly restored pressure coordinate. Review sidecars retain
both coordinates, original comments and method/wide/raw source cells.
Tracked summaries are `hybras_v1.controlled-pressure-summary.json` and
`hybras_v1.controlled-pressure-support.json` in `evaluation/datasets`.

Twelve new tests protect explicit regime matching, original-unit requirements,
exact coordinates, source-target identity, wide/long agreement and unchanged
water values. A temporary nearest-integer matching mutation failed the tests
for `nextafter(337,+inf)` and 336.6; the original script was restored byte for
byte. All 17 focused pressure/support/Clapp tests then passed; Ruff and ty
passed. No core runtime or scientific regression expressions changed.

Next review material preparation and predictor protocols for these 254 horizons,
and independently revisit whether the existing Gunarathna target material
contract is directly supported by its source measurement procedure. Do not
relax it to obtain more rows without source evidence. Existing Clapp external
scores and earlier VG/BC fits still belong to their original datasets; they
are not results for this restored-coordinate view. Real multi-function grouped
selection and VG/BC uncertainty qualification remain required.


## Gunarathna2019 and single-pressure selection checkpoint

The author's primary dissertation Chapter 6, Section 6.2 (printed page 96),
identifies the 2019 article and separates analytical texture samples from
undisturbed retention cores (54-mm diameter, 30-mm height) and density cores
(54-mm diameter, 60-mm height). The retention target was corrected from
`fine_earth/bulk_volume` to `soil/bulk_volume`; this does not change the prepared
fine-earth texture denominator. The remaining eight equations now have complete
measurement descriptors. All eleven regression expressions, statuses and
verification cases are unchanged. Source review is recorded in
`evaluation/datasets/gunarathna2019.measurement-review.json`. The primary text
was indexed from the author's university repository; direct PDF retrieval failed,
so no local PDF hash or visual inspection is claimed. The existing `g/cm3`
notation is registered as a density-unit alias.

Current inventory: 26 manifest functions of 146 implemented, 120 omitted,
328 missing numeric-input descriptors and 226 missing output descriptors.
Both meta-v3.3 readiness matrices, the raw-binding readiness summary and pressure
support reports were refreshed. Pressure support is not scoring eligibility.

The technical single-pressure selection gap is now implemented.
`SinglePressureLossPlan` / `single_pressure_mse_v1` score squared water-content
error at one exact declared pressure. Missing or nearby observations cannot
supply it. Zero pressure is allowed without constructing a log integral; the
old positive-width log-pressure contract remains unchanged. Registered constant
pairs use `constant_convex_pair_single_pressure_v1`, which must match the loss.
Atomic and ensemble strategies are assessed separately inside the existing
grouped nested validation. Pressure-transition learners, empirical domains and
additional uncertainty protocols are explicitly outside this first point-loss
run contract. The generic evaluator is `evaluate_selection_loss`; the original
log-pressure evaluation API is retained.

The standalone fixture builder is
`evaluation/examples/synthetic_single_pressure/build.py`. It restricts the
independent Beniaich two-pressure fixture to 33 kPa without generating targets
from native predictions. Three outer folds and two inner folds recover weights
0.25/0.75; altering outer test targets leaves training choices and weights
unchanged. This is technical validation, not evidence of real-soil accuracy.
Authoritative source and wheel runs: `local/single-pressure-source` and
`local/single-pressure-wheel`. All 15 payload files and three input documents
match byte for byte. All 64 installed package/schema files match source.
Each reproduction directory contains the matching wheel, generated manifest,
builder and dependent fixture documents with recursive checksums; use the
nested `examples/synthetic_single_pressure/build.py` snapshot for replay.
Validation: 917 full evaluator tests, 130 generator tests, 33 public Gunarathna
tests and 11 focused installed-wheel tests pass. Deterministic generation,
Ruff, ty and diff whitespace checks pass. The full suite preceded only
nonbehavioral docstring edits and strengthening existing assertions.

A further primary review of Nebel2010 found one 1-ha, 10-m-spaced, 100-point
sampling grid. These points are not demonstrated independent profile-level
population replicates. The 100-row Nebel and 99-row Parfitt-only HYBRAS groups
share a byte-identical Parfitt dissertation citation despite having different
reference-pair source IDs. This is recorded in
`evaluation/datasets/nebel2010.measurement-review.json`, with publisher PDF hash
`6308bea9b5af4f453ade4cc9f0c5398a45d8c3092fd7753d01fda0bca762a904`.
The source also reports 50x30-mm rings, Day pipette analysis with NaOH, and
Walkley-Black carbon. Generic pipette labels do not by themselves confirm
Gunarathna sand-preparation equivalence, and the ring geometry does not match
its density predictor. Gravimetric/volumetric source lineage needs review.

Next confirm exact sand preparation and target lineage for a declared real
subset, and resolve validation units across shared source citations and spatial
sampling before real nested selection. Do not treat profile counts or hashed
reference-pair IDs as proof of independence. Real model/ensemble winners and
VG/BC uncertainty qualification remain unfinished.


## Shared-reference source groups and source-level Clapp uncertainty

`evaluation/experiments/hybras/group_sources.py` now creates a separate canonical
source-group view. It computes exact nonempty-reference connected components
on the full pinned workbook before projecting a subset, so an omitted source
can still connect two selected sources. No fuzzy citation normalization is
performed. Source/sample/profile identities are checked against the workbook.
Only source-group keys change; original keys remain in a checksum-bound sidecar.
Every sample and observation was restored exactly to its parent in verification,
including all pressures, water values, features and quality flags.

Authoritative views and counts:
- `local/hybras-reviewed-linked-final`: 987 samples, 7,054 points; 35 source IDs
  become 34 reference components.
- `local/hybras-controlled-linked-final`: 254 samples, 1,465 points; four source
  IDs become three components. The Nebel/Parfitt block contains 199 samples.
- `local/hybras-clapp-linked-final`: 378 samples, 2,882 points; all 22 source IDs
  remain separate under exact-reference connectivity.

The controlled view fails the declared three-outer/two-inner split with at least
two training groups per partition. The full reviewed and Clapp views pass this
identity-only feasibility check. Neither outcome proves population independence
or predictor eligibility. Use source grouping on these views; profile grouping
would split reference blocks again. The controlled view reproduces byte for
byte under `local/hybras-controlled-linked-wheel`. Matching scripts and wheels
are archived under `reproduction`; the tracked count-only report is
`evaluation/datasets/hybras_v1.source-group-summary.json`.

Clapp was rerun with a reviewed source-group sidecar and whole-source bootstrap
rather than profile bootstrap. The helper rejects a different cohort, duplicate
review identities, mismatched profiles or source components requiring an
unapplied merge. Source and wheel runs are
`local/hybras-clapp-source-bootstrap-final` and
`local/hybras-clapp-source-bootstrap-wheel`; all 11 payload files and five input
files match byte for byte. Independent source-equation verification passes for
all predictions; the four descriptive error metrics exactly match the earlier
profile-bootstrap experiment. RMSE remains 0.0737532960617378, while the 95%
metric interval over 22 source blocks is
[0.06264537542628838, 0.08477170261973371]. Study independence and interval coverage
remain assumptions, not established by distinct references. This is not an
individual prediction interval or best-function selection. The new tracked
summary is `evaluation/datasets/hybras_v1.clapp-source-bootstrap-summary.json`;
the historical profile-bootstrap summary is retained separately.

An editable-install provenance gap was also corrected: hashing the Python
package root can omit the loaded extension, which is outside that root here.
Future run manifests record `ptfkit_native_binary_filename` and
`ptfkit_native_binary_sha256` separately. The actual binary SHA256 is
`a8e9522f4cd1e9cf5878d3928d0cbd9c1705c7b66cdf410be4d4acd94793eca9`.
Both source-bootstrap reproduction directories additionally archive an exact
26-function ptfkit Python/native snapshot ZIP with source-root and binary hashes.
Those runs precede the new manifest field; their matching old evaluator wheel
is retained. The field itself is verified in the new isolated source-groups
wheel. Validation passes 924 full evaluator tests, 22 focused installed-wheel
tests, Ruff and ty. No numerical regression expressions changed.

The Cosby logarithmic evidence gap now has a concrete next path. The official
ESCOMP/CTSM repository at commit
`350a14d5ba1a7f782223d72df570ea41617298d3` explicitly names a Table-5 implementation
in `src/main/FuncPedotransferMod.F90`, lines 83-103. It back-transforms the exact
published expressions with base 10, converts suction cm to mm, and uses the
rounded inch/hour-to-mm/s conductivity factor. The saved file's Git blob SHA1
is verified as `f775b688c446174db777a5922aa68a9b364e3c72`. Local snapshots and the
updated `cosby1984.measurement-review.json` distinguish this software
corroboration from an original-paper visual review. Cosby formulas, units,
manifest entries and bindings have not yet been changed.

Next migrate explicit logarithmic units/roles and register a verified Table-2
USDA-class midpoint derivation. Derived coordinates must not masquerade as
measured sand/silt/clay. Review the dry power-curve support without inventing a
wet branch. A target-free pressure-grid audit found 377 of the 378 Clapp curves,
covering all 22 source groups, contain both reported heads 102 and 15300 cm
(10.002783 and 1500.41745 kPa); that is a promising declared dry comparison
domain, not exact 10/1500-kPa support. Keep original units and all exclusions.
Real multi-function selection and qualified VG/BC uncertainty remain required.
