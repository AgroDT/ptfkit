---
title: Scientific verification policy
---

# Scientific verification policy

Verification cases fix representative inputs and expected outputs in each PTF
specification. They test generated implementations; they do not replace model
evaluation against observations.

## Provenance

Only two provenance kinds are supported:

- `published` means the complete input-output pair appears in the publication,
  supplementary material, official author software, or another authoritative
  source. `source_location` records where it can be checked.
- `calculated` means no complete numerical example was published. A reviewer
  selected a physically meaningful input and calculated the expected output
  from the published computational contract. `rationale` explains that choice.

Both kinds require `inputs` and `expected`. Record-valued functions require
every output field. A calculated case is implementation verification, not
independent validation of the PTF's scientific accuracy and not evidence of
parity with an unpublished artifact.

```yaml
verification_cases:
  - id: representative_soil
    kind: calculated
    inputs:
      clay: 30.0
      silt: 20.0
      soil_organic_carbon: 1.0
    expected:
      field_capacity: 0.213
      permanent_wilting_point: 0.117
    rationale: >-
      Interior physically plausible mineral-soil composition using mass
      percentages for texture and soil organic carbon.
```

A published lookup row instead records its source:

```yaml
verification_cases:
  - id: published_table_case
    kind: published
    inputs: {soil_texture: sand}
    expected: {coefficient: 1.25}
    source_location: "Table 4, row 2"
    notes: Values transcribed from the primary source.
```

The absence of a published example, row-level dataset, supplement, or author
calculator does not block extraction or implementation when the formula,
coefficients, units, preprocessing, transforms, branches, applicability, and
other parts of the computational contract are complete. Missing or ambiguous
parts of that contract remain blockers. Rights and licensing are a separate
release gate.

## Numerical comparison

All Rust, Python, C, and C++ generated tests use the same centralized tolerant
comparison:

```text
rtol = 1e-5
atol = 1e-12
abs(actual - expected) <= atol + rtol * abs(expected)
```

This checks implementation correctness at roughly five significant digits. It
does not claim that a PTF has that physical accuracy: RMSE, R², uncertainty,
and applicability describe model quality, not floating-point agreement.

Published values may declare explicitly reported display precision per output:

```yaml
precision:
  water_content: {decimal_places: 2}
```

The comparator then adds half of the published rounding quantum to the normal
implementation tolerance. For significant digits, the quantum is derived from
the expected value's decimal magnitude. Specifications never contain `rtol` or
`atol`.

## Selecting calculated cases

Prefer a complete published predictor row without an output, then published
means or medians, then an interior point of the documented domain, and finally
an expert-selected typical soil. Inputs must use the stated units and scales,
stay away from boundaries, keep texture components and logarithm arguments
valid, and respect physical relations such as
`theta_1500 <= theta_33 <= theta_s`.

Piecewise functions, decision trees, and other multi-branch models need at
least one case for every material computational branch. Use published cases
where they exist and calculated cases for the remaining branches. Expected
calculated outputs are produced once with simple reference code and retained in
YAML; generation does not recalculate them.
