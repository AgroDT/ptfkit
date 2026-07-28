# Python Bindings Contract

## Public API Defaults

- Public modules remain `crates/ptfkit-py/python/ptfkit/<author><year>.py`.
- Public functions remain keyword-only.
- Existing function names and result classes are preserved unless the spec says the function is new.
- Multi-output functions return project `NamedTuple` classes, not raw tuples.
- Scalar inputs return scalar-like values or `NamedTuple` of scalar-like values.
- Array inputs return `NDArray` values or `NamedTuple` of `NDArray` values.

## Vectorization

Bindings must support the spec contract:

- scalar inputs
- NumPy array inputs
- NumPy broadcasting when `broadcasting: numpy`
- `out` when `supports_out: true`

Prefer a shared Python wrapper layer for broadcasting and `out` unless the Rust
binding already provides a well-tested NumPy array path.

## Tests

Core formula golden tests live in the Rust core crate. Python tests are binding
and public API compatibility tests. For each public function, add or update
tests for:

- scalar wrapper calls
- ndarray calls
- mixed scalar and ndarray broadcasting
- `out` arrays for single-output functions
- `out` result containers for multi-output functions
- result class type, field names, and field order

## Documentation

Docstrings must be generated from the validated spec content:

- APA reference and DOI
- model identifiers when applicable
- territory and dataset when specified
- argument descriptions and units
- return descriptions and units

## Compatibility Blocks

Stop and ask before changing:

- public module names
- public function names
- keyword-only argument names
- result class names
- result field order
- output units
- scalar vs ndarray return behavior
