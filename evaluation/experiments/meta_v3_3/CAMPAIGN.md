# Catalog exploratory campaign

This opt-in experiment expands reproducible real-data execution across the entire
implemented catalog. It keeps the strict and harmonized runs immutable. All new
scores and ensembles are descriptive, excluded from the main leaderboard, and
ineligible for recommendations. Computational execution does not establish regional,
analytical, or predictive applicability.

## Reproduce

Run from the repository root with the installed native extension matching the
generated manifest:

```sh
uv run --project targets/ptfkit-eval --no-sync python -B -m evaluation.experiments.meta_v3_3.campaign \
  --benchmark local/meta-benchmark-ensemble-final-20261025 \
  --harmonized local/meta-harmonized-complete-20261025 \
  --workbook local/meta_v3.3.xlsx \
  --output local/meta-campaign-new-run
```

The workbook is private and remains local. The output directory must be new and
outside both pinned benchmark directories. `mise run eval:campaign` exposes the
same four positional arguments. The run checks input inventories before and after
execution and writes its final artifact inventory only after the report succeeds.
Compare that inventory and every output byte against a second independent run.

## Shared policies

`campaign-policies.json` registers the policies before evaluation; the output also
snapshots the inherited `exploratory-policies.json`. Nothing is calibrated to the
observed scores. Every stage and leave-one-policy-out ablation revisits every
catalog function, including those without a supported target.

Source specifications supply physically defined outputs, native public aliases,
units, enumerations, and explicit computational domains. Generic adapters support
fixed pressures, a declared water-content pressure axis, direct bulk density,
the defined logistic pressure-scale family, and the defined Hutson-Cass dry branch.
Copied water-content input anchors are excluded from predictive scoring. Unknown
water denominators and unspecified retention variants remain unsupported. An
operational field-capacity or wilting-point name never supplies a pressure.

The primary target policy uses adjacent measured observations and linear water
content in log10 pressure. It preserves exact observations, rejects extrapolation,
and retains measured parents, requested pressure, brackets, spans, formula and the
original water contract. Separate VG-Mualem and Brooks-Corey diagnostics accept
only fitted records with identical experimental pressures, values and observation
references. Fit targets remain reconstructed even at measured coordinates. The
registered disagreement threshold is 0.03 in the original volume-fraction basis.

Density discovery scans every workbook view with recognized identity and density
headers. It requires exact source/sample identity and agreement of duplicate
values. Formula averages, other horizons and population means are rejected.
Mass/volume conversion uses only same-sample density. Carbon/matter aliases share
the inherited fixed factor and retain reported versus derived provenance; an
available reported counterpart takes precedence. USDA classes derived from a
closed exploratory PSD inherit its approximation status.

An additional high-leverage policy fills missing PSD components only when a
confirmed reported USDA class exists. It uses the uniform mean of the closed 1%
USDA lattice conditional on available components within 0.5 percentage points.
It preserves available components, rescales only missing components to closure,
and rejects inconsistent results. This explicit within-class distribution is an
approximation, not a measured PSD. Russian texture labels are not mapped to USDA,
and USDA is not mapped to other classification systems. Source-specific PSD bins
are obtained from the registered cumulative distribution with traceable rebinning.

## Accounting and comparisons

The assumption ceilings are cumulative: E0 pinned strict; E1 exact conversion or
deterministic derivation; E2 target reconstruction; E3 approximate predictors or
analytical comparability; E4 combined reconstruction and approximation or material
conversion. Unsupported assumptions do not create another execution tier. A
function's minimum tier can occur on a smaller cohort than its full coverage.

Function coverage, unique function/sample/target combinations and scenario
executions are separate counts. The initial and final funnels assign one next
blocker per unexecuted function and retain every co-blocker. Potential policy gains
are conditional upper bounds, not forecasts. Leave-one-policy-out effects overlap
and must not be added together. The source-level density audit uses sample counts
and separately reports measured-point counts.

Comparative tables require an identical target, scenario, route and common set of
observations. Empty common cohorts do not produce rankings. Cross-PSD sensitivity
uses coordinates shared by both scenarios; fewer than two candidates cannot
establish ranking stability. Per-model maximal-cohort errors are descriptive and
must not be compared as rankings. Existing fixed equal means use the roster-wide
common cohort when available; otherwise each pair's exact common cohort is labeled
as unsuitable for comparison across pairs. Existing grouped convex blending runs
only with at least three confirmed independent profile groups. Missing profile
identities are never invented. Retention-input PTFs are conditional reconstruction
experiments, not independent predictive validation.

`report.md` contains coverage, policy contributions, both blocker funnels, target
pools, scenario diagnostics, the density audit, per-model assumption burdens and
all final blockers. `summary.json` also contains exact common-cohort metrics,
paired prediction differences and ensemble evidence. Full matrices, prediction
lineage and fit disagreements remain local. Specification, implementation, native
extension and input hashes bind the results to their executable interpretation.

## Retained META result

The 2026-10-26 run executes 43/146 unique functions: the pinned strict two plus
41 exploratory functions, up from the previous 11 exploratory functions. It covers
52 samples, 1,352 unique function/sample/target combinations and 2,582 primary
scenario executions. An additional 800 accepted-fit diagnostic executions are
counted separately. Cumulative E0/E1/E2/E3/E4 coverage is 2/2/2/4/43; Saxton 2006
and the Wosten loam/clay density function first become executable at E3. Most
functions require combined assumptions at E4.

The 30 newly executed functions are Chakraborty eq1-eq6; Gunarathna vwc10_set1,
vwc33_set1, vwc1500_set1/set3/set4; Rawls 1982 full_wrc/theta_33/theta_1500;
all four Rawls 2003 SOC models; Myeni fc/pwp; Oosterveld retention/wilting_point;
Mayr; Saxton 2006; Vereecken 1989; Varallyai chernozem a/b/c and meadow; and
Wosten 2001 loam_clay_table5. Full identifiers and policy-specific affected lists
are in `evaluation/datasets/meta_v3_3.campaign-summary.json`.

Sequential coverage is 13 -> 25 -> 41 -> 43. Removing interpolation, source-spec
bridges, conditional class PSD, OC/OM aliases/conversion, same-sample density
conversion, retention predictors, or depth midpoints loses respectively
39, 23, 18, 6, 4, 2, or 2 functions. These conditional effects overlap.
Automatic USDA class derivation contributes no additional unique function on this
particular dataset; the policy remains available without inventing other taxonomies.

There are 18 target pools: mass-basis water at 10/33/100/500/1500 kPa;
volume-basis water at 7/10/20/33/60/100/200/400/500/700/1000/1500 kPa; and bulk
density. Of 50 mass-basis samples, 17 have same-sample density and 33 lack it.
Scanning duplicate views adds zero density links. Among 800 fit diagnostic
executions, 32 differ from interpolation by more than 0.03 original volume fraction;
the maximum absolute disagreement is about 0.103. These are execution counts,
including repeated functions and scenarios, not 800 independent observations.

The final exclusive blocker accounting is 15 data limitations, 78 absent targets,
zero remaining evaluator-only blockers, and 10 functions requiring unsupported
semantics or domain relaxation. This sums to the 103 unexecuted functions.
Li 2007 lacks an in-range saturation observation; Pidgeon operational quantities
are not assigned a guessed pressure; six Gunarathna variants violate the explicit
silt domain on the otherwise best-supported samples; four Dharumarajan variants
retain an explicit gravimetric/volumetric ambiguity warning.

No ordering changes occur on the available roster-wide cross-PSD common cohorts.
Several primary mass-water pools have empty roster-wide common cohorts, so their
overall ranking is unavailable. Individual prediction sensitivity is nevertheless
nonzero, reaching about 0.063 mass fraction on paired coordinates. Existing equal
means are descriptive; insufficient confirmed profile groups prevent learned blends.
