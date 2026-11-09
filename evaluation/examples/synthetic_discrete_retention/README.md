# Synthetic discrete retention selection

This is a technical example, not external predictive-accuracy evidence. It
uses two implemented [Beniaich (2023) regressions](https://www.frontiersin.org/journals/environmental-science/articles/10.3389/fenvs.2023.1090688/full) on explicitly synthetic soil
profiles, with predictions defined only at 33 and 1500 kPa. Both the dataset
and evaluation plan use version 2; the run plan and ptfkit manifest remain
version 1.

The target is gravimetric water content in mass fractions of dry soil. Source
input methods and prepared fine-earth material are retained. Table 5 gives,
at clay 20% and sand 50%, SLR1 outputs 0.17577 and 0.09621 g/g and SLR3 outputs
0.1848 and 0.11077 g/g. The prespecified synthetic observations are 0.1825425
and 0.10713, a 0.25/0.75 combination of those hand-derived values. The builder
does not call ptfkit to generate observation targets.

Six synthetic profile groups support three outer folds and two inner folds.
The fixed atomic strategy selects SLR3. The convex ensemble is fitted only on
training groups and selected using inner validation. Its known left weight is
0.25. The example compares the two strategies on untouched outer groups; it
does not choose a final strategy using the lowest outer test error.

Run from the repository root:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval plan evaluation/examples/synthetic_discrete_retention/run.json
targets/ptfkit-eval/.venv/Scripts/python.exe -m ptfkit_eval run evaluation/examples/synthetic_discrete_retention/run.json --output local/synthetic-discrete-retention
```

Rebuild the inputs into a fresh directory with `build.py --output <directory>`.
Input hashes are written into the run plan. Existing inputs and run artifacts
are never overwritten.

`function_points` and `fixed_outputs` register an explicit finite support.
Output order does not assign pressures; each field's manifest condition does.
Duplicate converted pressures and unsupported output conditions are rejected.
No prediction is supplied at an intermediate or extrapolated pressure. The
trapezoidal log-pressure loss is a registered squared-error diagnostic on the
two observed points, not an interpolated retention prediction. The source
capillary-saturation output is deliberately absent.

The measured mass dataset currently has no exact observations at these two
pressures. This synthetic example does not resolve that real-data blocker or
qualify source transfer, interval coverage or a soil applicability domain.
