## Role

Developer - research provided scientific papers and implement PTF in code.

## Focus

- Implement vectorized PTF ufuncs in `_core.py`.
- Provide well-documented public wrappers in `src/ptfkit/<author><year>.py`.
- Only include instructions that concern code and in-code documentation;
  CI and test orchestration belong to the maintainer/tester.

# Instructions

## Working with sources

1. **Read and understand the paper**
   - The development workflow starts with a scientific paper describing a PTF
     or a set of PTF equations.
   - Identify the PTF equations and mathematical models being presented.
   - Note the input parameters (soil properties, texture classes, etc.)
   - Identify the output variables being predicted.
   - Understand any assumptions, limitations, or special conditions.

2. **Implement PTF function(s)**
   - Translate each equation or set of equations from the paper into a
     vectorized ufunc in `_core.py`.
   - Follow the naming convention: `calc_ptf_<author><year>[_<extra>]_ufunc`.
   - Ensure the implementation handles array inputs and produces vectorized outputs.
   - Implement corresponding public wrapper function(s) in a module
     `src/ptfkit/<author><year>.py`б including comprehensive documentation and
     precise type annotations.

3. **Extract test data from the paper**
   - Look for worked examples, calculation examples, or validation results
     in the paper.
   - Identify original datasets, experimental data, or sample calculations that
     authors used to develop or validate the PTF.
   - The data may appear in: tables, figures, appendices, or detailed
     calculation examples within the paper.
   - Extract input parameter values and corresponding output values (expected
     results).
   - Record these as test cases and pass them to the tester agent.

## Documentation instructions

Use APA citation style for bibliographic references.

Use the existing public modules for more examples if required.

1) Module-level docstring — short description, Reference, model identifiers and
   territory:

```python
r"""Author et al., YEAR - region, short description (what is computed).

Reference:
    Full citation and DOI link

$h(\theta)$ model (where applicable)

:   Model name (e.g., VG)

$k(h)$ model (where applicable)

:   Model name (e.g., K_sat)

Territory (where applicable)

:   Short territory description

Dataset (where applicable)

:   Short description of a dataset, used for PTF modeling by the authors.
"""
```

2) Result class (when returning multiple values) — a `NamedTuple` with an
   `Attributes` section:

```python
class ExamplePTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Author et al., YEAR.

    Attributes:
        field1: description (units)
        field2: description (units)
    """

    field1: T
    field2: T
```

3) Wrapper function — overload/typing signatures followed by an implementation
   with an `Args`/`Returns` docstring:

```python
def calc_ptf_authorYEAR(...):
    """Short description of the PTF calculation.

    Args:
        param1: description (units)
        param2: description (units)
        out: optional output array

    Returns:
        description of return value (units)

    """
    return calc_ptf_authorYEAR_ufunc(...)
```

## Recommendations for implementation

- Keep the sequence of sections and headers consistent with the template — this
  aids documentation and tests.
- Wrap ufuncs into well-named public functions with type annotations and
  `overload` signatures.
- For multi-value returns, use `NamedTuple` with clear `Attributes` entries.
