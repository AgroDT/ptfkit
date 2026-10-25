# HYBRAS source inventory

The official [HYBRAS archive](https://rigeo.sgb.gov.br/items/edfbb5ff-604c-43c6-940b-18fc6fa53caf)
contains measured retention data, fitted parameters and estimated retention
values. This inventory establishes counts and checksums; it does not authorize
native PTF scoring or establish external validation independence.

Run from the repository root with the evaluator environment:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/audit.py local/source-review/hybras2018/hybras_v1_2020.zip local/hybras-inventory-replay.json
```

The command creates a new output and refuses to overwrite an existing file.
The tracked result is `evaluation/datasets/hybras_v1.inventory.json`.
The official archive and manual remain local.

The workbook contains 1,075 horizons, 445 distinct profile identifiers and
8,793 rows in `RAWRET_lines`. Of its 1,075 zero-head values, 289 are explicitly
derived from total porosity. The porosity comment repeats on all points of
those curves: exclude the derived zero-head point, not the entire curve.
The remaining 7,718 positive-head rows still require provenance and quality
review before use. Their presence in a raw table does not establish that
they are individual, undigitized, independent measurements.

Use the long raw table's pressure-head units (cm) consistently. The wide table
also labels approximate kPa equivalents; do not silently substitute those
labels for exact converted pressures. Keep derived/contributed van Genuchten
parameters and estimated water contents separate from measured targets.

Next review the manual and per-row comments for digitization, replicate
averaging, pressure conversions, drying paths, and saturation provenance.
Verify profile/source grouping, material and texture conventions, predictor
methods, and overlap with candidate calibration studies before selection.
Raw-data redistribution also requires a verified license.

## Positive-head approximation import

The manual review is recorded in
`evaluation/datasets/hybras_v1.source-review.json`. The adapter pins both the
archive and workbook checksums and writes the full canonical import, a reviewed
fitting subset, full source provenance and a count-only summary to a new directory:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/build.py local/source-review/hybras2018/hybras_v1_2020.zip local/hybras-positive-head-replay-new
```

The tracked `hybras_v1.import-summary.json` is reproduced by this command's
`import-summary.json`. The raw observations remain local. All 1,075 zero-head
values are deferred: 289 porosity-derived and 786 reported saturation values.
This conservative cohort therefore has no measured saturation anchor.

The 7,718 positive-head values are retained unchanged, including nonmonotone
series. Source comments declare `1atm=1020cm` for 664 points in 88 horizons,
whereas other records use `1atm=1033cm`. These points are blocked in
`dataset.json`; their pressure values are preserved pending original-source
review. `fitting-dataset.json` excludes them and contains 7,054 observations
from 987 horizons. Noncorrecting physical diagnostics identify 83 increases across 68
curves. Empty observation flags do not assert that these curves passed physical
quality screening; diagnostics are reported separately, as in the existing
descriptive reference-fit experiment. The explicit material basis is
`unspecified`, and predictor features remain empty. This cohort supports
descriptive approximation analysis, not native PTF ranking.

The existing reference experiment can be applied without changing its declared
parameter boxes or acceptance criteria:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/measured_retention/fit.py local/hybras-positive-head-replay-new/fitting-dataset.json --output local/hybras-positive-head-replay-new/reference-fits.json
```

Its parameter boxes are computational restrictions, not universal HYBRAS
applicability ranges. In particular, the residual-water upper bound 0.14 and
saturation interval [0.25, 0.8] can restrict tropical-soil fits. Rejections,
boundary solutions and local uncertainty-support diagnostics must be retained.
Do not interpret local linear Student-t intervals as externally calibrated
confidence or predictive coverage, or use training residuals to choose the
best native PTF or ensemble.

The initial 4,300 independent curve fits completed on the preliminary full
positive-head cohort before the ambiguous conversion records were blocked.
Keep that artifact for provenance. A count-only review retains the 3,948 fits
whose entire observation series matches the reviewed subset exactly:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/review_fits.py local/hybras-positive-head-first/reference-fits.json local/hybras-positive-head-reviewed/fitting-dataset.json local/hybras-reviewed-fit-summary-replay.json
```

The tracked result is `evaluation/datasets/hybras_v1.reference-fit-summary.json`.
The review rejects missing/duplicate fits or changed observations. Exclusions
depend on source pressure provenance, not fit outcomes. The existing per-curve
optimizer uses fixed plans and seeds independently, so it does not require
refitting unchanged curves after this cohort exclusion.

## Ordered-water fitting experiment

`fit_ordered.py` uses the registered
`bounded_trf_ordered_water_multistart_v1` method with overlapping residual and
saturated-water boxes. The VG Mualem boxes and initials follow manual PDF page
21 (printed page 15), with alpha converted from cm^-1 to kPa^-1. The Brooks-Corey
air-entry [0.001, 1000] kPa and lambda [0.01, 5] boxes are explicit computational
choices. This does not reproduce the source's optimizer, saturation anchors
or published fits, and does not qualify either family's applicability domain.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/fit_ordered.py local/hybras-positive-head-reviewed/fitting-dataset.json local/hybras-ordered-water-new
```

The command writes package source hashes, complete plans, the dataset,
incremental JSONL fit records and a terminal summary. A partial run without
`summary.json` is not a completed experiment. Existing output directories are
rejected. All 1,974 fits completed on the 987 reviewed curves: 486 VG Mualem and
399 Brooks-Corey fits passed the declared numerical evidence gates.

The first run under `local/hybras-ordered-water-first` emitted a pretty JSON
sequence despite its `.jsonl` filename. The original remains intact; its
`fits.repaired.jsonl` contains the same 1,974 records serialized one per line.
`serialization-repair.json` records both hashes and the lossless repair.
The current script writes compact JSONL directly. The first run's exact code
and script snapshot remain in its `reproduction` directory.
The isolated-wheel run under `local/hybras-ordered-water-wheel-replay` reproduces
all 1,974 repaired records byte for byte and has its matching wheel/script
archive and an environment record.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/compare_ordered.py local/hybras-positive-head-first/reference-fits.json local/hybras-ordered-water-first/fits.repaired.jsonl local/hybras-positive-head-reviewed/fitting-dataset.json local/hybras-ordered-comparison-replay.json
```

The tracked `hybras_v1.ordered-fit-comparison.json` checks the complete reviewed
roster and exact observation equality. Bounds, initials and coordinates changed
together, so these counts do not isolate a solver effect. Six previously
accepted fits are now rejected. In 27 Brooks-Corey cases a converged objective
is worse than the baseline by more than 1e-12 despite the broader feasible
region, including six numerically accepted fits; retain these optimizer
counterexamples for a restart audit. The comparison explicitly reports
`insufficient_evidence` for uncertainty qualification.

Uncertainty limitations remain substantial: parameter intervals exceed their
declared boxes in 327 of 486 accepted VG fits and 130 of 399 accepted BC fits.
Mean-curve intervals exceed physical water bounds in 11 and 5 fits,
respectively. These intervals remain unmodified diagnostics, not qualified
confidence statements. Profile-based optimality/region review, broader coverage
experiments and external native PTF/ensemble selection remain outstanding.

## Counterexample restart audit

`audit_restarts.py` pins the exact baseline and ordered fit streams and retains
all 27 BC objective regressions. The best narrower-box solution becomes an
explicit additional physical start. Original seeded solves, targets, bounds
and evidence gates remain unchanged. The audit compares this augmentation
under seeded, pressure-partition and interval-solve restart policies.

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/audit_restarts.py local/hybras-positive-head-first/reference-fits.json local/hybras-ordered-water-wheel-replay/fits.jsonl local/hybras-restart-audit-new
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/summarize_restarts.py local/hybras-restart-audit-new local/hybras-restart-summary-new.json
```

All 81 refits and 20 full parameter profiles reproduced byte for byte from an
isolated wheel. Each policy resolves all 27 known objective regressions within
the declared 1e-12 tolerance, with 11 locally accepted and 16 boundary-rejected
fits. Five of the six originally accepted counterexamples remain accepted;
the other now fails the boundary gate. All four parameters of those five fits
were profiled on five fixed box values plus the estimate. No lower objective
was found on these grids. Six grid regions reach a parameter-box boundary;
13 contain only the estimate. Neither finding defines a continuous confidence
interval or proves global optimality.

The tracked `hybras_v1.restart-audit-summary.json` independently verifies 5,325
converged objectives against the direct BC plateau/power equation, including
nuisance-profile solves. It requires a completed terminal summary, matching
stream checksum and complete sample/policy roster. The numerical results and
matching wheel/scripts remain under `local/hybras-brooks-corey-restart-audit`
and `local/hybras-brooks-corey-restart-wheel-replay`.

This is a targeted posthoc optimizer audit. Do not substitute its 27-curve
counts for the full-cohort results. Uncertainty qualification remains
`insufficient_evidence`; native function contracts, dataset compatibility and
external function/ensemble selection remain part of the original objective.


## Saxton2006 numerical preflight

Run the source-pinned raw-predictor audit into a new directory:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/saxton_preflight.py local/source-review/hybras2018/hybras_v1_2020.zip local/hybras-positive-head-reviewed/fitting-dataset.json local/hybras-saxton-new
```

Current source and installed-wheel runs are
`local/hybras-saxton2006-native-final` and `local/hybras-saxton2006-native-wheel`.
Their complete streams and summaries match byte for byte; matching inputs and
wheel hashes are archived in each `reproduction` directory. Of 987 horizons,
607 execute within numeric predictor limits and 604 pass the registered curve
adapter. Two negative air-entry values and one negative wilting-point water
with nonfinite derived parameters remain explicit failures. No observed targets
are scored: fine-earth target basis, predictor methods/origins and applicability
still need review. See `hybras_v1.saxton-preflight-summary.json`.


## Next binding review: Clapp and Vereecken

`review_native_bindings.py` inventories the pinned source workbook without
assigning canonical features or granting eligibility. Reproduce into a new path:

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/review_native_bindings.py local/source-review/hybras2018/hybras_v1_2020.zip local/hybras-binding-review-new.json
```

Tracked results are `evaluation/datasets/hybras_v1.native-binding-review.json`.
A strict lexical shortlist of single A/B/E horizon designations contains 378
horizons from 144 profiles in the full archive, before joining the reviewed
positive-pressure cohort. This is a review shortlist, not eligible sample counts.
The NRCS Soil Survey Manual identifies these master horizons as mineral; missing,
compound and annotated names remain outside this initial shortlist. Mineral
horizons do not prove fine-earth preparation or absent gravel. The reported
texture classes still require a source-reviewed crosswalk before Clapp scoring.
All density method cells report only a volumetric ring, leaving Vereecken's
required drying temperature, duration and core size unresolved. Carbon assays
also differ and must be matched per row rather than globally equated.


## Source-reviewed Clapp external validation

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/run_clapp.py local/source-review/hybras2018/hybras_v1_2020.zip local/hybras-positive-head-reviewed/fitting-dataset.json local/source-review/hybras2018/manual.pdf local/hybras-clapp-new
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/summarize_clapp.py local/hybras-clapp-new local/hybras-clapp-summary-new.json
```

The source-pinned overlay uses source-reported USDA classes reviewed visually
in manual Figure 3 and simple A/B/E mineral horizon labels, with exact workbook
identity joins. It preserves pressures, targets, profiles, source groups and
nonmonotone observations. The resulting 378 horizons, 144 profiles and 2,882
points support fixed Clapp external validation, not best-model selection.
RMSE is 0.0737533 with profile-bootstrap 95% metric CI [0.0673851,0.0806099].
Profiles share 22 source groups; these intervals condition on represented
studies. Individual prediction uncertainty and transfer to new study
populations are not qualified. Unknown rocky-soil status remains a calibration
transfer limitation; no zero-gravel or fine-earth assumption is made.

Final source and wheel runs are `local/hybras-clapp-reviewed-final` and
`local/hybras-clapp-reviewed-wheel`. All 11 artifact payloads and four input
files reproduce byte for byte; wheel/scripts/specification are archived in each
`reproduction` directory. The independent verifier checks every persisted
prediction against the published gradual-air-entry parabola or dry power curve,
not a plateau approximation, and separately computes sample-balanced means.
Tracked summary: `evaluation/datasets/hybras_v1.clapp-validation-summary.json`.


## Original controlled kPa regimes

```powershell
targets/ptfkit-eval/.venv/Scripts/python.exe evaluation/experiments/hybras/restore_pressure_protocols.py local/source-review/hybras2018/hybras_v1_2020.zip local/hybras-positive-head-reviewed/fitting-dataset.json local/hybras-controlled-kpa-new
targets/ptfkit-eval/.venv/Scripts/python.exe -m evaluation.experiments.catalog_coverage.pressure_support --dataset local/hybras-controlled-kpa-new/dataset.json --output local/hybras-controlled-kpa-new/fixed-pressure-support.json
```

This separate view restores source-declared controlled kPa regimes only where
an exact reviewed method list, original-kPa conversion comment, unique rounded
head identity and matching wide/long water values agree. It preserves source
identities and every water value. It does not snap nearby heads, interpolate,
invert unknown original units or interpret ranged method descriptions.

The current view contains 1,465 observations, 254 horizons, 224 profiles and
four source groups, including 254 exact observations each at 10, 33 and
1500 kPa. Material and predictor eligibility remain unbound. Source and wheel
outputs in `local/hybras-controlled-kpa-first` and
`local/hybras-controlled-kpa-wheel` match byte for byte; matching script/wheel
archives are in `reproduction`. Review sidecars preserve original rounded
heads, parent kPa coordinates and all source-cell decisions. Tracked summaries:
`hybras_v1.controlled-pressure-summary.json` and
`hybras_v1.controlled-pressure-support.json`.

Historical approximation fits and native accuracy scores retain their original
input hashes. They must not be relabelled as results on this new coordinate
view. Four source groups also limit broad new-study uncertainty claims even
though there are 224 profile identifiers.
