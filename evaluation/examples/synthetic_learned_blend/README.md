# Native learned blend-interval example

This run uses the declared synthetic IID group population from
`../synthetic_conditional_risk/` and actual Clapp/Vereecken forecasts. The
registered ensemble learns one of two blend intervals: (1,100) or (10,100) kPa.
Weights are fixed linear functions of log10 pressure. Both endpoints must be
strictly inside the registered loss domain; member identities, grid, axis,
weighting and loss-separation gate are chosen before validation.

Inner fitting uses only inner training groups. Candidate validation locks a
choice, then each outer training partition refits the interval before any test
loss is inspected. All interval scores and failed identification evidence are
retained. There is no fitted-parameter confidence interval or nonlinear
predictor gate, and no physical monotonicity guarantee is inferred from blending.

The run also registers independent four-training/two-test-group block policies
for both strategies and their paired joint-success risk difference. Those have
separate confidence allocations and targets. The prior population loss bound
one remains valid because all finite native forecasts, targets and convex
mixtures in this constructed population lie in [0,1]. Two independent blocks
give uninformative bounds; the example demonstrates full procedure replay.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval run evaluation/examples/synthetic_learned_blend/run.json --output local/synthetic-learned-blend
```

`learned-selection.json` retains interval grids, axis/weighting, all training
scores and locked refits. `learned-blend-endpoints.json` forecasts both members
at the already locked lower/upper endpoint for every outer test sample, using
predictors only. A member contrast is not a blend jump; endpoint weights select
one member. Missing inputs remain unavailable and no observations are used to
refit, correct or choose endpoints. Curve physical diagnostics and empirical
inside/outside support remain separate outputs.

Complete learner uncertainty is recorded in `independent-training-risk.json`
and `paired-training-risk.json`. Exact mathematical blend training-law
calibration is in `evaluation/experiments/blend_training_law/`; it uses its own
explicit finite populations and does not fabricate native PTF predictions.
Original workbook measurement and source-independence blockers remain unresolved.
