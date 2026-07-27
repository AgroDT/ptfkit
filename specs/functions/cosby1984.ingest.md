# Paper Ingest Report: cosby1984

## Source

- paper_md: `specs/papers/1984_Cosby_A_Statistical_Exploration_of_the_Relationships_of_Soil_Moisture_Characteristics_to_the_Physical_Properties_of_Soils.md`
- title: A Statistical Exploration of the Relationships of Soil Moisture Characteristics to the Physical Properties of Soils
- authors: B. J. Cosby, G. M. Hornberger, R. B. Clapp, T. R. Ginn
- year: 1984
- status: ready-for-pilot

## Extracted Function Specs

| function_name | spec_path | status | notes |
| --- | --- | --- | --- |
| calc_ptf_cosby1984_univariate | `specs/functions/cosby1984.md` | ready-for-implementation | Extracted from Table 5 univariate regressions for a test pilot. |

## Blocked Function Specs

| function_name | spec_path | blocking_issues |
| --- | --- | --- |

## Developer Task

- Review `specs/functions/cosby1984.md`.
- Implement only this function as an end-to-end pilot.
- Do not use `specs/papers/*.md` directly during Rust or Python implementation.

## Tester Task

- Use the golden data embedded in `specs/functions/cosby1984.md`.
- Include scalar and NumPy vectorized cases.
- Include tolerances for log-transformed outputs and percentage outputs.
- Add `out` behavior cases for each output field.

## Blocking Questions For Spec Owner

- What DOI should be recorded before publication-quality docs?
- Should log-transformed output units be refined before publication-quality docs?
