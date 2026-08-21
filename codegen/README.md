# Code Generator Architecture

`ptfkit-codegen` validates the YAML specifications, compiles their formulas
into a shared semantic representation, and renders every committed target.
The generated files, after their target formatter runs, are the compatibility
contract; internal generator APIs are not.

## Pipeline

1. `specs` loads source specifications and `validate` checks their contracts.
2. `compile` resolves formulas and golden cases into `CompiledFunction` values.
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
