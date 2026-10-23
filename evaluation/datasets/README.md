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
rows: 649 observations are normalized, 1,057 currently have blocked-rule
exclusions, one reviewed observation has an explicit missing water value, 48
have stale cached sample identifiers that disagree with the
source and sample-number cells, and 92 fitted van Genuchten parameters are held
in a separate in-memory table. Confirmed source aliases and sample crosswalks
are applied to canonical identities; proposed joins remain inactive. No row is
silently discarded. The summary contains counts only; the workbook and copied
measurement values remain outside version control while redistribution rights
are unresolved.


Primary-paper review unlocks 167 numeric observations from Bolotov et al. (2014)
and 56 from the orchard study by Makarychev et al. (2014). Both use volumetric
fractions and log10(kPa) axes despite the workbook's raw `pF` label. Their 16
complete curves require reviewed sample crosswalks; source case normalization
alone cannot repair lexical long-sheet sample numbering. See the
[source review](../../docs/src/contributing/ptfkit-eval-source-review.md).
These 223 volumetric observations accompany 426 reviewed gravimetric observations;
they do not establish predictor method compatibility or external PTF accuracy.


Additional primary evidence confirms Gumatov 1991 (190 observations), Gumatov
1992 (10), and the arboretum Makarychev 2018 block (96). The resulting six
normalization-ready rules retain 62 sample identities with 223 volumetric and
426 gravimetric observations. Gumatov's raw `mPa` label denotes MPa magnitudes
for that source only. Generic unresolved workbook labels remain blocked.

Panina's public thesis confirms volumetric-percent plots, but the long table
mixes sample identities and its saturation-axis replacement remains disputed.
Those observations remain excluded. The Makarychev 2014 thermal-property paper
reports hydrological constants rather than a verified pressure grid; no pressure
is assigned to those constants by assumption.
