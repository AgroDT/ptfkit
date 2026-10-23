# ptfkit-eval extended implementation progress

Current authorized window ends at **23:28 UTC on 2026-10-23**
(02:28 Europe/Moscow on 2026-10-24), following explicit renewal.
Latest verified component checkpoint: **698 passing tests**.
Online primary-source review is active; unavailable original workbook materials
remain a separate blocker. Historical session contracts below are preserved.

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
