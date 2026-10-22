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
axis point. The built-in parameter adapters are `clapp1978_h_theta` and
`vereecken1989_h_theta`. The latter evaluates the reduced van Genuchten model
with `m = 1` from predicted residual and saturated water content, alpha, and n.

```python
from ptfkit_eval import evaluate_candidate, load_evaluation_plan

plan = load_evaluation_plan(
    {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'vereecken_mean_soil',
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
                'function': 'calc_ptf_vereecken1989',
                'prediction': {
                    'kind': 'model_adapter',
                    'id': 'vereecken1989_h_theta',
                },
            }
        ],
    }
)

curve = evaluate_candidate(
    plan.candidates[0],
    [0.1, 1.0, 10.0, 100.0],
    {'sand': 52.14, 'clay': 10.93, 'carbon': 1.03, 'bulk_density': 1.466},
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

`normalize_retention_workbook()` then applies only `confirmed`
source-and-encoding rules. It converts water content and pressure to the
declared canonical units, preserves source cells, separates workbook-supplied
van Genuchten parameters, and emits an explicit exclusion for every observation
that is blocked or invalid. It verifies the workbook checksum and reconciles all
row-role counts with the bound retention profile. Cached sample identifiers are
also recomputed from the source and sample-number cells; disagreements remain
explicit exclusions. Confirmed source aliases and sample crosswalks can repair
identities only when the mapping carries reviewed evidence; proposed joins are
ignored.

```python
from ptfkit_eval import (
    load_dataset_mapping,
    normalize_retention_workbook,
    write_retention_normalization_summary,
)

mapping = load_dataset_mapping('../../evaluation/datasets/meta_v3_3.yaml')
result = normalize_retention_workbook('meta_v3.3.xlsx', mapping)
write_retention_normalization_summary(result, 'normalization-summary.json')
```

The summary writer deliberately records only row counts, exclusion reasons,
and blocker counts. It does not copy measurements from a workbook whose
redistribution status is unresolved.

`audit_predictor_workbook()` builds the predictor side of the eligibility
matrix directly from the installed ptfkit manifest. Candidate rows come only
from declared retention reconstruction blocks, so source-control rows cannot
leak into the sample cohort. Each in-memory value retains its raw cell,
function input, normalized value when compatible, binding state, and blockers.
Categorical values require either an exact value under a confirmed binding or a
confirmed category crosswalk. Numeric values require an exact measurement
contract; this first implementation does not guess units or apply implicit
conversions. Source-local measurement overrides are restricted to declared
sample-row ranges and retain their header evidence in lineage. The summary
separately reports full-contract and particle-size-boundary compatibility.

```python
from ptfkit_eval import (
    audit_predictor_workbook,
    load_dataset_mapping,
    write_predictor_audit_summary,
)

mapping = load_dataset_mapping('../../evaluation/datasets/meta_v3_3.yaml')
result = audit_predictor_workbook('meta_v3.3.xlsx', mapping)
write_predictor_audit_summary(result, 'predictor-audit.json')
```

The summary contains counts and reason codes only. The current workbook audit
covers 206 declared retention sample rows and both functions in the public
manifest. `calc_ptf_clapp1978` remains blocked by the unresolved USDA texture
crosswalk. `calc_ptf_vereecken1989` has 34 rows with all four raw inputs, but
their clay values are below 1 micrometre rather than the required below 2
micrometres. A source-local header identifies the correct below-2-micrometre
boundary for 12 Panina 2015 rows, but those rows do not contain all four raw
Vereecken inputs and their particle-fraction unit and mass basis remain
unresolved. The headed `ГС-PSD` schemes contain no 1-to-2-micrometre bin, so
they cannot supply the missing interval by exact summation. Walkley-Black
carbon equivalence and the bulk-density unit and method also remain blocked.

`exact_particle_size_cover()` accepts a direct interval or a gap-free,
non-overlapping partition with exact boundary inclusion. It deliberately
rejects using a below-1-micrometre fraction as a below-2-micrometre predictor.

`audit_retention_reconstruction_workbook()` validates declared wide retention
blocks against the long sheet without treating global value equality as sample
identity. It compares observation and fitted-parameter multisets, matches only
complete identifier groups to master curves, verifies confirmed crosswalks, and
reports proposed transforms separately. A rule is `normalization_ready` only
when values, complete-curve identity, reviewed transforms, and all confirmed
crosswalks agree. Numeric and categorical axes are retained distinctly.
Parameter-only sources declare their own sample-row ranges, and individual
wide blocks may declare source-evidenced scale or axis overrides. Proposed axis
overrides keep a rule out of normalization even when reconstruction is exact.
Sparse wide blocks
may also declare numeric missing-value markers. Sparse wide blocks and explicit
long-table nulls must declare their exact expected counts; an explicit null is
matched by sample and axis, so any drift fails the audit instead of silently
changing coverage. Populated wide cells absent from the long sheet are tracked
separately as explicit coordinate-level exclusions and never relabelled as
missing values.

```python
from ptfkit_eval import (
    audit_retention_reconstruction_workbook,
    load_dataset_mapping,
    write_retention_reconstruction_audit,
)

mapping = load_dataset_mapping('../../evaluation/datasets/meta_v3_3.yaml')
audit = audit_retention_reconstruction_workbook('meta_v3.3.xlsx', mapping)
write_retention_reconstruction_audit(audit, 'reconstruction-audit.json')
```
