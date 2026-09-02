---
title: Scientific verification policy
---

# Scientific verification policy

Golden cases describe the provenance and precision of reference evidence. They
do not contain author-tuned `rtol` or `atol` values. ptfkit separates source
uncertainty (what the publication supports) from numerical uncertainty (what a
legal `f64` implementation may introduce), then compiles both into one closed
acceptance interval shared by every generated target test.

## Verification kinds

An exact source value retains its nominal value and requires `f64` equality.
This is appropriate for integer results and authoritative, exactly stored
lookup rows:

```yaml
expected: {factor: 2.0}
verification:
  kind: exact
```

A calculated reference is evaluated from the validated semantic IR by the
target-independent oracle. It normally has no stored `expected` value:

```yaml
verification:
  kind: calculated_reference
```

A printed, rounded value records its source precision:

```yaml
expected: {water_content: 1.24}
verification:
  kind: published_rounded
  precision:
    decimal_places: 2
```

Significant-digit precision is an alternative, not an additional field:

```yaml
expected: {conductivity: 0.00340}
verification:
  kind: published_rounded
  precision:
    significant_digits: 3
```

Use an explicit closed interval when that is what the source reports. ptfkit
does not infer a confidence level or probability distribution:

```yaml
verification:
  kind: published_interval
  lower: 1.20
  upper: 1.30
```

An explicitly reported symmetric absolute uncertainty can also be retained:

```yaml
verification:
  kind: published_uncertainty
  value: 1.25
  absolute_uncertainty: 0.05
```

One case-level policy applies to all output fields by default. A record field
with different evidence can override it without repeating metadata for every
other field:

```yaml
verification: {kind: calculated_reference}
output_verification:
  reported_field:
    kind: published_rounded
    precision: {decimal_places: 1}
expected: {reported_field: 8.1}
```

`expected` is required for `exact` and `published_rounded`. Calculated
references derive it from the IR; intervals and uncertainties carry their own
source bounds.

## Published rounding intervals

Published values are interpreted as conventional rounding to the nearest
decimal quantum. Endpoints are included because publications usually do not
state how exact ties were resolved. For `decimal_places: d`, the source
interval is the nominal value plus or minus `0.5 * 10^-d`. Thus `1.24` at two
decimal places represents `[1.235, 1.245]`, and `-2.5` at one decimal place
represents `[-2.55, -2.45]`.

For a nonzero nominal value and `significant_digits: s`, ptfkit computes
`e = floor(log10(abs(value)))`; the quantum is `10^(e-s+1)`, and the same half-
quantum rule applies. Consequently `0.00340` at three significant digits has
source boundaries `0.003395` and `0.003405`. Significant digits for zero are
ambiguous and rejected; use decimal places or an explicit interval. Decimal
construction uses the 256-bit evaluator and rounds each final boundary outward
by one `f64` value, so decimal and scientific notation behave consistently near
binary conversion boundaries.

## High-precision oracle and numerical policy

The oracle uses `astro-float` at 256-bit precision with round-to-nearest,
ties-to-even. It consumes the same validated semantic IR used by code
generation and covers every currently legal operation: unary plus/minus,
addition, subtraction, multiplication, division, power, square root,
exponential, natural and base-10 logarithms, absolute value, minimum, maximum,
and typed record lookup. A future legal IR operation must be added explicitly;
there is no fallback to a production `f64` target.

The centralized numerical allowance is an interval around the correctly
rounded `f64` oracle result: eight adjacent representable values on each side
for elementary arithmetic and lookup expressions, or sixty-four on each side if
the function contains power, square root, exponential, or logarithmic
operations. Source intervals are expanded by the same number of representable
values at each endpoint. This accommodates operation ordering and normal libm
variation without introducing scale-dependent hand-tuned constants. Exact
verification receives no numerical expansion.

## What each verification level proves

Specification validity means the YAML satisfies the JSON Schema. Semantic
validity means it resolves into a complete target-independent IR. A source-
based golden case checks independently documented evidence from the
publication. A calculated reference checks that generated targets execute the
validated IR consistently.

Because the calculated oracle and production generators consume the same IR,
it does not independently prove that the publication was transcribed correctly.
That requires an exact lookup, published rounded value, published interval, or
published uncertainty. `corpus-report` therefore reports source-based coverage
separately from IR-derived implementation verification.

## Current corpus migration

The tolerance-field migration classified all 136 retained golden cases from
their case notes and scientific context. The 11 literal Clapp and Hornberger
Table 2 lookup rows are `exact`; the other 125 cases are explicitly documented
equation evaluations and are `calculated_reference`. No case required an
unresolved review state. The calculated cases no longer retain hand-entered
nominal outputs, eliminating duplicate values that were sometimes printed with
fewer digits than the semantic result. The migration found no case that had
failed the former generated target tests, but those old tolerance-based checks
were not treated as independent scientific evidence.
