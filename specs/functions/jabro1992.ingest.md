# Paper Ingest Report: jabro1992

## Source

- paper_md: `specs/papers/1992_Jabro_Estimation_of_saturated_hydraulic_conductivity_of_soils.md`
- title: Estimation of saturated hydraulic conductivity of soils from particle size distribution and bulk density data
- authors: J. D. Jabro
- year: 1992
- status: complete

## Extracted Function Specs

| function_name | spec_path | status | notes |
| --- | --- | --- | --- |
| calc_ptf_jabro1992 | `specs/functions/jabro1992.md` | ready-for-implementation | Extracted from equation (3). |

## Blocked Function Specs

| function_name | spec_path | blocking_issues |
| --- | --- | --- |

## Implementation Task

- Implement `calc_ptf_jabro1992` in pure Rust and expose it through the existing Python API.
- Preserve keyword-only arguments, scalar behavior, NumPy broadcasting, and `out`.
- Do not use the paper MD directly during implementation.

## Validation Task

- Use the golden data embedded in `specs/functions/jabro1992.md`.
- Verify scalar, NumPy vectorized, broadcasting, and `out` behavior.
- Verify cm/h to m/s conversion.

## Blocking Questions For Spec Owner

- None.
