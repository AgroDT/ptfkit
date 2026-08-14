# Implement the native C/C++ generation target

Add a new native generation target that produces independent header-only C and C++ implementations from the shared semantic IR.

## Target layout

Use a single distribution target for both languages:

```text
targets/
└── ptfkit-native/
    ├── CMakeLists.txt
    ├── cmake/
    ├── include/
    │   └── ptfkit/
    │       ├── c/
    │       │   └── ptfkit/
    │       │       ├── ptfkit.h
    │       │       ├── cosby1984.h
    │       │       ├── rawls1982.h
    │       │       └── ...
    │       └── cpp/
    │           └── ptfkit/
    │               ├── ptfkit.hpp
    │               ├── cosby1984.hpp
    │               ├── rawls1982.hpp
    │               └── ...
    └── tests/
        ├── c/
        └── cpp/
```

The extra `ptfkit/c` and `ptfkit/cpp` levels are intentional. They keep installed files namespaced under `ptfkit` while allowing each CMake target to expose a clean public include root.

A system installation should therefore look like:

```text
/usr/include/ptfkit/c/ptfkit/*.h
/usr/include/ptfkit/cpp/ptfkit/*.hpp
```

but consumers should write:

```c
#include <ptfkit/wang2012.h>
```

or:

```cpp
#include <ptfkit/wang2012.hpp>
```

depending on the CMake target they link against.

## C generation

Generate standalone header-only C implementations directly from the semantic IR.

Use `static inline` functions so every header is self-contained and does not require a separately compiled library.

Scalar outputs should return `double`:

```c
static inline double ptfkit_example(
    double sand,
    double clay
) {
    return /* generated expression */;
}
```

Record outputs should use generated C structs returned by value:

```c
typedef struct {
    double theta_s;
    double theta_fc;
    double k_sat;
} ptfkit_wang2012_result;

static inline ptfkit_wang2012_result ptfkit_wang2012(
    double sand,
    double silt,
    double clay,
    double bulk_density,
    double soil_organic_carbon,
    double altitude
) {
    /* generated intermediate variables */

    return (ptfkit_wang2012_result) {
        .theta_s = /* generated expression */,
        .theta_fc = /* generated expression */,
        .k_sat = /* generated expression */,
    };
}
```

Render mathematical operations using the standard C math library where required.

Generate one header per specification source plus an umbrella header:

```c
#include <ptfkit/ptfkit.h>
```

The umbrella header includes all generated source headers.

## C++ generation

Generate a separate header-only C++ implementation from the same semantic IR.

Do not wrap or call the generated C API. The C++ renderer should emit its own arithmetic expressions using native C++ facilities.

Generated declarations live in:

```cpp
namespace ptfkit {
    // ...
}
```

Use idiomatic C++ types and `<cmath>` functions:

```cpp
namespace ptfkit {

struct wang2012_result {
    double theta_s;
    double theta_fc;
    double k_sat;
};

[[nodiscard]]
inline wang2012_result wang2012(
    double sand,
    double silt,
    double clay,
    double bulk_density,
    double soil_organic_carbon,
    double altitude
) {
    const double soc_g_kg = 10.0 * soil_organic_carbon;
    const double value = std::log10(sand);

    return {
        .theta_s = /* generated expression */,
        .theta_fc = /* generated expression */,
        .k_sat = /* generated expression */,
    };
}

}
```

Generate one `.hpp` file per specification source plus:

```cpp
#include <ptfkit/ptfkit.hpp>
```

as the umbrella header.

## CMake interface

The native target is header-only.

Expose two independent interface targets:

```cmake
ptfkit::c
ptfkit::cpp
```

`ptfkit::c` exposes the C include root:

```text
<install-prefix>/include/ptfkit/c
```

`ptfkit::cpp` exposes the C++ include root:

```text
<install-prefix>/include/ptfkit/cpp
```

This makes both APIs appear to consumers under the same clean include namespace:

```text
<ptfkit/...>
```

while keeping the installed files physically separated.

Use standard CMake install/export support so consumers can use:

```cmake
find_package(ptfkit CONFIG REQUIRED)

target_link_libraries(app PRIVATE ptfkit::c)
```

or:

```cmake
find_package(ptfkit CONFIG REQUIRED)

target_link_libraries(app PRIVATE ptfkit::cpp)
```

Set suitable language requirements on the interface targets, for example C11 and C++17 unless implementation details require otherwise.

## Generation architecture

C and C++ are independent renderers:

```text
semantic IR
   │
   ├── C renderer
   │    └── *.h
   │
   └── C++ renderer
        └── *.hpp
```

Do not introduce a compiled C library and do not make the C++ implementation depend on the generated C implementation.

Both renderers may duplicate mathematical expressions. The specification and semantic IR remain the single source of truth.

## Tests

Each language has its own native test harness.

Generate golden-case tests from the specification for both C and C++ independently.

The C tests should validate:

- scalar results;
- record results;
- generated public headers;
- floating-point behavior required by the specifications.

The C++ tests should validate:

- scalar results;
- record result types and field names;
- namespace-qualified API;
- generated public headers;
- floating-point behavior required by the specifications.

Use the tolerances stored in the specification. Do not require bit-identical C and C++ results.

The native target must be buildable and testable through CMake without requiring Rust, Python, or R at consumer build time.
