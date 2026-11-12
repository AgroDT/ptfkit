---
title: Rosetta3 parameters
---

# Rosetta3 parameters

The bundled `specs/models/rosetta3/rosetta3.ptfm` contains parameters imported
from [USDA rosetta-soil](https://github.com/usda-ars-ussl/rosetta-soil), version
`0.3.3.dev2+g6b0e3902f`, commit `6b0e3902f8a145805d41b691dc36f8e69e898f2a`.
Retrieval recorded with the initial bundle: 2026-10-30. Upstream license:
CC0-1.0. Upstream attributes the trained parameters to Marcel Schaap and
Yonggen Zhang. The imported binary is redistributed under that upstream notice.

The YAML specification declares the artifact path, size, SHA-256, license,
network dimensions, parameter ordering, scales, and scientific calculations.
`codegen/scripts/import_rosetta3.py` imports a trusted local upstream checkout
and checks dimensions and member/layer/row ordering against those declarations.
The NPZ metadata uses pickle; run the importer only on a trusted checkout.

Use `mise run generate` and `mise run models:prepare`, followed by
`mise run verify`. Explicit model initialization shares immutable bundled
weights. Named public calculation methods are covered by the normal test suites;
`specs/models/rosetta3/reference.json` retains the upstream numerical cases.
