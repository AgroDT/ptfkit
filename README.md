# ptfkit

[![CI](https://img.shields.io/github/actions/workflow/status/AgroDT/ptfkit/pr.yaml?branch=main)](https://github.com/AgroDT/ptfkit/actions/workflows/pr.yaml)
[![Documentation](https://img.shields.io/github/actions/workflow/status/AgroDT/ptfkit/deploy-docs.yaml?label=docs)](https://agrodt.github.io/ptfkit/)
[![PyPI version](https://img.shields.io/pypi/v/ptfkit)](https://pypi.org/project/ptfkit/)
[![Python versions](https://img.shields.io/pypi/pyversions/ptfkit)](https://pypi.org/project/ptfkit/)
[![crates.io version](https://img.shields.io/crates/v/ptfkit)](https://crates.io/crates/ptfkit)
[![License](https://img.shields.io/github/license/AgroDT/ptfkit)](https://github.com/AgroDT/ptfkit/blob/main/LICENSE)

ptfkit is a specification-driven collection of pedotransfer functions (PTFs)
for estimating soil hydraulic properties.

A PTF is an empirical model that predicts a soil property from measurements
that are generally easier, faster, or less expensive to obtain directly. Common
inputs include particle-size fractions, bulk density, and organic matter
content; predicted properties include soil water-retention characteristics and
hydraulic conductivity.

ptfkit makes selected PTFs from soil-science publications available through
consistent interfaces in several programming languages. It is intended for
soil scientists, hydrologists, environmental modellers, agronomists, students,
and software developers who need traceable implementations of published soil
models.

The [documentation](https://agrodt.github.io/ptfkit/) provides a catalogue of
source publications and API references for the supported targets.

## Specification-driven development

Every PTF in ptfkit starts with its original scientific publication. The
equations and the information needed to interpret them are transcribed into a
reviewed YAML specification under [`specs/functions`](./specs/functions/).
Each specification records the source citation, variable definitions, units,
calibration scope, equations, numerical examples, notes, and warnings.

The specifications are the target-independent source of truth. The generator
under [`codegen`](./codegen/) validates them, compiles their equations into a
shared semantic model, and generates the language implementations, tests, PTF
catalogue, and API reference pages. Generated artifacts are committed to the
repository, but changes to a PTF are made in its specification or in the
generator rather than in generated files.

This workflow keeps the scientific description, public interfaces, numerical
tests, and documentation aligned across targets. A source specification may
also document a PTF that is not implemented yet; its status in the
[PTF catalogue](https://agrodt.github.io/ptfkit/ptf-catalog/) indicates whether
it is available for generation and use.

See the
[PTF source specification guide](https://agrodt.github.io/ptfkit/ptf-catalog/)
for the scientific and structural contract represented by the YAML files.

## Targets

| Target | Interface and distribution | Documentation |
| --- | --- | --- |
| [Python](./targets/ptfkit-py/) | Scalar and NumPy array inputs backed by native ufuncs; distributed on [PyPI](https://pypi.org/project/ptfkit/) | [Python API](https://agrodt.github.io/ptfkit/reference/python/) |
| [Rust](./targets/ptfkit-rs/) | Scalar functions grouped by source publication; distributed on [crates.io](https://crates.io/crates/ptfkit) | [Rust API](https://docs.rs/ptfkit/) |
| [C](./targets/ptfkit-native/) | Header-only C11 functions provided as a CMake package and release archive | [C API](https://agrodt.github.io/ptfkit/reference/c/) |
| [C++](./targets/ptfkit-native/) | Optional C++20 modules provided by the native CMake package | [C++ API](https://agrodt.github.io/ptfkit/reference/cpp/) |

Installation and usage instructions are maintained in each target's linked
README.

## Scope and limitations

Pedotransfer functions are empirical models fitted to particular datasets,
territories, measurement methods, and variable ranges. Their accuracy and
applicability outside those calibration conditions are not guaranteed. A PTF
that is appropriate for one soil population or study design may be unsuitable
for another.

ptfkit reproduces the reviewed equations, declared unit conversions, and
documented numerical behavior. It does not select a PTF for a particular use
case, assess the quality of input measurements, or replace expert scientific
judgement. Declared input domains describe the source or mathematical contract
and do not necessarily imply runtime range validation.

Before using a function, consult its catalogue page and original publication
for the citation, calibration dataset, input definitions, units, domains,
notes, and warnings. Also verify that the function is marked as implemented and
is present in the API reference for the intended target.

## Contributing and development

Contributions may include reporting an implementation error, requesting a PTF,
improving a specification, extending the generator, or working on a language
target. Use [GitHub Issues](https://github.com/AgroDT/ptfkit/issues) to report a
problem or propose a change.

ptfkit has strict ownership and validation rules for specifications and
generated files. Before making a contribution, read the
[development guide](https://agrodt.github.io/ptfkit/contributing/development/)
for repository setup, dependency management, the PTF extraction and generation
workflow, validation commands, documentation builds, and commit conventions.
The [PTF source specification guide](https://agrodt.github.io/ptfkit/ptf-catalog/)
describes the scientific information and cross-target contracts that each
specification must preserve.

## Citation

### APA

```text
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
