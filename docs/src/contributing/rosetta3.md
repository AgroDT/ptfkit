---
title: Rosetta3 local native verification
---

# Rosetta3 local native verification

Rosetta3 is **not implemented in the released ptfkit APIs**. This work provides
the requested fallback for unresolved trained-parameter redistribution rights:
a pinned importer, a reusable native neural ensemble interpreter, independently
executed reference fixtures, and opt-in local Rust, C11, C++23 module, and
CPython targets. The four catalogue entries remain blocked. Do not describe
local verification as completion of the production integration.

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

Trained NPZs, converted binaries, generated weight sources, local executables,
and development environments remain under ignored local directories. They are
not copied to any package, crate, native installation, or generated release API.
The committed network metadata contains normalization constants and topology,
not trained weights. The fixtures contain predictions, not parameter tensors.
The CC0 source declaration and unresolved third-party parameter provenance must
both be preserved in any future distribution assessment.

## Exact inference contract

Predictors are ordered sand, silt, clay (mass percentages), bulk density
(g/cm³), volumetric water content at 33 kPa, and volumetric water content at
1500 kPa (cm³/cm³). Level N takes the first N+1 predictors. The software audit
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
texture components summing to 99–101 inclusive; bulk density 0.5–2 inclusive;
`0 < theta_1500 < theta_33 < 1`. Missing/invalid optional inputs downgrade the
model. Invalid texture produces code -1 and NaNs. The upstream low-level
`Rosetta.predict` validates shape but does not impose these physical checks.

The local API intentionally requires an explicit level and rejects invalid or
non-finite required predictors instead of downgrading. Rust returns `None`,
C/C++ return 0 (and initialize available output storage to NaNs), and CPython
raises `ValueError`. This difference is documented and tested against the eight
frozen upstream validation cases. Missing-value sentinels and strings are not
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

## Reproduction workflow

Use a dedicated feature branch. Install the project toolchains as described in
the [development guide](development.md). Commands below run from the repository
root. Download and check out the exact revision:

```sh
git clone https://github.com/usda-ars-ussl/rosetta-soil .rosetta-upstream
git -C .rosetta-upstream checkout 6b0e3902f8a145805d41b691dc36f8e69e898f2a
uv venv .rosetta-env
```

Install the local upstream checkout, NumPy 2.4.3 and pytest 9.2.0 into this
separate environment. On Windows its interpreter is
`.rosetta-env/Scripts/python.exe`; on POSIX use `.rosetta-env/bin/python`:

```sh
uv pip install --python .rosetta-env/Scripts/python.exe numpy==2.4.3 pytest==9.2.0 ./.rosetta-upstream
.rosetta-env/Scripts/python.exe -m pytest .rosetta-upstream/tests -q
mise run rosetta:import .rosetta-upstream
mise run rosetta:verify-rust
mise run rosetta:generate-local
```

Every source/artifact hash is checked **before** loading NPZ object metadata
with pickle. Only trusted pinned artifacts are accepted. The binary stores
little-endian binary64 parameters in network, member, layer order; each layer
stores row-major weights followed by biases. Its size is 2,211,200 bytes and
SHA-256 is
`f2b0ed39cc763fd2924e38cdfdafb5e0abb298094e561f73f7be290405b70990`.
The Rust loader also validates SHA-256, finite parameters, topology, contiguous
offsets, scaler arity, denominator validity, and exact byte consumption.
The Rosetta-specific local renderer additionally compares all metadata to the
reviewed network contract. Output directories must not already exist: an import
or generation never silently replaces reviewed local artifacts.

Compile the generated Rust runner and CMake targets:

```sh
mise exec -- rustc --edition 2024 -O .rosetta-local/native/runner.rs -o .rosetta-local/native/rosetta_rust.exe
mise exec -- cmake -S .rosetta-local/native -B .rosetta-local/build -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ -DPython_EXECUTABLE=.rosetta-env/Scripts/python.exe
mise exec -- cmake --build .rosetta-local/build
.rosetta-env/Scripts/python.exe codegen/scripts/verify_rosetta3_targets.py --build .rosetta-local/build --rust .rosetta-local/native/rosetta_rust.exe
```

On Windows run CMake in a Visual Studio x64 development shell, use the pinned
`clang-cl.exe` for both compilers, and provide the pinned
`clang-scan-deps.exe` through `CMAKE_CXX_COMPILER_CLANG_SCAN_DEPS`. Use an absolute
Python executable path. The repository's `native:configure` task demonstrates
the same SDK setup. On POSIX omit `.exe` and adjust interpreter paths. The
verification task `rosetta:verify-targets` can also run the comparison when its
Python interpreter matches the built extension ABI.

The immutable reference is `specs/models/rosetta3/reference.json`: 120 prediction
cases (four levels, three estimate modes, ten soils), eight validation cases,
selected original ensemble-member values, and separate conductivity reference
statistics. Expected values come from actual upstream execution in the isolated
environment, never the ptfkit interpreter. Provenance includes revision,
manifest hash, Python/NumPy/distribution versions, and the called upstream API.
To independently reproduce it, write to a **new** file:

```sh
.rosetta-env/Scripts/python.exe codegen/scripts/reference_rosetta3.py --upstream .rosetta-upstream --output .rosetta-local/reference-repeat.json
```

Fixture replacement requires scientific review; neither ordinary generation
nor verification updates expected results. Changing a hash is not permission to
redistribute the model.

## Architecture decision: local artifact fallback

Status: experimental fallback, production integration deferred.

The existing scalar formula/Random Forest semantic IR does not express model
handles, external binary artifacts, ensemble-valued predictions, or uncertainty
aggregation. Pretending a neural model is a scalar formula would obscure that
contract. The local path is separate and explicitly does not change the public
pipeline. A reusable dense-network representation supports validated layer
widths, per-layer activations, input/output transforms, row-major parameters,
and bootstrap membership. Rosetta aggregation is a separate layer.

The Rust generator emits local standalone targets from this representation.
Rust embeds the little-endian binary with `include_bytes!`; C compiles weights
once in a separate translation unit. Public headers contain no trained arrays.
C++23 exports the C API through a compiled module; CPython delegates directly
to the C engine with no NumPy, SciPy, original Rosetta package, or ML framework
runtime. The release trees remain weight-free. Local generated sources are not
manually edited or committed. SHA-256 binds data to metadata before generation.

Before production integration, design and review a public model-handle and
optional external artifact contract across semantic IR and all targets, wire
that into normal generation/packaging, add package-level parity tests and API
documentation, and establish distribution permission for any shipped trained
data. Unresolved weight rights block bundling; they do not inherently prohibit
a future weight-free public model-loading API. That API remains engineering
work, not an alleged legal prohibition. The current local C API embeds a model
in the local binary; it is not the future external-artifact loading API.

## Measured local results and limitations

Windows x64, Clang 23.1.4 (MSVC ABI), optimized CMake build, Rust 1.98.1,
CPython 3.13.12, NumPy 2.4.3 for offline references:

| Local target | Upstream prediction cases passed | Executable/extension bytes |
| --- | ---: | ---: |
| Rust | 120 | 2,448,896 |
| C11 | 120 | 2,249,216 |
| C++23 module | 120 | 2,249,216 |
| CPython native extension | 120 | 2,249,728 |

All four also rejected the eight invalid-input cases under the documented
fixed-level policy, plus 22 additional checks of invalid levels/modes, predictor
counts, and non-finite values in every predictor. Explicit cross-target
comparisons showed zero difference on this platform. The upstream's own test
suite passed 25 tests. The first
local C/C++/CPython configure and build command took approximately 7.8 seconds
wall time, including SDK setup and CMake compiler detection. A 1000-call warm
CPython level-5 arithmetic run took approximately 128 microseconds per sample.
These are local observations, not cross-platform performance guarantees.

The C engine allocates two 5000-double retention buffers (80,000 bytes) plus
small network and conductivity scratch arrays on the stack and accesses the
2.21 MB trained array in read-only storage. Rust additionally decodes the
embedded little-endian data into a 2.21 MB `Vec<f64>` and allocates ensemble rows.
These are storage accounting figures; peak process RSS was not measured.
Wheel size, Rust crate size, and native release-distribution impact are not
measured because no release package includes the models. The local binary
measurements do not substitute for those packaging measurements.

The retained release APIs do not expose Rosetta3 yet. Generated release Rust,
Python, C, and C++ API reference pages therefore intentionally make no claim of
support. The normal catalogue contains four blocked scientific source entries.
The complete model paper, training population limitations, and granulometric
definitions require further scientific review; the computational software audit
does not establish those facts. The task's full Definition of Done is not met.

## Executed verification report

The following checks were actually executed successfully on this branch:

| Command/check | Result |
| --- | --- |
| `mise run validate` | 40 source specifications, 253 declared functions validated |
| `mise run generate` | Normal release trees and blocked-source catalogue regenerated |
| `mise run generate-check` | No generated-output drift |
| `mise run verify` | Full component format/lint/type/test checks passed; 362 Rust tests, 805 Python tests, 134 native CTest cases |
| `mise run codegen:verify` after the documentation fix | 136 tests passed, formatting and Clippy passed |
| `mise run docs:build` | Strict documentation build passed |
| `mise run rosetta:verify-rust` | 120 upstream prediction cases plus selected raw members and separate conductivity checks passed |
| Local CMake/Rust builds and `verify_rosetta3_targets.py` | All four local targets passed 120 upstream cases, eight upstream invalid cases, and 22 additional rejection checks each |
| Upstream `pytest .rosetta-upstream/tests -q` | 25 passed; two upstream pytest deprecation warnings |
| Repeated import/reference execution | Byte-identical binary, metadata, and upstream fixture |
| Repeated local target generation | All 13 generated files byte-identical |
| CPython inference with `-I -S` | Passed with site packages disabled and no NumPy import |
| Sample-SD mutation probe | Replacing `ddof=1` with population SD failed the intended assertion; original source restored |
| Matrix-orientation mutation probe | Transposing asymmetric weight matrices failed the intended prediction assertion; original source restored |

The new offline Python scripts also pass the repository's Ruff checks and
formatter. A pre-existing Windows toolchain environment issue required an
ignored `.mise.local.toml` PATH override pointing at the already installed
pinned Clang binaries. The first generation attempt failed because the
formatter was missing from the tool runner's PATH; generation and consistency
checks subsequently passed with that environment repaired. The first strict
documentation build exposed generation of an API page for an entirely blocked
source; the renderer now excludes nonexistent generated Python modules and has
a regression test. No generated source was edited to repair either issue.

Nothing was merged, published, or released. Production model handles, semantic
IR integration, package-level Rosetta APIs and documentation, release artifact
packaging measurements, peak RSS measurements, and trained-weight redistribution
permission remain outstanding. The local verification results are evidence for
the preserved numerical contract, not a claim that those deliverables are done.
