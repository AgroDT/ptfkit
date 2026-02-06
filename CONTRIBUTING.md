# Development Guide

## Project-wide guidelines

* Use **only English** for all code, in-code documentation, commit messages, and
  generated docs.
* Manage **all** dependencies and virtual environments exclusively with `uv`
  commands (`uv add`, `uv remove`, `uv sync`, etc.). Do not mix package
  managers.
* Run every development tool (tests, linters, docs, pre-commit, etc.) via
  `uv run --no-sync <command>` to avoid implicit dependency resolution.

## Workflow and collaboration

### Branch naming

Follow the template `(<type>)/<short-description>` where `<type>` is one of
`feature`, `fix`, `refactor`, `docs`, `ci`, etc., and `<short-description>` is a
concise, kebab-cased summary.

### Commit messages

* Use Conventional Commits in English (https://www.conventionalcommits.org):
  `<type>(<scope>): <short summary>`.
* Use imperative mood ("add", "fix", "update"), keep the subject ≤ 50
  characters and wrap body lines at 72 (50/72 rule).
* Avoid emojis and keep scope names short.

### Documentation alignment

Keep `README.md`, `AGENTS.md`, MkDocs content, and configuration files
(`pyproject.toml`, `setup.py`, `Justfile`, etc.) synchronized with code changes.
Build docs locally with:

```sh
uv run --no-sync mkdocs serve
```

## Step 1: Install `uv`

`uv` manages virtual environments, package installation, and dependency locking.
Install it with the official [installer](https://docs.astral.sh/uv/getting-started/installation/)
or use your system's package manager if applicable.

Verify installation:

```sh
uv --version
```

## Step 2: Synchronizing the Environment

Set up the virtual environment & dependencies with `uv sync`. To evaluate coverage during
development, you need to build the module in a special mode, which is enabled by
the `CYTHON_TRACING` environment variable.

**Unix-like**

```sh
CYTHON_TRACING=1 uv sync --no-build-isolation --reinstall-package=ptfkit
```

**Windows**

```sh
$env:CYTHON_TRACING=1
uv sync --no-build-isolation --reinstall-package=ptfkit
```

## Step 3: Function Implementations in Cython

PTFs are implemented in the private module [`_core.py`](./src/ptfkit/_core.py).
Every function is annotated with Cython types and decorators:

* `@cython.ufunc` for NumPy vectorized operations.
* `@cython.cfunc` for cdef function creation.

Each function is named with the template

```
calc_ptf_<first-author><year>[_<extra>]_ufunc
```

where:

* `first-author` and `year` are the bibliographic reference
* `extra` is an optional modifier, for example for similar PTFs with different inputs

<details markdown>
<summary>Example</summary>

```python
@cython.ufunc
@cython.cfunc
def calc_ptf_aimrun2009_ufunc(
    clay: cython.double,
    bulk_density: cython.double,
    organic_matter: cython.double,
    gmd: cython.double,
) -> cython.double:
    k_sat_m_per_day = np.exp(
        -2.368
        + 3.846 * bulk_density
        + 0.091 * organic_matter
        - 6.203 * np.log(bulk_density)
        - 0.343 * np.log(organic_matter)
        - 2.334 * np.log(clay)
        - 0.411 * np.log(gmd)
    )
    return k_sat_m_per_day * M_PER_DAY_TO_M_PER_SEC
```

</details>

## Step 4: Writing Pure Python Wrappers

Each PTF implementation is wrapped in a separate public module

```
<first-author><year>.py
```

Wrappers provide:

* Clean API with pure Python annotations
* Overloads for scalar and vector data
* Docstrings for the entire module, each PTF, and data structures

Each function is named with the template

```
calc_ptf_<first-author><year>[_<extra>]
```

### Documentation standards

Follow these conventions for every public module:

1. **Module docstring** — describe the model, include APA-formatted reference,
   DOI, model identifiers (`h(θ)`, `k(h)`), territory, and dataset details
   when available.
2. **Result containers** — when returning multiple values, expose a `NamedTuple`
   (optionally generic) with an `Attributes` section documenting each field and
   its units.
3. **Wrapper functions** — provide overloads for scalar and vector inputs,
   include detailed `Args`/`Returns` sections, and dispatch directly to the
   matching `calc_ptf_<author><year>[_<extra>]_ufunc`.

Refer to existing modules for concrete examples if unsure.

### Examples

<details markdown>
<summary>Jabro, 1992</summary>

* Located in a separate module [`jabro1992.py`](./src/ptfkit/jabro1992.py)
* Dispatches calls to `calc_ptf_jabro1992_ufunc`
* Returns a single scalar/vector of saturated hydraulic conductivity (m/s)

**Example usage:**

```python
from ptfkit.jabro1992 import calc_ptf_jabro1992

k_sat = calc_ptf_jabro1992(silt=20, clay=30, bulk_density=1.3)
```

</details>

<details markdown>
<summary>Li et al., 2007</summary>

* Located in a separate module [`li2007.py`](./src/ptfkit/li2007.py)
* Dispatches calls to `calc_ptf_li2007_ufunc`
* Returns a NamedTuple with attributes:
  * **theta_s** - saturated water content (θs) (cm^3/cm^3)
  * **a_vg** - fitting parameter of the van Genuchten equation, inversely related to the air-entry
    suction (α) (cm^-1)
  * **n_vg** - fitting parameter of the van Genuchten equation, that characterizes the pore-size
    distribution (n)
  * **k_sat** - saturated hydraulic conductivity (Ks) (m/s)

**Example usage:**

```python
from ptfkit.li2007 import calc_ptf_li2007

import numpy as np

sand = np.array([15, 30])
silt = np.array([25, 50])
clay = np.array([35, 40])
bulk_density = np.array([1.2, 1.3])
soil_organic_matter = np.array([3.4, 3.2])
res = calc_ptf_li2007(sand=sand, silt=silt, clay=clay, bulk_density=bulk_density, soil_organic_matter=soil_organic_matter)
k_sat = res.k_sat
```

</details>

## Step 5: Writing Tests

**Rules:**

* Scope: test only public wrappers under `src/ptfkit/`.
* Inputs: cover both scalar and `ndarray` scenarios.
* Prefer `pytest.mark.parametrize` for multiple cases and fixtures for shared inputs.
* Test files: `tests/test_<first-author><year>.py` (one test file for each public module)
* Test functions: `test_calc_ptf_<first-author><year>[_<extra>]`
* Assertions: prefer plain `assert` where possible and
  `np.testing.assert_array_almost_equal` for floating-point values.
* Coverage: normal and edge cases (normal practice is to test
  function performance using values provided in a reference paper)

**Run tests:**

```sh
uv run --no-sync pytest
```

For full rebuilds with coverage tracing (required when touching `_core.py`):

```sh
rm src/ptfkit/_core.c
CYTHON_TRACING=1 uv sync --reinstall-package=ptfkit --no-build-isolation
uv run --no-sync pytest
```
