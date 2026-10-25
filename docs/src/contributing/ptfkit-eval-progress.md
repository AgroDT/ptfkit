# ptfkit-eval extended implementation progress

Historical session window ended at **23:28 UTC on 2026-10-23**
(02:28 Europe/Moscow on 2026-10-24). Subsequent work follows the active goal
continuation requested by the user.
Latest verified component checkpoint: **740 passing tests**.

Current real-workbook checkpoint: **1,036 observations across 109 master
identities**, including 549 volumetric and 487 gravimetric observations. Six
complete source rules and five mandatory partial row reviews are active. Of
719 explicit exclusions, 644 have blocked physical rules, 48 have stale cached
identities, six have ambiguous master matches, 17 have unreviewed pressures,
three are non-observation table statistics, and one has missing water content.
Predictor method compatibility remains unresolved. Repeated measurements do not
establish independent soil samples.

## Session contract

Started 2026-10-23 at 08:15 UTC (11:15 Europe/Moscow). The user authorized
continued independent implementation for the available five-hour window,
ending no later than 13:15 UTC (16:15 Europe/Moscow). Primary-source review is
explicitly deferred because the input file is on another computer.

This file is the portable continuation record. It deliberately lives outside
the Git-ignored `local/` directory. Code, tests, and documentation changes are
uncommitted: transfer the complete worktree diff and new files together before
continuing on another computer. Do not copy only this log.

## Starting state

- The previous slices implement canonical retention metrics, maximal/common
  cohorts, and whole-cluster percentile metric confidence intervals.
- Last verified component baseline: 176 tests, Ruff 0.16.1 lint and format,
  ty 0.0.71, and `git diff --check` passed.
- The worktree already contains those intentional changes. Preserve them.
- Primary workbook source-rule blockers remain. No real-data PTF prediction
  accuracy result is authorized by the current scientific evidence.
- Read `ptfkit-eval-handoff.md`, `ptfkit-eval-plan.md`, `development.md`, and
  `AGENTS.md` before changing scientific or generated contracts.

## Active continuation

Implement a portable, versioned run contract and execution pipeline with
explicit measurement/input binding, observations, eligibility, prediction
traces, maximal/common metrics, cluster confidence intervals, reproducibility
hashes, machine-readable artifacts, and a human-readable report. Protect the
whole path with independent synthetic examples. Then continue independent
roadmap slices, recording each verified checkpoint here.

## Verification commands on this computer

Run from `targets/ptfkit-eval`:

```powershell
& C:/Users/KT/AppData/Local/mise/installs/ruff/0.16.1/ruff.exe check
& C:/Users/KT/AppData/Local/mise/installs/ruff/0.16.1/ruff.exe format --check
& C:/Users/KT/AppData/Local/mise/installs/ty/0.0.71/ty.exe check
.venv/Scripts/python.exe -m pytest
```

On a configured computer use `mise run eval:sync` and `mise run eval:verify`.
The local machine has the pinned executables, but `mise` is absent from PATH.

## Checkpoints

### 08:15 UTC: session initialized

Reviewed the current handoff, roadmap, plan schema, candidate resolver, and
predictor audit types. Confirmed the `local/` ignore rule and created this
portable log before implementation. No new executable changes yet.

### First run-pipeline draft

Added canonical dataset/run JSON Schemas, immutable dataset and run-plan
loaders, exact-byte SHA-256 input binding, scientific feature binding with
unit conversions and domain gates, a candidate/observation execution matrix,
sample coverage including missing targets, cohort/bootstrap integration,
deterministic artifact publication and integrity checks, and CLI commands
`inspect`, `normalize`, `plan`, `run`, and `report`.

The composite executor now prepares only routed members, so unavailable inputs
of inactive members do not exclude unrelated pressure points. Derived and
estimated features remain excluded until registered derivations can be checked;
no scientific source rule was promoted.

Initial end-to-end tests: eight passed against the real public Clapp function,
including hand-calculated predictions/errors, lineage, exclusion accounting,
repeatable artifacts, corruption rejection, and CLI execution. Type/lint
cleanup and additional scientific gate tests are in progress. This is not yet
a completed verification checkpoint.

### 08:30 UTC: portable run pipeline verified

Full component verification passed: 200 tests, Ruff lint, Ruff formatting,
and ty. The new pipeline has independent numeric descriptor/quantity/basis/
method/particle-boundary gates, converted-input domain-boundary regressions,
inactive-composite-member coverage, real-public-function synthetic predictions,
blocked-target/input handling, reproducible artifacts, byte-checksum drift
rejection, artifact tamper detection, and CLI tests.

Run directories include both the original source run plan and a rewritten
portable run plan with local canonical snapshots and corrected checksums.
Replaying the saved run reproduces its predictions and cohorts exactly.
Machine-readable records include explicit eligibility/status fields.

A test found an actual converted inclusive-boundary defect: 0.052 mass fraction
was rounded below the required 5.2 percent. Shared affine unit conversion now
uses 40-digit decimal arithmetic on the declared decimal values and coefficients,
then returns a float; no domain tolerance was widened. All existing checks pass.

Next: support fixed-pressure point outputs so the three public Gunarathna
contracts can run under the same pipeline, then complete examples/documentation
and continue independent quality/selection/fitting slices.

### Portable run and fixed-output checkpoint: 216 tests passed

Added `function_point`/`fixed_output` resolution, scalar public-output execution,
manifest-derived pressure support, and explicit pressure/method mismatch gates.
All three Gunarathna Set 1 public functions execute at their declared pressures;
unmatched pressures are excluded without interpolation. Fixed outputs at
different pressures retain empty common cohorts rather than being compared on
different observations.

Canonical nonsynthetic records now require a declared source-file identifier,
filename, and SHA-256 in addition to cell locators. JSON/YAML duplicate keys,
nonfinite values, cyclic aliases, and YAML merges fail document validation.
The artifact manifest records the installed ptfkit package/binary content hash
and NumPy version as well as evaluator source and manifest hashes.

A quality-gate mutation was applied only in memory: ignoring submitted target
quality flags made the regression test fail at the expected eligibility reason.
The production file was verified unchanged. Full unmodified component checks
then passed: **216 tests**, Ruff lint/format, and ty.

The CLI entry point was installed through `uv sync --frozen --all-groups`.
The committed-file candidate example lives at
`evaluation/examples/synthetic_retention/`: six sources, twelve samples, sixty
synthetic observations, Clapp/Vereecken atomics, and one fixed blend. Its plan
validated and executed successfully with the real public package and the full
2,000-replicate bootstrap. Local output is ignored under
`local/ptfkit-eval-demo/run-1`; copy the whole run directory if needed. The
example README gives commands to recreate it on another computer. Package
README documentation was updated.

Next independent work: curve quality diagnostics and deterministic grouped
outer/inner validation for fixed atomic and registered ensemble candidates.

### Nested fixed-candidate selection checkpoint: 244 tests passed

Added noncorrecting canonical curve diagnostics (physical bounds and adjacent
monotonicity), optional `curve-quality.json` artifacts, identity-only nested
source/profile folds with explicit fallback and group-count gates, and the
registered `log10_trapezoid_mse_v1` per-sample selection loss. The loss requires
exact observed domain endpoints and never interpolates missing endpoints.

`select_fixed_retention_candidates()` now selects atomics and registered fixed
ensembles independently from inner-held-out losses, locks each choice, and
assesses it on untouched outer groups. Coverage denominators include missing
targets and failed inputs. Output reports strategy performance, selected-model
stability, fold provenance, and explicit insufficient evidence; it does not
choose a final function by sorting outer errors. Learned/tuned candidates are
rejected by this fixed-only API. The run schema accepts a fully declared
optional selection contract and persists `selection.json` plus report results.

Independent tests include a held-out winner different from the inner-selected
candidate. An in-memory mutation leaked outer groups into inner scoring; that
test changed the selected candidate and failed as intended. Production files
were verified unchanged. Full component verification subsequently passed:
**244 tests**, Ruff lint/format, and ty.

Next: finish the example/docs for selection, then implement independent
approximation-family fitting with explicit parameter bounds, identifiability,
failure states, and clearly labeled parameter uncertainty. Dataset-source review
remains deferred. Do not enable the stored Kokareva parameters without evidence.

### 10:19 UTC: approximation fitting integrated; final checks in progress

NumPy and SciPy were added through `uv add`, updating the component lockfile
and installing SciPy 1.18.1 in this environment. New versioned families cover
Mualem-constrained van Genuchten, reduced m=1 van Genuchten, Brooks-Corey, and
the reviewed Clapp gradual-air-entry variant. Their kPa parameter conventions
are explicit and do not establish conventions for workbook-supplied parameters.

The fit plan requires physical parameter boxes, interior initial values, seed,
minimum log-pressure span, deterministic restarts, convergence/evaluation
limits, rank/conditioning gates, and confidence assumptions. The initial
implementation requires nonoverlapping theta_r/theta_s boxes and rejects
boundary, nonidentifiable, competing, and nonphysical solutions. It never falls
back to another family. Accepted fits expose separate local parameter intervals,
mean-curve confidence intervals, and conditional future-observation prediction
intervals under local linearity and iid homoscedastic residual assumptions.
Extrapolation outside the observed pressure extent is disabled.

Eleven independent fitter tests pass, including recovery for all four families,
an analytically derived Jacobian covariance oracle, df=1 Student-t interval
identities, rank-deficient plateau rejection, and optimizer/data failures.
A run-level test also passes: reference fitting remains independent of blocked
PTF predictors, excludes flagged observations, preserves missing-target failures,
writes `approximations.json`, and replays exactly from saved snapshots.
The full component recheck and README/roadmap updates are the next action.

### Fitting checkpoint: 256 tests passed

Full verification passed after integration: **256 tests**, Ruff lint/format
(58 Python files), and ty. A memory-only mutation replaced residual degrees
of freedom with observation count; the independent uncertainty test failed at
the expected residual-variance assertion. Production files were unchanged and
the complete unmodified suite passed afterwards.

The run schema now registers approximation policies, source/sample fits remain
separate from PTF candidates and nested selection, and saved approximation
artifacts replay exactly. Package documentation and the roadmap were updated.
CI now has a dedicated evaluator job on Python 3.11 and 3.13, including lock
validation, component verification, and wheel build. Pre-commit adds evaluator
lock/sync/type checks. Those remote jobs have not been executed locally; the
verified local interpreter is Python 3.13.12 on Windows.

Next: verify wheel contents and a transferable checkpoint, then continue
independent PTF prediction-interval and applicability-domain protocols while
keeping them separate from reference-family conditional uncertainty.

### Portable build and example verification

`uv build --wheel` succeeded. The wheel was installed without dependencies into
`local/ptfkit-eval-wheel-smoke` and imported from that installed path. It contains
the CLI entry point, all four JSON Schemas, and all approximation families;
the installed copy resolves the standalone selection example successfully.

The expanded example with nested selection and all four approximation families
executed successfully into `local/ptfkit-eval-demo/run-2`, retaining both accepted
and failed fits and their reasons. Integrity verification of the complete run
passed. A transferable worktree checkpoint is being written to
`local/ptfkit-eval-checkpoints/256-tests-fitter.zip`.

To resume from that archive on another computer, check `manifest.json` for the
base Git commit, unpack into a temporary directory, apply `changes.patch` to
the matching checkout (first use `git apply --check`), and copy the contents of
`new-files/` into the checkout. Preserve any independent local changes first.
Then run `mise run eval:sync` and `mise run eval:verify`. The archive excludes
ignored papers, workbooks, environments, caches, and local run outputs.

Next independent implementation: grouped split-conformal PTF prediction
intervals with disjoint training/calibration/test groups and explicit finite
calibration-evidence failures. These remain separate from approximation-family
conditional prediction intervals.

### 11:00 UTC: grouped PTF prediction intervals integrated

The new `fixed_group_max_split_conformal_v1` protocol uses disjoint explicit
training/calibration/test roles and complete calibration grids. Each independent
group contributes one maximum absolute residual across its samples and registered
pressures. The exact finite rank is ceil((G+1)*confidence); an out-of-range rank
returns insufficient evidence, never an interpolated finite quantile. Whole-group
exchangeability and a fixed prediction rule/design are explicit assumptions.

`predict_retention_grid()` uses sample features and registered pressures only,
without accepting test observations. An end-to-end regression proves missing or
flagged/changed test targets leave forecasts and prediction intervals identical.
The run schema, loader, pipeline, optional `prediction-intervals.json`, report,
and replay are wired. Nine independent calibration tests plus the pipeline test
pass; full component verification is the next action.

Two additional regressions now pass: zero-weight blend members do not require
inputs, and a nonfinite PTF output remains an explicit exclusion that can still
be published as strict JSON with an auditable textual failure trace.

### Paused checkpoint: 269 tests passed

Work stopped at the user's explicit request on 2026-10-23, after approximately
2 hours 47 minutes of the requested five-hour window. No further implementation
is scheduled in this session. All changes remain uncommitted.

The final complete verification passed: **269 tests**, Ruff lint, Ruff format
(61 Python files), and ty, using Python 3.13.12 on Windows. This supersedes the
pending-verification statement above. Remote CI on Python 3.11/3.13 has not run.
The wheel smoke test and `256-tests-fitter.zip` predate the conformal additions;
they must not be treated as verification of the latest wheel contents.

The current transferable checkpoint is
`local/ptfkit-eval-checkpoints/269-tests-paused.zip`. It uses the same restore
procedure described above and includes this journal. Transfer the archive
explicitly: `local/` is ignored by Git. The progress and handoff documents are
outside that ignored directory, but must also be committed or copied before
they become available on another computer.

Resume with the following priorities:

1. Review the current changes and document the conformal protocol with a
   standalone example; rebuild and smoke-test the latest wheel.
2. Implement training-input-only empirical applicability domains and composite
   seam diagnostics. Reported applicability is still `not_assessed`.
3. Extend validation to learned ensembles only with inner-fold training and
   outer-training refits; add paired comparisons/strategy uncertainty as needed.
4. After the deferred source review, finish explicit metadata and canonical
   workbook mapping, then run a scientifically eligible real-data pilot.

The four reference families, fixed-candidate nested selection, descriptive
cluster intervals, and fixed-rule conformal intervals are implemented, but
this does not complete the full roadmap. Fitting uncertainty currently uses a
local linear IID model; learned ensemble training is not implemented. Only five
of 146 implemented functions have evaluation-ready manifest contracts. The real
workbook currently yields no scientifically eligible predictions under these
contracts; the working demonstrations are synthetic. Source review, missing
contracts, and unit/method ambiguities remain explicit blockers.

Planning estimate, not a completion guarantee: allow roughly 20-40 focused hours
for a limited real-data pilot after source contracts become available, including
review and integration. The full roadmap, learned selection, broad function
coverage, and further numerical review can require 60-120 or more hours.
Primary-source verification time is additional and depends on available files.

### Resumed checkpoint: standalone conformal example and current wheel

Resumed at the user's request on 2026-10-23. The worktree was clean; earlier
implementation checkpoints are now part of the repository baseline.

Added `evaluation/examples/synthetic_conformal/` with nine calibration sources,
one unlabelled test source, explicit source-local lineage, byte-bound input
documents, and an independently calculable 90% group-max interval. The README
explains the exact rank, missing-grid failures, exchangeability assumptions,
and the distinction from other uncertainty and applicability outputs. Package
documentation now describes the implemented conformal API and run artifacts.

The example regression protects fixed numeric bounds and the test-source
forecast roster through the public run API. Its oracle is the published Clapp
sand curve at saturation and half saturation, with declared residual offsets
0.01 through 0.09. A wrong quantile rank or discarded calibration maximum
would change the expected 0.09 half-width; mutation assessment was reasoned
without modifying production code.

Verification on Python 3.13.12 / Windows:

- `uv sync --frozen --all-groups` restored the missing locked SciPy dependency.
- Ruff 0.16.1 lint and format checks passed (61 Python files); ty 0.0.71 passed.
- The first default-temp pytest run had 216 passes and 54 setup permission
  errors. A rerun with explicit workspace temp storage and elevated execution,
  `.venv/Scripts/python.exe -m pytest --basetemp ../../local/pytest-eval-resume -q`,
  passed all **270 tests**.
- CLI execution of the standalone example succeeded into ignored
  `local/synthetic-conformal-resume`.
- `uv build --wheel` passed after granting access to the external uv cache.
  The wheel was installed without dependencies into ignored
  `local/ptfkit-eval-wheel-resume`; importing that installed copy, executing
  the example, checking its numeric half-width, and verifying the CLI-created
  report's artifact integrity all passed.

Next continuation: training-input-only empirical applicability domains and
composite seam diagnostics. These need explicit versioned scientific contracts
and independent behavioral tests. Primary-source review remains deferred;
real-workbook scoring and learned ensembles remain blocked or unimplemented
as described above. No new scientific source rule was promoted.

### Empirical input domains and composite transition checkpoint: 290 tests

Implemented `training_input_envelope_v1`: explicitly disjoint training/test
source or source-local profile groups, a complete-case training-group gate,
inclusive numeric minima/maxima in manifest units, and canonical categorical
sets. Every composite member retains its own bounds, complete/excluded training
vectors, normalized input lineage, group count, and test-input assessments.
Targets are not accessed, test inputs cannot change training bounds, and
missing profiles never trigger implicit fallback. The API is
`assess_retention_applicability()` with `EmpiricalDomainPlan`; optional run
registrations write `empirical-domains.json` and report evidence/status counts.

Implemented `exact_transition_member_contrast_v1` through
`diagnose_composite_seams()`. It evaluates both members at each hard switch and
both blend endpoints, even at zero routing weight, for every sample including
those without targets. Canonical values, right-minus-left differences, input
and prediction traces, and failures are retained in `composite-seams.json`
and a report table. Ordinary routed eligibility and predictions are unchanged.
Hard-switch differences imply jumps only for continuous members; blend endpoint
contrasts are member disagreement, not jumps in the blended curve.

The empirical envelope describes marginal input support, not joint support,
predictive accuracy, literature-reported applicability, uncertainty coverage,
or validated pressure support. Its registered roles are independent of nested
selection folds. Automatic fold-specific domains, error stratification, and
learned ensemble training remain future work. These diagnostics do not gate
scoring, selection, or prediction intervals. Primary-source review and eligible
real-workbook scoring remain deferred/blocked.

Verification on Python 3.13.12 / Windows:

- Added 20 behavioral tests for numeric conversion/bounds, constant predictors,
  categorical support, complete-case exclusion, group multiplicity, source-local
  profiles, missing-profile rejection, role validation, input/target/order
  independence, member-specific composite domains, seam values/signs, missing
  inactive-member inputs, and artifact replay.
- Independent numeric seam expectations use the specification's mean-input
  Vereecken verification parameters and reviewed curve equations. Envelope
  expectations use declared training inputs, including mass-fraction conversion.
- In-memory mutations introducing test groups into training bounds and reversing
  seam subtraction both failed the focused tests at the expected assertions.
  Mutation probe code required a future-annotations prefix on the second attempt;
  no production file was edited by either probe.
- Ruff 0.16.1 lint/format (65 Python files) and ty 0.0.71 passed.
- `.venv/Scripts/python.exe -m pytest --basetemp ../../local/pytest-eval-domains-verified -o cache_dir=../../local/pytest-cache-domains -q`
  passed **290 tests**. Workspace-local temporary/cache paths avoided the earlier
  default-temp permission errors.
- The expanded synthetic CLI run succeeded into ignored
  `local/retention-domains-seams-demo`. Report integrity verification and replay
  matched all three empirical registrations and 24 seam records exactly.
- `uv build --wheel` passed with external-cache access. Installed without
  dependencies into `local/ptfkit-eval-wheel-domains`, the new wheel successfully
  loaded the updated schema and executed domain/seam APIs against the example.
- `git diff --check` passed. Changes remain uncommitted; preserve earlier
  conformal-example work along with this continuation.

Next: integrate training-only domains with each nested fold and report error
strata without changing candidate selection; then extend validation to learned
ensembles with inner-fold training and outer-training refits. Paired strategy
uncertainty remains pending. Scientific source review still requires the
deferred workbook/papers and must not be replaced by value-based inference.

### Goal continuation: nested input domains, 299 tests

The user requested ongoing goal-based work until the available token budget is
exhausted. The active goal continues beyond this checkpoint; primary-source
review remains deferred.

Implemented optional `selection.empirical_domains` registration with
`nested_training_input_envelope_v1` and `all_registered_members` sample labels.
After fixed nested choices are locked, each inner/outer training partition fits
its own member envelopes. Effective split grouping, including explicit source
fallback, is retained. Validation/test inputs cannot expand their own envelope.
Every registered candidate is diagnosed; selected outer candidates are flagged,
not reselected. Four strata retain full sample denominators, common-cohort
descriptive metric confidence calculations, and exact-grid log-pressure losses.
Input failures and insufficient training evidence remain explicit. Diagnostics
are written to `nested-applicability.json` and a dedicated report section.

The all-member rule is conservative and independent of observed target grids.
Metric bootstrap intervals condition on retained folds/envelopes and do not
repeat fitting/selection. Mean log-pressure losses have no interval here.
The synthetic example now enables both standalone and nested domain protocols.

Nine new behavioral tests protect exact inner/outer training roles, categorical
holdout novelty, hand-calculated 1/8 and 1/4 residual metrics and losses, missing
target denominators, no feedback into choices, split failure, source fallback,
all-member status priority, and artifact replay. An in-memory mutation changing
all-member support to any-member support failed the composite test at the
expected inside/outside assertion; production files were not modified.

Full verification passed: **299 tests**, Ruff 0.16.1 lint/format (67 Python
files), and ty 0.0.71. Pytest used workspace-local basetemp/cache directories.
Next goal slice: paired candidate differences with whole-cluster resampling,
explicit common-cohort contracts, independent oracles, and artifact integration.

### Goal continuation: paired candidate differences, 319 tests

Implemented `bootstrap_paired_retention_errors()` with
`paired_cluster_percentile_linear_v1`: strict identical comparison grids and
scientific contracts, one shared whole-cluster draw per replicate, preserved
sample weights/multiplicity, and left-minus-right metric estimates/percentile
bounds. Nonlinear RMSE and median differences follow separate replicate metric
calculations. Missing evidence retains reasons, with explicit profile/source
fallback. Input order does not change results or global random state.

Optional `paired_comparisons` run registrations validate distinct known
candidates and unique unordered pairs, preserving the registered orientation.
They use the exact run-wide common grid across every declared candidate,
including empty ones. `paired-comparisons.json` retains exact rows, estimates,
and intervals; the report explains their direction and limitations. These are
unadjusted descriptive comparisons and never feed selection or claim nested
strategy uncertainty. The synthetic example now registers two pairs.

Twenty new tests include exhaustive AA/AB/BA/BB cluster draws with unequal
sample/pressure counts, opposite residuals whose absolute metric differences
must be zero, constant-reference nonlinear metric bounds, orientation reversal,
order/global-state behavior, invalid scientific contracts before evidence gates,
explicit fallback, empty-third-candidate protection, registration validation,
and public pipeline/artifact replay. A memory-only mismatched-cluster mutation
failed the focused test at the expected interval bound.

Full pytest passed **319 tests**. Lint and ty passed during focused verification;
the full final lint/format recheck follows documentation updates. The expanded
CLI example ran into ignored `local/retention-nested-paired-demo`.
Goal work continues: inspect and verify the combined changes, then implement
the first narrowly registered learned-ensemble training protocol without
reusing outer targets or tuning choices from outer errors.

### Goal continuation: learned convex ensembles and stable losses, 346 tests

Implemented `nested_convex_pair_selection_v1` with explicit fixed candidate,
fold, coverage, and exact-grid loss contracts plus registered
`constant_convex_pair_log_pressure_v1` trainable ensembles. Only one constant
convex weight on two atomic curve candidates is fitted. Each inner training
partition minimizes the same sample-balanced log-pressure trapezoid MSE;
inner validation locks the candidate, and a selected learned ensemble is
refitted on all outer training groups before untouched outer testing. Fixed
composites may compete but cannot be trainable members. Fixed-pressure point
outputs, unknown/colliding members, and unsupported nested-domain registrations
inside this first learned protocol are rejected.

Weights 0 and 1 are valid constrained optima. Complete sample/pressure grids,
usable training groups, training coverage, and positive mean squared member
contrast are explicit evidence gates. Degenerate or nonfinite training
objectives remain failed fits without arbitrary weights or post-refit fallback.
Artifacts retain inner training fits, disjoint validation predictions/losses,
outer refits/predictions, candidate choices and strategy stability. Optional
`learned_selection` run registration writes `learned-selection.json` and a
separate report section; it leaves ordinary candidate predictions, fixed
selection, domains, and conformal protocols independent.

Twenty-three learned unit/integration cases protect the independently derived
quarter weight, valid boundary optima, identifiability failures, sample and
log-pressure weighting, recomputation on all outer training samples, training
coverage/group gates, nonfinite contrasts, role validation, pipeline replay,
and unchanged fixed scoring. A memory-only outer-refit leakage mutation changed
the fitted weight from 1/4 to 1/2 and failed the expected test assertion.

Extreme-value regression tests exposed two existing numerical defects in the
shared log-pressure loss: finite squared errors could overflow before final
normalization, and distinct adjacent large pressures could have identical
rounded logarithms, yielding division by zero. Both regressions failed before
their fixes. Normalization now precedes summation; close pressure gaps use
`log1p` while wide gaps retain a difference of logarithms. Finite nonnegative
sample losses use an overflow-safe mean with a scaled fallback; the ordinary
path preserves subnormal values. Fixed selection, learned selection, and nested
strata share this averaging contract. This does not widen domains, interpolate
endpoints, or clip predictions.

Verification: **346 tests**, Ruff 0.16.1 lint/format, and ty 0.0.71 passed in
the evaluator environment. One ty invocation accidentally used the repository
root and reported unrelated environment/import errors; rerunning from
`targets/ptfkit-eval` passed. The expanded real-public-function synthetic CLI
run lives in ignored `local/retention-learned-stable-demo`. The current wheel
built successfully and was installed without dependencies into ignored
`local/ptfkit-eval-wheel-goal`. Integrity/exact replay checks for all three new
artifact families passed against that installed copy. That wheel predates the
subsequent learned-applicability integration below.

Remaining scientific scope: no learned pressure boundaries/nonlinear gates,
weight-uncertainty estimates, full selection-process confidence intervals,
learned-ensemble conformal calibration, or learned-fold applicability integration
is claimed. There is no final trained deployment model or real-data accuracy
claim. Primary-source review remains deferred. The active goal continues;
next inspect the combined contracts and add the next justified independent slice.

### Goal continuation: learned-fold applicability, 352 tests

Optional `learned_selection.empirical_domains` now diagnoses every inner
candidate and only the already locked outer choices. It reuses the same
training-only envelopes, conservative all-member labels, common-grid stratum
metrics, loss coverage, and conditional metric confidence calculations as the
fixed protocol. Trainable pairs combine their atomic constituents' envelopes
with explicit `left:` and `right:` member identities, including zero-weight
constituents. No new weights are fitted and no candidate is reselected.
Results persist to `learned-applicability.json` and a dedicated report section.
The older unsupported `fixed_selection.empirical_domains` nesting is still
rejected; use the learned registration's own diagnostic field.

Six additional behavioral tests protect exact inner/outer roles, hand-derived
training sand bounds and input labels, diagnostic group gates without changes
to weights/choices, held-out predictor shifts without envelope expansion,
target-independent labeling, and artifact integrity/replay. They exercise the
shared all-member combiner already challenged by the earlier in-memory mutant.
Optional artifact publication now uses a single filename/value registry so new
diagnostics do not require repeated serialization branches.

Full verification passed: **352 tests**, Ruff 0.16.1 lint/format (75 Python
files), and ty 0.0.71. The expanded CLI run is in ignored
`local/retention-learned-domain-demo`; all 30 learned-domain frames passed
integrity verification and exact replay. The latest wheel was rebuilt and
installed without dependencies into `local/ptfkit-eval-wheel-learned-domains`.
That installed copy loaded the updated schema, executed the new learned-domain
protocol, verified the saved report, and reproduced all 30 frames exactly.

The active goal remains in progress. Next useful slices are learned hard-switch
boundaries from an explicitly registered finite training grid, with independent
identifiability/coverage gates and the same inner fitting/outer refitting rules,
then target-free diagnostics at fitted seams. Weight/boundary uncertainty and
full selection-process uncertainty require separate protocols; do not relabel
the existing conditional descriptive intervals. Primary-source review and
real-data eligibility work remain deferred/blocked. Preserve all uncommitted
files from this goal, including earlier conformal/example work.

### Goal continuation: learned hard-switch grids and fitted seams, 383 tests

The previous goal turn made verified implementation progress. This continuation
inspected the authoritative worktree and added `nested_two_curve_selection_v1`
for mixed constant-convex and finite-grid hard-switch ensembles. The older
`nested_convex_pair_selection_v1` remains convex-only and rejects switch plans.
`HardSwitchGridPlan` declares fixed atomic members, at least two distinct
positive grid boundaries, exact boundary ownership, usable training-group gate,
and a positive minimum training-loss gap. Every grid value must be strictly
inside the registered exact-endpoint loss domain. All grid values are scored
on the identical complete training sample roster with the same sample-balanced
log-pressure loss used for validation.

Inner training fits the boundary, inner validation locks a candidate, and
outer training refits its boundary before untouched testing. Fits retain all
scores and require a strictly sufficient best-versus-second-best gap; ties or
inadequate separation give `unidentifiable_boundary` without an arbitrary
default. The evidence gate is not a significance test, and identification
concerns the registered discrete grid rather than a physical boundary's true
location or confidence interval. Existing learned-domain diagnostics support
both kinds without feeding back into fitting/selection.

Added target-free `diagnose_learned_switch_seams()` and
`locked_outer_switch_member_contrast_v1`. Both member forecasts are evaluated
for outer test samples at the already fitted boundary, preserving canonical
values, normalized input lineage, failures, ownership and right-minus-left
contrasts in `learned-seams.json` and a report table. No observations are read
and no boundary is refitted by this diagnostic. Contrasts imply jumps only for
member curves continuous at the seam.

The new `evaluation/examples/synthetic_hard_switch/` run reuses committed
synthetic inputs and registers a [1, 10, 100] kPa training grid. It selects
outer boundaries 1, 10 and 1 kPa and retains twelve held-out seam records.
This remains synthetic execution evidence, not a routing recommendation or
real-data accuracy claim.

Thirty-one new tests protect exact fitted boundaries and hand-calculated
losses, boundary ownership, strict loss separation, grid nonidentifiability,
inner/outer roles, refitting on all outer training samples, convex/switch
competition, input/grid ordering, group gates, schema/version validation,
input-domain integration, independently calculated public-function seam values,
missing seam inputs, target-free diagnostics, and complete artifact replay.
Memory-only mutations admitting equal loss gaps and leaking outer targets into
boundary refitting both failed at the expected assertions. Production files
were not modified by either probe. Existing convex tests now explicitly assert
the fitted parameter kind before checking weight-specific fields.

Full component verification passed on Python 3.13.12/Windows: **383 tests**,
Ruff 0.16.1 lint/format (79 Python files), and ty 0.0.71. Pytest used
`--basetemp ../../local/pytest-switch-full -o cache_dir=../../local/pytest-cache-domains`.
The synthetic CLI run lives in ignored `local/retention-switch-first-demo`.
The latest wheel built successfully and was installed without dependencies
into ignored `local/ptfkit-eval-wheel-switch`. That installed copy loaded the
new schema, verified the saved report and exactly replayed learned selection,
learned applicability, and all twelve fitted-seam records.

The active goal remains in progress. Next: noncorrecting physical diagnostics
for learned inner/outer prediction curves, then selected-strategy descriptive
assessment and carefully scoped uncertainty. Full selection-process uncertainty,
nonlinear predictor gates, learned blends, and primary-source/real-data work
remain separate unfinished roadmap items. Do not claim the full roadmap done.

### Goal continuation: held-out curve quality and strategy diagnostics, 404 tests

The previous goal turn made verified progress. This continuation inspected the
current result/quality/selection contracts and added a shared explicit
`selection_prediction_frames()` representation for fixed and learned inner
validation candidates and locked outer choices. Frames retain full holdout
rosters, missing predictions, candidate/fold/protocol identity, training/holdout
roles, and stored assessment evidence. Duplicate frames/point keys, predictions
outside their holdout roster, and mismatched learned-fit provenance are rejected.
Run candidate comparison construction is now shared by fixed selection,
learned selection, and nested fixed-domain diagnostics, preserving their exact
common-cohort contract.

`diagnose_selection_curves()` reports physical water-content bounds and adjacent
monotonicity findings independently for every frame/sample, including explicit
`no_predictions` records. It reads predicted values only, never repairs them,
and never changes choices, fitting, eligibility or scoring. Results persist as
`selection-curve-quality.json` with scoped report counts. Inner repeated holdouts
are not treated as independent repetitions; pressure support is descriptive.

`assess_selection_strategies()` implements
`locked_outer_strategy_descriptive_v1` separately for fixed and learned
selection. Only locked outer forecasts inside the registered loss domain enter
strategy metrics. Each sample must be assigned exactly once per outer strategy,
and retained rows must reproduce stored per-sample losses. Coverage denominators
include missing targets, failed exact endpoints and unavailable fits. Maximal
and common cohorts retain sample-balanced descriptive metrics, choice stability,
partial rows, outside-domain row counts, and atomic-minus-ensemble differences.
Failed outer folds prevent a complete strategy result and mean outer loss;
partial descriptive data remain visible. `strategy-assessment.json` and the
report expose this status and full coverage.

Strategy uncertainty is explicitly `not_estimated_crossfit_dependency`.
No confidence intervals from resampling fixed held-out rows are relabeled as
uncertainty of repeated selection/refitting with overlapping training groups.
Those require a separately justified inferential protocol. Existing fixed
candidate, paired, conformal and reference-fit intervals retain their own scopes.

Twenty-one new cases protect scope/identity validation, explicit absent curves,
target-independent noncorrecting physical findings, independent binary-fraction
strategy metrics, loss-domain filtering, missing-target denominators, failed
folds/splits, stored-loss consistency, duplicate outer evidence, fold ordering,
real-public-function pipeline replay and new-artifact corruption detection.
Memory-only mutations clipping unphysical predictions and dropping strategy
pressure-domain filtering both failed at their expected assertions. Production
files were not edited by either probe.

Full verification passed: **404 tests**, Ruff 0.16.1 lint/format (85 Python
files), ty 0.0.71, and `git diff --check`. Pytest used workspace-local
`local/pytest-strategy-full` and cache directories. The expanded CLI run is in
ignored `local/retention-strategy-diagnostics-demo`. The latest wheel built and
was installed without dependencies into `local/ptfkit-eval-wheel-strategy`;
that installed copy verified the saved report and exactly replayed all 96
curve-quality records and the complete strategy-assessment artifact.

The goal remains active. Next: investigate primary statistical sources for
full selection-process uncertainty under independent source/profile grouping
and unequal sample/pressure counts before registering an estimator. Complete-
pipeline resampling sensitivity can be a separate descriptive protocol, but
must not substitute for inferential intervals. Nonlinear gates, learned blends,
weight/boundary uncertainty, and deferred source/real-data work remain unfinished.
All edits remain uncommitted; preserve the full worktree and new files.

### Goal continuation: inference review and whole-group retraining, 423 tests

The previous turn made verified progress. This turn inspected the current
strategy/uncertainty contracts and reviewed primary statistical sources:
Bengio and Grandvalet (2004), Bates/Hastie/Tibshirani (author preprint and
published-paper metadata), and Schulz-Kümpel et al. (2025). The new
`ptfkit-eval-inference.md` records the sources and application-specific
qualification gaps. In particular, an independent group is not interchangeable
with an independent row when sample counts differ, and inference nesting is
not the same operation as inner candidate tuning. No full-process CI estimator
was promoted. An exact unequal-group counterexample was independently checked
with rational arithmetic: expected two-group holdout ratio 5/8 versus the
sample-weighted population target 3/4. This is our derivation, not a theorem
claimed on behalf of those papers.

Implemented `whole_group_bootstrap_retraining_sensitivity_v1` and optional
`selection_resampling` registrations for fixed/learned protocols. Each draw
samples whole original resolved groups with replacement, repeats sample and
observation occurrences, and reruns candidate selection, inner fitting,
outer refitting and outer assessment. Original source/profile identities stay
unchanged: all copies remain in the same fold and count once toward independent
training-group gates. Unequal group sizes retain their sample-occurrence weights.
Original effective grouping/source fallback is frozen before drawing, so dropping
a missing-profile group cannot silently switch the experiment back to profiles.

The registered fold seed is retained while assignments are rebuilt for each
draw. Upstream eligibility/fixed PTF predictions are cached because no supported
atomic function uses learned preprocessing. Every target-dependent selection,
convex fit or switch search is repeated. Failed draws remain explicit and are
not discarded or retried. `selection-resampling.json` records every multiplicity,
original membership, sample/observation occurrence map, derived dataset hash,
and complete repeated selection evidence. This internal view is not published
as a new measured dataset; replay begins from parent canonical snapshots.
The schema rejects confidence levels and labels the output
`not_estimated_retraining_sensitivity_only`. These trajectories are infrastructure
for future qualification, not a replacement for confidence intervals.

Nineteen new unit/integration cases protect independent rational weight oracles
with unequal group sizes, preserved source-local profile identity, zero/diverse
draw accounting, retained low-diversity failures without retry, frozen source
fallback, missing-target denominators, RNG/row-order reproducibility, fixed
ensemble handling, invalid original membership, registration rejection and
public pipeline artifact replay. Memory-only mutations collapsing multiplicity
and assigning each copied profile a fresh independent identity both failed at
the expected sample/group-count assertions. Production files were not edited.

Full verification passed: **423 tests**, Ruff 0.16.1 lint/format (89 Python
files), ty 0.0.71, and `git diff --check`. Pytest used workspace-local
`local/pytest-retraining-full` and cache directories. The new committed-input
example is `evaluation/examples/synthetic_retraining/`; its twelve synthetic
sources produce sixteen draws with 6–9 distinct groups under the fixed seed,
all supporting both strategies. The CLI run is in ignored
`local/retention-retraining-verified-demo`. The current wheel built and was
installed without dependencies into `local/ptfkit-eval-wheel-retraining`;
that installed copy verified the saved report and exactly replayed all sixteen
draws and their complete evidence.

The active goal continues. Next: coverage/calibration experiments for complete
selection under unequal/informative group sizes and failed-fit behavior,
including explicit conditional-versus-average risk targets. Only promote a CI
after its assumptions, normalization, training size, nesting and independent
oracles are justified. Learned blends/nonlinear gates and deferred scientific
source/real-data work remain additional unfinished roadmap items.


## Exhaustive group-size calibration checkpoint (433 tests)

The learned selector now exposes `select_grouped_forecast_candidates` for
already eligible forecast records and an explicit full sample roster. Native
runs delegate to the same selection core after retaining registered PTF member
and provenance validation. The supplied-forecast entry point validates exact
fixed candidate/kind rosters, atomic trainable members, canonical compatible
contracts, unique sample identities and source-local profile agreement before
splitting. Samples without forecasts remain in coverage denominators. This
supports mathematical calibration without attributing invented predictions to
published PTFs; callers remain responsible for forecast provenance and eligibility.

The standalone `evaluation/experiments/group_ratio/calibrate.py` exhaustively
runs eight equiprobable three-group datasets and ten probability-weighted
bootstrap multiplicity vectors each, for equal and informative unequal group
sizes. Targets are constant zero/one curves; forecasts are mathematical zero,
one, and a training-fitted convex pair. Pressure-grid density also differs.
Independent finite-state oracles distinguish population risk of rules trained
on two IID groups from the sample-weighted cross-fitted statistic. With group
sizes 1/3, expected atomic/ensemble population risks are 3/8 and 11/32, while
expected sample-weighted outer losses are 3/7 and 429/1120. The equal-size control
has zero bias for these targets. Only multiplicities (1,1,1), probability 2/9,
support the registered three outer folds; all other draws retain explicit
insufficient evidence. Successful draws reproduce the original statistic with
zero spread. No failed draws are discarded and no CI or coverage claim is made.
The experiment README derives all oracle fractions independently.

Ten new test cases cover sample-weighted training-only fits, roster/profile
and member-type errors, missing-forecast coverage denominators, exact population
and cross-fit oracles, multinomial probability accounting, and retained failed
draws. Full verification: **433 tests**, Ruff 0.16.1 lint/format, ty 0.0.71,
`git diff --check`. Workspace-local pytest directory:
`local/pytest-forecast-calibration-full`. Result artifacts are ignored
`local/group-ratio-equal.json` and `local/group-ratio-unequal.json`. The rebuilt
wheel installed into `local/ptfkit-eval-wheel-calibration` and exactly replayed
both complete experiments using that installed copy.

The active goal continues. Next work: missing-target and parameter-instability
calibration scenarios, a reusable generic whole-group replay boundary, and a
scientifically justified interval construction with explicit training-law risk,
training size and failed-fit policy. This finite experiment does not qualify an
interval or generalize its small-group failure rate to larger datasets. Deferred
source review, real-data scientific eligibility, learned blends/nonlinear gates,
and the remaining roadmap requirements are still unfinished.


## Shared group occurrences and missing-target calibration (443 tests)

`resample_grouped_forecasts` now materializes supplied eligible forecasts from
explicit counts and a resolved independent-group roster. It validates complete
unique sample membership, source-local profile identities, matching nonnegative
integer counts, and all supplied rows before copying. Missing forecasts stay
missing while their full sample roster is repeated. The returned
`GroupedForecastResample` exposes every original-to-copy sample mapping. It
applies counts only: it does not introduce an inference method or draw law.
Native run retraining and mathematical calibration share the same occurrence
materializer, retaining the existing native sample IDs/order and group gates.

The exhaustive experiment now includes informative missing targets: each high
group retains three latent samples but loses the target of its third sample.
Coverage is preregistered as 2/3. Training and validation see only available
comparisons; population-risk oracles include all latent samples. Full-population
atomic/ensemble risks are 3/8 and 25/72, versus observed sample-weighted outer
loss expectations 9/20 and 91/240. The README derives these independently from
four training states and eight original datasets. Original versus eligible
sample counts and failed-draw split reasons are explicit in every artifact.
The experiment still supplies no CI or nominal coverage claim.

Nine new helper tests protect missing-forecast copies, unequal group
multiplicities, source-local repeated profile names, exact lineage/values,
invalid counts, invalid membership and unknown supplied rows. The existing
exhaustive oracle test gained the missing-target scenario, explicit full-roster
coverage counts and exact failed-draw reasons. A memory-only mutation collapsing
repeated occurrences failed at the five-sample independent oracle; source files
were not changed by that probe.

Verification: **443 tests** passed in the full suite. The final added artifact
count/reason assertions also passed in the focused three-scenario suite. Ruff
0.16.1 lint/format, ty 0.0.71 and `git diff --check` passed. Pytest used
`local/pytest-shared-resampling-full` and workspace-local caches. The rebuilt
wheel installed into `local/ptfkit-eval-wheel-group-occurrences` and exactly
replayed all three experiment artifacts: equal, unequal and informative-missing,
each containing eight datasets and eighty probability-weighted multiplicity
cases. Artifacts are ignored `local/group-ratio-{equal,unequal,missing}.json`.

The active goal continues. Next: parameter-instability and hard-switch boundary
calibration, followed by a justified inference construction with an explicit
training-law estimand, nesting/training-size assumptions and failed-fit policy.
No complete strategy interval is qualified; deferred source/real-data work and
remaining learned strategy roadmap items remain unfinished.


## Exact hard-switch identification calibration (447 tests)

The standalone `evaluation/experiments/switch_instability/` experiment now
exhaustively assesses the learned finite-grid boundary procedure using supplied
mathematical forecasts. Each of eight original datasets and ten weighted
bootstrap multiplicity vectors preserves complete nested selection evidence,
failed fits, sample maps, original group identities and per-strategy statuses.
The package selection/resampling implementation is unchanged in this slice.

The README independently derives the exact trapezoid loss table and population
risks. With equal-sized groups, mixed two-group training states tie and fail:
failure probability 1/2, successful-fit conditional population risk 1/16, and
risk mass on success 1/32. Unconditional ensemble risk remains undefined under
that policy. Fully complete three-group datasets occur with probability 1/4
and have zero ensemble outer loss; dropping incomplete datasets would therefore
produce a misleading zero-error summary. Atomic success does not mask ensemble
failure. Bootstrap ensemble completion averaged over original datasets is 1/18.
With group sizes 1/3, mixed training states uniquely choose boundary 10. Atomic
and ensemble population risks are 7/64 and 3/64, versus expected outer losses
13/112 and 3/56: both differ by 3/448. No CI or coverage claim is produced.

Four new tests protect exact independent training-law risks/failure mass,
conditional versus unconditional result fields, complete-dataset selection,
full fold provenance, both learned boundary values, retained nonidentifiability,
bootstrap probability accounting and preservation of original source groups.
A memory-only mutation allowing tied boundaries to become fitted rules failed
the exact trajectory/failure-law test. Production files were not edited by the
probe. The handoff opening was reconciled to the current checkpoint, retaining
the acceptance target and historical details in the progress log.

Verification: **447 tests** passed in the full component suite, using
`local/pytest-switch-calibration-full` and workspace-local caches. Ruff 0.16.1
lint/format (package and standalone script), ty 0.0.71 and `git diff --check`
passed. Saved ignored artifacts are `local/switch-instability-equal.json` and
`local/switch-instability-unequal.json`. The existing current package wheel in
`local/ptfkit-eval-wheel-group-occurrences` exactly replayed both experiments,
including every selection/fit failure and sample lineage map. No package source
change required a new wheel in this slice. Remote CI/Python 3.11 were not run.

The active goal continues. Next: select and justify the actual inference
construction and its explicit risk target, training size, independent-group
assumptions and failed-fit law. The exact experiments reject naive conditioning
on successful procedures, but do not establish that all possible inference is
impossible. Full strategy CI qualification, learned blends/nonlinear gates,
source review and real-data scientific eligibility remain unfinished.


## Bounded conditional outer-rule risk intervals (472 tests)

The public `ConditionalOuterRiskPlan`, complete group/fold loss records and
`bound_conditional_outer_risks` implement
`simultaneous_group_hoeffding_conditional_outer_risk_v1`. Explicit assertions
cover IID nonempty groups, a value-independent partition, prior loss/group-size
bounds, complete test losses and training-only selection/tuning. Validation
checks group sizes, observed loss bounds, training complements and disjoint
folds. Normalized sums avoid overflow for large finite losses.

K conditional numerator events and one common denominator event share
alpha/(K+1) tail budgets. Integrated conditional Hoeffding bounds and their
union require no independence between folds. Ratio intervals simultaneously
cover fitted outer-rule sample risks and their equal-fold mean. This is not a
CI for observed sample-weighted CV, training-law average risk or a final model.
No success-conditioned or cross-strategy familywise claim is made. Full proof,
primary-source attribution and scope are in the conditional-risk experiment
README and the inference note.

Four exact binary-group experiments enumerate 4/20 groups per fold with group
sizes 1/1 or 1/3. With 20 equal-size groups, exact simultaneous/mixture coverage
is 274877896243/274877906944 and nonvacuity probability is 1. With unequal sizes,
simultaneous coverage is 549755813887/549755813888, mixture coverage is 1 and
nonvacuity is 184735249457/274877906944 (about 0.672). Every case retains complete
bound records and prior assertions, with independent rational risk oracles.

Twenty-five new tests cover high-precision radii, group versus sample counts,
ratio targets, explicit bounds, malformed partitions, finite extreme losses,
vacuous small-sample intervals, exact coverage/nonvacuity and actual nested
convex-selector refits feeding the API. A memory-only mutation substituting
sample counts for group counts failed the independent radius oracle. No probe
changed workspace files.

Verification: **472 tests**, Ruff 0.16.1 lint/format, ty 0.0.71 and
`git diff --check` passed. Pytest used `local/pytest-conditional-risk-full` and
workspace caches; final artifact metadata additions passed focused coverage
checks. A new wheel installed in `local/ptfkit-eval-wheel-conditional-risk`
exactly replayed all four `local/conditional-risk-{4,20}-{equal,unequal}.json`
artifacts, including all per-fold bounds and assumptions. Reversible encoding
fragments in the changed evaluation docs were repaired; subsequent document
reads/writes explicitly use UTF-8. Remote CI/Python 3.11 were not run.

The active goal continues. Next: native complete-coverage/provenance adapters,
explicit run-plan/schema policy registration, retained failed-fit reporting
and joint error allocation across strategies. Existing native uncertainty
statuses remain unchanged. Training-law full selection uncertainty, nonlinear
gates, learned blends and deferred source/real-data eligibility remain pending;
the conditional target does not replace those broader requirements.


## Native conditional-risk policy integration (494 tests)

`SelectionRiskPlan`, `SelectionConditionalRisk` and
`assess_selection_conditional_risks` now integrate the conditional outer-rule
bounds with native fixed/learned selectors. Before inference, the adapter
checks complete original sample/group membership, disjoint outer partitions,
fit training identities, resolved grouping, exact registered loss, eligible
common observation values/profiles, and reproduced per-sample losses/counts/
coverage/means. Partial coverage cannot silently redefine the population, even
when selector coverage gates allow a descriptive estimate. Failed fits/choices,
insufficient splits and observed prior-bound violations retain unavailable
intervals with explicit policy/fold reasons.

The optional `conditional_outer_risk` schema/run-plan array freezes up to four
unique fixed/learned atomic/ensemble policies. One family confidence level is
required. Each receives alpha/q, including failed policies; its K numerator
and one denominator events then share alpha/[q(K+1)]. The low-level plan's new
`simultaneous_policy_count` enters the log budget directly, avoiding adjusted
confidence values rounding to one. No failure-based budget reallocation occurs.
Policies inherit the selection loss and cannot override it. Grouping must match
selection's resolved grouping, including explicit source fallback.

The runner persists `conditional-outer-risk.json`; the verified human report
labels target, family confidence/allocation, population assertions, loss domain,
bounds and failures. These conditional fitted-rule intervals remain separate
from descriptive CV/metric confidence and retraining-sensitivity artifacts.
The native strategy-assessment uncertainty status retains its original target;
no training-law average-risk or final-model CI is claimed.

`evaluation/examples/synthetic_conditional_risk/` defines a finite IID binary
group population with fixed predictors, two samples per group, five pressures,
known targets and prior size/loss bounds. Its generator draws twelve fair states
with seed 20261023 and retains synthetic cell lineage. The dataset and run plan
regenerate byte for byte. Complete forecast support was checked: all 360 eligible
native/fixed-composite predictions lie between approximately 0.09889 and 0.43896;
fixed/learned convex combinations preserve the declared population loss bound.
This is a constructed population, not evidence for real-publication independence.

Twenty-two new adapter/run tests cover the four-policy independent ln(640)
radius oracle, retained fit failures and family budgets, near-one confidence,
partial targets, observed bound contradictions, source/profile identity and
source fallback, malformed registrations and retained evidence, and consistent
target/loss rewriting that must still fail the original observation-grid check.
Public artifact/report replay and an actual native unidentifiable-weight failure
are tested. A memory-only mutation omitting family allocation failed specifically
at the numerical radius assertion. The source file was never mutated on disk.

Verification: **494 tests** passed in the full suite using
`local/pytest-native-risk-complete` and workspace-local caches. Final report-domain
text and assertion-order updates were followed by focused adapter/run checks.
Ruff 0.16.1 lint/format (100 package/test files and the example generator),
ty 0.0.71 and `git diff --check` passed. A fresh wheel installed into
`local/ptfkit-eval-wheel-native-risk` verified the report in
`local/retention-conditional-risk-verified-demo` and exactly replayed both policy
results, including every family/fold bound. The saved CLI run used 2,000 metric
bootstrap replicates, twelve groups and twenty-four samples. Both conditional
mixture bounds are [0, approximately 0.855425], appropriately wide for the small
number of groups and conservative prior loss bound. Remote CI/Python 3.11 were
not run.

The active goal continues. Next: average risk over new training datasets and
its failure law, distinct from the conditional outer-rule target. Learned
blends/nonlinear gates, deferred scientific source review and real-data
eligibility remain unfinished. The new native policy does not replace those
broader requirements or establish real-workbook population assumptions.


## Independent training-law inference substrate (513 tests)

`IndependentTrainingRiskPlan`, complete independent block/test-group records
and `bound_independent_training_risk` implement
`independent_blocks_group_hoeffding_training_law_v1`. A named learner and named
IID original-group population, fixed training/test group counts, exact block
count, prior size/loss bounds, training-only failure classification and
simultaneous family allocation are explicit. Original groups/samples cannot
repeat across any block/role. Successful-block test coverage must be complete;
missing test losses cannot become training failures or change the population.

The API separately bounds training success/failure probability, successful
training risk mass E[I(success) R(D)], and R(D) averaged conditional on training
success when success probability is separated from zero. Failed training remains
in all block counts and population-size normalization; no zero-error model is
invented. Unconditional model-risk intervals require a prior total-learner
assertion. Even zero observed failures do not imply totality; a contradicting
failure suppresses inference. Normalized moment names explicitly distinguish
loss-sum/group-size means from the population risk ratio. Extreme finite block
sums are normalized before addition.

Three concentration events bound successful loss mass across independent
blocks, group size across all independent test groups, and training success
across blocks. Each receives alpha/(3q). Independent training/test roles give
B E[X]/E[Y] = E[I(success) R(D)], preserving informative sample weighting. This
construction averages over new T-group training datasets, unlike the existing
conditional outer-rule target. The proof, original Hoeffding attribution and
scope are in `evaluation/experiments/training_law_risk/README.md`.

Four exact twelve-block experiments enumerate all 455 multinomial sufficient-
count states. Failure learners have success probability 1/2; equal/unequal-size
risk masses are 1/4 and 3/8 and successful-training risks are 1/2 and 3/4.
Unconditional model risk remains undefined. Total learners have average risk
1/2. Exact joint coverage probabilities are 130959/131072 (equal/failure),
2096059/2097152 (unequal/failure), 2047/2048 (equal/total), and
16777215/16777216 (unequal/total), all above the nominal 95%. Successful-training
interval issuance for failure learners has probability 1255/2048. Error-and-
issuance probabilities are reported separately; no nominal coverage conditional
on issuing an interval is claimed.

Native conditional-risk integrity was also strengthened: deterministic nested
splits are rebuilt from the full original sample roster and registered plan,
catching coordinated inner-role/fit-provenance changes. Complete in-domain
pressure grids are required even if omitted interior points have consistently
rewritten losses; retained outside-domain diagnostics do not change the loss.
These checks preserve existing valid native artifacts and values.

Nineteen new cases cover these three integrity contracts, high-precision
independent-block moment/radius oracles, informative-size normalization,
training failure retention, totality assertions, unknown successful-block test
losses, shared/dropped groups, invented zero errors, finite extreme sums and
exact joint coverage. Memory-only mutations disabling either integrity check
were rejected at the public error contracts. A mutation assuming all training
succeeded failed the exact joint-coverage oracle. No probe changed source files.

Verification: **513 tests** passed in the full component suite using
`local/pytest-independent-training-law-verified` and workspace-local caches.
Final normalized-field names and explicit IID-group/learner metadata passed
32 focused cases in `local/pytest-training-law-final-verified`, Ruff 0.16.1
lint/format (103 package/test files plus the experiment), ty 0.0.71, and
`git diff --check`. A fresh final wheel installed into
`local/ptfkit-eval-wheel-training-law-verified` exactly replayed all four
`local/training-law-12-{equal,unequal}-{failure,total}.json` experiments, including
final field names/assumptions. It also verified the existing native conditional
report and exactly replayed both policies from
`local/retention-conditional-risk-verified-demo`. Remote CI/Python 3.11 were not run.

The active goal continues. Next: original-group block allocation, native
whole-selector reruns per block, explicit learner/training-size provenance,
retained fit/failure evidence, and run-policy/artifact integration for the
independent training-law method. That orchestration is required before claiming
native average-training inference. Learned blends/nonlinear gates and deferred
scientific source/real-data eligibility remain additional unfinished scope.


## Original-group block allocation and renewed source review (2026-10-23)

Implemented public `allocate_independent_training_blocks`,
`IndependentTrainingAllocation` and `TrainingBlockRoles`. Exactly the registered
original group count is required, with disjoint T/H roles in every block.
SHA256 ranking uses only the registered seed and original group identities;
all source-local sample memberships remain intact. Missing profiles under
resolved profile grouping, duplicate samples, empty identities and extra/missing
groups are rejected. The allocator does not infer sampling independence from
labels or rerun the learner. Group identifiers must be value-independent;
complete native selector block orchestration remains the next implementation.

Applied the unit-test-quality skill. Eight new cases protect full original
roster conservation, unequal group membership, source-local profile isolation,
input-order and sample-count invariance, seed influence and malformed roster
rejection. An in-memory mutation reused training groups as test groups. The
public conservation test failed at four unique groups versus the required six;
production file bytes were unchanged. The complete unmodified suite passed:
521 tests in 53.54 seconds, Ruff 0.16.1 lint/format (105 files), and ty 0.0.71.

Online source review resumed at the user's request. The durable
[source review](ptfkit-eval-source-review.md) records primary statistical
evidence, the Weynants 2009 independent-profile validation design and its 2017
measurement-unit erratum. The Vereecken 2010 methodological review is explicitly
identified as secondary evidence for original measurements. No Weynants formula
was added and no correction was transferred to Vereecken 1989 or the workbook.
Sapozhnikov/Kokareva primary measurement blockers remain unresolved.


## Native independent complete-selector training risk (2026-10-23)

Implemented an explicit original-group holdout builder and shared learned
forecast-validation/selection core. `select_grouped_forecast_holdout` repeats
inner selection and refits the locked choice on the explicitly allocated
training groups, with one external holdout. Its split method is distinct from
ordinary nested-CV allocation. The fixed outer-fold count is not used to
reassign these explicit roles; inner evidence gates remain active. Existing
nested selectors retain their previous behavior and public validation errors.

`assess_independent_forecast_training` allocates complete disjoint original
group blocks and repeats that whole learner per block. The native
`assess_independent_selection_training` validates registered member provenance,
caches only eligible fixed PTF forecasts, freezes original grouping/fallback,
and delegates. Parent CV predictions, choices and fitted weights are unused.
Original input forecasts and samples, all block memberships, inner scores,
choices, refits, test predictions and losses are retained. The selector digest
binds its specification and strategy, not external forecast provenance; native
snapshots additionally retain the evaluation specification and manifest.

Training-only fit/selection failures remain explicit and retain every original
test group with unavailable model losses. Missing successful-test predictions
suppress inference rather than becoming training failures. The risk target
remains the learner trained on T groups; no claim is transferred to a larger
final training size. Learned preprocessing is not supported by the cached
forecast path. Reference fits and domain reporting remain separate diagnostics.

Added the `independent_training_risk` run schema, loader, runner integration,
`SelectionTrainingRiskPlan` and family allocation. Up to two unique native
learned-selector strategies share a confidence level. All requested strategies,
including failed training, remain in q. The family is separate from existing
conditional outer-risk and descriptive metric families. Loss is inherited from
the registered selector. All population assertions, including prior learner
totality, remain explicit; no successful-fit sample proves totality.

`independent-training-risk.json` is an optional integrity-checked run artifact.
The report separately names success/failure probability, risk mass,
successful-training risk, unconditional model risk, training size and reasons.
The portable `evaluation/examples/synthetic_training_risk/` run uses the existing
constructed IID binary-group population with two disjoint blocks, each with
four training and two test groups. Its intervals are honestly uninformative;
this example demonstrates complete provenance and replay rather than precision.
The source review and inference notes retain the distinction between the
published bounded-mean inequality and our ratio/failure construction, and leave
all original workbook scientific blockers unresolved.

Applied the unit-test-quality skill. Twenty-five new cases include independent
convex-weight oracles (6/8 and 1/4), log-pressure losses 9/16, separate hard-switch
boundary recovery (10 versus 5 kPa, loss 1/8), target-mutation isolation, partial
test evidence, failed ensemble/atomic separation, unknown forecast rows,
overlapping/partial original groups, source fallback, native family budget,
invalid registrations and exact portable replay. Three in-memory semantic
mutations were detected: training on test groups changed the expected weight
from .75 to .6; relabeling test missingness as training failure incorrectly
issued inference; omitting q changed the radius from sqrt(ln(240)/4) to
sqrt(ln(120)/4). Production bytes were verified unchanged by each probe.

Verification: Ruff 0.16.1 lint/format (108 Python files), ty 0.0.71 and the full
component suite passed: **546 tests in 57.00 seconds**. Built the wheel with
`uv build --wheel` and installed without dependencies into the fresh ignored
`local/ptfkit-eval-wheel-independent-selection` directory. Imported that installed
package explicitly, verified the saved CLI report and exactly replayed both
native policies, including every block's full evidence, against
`local/retention-independent-training-verified-demo`. The pinned local environment
is Python 3.13.12; remote CI and Python 3.11 were not run.

Next substantive work: qualify the complete native training procedure on richer
finite populations and larger independent block designs; retain realistic fit
failures and informative group sizes. Broader point-metric strategy uncertainty,
nonlinear gates/learned blends and original-paper scientific compatibility are
still outstanding. The low-level exact kernel experiments and this native replay
must not be described as validation on the real workbook.


## Renewed execution window (2026-10-23)

The previous five-hour window ended at 13:15 UTC. After checking the clock,
the user explicitly authorized a new window ending at **23:28 UTC on
2026-10-23 (02:28 Europe/Moscow on 2026-10-24)**. Work resumed at 18:29 UTC.
The implementation baseline is 546 passing tests and exact installed-wheel
native block replay. Continue autonomously within this window, preserving the
uncommitted worktree and recording verified portable checkpoints. Online
primary-source/methodological review remains active; unavailable original
workbook materials and source-specific blockers remain explicit.


## Exact complete-selector law calibration (renewed window, 2026-10-23)

Added `evaluation/experiments/selector_training_law/` with actual public
allocation/inner-selection/refit/test-loss probes for all ordered local group
states. The T=2 finite-grid learner has genuine tied-refit failures. The equal
control has success=1/2, mass=1/32 and successful-training risk=1/16. The
informative four-state population has success=23/32, mass=11/256 and risk=11/184;
equal-group risk would differ by 1/736. All 8/64 local cases retain actual input,
fit and failure traces. This specific learner's permutation invariance justifies
exact convolution to 91/6,188 sufficient-count states at 12 blocks; the full
learner is not falsely claimed to run once per convolution state.

Joint coverage is 130959/131072 for the equal control and
79147917377670960618897997173/79228162514264337593543950336 for the informative
population, both above 95%. Issuance and joint error/issuance remain separate.
State probabilities are exact Fractions; interval endpoints use the public
floating-point kernel. The independent binomial issuance oracle requires six
successes. Outputs: ignored `local/selector-training-law-{equal,informative}-12.json`.

Applied unit-test-quality. Three new tests protect independent target/law
oracles, preserved failures and sample weighting. An in-memory mutation fitting
only one sample per group made an unequal-size majority into a tie; the exact
oracle rejected it. Production bytes remained unchanged. Full component
verification passed: **549 tests in 62.15 seconds**, Ruff 0.16.1 lint/format
(109 files), and ty 0.0.71. The standalone experiment also passes explicit
Ruff and component-environment ty. Installed-wheel replay exactly reproduced
72 local probes and 6,279 count states, including every retained trace.

Primary-source review added Varma and Simon (2006): the complete tuning
procedure belongs inside external validation. Their classification evidence is
not a proof of our informative-group ratio/failure interval construction.
Original workbook source rules remain unchanged. Derivations and full scope
limits are in the experiment README and the source-review record.


## Larger original-group native design (renewed window)

Added the standalone training-risk generator with separately registered
population/allocation seeds, checksum-bound self-contained input files and
no overwrite of existing evidence. Twenty blocks use 120 newly drawn original
groups and 240 samples, retaining T=4/H=2. A generated population seed is
embedded in the preserved dataset ID; generation metadata also binds its hash.
Two tests verify genuine group/sample conservation, deterministic generation,
seed separation including actual observation values, actual ensemble refits,
and the independent Decimal ln(240)/40 radius oracle. Full verification at
that checkpoint passed 551 tests in 67.60 seconds, Ruff/ty and an installed-wheel
exact replay of all 40 strategy/block invocations. The native example's
successful-training risk upper bound is about .59564, with success lower bound
about .62984 and no unconditional-model-risk assertion. Saved current run:
`local/retention-training-risk-20-final-verified`.

## Paired complete-selector training-law risk (renewed window)

Implemented `training_pairs.py`: a joint-success left-minus-right sample-risk
comparison on identical original train/test roles. Each raw model loss must
satisfy its own prior bound B before subtraction. The stable map
U=((left-right)/B+1)/2 reuses the qualified positive bounded kernel. Signed mass
is B*(2*M_U-p); joint-success risk differences use its affine conditional
interval. Nonnegative bounded losses can be subtracted without overflow;
normalizing afterward preserves identical binary differences across different
absolute errors. The transform is recorded explicitly. Prior joint totality
is required for unconditional model-risk differences, and observed failures
suppress contradicted assertions. All one-sided failures retain the successful
rule's available evidence and the complete original test roster.

`pair_selection_training_evidence` extracts both actual trained strategies from
shared retained invocations. Native `paired_training_risk` registration, schema,
loader/runner, full `paired-training-risk.json` provenance and explicit report
are integrated. The paired comparison has its own confidence allocation,
separate from marginal, conditional outer-risk and metric families. It does
not subtract marginal conditional CIs or infer fit failure from test missingness.

Extended exact complete-selector calibration with --paired. The informative
population has joint success=23/32, signed mass=23/512 and successful difference
1/16. Subtracting marginal successful-training risks yields 1559/23552 instead.
All 64 real local selector probes retain both rules, including atomic evidence
on switch-failure cases. The four sufficient states produce 455 exact 12-block
count states; the equal control has 13. Paired joint coverage is
1151753799494556037/1152921504606846976 and 2047/2048 respectively; both have
zero joint conditional-error/issuance probability on these finite laws. These
are finite-population qualification experiments, not workbook validation.

Twenty paired cases protect independent Decimal/Fraction oracles, orientation,
joint versus marginal success, raw-bound cancellation, missing tests, role
mismatch, extreme finite values, totality contradictions, stable binary-loss
transformation, schema rejection, family-budget separation and portable replay.
In-memory probes detected ignoring one-sided failure and premature per-loss
normalization that changed otherwise identical sufficient statistics. Production
bytes were verified unchanged. Full component checks passed: **571 tests in
76.27 seconds**, Ruff 0.16.1 lint/format (114 files), ty 0.0.71. Standalone
scripts pass explicit lint/format and component-environment type checks.

The native paired examples are `synthetic_training_risk/paired-run.json` and
the generator's --paired 20-block design. Current saved runs are
`local/retention-paired-training-risk-verified` and
`local/retention-paired-training-risk-20-verified`. Built a fresh wheel and
installed into `local/ptfkit-eval-wheel-paired-training-risk`; exact replay of
both native runs and both paired finite-law experiments is the final package
verification for this slice. Full derivation and limits live in
`evaluation/experiments/selector_training_law/paired-risk.md`.

The next justified roadmap slice is finite-grid learned blend intervals using
the existing fixed blend routing semantics, with inner-only fitting, full refits
and failure/provenance preservation. Nonlinear predictor gates, full descriptive
point-metric uncertainty and original scientific source compatibility remain
outstanding. Continue within the renewed deadline; do not mark the whole goal
complete merely because this checkpoint passes.


## Finite-grid learned blend intervals (renewed window)

Implemented `BlendGridPlan`, `BlendIntervalScore`, `BlendGridFit` and shared
finite-grid training for hard switches/blend intervals. The registered grid,
member order, axis transform and weighting are frozen before validation. Each
inner training fold evaluates every interval on the common exact pressure grid;
inner evidence locks a candidate and all outer training data refit its interval.
Strict loss separation and group/coverage gates retain explicit failures with
no invented transition. Fixed/learned selection, empirical domains, curve
quality, retraining sensitivity and independent/paired risk paths accept the
new learned fit. Parameter confidence remains unestimated; nonlinear predictor
gates and broad point-metric process uncertainty remain pending.

Added target-free `LearnedBlendEndpoint` diagnostics for both locked endpoints
and every outer test sample, with full member input/forecast traces and explicit
missingness. Deleting observations and inner/outer loss/prediction evidence
leaves the diagnostic unchanged; deleting a member input leaves both endpoint
records unavailable on that side. Contrasts are not interpreted as blend jumps.
The native artifact/report schema includes `learned-blend-endpoints.json`.
The selector report now distinguishes unestimated parameter intervals from
separate opt-in risk-policy intervals rather than saying all process intervals
are unestimated.

Preparation exposed an actual fixed-router numeric defect: adjacent finite
positive endpoints could share a rounded logarithm and divide by zero. Relative
log spans now preserve their weights. Finite linear endpoints with overflowing
span subtraction also retain correct relative positions. Independent 90-digit
Decimal and hand-fraction tests protect both cases; ordinary wide log routing
keeps its previous arithmetic path. No prediction clipping is introduced.

The exact blend training-law experiment runs all 8/64 actual local complete
learner cases. Mismatching the registered curves has sample loss 1/64. Its
normalized sufficient-state law matches the checked switch experiment; all
91/6,188 twelve-block count states run the public bounded kernel, with exact
normalized-moment and binary-scaled endpoint comparisons. Informative targets:
success=23/32, mass=11/2048, successful-training risk=11/1472. Equal-control
targets are 1/2,1/256,1/128. Independent sample-majority and loss oracles expose
extra ties from incorrect equal-group fitting. Actual failures remain undefined
model errors and stay in every original-group count. Outputs:
`local/blend-training-law-{equal,informative}-12.json`.

The native example is `evaluation/examples/synthetic_learned_blend/`, using the
previous explicitly constructed IID population and actual PTF forecasts. It
registers both independent training policies plus a paired comparison and keeps
all fit/endpoint/risk evidence. Saved CLI run:
`local/retention-learned-blend-verified-demo`. Two blocks remain uninformative
for confidence precision; this is a scientific-provenance/replay example.

Applied unit-test-quality throughout. Twenty-eight additional cases protect
exact linear/smoothstep interval recovery, hand objectives/gaps, linear-axis
semantics, held-out target isolation, unidentified members, domain/grid policies,
all native uncertainty paths, target-free endpoint diagnostics, missing inputs,
portable replay, precision boundaries and the finite-law proof. A memory-only
mutation ignoring the registered linear axis raised training loss from zero
to about .03020 and failed the intended oracle. Full component verification:
**599 tests in 96.43 seconds**, Ruff 0.16.1 lint/format (118 files), ty 0.0.71.
The standalone blend-law script passes explicit lint/format/type checks.

Primary-source review added Roberts et al. (2017): blocking must reflect
dependence and prediction scope; it does not establish IID publication groups.
Original scientific source-rule blockers remain unchanged. Next, build/replay
the current installed wheel with the learned blend and finite-law evidence,
then pursue remaining point-metric process uncertainty within the renewed window.


The final blend wheel was installed into
`local/ptfkit-eval-wheel-learned-blend`. Its exact replay matched the native
learned-selection, endpoint, independent-risk and paired-risk artifacts, plus
both complete blend finite-law experiment outputs. The 599-test checkpoint is
fully packaged and portable. The next active slice is explicit point-MAE/MSE
assessment of the complete learner, keeping its selection objective unchanged
and preserving full common pressure grids and failed-training/test evidence.


## Point-score whole-training risk checkpoint (2026-10-23)

Added explicit `PointErrorLossPlan` for per-sample equal-point MAE/MSE on the
complete original eligible common pressure grid inside the selection domain.
The complete learner still selects/refits with its registered log-pressure
objective. The new point result/block types retain full sample scores and
missing-grid/training-failure reasons. Incomplete successful test forecasts
suppress inference without changing training success or shrinking the roster.
MSE overflow remains unavailable; finite large MAE is retained without clipping.

Native `point_training_risk` registers up to four unique strategy/metric pairs,
allocating one simultaneous family across all successes and failures. Its
portable artifact is `point-training-risk.json`. Optional `point_metric` on the
paired policy applies the same score to both learners on joint success. The
point family and the paired comparison retain separate confidence allocations.
MSE additionally yields an increasing-square-root interval for pooled RMSE,
meaning sqrt(training-average MSE), not average per-training RMSE. Prior totality
is still required for the unconditional counterpart.

The blend experiment now also runs all 8/64 actual local complete learners with
MAE/MSE assessment, checks the independently derived 1/20 and 1/80 mismatch
losses, and evaluates all 91/6,188 twelve-block count states. Exact probabilities
and coverage agree with the qualified normalized law; nonbinary risk endpoint
scales are checked to numerical tolerance. Informative successful-training
truths are MAE=11/460 and MSE=11/1840, with success 23/32. Neither grid weighting
nor the selection objective is changed to manufacture that agreement.

The native `synthetic_point_risk` example and `synthetic_training_risk` generator
`--point-metrics` flag supply portable complete-input runs. Combining the flag
with `--paired` registers an MSE comparison. The constructed 20-block example
uses 120 distinct groups and 240 original samples. Its four-policy success
lower bound is 0.6071327799401579; no observed successes prove prior totality.
Saved native runs are `local/retention-point-risk-native-verified` and
`local/retention-point-risk-20-verified`.

Unit-test-quality checks include hand MAE/MSE values on irregular pressure grids,
complete native replay, unchanged inner selections/refits, fixed family counts,
failed policies, full original test accounting, paired raw scores, root-functional
oracles, and rejected registrations. Memory-only mutations replacing squared
error by absolute error and ignoring missing interior forecasts both failed their
intended assertions; source bytes remained unchanged. Full component verification: **628 tests in 94.97 seconds**, Ruff 0.16.1
lint/format (122 files) and ty 0.0.71. The standalone experiment and generator
were checked separately.

The wheel in `local/ptfkit-eval-wheel-point-risk` was installed separately under
`local/ptfkit-eval-installed-point-risk`; the replay explicitly checked the
import path. Both native runs exactly reproduced point/paired/learned artifacts.
The installed wheel also reran all four equal/informative MAE/MSE finite-law
experiments, preserving 144 local fit cases and 12,558 count states in total.
Gneiting (2011) was reviewed for score/functional/weighting distinctions; it is
not cited as proof of our block intervals or MAE optimality of a log-loss learner.
No scientific source rule or real-workbook eligibility was promoted.

Next active slice: registered nonlinear log-pressure sigmoid gates, with finite
center/steepness search inside every inner training fold and outer refit. This
is a pressure-only extension; soil-property gating remains separate. No sigmoid
implementation is included in the packaged point-risk checkpoint.


## Nonlinear pressure sigmoid checkpoint (2026-10-23)

Added `SigmoidGridPlan/Fit/ParameterScore` and stable
`sigmoid_left_weight`. The fixed two-curve blend has left weight
1/(1+exp(s*log10(pressure/center))), with positive finite registered center and
steepness pairs. Centers must lie strictly inside the original selection domain.
The generic grid learner refits every inner training fold and outer training
set; weak separation yields `unidentifiable_sigmoid_parameters`. Both member
forecasts remain required even at numerical saturation. Adjacent large pressures
retain their relative logarithm; extreme ratios and steepness avoid exponential
overflow. No pressure monotonicity or soil-property gating is inferred.

Native schema, loader, artifacts/report, empirical domains, curve diagnostics,
retraining sensitivity and independent/point/paired risk paths accept this fit.
`learned-sigmoid-centers.json` forecasts both members for every original outer
holdout sample at its locked center, retaining input traces, steepness and their
half-weight average. The diagnostic reads no observations and performs no fits;
missing member inputs retain explicit unavailable records. The runnable example
is `evaluation/examples/synthetic_sigmoid_gate`; saved CLI evidence is
`local/retention-sigmoid-gate-verified`.

The separate `sigmoid_training_law` experiment uses constant mathematical atomics
1 and 0, center 10 kPa and slopes ln(2),2*ln(2). Rational three-pressure curves
(2/3,1/2,1/3) and (4/5,1/2,1/5) have mismatch loss 2/225 with log weights
(1/4,1/2,1/4). The prior 1/64 bound exceeds that support loss. All 8/64 actual
complete learner cases validate the sample-majority law, matched/mismatched
losses and retained ties before the generic original-role convolution. All
91/6,188 twelve-block count states run the production bound. Informative truths
are p=23/32, mass=11/3600, successful risk=22/5175. Coverage and issuance agree
with independent binomial-tail oracles. Floating losses/endpoints use explicit
numeric tolerance; probabilities remain exact Fractions.

Twenty-seven additional cases protect rational weights and grid objectives,
90-digit adjacent-pressure behavior, extreme saturation, heldout-target isolation,
identification/registration rejection, native sample/group accounting, risk
failures, target-free/missing-input center diagnostics, retraining and replay.
A memory-only log-base mutation failed the rational-weight oracle; production
source bytes were unchanged. Full component verification: **655 tests in
151.72 seconds**, Ruff 0.16.1 lint/format (126 files), ty 0.0.71, git diff check.
The standalone calibration passes separate lint/format/type checks.

The wheel `local/ptfkit-eval-wheel-sigmoid-gate` was installed under
`local/ptfkit-eval-installed-sigmoid-gate`, with its import path explicitly
verified. Native learned choices, locked centers, point/paired risks and
retraining artifacts exactly replayed. Both finite populations ran through the
installed code; the informative JSON exactly matched the source run. A replay
harness initially compared a Python tuple to its JSON list; normalizing that
comparison fixed the harness, while the saved JSON artifacts already matched.

Jacobs et al. (1991) was reviewed from the author-hosted original text. Its
stochastic expert selection, mixture likelihood and learned experts differ from
our deterministic blend of fixed PTF forecasts. The review records this scope
rather than claiming that the publication proves our algorithm or uncertainty.
Remaining work includes soil-property gates, fitted-parameter confidence and
broader signed/median metric process inference; scientific source/data blockers
still apply. Original PTF publication review continues in parallel with roadmap
implementation within the authorized window.


## Adapter stability and real-workbook return (2026-10-24 Europe/Moscow)

Primary Clapp-Hornberger review exposed finite-input numeric failures. The
adapter now computes dimensionless pressure ratios, uses a rationalized wetness
deficit root and preserves tiny dry-branch results in log space. The published
positive-parabola constraint at fixed W_i=0.92 requires b<11.5 globally; invalid
shapes are rejected even for a dry or empty canonical grid. The fitting bound
shares the same constant. Canonical kPa evaluation uses the homogeneous ratio
without an unnecessary overflowing conversion to centimeters.

Reduced van Genuchten evaluation now applies its exponent in log space rather
than prematurely saturating an overflowing/underflowing alpha*h product. A shared
positive-product logarithm preserves the exact binary-input product residual
near unity, where large n amplifies cancellation. Scalar adapters and canonical
m=1/Mualem families agree with independent Decimal controls. Defined asymptotic
limits produce no range warnings. Source specifications and generated PTFs were
not changed.

Thirty-two new regressions cover pressure-scale invariance, tiny shapes and dry
results, global invalid shape/suction gates, empty grids, small/large exponents,
reciprocal inputs and scalar/vector consistency. Reference arithmetic uses
100-450 digits and the original equations; tiny values use zero absolute
comparison tolerance. A memory-only sum-of-logs mutation failed three intended
large-exponent controls; source bytes were unchanged. Full verification:
**687 tests in 130.61 seconds**, Ruff lint/format (127 files), ty 0.0.71.
Wheel `local/ptfkit-eval-wheel-stable-adapters` was built and installed separately;
both native replays match the source outputs exactly, and all 54 adapter/fitting
tests pass from the installed wheel with its import path verified.

The user confirmed `local/meta_v3.3.xlsx` and prioritized unlocking the maximum
number of scientifically supportable rows. Its digest exactly matches the
registered mapping (1322bf65b1ca0130085015209858a443d1ee82a7e2ae69232321cd8ede361e68).
A fresh real-file normalization/predictor/reconstruction audit was saved under
`local/meta-v3-3-recheck-20261024`: 130 normalized observations, 1,625 excluded
observation rows, 92 separate fitted parameters, 206 original predictor samples,
five public contracts and zero fully predictor-ready samples. The 130 reviewed
observations are gravimetric mass fractions, not volumetric targets; density and
material/method compatibility still gate their use for volumetric PTF scoring.
The blocker is scientific conventions, not absence of the workbook.

A count-only source/function overlap module `readiness.py` is under development
and not yet part of a verified checkpoint. After the user's reprioritization,
active effort moves to source-level evidence, starting with the large exactly
reconstructable Gumatov 1991 (190 rows) and Bolotov 2014 (168 rows) blocks.
Neither source has been promoted yet. Original-case source aliases and physical
conventions will be reviewed independently. No unit is inferred from magnitude.


## Primary-source row unlocking (2026-10-24 Europe/Moscow)

Bolotov 2014 and the orchard Makarychev 2014 block are now reviewed and enabled.
Their raw pF labels actually encode log10(kPa), established by matching the
published figures and their positive kPa axes. Added that explicit normalization
representation and 16 confirmed full-curve sample crosswalks. The real workbook
now yields **353 normalized observations: 223 volumetric and 130 gravimetric**,
up from 130. The missing Bolotov value remains explicitly excluded. Three source
rules are normalization-ready; all 1,847 rows remain accounted for. Predictor
compatibility remains a separate requirement. Review details and primary links
are in the source-review note. Focused verification and broader checks follow.


The completed source-review checkpoint now retains **649 observations across
62 samples**, up by 519 observations from the initial 130: Chestnova 130,
Gumatov 1991 190, Gumatov 1992 10, Bolotov 167, orchard Makarychev 56 and
arboretum Makarychev 96. Quantities remain distinct: 223 volumetric observations
and 426 gravimetric observations. All 1,847 long-sheet rows are accounted for:
649 normalized, 1,057 blocked-rule exclusions, 48 stale cached identifiers,
one explicit missing water value, and 92 separately retained fitted parameters.
Six reconstruction rules are normalization-ready and 62 complete-curve sample
crosswalks are confirmed. Predictor readiness remains zero under the five public
contracts; newly usable target observations do not prove input-method compatibility.

Normalization now supports explicit log10(kPa) and MPa representations. Ten
synthetic public-normalizer cases protect decade anchors, unit scale, sign and
finite-output gates. A memory-only mutation that applied the pF head factor to
log10(kPa) failed all three intended anchor controls; source bytes were unchanged.
The mapping test additionally protects the permuted Bolotov identities and null.
Full verification: **698 tests in 84.28 seconds**, Ruff lint/format and ty pass.

Panina's full public thesis and the 2014 thermal-property paper were reviewed.
They supply useful quantity evidence but do not resolve the mixed Panina
identities/saturation pressure or assign pressures to named hydrological
constants. These rows remain explicitly blocked. The optional overlap-report
prototype was moved to `local/ptfkit-eval-drafts/readiness.py`; it is deferred,
not shipped as an unverified module. Source-level unblocking remains the priority.


Installed-wheel verification also passed. The separately installed
`local/ptfkit-eval-wheel-primary-rows` wheel imports from its isolated target,
loads the packaged schema, normalizes the real workbook into exactly 649
observations and 62 identities, and reproduces both committed count summaries
byte-for-byte. All confirmed reconstruction crosswalks are noncontradictory.
The deferred overlap prototype is outside the distributable package. Final
Ruff lint/format (127 files), ty and whitespace checks pass.


## Partial Panina recovery with row-level proof (2026-10-24 Europe/Moscow)

The Panina source's positive-pF observations can be released without repairing
its broken global identifier groups or assigning a pressure to saturation.
The reviewed physical rule uses volumetric percent and centimeter-head pF.
An exhaustive 132-row decision table releases 116 unique pressure-water matches,
excludes four ambiguous matches and excludes all 12 disputed saturation points.
The first-axis replacement remains proposed and unused for normalization. Stored
fit parameters and the unresolved complete-curve reconstruction remain separate.

Every release is rechecked against the immutable workbook's original wide
records at the declared decimal precision and confirmed water scale. It must
match exactly one unused master point and its source/id/number triple. Missing,
duplicate, misplaced or inconsistent decisions fail closed. The required-review
flag prevents deleting the policy to restore cached-id fallback. Physical source
blockers still prevent normalization even when a row identity is reviewed.

The real-file result is now **765 observations across 74 samples**: 339 volumetric
and 426 gravimetric. Exclusions total 990: 925 blocked source rules, 48 stale IDs,
one missing water value, four ambiguous point identities and 12 unresolved
saturation pressures. The six complete-source rules remain normalization-ready;
Panina is a partial seventh source, not a fully reconstructed curve/parameter set.

New behavioral tests cover shared cached IDs, stale-ID repair, provenance,
exhaustive policy coverage, invalid canonical IDs, absent policies, duplicate
coordinates, wrong master identities/axes, ambiguous master matches and scaling
gates. An initial ambiguity mutation exposed an incidental later failure in the
fixture; the fixture was strengthened to isolate the ambiguous point. The
corrected memory-only first-match mutation is detected with source bytes intact.
Full-suite checkpoint: **716 tests in 87.38 seconds**; strengthened focused suite:
52 passing tests. Final post-strengthening broad verification follows.


## Real workbook: three partial sources and physical diagnostics (2026-10-24)

Primary-source review now releases 106 Badenko observations and 81 Umarova
observations in addition to the 116 Panina observations released in this goal.
Together these add 303 observations and 40 exact sample identities to the
previous 649/62 checkpoint. All 952 retained observations preserve original
values and cell lineage. Six complete source rules remain normalization-ready;
partial row evidence does not promote complete-curve or fitted-parameter joins.

The loader requires exhaustive row decisions for flagged physical rules.
Normalization rechecks the source's literal original wide points, confirmed
water scale, canonical master identity, and actual axis/water/identity cells.
An ambiguous master pair, reused master point, missing policy, uncovered row,
wrong identity, or invented evidence coordinate fails closed. Proposed axis
replacements remain inactive. An in-memory ambiguity mutation initially exposed
an incidental-failure weakness in its fixture; the corrected independent case
now rejects that mutation for the intended uniqueness contract.

The count-only physical audit diagnoses 56 volumetric curves at zero tolerance:
20 have 32 adjacent increases with suction, and none exceeds volumetric bounds.
The 46 gravimetric curves are outside that diagnostic's scope. These findings
remain visible without clipping, smoothing, deletion, or scoring qualification.
A separate normalization correction permits dry-soil-mass water ratios above
one while retaining nonnegative bounds and the volumetric upper bound. Its
independent example is 1.25 g water per 1 g dry soil, equivalent to 125%.
The real-workbook counts are unchanged by this correction.

Verification: **725 component tests pass in 89.45 seconds**, with Ruff lint and
format checks and ty passing. The standalone physical-audit script also passes
Ruff and ty. A fresh isolated wheel installs successfully and reproduces the
normalization and reconstruction JSON bytes and physical-summary content:
952 observations, 102 samples, 526 volumetric and 426 gravimetric observations.
No workbook values are redistributed. The workbook SHA256 remains unchanged.

Remaining work prioritizes original source evidence for blocked retention
rules and exact predictor methods/particle-size boundaries. The real PTF pilot
still has zero qualified predictor sets; normalized retention counts do not
establish input compatibility or external accuracy. Pestonova's newly found
catalog lead returned HTTP 403, and the author-hosted Khaidapova paper returned
HTTP 429; neither supplied unit evidence, so their exclusions remain active.


### Sadovnikova continuation: 61 additional experimental points

The original journal archive supplied the complete Sadovnikova and Smagin
2011 paper. Figure 1 confirms dry-mass W percent, logarithmic kPa pressure
magnitudes, and filled/open symbols for experimental repeats. Its exact
soil/horizon/depth descriptions match the workbook. Sixty-one unique literal
master points are now released through 63 exhaustive row decisions; long rows
778 and 793 retain explicit exclusions for unsupported 0.01 pressure placeholders.
No guessed replacement is applied. The four retained master identities describe
two experimental series for each of two soils, not four independent soil units.

The updated result is **1,013 observations / 106 master identities**, comprising
526 volumetric and 487 gravimetric points. There are 742 explicit exclusions:
673 blocked physical rules, 48 stale cached identities, six ambiguous matches,
14 unreviewed pressures, and one null. The 92 stored fitted-parameter rows stay
separate. Complete-curve readiness remains six rules. The count-only physical
summary diagnoses the same 56 volumetric series and keeps the now 50 gravimetric
series outside that volumetric diagnostic. Predictor eligibility remains zero.

Verification: **726 tests pass in 154.36 seconds**, Ruff lint/format and ty pass.
The installed wheel reproduces both count JSON files byte for byte and the
physical-summary content exactly at 1,013 observations and 106 identities.
The unchanged workbook SHA256 was checked again. The source-review note records
the journal URL, figure, physical interpretation, dependent repeats, exclusions,
and reviewed PDF hash. No generated PTF target, source specification, or workbook
measurement value was changed or redistributed.

Next source leads include Sidorova and Borisova's 2016 paper (DOI
10.3103/S0147687416020071), whose abstract alone does not confirm the retention
units, and the original Smagin/Khaydapova/Pestonova papers. The journal's 2016
issue page exposed no article or figure text. Keep these rows excluded until
source evidence is obtained. Also preserve the workbook warning that Shein
2012 curves were approximated from physical/hydrological constants: unit recovery
alone must not promote them to independent measured validation targets.


### Moiseev continuation: measured table columns and non-observation exclusions

The original 2018 journal PDF (Table 2, printed p. 82) independently confirms
23 volumetric-percent / pF experimental points for three workbook horizons.
Each pair was compared against an independent transcription of the published
experimental column, not the PSF calculated column. Soil/source/horizon/depth
metadata also match. All 29 observation-labelled long rows now have exhaustive
row decisions: 23 releases, three unsupported saturation-axis exclusions and
three explicitly non-observational U/U-critical table-statistic exclusions.
No proposed pressure replacement is activated. Source evidence and PDF SHA256
are recorded in the source-review note.

The canonical result is **1,036 observations / 109 master identities**, with
549 volumetric and 487 gravimetric points. The 719 exclusions comprise 644
blocked source rules, 48 stale cached identities, six ambiguous master matches,
17 unreviewed pressures, three non-observation table values and one null.
The raw profiler's 1,755 observation-labelled rows include those three table
statistics; exclusion preserves their role discrepancy without changing bytes.
Complete-curve readiness remains six sources. Volumetric physical diagnostics
now cover 59 series, of which the same 20 contain 32 adjacent increases at zero
tolerance. Predictor eligibility remains zero.

The runtime can leave an original missing pressure axis unindexed while
releasing other unique literal source points. It still rejects any attempted
release of that missing-axis point. New behavioral tests distinguish these two
cases and preserve explicit statistic exclusion before pressure interpretation.
The first focused run encountered the preceding physical-summary artifact while
its regeneration process was still running; after regeneration completed, the
full suite passed **729 tests in 154.15 seconds**. Ruff lint/format and ty pass.
A fresh wheel installs and reproduces both count JSON files byte for byte and
physical-summary content exactly, including three non-observation exclusions.

A further lead identifies Manucharova et al. (2012), DOI
10.3103/S0147687412010048. Its prose suggests checking whether the workbook's
soil names were aligned with the original moisture-table columns. The primary
table/figure could not yet be inspected, so neither units nor any metadata
correction is promoted from this lead. These rows remain excluded.


The 48 remaining stale cached identities all belong to Khaydapova 2001. Their
physical source rule is still blocked; repairing cached identifiers alone cannot
release them. The workbook-linked Aksenov 2003 library record rsl01002343790 is
the full 107-page thesis, and the public viewer reports restricted access. No
restricted reading or download was attempted. A freely readable original author
abstract or original 2001 paper is still needed for that source review.


### Source semantics: known water basis and hysteresis provenance

Vasyukov et al. (2012), printed pp. 67-70, was obtained from the author's
university-hosted original issue. Its p. 70 figure confirms volumetric fractions
for all 28 source rows, resolving the water quantity and scale. It does not name
the pressure/head unit behind its logarithmic potential ordinate. The source
rule now records the known water semantics and explicitly leaves pressure
representation/convention unset. All 28 rows remain blocked without guessing
standard pF from the workbook label.

Shvarov's earlier original author abstract, Table 2, provides a more fundamental
warning: two complete five-value vectors and their soil/horizon/depth metadata
match master rows 88 and 108, but the table explicitly reports adsorption-
desorption moisture differences in percent against relative vapor pressure.
These cannot be treated as absolute retention water contents. The printed
imprint is 1984 although the hosting index dates the abstract 1983; the
workbook's 2008 source year is unchanged. Other source rows and the original
2008 tables remain unreviewed; no blanket reversal, reinterpretation or repair
is applied. The manifest now carries a dedicated
`retention_observation_provenance` blocker for all 119 source-labelled rows.

Two independent contracts are protected by new tests: a confirmed volumetric
water basis does not supply a missing logarithmic pressure reference, and
hypothetically confirmed physical units cannot override unresolved absolute-
water versus hysteresis provenance. Verification passes **731 tests in 154.18
seconds**, Ruff lint/format and ty. The installed wheel reproduces all three
regenerated artifacts, including 119 provenance-blocked source rows. The result
remains 1,036 normalized observations / 109 master identities and 719 exclusions;
the workbook checksum remains unchanged.

A new lead identifies Shein and Mady (2018), DOI
10.3103/S0147687418030080, as a possible original for the four Eldigino curves.
Its abstract confirms capillarimetric head units but does not establish water
scaling, retained drying/wetting branch or all horizon identities. The publicly
indexed Russian PDF returned a CAPTCHA; no challenge bypass was attempted.
The openly published 2019 follow-up, DOI 10.13187/bgt.2019.1.59, may supply
independent corroboration, but its OAJI copy currently returns HTTP 410.
Keep the 2018 source blocked until the primary figures/tables can be reviewed.

### Goal continuation: distinguish supporting papers from source observations

Recovered the publisher-hosted Shein/Mady 2019 follow-up through its registered
DOI metadata. It describes field dynamics and HYDRUS validation, does not
reproduce the required 2018 curves, and uses different laboratory layer
intervals. No predictor overrides or observation releases follow from it.

Reviewed Smagin's open 2009 chernozem paper and 2011 follow-up. Their discussion
and humus models do not establish the three workbook retention curves. A
longer 2009 journal contribution remains a separate source-recovery lead;
the current journal archive omits that issue. Recorded exact reviewed PDF
checksums and the distinction between publications in the source-review log.

This checkpoint changes documentation only. Counts remain 1,036 observations,
109 master identities and 719 exclusions. The last code verification remains
731 passing tests; no additional test run is needed for these evidence notes.
The goal remains active: recover original figures/tables for blocked sources,
verify physical units and exact identities, then release supported rows and
rerun normalization and behavioral checks for any mapping or code changes.

### Goal continuation: Sapozhnikov experiment and archived methods review

Recovered Sapozhnikov's 1994 original author abstract as hosted OCR. It links
the 1988 paper to the long-term fertilizer experiment and describes a mixture
of measurement methods and an experimental-calculation method. It does not
reproduce the required 12 retention curves or confirm their water scale and
pressure coordinates. Recorded an explicit review requirement to separate
measured points from calculated segments, without assigning an unverified
provenance category to individual rows. The 108 source observations stay
blocked pending original figures/tables.

Recovered the archived original journal page for Smagin's 2006 methods
paper. Its PDF link returns HTTP 404; public archive metadata contains no
successful capture for that path or the checked 2009 bibliography directory.
Continue with other source copies rather than repeating those download paths.
Only evidence documentation changes in this checkpoint; normalization counts
and the last 731-test verification remain unchanged.

### Goal continuation: Kamennaya Steppe provenance and two source leads

Identified the Shein/Shcheglov/Moskvin 2012 article and reviewed the related
original 2013 author abstract. Exact field-location wording matches the
workbook. The methods reconstruct retention curves from measured constants
through Voronin pressure assignments and van Genuchten approximation; the
30 stored curve points cannot yet be classified as independent measurements.
Recorded that distinction and the original-figure requirement without
releasing rows or changing the existing exclusions.

Identified Chudinova 2009, DOI 10.1134/S1064229309040073, with the relevant
three soil classes. The historical public PDF is unavailable on the checked
route. Identified Sidorova/Borisova 2016, DOI 10.3103/S0147687416020071, as a
candidate for the two remaining sod-podzolic records; exact horizon matching
is still required. These are source-recovery leads, not physical confirmations.
Counts remain 1,036 normalized observations and 719 exclusions. This stage
changes evidence documentation only; the last code check is 731 passing tests.

### Goal continuation: protect reconstructed targets and consolidate source requests

The Shein 2012 mapping now requires observation-provenance review in both its
source and reconstruction rules. The original publication and related author
abstract describe reconstruction from measured constants and inferred pressure
coordinates; confirming units cannot establish independent target measurements.
Extended the existing public-loader regression to both this source and Shvarov.
It checks that hypothetical physical confirmation with an unresolved provenance
blocker is rejected. Removing the source's blocker also fails its precondition.

Recomputed normalization, reconstruction and count-only quality artifacts.
The result remains 1,036 observations / 109 master identities and 719 exclusions;
149 rows now carry the dedicated provenance blocker. The installed wheel
reproduces all three artifacts and the workbook checksum is unchanged.
Verification passes **732 tests in 151.58 seconds**, Ruff lint/format and ty.

The source-review document now has a complete queue for the 15 blocked physical
source rules and their 692 workbook-labelled rows, including 48 Khaydapova
identity mismatches. It names the specific missing scientific evidence for each
source. The other 27 exclusions remain explicit reviewed-row or invalid-value
decisions. Sidorova's publisher confirms the Russian citation as 2016, no. 2,
pp. 25-32, but exposes only an abstract and subscription access. Exact figures,
axes and both horizon identities remain unverified. Continue source recovery
from this queue without treating source-row counts as promised usable targets.

### Goal continuation: Pestonova water scale resolved from the author abstract

Recovered the complete original 2007 author abstract and identified its free
RSL viewer record, `rsl01003058664`. Figure 7's six horizon labels match the
six populated workbook records. The shared W-percent axes and dry-mass methods
resolve water semantics as gravimetric percent. The public library text layer
independently corroborates the figure labels; its pressure-axis text is lost.
Browser rendering returned a gateway error, then a blank page. Free viewing
is authorized by library metadata; downloading is unavailable and was not
attempted. Visual pressure-axis review remains the next source-specific step.

Updated the source and reconstruction rules without confirming pressure or
the proposed saturation replacement. The water-scale blocker count decreases
from 545 to 464 rows. All 81 Pestonova rows remain excluded, and normalized
counts remain 1,036 / 109 identities with 719 total exclusions. All three
artifacts were regenerated and the workbook checksum is unchanged.

Extended the known-water/unknown-pressure contract to this source. All **35
dataset-mapping tests pass in 15.30 seconds**, including the four focused
water/provenance cases; Ruff lint/format, ty and diff checks pass. Production
Python code is unchanged. The preceding full component checkpoint remains
732 passing tests; this checkpoint does not claim a new full-suite run.

### Technical continuation: normalization-to-canonical export

The user redirected work from further source recovery to technical
implementation. Added `export_normalized_retention_dataset()` and the `export`
CLI command. Volumetric measurements retain their values, identities and cell
lineage. The result explicitly accounts for omitted gravimetric rows. Unknown
profiles and missing predictors stay unknown; the material basis is a caller
declaration, with `unspecified` available for unresolved evidence. Canonical
validation rejects duplicate sample-pressure pairs without averaging. Explicit
physical-contract checks reject noncanonical units, total potentials and wrong
denominator bases. Existing files are never overwritten.

The real workbook exports 549 volumetric observations across 59 records;
487 gravimetric observations remain explicitly accounted for. Raw measurements
stay in ignored `local/` outputs. The offline-built wheel installed into a
separate directory reproduces the canonical dataset byte-for-byte. The CLI
summary includes dataset, mapping and workbook checksums. This export does
not establish PTF compatibility or independence, and it does not release any
previously excluded source rows.

Final verification passes **740 tests in 147.82 seconds**, Ruff lint/format,
ty and diff checks. Seven focused export tests protect unchanged values and
lineage, explicit gravimetric accounting, absent predictor/profile inference,
duplicate-pressure rejection, four incompatible physical contracts and CLI
no-overwrite behavior. The installed wheel replay is saved under
`local/meta-v3-3-canonical-export-wheel.json`; its dataset semantic checksum is
`000c3c9fff04a714ff2cc6e9d32fc3d00bd3a3246616caf5dfac4f1673fdd93f`.
Next technical step: exercise the canonical real-data export through the
registered approximation families and persist fitting failures/diagnostics
without inferring missing predictors or asserting scientific scoring readiness.
# Measured reference fitting checkpoint

The standalone `evaluation/experiments/measured_retention/fit.py` experiment now
connects the canonical export to all four registered approximation families
without fabricating an eligible PTF candidate. On the 549-point, 59-series real
export it retains all 236 results: 133 accepted fits, 86 boundary failures,
13 nonidentifiable fits, and four insufficient-observation failures. Parameter
boxes remain the initial synthetic-example engineering policy; these results
do not establish source-specific bounds or qualify PTF prediction uncertainty.

The artifact embeds measurements, source lineage, exact fit policies, optimizer
attempts, failure diagnostics, noncorrecting curve quality, input/script hashes,
and dependency versions. Exact replay produced identical bytes with SHA-256
`78816677bcc0d5844bedb9965c24d5116a680c9740417bfabfbb66422f4555a0`.
Exclusive output rejection preserved the existing artifact. Ruff lint/format
and ty passed for the new experiment. The preceding package suite remains
740 passing tests; package code was unchanged in this checkpoint.

Next technical work remains source-justified fit policies and uncertainty
qualification, followed by predictor-backed PTF evaluation when its scientific
eligibility gates can be met. Accepted descriptive fits must not be substituted
for missing soil predictors or counted as independent soil samples.
# Fit uncertainty support checkpoint

The public `diagnose_fit_uncertainty_support` API now separates successful fit
acceptance from interval containment. It preserves original intervals, permits
exact endpoint contact, identifies unavailable parameter intervals, and reports
failed fits separately. The measured experiment embeds these diagnostics and
still replays byte-for-byte. Among 133 accepted fits, 67 have parameter intervals
outside declared boxes, 12 have mean-curve intervals outside [0, 1], and 44 have
conditional prediction intervals outside [0, 1]; these counts overlap.

The official SciPy covariance documentation was reviewed and linked in the
source review. No soil-specific parameter bounds or statistical coverage claims
were inferred from that documentation. Regression tests distinguish exact
endpoint contact, lower/upper parameter violations, unavailable intervals,
mean/prediction interval types, and fit failure. Replacing strict containment
checks with inclusive checks or swapping interval types would fail the test.

Verification: **741 tests passed**, Ruff lint/format, ty, and exact real-data
artifact replay passed. Next: justified constrained uncertainty methods and
source-specific fitting policy, without clipping intervals or loosening bounds
to increase acceptance counts.
# Bounded nuisance profile checkpoint

The public `profile_retention_parameter` API now computes explicit-grid bounded
nuisance refits for any registered family parameter. It requires an accepted
fit, retains all starts and failures, accepts exact box endpoints, and rejects
invalid grids. These are numerical objective profiles, not confidence intervals
or globally certified optima. The JMP and SciPy methodological references and
the different uniform profile restart policy are recorded in the source review.

On the real canonical export, saturation profiling produced 133 profiles and
798 grid points, all with at least one converged nuisance refit. Two complete
runs produced identical bytes. Five profiles found a grid SSE more than 1e-10
below the original fitted SSE. This is evidence that initial multistart
acceptance does not certify the global optimum; profiles do not silently replace
those fits. Investigate this optimizer stability finding before using objective
thresholds for interval endpoints.

Verification: **742 tests passed**; Ruff lint/format and ty passed. The independent
synthetic oracle checks the exact saturation residual at zero suction, center
recovery, strict improvement over holding nuisance parameters fixed, bounded
nuisance outcomes, failure retention, grid validation, and deterministic replay.
# Profile counterexample and full-refit checkpoint

The public `assess_profile_optimality` API now records signed grid objective
improvement against an explicit absolute/relative error budget, with strict
threshold comparison and missing-solve accounting. No-improvement findings
remain local-grid evidence rather than global optimality certificates.

The five real-data counterexamples all concern Brooks--Corey. Starting a
separate full fit from each best profile solution produced five accepted fits
with SSE approximately 16--29% below the original result. The saturation
parameter is freed again in these refits; bounds and all acceptance diagnostics
remain unchanged. The experiment preserves original fits and summaries, records
new starts in separate refit plans, and refuses exact boundary starts instead
of adjusting them. Both complete replay artifacts are byte-identical.

Verification: **743 tests passed**, Ruff lint/format and ty passed, including
the experiment's type check. Independent objective-comparison fixtures protect
relative scaling, strict threshold contact, missing-grid evidence, invalid
tolerances, and best-point reporting. The next inference step still needs
optimizer-stability and coverage qualification before profile thresholds become
reported confidence endpoints.
# Post-refit stability checkpoint

The measured experiment now audits each accepted profile-start full refit
across every family parameter and preserves updated interval support alongside
the original fit, original profile, and full refit. For the five Brooks--Corey
refits, all 20 follow-up profiles report no improvement above the declared
1e-10 SSE threshold. This finding concerns the explicit grids and local
multistart policy only. Two full runs produced byte-identical artifacts.

One of these five refits still has a parameter interval outside its fit box;
none has a mean-curve or conditional prediction interval outside [0, 1]. The
stability result does not qualify interval coverage or remove the remaining
uncertainty blocker. The independent Brooks--Corey experiment regression test
checks all four parameter identities, exact grid endpoints, noiseless baseline
SSE, separate interval diagnostics, and absent/failed-refit handling.
Post-refit checkpoint verification: **744 tests passed** in the full package
suite; Ruff lint/format and ty passed, including the standalone experiment.
# Approximate profile grid-region checkpoint

The public `assess_profile_grid_region` API now applies a single-parameter
extra-SSE F threshold on the explicit profile grid. Generated profiles retain
original residual degrees of freedom and parameter bounds. Missing metadata,
missing solves, improved baseline objectives, degenerate residual variance, or
incomplete box grids withhold assessment. Accepted node runs and contact with
each parameter bound remain explicit; no continuous endpoints are interpolated.

On the five improved real-data fits, all 20 post-refit profile regions were
assessed at nominal 95%; two reached a declared parameter bound. No disconnected
accepted grid runs occurred. Two full runs reproduced identical bytes. These
remain approximate nonlinear grid regions, conditional on iid Gaussian
homoscedastic errors and adequate local optimization, without calibrated
constrained-boundary or simultaneous coverage.

The reviewed JMP extra-SSE approach and the threshold derivation are recorded
in the source review. Independent tests use the median-one symmetry of F(1,1),
disconnected node sets, unavailable evidence cases, and the original n-p
degrees of freedom in the experiment integration boundary.
Profile grid-region verification: **751 tests passed** in the full package
suite; the 22 focused profile/fitting/experiment tests also passed after the
metadata assertions were strengthened. Ruff lint/format and ty passed.
# Gaussian boundary coverage control checkpoint

The new `evaluation/experiments/profile_coverage/calibrate.py` experiment
exercises the public F-grid region API against an exact bounded mean SSE
profile and an independent unbounded t control. It records all-generated,
available, boundary-fit, interior-available, and covered counts separately.
Latent Gaussian responses are explicitly not physical retention measurements.

With 4000 repetitions per truth scenario and seed 20261024, observed coverage
was 3900/4000 at mean zero, 3904/4000 near the lower boundary (mean 0.02),
3795/4000 at the interior mean 0.5, and 3894/4000 at mean one. Selected interior
fit coverage uses different denominators, retained in the experiment README.
The boundary frequencies agree with the derived 97.5% single-boundary
reference within Monte Carlo precision; finite-box and nonlinear coverage
remain separate questions. Exact artifact replay passed.

Independent regression fixtures protect the difference between boundary and
interior coverage and between bounded F-region and unbounded t classification.
No retention uncertainty claim or modified confidence level is introduced.
Gaussian coverage-control verification: **753 tests passed** in the full
package suite; nine focused coverage/region tests passed after artifact scope
metadata was added. Ruff lint/format and ty passed, including the experiment.
# Nonlinear retention coverage pilot checkpoint

`evaluation/experiments/retention_coverage` now generates noisy controls for all
four registered families at interior and lower-boundary saturation truths.
Every realization, fit failure, raw fit, profile, and region assessment is
retained. There is no redraw, clipping, automatic rescue refit, or bound
widening. Known truth is used only in the inference grid to assess coverage
without interpolation error. Generator equations have independent numeric tests.

Two complete 400-realization runs reproduced identical artifact bytes. Of
400 generated samples, 298 fits were accepted and 102 were rejected at a
parameter boundary. Ten accepted Brooks--Corey fits produced lower-objective
profile counterexamples, withholding inference. The remaining 288 assessed
regions covered truth 269 times. These pooled counts are accounting only:
family/scenario denominators and coverage must be interpreted separately.
The adjacent experiment README preserves the complete eight-scenario table.

This 50-repetition-per-scenario pilot does not establish nominal coverage;
it exposes optimization instability and selected-fit coverage effects for
prespecified larger calibration. The original real-data source blockers,
parameter bounds, and uncertainty qualification status remain unchanged.
Nonlinear coverage-pilot verification: **755 tests passed** in the full suite;
11 focused nonlinear/Gaussian/region tests passed. Ruff lint/format and ty
passed, including the standalone experiment.
# Explicit Brooks--Corey pressure restart checkpoint

`RetentionFitPlan.restart_policy` now accepts the optional
`brooks_corey_pressure_partitions_v1` policy. The public run schema/parser
preserve it. Original seeded attempts remain first; additional air-entry starts
sample interior pressure knots and geometric partition midpoints, leaving
other initial values, bounds, and acceptance gates unchanged. Nuisance profiles
use the same extra locations when air entry remains free. Default behavior
remains `seeded_box_v1`; other families reject the pressure policy.

Two full paired 400-realization runs reproduced identical bytes, and their
observations matched the original pilot exactly. Best converged SSE improved
by more than 1e-10 for 18/100 Brooks--Corey fits and never worsened beyond
numerical tolerance. However, profile lower-objective counterexamples persisted:
seven interior plus two boundary-truth cases, versus six plus four originally.
The optional policy is not promoted as an optimizer-stability solution or an
uncertainty qualification. Profile refinement can reveal additional failures.

Verification: **758 tests passed**, Ruff lint/format and ty passed. Six focused
restart/run-plan/coverage tests passed with workspace-local temporary storage.
Tests independently protect partition locations, original attempt preservation,
unchanged nuisance starts, fixed-air-entry behavior, family rejection, and
explicit run-plan policy resolution. Next: investigate optimization within
piecewise air-entry intervals rather than relying on additional starts alone.
# Piecewise Brooks--Corey interval solves checkpoint

The optional `brooks_corey_interval_solves_v1` policy now retains original
full-box solves and adds each seeded start in every closed air-entry interval
formed by pressure knots and original endpoints. Full-fit and nuisance-profile
attempts record local `air_entry_interval` limits. Scientific parameter bounds
and all original acceptance gates remain unchanged. Tests protect original
attempts, complete interval coverage, unchanged input arrays, correct handling
of fixed air entry, and accepted solutions on internal pressure knots without
misclassifying those knots as physical parameter bounds. The run schema/parser
accept and preserve the policy; the other two policies remain available.

Paired 400-realization pilot comparisons used exactly the original noisy
observations. Best converged SSE improved by >1e-10 in 19/100 Brooks--Corey fits
and did not worsen beyond numerical tolerance. All Brooks--Corey profile
lower-objective counterexamples disappeared in this pilot: interior truth had
50 assessed regions with 47 covering truth; boundary truth had 25 assessed
regions with 21 covering truth and 25 boundary fit failures. Two formerly
accepted boundary-truth solutions now resolve to proper boundary rejections.
These results do not certify a global optimum or nominal coverage, especially
for selected boundary fits or nonsmooth knots.

Verification: **760 tests passed** in the full suite; eight focused tests passed
after the final dispatch refactor and knot regression assertions. Ruff lint,
format, and ty passed, including the experiment. The initial full replay was
byte-identical; final-dispatch replay is recorded in the follow-up verification.
Final interval-solve verification: the final experiment replay was
byte-identical, and its complete numerical payload matched the pre-refactor
artifact after excluding the intentionally changed script hash. Identical
generator observations against the original pilot were verified separately.
# Expanded calibration, real fitting, and predictor readiness checkpoint

The expanded study fixed 34 scenarios before execution and completed all
6800 realizations. Independent cell streams, checksummed resumable artifacts,
Monte Carlo standard errors, exact simulation-probability intervals, and a
prespecified Bonferroni-adjusted one-sided undercoverage test are implemented.
All 34 saved cells replayed without changing artifact bytes or modification
times. Exact runner/generator/plan snapshots and a matching wheel are retained
with the local study; `expanded-summary.json` contains the versioned summary.

Accounting totals: 5492 accepted/assessed fits, 1307 boundary fit failures, one
physically invalid realization, and no profile lower-objective counterexamples.
There is one adjusted undercoverage flag: dense van Genuchten--Mualem at
theta_s=0.3 and sigma=0.002, with 85/99 covered assessed regions, Monte Carlo
SE 0.0350, exact 95% interval [0.7741, 0.9205], and p=0.0004174 against the
0.05/34 threshold. These outcomes do not qualify the F-grid method or any
unflagged scenario, and no thresholds were tuned after seeing results.

The optional interval policy also ran on all real canonical curves. Of 59
Brooks--Corey series, 21 improved best converged SSE and none worsened beyond
tolerance; 20 fits stayed accepted, 37 stayed failed, and one changed in each
direction. Accepted count remained 21, with profile counterexamples falling
from five to zero. A count-only comparison rejects mismatched datasets,
observations, rosters, and non-policy settings. The installed wheel reproduced
the complete real-data fitting artifact byte-for-byte.

A separate count-only predictor readiness join verified all 59 exact unique
master identities and the unchanged predictor audit. Clapp has 24 complete raw
texture inputs, all classification-blocked. The remaining public functions
have no complete inputs on this cohort; all 59 lack the bound sand predictor
for Gunarathna. Canonical target material is still unspecified. Successful fits
therefore do not unlock external PTF scoring. The two new dataset summary
artifacts contain counts and hashes, not raw measurements or predictors.

Verification: **765 tests passed**, Ruff lint/format and ty passed. Tests protect
independent stream assignment, exact resume, corrupt-record detection, binomial
and Clopper--Pearson hand oracles, exact identity joins, workbook binding,
failure-preserving fit comparisons, and between-knot generation.

Next priorities: investigate and validate constrained uncertainty for the flagged
conditional scenario; obtain reviewed compatible predictor values and target
material evidence before external scoring. Additional optimizer restarts or
particle-size metadata on non-overlapping workbook rows do not resolve those
remaining requirements.
# Independent boundary-coverage investigation checkpoint

The flagged van Genuchten--Mualem case now has a separately prespecified
follow-up: five independent blocks of 400 nonlinear realizations, analytic
Jacobian audits of all 200 original cases, paired exact linear-model controls,
and a separate 100000-draw fixed-design Gaussian control. Public fitting,
profile thresholds, parameter boxes, and acceptance gates remain unchanged.

All original analytic full/nuisance audits converged and none improved public
objectives by more than 1e-10. In the original joint-selected cohort the linear
and nonlinear coverage events were identical (85/99). Independent nonlinear
coverage was 937/992, or 94.46%, exact 95% simulation interval
[92.84%, 95.80%], Monte Carlo SE 0.73 percentage points, one-sided p=0.2343.
The large exact linear control covered 94979/100000 overall and 47536/50005
after sign selection. Only three coverage decisions differed among the 986
jointly selected independent realizations.

The independent series did not reproduce the original strong shortfall; the
controls support sampling fluctuation as a possible explanation rather than
identifying a numerical profile-solver defect. The original 34-cell adjusted
flag remains recorded, and no global or real-soil coverage qualification is
claimed. See `BOUNDARY-FOLLOWUP.md` and `boundary-followup-summary.json`.

Verification binds the exact plan, generator, diagnostic implementation,
original source cell, and unchanged public fitting implementation. All 2000
generated error vectors, all derived paired counts, the pooled primary
inference, the first 400 complete fit/profile records, and the 100000-draw
linear control were replayed. The report generator is committed separately
from large local raw records. **767 tests passed** in the full package suite;
hand-derived derivative and coupled-design t-control regression tests passed
again after strengthening, with Ruff and ty passing.

Next work should not retune the F threshold from the old flag. Continued
uncertainty qualification needs prespecified practical tolerances and enough
Monte Carlo precision; external PTF evaluation still needs compatible inputs
and reviewed target-material evidence on the retained real cohort.
# Source-backed Clapp external pilot checkpoint

The 24 raw texture candidates were audited across four primary sources.
Six Panina gray forest horizons have a directly published supported class
and reviewed mineral material; six sod-podzolic horizons have an unsupported
Clapp class. Twelve Badenko/Bolotov/Moiseev candidates remain unresolved for
USDA compatibility. The source-review JSON records PDF hashes, locations,
master rows, depth correspondence and exact selected identities. No Russian
category crosswalk or unsupported Clapp class was invented.

`evaluation/experiments/panina_clapp/run.py` creates a separate checksum-bound
canonical overlay from the original export and reviewed PDF. It preserves
all selected pressures, water values and lineage, adds the directly reported
categorical predictor, and records all horizons as one profile. The global
workbook normalization and predictor mapping are unchanged.

The first nonempty fixed-candidate external check has six eligible horizons
and 56 points. Sample-equal metrics in volume fraction are ME 0.0288498422,
MAE 0.0305541769, RMSE 0.0350360985 and median AE 0.0325632289. Aggregate
confidence intervals are `insufficient_evidence/too_few_groups`, because the
independent profile count is one. The broad tested pressure extent does not
establish pressure-domain validation or national representativeness. See the
count/metric `meta_v3_3.clapp-pilot-summary.json`; raw runs remain local.

Artifact publication exposed a Windows 3.13 inherited temporary-ACL problem.
The writer now creates exclusive publication staging under the destination
parent on Windows, with bounded failure cleanup and atomic rename retained.
POSIX temporary staging is unchanged. Separate-process reading now succeeds;
complete original-plan replay and installed-wheel replay are byte-identical,
and persisted-plan predictions/cohorts match.

Verification: **771 tests passed** in the full package suite; 13 focused
builder/native-run/publication tests passed after final changes. Ruff and ty
passed. The native curve oracle uses the published Clapp silt-loam parameters
at a dry point; other tests protect source hashes, unchanged observations,
unsupported-class rejection, one-profile interval withholding and cleanup of
failed publication on both platform branches.

Next: expand independently reviewed class/material cohorts and source coverage,
and prespecify pressure-domain reporting. The pilot is a concrete end-to-end
external check, not evidence that remaining workbook rows or uncertainty
protocols are qualified.
# Full-catalog completion objective

The completion criterion is a per-dataset decision across all scientifically
eligible implemented functions and supported ensembles, together with explicit
selection blockers, approximation criteria, uncertainty and applicability for
van Genuchten and Brooks-Corey. A successful narrow pilot does not complete
this objective.

The reproducible inventory in
`evaluation/datasets/implemented-function-coverage.json` reconciles all 146
implemented functions with the generated manifest: five emitted, 141 omitted
for incomplete measurement contracts. It identifies 362 missing numeric-input
and 281 missing output descriptor bindings. The inventory resolves shared
definitions and records specification and manifest hashes. Its exact replay
was byte-identical; Ruff and formatting checks passed.

The next implementation dependency is source-reviewed contract migration for
retention-compatible functions, followed by a dataset eligibility matrix and
grouped nested strategy comparison. Other output targets remain in scope but
require their own compatible observations. The completion sequence and the
distinction between parameter intervals, curve uncertainty and applicability
are recorded in `evaluation/experiments/catalog_coverage/README.md`.

# Wosten adapter and full-catalog readiness matrix

The source-reviewed Wosten class-parameter function now enters the generated
manifest with six explicit output descriptors. A source-restricted retention
adapter implements its Mualem van Genuchten convention. The manifest contains
six functions; 140 implemented functions remain omitted. The inventory now
identifies 362 missing numeric-input and 275 missing output bindings.

All retained targets were regenerated through codegen. Deterministic
regeneration reported unchanged output, and the manifest generator test
passed. The package suite passed **784 tests** after the adapter change.
Subsequent focused tests passed **24 tests** covering the readiness matrix,
exact identity joins, predictor gates and adapter behavior. Ruff and ty passed.

`meta_v3_3.function-readiness-matrix.json` preserves all 146 implemented
functions across six source reporting partitions, 59 samples and 549
volumetric observations. It is raw predictor readiness, not scoring permission
or a selected-model result. A missing feature binding no longer counts as
complete raw inputs. The raw Wosten predictor count is correctly zero: no
reviewed Staring class is supplied by the workbook mapping.

The next implementation gap includes gravimetric canonical evaluation:
487 reviewed gravimetric observations are normalized, but the current canonical
retention schema/export accepts volumetric targets only. They must receive an
explicit compatible contract and evaluation path rather than an assumed
density conversion. Fixed-pressure gravimetric PTF contracts remain part of
the complete-catalog objective.

Additional verification: 55 public Python Wosten/manifest tests passed. The
matrix replay was byte-identical across all 876 function/source cells. A
separately executed m=1 probe was rejected by the analytic Mualem oracle,
without modifying production files. Existing Clapp predictions, cohorts,
eligibility and curve-quality artifacts remained byte-identical after the
manifest expansion. An isolated installed wheel reproduced every artifact
from the corresponding current-source Clapp run and passed the new scalar
adapter oracle. Historical source-pinned simulation artifacts were preserved.
# Gravimetric canonical evaluation checkpoint

Canonical dataset version 2 adds an explicit gravimetric contract:
`gravimetric_water_content`, `mass_fraction`, `dry_soil_mass`. Version 1 remains
volumetric-only, and the original volumetric export's semantic checksum is
unchanged. Export selects one quantity and accounts for omitted rows of the
other quantity without a density conversion. The real export retains all 487
mass-basis points from 50 sample curves, including 20 ratios above one.
Together with the 549 volume observations, these account for all 1,036
normalized points. Mass export replay is byte-identical.

Native fixed-output scoring, sample-balanced metrics, aggregate cluster
bootstrap intervals, curve quality and report units now respect the declared
water quantity. Comparisons preserve that quantity, mixed quantities are
rejected, and cohort targets must agree with comparison quantities. Volume
bounds remain [0, 1]; mass ratios are nonnegative without a universal upper
bound. The approximation families and grouped conformal prediction protocol
remain explicitly volumetric-only. New tests protect those rejection gates.

The full package suite passed **794 tests** after the execution changes;
subsequent focused export, physical-contract and unsupported-method tests
passed **51 tests**. Ruff and ty passed. The real mass readiness matrix retains
all 146 implemented functions across five source partitions; metadata and raw
predictor readiness still do not establish scoring permission.

The original Dharumarajan (2019) PDF was reviewed and relevant methods/tables
checked visually. It confirms the two target pressures but does not establish
the mass/volume water-content denominator. Existing YAML warnings already
preserve that ambiguity. The source review now records the blocker and PDF
checksum, so the legacy gravimetric identifier is not mistaken for reviewed
physical semantics. No unsupported contract or class crosswalk was added.

Final verification passed **797 tests** in the full package suite. An isolated
wheel passed all **51** focused normalization, export, unit/basis, native
execution and unsupported-method tests, and loaded the checksum-identical real
mass export. A temporary in-memory mutation imposing an upper bound of one on
mass ratios caused the intended regression test to fail; production files
were unchanged. All 730 mass function/source cells bind the current dataset
and coverage inventory. Readiness does not establish predictive validation.
# Beniaich gravimetric contract migration

The original Beniaich et al. (2023) PDF supports the gravimetric denominator,
disturbed 2-mm-sieved material, hydrometer protocol and organic-matter
processing. Sections 2.2-2.4 and Tables 5-6 were reviewed visually. All 11
implemented linear regressions now have complete measurement descriptors.
The new `organic_matter_content` quantity remains distinct from organic
carbon; method and derivation gates are retained. Source saturation is not
assigned an unreported controlled zero pressure.

The manifest now contains **17 of 146 implemented functions**, with 129
omitted. Remaining gaps are 342 numeric-input and 242 output bindings. All
targets were regenerated; deterministic regeneration was unchanged and all
130 generator tests passed. Public Beniaich/manifest tests passed 34 tests.
The full evaluator suite passed 813 tests; 18 subsequent focused contract,
organic-matter and exact-pressure support tests passed. Ruff and ty passed.

Both real-data readiness matrices and the canonical-volume readiness summary
were rebuilt against the 17-function manifest. The pressure-support audit
reveals no exact 33- or 1500-kPa observations in the 487-point mass cohort.
The 22 fixed-pressure Beniaich outputs therefore have no primary observed
targets in that cohort; 11 saturation outputs have no fixed-pressure
condition. See `meta_v3_3.fixed-pressure-support.json`. No near-pressure snap,
target interpolation, generic humus substitution or method relaxation was
introduced. Native real-function tests use explicitly synthetic inputs and
hand-derived Table 5 oracles; they are not external accuracy evidence.

Next technical dependency: discrete multi-output candidates or an explicitly
registered single-pressure selection loss are needed to compare point PTFs
within grouped nested selection. Existing log-pressure curve selection
requires at least two supported pressures. A single fixed output must not be
treated as a continuous curve. More real-data scoring additionally requires
reviewed predictors, material/method compatibility and observed targets at the
declared pressures, or a separate justified approximation-reference protocol.
# Discrete multi-output grouped selection checkpoint

Evaluation plan version 2 introduces `function_points` / `fixed_outputs`.
One native function can now contribute several explicitly registered output
pressures to the same candidate. Every output retains its physical contract
and method. Converted duplicate pressures and unsupported output conditions
invalidate the whole candidate; intermediate, near and extrapolated pressures
are never supplied. Version-1 plans retain their original types.

The native executor, observation exclusions, target-free forecast gates and
run-method checks all handle finite output sets. Plan resolution and execution
share the same affine conversion implementation. The public numeric-input
path now converts real scalar integers to float before native ufunc dispatch;
a regression test reproduced and protects that previously failing input.

The self-contained `synthetic_discrete_retention` example uses real Beniaich
SLR1/SLR3 functions, six synthetic profile groups and exact FC/PWP targets.
Targets are hand-derived constants, not generated with ptfkit. Grouped nested
selection locks SLR3 for the atomic strategy and trains a convex pair with
left weight 0.25. Changing untouched outer targets to favor SLR1 leaves inner
choices, training evidence and ensemble weights unchanged. Outer losses change
as expected. This is technical evidence, not external accuracy or interval
coverage, and no final strategy is chosen using the best outer test error.

Verification: **829 tests passed** in the full evaluator suite. Fourteen
focused tests also passed from an isolated installed wheel. The wheel
reproduced every current-source example artifact byte-for-byte; input
regeneration was identical. Ruff and ty passed. Two in-memory semantic
mutations were detected: inventing off-support predictions and checking only
the first output's observation method. Production files were untouched by the
probes. Historical source-pinned studies remain unchanged.

The scientific blockers remain: the real mass cohort has no exact FC/PWP
pressure targets and lacks reviewed compatible predictors/material/method
bindings. Single-pressure-only functions still need an explicit selection
loss rather than a degenerate log-pressure integral. The full objective,
including broad source migration, real-data strategy decisions and justified
van Genuchten/Brooks-Corey uncertainty, is not complete.

## HYBRAS inventory checkpoint

Retrieved the official HYBRAS archive and manual into local source review.
The reproducible inventory in `evaluation/experiments/hybras/` records archive
and workbook hashes, 1,075 horizons, 445 profile identifiers and 8,793 raw-table
points. It distinguishes 289 porosity-derived zero-head values from the 7,718
positive-head points. Saturation provenance repeats across each curve, so it
must not cause all points in that curve to be excluded. Two synthetic-workbook
tests protect this distinction and reject observations without horizon metadata.

This is an acquisition/inventory checkpoint, not an additional validation
result. Import still requires per-row provenance, group identity, method and
material compatibility, calibration-overlap and redistribution review. Fitted
and estimated retention columns must remain separate from observed targets.

## HYBRAS positive-head import

Reviewed manual PDF pages 12 and 14 (printed pages 6 and 8), including visual
inspection. Added a checksum-pinned adapter for the positive-head raw table:
7,718 observations, 1,075 horizons, 445 profile IDs and 36 source-reference
groups. Canonical data and complete observation/source comments remain local.
Two independent builds reproduced both dataset and provenance byte for byte.
The canonical dataset hash is
`fb18621135906b4fab7777c28b5383a31e2349bb11b80cb43b737bd8e6824f70`.

All zero-head values are deferred, including the 786 reported saturation
values. Reported cm heads use the standard cmH2O conversion without snapping
to the wide table's approximate kPa labels. Source digitization, averaging
and rounding remain explicit limitations. Physical diagnostics preserve 83
increases in water content across 68 curves without modifying observations.
Material remains unspecified and predictor features empty: this enables
descriptive approximation, not native PTF ranking or independent validation.

Three focused tests cover derived saturation versus positive-head points,
orphan metadata, exact pressure conversion, group identity, comment lineage
and noncorrecting physical diagnostics. Ruff and evaluator type checks pass.
The current evaluator's 63 Python/schema files match the archived wheel saved
with the HYBRAS reproduction scripts. Existing reference-fit boxes remain
computational limits; they do not become validated HYBRAS applicability ranges.

### Pressure review and completed reference fits

Subsequent inspection of every distinct raw comment identified `1atm=1020cm`
for 664 positive-head points in 88 horizons; other comments use `1atm=1033cm`.
The full canonical import now marks the ambiguous points blocked without
changing their heads. The reviewed fitting subset contains 7,054 observations
from 987 horizons, hash
`7ee2c78e07da2ffe97b987e776620ce275390b1e24939a63552f08f3039fd665`.
Earlier preliminary hashes above are retained for provenance, not current
eligibility. The source-review JSON records this additional exclusion.

The preliminary 4,300 independent per-curve reference fits completed. A strict
exact-observation review retains 3,948 fits for the reviewed cohort, with no
refitting or outcome-based cohort exclusions. Accepted counts are 91
Brooks-Corey, 138 van Genuchten Mualem, 120 van Genuchten m=1 and 109 Clapp.
Most rejections are boundary solutions under the existing restrictive boxes.
These findings prioritize broader physically ordered parameter support and
separate review of measured saturation anchors; they do not establish coverage
qualification or identify a best native PTF/ensemble. Tests reject changed
observations or duplicate records when reusing independent descriptive fits.

## Ordered water parameters and broader HYBRAS approximation

Implemented `bounded_trf_ordered_water_multistart_v1` alongside the unchanged
default method. A conditional residual-water fraction enforces physical water
ordering while permitting overlapping declared boxes. The numerical water
separation is 1e-10 volume fraction. Jacobians are transformed back to physical
parameters before identifiability and covariance calculations. Boundary/rank,
conditioning and competing-start gates remain active; the coordinate cap's
nondifferentiable neighborhood produces an explicit rejection. Fixed-parameter
profiles restrict nuisance water ranges to their feasible region.

The run schema and loader preserve the selected method through publication
and replay. Independent formula/finite-difference oracles cover VG Mualem,
VG m=1 and Brooks-Corey, including physical covariance and nuisance profiles.
An in-memory mutation omitting the inverse chain rule failed all three
covariance regressions. The complete suite passed 844 tests; the isolated wheel
passed 18 focused tests and reproduced eight full real-data fit records exactly.

HYBRAS manual PDF page 21 (printed page 15) was visually reviewed for VG bounds.
The new experiment uses those computational boxes, converts alpha from cm^-1
to kPa^-1, and declares separate BC scale/shape bounds. It does not reproduce
the manual's optimizer or saturation-anchor policy. All 1,974 fits completed:
486 VG Mualem and 399 BC fits passed local numerical gates. The paired audit
checks the complete 987-curve roster, unchanged targets and nested physical
boxes. Six formerly accepted fits are rejected; 27 BC fits have worse converged
SSE than the narrower-box baseline, including six locally accepted fits.
These optimizer counterexamples remain explicit uncertainty blockers.

Marginal parameter intervals exceed declared boxes for 327 accepted VG fits
and 130 BC fits; fitted-mean intervals exceed physical bounds for 11 and 5.
The tracked comparison declares `insufficient_evidence` for uncertainty
qualification. More local fits are not evidence of empirical coverage or
external PTF skill. Next audit baseline-seeded/pressure-partition restarts and
parameter profiles, separately review measured saturation, and continue the
original native function/data/ensemble selection work.

The installed wheel subsequently replayed all 1,974 complete fit records
byte for byte against the losslessly repaired first-run stream. Its terminal
summary hash matches the replay stream. Exact first-run sources, replay wheel,
scripts and environment records remain local; historical package hashes were
not rewritten.

## Explicit additional starts and BC counterexample audit

`RetentionFitPlan.additional_starts` now accepts immutable physical vectors in
registered family parameter order. Additional starts append after the original
seeded starts, preserve their solutions exactly, and participate in the existing
acceptance gates. The run schema/loader and nuisance profiles retain them,
including profiles whose declared parameter order differs from registry order.
All four approximation families are covered. Invalid dimensions, nonfinite or
out-of-box values and nonphysical water ordering are rejected. The full suite
passed 862 tests; 48 isolated-wheel tests also passed, including the independent
objective verifier added after that full-suite run.

The source-pinned audit retains all 27 BC cases whose broader-box objective was
worse than the narrower-box baseline. It appends each old best solution as an
additional start and compares seeded, pressure-partition and interval-solve
policies. Every original seeded attempt is checked for exact equality. All 81
refits resolve the known objective regressions within 1e-12; every policy
retains 11 locally accepted fits and 16 boundary rejections. These targeted
counts do not replace the full-cohort results.

Five of the six originally accepted counterexamples remain accepted; one is
now boundary-rejected. The five accepted interval-solve results have 20 explicit
parameter profiles. No lower objective was found on the declared grids, but
six regions reach box boundaries and 13 contain only the fitted estimate.
Grid regions remain approximate diagnostics, not continuous or coverage-qualified
intervals. The independent direct BC plateau/power verifier checked 5,325
converged objectives across fitting and nuisance-profile solves.

All 81 complete refit records, including the 20 profiles, and the terminal
summary reproduced byte for byte from the isolated wheel. Matching code/wheels
are archived with both runs. The count-only verified result is tracked as
`hybras_v1.restart-audit-summary.json`; raw numerical records remain local.
The known optimizer-regression checkpoint is resolved. Continue the original
native function contract/data/selection scope; empirical uncertainty coverage
and separately reviewed saturation observations remain outstanding.


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
