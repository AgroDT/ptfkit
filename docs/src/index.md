---
title: Pedotransfer functions for soil hydraulic properties
description: ptfkit is a specification-driven collection of published pedotransfer functions for estimating soil hydraulic properties in Python, Rust, C, and C++.
---

# Pedotransfer functions for soil hydraulic properties

**ptfkit** is a specification-driven collection of published pedotransfer
functions (PTFs) for estimating soil hydraulic properties. It provides
traceable implementations through consistent interfaces for Python, Rust, C,
and C++.

Pedotransfer functions estimate soil properties from measurements that are
generally easier, faster, or less expensive to obtain directly. Common inputs
include particle-size fractions, bulk density, and organic matter content;
predicted properties in ptfkit include soil water-retention characteristics and
hydraulic conductivity.

## Explore the PTF collection

The [PTF catalog](ptf-catalog/index.md) connects each implementation to its
scientific source. Source pages document the publication, calibration scope,
territory, inputs, outputs, units, equations, status, numerical examples,
limitations, and warnings retained by ptfkit.

The [PTF sources](ptf-catalog/sources/index.md) page provides an index of the
published pedotransfer-function sources currently represented in the catalog.
Use it to locate implementations by source publication and review their
applicability before use.

## Programming-language targets

ptfkit exposes generated implementations for several programming languages:

| Target | Interface | Documentation |
| --- | --- | --- |
| Python | Scalar and NumPy array inputs backed by native ufuncs | [Python target](targets/python.md) · [Python API](reference/python/index.md) |
| Rust | Scalar functions grouped by source publication | [Rust target](targets/rust.md) · [docs.rs](https://docs.rs/ptfkit/) |
| C | Header-only C11 functions | [C and C++ target](targets/native.md) · [C API](reference/c/index.md) |
| C++ | Optional C++23 modules | [C and C++ target](targets/native.md) · [C++ API](reference/cpp/index.md) |

Packages are distributed through [PyPI](https://pypi.org/project/ptfkit/) and
[crates.io](https://crates.io/crates/ptfkit); C and C++ releases are available
from the [GitHub repository](https://github.com/AgroDT/ptfkit/releases).

## Scientific traceability

Every PTF starts from its original scientific publication. Equations, variable
definitions, units, calibration scope, numerical examples, notes, and warnings
are transcribed into reviewed YAML specifications. Those specifications are the
target-independent source of truth from which ptfkit generates language
implementations, tests, the PTF catalog, and API reference pages.

This design keeps the scientific description and executable implementations
aligned across programming-language targets. It also makes the source and
applicability limits of each pedotransfer function explicit rather than treating
PTFs as interchangeable empirical formulas.

## Scope and limitations

Pedotransfer functions are empirical models fitted to particular datasets,
territories, measurement methods, and variable ranges. Their accuracy and
applicability outside those calibration conditions are not guaranteed.

Before using a function, review its catalog page and original publication for
the calibration dataset, input definitions, units, domains, notes, warnings,
and implementation status.

## Project resources

- [PTF catalog](ptf-catalog/index.md)
- [PTF sources](ptf-catalog/sources/index.md)
- [GitHub repository](https://github.com/AgroDT/ptfkit)
- [Development guide](contributing/development.md)
- [How to cite ptfkit](https://github.com/AgroDT/ptfkit/blob/main/CITATION.cff)
