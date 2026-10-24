# Gaussian profile coverage control

This experiment applies the public profile-grid region API to the analytically
solved bounded Gaussian mean model. It is a numerical/inference control, not a
retention curve model. Gaussian observations are latent responses, including
negative values; they are not passed off as physical water-content measurements.

```sh
python evaluation/experiments/profile_coverage/calibrate.py \
  --repetitions 4000 --seed 20261024 \
  --output local/profile-coverage-gaussian.json
```

The output must be new. It records the seed, environment, script hash, model,
truth scenarios, counts, and separate availability/coverage denominators. Two
runs with identical inputs and environment reproduce the artifact bytes.

For each sample of eight iid N(mean, 0.1^2) responses, the least-squares mean is
constrained to [0, 1]. Exact SSE values are supplied at both bounds, the true
mean, and the bounded estimate. The truth is explicitly a grid node, so this
control tests threshold coverage without grid interpolation error. It compares
the public F-region classification with an independently evaluated unbounded
one-sample t interval, following the
[NIST mean confidence-limit formula](https://itl.nist.gov/div898/handbook/eda/section3/eda352.htm).

At a single lower boundary with no upper constraint, negative sample means
make the true boundary the SSE minimum and are always covered. Positive sample
means use the ordinary two-sided t acceptance event. Symmetry gives boundary
coverage (1 + nominal level)/2, or 97.5% at nominal 95%. This is a half-line
reference, not an exact formula for an arbitrary finite box. The opposite-bound
fit count is retained to expose departures from that reference.

The fixed run produced:

| True mean | Covered / available | Covered / interior available | Unbounded t covered / generated |
| ---: | ---: | ---: | ---: |
| 0 | 3900 / 4000 | 1843 / 1943 | 3789 / 4000 |
| 0.02 | 3904 / 4000 | 2800 / 2895 | 3820 / 4000 |
| 0.5 | 3795 / 4000 | 3795 / 4000 | 3795 / 4000 |
| 1 | 3894 / 4000 | 1943 / 2049 | 3793 / 4000 |

The approximate Monte Carlo standard error at 4000 repetitions is 0.34
percentage points for coverage 95%, or 0.25 points for 97.5%. These simulation
frequencies are not exact probabilities. Interior-fit conditioning is a
diagnostic proxy for withholding boundary solutions, not a reproduction of all
retention fit gates or its boundary tolerance. Coverage among selected fits
cannot be substituted for unconditional procedure coverage. Nonlinear model
misspecification, non-Gaussian or dependent residuals, optimizer failures,
parameter correlation, and real-data coverage remain unqualified.
