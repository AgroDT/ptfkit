# Complete sigmoid learner on a finite group population

The two mathematical atomic forecasts are constants 1 and 0. The two registered
gates have center 10 kPa and steepness ln(2) or 2*ln(2), per log10 pressure decade.
On pressures 1, 10, 100 kPa, their curves are (2/3, 1/2, 1/3) and
(4/5, 1/2, 1/5). These rational targets are declared independently of production
routing. They define mathematical controls, not PTF or workbook predictions.

Log-pressure trapezoid weights are (1/4, 1/2, 1/4). Matching loss is zero and
mismatch loss is 2/225; actual floating-point losses are checked to tolerance.
The prior bound 1/64 exceeds that support loss and is not estimated from test
errors. Each actual two-group learner runs singleton inner folds and a complete
outer-training refit. It selects the sample-majority curve; equal opposing sample
counts retain `unidentifiable_sigmoid_parameters`. Unequal group sizes therefore
distinguish sample weighting from equal-group weighting.

The equal population assigns probability 1/2 to each one-sample curve. The
informative population assigns early/late one-sample groups probabilities 1/2,
1/4 and early/late three-sample groups 1/8 each. Every ordered training/test
triple runs the public complete-selector API, retaining original groups, raw
forecasts, inner fits, outer refits and failed test evidence. There are 8 or 64
actual local cases. Their six/three sufficient-state law matches an independently
qualified sample-majority reference after checking the local law. This learner
is permutation invariant because the inner folds are singletons and there is
only one ensemble. That does not justify convolution for arbitrary learners.

The generic original-role renamer materializes all 91/6,188 twelve-block count
states. Every state is evaluated by the production risk kernel. Multinomial
probabilities are exact Fractions; confidence endpoints use ordinary floating
arithmetic. Rational population truths are checked against independently derived
curve losses, with explicit numeric tolerance. Failed training remains in the
success law and has no invented zero-error model.

Informative truths are success=23/32, successful risk mass=11/3600 and
successful-training sample risk=22/5175. Equal controls are 1/2, 1/450 and 1/225.
No unconditional model risk is asserted. At 12 blocks, success-bound errors are
independently checked against binomial tails; issuance requires at least six
successes. Error-and-issuance probability is reported without claiming coverage
conditional on issuance.

From the repository root:

```sh
uv run --project targets/ptfkit-eval python evaluation/experiments/sigmoid_training_law/calibrate.py --population informative_four --blocks 12 --output local/sigmoid-training-law-informative-12.json
```

This qualifies the declared finite mathematical law and fixed training size.
It establishes neither scientific IID source groups nor real-workbook coverage,
pressure monotonicity, soil-property gates or parameter uncertainty.
