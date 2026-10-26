# Harmonized benchmark

Run this opt-in view from the repository root after the existing strict
benchmark. It verifies the strict run's artifact manifest and the installed PTF
manifest before evaluating the full implemented catalog:

```powershell
uv run --project targets/ptfkit-eval --no-sync python -B -m evaluation.experiments.meta_v3_3.harmonized --benchmark local/meta-benchmark-ensemble-final-20261025 --output local/meta-harmonized-new
```

The output directory must be new. The strict implementation and its eligibility
checks remain unchanged. `strict-matrix.json` is a byte-for-byte copy of the
existing strict matrix. Strict forecasts are preserved separately and compared
with the harmonized execution on identical source/sample/pressure coordinates.
Any changed or missing strict observation or prediction aborts reporting.

`harmonized-matrix.json` accounts for every implemented function, retained
canonical sample and discovered target pool. Each record includes independent
strict, harmonized and exploratory eligibility, execution status, predictor
evidence, target evidence and rejection reasons. Unresolved legacy contracts
remain in the matrix, with no native execution permission. A complete source
review is not a gate: only the function's required predictors and target matter.

`fixed-pressure-targets.json` deduplicates target evidence across functions,
including targets whose predictors remain blocked. Fixed targets cover all
catalog pressures and 10, 33 and 1500 kPa for registered curve adapters.
`harmonized-predictions.json` retains every successful comparison and its complete
evidence trace. `summary.json` and `report.md` report per-function and per-pool
coverage, errors, strict-subset preservation and ensembles. Function counts span
pools; errors are never averaged across different physical target contracts.
All artifacts, inputs, policies and implementation files have recorded hashes.
`count-summary.json` contains publication counts and errors without the private
sample-level ensemble forecasts, and can be retained under `evaluation/datasets`.

## Evidence policies

The reusable `ptfkit_eval.harmonization` module defines six separate categories:
`strict`, `converted`, `derived`, `reconstructed`, `approximate`, `unsupported`.
An evidence tier describes provenance; contract compatibility is a separate
decision. Only the existing strict decision can grant strict eligibility.
Transformations preserve their parent traces and cannot promote approximate or
unsupported evidence. Traces freeze nested metadata to prevent later mutation.

The registry is saved before execution. Registered operations are:

- Affine unit conversion through the existing manifest unit registry.
- Water interpolation between adjacent positive experimentally observed
  pressures in log10 pressure space. No extrapolation, averaging of duplicate
  coordinates or replacement of exact observations is allowed. Traces retain
  requested and neighboring pressures, pressure and log-pressure spans, exact
  observation status and an optional fitted-family numerical diagnostic.
  A diagnostic fit never becomes the primary observed target.
  Gravimetric ratios may exceed one; the volumetric upper bound is not applied
  to mass-basis water observations.
- OC/OM conversion with an explicit positive coefficient and source
  authorization. There is no default universal coefficient.
- Porosity from bulk and particle density with an explicit common basis/unit.
- Complementary texture fraction for a declared closed dry-mass fine-earth
  partition, and USDA class assignment from harmonized USDA fractions.
- Exact PSD rebinning from cumulative measurements and log-diameter boundary
  interpolation. The preregistered maximum adjacent diameter ratio is 5 for the
  main interpolation policy. This is a resolution rule for this experiment,
  not a general claim of physical equivalence. Wider intervals require the
  separate exploratory log-uniform assumption. Missing endpoints, nonmonotone
  cumulative data and unspecified material/mass basis are rejected.

The USDA classifier follows the class definitions and Figure 3-7 in the
[USDA Soil Survey Manual, Chapter 3](https://www.nrcs.usda.gov/sites/default/files/2022-09/SSM-ch3.pdf).

`resolve_harmonized_input` checks quantity, basis, particle boundaries,
conditions, required method, units and computational domain independently for
each predictor. New derived features can carry a registered `EvidenceValue`
through the in-memory catalog API; an unverified persisted dictionary cannot
self-authorize a derivation. Existing reviewed derivations still pass through
the unchanged strict binder, including the source-specific Cosby class
coordinates. These coordinates do not become measured numeric texture inputs
for other PTFs.

Approximate combinations are classified as exploratory and excluded from main
execution, errors and ensembles. This entry point does not run exploratory
scoring. No assumption about unknown units, fine-earth preparation, a missing
PSD boundary, or humus/OM equivalence is silently registered as a conversion.
The separately authorized [exploratory experiment](EXPLORATORY.md) executes
explicit approximate scenarios in its own output directory and verifies that
the main artifacts remain unchanged.

Ensembles use the existing equal-weight means and existing grouped convex
learning implementation within each physical target pool. With fewer than
three independent profiles, only descriptive fixed means are computed and
learning is explicitly unavailable. Member and training-observation tiers are
recorded; no final recommendation is made.

## Current data limitation

The 2026-10-25 run completes the 146-function traversal and reconstructs all
in-range catalog fixed-pressure targets in the released canonical data. It
retains two scored atomic PTFs: Clapp and Cosby. Each also scores the 10, 33 and
1500 kPa reconstructed target pools. Four target pools have a two-member mean;
the available profile groups do not support learned blends.

The requested increase beyond two scored functions is **not achieved**. The
existing canonical META datasets have empty numeric feature lists outside the
reviewed Panina class overlay. Global workbook columns have unresolved units,
material/mass basis and methods; the default clay boundary is below 1 micrometre
and cannot be relabelled below 2 micrometres. Reconstructing targets does not
resolve these input contracts. The summary therefore records
`coverage_milestone_met: false`. HYBRAS raw predictor preflights also explicitly
withhold fine-earth/protocol compatibility and are not promoted to harmonized
evidence by this run.

This is a completed infrastructure and target-reconstruction step, with the
requested larger-coverage milestone still open. Specific predictor metadata or
an explicitly separate exploratory assumption policy is required to increase
real-data atomic coverage without changing the evidence definitions.

## Verification

Tests use hand-computed log-pressure midpoints, density ratios, texture closure,
USDA triangle interiors and PSD cumulative differences. The integration test
executes the real Gunarathna sand-only PTF using 0.5 mass fraction converted to
50 percent and water reconstructed between 1 and 100 kPa. The published
regression gives 0.2952, independently of the runner. Negative tests fail if
missing predictors, wrong PSD boundaries, unknown basis or extrapolation reach
native execution. Approximate evidence must remain unscored, and changed strict
values must abort reporting. An isolated in-memory mutation replacing log-space
interpolation with linear-pressure interpolation must fail the midpoint test.
