# Implemented-function evaluation coverage

Run from the repository root:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/catalog_coverage/audit.py --output evaluation/datasets/implemented-function-coverage.json
```

The report resolves local specification references, lists every implemented
function and its input/output contract gaps, and checks exact agreement with
the generated manifest. File hashes bind the inventory to the specification
and manifest versions. No scientific descriptor is inferred from a field name.
The report is metadata readiness, not evidence of dataset compatibility.

Build the complete function-by-source readiness matrix for the reviewed
volumetric export with:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe -m evaluation.experiments.catalog_coverage.matrix --workbook local/meta_v3.3.xlsx --mapping evaluation/datasets/meta_v3_3.yaml --dataset local/meta-v3-3-canonical-export.json --output evaluation/datasets/meta_v3_3.function-readiness-matrix.json
```

This command recomputes the inventory and raw workbook predictor audit, checks
the installed and generated manifests agree, and requires the canonical
observations to bind the same workbook bytes. Every implemented function
remains visible in each source partition, including functions missing
measurement contracts. Source partitions are reporting strata, not assumed
independent experiments. Input readiness never grants scoring permission or
authorizes model selection. The separate source-reviewed Panina overlay is
outside this raw-binding matrix.

The initial inventory contains 146 implemented functions from 31 source
specifications. Five enter the evaluation manifest; 141 require contract
migration, with 362 missing numeric-input and 281 missing output descriptors.
Shared definitions count once per function binding. Output-quantity counts
overlap: a function may predict both water content and conductivity.
These quantity counts include legacy identifiers. They locate review work;
they do not establish physical compatibility without complete source-reviewed
measurement descriptors. The Dharumarajan retention review is an explicit
example of a legacy water-content label whose denominator remains unresolved.

After the reviewed Wosten class-parameter migration, six functions enter the
manifest and 140 remain omitted; 275 output descriptor bindings remain
missing. The associated retention adapter preserves the published Mualem
exponent convention and source classification. There is no reviewed Staring
class binding in the raw workbook mapping.

After the Beniaich (2023) migration, 17 functions enter the manifest and 129
remain omitted, with 342 missing numeric-input and 242 missing output
descriptor bindings. Its 11 linear regressions retain the documented
gravimetric denominator, analytical methods and the 33/1500-kPa output
conditions. Capillary saturation has no assumed zero-pressure condition.

Audit exact pressure support separately from predictor readiness:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe -m evaluation.experiments.catalog_coverage.pressure_support --dataset local/meta-v3-3-canonical-export.json --dataset local/meta-v3-3-canonical-mass-export.json --output evaluation/datasets/meta_v3_3.fixed-pressure-support.json
```

The mass cohort has no exact 33- or 1500-kPa observations. Nearby pressures
are not rounded, snapped or interpolated into observed targets. These counts
do not establish material, method or predictor compatibility. The generic
canonical normalization description is not evidence that a source's
disturbed-ring measurement protocol was followed.

## Completion sequence

1. Migrate source-reviewed measurement contracts for retention-compatible
   functions, prioritizing van Genuchten parameter functions and fixed-pressure
   water-content functions. Keep every other implemented function in the
   inventory and assign its required observation target. Regenerate targets
   through the project workflow; never edit the generated manifest directly.
2. Build a function-by-dataset eligibility matrix with explicit missing-input,
   incompatible-measurement, unsupported-model and unavailable-target reasons.
   Volumetric and gravimetric observations require separate compatible
   comparisons unless a source-supported density conversion is available.
   Conductivity functions require conductivity observations; retention curves
   alone do not validate them.
3. Run all eligible atomic candidates on prespecified common cohorts. Retain
   exclusions and failures. Report sample-balanced RMSE and MAE, signed bias,
   and results by pressure range. Compare candidates only on comparable targets
   and cohorts, with observation units declared.
4. Select atomic functions and supported ensembles inside grouped nested
   validation. Keep a soil profile together and keep repeated measurements of
   one soil together. Fit ensemble weights and choose model settings using
   training data only. Use outer folds to estimate selection performance;
   preserve insufficient-evidence outcomes when independent groups are lacking.
5. For van Genuchten and Brooks-Corey approximations, publish fit acceptance,
   parameter identifiability, parameter uncertainty and curve uncertainty
   separately. Existing local linear intervals and approximate profile-grid
   regions remain conditional diagnostics until their assumptions and coverage
   are supported. Report supported pressure/soil domains separately from
   confidence intervals; observed extrema alone do not establish applicability.
6. Deliver a reproducible per-dataset decision table: eligible and excluded
   candidates, selected strategy or selection blocker, validation design,
   metrics with uncertainty, approximation parameters, domain restrictions,
   source evidence, input hashes and replayable run artifacts.

The six-horizon Panina Clapp pilot has 56 observations but only one independent
profile. It is an external descriptive check and cannot establish a population
confidence interval or select a generally best model. The larger measured-curve
fitting study evaluates approximation fitting, which is distinct from testing
predictor-based pedotransfer functions.


The Saxton2006 base-contract checkpoint raises manifest coverage to 18 of 146
implemented functions. The remaining 128 functions lack complete contracts;
340 numeric-input and 234 output descriptors remain missing. These inventory
counts do not establish scientific or dataset eligibility.


After the source-backed Gunarathna migration, 26 functions enter the manifest
and 120 remain omitted, with 328 missing numeric-input and 226 missing output
descriptors. All eleven Gunarathna outputs describe undisturbed bulk soil;
fine-earth texture preparation is a separate input contract. The updated
readiness and pressure-only reports do not grant dataset scoring eligibility.
