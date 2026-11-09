# Synthetic simultaneous conditional-risk run

This example declares an actual constructed group population, rather than
inferring independence or bounds from source IDs. Each group independently has
state A or B with probability 1/2 and always contains two samples. Inputs are
the same fixed synthetic predictor vector in every state. At pressures
(0.1, 1, 10, 100, 1000) kPa, sample 1 has targets
(0.4, 0.36, 0.28, 0.2, 0.15) in state A; state B adds 0.1 at each pressure.
Sample 2 adds 0.02 to sample 1. Within-group dependence is unrestricted and
intentional. `generate.py` draws twelve states with seed 20261023, preserves
synthetic cell lineage, and writes the checksum-bound dataset and run plan.
It uses only earlier synthetic inputs, never real workbook measurements.

The finite input/pressure support is known in advance. Both atomic native
curves lie within [0,1] on that entire support; fixed/learned convex combinations
remain within [0,1]. Every population target also lies within [0,1]. Thus every
registered sample log-pressure squared-error loss is bounded by 1. Group size
is exactly two. These prior bounds follow from the constructed population and
complete forecast support, not observed maxima in an arbitrary dataset.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/examples/synthetic_conditional_risk/generate.py
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval plan evaluation/examples/synthetic_conditional_risk/run.json
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval run evaluation/examples/synthetic_conditional_risk/run.json --output local/retention-conditional-risk-demo
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval report local/retention-conditional-risk-demo
```

The `conditional_outer_risk` array requests the learned protocol's atomic and
ensemble strategies. Their common 95% confidence level applies to this entire
two-policy family. Each receives error budget 0.05/2, including a policy that
fails fitting, coverage or a declared observed bound. Within each policy, the
budget is divided over outer-rule numerator events and one denominator event.
Allocation is performed in logarithms using `simultaneous_policy_count`, so a
confidence level near one cannot round an allocated confidence level to one.

`conditional-outer-risk.json` retains policy assumptions, family allocation,
all available fold bounds and explicit failed-fold reasons. The Markdown report
labels the equal-fold mean conditional sample-risk target. It is neither an
interval around the observed sample-weighted CV statistic nor an interval for
training-law average risk or a final all-data model. Shared training sets are
handled by a union bound; independence between folds is not assumed. Failed
policies are never removed from the family or used to reallocate its budget.

The default run has 12 groups, 24 samples and complete inference for both
strategies. With so few groups and a conservative prior loss bound, the bands
are wide. This example demonstrates contracts and reproducibility, not a claim
of real-data accuracy, publication independence or confidence conditional on
successful fitting. The exact mathematical coverage experiments and derivation
are in `evaluation/experiments/conditional_risk/`.
