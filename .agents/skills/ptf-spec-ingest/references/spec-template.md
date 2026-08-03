# PTF Source Specification Template

Store source-oriented specifications at `specs/functions/<source-key>.md`. One
file may describe one or more functions from the same publication. Do not make a
second file merely because that publication provides another function.

Every specification begins with YAML front matter conforming to
[`specs/schema/ptf-spec-v1.schema.json`](../../../specs/schema/ptf-spec-v1.schema.json),
followed by Markdown for formulas and scientific explanation.

```markdown
---
schema_version: 1
source:
  key: author_year
  summary: Author et al. (YEAR), short territory.
  citation_apa: Author, A. (YEAR). Publication title. Journal, volume, pages.
  doi: {identifier: 10.1234/example, url: https://doi.org/10.1234/example}
scope:
  territory: Region
  dataset: Shared source dataset
functions:
  - name: calc_ptf_authoryear_property
    status: draft
    public_api:
      name: calc_ptf_authoryear_property
      result_class: null
      summary: Estimate a soil hydraulic property.
    scope:
      prediction_target: Soil hydraulic property.
      models:
        h_theta: null
        k_h: null
    inputs:
      - name: clay
        symbol: C
        unit: "%"
        domain: "0 <= value <= 100"
        description: Clay content.
    outputs:
      - name: property
        symbol: null
        unit: dimensionless
        domain: null
        description: Estimated soil hydraulic property.
    golden_tests:
      - id: scalar_001
        inputs: {clay: 58.0}
        expected: {property: 1.23e-6}
        rtol: 1.0e-10
        atol: 1.0e-12
        notes: Derived from the publication equation.
    edge_cases: []
    documentation:
      notes: []
      warnings: []
---

# Author et al. (YEAR)

## `calc_ptf_authoryear_property`

### Formula

```text
property = ...
```

### Constants

... constants, source-table details, unit conversions, and derivations ...

### Numeric policy

... NaN, domain, rounding, and precision behaviour ...

### Golden-test rationale

... source provenance, representativeness, or scientific interpretation of the
structured golden cases above ...
```

## Authoring rules

1. Create or locate the source-oriented file first. Reuse it when adding a
   function from the same publication.
2. Add a hand-authored source summary of at most 100 characters, the complete
   citation, the DOI identifier and URL (or `null`), complete source territory,
   and shared dataset only once at the top level. Do not derive the summary or
   DOI URL during generation.
3. Add one complete, ordered entry to `functions` for each public function.
   Inputs and outputs are deliberately local to each function.
4. Give every function exactly one matching `## \`calc_ptf_...\`` Markdown
   section in the same order as the YAML list.
5. Keep concise public documentation, golden cases, and edge cases in YAML.
   Keep formulas, constants, and scientific reasoning in Markdown.
6. Use `null` for absent structured values; never write `not specified`,
   `none`, or `not applicable` in place of `null`. Use `dimensionless` when it
   is a real unit.
7. `result_class` is `null` for exactly one output and is required for multiple
   outputs. Do not add redundant result-field or return-kind metadata.
8. Declare `functions[].scope.territory` only when that function has a narrower
   or different territory. It is independent of top-level `scope.territory`;
   do not inherit, override, or combine the two fields. Do not use YAML anchors
   or merge keys.
9. Package-wide scalar, NumPy, broadcasting, `out`, precision, and keyword-only
   contracts are documented centrally; do not repeat them in each source spec.
10. The spec filename and `source.key` identify its sole public Python module
    as `ptfkit.<source.key>`. Omit top-level `python_generation` for generated
    modules; use `python_generation: manual` only for an intentional manual
    module.
