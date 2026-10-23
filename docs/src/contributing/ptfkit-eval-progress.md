# ptfkit-eval extended implementation progress

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
