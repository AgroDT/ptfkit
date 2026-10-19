# ptfkit-eval implementation plan

## Status

In progress. The measurement-contract vertical slice, Phase 1 public manifest,
and the initial `ptfkit-eval` scaffold are implemented. The next task is a
manifest-aware evaluation-plan loader that validates function, output, model
adapter, quantity, unit, and interval references before dataset ingestion.

This document defines the staged work needed to add a separate `ptfkit-eval`
Python distribution to this repository. The package will evaluate implemented
ptfkit functions against external measured soil datasets while preserving the
meaning, units, provenance, and applicability of every value used in a
comparison.

The initial dataset is `meta_v3.3.xlsx`. It is an input to the work, not the
runtime data model of the package.

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
schema, and deterministic range-gated router are scaffolded. Manifest-reference
validation and the remaining package modules are still pending.

Add `targets/ptfkit-eval/` with:

```text
targets/ptfkit-eval/
  pyproject.toml
  uv.lock
  tasks.toml
  schemas/
    evaluation-plan.schema.json
  src/ptfkit_eval/
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
- confidence intervals;
- results inside and outside reported applicability metadata.

Conductivity reports should also include log-scale errors, geometric bias, and
fractions within factors of 2, 5, and 10.

Water-retention curve errors should first be aggregated within a sample so that
samples with dense pressure grids do not dominate. Uncertainty intervals should
use clustered resampling by profile or, when profile identifiers are
unavailable, by source.

Every comparison should provide both:

- a maximal cohort using every eligible sample for each function; and
- a common cohort containing the same samples for all functions being ranked.

A single ranking across different targets, protocols, or cohorts is prohibited.

## Phase 8: make runs reproducible and reportable

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

## Phase 9: perform the first Russian-dataset pilot

The pilot should start with water-retention observations because they have the
largest target coverage. It should include only functions whose particle-size
definitions, organic-property definitions, water-content bases, and pressure
conditions are exactly compatible or exactly derivable.

The pilot should produce three outputs:

1. A quality-control and normalization report for `meta_v3.3.xlsx`.
2. A complete function-sample eligibility matrix, including exclusion reasons.
3. A limited external-validation report on the scientifically compatible
   subset.

Saturated-conductivity evaluation should follow only after texture predictors
and conductivity units can be joined for the same samples. Any local
recalibration or selection of a preferred PTF should be a later, separately
registered experiment with source- or region-grouped holdout data.

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
- per-sample curve weighting;
- range-gated routing at boundaries, explicit gap rejection, and deterministic
  overlap blending;
- composite provenance and protection against selecting members from test
  targets;
- seam continuity and whole-curve monotonicity diagnostics;
- clustered resampling determinism with a fixed seed;
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
- repeated runs from identical inputs produce identical normalized artifacts
  and predictions;
- package verification is integrated with Mise and CI;
- the pilot report clearly distinguishes external validation from calibration
  and from claims of national representativeness.
