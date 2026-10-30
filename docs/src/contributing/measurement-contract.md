# Measurement contract

## Purpose

The measurement contract gives ptfkit and `ptfkit-eval` a shared,
machine-readable description of the physical meaning of a value. Matching an
argument name or a displayed unit is never sufficient for evaluation.

Version 1 is defined by
`specs/schema/measurement.schema.json`. The generated function-manifest
envelope is defined separately by `specs/schema/ptf-manifest.schema.json` and
has `schema_version: 1`.

## Descriptor fields

Every descriptor contains the following required fields:

| Field | Meaning |
| --- | --- |
| `quantity` | Stable identifier from `specs/quantities.yaml` |
| `unit` | Stable canonical identifier from `specs/units.yaml` |
| `reported_unit` | Literal notation at the source or public API boundary |
| `basis` | Material represented by the value and its denominator |
| `status` | How the value was obtained |
| `role` | How the value participates in an evaluation |

Optional or empty fields carry qualifiers that must not be inferred from a
name:

- `particle_size` defines open or closed lower and upper particle-diameter
  bounds and their unit;
- `conditions` defines controlled measurement conditions such as a
  matric-potential magnitude;
- `method` identifies an analytical method when method equivalence matters;
- `computational_domain` is the executable numeric interval in the descriptor's
  canonical unit;
- `reported_applicability` records source-supported constraints and their
  evidence location.

`status` is one of `required`, `observed`, `converted`, `derived`, `estimated`,
or `imputed`. Function inputs use `required`. Function outputs use `estimated`
or `derived`. Dataset adapters assign the other statuses and retain
transformation lineage outside the descriptor.

`role` is one of `predictor`, `prediction`, `observation`, `model_parameter`, or
`uncertainty`. Role is provenance metadata and is not by itself a physical
compatibility condition: a prediction is normally compared with an
observation.

## Vertical slice

The first reviewed source annotation is in `specs/functions/saxton2006.yaml`:

- `clay` is a fine-earth dry-mass fraction below 2 micrometres;
- `theta_33` is volumetric water content at a matric-potential magnitude of
  33 kPa;
- `saturated_conductivity` is saturated hydraulic conductivity in mm/h.

The manifest fixture at
`codegen/src/fixtures/measurement_manifest.json` represents the same three
contract shapes. Conductivity units carry a dimension and SI scale, so mm/h and
m/s are convertible without treating their numeric values as equal.

## Compatibility levels

Compatibility is evaluated in this order:

1. `quantity`, `basis`, particle-size interval, measurement conditions, and a
   required method must be semantically equal. A disagreement is
   `incompatible`.
2. Both unit identifiers must be registered for the quantity. Equal units need
   no conversion. Different units are convertible only when both have conversion
   metadata with the same dimension.
3. An observed value in the same unit is `exact`; an observed value in a
   convertible unit, or a value whose status is `converted`, is
   `unit_converted`.
4. A value produced by an explicitly registered deterministic derivation is
   `exactly_derived`. The derivation identifier, inputs, and lineage must be
   retained by the dataset adapter.
5. Values with `estimated` or `imputed` status are `estimated` and must not enter
   the primary observed-only benchmark.

Conversion metadata never authorizes a conversion across quantities or bases.
In particular, the text `%` is an alias for both mass percent and volume
percent. It cannot select a unit, quantity, or denominator. A dataset mapping
must supply those semantics from source evidence; missing `basis` is rejected
by the schema.

Particle-size intervals are part of equality. A mass fraction with an upper
bound of 1 micrometre is therefore incompatible with a requirement whose upper
bound is 2 micrometres, even when quantity, unit, and column name otherwise
match.

## Migration strategy

The current source schema keeps the legacy `unit`, `quantity`, `reported_unit`,
and free-text `domain` fields while allowing an additional validated
`measurement` descriptor. Codegen rejects a descriptor that disagrees with the
legacy fields. Generated target documentation and APIs therefore remain stable
during migration.

Manifest v1 exposes coverage explicitly. Only implemented functions whose
numeric inputs and outputs have complete descriptors enter `functions` during
the staged migration. `coverage` records the total implemented count, emitted
count, and every omitted function with reason
`incomplete_measurement_contract`; omission is never silent.

The reproducible implemented-function inventory is maintained in
`evaluation/datasets/implemented-function-coverage.json` by
`evaluation/experiments/catalog_coverage/audit.py`. It resolves shared
definitions, names every missing input/output descriptor binding and checks
exact agreement with the generated manifest. Counts are per function binding,
including repeated uses of shared definitions. Manifest inclusion is metadata
readiness and does not establish compatibility with a particular dataset.

The Wosten (2001) class-parameter contract uses material `soil` because its
original Dutch Staring classes include mineral and organic soils. This is a
distinct material identifier, not a compatibility wildcard for `mineral_soil`,
`fine_earth` or `unspecified`. Source evidence and review decisions are recorded
in `evaluation/datasets/wosten2001.measurement-review.json`.

Migration proceeds by semantic family rather than by bulk text inference:

1. particle-size fractions, including every source-specific boundary and
   fine-earth or bulk-soil basis;
2. water-content inputs and outputs, including gravimetric or volumetric basis
   and matric-potential conditions;
3. hydraulic conductivity and infiltration rates;
4. density, carbon, organic matter, porosity, and exchange properties;
5. fitted model parameters, climatic predictors, and source-specific
   quantities.

Each source migration requires review of the publication evidence. Descriptions
may help locate candidates but are not converted automatically. A descriptor is
added only when all required semantics are supported; otherwise the field stays
legacy and is ineligible for manifest-driven evaluation.

## Schema evolution

Canonical retention datasets have their own version independently of manifest
v1. Dataset version 1 remains restricted to volumetric water content. Dataset
version 2 additionally supports gravimetric `mass_fraction` with denominator
`dry_soil_mass`. Unit and denominator combinations are validated together;
version-1 records are not reinterpreted. A mass ratio has no universal upper
bound of one. The material identifier must still be supplied explicitly, and
neither export nor schema acceptance proves PTF compatibility.

Evaluation plans also have an independent version. Version 2 adds explicit
finite multi-output candidates, with each pressure and measurement method
resolved from the manifest. This does not change manifest v1 or reinterpret
version-1 evaluation plans. A finite set of output pressures is not a
continuous pressure-domain claim.

New registry identifiers can be introduced within version 1 when their existing
field semantics are unchanged. Adding descriptor fields, changing required
fields, expanding closed vocabularies, changing compatibility meaning or
ordering guarantees, or reinterpreting registry data requires a new manifest
schema version and an explicit reader migration.


The Saxton2006 base function adds the eighteenth complete manifest entry
(146 implemented functions total). Its available-water output is a pressure
interval difference, not a prediction at one pressure. Normal density is a
model parameter, not observed sample density. Complete metadata and successful
numeric execution still require separate source/data eligibility review.
