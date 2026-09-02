# Code Generator Architecture

`ptfkit-codegen` validates the YAML specifications, compiles their formulas
into a shared semantic representation, and renders every committed target.
The generated files, after their target formatter runs, are the compatibility
contract; internal generator APIs are not.

## Pipeline

1. `specs` loads source specifications and `validate` checks their contracts.
2. `compile` resolves formulas and golden cases into `CompiledFunction` values.
   `verification` evaluates calculated cases from the validated IR at 256-bit
   precision and centrally derives exact or interval acceptance criteria.
3. `documentation` provides borrowed source/function facts without target
   markup. `render` contains shared text, Markdown, and C-family expression
   rendering support.
4. `targets::{catalog, reference, native, python, rust}` render concrete
   generated products and return `GeneratedFile` artifacts.
5. `output` owns layouts, staging, formatter execution, cleanup, snapshots,
   and atomic replacement.

`check-generated` snapshots all marker-owned files, runs the same pipeline,
and fails if the generated tree changes.

## Extension points

Add target-local syntax and escaping beside its renderer. Reusable C-family
expression precedence belongs in `render::c`; reusable Markdown file/block
composition belongs in `render::markdown`. Use `render::Writer` only where
indentation-aware text composition is natural; Rust remains token-based with
`proc_macro2` and `quote`. Add an `output::Layout` only when a new output group
needs a distinct root, cleanup root, marker, or formatter. Do not introduce a
cross-language syntax AST or let renderers own filesystem, staging, formatting,
or cleanup policy.

## Corpus report

Generate a human-readable summary of the current specification corpus from the
repository root:

```sh
mise run corpus-report
```

Use `--format json` for a deterministic, machine-readable report suitable for
CI checks and publication tables:

```sh
mise run corpus-report --format json
```

The command uses the normal specification loader, schema and semantic
validation, and compilation path. It counts every schema-valid function,
including `draft` and `blocked` functions. Verification coverage counts declared
`golden_tests` and `edge_cases`; it does not describe external predictive
validation on soil datasets, and a declared edge case is not necessarily an
executable test. Golden provenance counts distinguish source-based evidence
from calculated references derived from the same semantic IR.

The JSON document has stable top-level `sources`, `functions`, `verification`,
`inputs`, `outputs`, `scope`, and `blocked_functions` sections. Category tables
are emitted as sorted arrays with explicit counts and percentages. Inputs are
resolved by the specification loader and reported separately as `numeric` or
`categorical`.

The schema does not have an explicit publication-year field. The report accepts
the final four characters of the APA-style source slug only when all four are
ASCII digits and lists unresolved source slugs separately. It reports the
existing `prediction_target`, `h_theta`, and `k_h` strings without attempting
free-text scientific-property classification. Blocker evidence is retained from
function documentation and source `scientific_notes`, but the current schema
does not provide structured blocker categories.
