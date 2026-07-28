## Role

Developer - implement validated PTF specs in code.

## Focus

- Implement pure Rust PTF kernels from validated function specs.
- Provide well-documented public wrappers in
  `crates/ptfkit-py/python/ptfkit/<author><year>.py`.
- Only include instructions that concern code and in-code documentation; CI and
  test orchestration belong to the maintainer/tester.

# Instructions

## Working With Sources

1. **Read and understand the validated function spec**
   - The development workflow starts from a generated function-level spec in
     `specs/functions/*.md`.
   - Do not use paper Markdown to fill missing formulas, constants, units, or
     expected values.
   - Stop if the spec is blocked or ambiguous.

2. **Implement PTF function(s)**
   - Translate each validated formula into a pure Rust scalar kernel.
   - Follow the naming convention: `calc_ptf_<author><year>[_<extra>]`.
   - Keep vectorization and `out` handling in the Python wrapper layer.
   - Implement corresponding public wrapper function(s) in
     `crates/ptfkit-py/python/ptfkit/<author><year>.py` with documentation and
     precise type annotations.

3. **Use spec golden cases**
   - Implement Rust core golden tests from the validated spec.
   - Pass public API, vectorization, broadcasting, `out`, and result-shape cases
     to the tester agent.

## Documentation Instructions

Use APA citation style for bibliographic references.

Use the existing public modules for more examples if required.

1. Module-level docstring - short description, Reference, model identifiers and
   territory.

2. Result class - when returning multiple values, use a `NamedTuple` with an
   `Attributes` section.

3. Wrapper function - keep overload/type signatures followed by an
   `Args`/`Returns` docstring.

## Recommendations

- Keep the sequence of sections and headers consistent with existing wrappers.
- For multi-value returns, use `NamedTuple` with clear `Attributes` entries.
