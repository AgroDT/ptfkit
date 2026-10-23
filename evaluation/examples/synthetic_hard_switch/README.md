# Synthetic learned hard switches

This run reuses the committed synthetic dataset and atomic candidate definitions
from `../synthetic_retention/`. It trains a single Clapp/Vereecken hard switch
on the preregistered grid [1, 10, 100] kPa, with exact boundaries owned by the
left member. It provides execution evidence only, not real-soil accuracy or
a scientific recommendation about switching these publications.

From the repository root:

```sh
mise run eval:sync
uv run --project targets/ptfkit-eval ptfkit-eval plan evaluation/examples/synthetic_hard_switch/run.json
uv run --project targets/ptfkit-eval ptfkit-eval run evaluation/examples/synthetic_hard_switch/run.json --output local/hard-switch-demo
uv run --project targets/ptfkit-eval ptfkit-eval report local/hard-switch-demo
```

The `nested_two_curve_selection_v1` protocol uses three outer source folds and
two inner source folds. Every inner training partition scores every grid
boundary on exactly the same usable sample/pressure roster using normalized
log-pressure trapezoid MSE over 0.1 to 1,000 kPa. Both domain endpoints must be
observed exactly. Boundaries are strictly inside that domain, ensuring that
usable training curves have measured pressure support on both sides.

Fits require two usable training groups and a best-versus-second-best training
loss gap strictly greater than 1e-10 volume-fraction squared. This gate is not
a statistical significance test. Ties or insufficient separation retain all
scores and `unidentifiable_boundary`, with no default boundary. Identification
concerns only the registered discrete grid, not the true location of a physical
boundary or its uncertainty. Failed inner fits cannot compete via partial
validation scores; failed outer refits have no alternative-candidate fallback.

Inner validation locks the ensemble, which is refitted on all outer training
groups before outer testing. The synthetic example selects outer boundaries
1, 10, and 1 kPa for folds 0, 1, and 2 under the registered seed. These are
synthetic fitted choices, not a final deployment model. `learned-selection.json`
retains every training score, loss gap, fit role, prediction, and assessment.

`learned-applicability.json` separately reports training-input support and error
strata for inner candidates and locked outer choices. Both constituent domains
must support a sample; diagnostics do not select or refit boundaries.

`learned-seams.json` evaluates both members for all twelve outer test samples
at their already fitted boundary, without reading test observations. Each
record retains normalized inputs, forecasts, right-minus-left contrast and
explicit failures. A contrast implies a jump only if both member curves are
continuous at the seam. Bounds, targets, and curves are never repaired.
No confidence interval for boundary location or full selection-process
uncertainty is claimed. Saved run directories contain portable snapshots and
can be replayed independently of the original example paths.

The run also emits `selection-curve-quality.json` for every held-out curve,
including empty predictions, and `strategy-assessment.json` for locked outer
atomic/ensemble strategies. Strategy metrics use only the registered 0.1-to-
1,000 kPa domain and retain maximal/common cohorts and full sample denominators.
Partial outer evidence never becomes a complete strategy result. Strategy
uncertainty is explicitly unestimated: these descriptive held-out rows do not
justify confidence intervals that ignore overlapping training and selection.
