# Categorical inputs and typed lookups

Use this contract only when the source explicitly defines a finite categorical
input or a complete numeric table selected by such an input. Do not replace a
continuous predictor with representative categories, derive categories from
numeric inputs, or add aliases and normalization that the source does not define.

## Enum type and input binding

Declare the reusable categorical type in `$defs`. Its key is the canonical
PascalCase type name. The required `description` documents the type as a whole.
Each value has a lower-snake-case schema `name`, the exact public textual
`value`, and an optional source-supported `description`.

Bind the type to a function argument with `name` and `$ref`. Add the optional
binding `description` only when the argument's role needs information beyond
the enum type description. Categorical inputs do not have units, symbols, or
numeric domains.

```yaml
$defs:
  TextureClass:
    type: enum
    description: Source-defined texture class.
    values:
      - name: coarse
        value: "Coarse"
        description: Source-defined coarse class.
functions:
  - inputs:
      - name: texture
        description: Class used to select the published table row.
        $ref: "#/$defs/TextureClass"
```

## Lookup definition and implementation

A lookup definition references an enum input type and a record output type.
Its rows must cover every enum member exactly once. Row `key` values are enum
member schema names; every row `value` must contain exactly the output record's
field names.

Invoke the lookup as an ordered implementation variable. Its `key` names an
in-scope input of the lookup's enum type. Return a compatible record-valued
variable directly, or use `variable.field` in later formula expressions.
Verification-case categorical inputs also use enum member schema names.

```yaml
$defs:
  Parameters:
    type: record
    name: Parameters
    fields:
      - name: coefficient
        symbol: c
        unit: "1"
        domain: null
        description: Published coefficient.
  ParametersByTexture:
    type: lookup
    input:
      $ref: "#/$defs/TextureClass"
    output:
      $ref: "#/$defs/Parameters"
    values:
      - key: coarse
        value: {coefficient: 1.25}
functions:
  - implementation:
      variables:
        - name: parameters
          lookup:
            table:
              $ref: "#/$defs/ParametersByTexture"
            key: texture
    verification_cases:
      - id: coarse_table_row
        kind: published
        inputs: {texture: coarse}
        expected: {coefficient: 1.25}
        source_location: "Published parameter table, coarse row"
        notes: Direct published table row.
```

Treat a missing category, ambiguous label, incomplete row, unexplained numeric
value, or uncertain category-to-row mapping as a scientific blocker.
