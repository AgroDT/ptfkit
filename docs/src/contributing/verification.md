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

Every scalar output and record field declares a stable physical or model
`quantity`. The repository-level `specs/quantities.yaml` registry assigns a
reviewed project-default tolerance to each exact quantity-unit combination.
An unknown quantity or unit is a validation error; there is no global
scientific fallback and no implicit unit conversion.

A publication may support a more appropriate function-output tolerance. Such
an override is declared once on the function, not in an individual case:

```yaml
verification_tolerances:
  field_capacity:
    absolute: 0.005
    relative: 0.01
    source_location: "Table 5"
```

The cited override replaces the registry default. Model-performance metrics
such as RMSE, MAE, bias, or R² must not be converted mechanically into
implementation tolerances.

All Rust, Python, C, and C++ generated tests resolve the same comparison:

```text
scientific_tolerance = max(absolute, relative * abs(expected))
abs(actual - expected) <= max(scientific_tolerance, floating_point_guard)
```

`absolute` is mandatory and expressed in the output unit; `relative` is
optional and dimensionless. The centrally generated floating-point guard only
absorbs insignificant implementation and math-library variation and is much
smaller than normal scientific tolerances. Failure messages report actual and
expected values, their difference, the resolved tolerance, quantity, unit, and
whether the policy came from the registry or a cited source override.

Registry values are transparent ptfkit verification policy. They are not
universal metrological claims, measurement uncertainty, or evidence of PTF
predictive accuracy. Stored expected values may retain extra digits for stable
regeneration without implying that every digit is scientifically significant.

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
