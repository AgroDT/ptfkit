---
title: PTF Catalog
---

## PTF source specifications

The PTF catalog is formed from source specifications in YAML format. Each file
describes a single scientific publication and the pedotransfer functions
extracted from it by ptfkit. The specification serves both as a trackable
scientific document and as the source from which ptfkit generates
implementations, tests, and documentation.

This page explains what the specifications represent and what information they
must preserve. The
[`ptf-spec.schema.json`](https://github.com/AgroDT/ptfkit/blob/main/specs/schema/ptf-spec.schema.json)
file remains the authoritative definition of the complete YAML structure,
allowed values, and required fields. Existing files under
[`specs/functions/`](https://github.com/AgroDT/ptfkit/tree/main/specs/functions)
provide complete examples.

## One file represents one source

The filename is an APA-style slug derived from the source, such as
`rawls1982.yaml`. It identifies the source throughout ptfkit and must remain
stable after publication.

The top-level `source` section records:

- a short summary used to identify the source in the catalog;
- the complete APA citation;
- the DOI and DOI URL when they are available.

The optional top-level `scope` describes the publication as a whole. Its
territory and dataset identify where the source data came from; they are not a
claim that every documented PTF is suitable everywhere within that region.

## Functions describe scientific and public behavior

The `functions` list contains the PTFs documented from the publication. Each
function combines four kinds of information:

- `public_api` gives the public function name and a concise summary;
- `scope` identifies the predicted property and the scientific model family;
- `inputs` and `outputs` define the quantities exposed by the function;
- `implementation`, when present, records the executable equations.

Input order and record-field order are significant and must follow the intended
public interface. The source territory describes the complete publication and
its module. A function declares a territory only when it is narrower or
different. The two descriptions remain independent: function territory neither
inherits from nor overrides source territory.

The `status` communicates how far the function has progressed:

- `draft` means that extraction or documentation is incomplete;
- `blocked` means that the available source does not support a safe
  implementation;
- `ready-for-implementation` means that the scientific description and
  equations have been reviewed but generated targets are not yet complete;
- `implemented` means that the retained targets have been generated and
  verified.

The catalog may therefore document functions that are not yet callable. Users
should check both the function status and the API reference for their target.

## Inputs, quantities, units, and domains

Quantitative inputs identify a source variable through a name, symbol, unit,
domain, and description. Outputs additionally carry a stable `quantity`
identifier resolved against `specs/quantities.yaml`, a normalized `unit` identifier
from `specs/units.yaml`, and `reported_unit` preserving the literal source notation.
These values must preserve the source's definitions and numerical values. A domain records the published calibration or
mathematical range; it does not imply that every target performs runtime range
validation.

Categorical inputs reference a self-contained enum definition and bind it to a
function argument name. The enum owns its type description and admissible
values, while the binding may optionally describe the argument's role in that
function. Units, numeric domains, and scientific symbols do not apply to enum
inputs. The binding name belongs to the function, so one enum type can be used
under different argument names.

Outputs are either scalar values or records with ordered fields. Record names
are stable public type names, while field order is part of the cross-target
result contract. Reusable parameter declarations, enum types, and record shapes
may be declared once in `$defs` and referenced by multiple functions. The
`$defs` key is the canonical name of a reusable declaration, type, or record.
Enum definitions shared by multiple source specifications live directly under
`specs/definitions/` and are referenced with a relative file reference such as
`../definitions/soil.yaml#/$defs/UsdaTextureClass`. References are resolved
relative to the YAML document that contains them. Only local direct references
to one `$defs` member are supported; source-local `$defs` remain independent,
including when a local definition has the same name as a shared definition.
Shared definitions keep their defining document identity in generated targets,
so Python functions from separate source modules accept the same enum class and
the same typed `EnumArray` without conversion. The input binding description
remains specific to the function and is not taken from the shared type.
Shared definition filenames use lowercase identifiers (`soil.yaml`, for example).
Referenced enums are emitted once in `ptfkit.definitions.soil` for Python,
`ptfkit::definitions::soil` for Rust and C++, and
`ptfkit/definitions/soil.h` for C (with the `definitions_soil_` symbol prefix).
Python consumers import the shared class from its defining module; source-local
enums remain available through their existing source modules. Unreferenced shared
definitions are validated but do not produce target modules. Remote references,
nested definition paths, and references through other definitions are unsupported.
Both registries are top-level maps keyed by stable identifiers. The unit registry
owns only `preferred_notation` and equivalent `aliases`. The quantity registry
lists allowed unit identifiers and owns each quantity × unit tolerance.

```yaml
quantity: volumetric_water_content
unit: volume_percent
reported_unit: "vol.%"
```

Alias matching is exact and contextual: the reported notation must equal the
selected unit's preferred notation or an alias, and the quantity must permit that
unit. Ambiguous notations such as `%`, `1`, and `dimensionless` are interpreted
only within the quantity's allowed units. Multiple units within one quantity
must not claim the same notation.

Aliases preserve numerical values exactly. `vol.%`, `% v/v`, and
`% volume/volume` share a representation; `cm³/cm³` and `cm^3/cm^3` do too.
Volume fractions and volume percentages, `mm/h` and `cm/h`, and `kPa` and
`cm H2O` remain distinct. Normalization never multiplies, divides, offsets, or
otherwise transforms a value. Missing identifiers, unsupported quantity/unit
pairs, and unmatched source notations block validation and require an explicit
registry decision. Registry edits must be reviewed for numerical equivalence;
validation checks the declared aliases, not physical conversion formulas.

## Scientific evidence and numerical expectations

Specifications retain more than executable formulas:

- `scientific_notes` records derivations, source notation, numerical policy,
  and review decisions that apply to the source;
- documentation notes and warnings communicate function-specific limitations;
- `verification_cases` preserve representative inputs and fixed expected
  outputs with `published` or `calculated` provenance; comparison is defined by
  the [verification policy](../contributing/verification.md), with reviewed
  function-output overrides recorded in YAML when the source supports them;
- `edge_cases` record boundary conditions and the expected behavior.

This information must be supported by the publication or by an explicit,
reviewed implementation decision. Missing units, ambiguous formulas, unclear
result shapes, or unsupported numerical assumptions must remain visible and
can prevent a function from advancing beyond `draft` or `blocked`.

## Implementation data

Functions marked `ready-for-implementation` or `implemented` include an
`implementation` and at least one verification case. Verification-case IDs are
required to be unique within each function and valid as Rust test function
names; descriptive lowercase `snake_case` is recommended, avoiding Rust keywords.
Specification validation checks uniqueness, not Rust identifier syntax; invalid
names may fail during Rust code generation or compilation. See the
[verification policy](../contributing/verification.md) for details.

Implementations express ordered variables used to reproduce
the published PTF. A variable can be populated by a formula or by a typed lookup.
Enums, records, and lookups are independent reusable definitions: a lookup maps
an enum member to a record, and later formulas can access fields of that record.
Enum definitions give each categorical member a stable schema `name`, its exact
canonical textual `value`, and optional documentation-only `description`.
Lookup rows reference the member `name`; they do not define public numeric codes
or match canonical strings at runtime. Targets may encode members with private
ordinals as an implementation detail. Scalar outputs resolve to one value,
while record outputs resolve their declared fields by name or return a compatible
record-valued variable directly.

Python exposes scalar categories as ordinary `Enum` members. Reusable arrays
are constructed once with `EnumType.array(...)` and represented by a typed
`EnumArray[EnumType]`; generated wrappers pass its private `uint32` NumPy array
to the native ufunc without re-encoding it on each call. Strings, integers, and
arbitrary arrays are not accepted as enum inputs.

The YAML is the canonical target-independent representation. Language-specific
details, generated file ownership, and the commands used to validate and
generate targets are documented in the
[development guide](../contributing/development.md).
