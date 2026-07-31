# Paper Ingest Report Template

Use this when converting article-level Markdown from `specs/papers/*.md` into
function-level specs under `specs/functions/*.md`.

```markdown
# Paper Ingest Report: <source_key>

## Source

- paper_md: `specs/papers/<paper_file>.md`
- title: <title>
- authors: <authors>
- year: <year>
- status: complete | blocked

## Extracted Function Specs

| function_name | spec_path | status | notes |
| --- | --- | --- | --- |
| calc_ptf_example | `specs/functions/<apa_article_key>.md` | ready | TODO |

## Blocked Function Specs

| function_name | spec_path | blocking_issues |
| --- | --- | --- |
| calc_ptf_example | `specs/functions/<apa_article_key>.md` | Missing golden tests. |

## Implementation Task

- Implement only function specs with `status: ready-for-implementation`.
- Use `ptf-rust-core` for pure Rust scalar kernels.
- Use `ptf-python-bindings` for PyO3/maturin bindings and public wrapper
  compatibility.
- Do not use the paper MD directly during implementation.
- Do not implement blocked specs.

## Validation Task

- Build tests only from function-level specs and golden data.
- Verify scalar public API behavior.
- Verify NumPy/vectorized behavior when declared.
- Verify `out` behavior when declared.
- Verify units, tolerances, output field order, and edge cases.

## Blocking Questions For Spec Owner

- <question>
```
