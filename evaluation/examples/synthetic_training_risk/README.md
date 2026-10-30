# Synthetic whole-selector independent training blocks

This example reuses the explicitly constructed IID binary-group population in
`../synthetic_conditional_risk/`. Its generator, observed data and finite
prediction/target support establish the declared two-sample group size and
sample-loss bound one. It supplies twelve original groups; each is assigned
exactly once to two blocks of four training and two test groups.

The registered native atomic and ensemble procedures repeat their own inner
selection on each training block and refit the selected learned pair there.
The parent nested-CV choices and fits are not reused. Original memberships,
all inner evidence, locked choices, fits, test forecasts and sample losses are
retained in `independent-training-risk.json` with the input snapshots and
integrity-checked report. Fixed native forecasts can be cached because their
inputs have no learned preprocessing.

From the repository root:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval run evaluation/examples/synthetic_training_risk/run.json --output local/synthetic-training-risk
```

The two requested strategies form their own 95% simultaneous family. Failed
policies remain in that family and all allocated blocks remain in the draw law.
The confidence family is separate from descriptive metric/bootstrap intervals
and any conditional outer-rule risk policy family.

Two blocks give conservative, uninformative bounds: successful-training risk
cannot be issued when the success-probability lower bound is zero. This small
example demonstrates reproducibility and complete training/failure accounting;
it does not demonstrate useful precision. Increasing the number of overlapping
CV folds or bootstrap draws cannot increase its independent block count.

The plan deliberately sets `total_learner=false`; no unconditional model-risk
interval is inferred from observing successful fits. The target is the learner
trained on four fresh groups, not a final twelve-group model. The exact finite
training-law calibration and derivation are in
`evaluation/experiments/training_law_risk/`. No workbook scientific blocker is
resolved by this synthetic run.

## Larger independent design

`generate.py` draws a new IID state for every original group and writes a
self-contained input directory with checksum-bound dataset and candidate plan.
Population and allocation seeds are separate preregistered choices. Generation
metadata records both; the population seed is also embedded in the dataset ID
that survives native run snapshots. Existing output directories are rejected.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/examples/synthetic_training_risk/generate.py --blocks 20 --metric-resamples 64 --output local/training-risk-20-inputs
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval run local/training-risk-20-inputs/run.json --output local/training-risk-20-run
```

Twenty blocks require 120 genuinely new groups (240 samples), retaining four
training and two test groups per block. This increases independent evidence
without changing the effective training size. Metric bootstrap draw count is
separate from block inference; changing it does not change the risk bounds.
The registered seed produces no training failures and a success-probability
interval approximately [0.62984, 1]. The successful-training sample-risk upper
bound is approximately 0.59564 for both strategies, below the prior bound one.
The ensemble is actually refitted in every block. Unconditional model risk
remains unavailable because prior totality is deliberately not asserted.

These conservative intervals demonstrate that additional original independent
blocks can make the bounds nonvacuous. They do not establish precision for a
real soil population. Do not choose seeds or regenerate until a desirable
interval appears. Original workbook unit/method and sampling assumptions remain
unresolved; this generator contains only the declared synthetic population.


## Paired training-law comparison

`paired-run.json` registers one atomic-minus-ensemble comparison on shared
training and test blocks. It reports joint training success/failure and the
signed sample-risk difference when both rules can be trained. It does not
subtract marginal conditional risks with potentially different success events.
The complete successful rule is retained when only the other learner fails.
Its confidence allocation is separate from any marginal policy family.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval run evaluation/examples/synthetic_training_risk/paired-run.json --output local/paired-training-risk
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/examples/synthetic_training_risk/generate.py --paired --blocks 20 --metric-resamples 64 --output local/paired-training-20-inputs
```

The generator preserves population/allocation seed separation and the same
four-training/two-test-group law. Full actual fit, loss and one-sided failure
records are written to `paired-training-risk.json`. For the bounded affine
construction and the exact mathematical population calibration, see
`evaluation/experiments/selector_training_law/paired-risk.md`.


Add `--point-metrics` to register a separate four-policy MAE/MSE family while
keeping the same dataset, log-pressure learner and original-group allocation.
Each sample gives equal weight to its complete eligible common pressure grid.
Combining `--point-metrics --paired` also registers a paired MSE comparison;
without `--point-metrics`, paired assessment retains log-pressure curve loss.
Generation metadata records both switches. Point MSE can additionally yield an
interval for the square root of training-average MSE. This is not an interval
for average per-training RMSE or for a larger final training dataset.
