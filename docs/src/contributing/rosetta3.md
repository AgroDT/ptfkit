---
title: Rosetta3 and external models
---

# Rosetta3 and external models

Rosetta3 is available in the public Rust, C11, C++23 and Python APIs. All four
predictor levels require an explicitly loaded external model. No trained
Rosetta parameters are included in wheels, crates, native installations or
headers, and loading never downloads data or invokes the original Python
package. Python inference delegates to a separate native extension without a
NumPy runtime dependency.

The versioned scientific binding is `implementation.external_model` in
`specs/functions/zhang_schaap2017.yaml`. The normal generator emits public APIs,
umbrella registrations and reference documentation from that binding. Scalar
formula and Random Forest implementations retain their existing pipeline.

## Computational source and rights assessment

The audited source is the [official implementation at revision
6b0e3902f8a145805d41b691dc36f8e69e898f2a](https://github.com/usda-ars-ussl/rosetta-soil/tree/6b0e3902f8a145805d41b691dc36f8e69e898f2a).
The repository declares CC0, but its README attributes the trained weights and
biases to Marcel Schaap and Yonggen Zhang at the University of Arizona. The
reviewed repository contains no separate statement establishing their authority
to dedicate those contributed parameters to CC0. This audit does not establish
that redistribution is prohibited; it establishes that the requested evidence
of permission remains unresolved. No author has been contacted and no permission
is inferred or fabricated.

The committed `specs/models/rosetta3/manifest.json` pins the revision and SHA-256
hashes of the implementation, README, license, packaging definition, tests, and
all thirteen NPZ files. Only these five artifacts are imported:

| Artifact | Members | Network widths | Role |
| --- | ---: | --- | --- |
| `rose3_mod2_0.npz` | 1000 | 3, 6, 5 | Texture |
| `rose3_mod3_0.npz` | 1000 | 4, 6, 5 | Texture and bulk density |
| `rose3_mod4_0.npz` | 1000 | 5, 6, 5 | Also water content at 33 kPa |
| `rose3_mod5_0.npz` | 1000 | 6, 6, 5 | Also water content at 1500 kPa |
| `rose1_unsat_k.npz` | 100 | 4, 6, 2 | K0 and L from physical retention parameters |

The other eight Rosetta1 retention/conductivity artifacts are unnecessary for
Rosetta3. Rosetta3 uses one joint ensemble for its first five outputs; K0 and L
come from the separate 100-member Rosetta1 ensemble. No models are retrained.

Trained NPZs, converted binaries, generated local weight sources and development
environments remain under ignored local directories. They are not copied to any
package, crate, native installation, or generated public header.
The committed network metadata and trusted artifact descriptor contain hashes,
normalization constants and topology,
not trained weights. The fixtures contain predictions, not parameter tensors.
The CC0 source declaration and unresolved third-party parameter provenance must
both be preserved in any future distribution assessment.

## Exact inference contract

Predictors are ordered sand, silt, clay (mass percentages), bulk density
(g/cmВі), volumetric water content at 33 kPa, and volumetric water content at
1500 kPa (cmВі/cmВі). Level N takes the first N+1 predictors. The software audit
does not establish granulometric cutoffs or applicability beyond this upstream
contract. No texture conversion, renormalization, or representative texture
values are introduced.

The versioned `specs/models/rosetta3/network.json` records every scaler,
activation, width, ensemble size, parameter offset, and the converted binary's
hash. Inputs to the Rosetta3 networks use `(x - p0) * p1 + p2` with zero offsets.
Texture multipliers are 0.01; bulk density and retention predictors use 1.0.
In particular, the Rosetta3 bulk-density multiplier is **not** the 0.4 used by
the inspected Rosetta1 retention networks.

For each layer and member, compute the row-major weight dot product first,
then add its bias, then apply its activation. The first Rosetta3 layer uses
`-1 + 2 / (1 + exp(-2*x))`, exactly as upstream, rather than substituting
`tanh`. The second layer uses `1 / (1 + exp(-x))`. Outputs use `x*p0+p1` with
coefficient pairs `(1,0)`, `(1,0)`, `(-8,2)`, `(1.5,0)`, `(8,-2)`.
The resulting outputs are theta_r, theta_s, log10(alpha), log10(n),
log10(Ksat), in that order. Alpha refers to inverse centimetres and Ksat to
centimetres per day. A logarithm uses the numeric value in the stated unit;
it is not an implicit conversion to another unit.

The conductivity network consumes theta_r, theta_s, physical alpha, and
physical n. Its input transforms are identity division by 1 for the first two,
`log10(alpha)/(-8)+0.25`, and `log10(n)/1.5`. Both layers use sigmoid.
Outputs use `10*(x-0.3)` and `100*(x-0.5)`, returning log10(K0) and L.
K0 is the unsaturated-conductivity matching point in cm/day, not Ksat.
The network rejects retention inputs unless `0 <= theta_r < theta_s < 1`,
`alpha > 0`, and `n > 1`; the upstream result is NaN for those K0/L outputs.

| Estimate mode | First five reported means | Reported SD | Retention input to K0/L ensemble |
| --- | --- | --- | --- |
| Arithmetic (0) | Exponentiate each alpha/n/Ksat member, then average | Physical scale | Arithmetic means in physical units |
| Log (1) | Average the original network outputs | Log10 for alpha/n/Ksat; physical for water contents | Geometric means of alpha/n, arithmetic water contents |
| Geometric (2) | Exponentiate the log means for alpha/n/Ksat | Physical scale, as upstream | Geometric means of alpha/n, arithmetic water contents |

For K0, arithmetic mode exponentiates every conductivity-ensemble member
before computing mean and SD; log mode computes both statistics in log10;
geometric mode exponentiates the log10 mean but uses physical-scale SD.
L always uses arithmetic mean and SD. Geometric-mode SD is therefore not a
geometric standard deviation. All SDs are sample standard deviations with
`ddof=1`; none are standard errors. The conductivity ensemble is evaluated
once from aggregated retention predictions, not from each of the 1000 retention
members. It does not propagate the entire retention ensemble uncertainty.

## Input policy and numerical behavior

The upstream high-level API selects the best available model: nonnegative
texture components summing to 99вЂ“101 inclusive; bulk density 0.5вЂ“2 inclusive;
`0 < theta_1500 < theta_33 < 1`. Missing/invalid optional inputs downgrade the
model. Invalid texture produces code -1 and NaNs. The upstream low-level
`Rosetta.predict` validates shape but does not impose these physical checks.

The public APIs require an explicit level and reject invalid or non-finite
required predictors instead of downgrading. Rust returns `ModelError::Input`,
C returns `PTFKIT_MODEL_INPUT`, C++ throws `ModelError` with `ModelStatus::Input`,
and Python raises `ModelInputError`. C initializes valid output storage to NaNs
on failure. This difference is tested against the eight frozen upstream
validation cases. Missing-value sentinels and strings are not
interpreted as soil measurements. The texture sum is not forced to 100.

All trained parameters and operations use binary64. Scalar dot-product order
can differ from NumPy BLAS, and libm implementations may differ. Do not enable
fast-math or floating-point reassociation for scientific reproduction. The local
reference comparison uses `max(1e-11, 1e-12*abs(expected))`. This strict numerical
reproduction check is distinct from the catalogue's quantity-based scientific
tolerances. Initial unadjusted comparisons on the audited fixture showed at most
`3.965396899729967e-10` absolute and `4.649452749860472e-13` relative difference;
the larger absolute difference occurs on a large conductivity uncertainty.
The tolerances were not widened to make a failing case pass. Results on other
architectures and math libraries still require measurement.

## Build the external artifact

Run from the repository root with the pinned toolchains from the
[development guide](development.md). The upstream audit/import and all existing
local verification commands remain available unchanged:

```sh
git clone https://github.com/usda-ars-ussl/rosetta-soil .rosetta-upstream
git -C .rosetta-upstream checkout 6b0e3902f8a145805d41b691dc36f8e69e898f2a
mise run rosetta:import .rosetta-upstream
mise run rosetta:pack
mise run rosetta:verify-rust
```

For an existing imported checkout, run only `rosetta:pack`. Import and packing
use exclusive output creation; choose a new output path for a repeat run rather
than silently replacing an artifact. The general packer is:

```sh
cargo run --manifest-path codegen/Cargo.toml -- pack-neural-model --model .rosetta-local/imported/models.json --output .rosetta-local/rosetta3.ptfm
```

The resulting PTFKNN01 container is 2,212,632 bytes. Its SHA-256 is
`d4d2ca39f41762830f736c70fba16ed68a81cb52d4639b1f48c6a24e502c4796`.
The original parameter-only binary remains unchanged: 2,211,200 bytes, SHA-256
`f2b0ed39cc763fd2924e38cdfdafb5e0abb298094e561f73f7be290405b70990`.
The public APIs pin the complete container digest from
`specs/models/rosetta3/artifact.json`; architecture and parameters are checked
together. The old manifest and reference fixtures are not rewritten by packing.

## Public APIs

Python uses named result fields and requires no scientific Python runtime for
model evaluation:

```python
from ptfkit.zhang_schaap2017 import Rosetta3, Estimate, calc_ptf_zhang2017_mod5

model = Rosetta3.load("rosetta3.ptfm")
result = calc_ptf_zhang2017_mod5(
    model, sand=30, silt=30, clay=40, bulk_density=1.5,
    theta_33=0.3, theta_1500=0.1,
)
print(result.alpha_mean, result.alpha_std)
logged = model.predict(5, [30, 30, 40, 1.5, 0.3, 0.1], Estimate.LOG10)
```

The four `calc_ptf_zhang2017_mod2` through `mod5` functions report arithmetic
statistics in physical units, matching their scientific specifications.
`Rosetta3.predict` additionally exposes log10 and geometric estimates. Result
fields are `theta_r_mean` through `l_mean` and `theta_r_std` through `l_std`.
Python provides `mean` and `stddev` tuple properties; Rust and C++ provide the
same ordered arrays through methods.

```rust
use ptfkit::zhang_schaap2017::{Rosetta3, Estimate, calc_ptf_zhang2017_mod2};

fn example() -> Result<(), ptfkit::models::ModelError> {
let model = Rosetta3::load("rosetta3.ptfm")?;
let result = calc_ptf_zhang2017_mod2(&model, 30.0, 30.0, 40.0)?;
let logged = model.predict(2, Estimate::Log10, &[30.0, 30.0, 40.0])?;
    Ok(())
}
```

```c
#include <ptfkit/ptfkit.h>

int main(void) {
    ptfkit_model *model = NULL;
    if (ptfkit_rosetta3_load("rosetta3.ptfm", &model) != PTFKIT_MODEL_OK)
        return 1;
    ptfkit_rosetta3_statistics result;
    ptfkit_model_status status = calc_ptf_zhang2017_mod2(model, 30, 30, 40, &result);
    ptfkit_model_free(model);
    return status == PTFKIT_MODEL_OK ? 0 : 1;
}
```

C's `ptfkit_rosetta3_predict` accepts a level, a numeric mode (0 arithmetic,
1 log10, 2 geometric), required predictors, and storage for fourteen doubles:
seven means followed by seven SDs. Its outputs are initialized to NaN on errors.
Callers must check status; failed loading returns a null output handle. Free a
successful handle exactly once after all readers have finished. C paths use the
platform C runtime encoding; `ptfkit_model_from_bytes` allows caller-managed I/O.
Low-level C input and output buffers must not overlap.

```cpp
import ptfkit;

int main() {
    auto model = ptfkit::Rosetta3::load("rosetta3.ptfm");
    auto result = ptfkit::calc_ptf_zhang2017_mod2(model, 30, 30, 40);
    return result.theta_s_mean > result.theta_r_mean ? 0 : 1;
}
```

C++ model handles use move-only RAII. Installed `ptfkit::cpp` propagates the
public header include path and math-library requirements through `ptfkit::c`.
Rust models own their data and can be shared through `Arc`; Python owns a native
capsule. Prediction uses per-call scratch data and never modifies a loaded
model. Changing or removing the source file after loading does not change
predictions. A failed new load does not change another live model.

## Universal model loading and container contract

`ptfkit.models.Model` (Python), `ptfkit::models::Model` (Rust), `ptfkit::Model`
(C++), and `ptfkit_model` (C) load the same external container. Generic loaders
require an explicit trusted SHA-256. Obtain that digest from a trusted manifest;
accepting a digest from the same untrusted file would not establish its origin.
Rosetta3 adapters supply the reviewed digest automatically and reject other
valid model containers. Generic prediction returns raw ensemble members in the
container's original output scales, without Rosetta-specific aggregation.

The complete file is hashed before decoding parameter data. Readers validate
version, topology, scaler/activation identifiers, finite values, nonzero scale
denominators, unused scale padding, contiguous parameter offsets, exact tensor
counts, truncation and trailing bytes. Limits are 64 MiB, 1?64 networks,
2?1000 members per ensemble, 1?16 layers, and 1?64 nodes per layer. There is no
pickle, executable content, automatic file search, implicit default model or
network access. Exceeding a limit produces an error rather than partial inference.

All integers and IEEE binary64 values are little-endian. The version-1 layout is:

| Field | Encoding |
| --- | --- |
| Magic/version | Eight bytes `PTFKNN01` |
| Network count | u32 |
| Each network | u32 member count; u32 layer count; layer-count+1 u32 widths; layer-count u32 activation identifiers |
| Input then output scalers | Each scaler: u32 identifier and three f64 parameters, zero-padded to its declared arity |
| Each network parameter offset | u64 offset in doubles into the common tensor array |
| Tensor count and tensor data | u64 count, followed by f64 values in network/member/layer order; row-major weights then biases per layer |

Activation identifiers are linear=0, sigmoid=1, tansig=2, ReLU=3. Scalers are
asis=0, division=1, logtr=2, affine=3, minmax=4, linear=5, using the previously
audited formulas. The digest covers every byte, including architecture.
`network_count` and `network_shape` expose ensemble dimensions without decoding
metadata in application code. C uses status codes, Rust `ModelError` variants,
C++ `ModelError` with `ModelStatus`, and Python `ModelIntegrityError`,
`ModelFormatError`, or `ModelInputError` (all `ValueError` subclasses).
Missing-file errors remain I/O errors.

## Architecture decision: external model handles

Status: implemented, external parameters required.

The ordinary scalar formula/Random Forest IR is preserved. An explicitly typed
`implementation.external_model` binding selects the external ensemble backend;
its model kind, artifact reference, predictor ordering, level, function names and
output fields are validated before rendering. The backend emits generic loaders
and model-specific adapters through the normal atomic output pipeline, including
umbrella modules and API references. `generate-check` covers those files.
The four Rosetta3 bindings form one enabled model family; blocked bindings do
not produce public APIs or trigger artifact lookup.

The dense Rust kernel and C kernel retain their original operation order and
transforms. The Rosetta statistics layer is reused unchanged. C remains header
only, with a small SHA-256 implementation and owned heap data. C++ exports inline
adapters compatible with the existing interface-module installation. The Python
extension uses only the CPython C API and the native C loader. Rust uses `sha2`
for integrity checks. No runtime depends on the importer or original package.

The original local generation workflow remains available as an additional
reference path; it is no longer the public implementation. Unresolved weight
redistribution rights continue to prohibit bundling under this project's stated
release policy; they do not block these weight-free public APIs. The full paper,
training-population applicability and granulometric cutoffs still require
separate scientific review. This integration establishes computational parity,
not predictive accuracy for a new soil population.

## Verification

The immutable `specs/models/rosetta3/reference.json` and all pre-existing tests
are preserved. Public verification executes the released-package interfaces,
not copies of generated kernels: the Python native package, Rust crate example,
C umbrella header and C++ umbrella module. It checks all 120 upstream cases,
raw selected members, explicit-level rejection and changed-file integrity
failures. Independent hand-specified affine containers exercise all four generic
loaders, including owned data, typed failures, move semantics and correctly
hashed malformed inputs. The numerical reproduction tolerance remains
`max(1e-11, 1e-12*abs(expected))`.

```sh
mise run validate
mise run generate
mise run generate-check
mise run verify
mise run docs:build
mise run rosetta:verify-rust
mise run rosetta:verify-public
```

`rosetta:verify-public` requires the external artifact and explicitly fails when
it is absent. It builds the actual native targets and Rust example and rebuilds
the Python package before comparing the original fixtures. Ordinary tests use
only tiny hand-specified affine test data and do not require trained Rosetta
weights. No numerical expectations are regenerated from the new implementation.

## Executed integration checks

On Windows x64, the public Python package, Rust crate, C11 umbrella header and
C++23 umbrella module each passed all 120 unchanged upstream cases. Each also
rejected 30 invalid predictor/level/mode cases and changed model files. The
maximum observed absolute difference remained `3.965396899729967e-10`, and the
maximum relative difference remained `4.649452749860472e-13`. The original
reference JSON, import manifest, network metadata and parameter bytes were
unchanged. Repeated container packing produced byte-identical output.

| Check | Result |
| --- | --- |
| Specification validation | 40 source files, 253 declared functions |
| Codegen verification | 140 tests, formatting and Clippy passed |
| Rust verification | 362 existing tests and 2 new public loader tests passed |
| Python verification | 805 existing tests and 2 new public loader tests passed |
| Native verification | 134 existing tests and 2 new C/C++ loader tests passed |
| Public reference task | 120 upstream cases and 30 rejection cases per language passed |
| Distribution wheel, with `-I -S` and NumPy unavailable | All 120 original reference cases passed |
| Installed C++ package | Independent consumer compiled and matched upstream results; TU-local exposure diagnostics treated as errors |
| SHA-256 | Independent affine-container fingerprint and standard empty/abc/56-byte known-answer vectors passed |

The wheel, Python sdist, Rust crate and native installation were built locally
and inspected for `.npz`, `.ptfm`, `models.bin` and generated `weights.c` files;
none were present. Example archive sizes for the full existing ptfkit corpus
were approximately 1.85 MB (Windows wheel), 2.47 MB (Python sdist), and 2.12 MB
(Rust crate). These are local build measurements, not universal package sizes
or Rosetta-only costs. The 2.21 MB external trained artifact remains separate.
No package was published and nothing was merged to main.
