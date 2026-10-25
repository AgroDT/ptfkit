# Dataset inventory artifacts

This directory contains reviewed, versioned metadata for external evaluation
datasets. It does not contain the source workbooks or copied measurement rows.

`meta_v3_3.inventory.json` is a deterministic read-only structural inventory of
`meta_v3.3.xlsx`. Its SHA-256 digest binds the report to the exact source bytes.
The report records worksheet dimensions, nonempty and formula counts, cached
formula availability, merged ranges, explicit missing-value markers, inferred
header blocks, header cells, and candidate identifier columns. Header blocks
and identifier columns are heuristic findings that require review before they
become normalization rules.

Regenerate an inventory through the public API:

```python
from ptfkit_eval import inspect_workbook, write_workbook_inventory

inventory = inspect_workbook("/path/to/meta_v3.3.xlsx")
write_workbook_inventory(
    inventory,
    "evaluation/datasets/meta_v3_3.inventory.json",
)
```

The generated JSON stores only the source filename, never its machine-specific
absolute path.

`meta_v3_3.yaml` is the corresponding source-to-canonical mapping. It is bound
to the inventory filename, workbook checksum, byte size, worksheet dimensions,
detected header blocks, and `meta_v3_3.retention-profile.json`. The mapping
records confirmed row roles and physical semantics separately from proposed
aliases and unresolved scientific questions. Its `draft_blocked` status means
that no consumer may silently promote blocked encodings or quarantined rows
into an evaluation dataset.

The retention profile is deterministic, checksum-bound evidence grouped by the
exact source labels in the `ОГХ` worksheet. It records row and sample counts,
exact water and pressure encodings, numeric ranges, values at or below one,
values above one, pressure signs, fitted VGN parameter names, missing values,
and unclassified rows. It deliberately makes no unit, scale, or physical-basis
inference from those numeric patterns.

The mapping also contains one `retention_source_rules` entry for every profiled
source label and one observation rule for every exact water-pressure encoding
pair. A rule can be applied only when its status is `confirmed`, all physical
semantics are explicit, and its blocker list is empty. The first confirmed rule
covers the 2017 Chestnova source. Its ten sample identities are backed by exact
ordered 13-point curve matches to the master sheet, and its water scale is
supported by an exact factor-of-100 relationship plus the source documentation.
Five additional source rules are now supported by primary-source review;
all remaining rules stay blocked. Numeric magnitude is never used to infer
percent versus fraction.

Sapozhnikov et al. (1988) is the first partially reviewed blocked source. Its
case-only source alias is confirmed by a bijection between all 12 complete
nine-point curves and their sample numbers. The block control cell `Данные!W7`
and legend cell `Данные!W1` establish a gravimetric water quantity, but not
whether the stored values are fractions or percentages. Its pressure convention and the physical
meaning of the proposed first-axis replacement also remain blocked.

`meta_v3_3.reconstruction-audit.json` is the count-only result of applying the
declarative wide-block rules to the exact workbook bytes. The audit treats value
integrity and sample identity as separate claims. Its 27 rules account for all
1,755 long-form observations: 1,741 have exact master-sheet counterparts, and
14 Shvarov observations have no master counterpart. Twenty-one rules are
structurally reconstructable. Five more retain exact global point multisets but
broken cached identity groups: Khaydapova, Sadovnikova, Shein 2012, Badenko,
and Panina. The audit handles numeric and categorical axes, explicit long-table
nulls, numeric missing markers, coordinate-level exclusions, block-specific
scales and axes, and parameter-only sources. All 92 stored fitted-parameter
pairs are covered across Kokareva, Shein, and Panina. Six rules now combine
structural reconstruction, reviewed physical transforms and confirmed
crosswalks. Their counts and evidence are summarized below.

`meta_v3_3.predictor-audit.json` is the count-only, manifest-aware input
eligibility result for the same workbook bytes. Its candidate cohort contains
the 206 distinct master-sheet rows declared as samples by the retention
reconstruction rules; control rows are not inferred from numeric markers. The
current public ptfkit manifest contains five function contracts. The
`calc_ptf_clapp1978` texture input remains blocked by the unresolved USDA
crosswalk. The three sand-only Gunarathna et al. (2019) contracts each have 51
populated raw candidates in the master sand column, but all remain blocked:
the PTF requires the 50-to-2,000-micrometre dry-mass fraction of fine earth
measured by sieve analysis, whereas the workbook states only a
greater-than-50-micrometre lower boundary. The four `calc_ptf_vereecken1989`
inputs are bound to the master
sand, clay, organic-carbon, and bulk-density columns. Thirty-four rows contain
all four raw values, but their clay fraction is below 1 micrometre rather than
the required below 2 micrometres. The source-local header at `Данные!N210`
does establish the correct boundary for 12 Panina 2015 sample rows; the audit
records those rows separately, but none has all four raw Vereecken inputs and
their particle-fraction unit and mass basis remain unresolved. The headed
`ГС-PSD` schemes terminate at below 1 micrometre and do not provide a
1-to-2-micrometre bin for exact reconstruction. Walkley-Black carbon
equivalence and the bulk-density unit and method remain unresolved. The
artifact contains no raw predictor values.

Validate both artifacts together through the public API:

```python
from ptfkit_eval import load_dataset_mapping

mapping = load_dataset_mapping('evaluation/datasets/meta_v3_3.yaml')
```

Regenerate the retention evidence without copying measurement rows into the
artifact:

```python
from ptfkit_eval import profile_retention_workbook, write_retention_profile

profile = profile_retention_workbook('/path/to/meta_v3.3.xlsx')
write_retention_profile(
    profile,
    'evaluation/datasets/meta_v3_3.retention-profile.json',
)
```

Run the rule-gated normalizer and regenerate the non-sensitive accounting
summary without writing measurement values to the repository:

```python
from ptfkit_eval import (
    load_dataset_mapping,
    normalize_retention_workbook,
    write_retention_normalization_summary,
)

mapping = load_dataset_mapping('evaluation/datasets/meta_v3_3.yaml')
result = normalize_retention_workbook('/path/to/meta_v3.3.xlsx', mapping)
write_retention_normalization_summary(
    result,
    'evaluation/datasets/meta_v3_3.normalization-summary.json',
)
```

To write a private canonical volumetric dataset, use `ptfkit-eval export` with
`--mapping`, `--dataset-id`, `--material-basis` and an explicit `--output` path.
Use `unspecified` for an unreviewed material basis. The current workbook exports
549 volumetric observations and accounts separately for 487 gravimetric rows;
no mass-to-volume conversion is inferred. Export preserves cell lineage and
does not fill predictors or establish scoring eligibility. Output contains
measurements and belongs outside versioned summaries, for example under `local/`.

Regenerate the wide-to-long reconstruction evidence through the same bound
mapping:

```python
from ptfkit_eval import (
    audit_retention_reconstruction_workbook,
    load_dataset_mapping,
    write_retention_reconstruction_audit,
)

mapping = load_dataset_mapping('evaluation/datasets/meta_v3_3.yaml')
audit = audit_retention_reconstruction_workbook('/path/to/meta_v3.3.xlsx', mapping)
write_retention_reconstruction_audit(
    audit,
    'evaluation/datasets/meta_v3_3.reconstruction-audit.json',
)
```

Regenerate the manifest-aware predictor evidence without copying raw values:

```python
from ptfkit_eval import (
    audit_predictor_workbook,
    load_dataset_mapping,
    write_predictor_audit_summary,
)

mapping = load_dataset_mapping('evaluation/datasets/meta_v3_3.yaml')
audit = audit_predictor_workbook('/path/to/meta_v3.3.xlsx', mapping)
write_predictor_audit_summary(
    audit,
    'evaluation/datasets/meta_v3_3.predictor-audit.json',
)
```

For the reviewed workbook bytes, the summary accounts for all 1,847 populated
rows: 1,036 observations are normalized, 644 currently have blocked-rule
exclusions, one reviewed observation has an explicit missing water value, 48
have stale cached sample identifiers that disagree with the
source and sample-number cells, and 92 fitted van Genuchten parameters are held
in a separate in-memory table. Six ambiguous sample matches and 17 unreviewed
pressures remain explicit exclusions. Three miscopied table-statistic pairs are
excluded as non-observations. Confirmed source aliases and sample crosswalks
are applied to canonical identities; proposed joins remain inactive. No row is
silently discarded. The summary contains counts only; the workbook and copied
measurement values remain outside version control while redistribution rights
are unresolved.

The original Vasyukov 2012 figure resolves volumetric fractions for 28 rows but
does not identify the unit behind its logarithmic potential axis. These rows
remain blocked. Shvarov's source additionally requires observation-provenance
review: matching original-author table vectors describe hysteresis moisture
differences, which cannot be released as absolute retention water contents merely
by confirming physical units. The 119 source-labelled rows retain this blocker.
The 30 Shein 2012 rows also retain it: the original study describes retention
curves reconstructed from measured constants and inferred pressures. Original
figure/table review must identify any independent measurement subset before
release. In total, 149 source-labelled rows require this provenance review.
The source-review document includes a count-based queue for all 15 blocked
physical source rules and their 692 affected rows.


Primary-paper review unlocks 167 numeric observations from Bolotov et al. (2014)
and 56 from the orchard study by Makarychev et al. (2014). Both use volumetric
fractions and log10(kPa) axes despite the workbook's raw `pF` label. Their 16
complete curves require reviewed sample crosswalks; source case normalization
alone cannot repair lexical long-sheet sample numbering. See the
[source review](../../docs/src/contributing/ptfkit-eval-source-review.md).
The current 549 volumetric observations accompany 487 reviewed gravimetric observations;
they do not establish predictor method compatibility or external PTF accuracy.


Additional primary evidence confirms Gumatov 1991 (190 observations), Gumatov
1992 (10), and the arboretum Makarychev 2018 block (96). The resulting six
normalization-ready rules retain 62 sample identities. Five partially reviewed
sources add 387 observations and 47 sample identities. Gumatov's raw `mPa` label denotes MPa magnitudes
for that source only. Generic unresolved workbook labels remain blocked.

Panina's public thesis confirms volumetric-percent plots. Exhaustive row decisions
release 116 uniquely matched positive-pF observations, while four ambiguous pairs
and 12 saturation-axis rows remain excluded. Badenko's original experimental table
confirms volumetric fractions and kPa magnitudes: 106 unique observations are
released and two ambiguous sample matches remain excluded. Umarova's original
author abstract confirms volumetric-percent/pF plots, releasing 81 unique retained
observations. Missing and omitted wide-sheet points remain unreleased.

Sadovnikova and Smagin's original 2011 paper additionally confirms dry-mass
percent water content and logarithmic kPa magnitudes. It releases 61 unique
experimental points; two unsupported chernozem pressure placeholders remain
excluded. Four master identities represent experimental repeats of two soils
and do not establish four independent samples. Gravimetric water/dry-soil ratios
may exceed one, as the original peat observations demonstrate.

Moiseev et al. (2018), Table 2, supplies 23 exact experimental volumetric-percent
and pF pairs across three master identities. Three Mann-Whitney U/U-critical
pairs were copied into the workbook as observations and are explicitly excluded
as `non_observation_table_value`; three unsupported saturation-axis rows remain
excluded too. PSF calculated curves are not treated as independent measurements.
The profiler's 1,755 observation-labelled input rows include these three
misclassified statistics; the original workbook bytes and classification counts
remain auditable while normalization records their exclusion explicitly.

The optional `retention_row_reviews` policy accounts for every observation in each
participating source. Its physical rule must require row review. Every released
row is rechecked against one unique original master point, its canonical identity,
and its axis, water and identity evidence cells. Proposed axis replacements are
inactive. Complete-curve reconstruction remains blocked for these five sources.

The Makarychev 2014 thermal-property paper
reports hydrological constants rather than a verified pressure grid; no pressure
is assigned to those constants by assumption.

`meta_v3_3.quality-summary.json` reports counts without measurements. Regenerate it
with the component environment and `audit_meta_v3_3_quality.py --workbook
local/meta_v3.3.xlsx` from the repository root. At zero monotonicity tolerance,
20 of 59 reviewed volumetric curves contain 32 adjacent increases with suction;
none has values outside volumetric bounds. These diagnostics preserve all values
and establish no scoring eligibility. The 50 gravimetric curves require their own
physical checks and are excluded from this volumetric diagnostic.
# Canonical curve and predictor readiness join

`audit_meta_v3_3_readiness.py` joins canonical curve identities to the reviewed
predictor audit by exact source and sample identifiers, requiring one master
row and identical workbook bytes. It reports counts only; ambiguous identities
and unmatched rows remain explicit. Predictor readiness is not scoring
eligibility and does not create predictor features in the canonical export.

All 59 exported curve identities match exactly, but no current public function
has eligible inputs on this cohort. Clapp has 24 complete raw texture inputs,
all blocked by classification compatibility; the other 35 lack texture. Every
one of these 59 curves lacks at least one input for Vereecken, and all 59 lack
the bound sand input for the three Gunarathna functions. Consequently, resolving
particle-size metadata for the 51 populated sand rows elsewhere in the workbook
would not unlock these 59 curves by itself. New source-backed inputs or another
reviewed predictor/target cohort are required. See the count-only
`meta_v3_3.readiness-summary.json` and `meta_v3_3.fit-policy-comparison.json`.

The export's target material basis is still `unspecified`; resolving predictor
availability does not resolve that target-contract gate. A source-backed
classification/material review and compatible predictor values are required
before any external PTF score can be produced for a retained subset.

The subsequent source audit supplied a separate reviewed Panina subset:
six mineral gray forest horizons with directly published USDA-compatible
classes. This external overlay does not reinterpret the global workbook
category binding. Its 56 eligible measured points now have a descriptive
Clapp check; see `meta_v3_3.clapp-source-review.json`,
`meta_v3_3.clapp-pilot-summary.json`, and
`evaluation/experiments/panina_clapp/README.md`. Six other Panina horizons have
the source-reported class silt, which the Clapp contract does not support.

The complete implemented-function inventory is
`implemented-function-coverage.json`. The associated
`meta_v3_3.function-readiness-matrix.json` keeps every implemented function
visible across the six source partitions in the volumetric export, with
contract gaps and raw predictor blockers. These partitions are reporting
strata, not assumed independent experiments. Neither artifact grants scoring
permission. Reproduction commands are in
`evaluation/experiments/catalog_coverage/README.md`.

`wosten2001.measurement-review.json` records the source review that added the
Staring class-parameter function to the manifest. Its original Dutch classes
have no reviewed raw workbook binding; its inclusion does not unlock this
dataset or authorize a texture crosswalk.

Canonical export now accounts for all 1,036 normalized observations in two
separate datasets: 549 volumetric observations in version 1 and 487 gravimetric
observations in version 2. The count-only checksums and target contracts are in
`meta_v3_3.canonical-exports-summary.json`; raw exports remain local. The
gravimetric export preserves 20 dry-mass ratios above one and does not apply a
density conversion. Its full-catalog raw readiness matrix is
`meta_v3_3.gravimetric-readiness-matrix.json`.

The primary-source review in `dharumarajan2019.measurement-review.json` preserves
an unresolved water-content denominator. The legacy gravimetric output label
does not authorize measurement-contract migration or evaluation on the newly
exported mass-basis data.

`beniaich2023.measurement-review.json` records the successful contract migration
for 11 implemented linear regressions. The current inventory and readiness
matrices include 17 manifest functions. The exact-pressure audit in
`meta_v3_3.fixed-pressure-support.json` separates output pressure support from
predictor readiness. None of the mass observations is exactly at 33 or
1500 kPa. Nearby pressures and capillary saturation are not assigned invented
fixed-pressure targets. Reproduction is documented in the catalog coverage
experiment directory.


The Saxton2006 checkpoint adds `saxton2006.measurement-review.json` and
`hybras_v1.saxton-preflight-summary.json`. Current metadata coverage is 18 of
146 implemented functions; 128 remain omitted. The HYBRAS audit executes 607
numerically eligible raw predictor rows, of which 604 pass curve checks, without
claiming target compatibility or external accuracy. The separate
`cosby1984.measurement-review.json` retains unresolved logarithmic-contract and
application-protocol questions. Raw source data remain local.


`hybras_v1.clapp-validation-summary.json` records the first real HYBRAS native
external accuracy run: 378 source-reviewed mineral horizons, 144 profiles,
22 source groups and 2,882 observations. The crosswalk and horizon decisions
are checksum-bound in each local run's `review.json`. Fixed Clapp RMSE is
0.0737533 volume fraction, with profile-bootstrap 95% metric CI
[0.0673851,0.0806099]. This is not final function/ensemble selection or
individual prediction uncertainty. See the HYBRAS experiment README for
source and wheel replay commands and independent numerical verification.


`hybras_v1.controlled-pressure-summary.json` and
`hybras_v1.controlled-pressure-support.json` describe a separate source-reviewed
view of 1,465 observations from 254 horizons. Exact original-controlled regimes
are recoverable from explicit method lists, original-unit comments and matching
wide/long observations: 254 points each at 10, 33 and 1500 kPa. This removes a
pressure-coordinate blocker, not material, predictor or scoring blockers.
Historical datasets, fits and Clapp results remain bound to their original
hashes. See the HYBRAS experiment README for source and installed-wheel replay.


The current Gunarathna2019 checkpoint raises complete manifest coverage to
26 of 146 implemented functions. `gunarathna2019.measurement-review.json`
corrects the undisturbed bulk-soil retention target separately from fine-earth
texture aliquots and records the remaining predictor-method review.
`nebel2010.measurement-review.json` identifies a 100-point spatial grid and an
exact shared Parfitt citation across two HYBRAS source IDs. Neither reference-pair
hashes nor profile counts establish independent validation replicates. The
controlled-pressure support audit now checks 15 volumetric prediction outputs;
its original data view and historical runs remain unchanged.
