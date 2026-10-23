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
