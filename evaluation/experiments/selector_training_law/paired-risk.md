# Paired complete-selector training-law risk

The native `paired_training_risk` policy and low-level
`bound_paired_independent_training_risk` compare two complete learners on the
same original training and test group roles. Orientation is left minus right.
The sample loss remains the registered complete log-pressure MSE. This is a
risk difference, not a ratio or an interval for the difference between fitted
weights. It does not compare observed overlapping-CV means.

## Target and exact transformation

Let I(D) indicate that both learners return trained rules on the same fresh
T-group training dataset D. Each learner's sample loss must lie in [0,B], with
the bound fixed from population knowledge. Denote their sample-population risks
by R_left(D) and R_right(D) when they exist. The targets are:

```text
p = P(I(D)=1),
M_delta = E[I(D) (R_left(D)-R_right(D))],
delta_success = M_delta/p,                      if p>0.
```

On joint success, map the two complete sample losses to

```text
U = ((loss_left-loss_right)/B + 1)/2,             in [0,1].
```

Subtracting the bounded nonnegative losses first preserves identical binary
differences across different absolute loss levels. That difference remains
within [-B,B], so it cannot overflow. Dividing before the shift avoids forming
`2*B`. Apply the existing independent-block bounded-mean kernel
to U and the joint training-success indicator, with prior loss bound one.
It jointly bounds p and M_U=E[I R_U(D)]. The sample-population denominator
remains E[N]; adding a constant per sample is preserved even for informative
group size. Therefore:

```text
M_delta = B (2 M_U - p),
delta_success = B (2 M_U/p - 1).
```

Signed mass endpoints follow from the simultaneous rectangle for M_U and p,
intersected with [-B p_upper, B p_upper]. Successful-training risk-difference
endpoints are the affine image of the kernel's successful-training U interval.
No independence between learners, losses, size and success events is required.
The underlying three-event allocation is unchanged. This is an algebraic use of
the documented bounded-group construction, not a separate published CV theorem.

The result records `half_shifted_normalized_sample_loss_difference_v1`. Its
`transformed_bound` contains the positive-kernel calculation; the nested loss
descriptor names the original component loss domain. Its normalized U risk is
not the squared error of another predicted retention curve. The outer signed
fields are the actual paired estimands.

One-sided training failures remain in p and all test-size denominators. The
successful rule's losses may still be retained, but no paired model error is
invented for the undefined other rule. A missing test loss on joint success
suppresses inference. A failed-training reason must be established using only
training data. Per-learner bounds are checked before subtraction, so two
out-of-bound errors cannot cancel into a seemingly acceptable zero difference.
Both learners must have identical original block memberships and roles.

An unconditional model-risk difference requires prior joint learner totality;
observed success alone cannot establish it. If any training contradicts that
assertion, no interval is issued. Otherwise the unconditional difference is the
same affine transformation of the kernel's total-learner risk interval.
Issuance of a joint-success conditional interval is a random event; coverage is
joint and unconditional, not nominal conditional on issuance.

## Exact complete-selector experiment

The same finite group populations and actual selector probes as the main
experiment are used. The inner-selected atomic competitor is the high or low
constant curve. On a unique training majority it matches the learned switch's
direction. Its loss is always 1/16 greater than the switch's loss on any test
curve. Hence delta_success=1/16 on the full population support of joint success.
Both raw model losses are bounded by B=3/16. The atomic strategy always trains;
the switch fails on a balanced training sample count.

For the informative population, joint success is p=23/32 and M_delta=23/512.
The atomic procedure's marginal mean risk is 129/1024; the switch's mean risk
conditional on its own successful training is 11/184. Subtracting those yields
1559/23552, unlike the paired joint-success target 1/16. The equal-size control
hides this distinction because symmetry makes both differences 1/16.

Every actual local probe retains both trained rules, the successful atomic
test losses and unavailable switch losses on failure. The joint law collapses
to two equal-control or four informative sufficient states. At n=12 this gives
13 or 455 exact count states. Independent count probabilities and conditional
targets test the implementation; no failed training is dropped.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/selector_training_law/calibrate.py --population equal_binary --blocks 12 --paired --output local/selector-paired-law-equal-12.json
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/selector_training_law/calibrate.py --population informative_four --blocks 12 --paired --output local/selector-paired-law-informative-12.json
```

The native example is `evaluation/examples/synthetic_training_risk/paired-run.json`.
It uses actual PTF forecasts and four-group learners; it is a separate replay
demonstration, not the mathematical two-group law above. The paired comparison
has its own confidence allocation. It does not inherit joint coverage with
separately registered marginal, conditional outer-risk or metric families.
Scientific workbook compatibility and real sampling assumptions remain unresolved.
