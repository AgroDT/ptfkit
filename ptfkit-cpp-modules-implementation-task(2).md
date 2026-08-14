# Implement the C++20 module target

Add a C++20 module backend to `ptfkit-native`.

Each APA source specification generates one named C++ module. The top-level `ptfkit` module is an umbrella that only re-exports the generated source modules.

## Module layout

Generate one module interface unit per source:

```text
targets/
└── ptfkit-native/
    └── cpp/
        ├── ptfkit.cppm
        ├── aimrun2009.cppm
        ├── beniaich2023.cppm
        ├── cosby1984.cppm
        ├── wang2012.cppm
        └── ...
```

Module names follow the source slug:

```cpp
export module ptfkit.wang2012;
```

Do not use module partitions for APA sources.

## Source namespaces

Every source module exports its API from a dedicated namespace:

```cpp
export module ptfkit.wang2012;

export namespace ptfkit::wang2012 {
    // generated API
}
```

The namespace name is the same source slug used by the module.

Users should therefore access functions as:

```cpp
import ptfkit.wang2012;

auto result = ptfkit::wang2012::calc_ptf_wang2012(...);
```

## Function names

Preserve function names from the specification exactly.

All generated PTF functions follow the project naming convention:

```text
calc_ptf_<author><year>[_<addition>]
```

The source namespace must not shorten the function name.

For example:

```cpp
ptfkit::wang2012::calc_ptf_wang2012(...)
```

and, for a function with an addition:

```cpp
ptfkit::<source>::calc_ptf_<author><year>_<addition>(...)
```

Do not derive alternative C++-specific function names.

## Result types

Do not synthesize result type names in the C++ backend.

Use the result type name already resolved from the specification by the shared model:

- scalar outputs return `double`;
- record outputs use the existing resolved result class name;
- when a record output references a reusable `$defs` output schema, use that schema name;
- otherwise use `public_api.result_class`.

The generated result type belongs to the same source namespace as its function.

For example, the existing `wang2012` specification defines:

```yaml
public_api:
  result_class: Wang2012PTFResult
```

so the generated C++ API should be:

```cpp
export module ptfkit.wang2012;

export namespace ptfkit::wang2012 {

struct Wang2012PTFResult {
    double theta_s;
    double theta_fc;
    double k_sat;
};

[[nodiscard]]
Wang2012PTFResult calc_ptf_wang2012(
    double sand,
    double silt,
    double clay,
    double bulk_density,
    double soil_organic_carbon,
    double altitude
) {
    // generated implementation
}

}
```

The fully qualified type is therefore:

```cpp
ptfkit::wang2012::Wang2012PTFResult
```

The backend must never produce names such as:

```text
calc_ptf_wang2012_result
calc_ptf_wang2012_water_retention_result
```

unless such a name is explicitly present in the specification.

## Umbrella module

Generate a small umbrella module containing only re-exports:

```cpp
export module ptfkit;

export import ptfkit.aimrun2009;
export import ptfkit.beniaich2023;
export import ptfkit.cosby1984;
export import ptfkit.wang2012;
// ...
```

Users may import one source:

```cpp
import ptfkit.wang2012;

auto result = ptfkit::wang2012::calc_ptf_wang2012(...);
```

or the complete API:

```cpp
import ptfkit;

auto result = ptfkit::wang2012::calc_ptf_wang2012(...);
```

The umbrella module must contain no numerical implementations.

## Code generation

The C++ backend consumes the shared semantic IR directly and generates one `.cppm` file per source specification.

Each generated source module contains:

- the named module declaration;
- the `ptfkit::<source>` namespace;
- spec-defined record result types where required;
- generated PTF functions;
- generated intermediate calculations.

Use idiomatic C++ standard-library math functions:

```cpp
std::sqrt(x)
std::exp(x)
std::log(x)
std::log10(x)
std::abs(x)
```

Use `[[nodiscard]]` for generated PTF functions.

The C++ backend must not depend on the generated C implementation.

## CMake integration

Require CMake 3.28 or newer for the C++ module target.

Expose generated module interface units through a `CXX_MODULES` file set:

```cmake
add_library(ptfkit_cpp)

target_sources(
    ptfkit_cpp
    PUBLIC
    FILE_SET CXX_MODULES
    FILES
        cpp/ptfkit.cppm
        cpp/aimrun2009.cppm
        cpp/beniaich2023.cppm
        cpp/cosby1984.cppm
        cpp/wang2012.cppm
)
```

Require C++20 and expose the installed target as:

```cmake
ptfkit::cpp
```

Consumers should be able to use:

```cmake
find_package(ptfkit CONFIG REQUIRED)

target_link_libraries(app PRIVATE ptfkit::cpp)
```

The generated CMake module file list must stay synchronized with the available source specifications.

## Tests

Generate C++ golden-case tests independently from the other targets.

Tests must cover both import styles:

```cpp
import ptfkit.wang2012;
```

and:

```cpp
import ptfkit;
```

Verify:

- scalar outputs;
- record outputs;
- exact preservation of spec-defined function names;
- exact preservation of spec-defined result class names;
- `ptfkit::<source>` namespace placement;
- source-specific imports;
- umbrella imports;
- golden-case numerical results using tolerances from the specification.

The C++ module target must remain independently buildable and testable through CMake.
