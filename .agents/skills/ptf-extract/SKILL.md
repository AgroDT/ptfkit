---
name: ptf-extract
description: Extract a user-supplied local paper into a validated draft PTF source specification. Use when a paper must become a YAML source file in specs/functions before human review; preserve missing or ambiguous scientific details as blockers and never generate targets.
---

# PTF Extract

## Invocation

Use `$ptf-extract <path-to-local-source-file>`.

Accept exactly one positional argument: a readable local regular file containing
the supplied paper or source material. Reject a missing argument, more than one
argument, a directory, a non-local path, or an unreadable file. Do not create or
change a specification when input validation fails; report `Blocked` and the
input error.

## Procedure

1. Read the supplied local paper, `specs/schema/ptf-spec.schema.json`, and
   `references/extraction-quality-gate.md`.
2. Extract only facts explicitly supported by the paper. Write its standalone
   YAML directly to `specs/functions/<apa_article_key>.yaml`, following
   `references/spec-template.yaml`.
3. For particle-size or texture-related inputs, examine whether sand, silt, and
   clay are mass or volume fractions; whether percentages use the fine-earth
   fraction; the particle-size boundaries and their units; any named
   particle-size or texture-classification system; whether the fractions should
   sum to 100; and whether the source directly uses a categorical texture-class
   predictor.
4. For functions with numeric particle-size inputs that could potentially be
   supplied through the common USDA texture adapter, record
   `input_adapters.usda_texture` as:
   - `supported` only when the source provides explicit compatibility evidence;
   - `unsupported` only when the source provides explicit incompatibility
     evidence;
   - `unknown` when the relevant definitions are absent or ambiguous.

   Require non-empty evidence for every recorded status. Do not add this adapter
   metadata merely because input parameters are named `sand`, `silt`, or
   `clay`. If the source directly uses a categorical texture-class predictor,
   preserve that predictor as part of the published model rather than replacing
   it with representative numeric fractions.

   An `unknown` adapter status blocks only a USDA compatibility claim, not an
   otherwise complete PTF specification.
5. Record missing or ambiguous scientific information required to interpret or
   implement the published PTF as explicit blockers and set affected functions
   to `blocked`; otherwise set reviewed, complete functions to
   `ready-for-implementation`. Do not treat information needed only to establish
   USDA adapter compatibility as a PTF implementation blocker.
6. Run `cargo run --manifest-path codegen/Cargo.toml -- validate` and fix
   validation errors before finishing. Validation never justifies inferred
   science.

## Output

Return `Ready for user review` with the exact YAML path, or `Blocked` with the
exact YAML path and explicit blockers.

## Hard rules

- Do not set `implemented`, run target generation, or edit generated files.
- Do not invent formulas, units, metadata, golden values, applicability, or
  API details. Keep uncertainty explicit in the YAML.
- Give every `type: record` output a PascalCase `name`, whether it is inline or
  declared in `$defs`. It names generated structures and classes; `$defs` keys
  only resolve local `$ref` targets.
- Use `generation.public_python: manual` only when the public wrapper cannot
  follow the standard generated API; it never opts the native NumPy ufunc out
  of generation.
- Never infer USDA compatibility from parameter names alone.
- Never replace measured or source-defined particle-size fractions with
  representative USDA fractions during extraction.
- Never create a golden test by converting a texture-class label to
  representative sand, silt, and clay values.
- If the publication directly defines a categorical texture-class predictor,
  preserve it rather than rewriting the published model as a numeric
  sand-silt-clay model.
- Never copy the common USDA representative-value table into an individual PTF
  specification.
- `ptf-extract` records compatibility evidence; it does not perform user-data
  conversion.
