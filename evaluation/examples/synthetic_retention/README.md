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

The optional empirical-domain registrations use only predictors from sources
a through d to construct inclusive numeric ranges and observed category sets.
Sources e and f supply test inputs. Each composite member has its own complete
training-vector roster and a four-source evidence gate. These descriptive roles
are separate from the nested selection folds above; domain results do not choose
candidates, change eligibility, or constitute accuracy evidence. See
`empirical-domains.json` for complete lineage and `inside`/`outside` decisions.
Marginal ranges do not establish joint predictor support.

The composite also emits `composite-seams.json`, inspecting both members at
10 and 100 kPa. These are blend endpoint disagreements, not discontinuities
in the blended curve. Diagnostics inspect zero-weight members too, retaining
any unavailable inputs separately from ordinary routed prediction eligibility.

`selection.empirical_domains` separately fits predictor envelopes within every
inner and outer training fold with a two-group evidence gate. Test labels use
all registered composite members; missing inputs and insufficient evidence
remain distinct. `nested-applicability.json` reports common-cohort errors and
coverage for each input stratum and flags the already locked outer choices.
These labels never feed back into selection. Fold-stratum bootstrap metric
intervals condition on the folds/envelopes; many have too few groups for the
five-group bootstrap gate and correctly retain insufficient evidence.

Two predeclared paired comparisons report Clapp minus Vereecken and the fixed
blend minus Clapp on the run-wide common cohort. Both sides use identical
whole-source bootstrap draws; negative absolute-error metric differences favor
the left candidate on this cohort. `paired-comparisons.json` retains rows,
estimates, and unadjusted percentile bounds. These descriptive comparisons do
not select a winner or estimate uncertainty from repeating nested selection.

An independent `learned_selection` registration compares the same fixed roster
with `trained_convex_pair`, a constant convex Clapp/Vereecken blend. Each inner
training partition fits its own weight; inner validation locks an ensemble,
which is refitted on the complete outer training partition before testing.
The example requires two usable training sources and mean squared member
contrast strictly above 1e-10. Boundary weights are valid optima. Failed fits
are explicit; no weight or ensemble is substituted after an outer refit failure.
`learned-selection.json` retains fits, held-out predictions, selection evidence,
and outer strategy results. It does not train a final deployment ensemble or
claim weight uncertainty, learned routing, or scientific accuracy on real soils.

`learned_selection.empirical_domains` separately diagnoses all inner candidates
and only locked outer choices. For the trained pair it requires input support
from both constituent domains, including a constituent assigned zero weight.
`learned-applicability.json` retains explicit left/right member identities,
fold-specific training bounds, input labels, and held-out error strata.
The diagnostic does not fit new weights or change choices.

`selection-curve-quality.json` keeps all inner and locked outer curve diagnostics
separate, without repairing predictions. `strategy-assessment.json` separately
summarizes fixed and learned selection strategies using only locked outer rows
inside the registered loss domain. It retains maximal/common cohorts, sample
coverage, failed folds and descriptive atomic-minus-ensemble differences.
Strategy confidence intervals are explicitly unestimated; resampling the
retained rows would not repeat training or selection.
