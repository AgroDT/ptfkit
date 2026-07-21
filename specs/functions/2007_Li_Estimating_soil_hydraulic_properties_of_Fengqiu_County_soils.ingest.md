# Paper Ingest Report: li2007

## Source

- paper_md: `specs/papers/2007_Li_Estimating_soil_hydraulic_properties_of_Fengqiu_County_soils.md`
- title: Estimating soil hydraulic properties of Fengqiu County soils in the North China Plain using pedo-transfer functions
- authors: Y. Li, D. Chen, R. E. White, A. Zhu, J. Zhang
- year: 2007
- status: complete

## Extracted Function Specs

| function_name | spec_path | status | notes |
| --- | --- | --- | --- |
| calc_ptf_li2007 | `specs/functions/2007_Li_Estimating_soil_hydraulic_properties_of_Fengqiu_County_soils.md` | ready-for-implementation | Extracted from Table 6. |

## Blocked Function Specs

| function_name | spec_path | blocking_issues |
| --- | --- | --- |

## Developer Task

- Implement `calc_ptf_li2007` in pure Rust and expose it through the existing Python API.
- Preserve `Li2007PTFResult`, field order, keyword-only arguments, scalar behavior, NumPy broadcasting, and `out`.
- Do not use the paper MD directly during implementation.

## Tester Task

- Use the golden data embedded in `specs/functions/2007_Li_Estimating_soil_hydraulic_properties_of_Fengqiu_County_soils.md`.
- Verify scalar, NumPy vectorized, broadcasting, result field order, and `out` behavior.
- Verify cm/day to m/s conversion for `k_sat`.

## Blocking Questions For Spec Owner

- None.
