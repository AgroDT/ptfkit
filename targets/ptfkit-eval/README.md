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

## Descriptive retention metrics

`summarize_retention_errors()` summarizes one already eligible cohort for one
candidate, target contract, and evaluation protocol. Input rows use suction
magnitudes in kPa and volumetric water content in volume fractions; the caller
must establish measurement compatibility and preserve prediction lineage before
constructing comparisons.

```python
from ptfkit_eval import RetentionComparison, summarize_retention_errors

summary = summarize_retention_errors(
    [
        RetentionComparison('source_a', 'sample_1', 10.0, 0.30, 0.32),
        RetentionComparison('source_a', 'sample_1', 100.0, 0.15, 0.18),
        RetentionComparison('source_a', 'sample_2', 10.0, 0.25, 0.24),
    ]
)
```

Each sample has equal total weight, distributed equally across its distinct
pressure points. Metrics include signed mean error (prediction minus
observation), MAE, RMSE, and weighted median absolute error. RMSE is the square
root of mean sample MSE, rather than mean sample RMSE. The weighted median uses
the same sample-balanced point weights; an exact half-weight split averages the
adjacent absolute errors. Per-sample metrics, source and sample counts, point
counts, and each sample's observed pressure extent remain explicit. Sample
identifiers are local to their source.

Empty cohorts, duplicate source/sample/pressure keys, invalid observations,
nonfinite values, and overflowing squared errors are rejected. Finite
predictions outside the physical range remain in the errors without clipping.
These are descriptive point-grid metrics. Log-pressure integration, prediction
intervals, parameter uncertainty, and model selection remain separate roadmap
work. An optional `profile_id` is local to the source and must be consistent
across every point of a sample. Summaries count known source-local profiles
and samples without profile identifiers separately.

## Maximal and common cohorts

`build_retention_cohorts()` accepts explicit
`RetentionCandidateComparisons` records containing a candidate identifier,
dataset identifier, protocol identifier, canonical `TargetSpec`, and eligible
comparison tuple. Every candidate must share the dataset, protocol, and exact
target contract. The caller must establish scientific compatibility upstream;
an equal protocol name alone cannot establish measurement equivalence.

Maximal cohorts retain all eligible points per candidate. Common cohorts take
the exact intersection of `(source_id, sample_id, suction_kpa)` across every
declared candidate, giving each candidate identical samples and pressure grids.
Observed values must agree exactly at shared keys; profile identity must agree
even where a shared sample has different pressure grids. No interpolation or
approximate identity matching occurs. Prediction values never choose cohort
membership. Common-cohort exclusions retain the original comparison and the
reason `point_not_shared_by_all_candidates`.

Empty candidates remain explicit and make every common cohort empty. An empty
cohort has `status == 'empty_cohort'` and `summary is None`, distinct from a
zero-error result. Results and comparisons use sorted deterministic order.

## Clustered metric confidence intervals

`bootstrap_retention_errors()` resamples whole sources or source-local profiles
with replacement. Every replicate draws the original number of groups;
repeated groups retain their full multiplicity and all their samples and
pressure points. Replicate metrics keep equal weight per sample occurrence,
so grouping does not replace the estimand with a mean of source means.

```python
from ptfkit_eval import ClusterBootstrapPlan, bootstrap_retention_errors

policy = ClusterBootstrapPlan(
    seed=20261023,
    minimum_groups=5,
    grouping='profile',
    missing_profiles='source',
    confidence_level=0.95,
    n_resamples=2000,
)
result = bootstrap_retention_errors(comparisons, plan=policy)
```

The seed and minimum group count are required. The value five above is an
example of a declared evidence gate, not a guarantee of statistical coverage.
If any sample lacks a profile, the explicitly requested `source` fallback
regroups the entire cohort by source. The default `reject` policy reports
`insufficient_evidence` with reason `missing_profile_ids`. Empty cohorts and
too few independent groups also return explicit reasons and no intervals.
Invalid records are rejected before applying the group-count gate.

The versioned method `cluster_percentile_linear_v1` computes two-sided
equal-tail percentile intervals for all four descriptive metrics. It uses
linear interpolation at `(n_resamples - 1) * probability`; the percentile
construction is described in the
[SciPy bootstrap documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
The implementation uses a local seeded Python `random.Random` generator and
canonical group order. Repeatability assumes the same Python and package
environment. Results preserve the full plan, effective grouping, group count,
and descriptive summary. This confidence algorithm uses the Python standard
library; the fitting layer uses the locked SciPy dependency.

These intervals concern aggregate error metrics. Prediction intervals,
parameter uncertainty, applicability domains, and observed pressure support
remain separate concepts. Paired candidate-difference intervals and nested
selection are separate protocols from this confidence API.

## Portable evaluation runs

`load_retention_dataset()` validates canonical JSON/YAML samples, features,
observations, physical target, method, reviewed states, quality flags, and
provenance. Source-local sample keys, feature names, observation identifiers,
and sample/pressure keys must be unique. Nonsynthetic records must identify a
source file whose filename and SHA-256 are declared in the dataset. Synthetic
records cannot be presented as a measured dataset. Canonical documents are
recursively read-only. Duplicate JSON/YAML fields, nonfinite values, cyclic
YAML aliases, and implicit YAML merges are rejected.

`load_retention_run_plan()` joins a byte-checksum-bound dataset and evaluation
plan, resolves candidates against the installed manifest, and registers a
protocol, explicit feature bindings, requested cohorts, and bootstrap policy.
The packaged `retention-dataset.schema.json` and `retention-run.schema.json`
describe these versioned contracts. Existing evaluation-plan documents remain
valid and independent of the run envelope.

`execute_retention_run()` records every candidate/observation decision and every
candidate/sample coverage row, including samples without targets. Numeric
features require compatible quantity, basis, method, particle boundaries, and
conditions. Unit conversions preserve raw and normalized values and use decimal
affine coefficients before checking computational bounds. Categorical bindings
require an exact category-system identifier and member. Unreviewed, estimated,
or unverified derived values remain exclusions. Reported applicability remains
explicitly `not_assessed` in this slice.

Evaluation plans now support `function_point` candidates with
`prediction: {kind: fixed_output, name: theta_10}`. Fixed support comes only
from the manifest's pressure condition. No nearest-pressure matching or
interpolation occurs. This makes the three public Gunarathna Set 1 outputs
executable under the same pipeline; targets at another pressure are excluded.
Fixed-output observation methods must match the manifest contract. Curve
adapters continue to evaluate the actual observed pressures. Composite execution
requires inputs only from members routed at the requested points.

`write_retention_run()` publishes a new directory containing original and
portable run plans, canonical input snapshots, the manifest snapshot,
eligibility and prediction traces, coverage/exclusion counts, cohorts, metric
intervals, and a Markdown report. A run manifest records package/Python versions,
Git revision and dirty state, evaluator source hash, input hashes, and each
artifact's size and checksum. Reports distinguish synthetic validation from
external validation. Existing output directories are rejected. Persisted
snapshots can be replayed through their portable `run-plan.json`.

CLI commands are available as `ptfkit-eval` or `python -m ptfkit_eval`:

```text
ptfkit-eval inspect <workbook> [--output <inventory.json>]
ptfkit-eval normalize <workbook> --mapping <mapping> [--output <summary.json>]
ptfkit-eval plan <evaluation-or-run-plan>
ptfkit-eval run <run-plan> --output <new-directory>
ptfkit-eval report <run-directory>
```

`normalize` emits a count-only summary. Full measurement artifacts are written
only from an explicitly supplied canonical dataset. See the self-contained
[synthetic example](../../evaluation/examples/synthetic_retention/README.md).

## Grouped selection and curve diagnostics

`diagnose_retention_series()` reports water contents outside [0, 1] and
increases with suction; it never repairs values. `diagnose_retention_run()`
keeps observed and predicted findings separate. Observed diagnostics include
blocked rows so problems remain visible; diagnostic presence never promotes
eligibility. Run directories retain `curve-quality.json` and finding counts.

`build_nested_group_folds()` uses only declared sample identities. It shuffles
sorted source or source-local profile groups with a registered seed and
balances group counts round-robin. Every outer group is tested once; each
inner partition uses only the corresponding outer training groups. Missing
profiles require explicit whole-roster source fallback. Insufficient groups
produce no partial validation assignment.

`select_fixed_retention_candidates()` compares an explicit candidate roster
using its exact common observation grid. The registered selection loss,
`log10_trapezoid_mse_v1`, integrates piecewise-linear squared errors over
log10 pressure and normalizes by the declared log span. Both domain endpoints
must be observed exactly. This differs from descriptive point-grid RMSE.
Each sample has equal selection weight. Coverage denominators include missing
targets and failed predictor bindings.

The selector separately locks an atomic candidate and a registered fixed
ensemble from inner validation, then assesses each locked strategy on outer
groups. Lexical candidate identifiers break exact ties. Reports include fold
provenance, inner scores, outer coverage and errors, selection stability, and
explicit insufficient evidence. They do not choose a final function by sorting
outer errors. Learned weights, boundaries, and gates require a separate nested
training implementation and are rejected by this fixed-candidate API.

An optional `selection` section in the run schema records every choice and
persists `selection.json`. The standalone synthetic example includes it.

## Retention approximation fitting

`retention_families()` registers distinct `van_genuchten_mualem_v1`,
`van_genuchten_m1_v1`, `brooks_corey_v1`, and
`clapp1978_gradual_air_entry_v1` equations. Their parameters use kPa-based
suctions/scales and volumetric volume fractions. The model variant and target
material basis remain explicit; the registry does not identify the convention
of workbook-supplied parameter sets.

`fit_retention_family()` fits one sample curve under a `RetentionFitPlan`.
Parameter bounds and interior initial values are required, with no data-derived
guessing. The first implementation requires nonoverlapping residual/saturated
water-content boxes to preserve physical ordering. It uses SciPy bounded TRF,
three-point numerical Jacobians, equal point weights, and deterministic
multistart seeds. Scale-parameter restarts are log-uniform. The plan records
minimum pressure span, evaluation/convergence limits, boundary/rank/condition
and competing-solution gates, and confidence settings. Rejected fits retain
attempt provenance and explicit failure reasons and never change family.

Accepted fits distinguish:

- family approximation error at measured pressures;
- local uncertainty intervals for that family's fitted parameters;
- confidence intervals for the fitted mean curve; and
- conditional prediction intervals for future observations under the fit.

The uncertainty method assumes local linearity and independent homoscedastic
residual errors; it uses residual degrees of freedom and Student-t critical
values. These assumptions are not evidence about external PTF prediction
accuracy. This is an approximate conditional calculation, not a replacement
for cluster metric confidence intervals or applicability assessment. The
covariance convention follows the local-linear construction described in
[SciPy curve fitting](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.curve_fit.html),
while bounded optimization uses
[SciPy least squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
`evaluate_retention_fit()` permits interpolation only within the observed
pressure extent. Parameters from different families must not be ranked against
one another.

Optional `approximations` run registrations fit each requested family to every
declared sample using only eligible observations, independently of PTF predictor
availability. Missing targets and scientific/numerical fit failures remain
explicit. `approximations.json` and a separate report section preserve this
evidence; reference fits never influence fixed PTF selection.

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

Source review may narrow a blocked rule without making it executable. For
example, the Sapozhnikov et al. (1988) workbook block is now known to contain
gravimetric water content and its case-only long-to-master source alias is
confirmed by 12 bijectively matching curves. The rule remains blocked because
the water scale and pressure convention are not yet supported by source-level
evidence. Partial review never promotes a rule to `confirmed`.

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
covers 206 declared retention sample rows and all five functions in the public
manifest. `calc_ptf_clapp1978` remains blocked by the unresolved USDA texture
crosswalk. Each of the three sand-only Gunarathna et al. (2019) functions has
51 populated raw candidates, but the workbook does not establish the required
2-millimetre upper boundary, dry-mass fine-earth basis, or sieve method.
`calc_ptf_vereecken1989` has 34 rows with all four raw inputs, but
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
