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
