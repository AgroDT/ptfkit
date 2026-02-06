# ptfkit

<!-- github:start -->
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/AgroDT/ptfkit/deploy-pypi.yaml)
![Coveralls](https://img.shields.io/coverallsCoverage/github/AgroDT/ptfkit)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/ptfkit)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/ptfkit)
![PyPI - Version](https://img.shields.io/pypi/v/ptfkit)
![PyPI - Downloads](https://img.shields.io/pypi/dm/ptfkit?label=pypi%20downloads)
<!-- github:end -->

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

## Contributing

Contributions of all kinds are welcome! If you spot a bug, have a feature request, or want to share an idea, please open [an issue](https://github.com/AgroDT/ptfkit/issues).

For a complete guide on setting up the development environment, deployment workflow, and testing, please see the [`CONTRIBUTING.md`](./CONTRIBUTING.md) file.

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
