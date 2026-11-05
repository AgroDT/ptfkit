# Conditional outer-rule risk: proof and exact calibration

`simultaneous_group_hoeffding_conditional_outer_risk_v1` bounds the conditional
sample risk of each already trained outer rule, jointly within one registered
strategy. It also bounds their equal-fold mean. Selection, preprocessing and
parameter fitting may be arbitrary provided they use only each rule's training
groups. The method does not estimate risk averaged over new training datasets,
the observed sample-weighted cross-validation statistic, or the risk of a final
rule trained on all data. These targets remain distinct in the public API.

## Assumptions and derivation

The independent unit is an IID nonempty group from a named population. The
partition into folds is fixed or independent of all group contents. Within a
group, samples may be dependent and group size may be informative. Population
group size N lies in the preregistered integer interval [m, M], with m >= 1.
Every sample's declared loss lies in [0, B], where B > 0 is another population
assertion. Observed maxima cannot establish these assumptions. All test samples
must have their losses observed; missing losses cannot be silently discarded.

The starting inequality is the bounded-independent-sum result of
[Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830),
also available as a [primary-paper scan](https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf).
Its two-sided bounded-mean form gives a tail probability at most
`2 exp(-2 n epsilon² / range²)`. The following ratio and cross-fit construction
is our application-specific derivation, rather than a claim made by that paper.

For rule j, freeze its training groups and all training-only tuning. A fresh
independent group's total sample loss is S_j. Define

```text
X_j = S_j / (B M),       0 <= X_j <= 1,
Y   = N / M,             m/M <= Y <= 1,
R_j = E[S_j | training_j] / E[N] = B E[X_j | training_j] / E[Y].
```

Let K be the number of outer folds, n_j the test-group count in fold j, and
n the total original independent-group count. Write alpha = 1 - confidence.
For a predeclared family of q policy invocations (q=1 by default), allocate
alpha/[q(K+1)] to each of K numerator events and one denominator event.
Using the empirical test-group mean x_j and the all-group mean y:

```text
c       = ln(2 (K+1) q / alpha),
e_j     = sqrt(c / (2 n_j)),
e_N     = (1 - m/M) sqrt(c / (2 n)),
L_N     = max(m/M, y - e_N),
U_N     = min(1,   y + e_N).
```

Conditional on training_j, its held-out groups remain independent from that
training and IID from the named population. Hoeffding bounds the numerator
failure probability by alpha/[q(K+1)]. Integrating over training preserves that
unconditional bound. Hoeffding separately bounds the denominator event, which
uses every original group size. The union bound limits the probability of any
event failing by alpha/q, and all q policies jointly by alpha. It needs neither independent folds nor independence
between numerator and denominator events. Shared training sets therefore do
not invalidate this construction.

On the simultaneous event, positive population normalization and loss bounds give

```text
R_j in B * [min(1, max(0, x_j-e_j)/U_N),
            min(1,        (x_j+e_j)/L_N)].
```

The lower cap at one keeps a valid ordered interval even off the simultaneous
event. Averaging lower and upper endpoints equally gives a band for
`(R_1 + ... + R_K) / K`. Each R_j is conditional on its own training set; the
coverage probability is over original IID group draws, not conditional on the
whole observed dataset or on successful output. If fits or coverage gates
suppress output, no guarantee of coverage conditional on successful output is
claimed. Failed procedures cannot be dropped and redefined as the original law.

The guarantee applies to one specified strategy per invocation. For q>1, the
plan's `simultaneous_policy_count` applies the declared family allocation without
rounding an adjusted confidence level. Native runs freeze q from the entire
registered policy roster, including failed policies. Separate default q=1 calls
do not supply familywise coverage; unregistered post-hoc choices are not covered.

## Exact calibration

The executable experiment uses independent binary group states with probability
1/2. A low group has one target-zero sample; a high group has h target-one
samples, h in {1, 3}. A constant convex forecast is fitted by sample-balanced
squared loss on the opposite fold. With k high groups among t training groups,
its closed-form forecast is `h k / (h k + t-k)`. Its independent exact population
risk is `[c² + h(1-c)²] / (1+h)`. The loss bound B=1 is known from this constructed
population and the fitted forecast's range, not estimated from observed errors.

With t groups in each of two folds, all `(t+1)²` sufficient-count states are
enumerated. Count-pair (k,l) has exact probability
`choose(t,k) choose(t,l) / 2^(2t)`. Group counts, rather than sample counts, govern
the concentration radius. Within-fold permutations leave this learner, its
group-sum statistics and population risks unchanged, so this enumeration has
the full original-data probability law for this experiment.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/conditional_risk/calibrate.py --groups-per-fold 20 --high-group-size 1 --output local/conditional-risk-20-equal.json
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/conditional_risk/calibrate.py --groups-per-fold 20 --high-group-size 3 --output local/conditional-risk-20-unequal.json
```

The small t=4 control is also registered. Tests separately check high-precision
closed-form radii, informative-size ratio normalization, observed-bound and
fold-membership rejection, vacuous small-sample intervals, finite extreme-loss
arithmetic, exact binomial coverage and nonvacuity, and actual nested-selector
convex refits feeding the interval API. Coverage evidence alone cannot validate
a method that always returns the full prior range.

## Scope in ptfkit

The low-level public API requires complete group losses and explicit training
identities. It checks disjoint test folds, training complements, declared size
and loss bounds, and finite evidence. Population assumptions and fitted-rule
provenance remain the caller's responsibility. Native run integration now checks full sample coverage, registered loss,
resolved grouping, original eligible observations, reproduced losses and fitted
training roles. The optional `conditional_outer_risk` run array explicitly
registers protocol/strategy policies, population assertions and a common family
confidence level. Its full original roster controls allocation even when a
policy fails. See `evaluation/examples/synthetic_conditional_risk/`.

These conditional bands do not replace the outstanding full training-law
selection-process uncertainty work. Publication/profile independence,
representativeness and finite population bounds are not established for the
real workbook. That scientific work remains deferred and unresolved.
