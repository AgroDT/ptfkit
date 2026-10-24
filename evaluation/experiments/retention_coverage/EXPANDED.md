# Prespecified expanded coverage study

`expanded-plan.json` fixes 34 cells and 200 repetitions per cell (6800 total)
before execution. The seed is fixed and each cell receives an independent,
identifier-derived stream, so cell order and resuming do not change samples.

The dense design crosses saturation truth 0.3, 0.305, and 0.5 with Gaussian
noise standard deviation 0.002 and 0.01 for all four families. A sparse design
adds saturation 0.3 and 0.5 at noise 0.002 for all four families. Two additional
Brooks--Corey dense interior cells place air entry at 7.5 kPa, between pressure
knots, at both noise levels. The ordinary air-entry truth is 10 kPa. Other true
parameters remain theta_r=0.1, alpha=0.1/kPa, n=2, Brooks--Corey lambda=0.5,
and Clapp saturation suction=1 kPa with b=4, as applicable. Clapp's positive
generating pressures remain on its dry branch.

```sh
python evaluation/experiments/retention_coverage/expanded.py \
  --output local/retention-expanded-new
```

Reusing the same output resumes completed cells after checking their hashes,
study configuration, implementation hashes, versions, counts, and record
lengths. A differing context or corrupt cell fails rather than being replaced.
Every generated observation and fit/profile outcome remains in the local cell
artifact. `summary.json` is emitted only after the entire matrix is complete.
Raw cell artifacts remain local; they are not needed in version control.

The study follows the design/reporting principles in
[Morris, White and Crowther (2019)](https://doi.org/10.1002/sim.8086): explicit
aims, generators, estimands, methods, performance measures, and Monte Carlo
uncertainty. It evaluates the fixed interval-solve Brooks--Corey policy and
unchanged other-family policies. It does not choose a policy by coverage.

Each cell reports coverage among assessed regions, estimated Monte Carlo SE,
and an exact 95% Clopper--Pearson interval for that simulation probability.
These intervals are descriptive, not simultaneous intervals for all cells.
A prespecified one-sided exact binomial test against 0.95 uses the Bonferroni
threshold 0.05/34 to flag evidence of undercoverage. No flag establishes
adequacy. The coverage test concerns the conditional simulation probability
after assessment, not the probability of returning a covering region among all
generated samples; all failure and availability denominators remain visible.

With only 200 generated repetitions per cell, expected Monte Carlo SE near
95% is about 1.5 percentage points before withholding reduces the denominator,
or about 2.2 points at 100 assessed regions. This study can reveal substantial
problems but cannot certify small departures from nominal coverage. It does not
qualify workbook residual assumptions, knot smoothness, or real-soil coverage.

The completed run is summarized in `expanded-summary.json`. Of 6800 generated
realizations, 5492 fits were accepted and assessed, 1307 were boundary failures,
and one was physically invalid. No lower-objective profile counterexample
remained. These are accounting totals, not a pooled coverage claim.

One cell met the prespecified undercoverage criterion: dense-grid van
Genuchten--Mualem at saturation 0.3 and noise 0.002 covered truth in 85/99
assessed regions. The estimated conditional probability is 85.86%, Monte Carlo
SE 3.50 percentage points, and exact 95% interval [77.41%, 92.05%]. The
one-sided p-value 0.0004174 is below 0.05/34. This is evidence against nominal
coverage for that simulated conditional procedure, not evidence that every
other scenario is adequate. No confidence threshold or bounds were retuned.

Exact executed runner/generator/plan snapshots and a wheel whose source hash
matches the study context are retained under the local run's `reproduction/`
directory. Resume the completed context with its archived entry point:

```sh
python local/retention-expanded-6800/reproduction/expanded.py \
  --output local/retention-expanded-6800
```

This replay verified every saved cell and left all artifact bytes and file
modification times unchanged. Later repository changes, including formatting,
can change the strict context hash; use a new output directory for a changed
runner rather than weakening compatibility checks.
