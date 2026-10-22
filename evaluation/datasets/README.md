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
