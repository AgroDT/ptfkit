# Nonlinear pressure sigmoid gate

Run from the repository root:

```sh
uv run --project targets/ptfkit-eval ptfkit-eval run evaluation/examples/synthetic_sigmoid_gate/run.json --output local/retention-sigmoid-gate
```

The fixed native atomic curves are mixed with left weight
`1 / (1 + exp(steepness * log10(pressure / center_kpa)))`.
A preregistered finite center/steepness grid is fitted only inside each inner
training fold, then refitted on outer training groups. A tied or insufficiently
separated objective produces an identification failure, never default parameters.
The log-pressure curve objective and common eligible point roster remain fixed.
Both member forecasts remain required, including numerical saturation of weights.

The dataset and native evaluation plan are shared with the declared synthetic
IID group population. Four separate point MAE/MSE policies, a paired MSE comparison
and whole-group retraining sensitivity demonstrate the same complete procedure.
Two independent blocks are intentionally insufficient for precise risk bounds.
Retraining sensitivity is not a parameter confidence interval. The run additionally
writes `learned-sigmoid-centers.json`: member input/prediction traces and their
half-weight average at each locked center, without accessing observations.

This gate uses pressure alone, with steepness per log10 pressure decade. It does
not implement soil-property gating, fit atomic PTF coefficients, enforce curve
monotonicity or produce parameter confidence intervals. The existing physical
curve and applicability diagnostics still apply. No workbook measurement rule
or external-data accuracy claim follows from this constructed example.

See `evaluation/experiments/sigmoid_training_law` for independent rational
curve oracles, retained failed fits and exact finite-population coverage checks.
