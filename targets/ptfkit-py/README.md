# ptfkit for Python

Python bindings for the pedotransfer functions implemented by ptfkit. Public
functions accept scalar values or NumPy-compatible arrays and delegate the
calculation to native NumPy ufuncs.

## Installation

Supported Python versions are declared in the package metadata.

```shell
pip install ptfkit
```

## Usage

```python
import numpy as np

from ptfkit.jabro1992 import calc_ptf_jabro1992

k_sat = calc_ptf_jabro1992(
    silt=np.array([20.0, 35.0]),
    clay=np.array([30.0, 18.0]),
    bulk_density=np.array([1.3, 1.45]),
)
```

Inputs are keyword-only. Array inputs follow NumPy broadcasting rules, and an
optional `out` array can be supplied for in-place calculation.

## Documentation

- [PTF source catalogue](https://agrodt.github.io/ptfkit/ptf-catalog/)
- [Python API](https://agrodt.github.io/ptfkit/reference/python/)
- [Repository](https://github.com/AgroDT/ptfkit)

The applicability of each PTF depends on the dataset, territory, measurement
methods, and variable ranges reported by its source publication. Review the
corresponding source page before using a function outside its calibration
conditions.
