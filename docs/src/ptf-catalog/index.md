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

Quantitative inputs and outputs identify a scientific quantity through a name,
symbol, unit, domain, and description. These values must preserve the source's
definitions and conversions. A domain records the published calibration or
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

## Scientific evidence and numerical expectations

Specifications retain more than executable formulas:

- `scientific_notes` records derivations, source notation, numerical policy,
  and review decisions that apply to the source;
- documentation notes and warnings communicate function-specific limitations;
- `verification_cases` preserve representative inputs and fixed expected
  outputs with `published` or `calculated` provenance; comparison is defined by
  the [verification policy](../contributing/verification.md), never tuned in YAML;
- `edge_cases` record boundary conditions and the expected behavior.

This information must be supported by the publication or by an explicit,
reviewed implementation decision. Missing units, ambiguous formulas, unclear
result shapes, or unsupported numerical assumptions must remain visible and
can prevent a function from advancing beyond `draft` or `blocked`.

## Implementation data

Functions marked `ready-for-implementation` or `implemented` include an
`implementation`. Implementations express ordered variables used to reproduce
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
