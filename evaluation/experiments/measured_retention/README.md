# Measured retention reference fits

This descriptive experiment fits the four registered retention families to a
canonical, confirmed measured dataset without requiring PTF predictors. It does
not train or assess a PTF, rank families, or establish independent soil samples.
Keep exported measurements and fitting artifacts in ignored `local/` storage.

From the repository root, using the `ptfkit-eval` environment:

```sh
python evaluation/experiments/measured_retention/fit.py \
  local/meta-v3-3-canonical-export.json \
  --output local/meta-v3-3-reference-fits.json
```

The output path must be new. The artifact embeds the complete canonical dataset,
its semantic and file hashes, the script hash, dependency versions, every fit
plan, optimizer attempts, identifiability diagnostics, accepted parameters and
local uncertainty, failed fits, and noncorrecting physical curve diagnostics.
Replay with the same environment to a different path to compare exact bytes.
Flagged or unconfirmed observations are rejected before fitting. Physical
increases found by the diagnostic are retained without smoothing or exclusion.

Parameter boxes, seed 7123, three starts, and the minimum two-decade positive
pressure span follow the existing synthetic retention example. They are an
initial engineering policy, not source-validated bounds for every measured soil.
Boundary failures remain failures; bounds are not widened after observing them.
The material basis is inherited unchanged from the canonical dataset, including
`unspecified`. Local Student-t intervals retain the fitting API's independent,
homoscedastic residual assumptions; this experiment does not validate those
assumptions or qualify intervals as PTF prediction uncertainty.

The 549-point, 59-series `meta_v3.3` canonical export produced 236 attempts under
this policy: 133 accepted fits, 86 boundary failures, 13 nonidentifiable fits,
and four insufficient-observation failures. Accepted fits by family were 35
van Genuchten--Mualem, 43 van Genuchten with m=1, 21 Brooks--Corey, and 34
Clapp gradual air entry. These counts describe this policy and export only.

Each result also includes `uncertainty_support`, computed without altering the
fit or its intervals. On the same export, 67 accepted fits have parameter
intervals extending beyond their declared fit boxes, 12 have mean-curve
intervals outside [0, 1], and 44 have conditional prediction intervals outside
[0, 1]. These overlapping counts concern different interval types. Exact
endpoint contact is allowed. A failed fit reports `fit_failed`, not a clean
interval assessment. Containment does not establish interval coverage.

The diagnostic follows the distinction in the
[SciPy covariance documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html):
local covariance depends on a linear approximation around the optimum. Support
checks expose a limitation of the resulting symmetric intervals; they neither
validate local linearity nor replace a justified constrained uncertainty method.

Add `--profile-saturation-points 5` to calculate bounded nuisance-refit profiles
for `theta_s` on every accepted fit. The grid includes five evenly spaced
declared-box values and the fitted estimate. Failed fits retain a null profile.
Each profile records its baseline objective, parameter order, all starts and
outcomes, and the smallest converged objective at each grid value. A missing
objective means no start converged; it is not interpolated or replaced.

The public `profile_retention_parameter` API accepts explicit grids for any
family parameter. Profiling fixes that parameter and optimizes the others,
following the numerical principle described in the
[JMP profile-likelihood reference](https://www.jmp.com/support/help/en/19.2/jmp/statistical-details-for-profile-likelihood-confidence-limits.shtml).
This implementation provides a grid diagnostic, without confidence thresholds,
root searches, globally certified minima, or coverage claims. Its bounded local
solutions expose objective geometry without clipping the previous intervals.

The real-data run produced 133 saturation profiles / 798 grid points, with a
converged nuisance solve at every point and byte-identical replay. Five profiles
improved the original fitted SSE by more than 1e-10. Original fit acceptance is
therefore not a global optimality certificate; investigate these cases before
interpreting objective thresholds. The experiment retains the original fit.

`assess_profile_optimality` compares grid SSE with baseline using explicit
absolute and relative tolerances: improvement must strictly exceed
`atol + rtol * abs(baseline SSE)`. The measured experiment uses `atol=1e-10`
and `rtol=0`. Missing grid solves remain distinct from no improvement; a clean
assessment does not certify global optimality.

For a detected improvement, the experiment starts a separate full fit from the
best converged profile solution, freeing the profiled parameter again. The
original bounds, seed, restarts, and acceptance diagnostics remain in force.
The changed initial values are recorded in the separate `profile_refit` plan.
An exact boundary start is reported as `profile_start_on_boundary`, without
nudging it into the box. The original fit and aggregate counts are preserved.
All five real-data counterexamples produced accepted full refits with lower
SSE (approximately 16--29% reduction from the original fit).

Every accepted full refit is audited again across all family parameters, using
the same grid size plus each refitted estimate. `profile_refit_audit` records
these profiles, their objective comparisons, and updated interval support
diagnostics. It is null when there is no accepted full refit. The five measured
Brooks--Corey refits produced 20 follow-up profiles without a further improvement
exceeding 1e-10 on these grids. This finding remains local to the declared grids
and optimization policy; it does not validate confidence interval coverage.

Post-refit audits also record `approximate_grid_region` at the fit plan's nominal
confidence level. The single-parameter extra-SSE rule is
`SSEmin * (1 + F(1, n-p; level)/(n-p))`. Each generated profile records residual
degrees of freedom and its original parameter bounds. Missing metadata or grid
solves, an improved baseline, zero residual variance, or a grid omitting either
box endpoint withhold this assessment. Accepted node runs stay separate, with
explicit flags when they reach either declared bound. No interpolation or
continuous confidence endpoint is supplied.

This is approximate nonlinear inference conditional on iid Gaussian,
homoscedastic residuals, the model, box constraints, and adequate optimization.
It is not simultaneous inference or a calibrated boundary-aware interval.
The workbook's residual assumptions and coverage have not been validated.

Use `--brooks-corey-policy brooks_corey_interval_solves_v1` to run the optional
interval solver on real canonical curves. Other family policies, original
observations, and non-policy fit settings remain unchanged. The adjacent
`compare.py` command reports counts only and rejects comparisons with different
dataset hashes, sample/family rosters, observations, or non-policy settings.

```sh
python evaluation/experiments/measured_retention/compare.py \
  --baseline local/meta-v3-3-profile-regions.json \
  --candidate local/meta-v3-3-measured-interval-policy.json \
  --output local/measured-policy-comparison.json
```

On the 59 real Brooks--Corey series, 21 best converged objectives improved by
more than 1e-10 and none worsened beyond 1e-12. Twenty accepted fits stayed
accepted, 37 failures stayed failed, one accepted fit became failed, and one
failed fit became accepted. The accepted count stayed at 21; profile
counterexamples fell from five to zero. These are descriptive optimizer results,
not external PTF predictive accuracy or evidence of interval coverage.
