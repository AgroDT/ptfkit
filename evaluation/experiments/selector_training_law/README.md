# Complete-selector training-law calibration

This experiment pushes an explicitly finite IID whole-group population through
the actual public `assess_independent_forecast_training` path: original-group
allocation, inner tuning, full-training refit, untouched test prediction and
training-failure/loss evidence. Its fixed forecasts are mathematical inputs,
not invented native PTF results. Native runs use the same selection core.

The bounded independent-block construction and assumptions are derived in
`../training_law_risk/README.md`. This experiment extends its executable evidence
from manually supplied learner losses to the complete finite-grid learner. It
does not qualify real-workbook measurement compatibility or independence.

## Registered population and learner

Each group repeats one observed curve across all its samples. On the exact
pressure grid (1, 10, 100) kPa, the two curves are:

| Curve | Water-content fractions | Correct boundary |
| --- | --- | --- |
| early | (3/4, 1/4, 1/4) | 5 kPa |
| late | (3/4, 3/4, 1/4) | 10 kPa |

The fixed member forecasts are constants 3/4 and 1/4. The single registered
ensemble switches from the high to the low member, choosing a boundary in
{5, 10} kPa with left ownership. A mismatched curve differs only at the middle
pressure; its sample log-trapezoid loss is (1/2)(1/2)^2 = 1/8. The selected
ensemble therefore has a prior sample-loss bound B=1/8 on the entire population
support. This bound concerns that ensemble strategy, not arbitrary candidates.

The learner has T=2 training groups. Inner two-fold validation fits each
singleton training group, for which the boundary is uniquely identified. There
is exactly one ensemble candidate, so it is selected after both inner fits.
The refit uses every original training sample with equal sample weight. It
chooses the curve with the larger training sample count. Equal counts give the
genuine `unidentifiable_boundary` failure, with no invented tie-breaking model.
H=1 independent test group supplies the block's observed losses.

Group IDs and the allocation seed are fixed before population states are
assigned. Input sample counts cannot change group allocation. The two singleton
inner roles may swap when IDs change, but the complete procedure is invariant
to that swap: both fits exist, only one ensemble competes, and refitting sums
sample losses. This specific property justifies a common block law across
administrative IDs; it is not assumed for arbitrary selectors.

## Independent exact targets

The equal control assigns probability 1/2 to each one-sample curve. Refitting
succeeds only on same-curve pairs, so success probability p=1/2, successful risk
mass M=1/32, and successful-training risk M/p=1/16. Failed-training probability
is 1/2. Unconditional model risk is undefined under this failure policy.

The informative-size population has four whole-group states:

| State | Size | Probability |
| --- | ---: | ---: |
| early | 1 | 1/2 |
| late | 1 | 1/4 |
| early | 3 | 1/8 |
| late | 3 | 1/8 |

E[N]=3/2, while E[N times late indicator]=5/8. The sample-population late
fraction is therefore q=5/12, unlike the group probability 3/8. The probabilities
of selecting early, selecting late and failing are respectively 29/64, 17/64
and 9/32. Consequently:

```text
p = 23/32,
M = [(29/64)(5/12) + (17/64)(7/12)] / 8 = 11/256,
R_success = M/p = 11/184.
```

Using an equal-group test target instead would produce conditional risk 43/736,
differing by 1/736. Discarding failed training would lose the defined mass and
failure targets. The executable oracle checks actual refits against the sample
majority, independently of the selector's loss computation.

## Exact probability enumeration

For each population, enumerate every ordered two-training/one-test state triple
(8 or 64 cases) through the public complete-selector adapter. All fixed forecast
inputs, original memberships, inner evidence, refits, predictions and failure
records for the probed block are retained. The second block in these probes is
a fixed control; only the first block is used to derive the local law.

Collapse local cases only when they have identical sufficient statistics for
the inference kernel: training success, complete test-group size and successful
test-loss sum. The informative population has six states:

| Training | Test size | Loss sum | Probability |
| --- | ---: | ---: | ---: |
| success | 1 | 0 | 75/256 |
| success | 1 | 1/8 | 63/256 |
| success | 3 | 0 | 23/256 |
| success | 3 | 3/8 | 23/256 |
| failure | 1 | unavailable | 27/128 |
| failure | 3 | unavailable | 9/128 |

For a failed learner, zero is used only in the explicitly defined risk-mass
statistic. The stored test model losses remain unavailable. Every group size
still enters normalization. Different original training states can share a
sufficient state because the kernel uses their failure indicator rather than
their training losses; all satisfy the same prior size bounds.

Enumerate every n-block count vector with its exact multinomial Fraction
probability. There are 91 equal-control or 6,188 informative count states at
n=12. Canonical disjoint representatives preserve the kernel's sufficient
statistics; the full selector is not rerun 6,188 times. This is an exact
pushforward/convolution of its exhaustively checked local law, not a Monte Carlo
sample or a success-conditioned draw law. Interval endpoints use the public
kernel's floating-point arithmetic; state probabilities are exact rationals.

The output separately reports joint unconditional coverage, successful-risk
interval issuance and joint error/issuance probability. It makes no nominal
coverage claim conditional on issuance. For n=12, issuing that interval requires
at least six training successes, giving an independent binomial issuance oracle.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/selector_training_law/calibrate.py --population equal_binary --blocks 12 --output local/selector-training-law-equal-12.json
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/selector_training_law/calibrate.py --population informative_four --blocks 12 --output local/selector-training-law-informative-12.json
```

Both populations also register n=4. The regression tests check exact local
probabilities and targets, all count-state probabilities, preserved failures,
informative sample weights and family-level coverage. These experiments do not
transfer a two-group learner's risk to a larger training size or validate the
separate descriptive overlapping-CV statistic.


The `--paired` extension and its distinct joint-success estimand are documented
in [Paired complete-selector training-law risk](paired-risk.md). It retains
both actual learners and exposes the informative-size counterexample to
subtracting separately conditioned risks.
