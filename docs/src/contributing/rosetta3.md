---
title: Rosetta3 and external models
---

# Rosetta3 and external models

Rosetta3 is available in the public Rust, C11, C++23 and Python APIs with
bundled CC0 parameters. No model download, conversion, external model file,
NumPy inference runtime or original Rosetta package is required. All four
predictor levels and all three reporting modes use the same pinned parameters
and numerical kernels as the existing upstream reference tests. Generic
integrity-checked external model loading remains available as an option.

The versioned scientific binding is `implementation.external_model` in
`specs/functions/zhang_schaap2017.yaml`. The normal generator emits public APIs,
umbrella registrations and reference documentation from that binding. Scalar
formula and Random Forest implementations retain their existing pipeline.

## Computational source and rights assessment

The audited source is the [official implementation at revision
6b0e3902f8a145805d41b691dc36f8e69e898f2a](https://github.com/usda-ars-ussl/rosetta-soil/tree/6b0e3902f8a145805d41b691dc36f8e69e898f2a).
The USDA repository publishes its implementation and included NPZ artifacts
with a [CC0 declaration](https://creativecommons.org/publicdomain/zero/1.0/).
No NPZ-specific license exclusion was found in the reviewed checkout. CC0 is
an explicit public-domain dedication, with a fallback license where a waiver
cannot take effect; it permits copying and redistribution without requesting
individual permission. Its README attributes the trained weights and biases
to Marcel Schaap and Yonggen Zhang at the University of Arizona.
An initial review of that repository alone missed the separate
[author repository](https://github.com/YonggenZhang/Rosetta/tree/2a4aae0bdcea20cc2f1887ce25aa0b4336dd9510).
The author repository supplies the original trained networks in a SQLite
database, a GPLv3 `LICENSE`, and source headers identifying Marcel G. Schaap's
2016 copyright and GPLv2-or-later terms. This is positive evidence of author
publication with GPL licensing notices; describing these weights as having no
author-published licensing evidence would be incorrect.

The exact comparison below establishes parameter identity for the four
Rosetta3 retention/Ksat ensembles. The author GPL notices and USDA CC0
declaration are both recorded. Neither an acknowledgment of other authors nor
another publication under GPL, by itself, establishes that USDA's CC0
declaration is invalid. This comparison does not determine ownership or license
validity, and CC0 does not waive rights its declarant does not hold.

The earlier assessment treated the absence of a separate permission statement
from each contributor as a distribution blocker. That conclusion was too
categorical and was not established by the reviewed evidence. The reviewed USDA parameters are now bundled under their published CC0 terms.
This adds no author approval requirement. No author has
been contacted.

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

The original NPZs and author database remain in ignored audit checkouts.
The byte-identical reviewed PTFKNN01 container is committed at
`specs/models/rosetta3/rosetta3.ptfm`. Normal generation verifies its size and
SHA-256, emits the Rust binary resource and the C data translation unit, and
checks both for generated-output drift. Public headers contain declarations,
not trained arrays. `MODEL_NOTICE.txt` in each distribution records CC0,
upstream revision, credits and container hash. ptfkit code remains MIT-licensed.
The network metadata and fixtures contain topology, normalization and
predictions; the trained tensors are confined to the designated model assets.
Preserve the USDA CC0 declaration, the author GPL notices and the verified
parameter identity in provenance records. The absence of K0/L from this author
database limits this particular comparison; it is not evidence that the USDA
K0/L artifact cannot be distributed under its published terms. The original
import manifest's redistribution label records the earlier fallback decision;
it remains unchanged to preserve the hashes recorded in the frozen reference
fixture and is not the current licensing assessment.

## Author database comparison

`specs/models/rosetta3/author-manifest.json` pins author revision
`2a4aae0bdcea20cc2f1887ce25aa0b4336dd9510` and SHA-256 hashes of its license,
README, three Python sources, SQLite database and SQL dump. The database hash is
`0e1a3f3ccbcf569066dc3c19027183646e434eece30213896f00df6f477910de`.
The committed `author-comparison.json` records the independently executed audit;
it contains hashes, dimensions, scalers and comparison outcomes, not weights.

| USDA NPZ | Author model ID | Members | Weight/bias values | Result |
| --- | ---: | ---: | ---: | --- |
| `rose3_mod2_0.npz` | 2 | 1000 | 59,000 | Bitwise equal |
| `rose3_mod3_0.npz` | 3 | 1000 | 65,000 | Bitwise equal |
| `rose3_mod4_0.npz` | 4 | 1000 | 71,000 | Bitwise equal |
| `rose3_mod5_0.npz` | 5 | 1000 | 77,000 | Bitwise equal |
| `rose1_unsat_k.npz` | Absent | 100 in USDA | 4,400 in USDA | Not established |

All 272,000 Rosetta3 binary64 weight/bias values match exactly, including member
order when SQLite rows are sorted by `Ann.seq`. Network widths, activation
functions, input normalization, output transforms and log-output conventions
also match. These are comparisons of every stored parameter, not inference from
similar aggregate predictions. The eight additional Rosetta1 retention/Ksat
NPZs also match their author ensembles, covering all 4,640 networks in the
database. The database has no two-output network and therefore does not supply
the separate 4-6-2 K0/L ensemble used by ptfkit.

Parameter identity does not imply identical high-level software behavior. The
author beta's `PTF_MODEL.sum_stat` uses population covariance (`ddof=0`) and its
code marks unsaturated-conductivity integration as unfinished. ptfkit continues
to use the audited USDA reporting modes, sample SD (`ddof=1`), K0/L ensemble and
unchanged upstream reference fixture. No inference kernel, trained binary or
existing numerical expectation was changed by this provenance audit.

To reproduce the audit from the repository root:

```sh
git clone https://github.com/YonggenZhang/Rosetta .rosetta-local/author-upstream
git -C .rosetta-local/author-upstream checkout 2a4aae0bdcea20cc2f1887ce25aa0b4336dd9510
mise exec -- uv run --no-project --with numpy==2.4.3 python codegen/scripts/compare_rosetta3_author.py --author .rosetta-local/author-upstream --upstream .rosetta-upstream --output .rosetta-local/author-comparison-repeat.json
```

Obtain the pinned USDA checkout as described under
[Build the external artifact](#build-the-external-artifact). Both checkout
revisions and all pinned file hashes are verified before NPZ pickle loading.
The author Python code is inspected but never imported or executed; the script
reads the SQLite database in immutable read-only mode and decodes network
matrices independently. The output path must be new. Ordinary generation does
not replace the committed audit report.

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

This section is optional: installed packages already contain the reviewed
model. It independently reproduces the bundled container from the original
`.npz` files in the official upstream Git repository. Run the following commands from a ptfkit repository checkout with
Git and the pinned toolchains installed as described in the
[development guide](development.md):

```sh
git clone https://github.com/usda-ars-ussl/rosetta-soil .rosetta-upstream
git -C .rosetta-upstream checkout 6b0e3902f8a145805d41b691dc36f8e69e898f2a
mise run rosetta:import .rosetta-upstream
mise run rosetta:pack
```

The clone contains all thirteen original `.npz` files under
`.rosetta-upstream/src/rosetta/data/`; no separate model download or installed
Rosetta Python package is needed. Keep the complete checkout: the importer
checks the exact Git revision and every source/artifact hash recorded in
`specs/models/rosetta3/manifest.json`, including the eight unused model files,
before opening any NPZ pickle metadata. A different revision or changed file
is rejected.

`rosetta:import` runs `codegen/scripts/import_rosetta3.py` using uv's isolated
environment with NumPy 2.4.3. On the first run, uv needs access to that dependency;
there is no need to install NumPy into the application's runtime environment.
Import writes `.rosetta-local/imported/models.json` (network metadata) and
`.rosetta-local/imported/models.bin` (binary64 parameters).
`rosetta:pack` then runs the Rust converter and writes the complete external
container `.rosetta-local/rosetta3.ptfm`. Loading an original `.npz` or the
intermediate `models.bin` directly with `Model.load()` is unsupported.

For an existing imported checkout, run only `rosetta:pack`. Import and packing
use exclusive output creation; choose a new output path for a repeat run rather
than silently replacing an artifact. The general packer is:

```sh
mise exec -- cargo run --manifest-path codegen/Cargo.toml -- pack-neural-model --model .rosetta-local/imported/models.json --output .rosetta-local/rosetta3.ptfm
```

The resulting PTFKNN01 container is 2,212,632 bytes. Its SHA-256 is
`d4d2ca39f41762830f736c70fba16ed68a81cb52d4639b1f48c6a24e502c4796`.
The original parameter-only binary remains unchanged: 2,211,200 bytes, SHA-256
`f2b0ed39cc763fd2924e38cdfdafb5e0abb298094e561f73f7be290405b70990`.
The public APIs pin the complete container digest from
`specs/models/rosetta3/artifact.json`; architecture and parameters are checked
together. The old manifest and reference fixtures are not rewritten by packing.

The reproduced file must be byte-identical to
`specs/models/rosetta3/rosetta3.ptfm`. It can also be supplied to the optional
`Rosetta3.load` APIs. No application needs this workflow to use the bundled
model. Loading never downloads or converts parameters implicitly.

## Public APIs

Python uses named result fields and requires no scientific Python runtime for
model evaluation:

```python
from ptfkit.zhang_schaap2017 import Rosetta3, Estimate, calc_ptf_zhang2017_mod5

model = Rosetta3()
result = calc_ptf_zhang2017_mod5(
    model,
    sand=30,
    silt=30,
    clay=40,
    bulk_density=1.5,
    theta_33=0.3,
    theta_1500=0.1,
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
let model = Rosetta3::builtin()?;
let result = calc_ptf_zhang2017_mod2(&model, 30.0, 30.0, 40.0)?;
let logged = model.predict(2, Estimate::Log10, &[30.0, 30.0, 40.0])?;
    Ok(())
}
```

```c
#include <ptfkit/ptfkit.h>

int main(void) {
    ptfkit_model *model = NULL;
    if (ptfkit_rosetta3_builtin(&model) != PTFKIT_MODEL_OK)
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
    auto model = ptfkit::Rosetta3::builtin();
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

In codegen, `neural/public.rs` renders the shared loaders and dispatches model
kinds to scientific adapters. `neural/public_rosetta.rs` owns the Rosetta3
publication identity, predictor/output ordering, required levels, pinned
artifact and aggregation bindings. Its CPython method is supplied separately
by `public_rosetta_python.c`; the generic bridge has no Rosetta method or header
unless the adapter registers them. The existing local C runtime remains the
shared source for the dense kernel so this separation does not duplicate or
change its numerical operations.

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

## Architecture decision: bundled model with optional external handles

Status: implemented, reviewed parameters bundled.

The ordinary scalar formula/Random Forest IR is preserved. An explicitly typed
`implementation.external_model` binding selects the ensemble backend;
its model kind, artifact reference, predictor ordering, level, function names and
output fields are validated before rendering. The backend emits generic loaders
and model-specific adapters through the normal atomic output pipeline, including
umbrella modules and API references. `generate-check` covers those files.
The four Rosetta3 bindings form one enabled model family; blocked bindings do
not produce public APIs or trigger artifact lookup.

The dense Rust kernel and C kernel retain their original operation order and
transforms. The Rosetta statistics layer is reused unchanged. Rust uses
`include_bytes!` for a generated binary resource. C compiles the container once
in a separate data translation unit; model handles authenticate and decode it
through the existing generic loader. The installed native package includes
portable data source and compiles it once with the consumer's toolchain, for
C-only, C++-only and mixed projects. C++ module objects supply their runtime
definitions, including exception RTTI. The Python native extension links the
same data translation unit and uses no NumPy runtime API. Its constructor
briefly copies the embedded bytes before the generic native loader owns the
decoded model. Rust uses `sha2` for integrity checks. No runtime depends on
local audit checkouts or development environments.

The original local generation workflow remains available as an additional
reference path; it is no longer the public implementation. Bundled parameters are the default; external model
loading remains optional. The published CC0 declaration does
not itself prohibit bundling, and this document imposes no additional author
permission requirement. The full paper,
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
mise run rosetta:verify-bundled
```

`rosetta:verify-public` requires the external artifact and explicitly fails when
it is absent. It builds the actual native targets and Rust example and rebuilds
the Python package before comparing the original fixtures. Ordinary tests include hand-specified affine containers and bundled-model
checks against frozen upstream values. `rosetta:verify-bundled` compares all
four bundled APIs with the 120 upstream cases and 30 rejection cases without
accepting any external model path; CI runs it in the native job. No numerical expectations are regenerated from the new implementation.

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
| Codegen verification | 144 tests, formatting and Clippy passed |
| Rust verification | 362 existing tests and 3 public model tests passed |
| Python verification | 805 existing tests and 3 public model tests passed |
| Native verification | 134 existing tests and 2 new C/C++ loader tests passed |
| External and bundled reference tasks | Each path passed 120 upstream cases and 30 rejection cases per language |
| Distribution wheel, with `-I -S` and NumPy unavailable | All 120 original reference cases passed |
| Installed C++ package | Independent consumer compiled and matched upstream results; TU-local exposure diagnostics treated as errors |
| SHA-256 | Independent affine-container fingerprint and standard empty/abc/56-byte known-answer vectors passed |

The earlier weight-free build measured approximately 1.85 MB for the Windows
wheel, 2.47 MB for the Python sdist and 2.12 MB for the Rust crate. Those are
historical baseline measurements, not measurements of the bundled packages.
The bundled container adds 2,212,632 binary bytes before compression; the C data
translation unit is a textual representation of those same bytes. The new Windows packages were built and inspected, including the model data
and CC0 notices. The wheel was built from the sdist and passed all 120 original
cases with `-I -S`, NumPy unavailable and an empty working directory. Fresh
C-only and C++-only installed consumers passed the bundled upstream case.

| Bundled distribution | Measured bytes |
| --- | ---: |
| CPython 3.13 Windows x64 wheel | 4,000,832 |
| Python sdist | 5,524,479 |
| Rust crate | 4,271,931 |
| Native portable source archive | 7,666,392 |

The installed native source tree occupied 49,862,462 bytes, including the
existing PTF corpus. In the isolated CPython wheel check, a warm 1000-call
level-5 arithmetic run measured about 132 microseconds per sample; the process
peak working set was 24,084,480 bytes. The latter includes Python, imported
modules and the verification workload, not just the model. These are local
Windows measurements, not cross-platform size, memory or speed guarantees.
No package has been published by this work.
