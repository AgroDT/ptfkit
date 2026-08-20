# Code Generator Architecture

`ptfkit-codegen` validates the YAML specifications, compiles their formulas
into a shared semantic representation, and renders every committed target.
The generated files, after their target formatter runs, are the compatibility
contract; internal generator APIs are not.

## Pipeline

1. `specs` loads source specifications and `validate` checks their contracts.
2. `targets::compile` resolves formulas and golden cases into
   `CompiledFunction` values.
3. Target renderers consume those values and return `GeneratedFile` artifacts.
   `documentation` provides borrowed source/function facts to every renderer;
   it deliberately contains no target markup.
4. `targets::run` assigns artifacts to declarative `Layout` values.
5. `targets::write` stages files, runs each layout's formatter, atomically
   replaces targets, and removes obsolete marker-owned files.

`check-generated` snapshots all marker-owned files, runs the same pipeline,
and fails if the generated tree changes.

## Extension points

Add target-local syntax and escaping beside its renderer. Use
`render::Writer` only where indentation-aware text composition is natural;
Rust remains token-based with `proc_macro2` and `quote`. Add a `Layout` only
when a new output group needs a distinct root, cleanup root, marker, or
formatter. Do not introduce a cross-language syntax AST or let renderers own
filesystem, staging, formatting, or cleanup policy.
