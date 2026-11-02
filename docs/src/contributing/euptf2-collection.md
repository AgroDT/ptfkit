---
title: EU-PTF v2 model collection
---

# EU-PTF v2 model collection

The pinned euptf2 1.0.0 package contains **77 distinct trained objects** and
**205 ranger regression forests**. The original scientific archive additionally
contains four forests forming **VG_PTF26**, omitted from the package registry.
ptfkit supports all **78 model groups / 209 original forests**. The collection inventory is
`specs/models/euptf2/collection.json`. It records every original filename,
SHA-256, ordered predictor list, component name, fitted-scale transformation,
forest dimensions, training sample count and terminal-response completeness.
Every forest has finite stored response samples at all reachable terminal nodes.
No model needs retraining or an approximation to its original quantile algorithm.

The implementation uses the same QRF traversal, leaf means, stored response
samples and type-7 interpolation validated by the
[THS_PTF01 reference slice](euptf2.md). `Euptf2Ths` and its PTFKQF01 artifact
remain compatible. `Euptf2Model` selects a distinct original object explicitly;
the package's recommended PTF aliases for 32 predictor combinations are not
additional trained models and do not trigger automatic selection or fallback.

## Coverage

| Family | Original objects | Native status | Upstream rows per object |
| --- | ---: | --- | ---: |
| THS | 5 | Implemented | 16 default + 2 custom |
| FC | 10 | Implemented | 16 default + 2 custom |
| FC_2 | 13 | Implemented | 16 default + 2 custom |
| WP | 7 | Implemented | 16 default + 2 custom |
| AWC | 2 | Implemented | 16 default + 2 custom |
| AWC_2 | 3 | Implemented | 16 default + 2 custom |
| KS | 3 | Implemented | 16 default + 2 custom |
| VG | 22 | Implemented | 25 default + 2 custom |
| MVG | 13 | Implemented | 31 default + 2 custom |

All 78 models are implemented; none is blocked. The first checkpoint covers
43 scalar models; the second adds 35 VG/MVG models through the same inference
engine. Every model has independent upstream fixtures and complete QRF state.

Per-model and per-target verification counts and numerical errors are recorded in
`specs/models/euptf2/verification.json`.
All four targets passed 1,797 upstream prediction rows each (7,188 total,
136,452 numeric comparisons). The largest absolute difference was
1.4551915228366852e-11 in physical-scale conductivity; the largest relative
difference was 1.4220422464135535e-14. Every model was also checked for missing
predictors, input shape errors, invalid probabilities and changed artifact bytes.

## Scientific contract

The scientific specification is `specs/functions/szabo_weynants_weber2021.yaml`.
Normal generation produces the catalog, named result records, scientific
functions and API documentation for all retained targets. Inputs and outputs
are validated against the independently inspected model contract before rendering.
The source is [Szabó, Weynants and Weber (2021)](https://doi.org/10.5194/gmd-14-151-2021),
with the computational reference pinned to euptf2 `v1.0.0`, revision
`f22c38f7e73819ad23d7f6ff00b970288a7d57d0`. The original package source hashes
and release provenance remain in `specs/models/euptf2/manifest.json`.

The scientific archive is `brigittaszabo/euptfv2` v.2.0.0, revision
`35e2df971259f8f1d9904c5d0359eb09406175b1`, corresponding to
[Zenodo 3759443](https://zenodo.org/records/3759443). The downloaded GitHub
revision ZIP has SHA-256
`e0fe56929e72f5bc1876962b12c24eb797744d289545f837cce0dac1c42b041a`.
`scientific-archive.json` records all 209 original forest hashes.
`archive-comparison.json` records direct R comparisons: all 205 packaged forests
have identical topology, split values, predictor metadata and complete stored
response matrices to their archived originals. VG_PTF26 uses the four remaining
original forests in THS, THR, ALP, N order.

| Predictor | Original unit and definition |
| --- | --- |
| USSAND | Mass %, USDA sand 50-2000 micrometres |
| USSILT | Mass %, USDA silt 2-50 micrometres |
| USCLAY | Mass %, USDA clay below 2 micrometres |
| DEPTH_M | Mean soil horizon depth in **cm** |
| OC | Organic carbon mass % |
| BD | Dry bulk density, g/cm3 |
| CACO3 | Calcium carbonate mass % |
| PH_H2O | pH measured in water |
| CEC | meq/100g, numerically equivalent to cmol(+)/kg |

All predictors enter the forest without transformation. Their order is the
saved forest's order, also exposed through model metadata. A scalar row must
contain every required predictor. NaN is missing and produces an input error;
the upstream table wrapper's complete-case filtering and OBS_ID preservation
belong to caller-side table orchestration. No imputation, clipping, texture
renormalization, unit conversion or model downgrade occurs. Numerical infinity
follows ordered comparisons as in ranger; it is not asserted to represent a
valid soil measurement.

| Output | Original-scale reporting | Back-transform after forest aggregation |
| --- | --- | --- |
| THS, THR | cm3/cm3 | THS identity; THR `10^x - 1` |
| FC_2 | cm3/cm3 at -100 cm matric potential head | Identity |
| FC | cm3/cm3 at -330 cm matric potential head | Identity |
| WP | cm3/cm3 at -15000 cm matric potential head | Identity |
| AWC_2, AWC | Directly fitted available water content, cm3/cm3 | Identity |
| KS, K0 | cm/day | `10^x` |
| ALP | 1/cm | `10^x` |
| N | Dimensionless | `10^x + 1` |
| L | Dimensionless | Identity |
| M | Dimensionless, point estimate only | `1 - 1/N` |

Means are aggregated on each forest's fitted scale before the original
back-transform. In particular, the KS point estimate is `10^mean(log10KS)`.
AWC models retain their directly fitted predictions. The default quantile
probabilities are **0.05, 0.25, 0.5, 0.75, 0.95**. Quantiles first interpolate
the saved terminal response samples on the fitted scale, then apply the
corresponding back-transform. They do not take percentiles of tree means or
interpolate already exponentiated responses.

VG orders its forests THS, THR, ALP, N; MVG adds K0 and L. Their mean outputs
append derived M. Their quantile outputs contain only the independently fitted
parameters, exactly as the upstream package: no M quantile is invented. These
are marginal distributions, with no joint parameter sampling, covariance or
enforced physical constraints between independently predicted parameters.

## Offline local import

Use the exact authenticated source described in the reference-slice guide.
The importer validates all 77 packaged RData hashes and the supplied archive's
four additional forest hashes before deserializing any object, including when
importing only a scalar subset. Base R performs the
conversion offline; ranger is not needed for conversion. No fitting or random
sampling occurs. All outputs must match their frozen whole-container digests
and sizes before the new destination directory becomes visible.

```sh
python codegen/scripts/import_euptf2.py --collection --upstream .euptf2-local/upstream --archive .euptf2-local/scientific-archive --output .euptf2-local/models
```

The output directory must be new. Pass `--rscript /path/to/Rscript` when needed.
The source paths are extracted repository roots at the exact revisions above.
The default `--group all` imports 78 models and requires both source trees.
`--group package` imports the 77 packaged objects without the archive;
`--group scalar` imports only the 43 scalar objects. To reproduce the full
archive reconciliation, run:

```sh
python codegen/scripts/audit_euptf2_archive.py --upstream .euptf2-local/upstream --archive .euptf2-local/scientific-archive --library .euptf2-local/R-library --output .euptf2-local/archive-comparison.json
```

This optional audit authenticates all 209 original archived forest files before
R compares their saved states against the installed package. The trained files and the
original upstream GPL source remain outside ptfkit release directories.
Runtime inference requires no R, NumPy inference API or ML framework.

```python
from ptfkit.models import Euptf2Model
from ptfkit.szabo_weynants_weber2021 import calc_ptf_szabo2021_fc_2_ptf03

model = Euptf2Model.load('FC_2_PTF03', '.euptf2-local/models/FC_2_PTF03.ptfq')
prediction = model.predict([40, 40, 20, 30, 1.3])
custom = model.predict([40, 40, 20, 30, 1.3], [0.1, 0.9])
named = calc_ptf_szabo2021_fc_2_ptf03(
    model, ussand=40, ussilt=40, usclay=20, depth_m=30, bd=1.3
)
```

Rust exposes `models::Euptf2Model`, `euptf2_models()` and `descriptor()`;
`predict(&inputs)` uses the five defaults and
`predict_quantiles(&inputs, &probabilities)` selects custom quantiles.
The scientific functions live in `szabo_weynants_weber2021`.
C11 exposes `ptfkit_euptf2_contracts`, `ptfkit_euptf2_load`,
`ptfkit_euptf2_from_bytes`, `ptfkit_euptf2_predict` and `ptfkit_euptf2_free`
through `<ptfkit/ptfkit.h>`. The prediction function accepts explicit storage
lengths; quantiles are parameter-major. NULL probabilities with count 5 select
the defaults. C++23 exposes the move-only `ptfkit::Euptf2Model` through
`import ptfkit`, with default/custom `predict` overloads. All four targets also
expose `calc_ptf_szabo2021_<family>_ptf<number>` named functions with fixed
default probabilities and model-identity validation.

Generic means and quantiles are separate arrays because VG/MVG have different
mean and quantile output counts. Quantile rows follow `quantile_outputs` and
columns follow the supplied probability order. The native interface permits
1-64 probabilities strictly inside (0,1), including repeated or unsorted
probabilities. Model handles own their decoded state and use read-only metadata.

## Versioned collection format

PTFKQF02 stores one original trained object. All integers are little-endian u32
and numeric records use IEEE-754 little-endian binary64. The header contains
the eight-byte magic, trusted scientific model ID, predictor count and forest
count. Each forest starts with its transform code (0 identity, 1 power ten,
2 power ten minus one, 3 power ten plus one), then the tree count and the
original PTFKQF01 tree layout: node count and 28-byte node records, with left
child, right child, feature, threshold/terminal mean and terminal response sample.
The same decoder and QRF evaluator handle all forests and the retained reference
slice. Original response-inclusive split IDs are normalized exactly once by
the offline importer.

Whole-container SHA-256 authentication precedes parsing. The scientific model
ID, feature/forest counts and transform codes must match the trusted contract.
The decoder checks finite values, canonical leaf markers, ordered child IDs,
unique parents, reachability, sizes, truncation and trailing data. Containers
are bounded to 64 MiB, with up to 1000 trees per forest and six forests per
object. The largest original object fits within these limits. No trained
thresholds, means or response-sample arrays are embedded in generated targets.

## Independent verification

`codegen/scripts/reference_euptf2_collection.R` executes the actual installed
upstream `euptf2::euptfFun` for the 77 packaged objects' means, default quantiles
and custom 0.1/0.9 quantiles, and inspects every original saved object.
For archive-only VG_PTF26 it calls the unmodified exported upstream helpers
`ptfFun.pred`, `ptf.transFun` and `ptfFun.quant` on the four original forests,
then applies the original derived-M equation. The package's top-level registry
cannot load this omitted model. This oracle distinction is explicit in its fixture.
The reference script reads no converted
artifact and calls no ptfkit prediction. References are frozen per object under
`specs/models/euptf2/references/`. Inputs use 17-digit decimal strings to
preserve the exact binary64 thresholds used by the oracle; replay parses these
strings as numeric values before inference. Expected predictions come only
from upstream R.

Each fixture includes ten original sample soils, exact root thresholds and
both sides for each parameter forest, plus three extreme textures. Native
verification also checks each required predictor as missing, incorrect input
lengths, invalid probabilities and a changed artifact. Python verification
executes every generated named scientific function as well as its generic API.
Hand-specified synthetic forests protect inclusive routing, the distinction
between leaf means and response samples, the ninth predictor, transform order,
default/custom probability ordering and derived M behavior.

```sh
Rscript --vanilla codegen/scripts/reference_euptf2_collection.R .euptf2-local/upstream .euptf2-local/R-library .euptf2-local/reference-repeat .euptf2-local/scientific-archive
cargo build --manifest-path targets/ptfkit-rs/Cargo.toml --example euptf2_runner
uv run --project targets/ptfkit-py --frozen python codegen/scripts/verify_euptf2_collection.py --models .euptf2-local/models --rust targets/ptfkit-rs/target/debug/examples/euptf2_runner --report .euptf2-local/verification.json
```

Use the pinned R 4.4.3 / ranger 0.18.0 reference environment; the destination
must be new. On Windows append `.exe` to the Rust runner path. Build the native
targets and Python extension first. The comparison tolerance is
`max(2e-14, 2e-13*abs(expected))`, selected for binary64 aggregation,
interpolation and exponential back-transforms in the original output units.
It is distinct from predictive accuracy or the catalog's scientific tolerances.
No tolerance was increased in response to a failing comparison.

The completion checks passed 145 codegen tests, 365 Rust unit tests and three
integration tests, 137 native CTest cases, 808 Python tests and six importer
tests, plus formatting, linting, type checking, deterministic generation and a
strict documentation build. Rosetta3 passed its unchanged 120 upstream cases
and 30 rejected-input cases on each target. A fresh wheel passed every model's
fixtures in an isolated interpreter without NumPy or R installed. The wheel,
source distribution and Rust package listing contain no upstream R source or
trained QRF artifacts. The original THS_PTF01 interface and artifact remain
compatible with its 60-case reference suite.

The Rosetta container, neural kernels, normalization and reference expectations
are retained. This computational parity work does not establish predictive
accuracy outside the training populations. The collection is limited to the
original released objects and their marginal predictions; it adds no fitting,
training, physical repair, automatic PTF selection or OOB uncertainty interface.
