# Sample-balanced point training-law risk

Run from the repository root:

```sh
uv run --project targets/ptfkit-eval ptfkit-eval run evaluation/examples/synthetic_point_risk/run.json --output local/retention-point-risk
```

The checksum-bound synthetic dataset and fixed native forecasts are shared with
`synthetic_conditional_risk`. The inner selector still minimizes registered
log-pressure trapezoid MSE. Point assessment separately registers MAE and MSE
for both atomic and learned-blend strategies, with a four-policy simultaneous
confidence family. The paired comparison assesses atomic-minus-blend MSE on
jointly successful training procedures, with its own error allocation.

Every sample uses equal weights on its complete fixed-roster common pressure
grid inside the selection domain. These sample-balanced population risks differ
from pooling all pressure rows when grid sizes vary. Missing test predictions
suppress inference rather than change training success or shrink the roster.

The prior loss bound 1 follows from this synthetic support and convex blend
predictions in [0, 1]. It is not inferred from observed errors. Two independent
blocks cannot separate training-success probability from zero at this confidence,
so successful-training risk and pooled RMSE may remain unavailable. Pooled RMSE
means the square root of training-average MSE, not average per-training RMSE.

See `evaluation/experiments/blend_training_law` for exact finite-population
coverage checks with point MAE/MSE, informative group sizes and retained failures.
No workbook accuracy or larger-training-size guarantee follows from this example.
