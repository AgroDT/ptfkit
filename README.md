# ptfkit

## Overview

ptfkit helps researchers quickly estimate key soil water characteristics from
basic soil data. It is reliable, easy-to-use, and consistent across studies and
scales, streamlining analysis and supporting scientific workflows.

## About the Package

ptfkit is a library of **pedotransfer functions (PTFs)** for estimating key soil
hydraulic properties, such as water retention and hydraulic conductivity curves,
from basic soil parameters.

The library is built on publicly available scientific articles in soil science,
with the goal of creating a comprehensive resource that includes as many PTFs as
possible for soils worldwide. This fosters knowledge sharing and supports
international scientific collaboration.

Each module contains one or more PTFs and references the original scientific publication.
PTFs calculate hydrological parameters from easily measurable soil properties, such as:

* Soil texture (sand, silt, clay)
* Bulk density
* Organic matter content

Using PTFs is advantageous because measuring base soil properties is simpler and cheaper
than directly determining hydraulic function parameters. The library is intended for:

* Soil scientists conducting research
* Students for educational purposes
* Farmers applying precision agriculture techniques

If you discover any errors in PTF implementations or would like your PTF
to be added to the library, please create a new issue on GitHub.

## Core Features

1. 🔗 **Pedotransfer Function API** - Compute soil hydraulic properties across studies.
2. 🧮 **Vectorized Input Support** - Accept NumPy arrays for batch processing.
3. 🗂️ **Model-Specific Output Structures** - NamedTuple outputs for clarity.
4. 🛠 **Extensibility for New Models** - Easily add new PTFs.
5. ⚡ **Performance Optimization via Cython** - Fast computations on large datasets.
6. 📦 **Packaging & Distribution** - Precompiled packages for easy installation via pip.
7. 🚧 **Strong typing** - Type annotations ready for static analysis and linting.
8. 🎓 **Well documented** - Docstrings for all implemented PTFs with proper references.

## Installation

**Prerequisites:**

- Python >= 3.10

We strongly recommend to install ptfkit into a virtual environment

**Linux (Debian-based):**

Install Python

```sh
sudo apt install python3 python3-venv
```

Create virtual environment and activate it

```sh
python -m venv ptfkit-venv
source ptfkit-venv/bin/activate
```

**Windows**

Install Python with the official [installer](https://www.python.org/downloads/)
or use [winget](https://learn.microsoft.com/en-us/windows/package-manager/winget/)

```ps1
winget install --id Python.Python.3 --source winget
```

Create virtual environment and activate it

```ps1
python -m venv ptfkit-venv
.\ptfkit-venv\Scripts\activate
```

### PyPi

Install our precompiled binary wheels

```sh
pip install ptfkit
```

### Build from Source

**Extra prerequisites:**

- Python development files
- C compiler
- git

**Linux (Debian-based):**

```sh
sudo apt install gcc git python3-dev
```

**Windows:**

1. Download [Build Tools for Visual Studio](https://visualstudio.microsoft.com/downloads/)
2. Select **Desktop development with C++**
3. Install git

```ps1
winget install --id Git.Git -e --source winget
```

**Install ptfkit from git:**

```sh
pip install 'git+https://github.com/AgroDT/ptfkit.git'
```

## Development Guide

### Step 1: Install `uv`

`uv` manages virtual environments, package installation, and dependency locking.
Install it with the official [installer](https://docs.astral.sh/uv/getting-started/installation/)
or use your system's package manager if applicable.

Verify installation:

```sh
uv --version
```

### Step 2: Synchronizing the Environment

Setup virtual environment & dependencies with `uv sync`. To evaluate coverage during
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

### Step 3: Function Implementations in Cython

PTF are implemented in a private module [`_core.py`](./src/ptfkit/_core.py).
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

### Step 4: Writing Pure Python Wrappers

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

#### Examples

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

### Step 5: Writing Tests

**Rules:**

* Test files: `tests/test_<first-author><year>.py` (one test file for each public module)
* Test functions: `test_calc_ptf_<first-author><year>[_<extra>]`
* Assertions: simple `assert`
* Coverage: normal and edge cases (normal practice is to test
  function performance using values provided in a reference paper)

**Run tests:**

```sh
uv run pytest
```

## Contributing

* [Report Issues](https://github.com/AgroDT/ptfkit/issues)

## Citation

### APA

```
AgroDT lab (2025). ptfkit repository [Computer software]. https://github.com/AgroDT/ptfkit
```

### BibTeX

```bibtex
@misc{ptfkit,
  author       = {AgroDT lab},
  title        = {ptfkit repository},
  year         = {2025},
  howpublished = {\url{https://github.com/AgroDT/ptfkit}},
  url          = {https://github.com/AgroDT/ptfkit}
}
```
