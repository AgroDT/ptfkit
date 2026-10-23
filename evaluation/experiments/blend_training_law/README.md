# Exact blend-interval training-law calibration

This experiment runs the public complete-selector block adapter for an actual
finite-grid blend learner, then verifies its complete normalized probability
law and every confidence-count state. Fixed forecasts are mathematical inputs,
not fabricated native PTF results. Native selection uses the same fitting core.

## Prior finite population and independent oracle

Two candidate blend intervals, (1,100) and (10,100) kPa, mix the constants 3/4
and 1/4 with linear weights on a log10 pressure axis. The measured grid is
(0.1,1,10,100,1000) kPa. The early curve is (3/4,3/4,1/2,1/4,1/4); the late curve
is (3/4,3/4,3/4,1/4,1/4). Each group repeats one curve across all its samples.

A wrong interval differs only at 10 kPa, by 1/4. The interior log-trapezoid
weight is 1/4, so sample loss is (1/4)(1/4)^2=1/64. This proves the prior bound
B=1/64 for the registered ensemble on its entire finite support. The bound does
not cover arbitrary competing atomic predictions; only the ensemble is bounded
by this experiment's inference policy.

The complete learner uses T=2 training groups and two singleton inner folds.
Each singleton identifies a unique interval and the sole ensemble candidate is
selected. The full-training refit chooses the sample-count majority, with
balanced opposing counts giving `unidentifiable_blend_interval`. No default
interval is invented. The test group remains untouched and H=1.

The equal control assigns probability 1/2 to each one-sample curve. The
informative population assigns probabilities (1/2,1/4,1/8,1/8) to early-one,
late-one, early-three and late-three groups. The sample-population late fraction
is E[N_late]/E[N]=5/12. Training selects early/late/failure with probabilities
29/64,17/64,9/32. Its independent targets are:

| Population | Success probability | Risk mass on success | Successful-training sample risk |
| --- | ---: | ---: | ---: |
| equal | 1/2 | 1/256 | 1/128 |
| informative | 23/32 | 11/2048 | 11/1472 |

Unconditional model risk is undefined under the failure policy. Every ordered
training/test state triple (8 or 64) runs actual allocation, inner fitting,
refitting, test prediction and loss accounting. Original group IDs are assigned
before values. Full input, score, fit and failure traces are retained. Unequal
training sizes must favor the sample majority; equal-group averaging would
incorrectly create extra failed fits.

## Exact normalized-law equivalence

The reference experiment in `../selector_training_law/` has a mismatched loss
of 1/8. Both learners have the same sample-majority/failure law and their losses
divided by prior B are exactly 0 or 1. The normalized group-size and successful
loss statistics therefore agree, not merely their empirical coverage.

The blend experiment independently computes its actual local probabilities and
checks equality with the reference normalized sufficient law before reusing its
multinomial count vectors and disjoint-role materializer. It then runs the public
bounded kernel on actual blend representatives for every count state. Every
normalized moment, success interval and risk interval is checked: risk endpoints
must be exactly one eighth of the switch endpoints. This binary scaling also
preserves floating-point endpoints without introducing nonbinary roundoff.
Joint coverage is independently checked against the blend population targets.

At n=12 there are 91 equal-control or 6,188 informative count states. All failed
training remains in the draw law, with unavailable model losses and preserved
test-group sizes. State probabilities are exact Fractions; CI endpoints use the
public floating-point kernel. Conditional-interval issuance and joint error/
issuance are reported separately from joint unconditional coverage.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/blend_training_law/calibrate.py --population equal_binary --blocks 12 --output local/blend-training-law-equal-12.json
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/blend_training_law/calibrate.py --population informative_four --blocks 12 --output local/blend-training-law-informative-12.json
```

Both populations also register n=4. This qualifies only the stated finite-law
construction and the two-group learner; it does not transfer risk to larger
training sets, establish fitted-interval parameter confidence or validate
scientific workbook compatibility. The native example in
`evaluation/examples/synthetic_learned_blend/` is a separate provenance/replay
demonstration using actual PTF forecasts.


## Separate point-score assessment

Pass `--point-metric mae` or `--point-metric mse` to retain the same complete
log-loss-trained learner while assessing equal point weights within each sample.
A mismatched learned blend differs from its target at one of five pressures by
1/4. Its sample MAE is 1/20 and sample MSE is 1/80; curve log-MSE is 1/64.
Every actual local fit is rerun and its full `point_losses` evidence retained.
The exact normalized sufficient-state law remains the same, with nonbinary
floating-point interval rescaling checked to numerical tolerance. All 6188
informative count states are assessed by the production bound independently.

For the informative population, success probability is 23/32, MAE risk mass
11/640 and successful-training MAE 11/460; MSE risk mass is 11/2560 and
successful-training MSE 11/1840. These are separate registered functionals.
The square root of 11/1840 describes pooled successful-training RMSE. It differs
from expected per-training RMSE, which here is
(29 * sqrt(1/192) + 17 * sqrt(7/960)) / 46. No interval for that latter target
is claimed. Point-metric qualification does not change model selection, prior
totality, conditional-on-issuance limitations or independence requirements.
