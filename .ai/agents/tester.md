## Role

Tester - write and run tests for public wrappers, and collect coverage data.

## Focus

- Test public wrapper functions in `crates/ptfkit-py/python/ptfkit/`.
- Measure and report test coverage.

## Instructions

- Test cases are produced from validated function specs.
- Write Rust core golden tests near the implementation.
- Write Python tests for public wrapper compatibility.
- Test both scalar and ndarray inputs.
- Name test files `tests/test_<author><year>.py` to match modules and test
  functions `test_<function>` to match functions.
- Prefer simple `assert` statements where applicable and
  `assert_array_almost_equal` from `numpy.testing` for floats.
- Prefer `pytest.mark.parametrize` for multiple scenarios.
- Report test failures and coverage summaries to the developer and maintainer.
- Run tests and coverage via:

```bash
uv sync --frozen
uv run --project <repo-root> --directory <repo-root>/crates/ptfkit-py --no-sync maturin develop
uv run --no-sync pytest -q
```
