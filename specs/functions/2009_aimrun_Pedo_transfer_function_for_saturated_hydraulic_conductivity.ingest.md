# Paper Ingest Report: aimrun2009

## Source

- paper_md: `specs/papers/2009_aimrun_Pedo_transfer_function_for_saturated_hydraulic_conductivity.md`
- title: Pedo-transfer function for saturated hydraulic conductivity of lowland paddy soils
- authors: W. Aimrun, M. S. M. Amin
- year: 2009
- status: complete

## Extracted Function Specs

| function_name | spec_path | status | notes |
| --- | --- | --- | --- |
| calc_ptf_aimrun2009 | `specs/functions/calc_ptf_aimrun2009.md` | ready-for-implementation | Extracted from equation (10). |

## Blocked Function Specs

| function_name | spec_path | blocking_issues |
| --- | --- | --- |

## Developer Task

- Implement `calc_ptf_aimrun2009` in pure Rust and expose it through the existing Python API.
- Preserve keyword-only arguments, scalar behavior, NumPy broadcasting, and `out`.
- Do not use the paper MD directly during implementation.

## Tester Task

- Use the golden data embedded in `specs/functions/calc_ptf_aimrun2009.md`.
- Verify scalar, NumPy vectorized, broadcasting, and `out` behavior.
- Verify m/day to m/s conversion.

## Blocking Questions For Spec Owner

- None.
