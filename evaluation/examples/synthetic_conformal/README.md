# Synthetic grouped prediction intervals

This standalone example calibrates the fixed Clapp sand curve with nine
synthetic sources and forecasts a tenth source without test observations.
It demonstrates the protocol only; it provides no external accuracy evidence.
All inputs and observations declare synthetic provenance and cell lineage.

From the repository root:

```sh
mise run eval:sync
uv run --project targets/ptfkit-eval ptfkit-eval plan evaluation/examples/synthetic_conformal/run.json
uv run --project targets/ptfkit-eval ptfkit-eval run evaluation/examples/synthetic_conformal/run.json --output local/conformal-demo
uv run --project targets/ptfkit-eval ptfkit-eval report local/conformal-demo
```

Use a new output directory for each run. Copy the complete output directory
to replay its portable `run-plan.json` on another computer.

The registered `fixed_group_max_split_conformal_v1` method takes one maximum
absolute residual over every sample and pressure in each calibration source.
The two registered pressures are 0 and `3.5 * 2**4.05 * 0.0980665` kPa.
The Clapp sand curve predicts 0.395 and 0.1975 there. Calibration source i
adds i/100 to both predictions, giving group scores 0.01 through 0.09.
At confidence 0.9 the exact rank is ceil((9 + 1) * 0.9) = 9, so the
half-width is 0.09. The test intervals are [0.305, 0.485] and
[0.1075, 0.2875], up to floating-point rounding.

Training groups are empty because this published fixed candidate is not
trained or selected here. Calibration and test groups are explicitly disjoint.
No test targets are supplied or needed to construct the forecasts. Missing
calibration grid points produce insufficient evidence; groups are not silently
dropped. Changing confidence to 0.95 with only nine groups also produces
insufficient evidence because the finite rank would exceed nine.

Coverage interpretation requires exchangeable whole groups, a fixed prediction
rule, and a fixed observation design. The scope is simultaneous over the
registered grid and samples of a future group under those assumptions, not
conditional coverage for every soil type or arbitrary new pressure grids.
Bounds are not clipped to physical limits. These prediction intervals remain
separate from bootstrap metric confidence intervals, fitted-family uncertainty,
applicability domains, and validated pressure ranges.
