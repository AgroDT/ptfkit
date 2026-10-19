# ptfkit-eval

`ptfkit-eval` provides reproducible external evaluation protocols for the
pedotransfer functions published by `ptfkit`.

The package is under active development. Its first implemented contract covers
single-function and range-gated composite water-retention curve candidates.
`load_evaluation_plan()` validates JSON or YAML plans against the packaged
schema and resolves their function, output, unit, basis, and model-adapter
references against the installed `ptfkit` manifest before execution.
