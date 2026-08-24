# Input adapter registry

Input adapters are specification-owned categorical-to-numeric-record contracts.
Each `specs/adapters/<id>.yaml` file has a paired schema and defines a stable
category order, numeric output metadata and domains, representative mappings,
validation constraints, and provenance. The registry is loaded and validated
before PTF source specifications. Adapter IDs and registered input types must be
globally unique.

PTF inputs are numeric by default. Omitting `type` is equivalent to
`type: number`. The registered `usda_texture_class` type has these exact values,
in stable code order:

1. `sand`
2. `loamy sand`
3. `sandy loam`
4. `loam`
5. `silt loam`
6. `silt`
7. `sandy clay loam`
8. `clay loam`
9. `silty clay loam`
10. `sandy clay`
11. `silty clay`
12. `clay`

The registry values come from the USDA-NRCS Soil Texture Calculator workbook.
They are representative percent-by-mass fine-earth fractions, not laboratory
measurements. Replacing measured fractions with representative values adds
uncertainty and is scientifically valid only when the PTF source supports the
same particle-size definitions and categorical transformation.

## Derived-input bindings

A distinct adapter-backed PTF variant declares its public categorical input and
an explicit binding:

```yaml
inputs:
  - name: texture_class
    type: usda_texture_class
    symbol: null
    unit: USDA texture class
    domain: null
    description: Basic USDA fine-earth texture class.
derived_inputs:
  - adapter: usda_texture
    input: texture_class
    evidence: >-
      Source-backed explanation establishing compatible particle-size
      definitions and supporting the categorical-to-fractions transformation.
    components:
      sand: sand
      silt: silt
      clay: clay
```

Component keys name adapter outputs; values name numeric symbols used by the
formula. A binding may select any non-empty subset. No component is inferred
from formula or parameter names. The semantic IR retains the resolved adapter,
source public input, component, derived symbol, and evidence. Its numeric scope
contains numeric public inputs, explicit derived inputs, and previously
evaluated implementation variables; categorical public inputs are excluded.

Scientific review must confirm the binding evidence from the source itself.
Country, dataset location, common practice, parameter names, another paper, or
another software implementation are insufficient. Missing adapter evidence does
not block the original numeric PTF; it means no adapter-backed variant is added.

## Target lowering

- C uses a `uint8_t`-compatible type, stable constants, a fractions structure,
  and an invalid-code-safe generated conversion in an adapter header.
- C++ uses `enum class UsdaTexture : std::uint8_t`, a fractions structure, and
  a generated adapter module.
- Rust uses an idiomatic `UsdaTexture` enum without `repr`, plus generated
  `From<UsdaTexture> for UsdaTextureFractions` mapping.
- CPython/NumPy ufuncs accept `NPY_UINT8` category codes, map them inside the
  loop, bind only requested scalar components, and preserve broadcasting and
  `out` behavior without materializing fraction arrays.

Generated PTF APIs expose only public inputs. Raw string parsing is outside the
generated PTF cores because it is target-specific convenience behavior rather
than scientific adapter data.

## Python preparation

Use the handwritten direct-extension preparation layer once, then reuse the
sealed prepared value:

```python
from ptfkit.cosby1984 import calc_ptf_cosby1984_univariate_usda_texture
from ptfkit.texture import prepare_usda_texture

texture = prepare_usda_texture(["loam", "sand"])
result = calc_ptf_cosby1984_univariate_usda_texture(texture_class=texture)
```

`UsdaTextureClass` is an exact `Literal[...]` union. Preparation accepts one
exact Python Unicode string or a shape-preserving string array/sequence and
returns protected, read-only `uint8` codes inside `PreparedUsdaTexture`. Wrong
case, altered whitespace, hyphens, underscores, aliases, abbreviations,
subclasses, fragment modifiers, and fuzzy matches raise `ValueError`; array
errors identify the invalid value and index. Public categorical PTF wrappers
reject raw strings and arbitrary `uint8` arrays.

Rust keeps its exact `FromStr` parser handwritten in a separate module. Neither
Python nor Rust parsing is generated from the adapter specification.

The Cosby et al. (1984) adapter-backed variant is additive. The original numeric
API remains available for measured sand, silt, and clay fractions. The variant's
binding cites page 684, where the authors report assigning representative sand,
silt, and clay percentages from the USDA texture triangle because measured
particle-size distributions were unavailable.
