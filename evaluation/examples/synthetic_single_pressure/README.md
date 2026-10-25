# Native single-pressure selection example

This is the 33-kPa restriction of the independently specified two-pressure
Beniaich fixture in `../synthetic_discrete_retention`. The six profiles retain
synthetic observations calculated from published coefficients, not by calling
the candidates: 0.25 * 0.17577 + 0.75 * 0.1848 = 0.1825425 mass fraction.

```powershell
python evaluation/examples/synthetic_single_pressure/build.py local/single-pressure-new
ptfkit-eval run local/single-pressure-new/run.json --output local/single-pressure-new/artifacts
```

The registered single-pressure MSE selects SLR3 among atomic competitors;
constant convex-pair training recovers left weight 0.25. Three outer folds and
two inner folds preserve whole profiles. A test replaces one outer fold's
targets with the competing atom's values and verifies that training choices
and weights do not change. Complete source/wheel artifact replays belong under
`local`, with their matching wheel and builder archived for reproduction.

This fixture provides no evidence about native function accuracy on real soils
or calibrated prediction/parameter intervals.
