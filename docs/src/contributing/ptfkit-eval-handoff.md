# ptfkit-eval development handoff

## Purpose

This is a living handoff for the ongoing implementation of the
`ptfkit-eval` roadmap. It records completed work, verification evidence,
scientific blockers, and the exact continuation point so that a later session
can resume without reconstructing decisions from chat history.

Last updated: 2026-10-22.

## Acceptance target

The package is intended to evaluate every implemented ptfkit function against
every scientifically compatible observation that can be recovered from
`meta_v3.3.xlsx`. It must select atomic functions and registered ensembles only
through leakage-safe grouped validation, and it must fit and report supported
retention approximation families with distinct applicability, confidence,
prediction, and parameter-uncertainty intervals.

The detailed contract and roadmap remain in
`docs/src/contributing/ptfkit-eval-plan.md`.

## Current repository state

The public manifest contains five evaluation-ready contracts:

- `calc_ptf_clapp1978`;
- `calc_ptf_vereecken1989`;
- `calc_ptf_gunarathna2019_vwc10_set1`;
- `calc_ptf_gunarathna2019_vwc33_set1`;
- `calc_ptf_gunarathna2019_vwc1500_set1`.

The evaluator already provides a measurement-aware manifest loader, dataset
mapping schema, workbook inventory, retention profiler, rule-gated
normalization, wide-to-long reconstruction audit, predictor audit, range-gated
curve router, reduced van Genuchten adapter, Clapp-Hornberger adapter, and a
curve execution layer.

The real-workbook artifacts are checksum-bound to SHA-256
`1322bf65b1ca0130085015209858a443d1ee82a7e2ae69232321cd8ede361e68`.
The workbook remains external because redistribution rights are unresolved.

## Current dataset evidence

The retention profile accounts for 1,755 observations and 92 fitted van
Genuchten parameter values. Chestnova 2017 is the only normalization-ready
retention source and emits 130 canonical observations. All other observations
remain explicit exclusions rather than inferred values.

The predictor cohort contains 206 reviewed sample rows. The current manifest
contracts have the following raw-input coverage:

- Clapp: 89 complete texture values and zero eligible rows;
- each Gunarathna Set 1 function: 51 populated sand values and zero eligible
  rows;
- Vereecken: 34 rows with all four raw inputs and zero eligible rows.

The 51 sand-bearing rows are split across Sapozhnikov 1988 (12), Khaydapova
2001 (6), Shein 2011 (6), Makarychev-1 2014 (5), Makarychev-2 2014 (7),
Chestnova 2017 (10), and the parameter-only Kokareva 2007 block (5).
Thirty-four rows also contain bulk density.

## Sapozhnikov 1988 review

The following claims are now supported directly by workbook structure:

- the long label `1988_сапожников` and master label `1988_Сапожников` identify
  the same source and sample-number namespace;
- all 12 long-sheet sample groups match the 12 complete nine-point master
  curves bijectively;
- `Данные!W7` assigns the wide block the `W` encoding;
- `Данные!W1` defines `W` as mass-based water content, so the physical quantity
  is `gravimetric_water_content`.

The source is still blocked. The workbook does not distinguish percent from
fraction for this block, does not establish the source-specific pF convention,
and does not explain the first-axis `0.01` to `-1` replacement. It also does
not prove the 2,000-micrometre sand upper boundary, fine-earth dry-mass basis,
sieve method, bulk-density unit, or bulk-density method required for scoring.

The mapping, reconstruction audit, documentation, and regression tests encode
this partial review. The primary 1988 article was not recovered during the
initial search; secondary bibliographies identify it as an article in
`Pochvovedenie`, issue 10, pages 67-74.

## Verification status

Checks completed after the Sapozhnikov update:

- full `ptfkit-eval` test suite: 97 passed;
- focused mapping and reconstruction tests: 20 passed;
- Ruff for the changed mapping test: passed;
- Ruff formatting for all 25 `ptfkit-eval` Python files: passed;
- `git diff --check`: passed.

At the start of the current continuation, full component verification still
had three Ruff `PLR0917` diagnostics in `predictors.py` and 13 ty diagnostics
in `test_predictors.py`. A parallel work item is resolving those without
changing behavior or weakening checks. Update this section after integration.

## Immediate continuation order

1. Restore a green `ptfkit-eval` lint, format, typecheck, and test run.
2. Complete the Kokareva 2007 source search. If its parameter convention can be
   proven, register the exact fitted van Genuchten variant and expose the five
   parameter sets as reference curves with lineage. If not, retain the blocker
   and continue to the next source.
3. Implement the next self-contained evaluator slice selected from the roadmap,
   with synthetic independent-oracle tests before applying it to the workbook.
4. Regenerate every affected count-only workbook artifact and update this file,
   the main plan, and the package README.
5. Run the complete relevant verification suite and record exact commands and
   results here.

## Non-negotiable scientific rules

- Never infer units, bases, methods, or particle boundaries from value
  magnitudes alone.
- Never use measured held-out targets to choose a model, ensemble member,
  boundary, blend weight, or approximation family.
- Keep fitted-family approximation error separate from PTF prediction error.
- Keep confidence intervals, prediction intervals, fitted-parameter
  uncertainty, applicability domains, and validated axis ranges separate.
- Preserve raw-cell lineage for every normalized value and prediction.
- Keep ambiguous records visible as exclusions with machine-readable reasons.

## Worktree caution

The worktree contains intentional staged and unstaged changes from the ongoing
Gunarathna migration and dataset evaluation work. Do not reset or overwrite
them. Generated Gunarathna target files are expected changes. Inspect both
`git diff` and `git diff --cached` before editing overlapping files.

## Resume checklist

At the beginning of the next session:

1. Read `AGENTS.md`, the development guide, this handoff, and the main plan.
2. Run `git status --short` and preserve the existing worktree.
3. Read the latest verification results in this file.
4. Resume the first unfinished item in **Immediate continuation order**.
5. Update this handoff as decisions and verification results change.
