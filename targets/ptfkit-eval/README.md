# ptfkit-eval

`ptfkit-eval` provides reproducible external evaluation protocols for the
pedotransfer functions published by `ptfkit`.

The package is under active development. Its implemented contract covers
single-function and range-gated composite water-retention curve candidates.
`load_evaluation_plan()` validates JSON or YAML plans against the packaged
schema and resolves their function, output, unit, basis, and model-adapter
references against the installed `ptfkit` manifest.

`evaluate_candidate()` executes resolved direct-output and parameter-model
curves, converts the declared axis and target units through the manifest, and
retains the value and weight of every contributing composite member at every
axis point. The first built-in parameter adapter is `clapp1978_h_theta`. It
implements the power branch and the gradual-air-entry parabola from Clapp and
Hornberger (1978), including the published inflection wetness of 0.92.

```python
from ptfkit_eval import evaluate_candidate, load_evaluation_plan

plan = load_evaluation_plan(
    {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'clapp_sand',
                'kind': 'function_curve',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'log10',
                },
                'target': {
                    'quantity': 'volumetric_water_content',
                    'unit': 'volume_fraction',
                    'material_basis': 'mineral_soil',
                    'denominator_basis': 'bulk_volume',
                },
                'function': 'calc_ptf_clapp1978',
                'prediction': {
                    'kind': 'model_adapter',
                    'id': 'clapp1978_h_theta',
                },
            }
        ],
    }
)

curve = evaluate_candidate(
    plan.candidates[0],
    [0.1, 1.0, 10.0, 100.0],
    {'soil_texture': 'sandy_loam'},
)
```

## Workbook inspection

`inspect_workbook()` creates a read-only, checksum-bound structural inventory
before any dataset-specific interpretation is applied. It detects repeated and
multiline header blocks, formulas, merged cells, explicit missing-value markers,
and candidate sample-identifier columns without copying measurement rows into
the inventory.

```python
from ptfkit_eval import inspect_workbook, write_workbook_inventory

inventory = inspect_workbook('meta_v3.3.xlsx')
write_workbook_inventory(inventory, 'meta_v3_3.inventory.json')
```

## Dataset mappings

`load_dataset_mapping()` validates a JSON or YAML source-to-canonical mapping
against the packaged schema and its referenced workbook inventory. It rejects
checksum drift, omitted or unknown worksheets, changed dimensions or header
blocks, duplicate mapping identifiers, and an `active` status while scientific
blockers remain.

```python
from ptfkit_eval import load_dataset_mapping

mapping = load_dataset_mapping('../../evaluation/datasets/meta_v3_3.yaml')
```

The current `meta_v3_3` mapping is intentionally `draft_blocked`. Confirmed
layout facts are usable, but ambiguous water-content scales, pressure labels,
particle-size schemes, duplicate sample identifiers, and formula-derived
measurements remain explicit blockers or quarantines. Proposed aliases are not
silently treated as reviewed joins.

`profile_retention_workbook()` produces source-level evidence for the reviewed
`ОГХ` layout. It separates observations, fitted VGN parameters, and
unclassified rows and reports numeric shape without guessing whether a water
value is a fraction or percentage or whether an ambiguous pressure label means
a particular unit.

```python
from ptfkit_eval import profile_retention_workbook, write_retention_profile

profile = profile_retention_workbook('meta_v3.3.xlsx')
write_retention_profile(profile, 'meta_v3_3.retention-profile.json')
```
