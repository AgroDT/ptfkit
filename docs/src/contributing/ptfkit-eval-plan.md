# ptfkit-eval implementation plan

## Status

Latest continuation (2026-10-23): training-input-only marginal empirical
envelopes, fold-specific domains/error strata, target-free composite transition
member contrasts, paired cluster metric differences, and nested training of
constant convex two-curve ensemble weights are implemented and integrated into
run schemas/artifacts/reports, including learned-fold input domains. The latest
component verification has 494 passing tests. Finite-grid hard-switch boundary
training and fitted-seam diagnostics are implemented. Nonlinear gates, learned
blend boundaries, weight/boundary uncertainty, and full selection-process
uncertainty remain pending.
Held-out curve physical diagnostics and locked outer strategy descriptive
maximal/common assessment are implemented. Native strategy confidence intervals
for descriptive CV statistics remain explicitly unestimated. Conditional
outer-rule risk intervals now integrate explicit native registration, full
coverage/provenance checks, failure artifacts and simultaneous family allocation,
with a generated IID population example. These intervals have a different target;
averaged-over-training selection-process inference remains unfinished.
Whole-group selection/refitting bootstrap trajectories are now available as
explicit retraining sensitivity, with preserved original cluster identities,
unequal sample-occurrence weights, and retained failed draws. They are not
confidence intervals. The source-backed
[inference qualification note](ptfkit-eval-inference.md) records why the
unequal-group target and complete tuning procedure need additional validation.
Supplied-forecast selection and shared sample-occurrence materialization now
support exact calibration for informative group sizes, missing targets and
finite-grid switch failures. Five mathematical scenarios have independent risk
oracles and installed-wheel replay. They expose selective completion and target
mismatch; they qualify no confidence interval.
The latest implementation evidence and continuation order are recorded in
`ptfkit-eval-progress.md`. Primary-source review remains deferred.

In progress. The measurement contract, public manifest, initial `ptfkit-eval`
scaffold, range-gated router, manifest-aware evaluation-plan loader, first
reviewed model adapter, curve execution layer, and reproducible structural
inventory of `meta_v3.3.xlsx` are implemented. A checksum-bound draft
source-to-canonical mapping, its JSON Schema, and its inventory-aware loader are
also implemented. A deterministic source-level retention profiler is bound to
the same workbook checksum and records the evidence needed to resolve each
water-content and pressure encoding without inferring units from value ranges.
The mapping now contains an exact source-rule contract for all 27 profiled
retention sources. A rule-gated canonical retention normalizer accounts for
every source row, preserves cell lineage, separates fitted van Genuchten
parameters, and applies only fully confirmed physical conversions.

The read-only workbook inspection records sheet names, dimensions, repeated or
multiline header blocks, merged cells, formulas, missing-value markers, and
candidate sample identifiers in `evaluation/datasets/meta_v3_3.inventory.json`.
The reviewed facts, proposed source aliases, quarantines, and unresolved
scientific questions are encoded in `evaluation/datasets/meta_v3_3.yaml`. The
mapping remains `draft_blocked`. The first real normalization run accounts for
all 1,847 populated `ОГХ` rows. The first evidence-reviewed source now yields
130 canonical observations for ten Chestnova samples; 1,577 observations retain
blocked-rule exclusions, 48 expose stale cached sample identifiers, and 92
fitted van Genuchten parameter rows enter a separate table. Full-curve matching
against the `Данные` wide blocks also exposed a second failure mode: internally
consistent long-sheet identifiers can still name the wrong master sample. The
normalizer therefore applies only confirmed sample crosswalks, never positional
or case-folded joins. The wide-to-long check is now a reusable, checksum-bound
audit with declarative source blocks. It independently reports point-multiset,
complete-curve identity, fitted-parameter, transform-review, and confirmed-
crosswalk status. All 27 profiled sources and all 1,755 long-form observations
are now structurally audited. Of these, 1,741 observations have exact master-
sheet counterparts; the 14 additional Shvarov observations are preserved as an
explicit mismatch. Twenty-one rules are structurally reconstructable, while
five exact point multisets retain broken cached identities. The audit also
covers all 92 fitted van Genuchten parameter pairs, including the parameter-only
Kokareva source, categorical axes, numeric missing markers, coordinate-level
exclusions, block-specific transforms, and explicit null observations. The
first manifest-aware predictor audit is now implemented: it derives 206
candidate sample rows exclusively from reviewed retention blocks, records
cell-level input lineage in memory, and produces a count-only artifact. The
public manifest now exposes five contracts: `calc_ptf_clapp1978`,
`calc_ptf_vereecken1989`, and the three sand-only Set 1 functions from
Gunarathna et al. (2019) for 10, 33, and 1,500 kPa. The Vereecken function has
a registered reduced van Genuchten adapter and four explicit predictor
bindings. Thirty-four candidate
rows contain all four raw inputs, but none is eligible yet: the workbook's
particle-size intervals, carbon method, and bulk-density unit and method do not
yet satisfy the function contract. A source-local header now establishes a
below-2-micrometre clay boundary for 12 Panina 2015 rows, but none of those rows
has all four raw Vereecken inputs and their fraction unit and mass basis remain
unresolved. The 34 complete-input rows retain below-1-micrometre clay. The
headed `ГС-PSD` schemes provide no 1-to-2-micrometre bin, so exact summation
cannot repair that mismatch. The audit preserves these distinctions instead of
treating similarly named columns as compatible. Each Gunarathna function has
51 rows with a populated raw sand value, but none is eligible: source review
established that the PTF requires the 50-to-2,000-micrometre dry-mass fraction
of fine earth measured by sieve analysis, while the workbook proves only a
greater-than-50-micrometre lower boundary.

This document defines the staged work needed to add a separate `ptfkit-eval`
Python distribution to this repository. The package will evaluate implemented
ptfkit functions against external measured soil datasets while preserving the
meaning, units, provenance, and applicability of every value used in a
comparison.

The initial dataset is `meta_v3.3.xlsx`. It is an input to the work, not the
runtime data model of the package.

## Remaining roadmap

The reusable foundation and dataset-discovery layer are implemented. Seven
delivery packages remain before the acceptance criterion is met:

| Package | Scope | Relative size | Status |
| --- | --- | --- | --- |
| 1. Source rules and normalization | Resolve source-level units and bases; emit canonical samples, measurements, particle bins, retention observations, and exclusions | Large | Retention contract and normalizer implemented; predictor lineage started; source review and particle tables pending |
| 2. Quality control and eligibility | Validate physical consistency and build the complete function-sample-target matrix | Large | Manifest-aware predictor eligibility implemented for the first five public function contracts |
| 3. Approximation families | Register and implement van Genuchten, Brooks-Corey, and remaining required fit/adaptation variants | Extra large | Four versioned families, bounded multistart fitting, identifiability/failure gates, and local conditional uncertainty implemented; source-specific reference conventions remain blocked |
| 4. Evaluation matrix | Execute every eligible atomic PTF and fixed composite with full traces | Medium | Portable canonical run pipeline executes curves, fixed-pressure outputs, and fixed composites with observation/sample eligibility and traces |
| 5. Metrics and uncertainty | Per-sample aggregation, clustered intervals, prediction intervals, parameter uncertainty, and domains | Large | Sample-balanced metrics, maximal/common cohorts, metric and paired cluster intervals, fixed-rule conformal intervals, local fitting uncertainty, and standalone/fold-specific empirical domains implemented; full selection-process uncertainty pending |
| 6. Nested selection | Deterministic grouped folds, atomic and ensemble selection, learned routing, and leakage protection | Extra large | Identity-only folds, fixed selection, constant convex weights and finite-grid hard-switch boundaries with inner training/outer refits implemented; nonlinear gates and learned blends pending |
| 7. Reporting and pilot | Reproducible artifacts, CLI, human report, and the complete Russian-dataset pilot | Large | Checksum-bound run artifacts, replay, CLI, Markdown reporting, and standalone synthetic example implemented; real-data pilot blocked by source review |

The first retention slice of package 1 is implemented. Each of the 1,755
observation rows now produces either a canonical pressure-water-content record
with cell lineage or an explicit exclusion, and the 92 fitted VGN rows are kept
in a separate parameter table. The current checksum-bound result is 130
normalized and 1,625 explicitly excluded: 1,577 by unresolved source rules and
48 by cached sample identifiers that disagree with the source and sample-number
cells. The normalized slice is the 2017 Chestnova source, whose ten 13-point
curves were matched exactly to master rows before its percent-to-fraction and
pF-to-kPa conversions were enabled. The reusable reconstruction audit now
accounts for all 1,755 observations from all 26 observation sources plus the
parameter-only Kokareva source. Twenty-one rules preserve complete one-to-one
records. The Gumatov 1991 and Sidorova rules explicitly account for 19 and five
empty wide cells omitted from the long table; Bolotov and Manucharova match
explicit nulls at the same sample and axis. Khaydapova 2001, Sadovnikova 2011,
Shein 2012, Badenko 2013, and Panina 2015 have exact global multisets but broken
cached identity groups. Shvarov has 14 long observations without master-sheet
counterparts. All 92 long-form fitted van Genuchten parameter pairs are covered
across Kokareva, Shein, and Panina. Exact particle-boundary composition and
source-local measurement overrides are now implemented. The Panina 2015
control header proves that 12 rows use a below-2-micrometre clay fraction, but
none has all four raw Vereecken inputs. The 34 complete-input rows use a
below-1-micrometre fraction, and the headed `ГС-PSD` blocks contain no
1-to-2-micrometre interval, so they cannot be converted exactly. The next step
is source-level review of the seven workbook sources that supply the 51 sand
values, beginning with the 34 rows that also contain bulk density. That review
must establish the 2-millimetre sand upper boundary, fine-earth dry-mass basis,
sieve method, water-content basis, density method, and pressure convention
before gravimetric observations can be converted to volumetric targets. No
value-magnitude heuristic may promote a binding.

The first additional migration is complete for the sand-only Set 1 family from
Gunarathna et al. (2019). Its three functions predict pressure-plate volumetric
water content at 10, 33, and 1,500 kPa and avoid the unresolved
below-2-micrometre clay input. Primary-source review established a
50-to-2,000-micrometre sieve fraction, dry-mass fine-earth basis, and the
published input domain. The functions now appear in the public manifest and
eligibility matrix. The master sand column is populated for 51 retention
candidates, but it states only particles above 50 micrometres; a workbook-wide
header scan found no source-local statement of the 2-millimetre upper boundary,
basis, or method. The 51 rows belong to seven workbook sources, and 34 also
contain a bulk-density value. Their retention observations are gravimetric or
unresolved rather than directly compatible volumetric targets. Dataset-source
review and explicit output eligibility therefore remain required before any
Gunarathna prediction may be scored.

Review of the first of those seven sources, Sapozhnikov et al. (1988), has now
resolved two independent claims without relying on value magnitudes. The 12
long-sheet sample groups map bijectively by sample number to 12 complete
nine-point master-sheet curves, so the case-only source alias is confirmed.
The block control cell `Данные!W7` and legend cell `Данные!W1` establish that
the water quantity is gravimetric. The source remains blocked because those
cells do not distinguish percent from fraction, the physical interpretation of the first
`0.01`/`-1` pF position is unresolved, and the workbook does not document the
sand upper boundary and method or the bulk-density unit and method. The next
source-review step is therefore to obtain the primary publication or another
source-level methods record for those claims; if it cannot be recovered, move
to the next source while retaining Sapozhnikov 1988 as an explicit partial
review rather than inferring the missing semantics.

The 51 sand-bearing candidates are now explicitly attributed to six
observation blocks plus the parameter-only Kokareva 2007 block: 12
Sapozhnikov, 6 Khaydapova, 6 Shein 2011, 5 Makarychev-1, 7 Makarychev-2, 10
Chestnova, and 5 Kokareva rows. Thirty-four of these rows also contain bulk
density. If the Sapozhnikov publication remains unavailable, Kokareva 2007 is
the next high-value review because all five rows contain sand and density and
their stored van Genuchten parameter sets can also advance the approximation-
family validation work. Those parameters remain unusable until their equation,
axis, units, and fitting convention are confirmed from source-level evidence.

The first descriptive metric slice is implemented in `summarize_retention_errors()`.
It accepts one already eligible canonical retention cohort, reports per-sample
errors and source-local sample counts, and gives each sample equal total weight.
Within a sample, distinct pressure points have equal weight. Cohort RMSE is the
square root of mean sample MSE; median absolute error uses the same balanced
point weights and averages adjacent errors at an exact half-weight split.
Duplicate sample-pressure keys and nonfinite values are rejected; finite
unphysical predictions are scored without clipping. This is a descriptive
point-grid protocol, not the future log-pressure-integrated selection loss.
`build_retention_cohorts()` now constructs maximal cohorts and a common exact
source/sample/pressure intersection across every declared candidate. It checks
dataset, protocol, target contract, observed values, and profile consistency;
excluded points and empty candidates remain explicit. This is stricter than
matching sample identifiers alone and requires no target-dependent selection.

`bootstrap_retention_errors()` implements the versioned
`cluster_percentile_linear_v1` method with whole-source or whole-profile draws,
replacement, and full cluster multiplicity. Profiles are local to their source.
Replicate metrics preserve equal sample weight. The seed and minimum number of
groups must be supplied; confidence defaults to 95% with 2,000 replicates.
Missing profiles either produce `insufficient_evidence` or, only under an
explicit policy, regroup the entire cohort by source. Empty cohorts and too
few groups produce no intervals. Results retain the plan, effective grouping,
group count, and descriptive summary. The minimum group count is a declared
evidence gate, not a statistical coverage guarantee. Prediction intervals,
parameter uncertainty, paired candidate-difference intervals, and selection
contracts remain pending. No real-workbook scoring was enabled by this slice.

## Objective

Build a reproducible evaluation system that can answer all of the following for
every prediction:

- Which ptfkit function and package version produced it?
- Which measured values were bound to each function input?
- Are the physical quantities, units, operational definitions, and measurement
  bases compatible?
- Which conversions or derivations were applied?
- Is the sample inside the computational and reported applicability domains?
- Which raw workbook cells support the inputs and target observation?
- Why was a function-sample pair included or excluded?
- Was a curve predicted by one function or by a registered composite, and which
  member produced or contributed to every pressure point?

## Acceptance criterion

The module is accepted only when the complete workflow below is reproducible
for every implemented ptfkit function and every target dataset that contains a
scientifically compatible measured output:

1. Every value that can be extracted reliably is normalized with physical
   meaning, units, basis, raw-cell provenance, and quality state. Ambiguous
   values remain visible as exclusions rather than being guessed or discarded.
2. Every implemented function appears in a function-sample-target eligibility
   matrix. A function that cannot be evaluated must have a machine-readable
   reason; complete coverage does not mean forcing incompatible comparisons.
3. Every eligible atomic function and every registered ensemble is executed on
   maximal and common cohorts. Parameter-producing functions are evaluated
   through a versioned adapter for their exact approximation family and
   parameter convention.
4. For each dataset, target, protocol, and predeclared cohort, the report names
   the selected atomic function and selected ensemble, or reports
   `insufficient_evidence`. Selection must use nested grouped validation and
   must never inspect the outer test targets.
5. Every selected and non-selected candidate retains its coverage, exclusions,
   metrics, uncertainty, applicability domain, validated axis range, and full
   prediction provenance. A winner without those diagnostics is not an
   acceptable result.
6. Every supported approximation family, including van Genuchten and
   Brooks-Corey variants present in the ptfkit corpus, has an explicit equation
   and parameterization identifier, parameter constraints, fitting criteria,
   identifiability checks, extrapolation policy, and uncertainty protocol.
7. Identical workbook bytes, mapping, ptfkit manifest, evaluation plan, and
   random seed reproduce identical normalized artifacts, folds, candidates,
   predictions, selections, and reports.

A dataset for selection purposes is a source publication or another
predeclared independent group, optionally subdivided into scientifically
defined strata. An individual measured curve is not an independent dataset on
which a winner may be chosen after observing that curve. A sample-level selector
is allowed only when it uses predictors available at prediction time and is
trained entirely outside the held-out group.

The first release should prioritize scientifically defensible comparisons over
the number of functions evaluated.

## Non-goals

The initial work will not:

- infer physical meaning from matching column and argument names;
- treat particle-size fractions with different boundaries as equivalent;
- infer percent-versus-fraction scales from numeric magnitude;
- silently correct suspect measurements;
- impute missing predictors in the primary benchmark;
- calibrate or refit published PTFs;
- produce one global leaderboard across different targets or sample cohorts;
- make a claim of representative coverage for the whole territory of Russia.

## Evidence from the initial dataset

The following inventory is a planning baseline and must be reproduced by the
eventual importer tests:

- The workbook contains eight sheets and more than 4,200 formula cells.
- The `Data` sheet contains 506 usable sample rows from 50 sources, 49 control
  rows that describe pressure grids, and trailing formula rows whose cached
  sample identifier is `_`.
- The main properties include 182 physical-clay values below 10 micrometres,
  171 fractions below 1 micrometre, 100 sand values above 50 micrometres, 100
  silt values from 1 to 50 micrometres, 221 bulk-density values, 200 organic
  carbon values, and 185 humus values.
- Only 96 rows contain sand, silt, and the fraction below 1 micrometre. This is
  not automatically a compatible sand-silt-clay triplet for PTFs whose clay
  boundary is 2 micrometres.
- The long water-retention sheet contains 1,847 rows for 239 sample identifiers.
  Safe Unicode, whitespace, and case normalization joins 171 of those
  identifiers to the main sample sheet. Explicit source-specific crosswalks are
  required for the remainder.
- Of those 171 joined samples, 46 have the three available broad particle-size
  fields and 29 additionally have bulk density.
- Water content uses mixed `W`, `Q`, `VGN`, and unresolved representations.
  Percent and fractional scales occur within the workbook and must be resolved
  from source evidence.
- Pressure representations include pF, kPa, an ambiguous `mPa` label, fitted
  parameter labels, and named soil-water constants.
- The dissertations sheet contains 36 saturated-conductivity values, but none
  of those rows contains sand and only six contain the fraction below 1
  micrometre.
- Candidate quality-control failures include porosity `473`, particle density
  `23774`, pF `32`, and particle-size sums outside a reasonable closure range.

These counts are not evaluation results. They are upper bounds before semantic
compatibility and quality-control rules are applied.

## Architectural boundary

The responsibilities must remain separated:

| Component | Responsibility |
| --- | --- |
| `specs/` and codegen | Authoritative function, quantity, unit, model, and applicability contracts |
| `ptfkit` | Generated numerical implementations and a generated machine-readable function manifest |
| `ptfkit-eval` | Dataset normalization, compatibility decisions, execution, metrics, and reporting |
| Evaluation configuration | Versioned mappings, single-function candidates, composite-curve definitions, and a reproducible evaluation plan |
| Raw and derived data | External or separately managed artifacts with checksums and provenance |

`ptfkit-eval` must consume a public generated manifest from `ptfkit`. It must
not scrape Python signatures or docstrings and must not duplicate equations.

## First work item: define the measurement contract

This is the first task. Do not begin by scaffolding the package or writing an
Excel reader.

The existing specification model identifies registered quantities and units for
outputs, but numeric inputs do not have equivalent machine-readable semantics.
The dataset also demonstrates that a quantity and unit alone are insufficient:
particle-size boundaries, fine-earth versus bulk-soil basis, water-content
basis, pressure condition, and measurement status affect compatibility.

The first pull request should define and validate a shared measurement
descriptor that can represent at least these three end-to-end examples:

1. Clay as a mass percentage of fine earth below 2 micrometres.
2. Volumetric water content at a matric-potential magnitude of 33 kPa.
3. Saturated hydraulic conductivity with a convertible canonical unit.

The descriptor should cover:

- stable quantity identifier;
- stable canonical unit identifier;
- material and denominator basis;
- particle-size interval where relevant;
- measurement condition such as matric potential;
- observed, converted, derived, estimated, or imputed status;
- optional measurement method;
- output role such as prediction, model parameter, or uncertainty;
- structured computational domain;
- structured reported applicability information when supported by the source.

The first pull request should also specify how this descriptor extends numeric
inputs, output fields, and generated metadata. It should include a migration
strategy for existing specifications rather than changing all publications
without a reviewed model.

### Completion criteria for the first work item

The first work item is complete when:

- the descriptor and its terminology are documented;
- the JSON Schema represents the three vertical-slice examples;
- codegen loads and validates those examples;
- a versioned manifest schema is defined;
- compatibility can distinguish exact, unit-converted, exactly-derived,
  estimated, and incompatible measurements;
- ambiguous percent notation cannot be resolved without a quantity and basis;
- particle fractions with upper bounds of 1 and 2 micrometres are not treated
  as interchangeable;
- focused schema and codegen tests pass;
- the remaining corpus migration is enumerated before bulk edits begin.

Implementation details and the migration inventory are recorded in the
[measurement contract](measurement-contract.md).

## Phase 1: generate a public function manifest

Status: implemented. The initial manifest exposes one fully described function
and explicitly records every implemented function still awaiting measurement
metadata; corpus migration remains incremental.

Extend codegen to produce a deterministic, versioned manifest for the Python
distribution. Each implemented function entry should include:

- source slug and stable function identifier;
- public Python module and callable name;
- status;
- ordered input descriptors;
- output descriptors and record-field order;
- computational domains;
- reported applicability metadata;
- model identifier and parameter bindings where applicable;
- output roles;
- warnings needed by the evaluator;
- manifest schema version.

During corpus migration, the manifest must include only fully described
implemented functions and enumerate every omitted implemented function in its
coverage metadata. The evaluator must never treat an omitted function as
evaluated or inapplicable.

The manifest should be packaged in the `ptfkit` wheel and exposed through a
small public read-only API. Codegen tests should verify deterministic output,
callable parity, field order, and rejection of incomplete measurement
descriptors.

## Phase 2: create the ptfkit-eval distribution

Status: in progress. The pure-Python distribution, versioned evaluation-plan
schema, deterministic range-gated router, manifest-aware loader, executable
`clapp1978_h_theta` adapter, scalar unit conversion, and traced curve executor
are implemented. The loader validates functions, outputs, adapters, physical
quantities, units, bases, parameters, intervals, and overlap routing before
execution. Dataset normalization, eligibility, metrics, and reporting remain
pending.

Add `targets/ptfkit-eval/` with:

```text
targets/ptfkit-eval/
  pyproject.toml
  uv.lock
  tasks.toml
  src/ptfkit_eval/
    schemas/
      evaluation-plan.schema.json
    catalog.py
    composites.py
    contracts.py
    eligibility.py
    execution.py
    metrics.py
    provenance.py
    units.py
    validation.py
    cli.py
    datasets/
    models/
    reporting/
  tests/
```

The distribution name will be `ptfkit-eval` and the import package will be
`ptfkit_eval`. It will depend on a compatible `ptfkit` manifest schema and use a
local editable `ptfkit` source during repository development.

Add `eval:sync`, `eval:lock`, `eval:test`, `eval:lint`, `eval:format`,
`eval:typecheck`, and `eval:verify` tasks through the existing Mise task include
mechanism. Dataset-independent verification should join the normal CI suite.

## Phase 3: define the canonical dataset model

The evaluator must normalize source data before evaluation. The canonical model
should contain separate logical tables.

### Samples

One row per physical sample, including source, site, profile, horizon, depth,
location, and raw-row provenance.

### Measurements

One row per measured or derived property, including the complete measurement
descriptor, value, source cells, transformation lineage, and quality-control
state.

### Particle-size bins

One row per particle-size interval, with explicit lower and upper diameter
bounds, mass fraction, analytical method, and denominator basis.

### Water-retention observations

One row per pressure-water-content pair, with canonical pressure magnitude,
water-content quantity, basis, units, sample condition, and provenance.

Use an analytical storage format such as Parquet for normalized artifacts. The
Excel workbook remains immutable source evidence and should not be read directly
by evaluation and reporting stages.

## Phase 4: implement the meta_v3.3 adapter

Status: in progress. The checksum-bound structural inventory, reusable XLSX
inspection API, draft mapping, mapping schema, inventory-aware loader, exact
source-rule coverage checks, and rule-gated retention normalizer are
implemented. The `ОГХ` pipeline classifies and accounts for all 1,847 populated
rows as 1,755 observations or 92 fitted VGN parameter rows, with no unclassified
or missing-source rows. One observation rule is confirmed: it emits 130
canonical Chestnova observations after an explicit ten-sample crosswalk derived
from exact 13-point curve matches between `ОГХ` and `Данные`. The remaining run
emits 1,577 blocked-rule exclusions and 48 cached sample-identifier mismatches.
It emits no guessed canonical values. A reusable reconstruction audit now
compares declared wide blocks with long observations and fitted parameters as
multisets, then separately tests whether complete raw identifier groups map
bijectively to master samples and whether confirmed crosswalks agree. It now
covers all 27 profiled sources and accounts for all 1,755 observations.
Twenty-one rules are structurally reconstructable, but only Chestnova is
normalization-ready because the others retain physical-semantic, alias, or
crosswalk blockers. Shvarov has 14 long-only observations; Khaydapova,
Sadovnikova, Shein 2012, Badenko, and Panina have exact point multisets but
unresolved complete-record identity. All 92 long-form fitted parameter pairs
are covered, and only Kokareva's five parameter sets preserve a complete
bijection.
Human resolution of the declared blockers and the remaining canonical sample,
predictor, and particle-size tables are pending.

Create a versioned dataset mapping under:

```text
evaluation/datasets/meta_v3_3.yaml
```

The mapping should include the expected workbook checksum, sheet layouts,
source aliases, sample identifier crosswalks, row roles, and source-specific
measurement rules.

Rules must explicitly resolve:

- percent versus fraction for every water-content source;
- gravimetric versus volumetric water content;
- every pressure representation and sign convention;
- the meaning of the `mPa` label;
- fitted VGN parameter rows versus observations;
- saturated-conductivity units;
- organic carbon and humus provenance and conversions;
- particle-size interval schemes;
- duplicated views of the same samples across sheets;
- formula-derived values;
- reviewed corrections and quarantined records.

The importer should read formulas and cached values separately. It should rebuild
the long water-retention representation in code and compare it with the existing
formula-generated sheet as a validation check.

The raw workbook should not be committed until its redistribution rights,
source attribution, and coordinate-publication policy are decided.

## Phase 5: add validation and eligibility

Validation should report rather than silently repair:

- duplicate and unresolved sample identifiers;
- missing units or bases;
- values outside physical ranges;
- particle-size closure failures;
- non-monotone water-retention observations;
- water content above independently measured porosity;
- bulk density greater than particle density;
- suspect decimal-scale errors;
- stale or missing formula caches;
- ambiguous source mappings.

For every function-sample-output combination, create an eligibility record with
machine-readable reason codes. At minimum support:

- `missing_input`;
- `quantity_mismatch`;
- `particle_boundary_mismatch`;
- `ambiguous_unit`;
- `outside_computational_domain`;
- `outside_reported_applicability`;
- `unresolved_category`;
- `derived_target_not_allowed`;
- `failed_quality_control`.

Compatibility levels should be `exact`, `unit_converted`, `exactly_derived`,
`estimated`, and `incompatible`. The primary benchmark should use only the
first three. Estimated inputs belong in a separate sensitivity analysis.

## Phase 6: implement evaluation protocols

### Fixed water-retention points

Prefer exact measured pressures. Log-pressure interpolation should be a separate
named protocol with declared bracketing and distance requirements. Nearest-point
matching must not be implicit.

Conversions between gravimetric and volumetric water content require measured
bulk density for the same sample and must produce a derived target with recorded
lineage.

### Retention-model parameters

When a PTF returns retention parameters, evaluate its predicted curve at the
observed pressures. Do not assume that fitted parameters from different model
variants or fitting procedures are directly comparable. Add explicit model
adapters for each supported equation and parameter convention.

### Approximation-family registry and fitting

Create a versioned approximation-family registry for van Genuchten,
Brooks-Corey, Campbell/Clapp-Hornberger, and every other hydraulic model needed
by an eligible ptfkit output. Each registry entry must declare:

- a stable family and variant identifier, equation, axis convention, and target
  measurement descriptor;
- parameter names, quantities, units, bounds, fixed relationships, and initial
  value policy;
- the minimum observation count and pressure span required for fitting;
- the objective function, observation weights, optimizer, convergence
  criteria, restart policy, and deterministic seed behavior;
- physical rejection checks, parameter identifiability checks, and whether a
  non-unique or boundary solution is reportable;
- interpolation and extrapolation policy and the validated pressure interval;
- the parameter-uncertainty and curve-uncertainty calculation method.

Fitting an approximation to a measured curve is a separate operation from
evaluating a PTF that predicts parameters of that approximation. Reports must
distinguish at least:

- approximation error of a fitted family against measured points;
- parameter error when compatible reference parameters exist;
- prediction error of the PTF-derived curve at measured pressures; and
- uncertainty introduced by fitting the reference curve itself.

Raw parameter values must not be ranked across different families or
parameterizations. A family fit that fails convergence, identifiability,
physical constraints, or minimum-data requirements remains an explicit failed
fit and must not silently fall back to another family.

### Composite water-retention curves

The evaluator must support a registered curve candidate whose members predict
different, explicit ranges of the matric-potential axis. This is a range-gated
composite (or mixture of experts), not a modification of the published PTFs and
not an implicit choice of the best function after seeing the test targets.

The `ptfkit` manifest remains the catalog of atomic functions, outputs, model
identifiers, units, and domains. A versioned evaluation plan owns the composite
definition. At minimum that definition must contain:

- a stable composite identifier and curve target;
- a canonical axis quantity, unit, sign convention, and optional transform;
- ordered members that reference a manifest function, output or model adapter,
  and an explicit closed or open pressure interval;
- a routing rule for overlaps, gaps, and points on interval boundaries;
- a transition policy: an exact hard switch or a declared blending function
  over an explicit overlap interval;
- rules for member failure and extrapolation, with extrapolation disabled by
  default;
- provenance for fixed boundaries, learned boundaries, and learned weights.

The versioned evaluation-plan schema represents a candidate equivalent to:

```yaml
id: example_piecewise_retention
kind: range_gated_curve
axis:
  quantity: matric_potential
  unit: kilopascal
  convention: magnitude
  transform: log10
target:
  quantity: volumetric_water_content
  unit: volume_fraction
  material_basis: fine_earth
  denominator_basis: bulk_volume
members:
  - id: wet_range
    function: calc_ptf_example_wet
    prediction: {kind: model_adapter, id: example_wet_h_theta}
    interval: {lower: {value: 0.1, inclusive: true}, upper: {value: 33, inclusive: true}}
  - id: dry_range
    function: calc_ptf_example_dry
    prediction: {kind: model_adapter, id: example_dry_h_theta}
    interval: {lower: {value: 10, inclusive: true}, upper: {value: 1500, inclusive: true}}
routing:
  gap: reject
  extrapolation: reject
  transitions:
    - kind: blend
      left_member: wet_range
      right_member: dry_range
      interval: {lower: {value: 10, inclusive: true}, upper: {value: 33, inclusive: true}}
      weighting: smoothstep
provenance: {kind: fixed, source: Pre-registered evaluation plan.}
```

The identifiers above are illustrative, not claims that those functions exist.
Schema and semantic validation must reject unordered or ambiguous intervals,
undeclared gaps, multiple active members without a blending rule, incompatible
output quantities, and references absent from the installed manifest.

Eligibility is evaluated at both sample and pressure-point level. Each point
must record the active member or members, their normalized inputs, predictions,
weights, and any exclusion reason. The composite result must retain this trace
rather than only storing the blended value.

Continuity and physical plausibility are evaluation outputs. Reports must show
jumps at seams, monotonicity violations with increasing suction magnitude,
water contents outside declared physical bounds, and the contribution of each
member to error. The evaluator must not silently smooth, clamp, or monotonize a
curve; any such post-processing is a separately registered candidate.

Fixed, literature-based ranges may be used directly. If range boundaries,
member selection, or blend weights are learned from this dataset, that process
is calibration and must use source- or profile-grouped training folds nested
inside the external validation split. Test observations must never choose the
member, boundary, or weight. Single functions and the composite must be
reported separately on both maximal and common cohorts.

### Hydraulic conductivity

Evaluate saturated conductivity in both its physical and base-10 logarithmic
scales. Do not evaluate a conductivity PTF until the target unit and required
particle-size inputs are resolved for the same samples.

### Point and derived outputs

Treat field capacity, wilting point, available water, density, porosity, and
plasticity limits as separate protocols with explicit operational definitions.
Names alone do not establish target equivalence.

## Phase 7: implement metrics and uncertainty

For each target and protocol, report:

- eligible sample, profile, and source counts;
- coverage of the candidate dataset;
- mean error;
- mean absolute error;
- root mean squared error;
- median absolute error;
- a configurable confidence level, with 95% as the default;
- clustered confidence intervals for every reported aggregate metric;
- prediction intervals as a function of the independent variable when the
  available data support them;
- parameter intervals and identifiability diagnostics for fitted approximation
  families;
- the empirical applicability domain and validated pressure range.
- results inside and outside reported applicability metadata.

Conductivity reports should also include log-scale errors, geometric bias, and
fractions within factors of 2, 5, and 10.

Water-retention curve errors should first be aggregated within a sample so that
samples with dense pressure grids do not dominate. Uncertainty intervals should
use clustered resampling by profile or, when profile identifiers are
unavailable, by source.

Keep the following concepts separate in schemas and reports:

- a confidence interval for a population-level error metric;
- a prediction interval for a future measured value or curve point;
- an uncertainty interval for a fitted approximation parameter;
- a reported or empirical applicability domain; and
- an axis interval supported by observations rather than extrapolation.

None of these intervals may be substituted for another. In particular, a
narrow bootstrap interval for RMSE does not expand the physical applicability
domain of a PTF.

Every comparison should provide both:

- a maximal cohort using every eligible sample for each function; and
- a common cohort containing the same samples for all functions being ranked.

A single ranking across different targets, protocols, or cohorts is prohibited.

## Phase 8: select atomic functions and ensembles without leakage

Selection is an evaluated protocol, not a post-hoc sort of test errors. Every
selection plan must declare:

- the independent grouping unit, normally source publication and, where
  justified, region or profile;
- deterministic outer grouped holdouts used only for final assessment;
- deterministic inner grouped folds used for candidate, boundary, and weight
  selection;
- the eligible candidate set, including atomic functions, fixed composites,
  and learnable composites;
- one primary loss, tie-breaking rules, minimum coverage, minimum group count,
  and failure policy;
- whether selection is global for a dataset, stratified by declared soil
  properties, or performed by a predictor-only gating model;
- all tunable pressure boundaries, blend weights, and hyperparameters;
- the random seed and complete training provenance.

The initial curve-selection protocol should use a per-sample loss integrated or
aggregated over the declared log-pressure domain so that a dense curve does not
outvote other samples. Pointwise metrics remain diagnostics. The exact primary
loss and pressure weighting must be registered before the outer test fold is
evaluated.

For each outer fold, the inner process selects and locks:

- the best eligible atomic candidate;
- the best eligible registered ensemble;
- any learned range boundaries or blend weights; and
- any predictor-only gating rule.

The locked candidates are then evaluated once on the outer fold. Reports must
show inner-selection stability, outer-fold performance, coverage, candidate
failure counts, and whether different folds selected different candidates.
Final recommendations must aggregate outer-fold evidence and may report
`insufficient_evidence` instead of forcing a winner.

Using the measured target of a held-out sample to choose its member, pressure
boundary, blend weight, approximation family, or post-processing rule is test
leakage and must be rejected by validation.

## Phase 9: make runs reproducible and reportable

Add commands equivalent to:

```text
ptfkit-eval inspect <workbook>
ptfkit-eval normalize <workbook> --mapping <mapping>
ptfkit-eval plan <evaluation-plan>
ptfkit-eval run <evaluation-plan>
ptfkit-eval report <run-directory>
```

Each run should write:

- a run manifest with package versions, git revision, manifest version, and
  input/configuration hashes;
- normalized eligibility records;
- long-form predictions;
- metrics and uncertainty intervals;
- exclusion counts and reasons;
- machine-readable tables and a human-readable report.

Every prediction must be traceable to its raw cells, input bindings, conversions,
function contract, and output observation.

## Phase 10: perform the first Russian-dataset pilot

The pilot should start with water-retention observations because they have the
largest target coverage. It should include only functions whose particle-size
definitions, organic-property definitions, water-content bases, and pressure
conditions are exactly compatible or exactly derivable.

The pilot should produce five outputs:

1. A quality-control and normalization report for `meta_v3.3.xlsx`.
2. A complete function-sample eligibility matrix, including exclusion reasons.
3. A fit and identifiability report for every registered approximation family
   on every curve with sufficient measured support.
4. A limited external-validation report on the scientifically compatible
   subset, including metric, prediction, and parameter uncertainty where
   supported.
5. A nested grouped selection report naming the best supported atomic function
   and ensemble for each dataset-target-protocol combination, or
   `insufficient_evidence`.

Saturated-conductivity evaluation should follow only after texture predictors
and conductivity units can be joined for the same samples. Any local
recalibration, learned ensemble boundary, blend weight, or selection of a
preferred PTF is part of a separately registered nested source- or
region-grouped protocol. Its locked outer-fold result must remain distinct from
the uncalibrated external-validation result.

## Test strategy

Use small reviewed fixtures rather than the complete workbook for normal CI.
Tests should cover:

- manifest-schema validation and deterministic generation;
- manifest parity with public Python callables and record fields;
- exact unit conversions and prohibited cross-quantity conversions;
- pF-to-pressure conversion;
- particle-size boundary compatibility;
- Excel control rows, formula cells, and cached values;
- explicit identifier aliases and rejection of fuzzy joins;
- hand-calculated metric examples;
- hand-calculated synthetic fits for every approximation family and rejection
  cases for non-identifiable and physically invalid fits;
- per-sample curve weighting;
- range-gated routing at boundaries, explicit gap rejection, and deterministic
  overlap blending;
- composite provenance and protection against selecting members from test
  targets;
- seam continuity and whole-curve monotonicity diagnostics;
- clustered resampling determinism with a fixed seed;
- deterministic nested grouped folds and explicit rejection of target leakage;
- selection based only on inner-fold evidence, including a case where the
  outer-test winner differs from the selected candidate;
- metric confidence intervals, prediction intervals, and fitted-parameter
  intervals with independent synthetic oracles;
- one end-to-end synthetic evaluation run;
- dataset-profile counts when the real workbook is available in an explicit
  integration-test environment.

Generated-code tests must follow the repository's codegen testing conventions.

## Release gates

The first `ptfkit-eval` release is ready only when:

- no input is bound by name alone;
- every conversion is quantity-aware and recorded;
- every composite prediction is traceable to its active members and weights;
- ambiguous records are excluded with reason codes;
- raw workbook duplication does not inflate sample counts;
- result tables report coverage and cohort composition;
- every implemented function has an eligibility result for each relevant
  dataset-target protocol;
- every supported approximation variant has an executable, tested adapter and
  fitting contract;
- every reported winner was selected inside nested grouped validation and then
  evaluated on untouched outer groups;
- every dataset-target protocol reports both the selected atomic function and
  selected ensemble, or `insufficient_evidence`;
- metric confidence intervals, prediction intervals, parameter uncertainty,
  applicability domains, and validated pressure ranges are distinguished;
- repeated runs from identical inputs produce identical normalized artifacts
  folds, predictions, selections, and reports;
- package verification is integrated with Mise and CI;
- the pilot report clearly distinguishes external validation from calibration
  and from claims of national representativeness.


Current verification checkpoint: **433 tests**. The supplied-forecast selection
boundary and exhaustive equal/unequal-group calibration are implemented; see the
latest progress entry. Full strategy confidence intervals remain unqualified.


Latest checkpoint: **443 tests**. Shared native/supplied-forecast group occurrence
materialization and informative missing-target calibration are verified, including
three exact installed-wheel experiment replays. See the last progress entry.
Continue with parameter-instability/boundary scenarios and justified inference;
the active goal and deferred scientific requirements remain unfinished.
