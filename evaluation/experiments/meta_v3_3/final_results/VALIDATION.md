# ptfkit v1.0 pointwise validation

- Full ptfkit-eval suite: 1110 passed (`python -m pytest targets/ptfkit-eval/tests -q`).
- Updated pointwise contracts: 5 passed after the final scoring-policy changes.
- Ruff lint and formatting pass for the eval component and all changed experiment files.
- The new scoring module passes ty. The component check with the repository root
  added to its import search path reports no type errors, but exits with an
  existing deprecated `contextmanager` return-annotation warning in
  `src/ptfkit_eval/artifacts.py:100`. The default component task additionally
  lacks the repository-root import path for existing experiment tests.
- Two temporary semantic mutations were rejected by the intended tests: ranking
  with held-out targets, and replacing equal sample weights with equal point
  weights. Both production changes were restored and the focused tests pass.
- Replayed 4708 original forecasts; all frozen historical analyses match exactly.
- All 43 Ksat functions retain their v1.0 RMSE, MAE, bias, factor fractions and
  observation counts within relative tolerance 1e-12.
- The 1701-point ledger is reconstructed from the pinned workbook and checked
  against its inventory. Every primary forecast matches an actual experimental
  sample, basis, pressure and observed water content. Duplicate predictions and
  reconstructed targets are rejected from primary scoring.
- Saved fit observations match the ledger, and saved fitted values are checked
  against evaluation of the saved curve parameters before plotting.
- All 281 diagnostic PNG pass the independently enumerated inventory, full image
  decoding and dimension checks: 131 PTF/ensemble/secondary diagnostics, 149
  approximation diagnostics, and one accuracy-coverage figure. See PNG-AUDIT.md.
- The diagnostic ZIP passes CRC checks. Private identities, observations,
  predictions, the complete image index and per-image hashes stay under
  `local/meta-final-v1_0-pointwise/`.

The source-held-out ensemble results do not demonstrate improvement over the
best individual at comparable or greater coverage for either water basis.
Volumetric coverage reaches 56.88%; gravimetric coverage reaches only 10.92%.
These limits and the different evaluation subsets remain central qualifications.
