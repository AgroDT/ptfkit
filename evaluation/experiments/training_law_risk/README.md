# Independent-block training-law risk and failure

`independent_blocks_group_hoeffding_training_law_v1` targets a learner repeated
on new training datasets. Each block has T training groups and H test groups;
every original group appears in exactly one role in one block. The entire
learner, including candidate selection, preprocessing and parameter fitting,
must use only that block's training data. Blocks are allocated independently
of group contents. Shared data-derived tuning across blocks is not permitted.
The learner/plan and any fixed seed are preregistered; averaging over additional
algorithmic randomness requires independent block-local randomization.

This differs from reusing fixed cross-fit predictions, resampling a fitted
model's rows, or averaging risks conditional on overlapping training datasets.
It deliberately requires new independent training/test blocks and reports the
effective training size T. It does not infer the risk of a final model trained
on a larger dataset.

## Target and failure law

Groups are IID from a named population, with prior nonempty size bounds
`m <= N <= M` and sample-loss bound `0 <= loss <= B`. Within a group, sample
dependence and informative group size are allowed. Losses must correspond to
the registered complete per-sample loss, including its pressure domain.

Let D be a fresh T-group training dataset, I(D) the indicator that training
succeeds, and R(D) the trained rule's sample-weighted population risk when it
exists. Success or failure is determined exclusively from training. A test
prediction/coverage failure cannot be relabeled as a training failure.

The estimands are:

```text
p = E[I(D)],
F = 1-p,
M_success = E[I(D) R(D)],
R_success = M_success / p,              if p > 0.
```

The product defining risk mass is zero on failed training, without defining a
model error there. It is neither an invented zero-error model nor a reason to
drop a block. An unconditional model risk is undefined if the learner can fail.
Only a prior, independently justified `total_learner=True` assertion makes
`E[R(D)] = M_success` a valid target. Observing no failures cannot establish
totality. Any observed failure contradicting that assertion suppresses all
intervals with an explicit reason.

## Derivation

The starting bounded-independent-mean inequality is from
[Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830). The following
independent-block ratio/failure construction is our application-specific
derivation. It does not rely on a new published CV variance estimator.

For block b, let S_b be the sum of all H test groups' sample losses after
successful training and let N_b be their total sample count. Define

```text
X_b = I_b S_b / (B H M),     in [0,1],
Y_b = N_b / (H M),           in [m/M,1],
Z_b = I_b,                  in [0,1].
```

For failed training, X_b is the defined risk-mass contribution zero; Y_b still
uses the complete original test roster and Z_b is zero. No failed block is
discarded. Independent training and test roles give

```text
E[Y_b] = E[N]/M,
E[X_b] = E[I(D) R(D)] E[N] / (B M),
M_success = B E[X_b]/E[Y_b],
p = E[Z_b].
```

The normalization remains sample-weighted even when group size is informative.
Replacing it by an equal-group error mean changes the target. Taking the mean
of finite test ratios would also introduce finite-denominator bias.

For n preregistered blocks and q preregistered policy invocations, allocate
alpha/(3q) to each of the three two-sided concentration events. Write

```text
c   = ln(6q/alpha),
e_X = e_Z = sqrt(c/(2n)),
e_Y = (1-m/M) sqrt(c/(2nH)).
```

X and Z are independent across blocks, so n controls their radii. Group sizes
are independent across all nH test groups, permitting the smaller denominator
radius. Samples within a group and test losses within a fitted-model block are
not treated as independent. No independence between X, Y and Z is needed for
their union bound.

Intersect the population means with their known ranges. Positive Y bounds give
an interval for risk mass by dividing the X interval by the Y interval and
multiplying by B. Since `M_success <= B p`, its upper endpoint can additionally
be limited by B times the success-probability upper bound. Off-event endpoint
ordering is preserved; on the simultaneous event no true parameter is removed.
Complement the success interval to bound failure probability. If its lower
endpoint is positive, divide the mass interval by the success interval to bound
R_success, intersecting with [0,B]. Otherwise that target remains unavailable
with `success_probability_not_separated_from_zero`.

The joint error probability is at most alpha/q per invocation and alpha over q
declared invocations. A conditional-risk interval is issued only when success
is separated from zero. The guarantee concerns the unconditional probability
of error and issuance, not coverage conditional on the inference procedure
issuing an interval. No success-conditioned renormalization is performed.

## Exact experiment

Each block draws independent fair binary training/test group states. A low
group has one target-zero sample; a high group has h target-one samples, h in
{1,3}. All pressure-grid targets and forecasts are constant, so squared error
is exactly the registered sample loss. The training rule fits its state's
constant target. In the failure version, state-one training is deliberately
unsupported; in the total version both states are supported. The population
loss bound B=1 follows from this construction.

The four train/test state pairs AA, AB, BA, BB have equal probabilities. With
n blocks, sufficient count vector (a,b,c,d) has probability
`n! / (a! b! c! d! 4^n)`. All count vectors are enumerated; the statistics and
the learner are invariant to block permutation, so this is the full draw law.

In the failure version, `p=1/2`, `M_success=h/[2(1+h)]`, and
`R_success=h/(1+h)`. No unconditional model risk is defined. In the total
version, `p=1` and average model risk is 1/2 for either h: its two training
states produce constants zero/one and complementary population risks.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/training_law_risk/calibrate.py --blocks 12 --high-group-size 3 --output local/training-law-12-failure.json
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/training_law_risk/calibrate.py --blocks 12 --high-group-size 3 --total-learner --output local/training-law-12-total.json
```

The equal-size controls and n=4 designs are also registered. Exact experiment
outputs retain joint coverage, probability of issuing a successful-training
risk interval, and probability of simultaneous issuance and error. They never
report nominal coverage conditional on successful output. Tests also challenge
the method with shared/dropped groups, invented zero losses for failed models,
partial successful-block test coverage, prior-bound contradictions, falsely
asserted totality, informative sizes and extreme finite loss sums.

## Scope in ptfkit

This is a low-level public inference API. Callers supply and retain all original
block records and own population assertions, training-only learner provenance
and loss reproduction. The API rejects group reuse and requires exactly the
registered number of blocks and role counts. It never uses source/profile IDs
alone as evidence of independence. Missing successful-block test losses cannot
change the population or become a training failure.

Native block allocation, complete selector reruns per block, run registration
and provenance artifacts are now implemented separately from this exact kernel
experiment. Real-data population assumptions remain unestablished.
This construction supplies no CI for the existing overlapping-fold CV statistic
and does not transfer a T-group algorithm-risk estimate to larger training sizes.


The separate public `allocate_independent_training_blocks` helper now provides
complete original-group roles from an exact roster and a registered seed. It
uses no target, forecast or sample-count balancing and rejects unresolved
profile IDs. Administrative identities must be value-independent. This does
not itself orchestrate native learners or turn overlapping folds into independent
blocks. The separate complete-selector adapter and native run registration now
repeat selection/refitting on these roles and retain full evidence; see
`evaluation/examples/synthetic_training_risk/`.
