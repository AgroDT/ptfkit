# Synthetic retention run

This self-contained example contains six synthetic sources, twelve samples,
sixty hand-declared retention observations, two atomic candidates, and one
fixed blended candidate. Its values test execution and reporting only. They are
not measured soils, external accuracy evidence, or a scientific routing proposal.

From the repository root:

```sh
mise run eval:sync
uv run --project targets/ptfkit-eval ptfkit-eval plan evaluation/examples/synthetic_retention/run.json
uv run --project targets/ptfkit-eval ptfkit-eval run evaluation/examples/synthetic_retention/run.json --output local/retention-demo
uv run --project targets/ptfkit-eval ptfkit-eval report local/retention-demo
```

Choose a new output directory for each run. Existing runs are never overwritten.
The report verifies every artifact checksum before displaying retained results.
The generated `run-plan.json` refers to local canonical snapshots with updated
byte checksums, so it can be replayed after copying the complete run directory.
`source-run-plan.json` preserves the original configuration for audit.

All observations and inputs explicitly declare synthetic provenance. Sand and
clay use the stated exact particle boundaries; carbon and bulk density declare
their required measurement conventions. The bootstrap uses six whole-source
clusters, a predeclared five-group gate, 2,000 replicates, seed 20261023, and
95% equal-tail metric confidence intervals. The minimum group count is a policy
choice, not a guarantee of confidence-interval coverage.

The fixed blend switches between Clapp and Vereecken over an explicitly declared
10-to-100 kPa overlap. The example does not learn its boundaries or weights.
Its fixed-candidate nested protocol uses three outer source folds, two inner
source folds, and normalized trapezoid MSE over log10 pressure with exact
0.1 and 1,000 kPa observed endpoints. It selects an atomic candidate and the
registered ensemble using inner validation, then assesses locked strategies
on outer groups. It does not choose a final function by sorting outer errors.
All selection evidence remains synthetic.

The run also registers four approximation families with explicit bounded
initialization and fit/identifiability policies. It fits each family to each
sample independently of PTF predictors and records failed fits without fallback.
Local parameter intervals, fitted-mean confidence intervals, and conditional
future-observation prediction intervals assume local linearity and independent
homoscedastic residual errors. They are not PTF prediction intervals. Five
observations leave only one residual degree of freedom for a four-parameter
fit; the resulting uncertainty is intentionally exposed rather than hidden.
