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
intervals, parameter uncertainty, and model selection use the separate
protocols described below. An optional `profile_id` is local to the source and must be consistent
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

## Paired candidate differences

`bootstrap_paired_retention_errors(left, right, plan=...)` accepts two
`RetentionCandidateComparisons` on an already identical source/sample/pressure
grid. Dataset, target, protocol, observations, and profile identities must
agree. Unequal grids fail rather than being silently intersected. Invalid
records fail before evidence gates. Every bootstrap replicate draws the same
whole sources or source-local profiles for both candidates, retaining cluster
multiplicity and equal sample-occurrence weights.

Differences are left minus right for ME, MAE, RMSE, and median absolute error.
Nonlinear RMSE and median differences are taken after calculating each
candidate's replicate metric; they are not metrics of residual differences.
`paired_cluster_percentile_linear_v1` uses the existing registered bootstrap
seed, group-count gate, confidence level, replicate count, and explicit
whole-roster source fallback. Empty cohorts or insufficient groups/profile
evidence retain reasons and no intervals.

Optional run `paired_comparisons` registrations declare pairs before execution:

```json
{
  "method": "paired_cluster_percentile_linear_v1",
  "left_candidate_id": "clapp",
  "right_candidate_id": "vereecken",
  "cohort": "run_common"
}
```

Run comparisons use the exact common cohort across every run candidate,
including empty ones, even when only maximal descriptive cohorts were requested.
They persist `paired-comparisons.json` and a report table. Negative MAE/RMSE/
median differences favor the left candidate on this cohort; signed ME is a bias
contrast, not an accuracy ordering. Intervals are unadjusted descriptive
comparisons, not simultaneous inference across many pairs, nested strategy
uncertainty, or a candidate-selection procedure. No model is retrained or
selected inside a replicate. Full prediction/input lineage remains in the run
decisions, and each paired artifact retains its exact comparison rows.

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
or unverified derived values remain exclusions. Literature-reported applicability
remains explicitly `not_assessed`; the optional empirical input diagnostic below
is a separate assessment.

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

## Learned convex ensemble selection

`select_learned_retention_candidates()` implements the narrowly registered
`nested_convex_pair_selection_v1` protocol. A `LearnedSelectionPlan` contains
a normal fixed candidate/fold/loss contract and one or more `ConvexPairPlan`
registrations. Each registration names exactly two atomic curve candidates,
a unique ensemble ID, a minimum usable training-group count, and a positive
minimum mean squared member contrast. Fixed range-gated composites may compete
against these trainable ensembles but cannot serve as trainable members.
Fixed-pressure point outputs cannot be trainable curve members.

The prediction is `w * left + (1 - w) * right`, with one constant weight
constrained to [0, 1]. In each inner training partition, an analytic quadratic
minimizer fits w using the registered exact-endpoint, sample-balanced
log-pressure trapezoid MSE. No observation outside that training partition
contributes to the fit. Validation losses select an atomic candidate and an
ensemble separately, with lexical ID ties and the declared coverage threshold.
The selected learned ensemble is refitted on all outer training groups before
it predicts the untouched outer test groups. Outer errors assess the locked
strategies; they do not choose a final model.

The fixed roster's common observation grid is used for every competitor.
Missing targets remain in coverage denominators. Insufficient training groups,
insufficient coverage, nonfinite training objectives, and an unidentifiable
weight remain explicit failures. The squared-contrast gate uses a strict
greater-than comparison; weights 0 and 1 are valid constrained optima.
No arbitrary default weight, alternative member, or post-refit fallback is
substituted on failure. Training samples, roles, coverage, fitted weights,
training losses, inner predictions/scores, outer refits/predictions, and
strategy stability are retained.

Optional run `learned_selection` contains `method`, `fixed_selection` (the same
schema as a fixed selection registration), and `ensembles`. Each ensemble
declares `method: constant_convex_pair_log_pressure_v1`, `id`,
`left_candidate_id`, `right_candidate_id`, `minimum_training_groups`, and
`minimum_mean_squared_contrast`. The synthetic retention example contains a
complete executable registration. Runs write `learned-selection.json` and a
dedicated report section. Ordinary candidate scoring, standalone conformal
intervals, and fixed selection remain independent of this registration.

This convex protocol does not learn pressure boundaries, nonlinear
input gates, publication formulas, or a final deployment model. It does not
estimate weight uncertainty or full selection-process confidence intervals.
Conformal calibration of trained ensembles is not integrated.

Optional `learned_selection.empirical_domains` uses the same nested-domain
method, group gate, and all-member rule as fixed selection. The separate
`diagnose_learned_applicability()` API inspects every inner candidate and only
the already locked outer choices. A trainable pair combines its constituents'
training-input envelopes with explicit `left:`/`right:` member identities,
including a zero-weight constituent. Its conservative labels depend on neither
fitted weight nor observed targets. Inner/outer predictions already retained
by learned selection supply stratum errors; no new weights are fitted and
no model is reselected. `learned-applicability.json` and a report section retain
training bounds, labels, common-grid errors, and coverage. Metric intervals
remain conditional descriptive summaries, not selection-process uncertainty.
`fixed_selection.empirical_domains` inside a learned registration is rejected;
register the learned diagnostic at `learned_selection.empirical_domains`.

## Learned hard-switch boundaries

`nested_two_curve_selection_v1` extends learned selection to a mixed roster of
constant convex pairs and `HardSwitchGridPlan` registrations. The older
`nested_convex_pair_selection_v1` remains convex-only. Each hard switch declares
`method: training_grid_hard_switch_v1`, two atomic curve IDs, at least two
distinct positive `boundary_grid_kpa` values, exact `boundary_member` ownership,
`minimum_training_groups`, and a positive `minimum_loss_gap`. Every boundary
must lie strictly inside the registered exact-endpoint loss domain.

Every grid value is scored on the same complete usable training sample roster
with the registered log-pressure MSE. Boundary search uses training targets
only; no interpolation, nearest-pressure routing, or predictor-dependent gate
is introduced. Fits retain every boundary score and require the best-versus-
second-best loss gap to exceed the declared threshold strictly. Failed evidence
or an indistinguishable grid keeps `unidentifiable_boundary` and no boundary.
The loss-gap gate is not a significance test or boundary confidence interval;
identification is only relative to the registered discrete grid.

The existing inner-choice/outer-refit lifecycle, coverage denominators, atomic
baseline, fixed-composite competition, and learned applicability diagnostics
also apply to switches. `learned-selection.json` and its report retain fitted
parameters by kind. `diagnose_learned_switch_seams()` evaluates both members at
the locked outer-training seam using test predictors only and writes
`learned-seams.json`. Member contrasts imply jumps only for curves continuous
at that boundary. No seam diagnostic changes selection or eligibility.
See the [synthetic hard-switch run](../../evaluation/examples/synthetic_hard_switch/README.md)
for a complete registration and portable CLI example.

## Held-out curve quality and strategy assessment

`selection_prediction_frames()` exposes fixed and learned predictions with
explicit protocol, strategy, outer/inner fold, training/holdout groups,
candidate, complete held-out sample roster, and stored assessment status.
Fixed frames use the exact selection-roster common cohort; learned frames
use their retained validation/test predictions. Frame identities and point
keys must be unique, all predictions must belong to the holdout roster, and
learned fit provenance must match the declared training partition.

`diagnose_selection_curves()` reports volumetric bounds and adjacent monotonicity
findings for every inner candidate and locked outer choice. Each sample stays
separate by protocol/fold/strategy/candidate, including explicit `no_predictions`
records for missing targets, inputs, fits or choices. Observed values are not
read. The diagnostic never clips, repairs, excludes or reselects predictions.
It describes the retained grid, not continuity or monotonicity between points.
Runs retain `selection-curve-quality.json` and scoped finding counts in the
report. Repeated inner holdouts are diagnostic records, not independent
replications of the experiment.

`assess_selection_strategies()` implements
`locked_outer_strategy_descriptive_v1` separately for fixed and learned
selection. Only already locked outer predictions inside the registered
selection-loss domain enter its error metrics. Each declared sample must
belong to exactly one outer fold per strategy. Retained rows must reproduce
the stored per-sample validation losses. Samples without targets remain in
coverage denominators; missing exact endpoints remain failed losses. Rows
outside the registered pressure domain are counted explicitly and excluded
from these strategy metrics.

Atomic and ensemble strategies retain maximal and exact common point cohorts,
sample-balanced descriptive ME/MAE/RMSE/median errors, full fold/choice lineage,
coverage, selection stability, and common-cohort atomic-minus-ensemble metric
differences. These strategies may choose different candidates in different
folds; no final function or ensemble is selected by these summaries. Negative
absolute-error differences favor the atomic strategy on the common cohort;
signed ME differences describe bias. Incomplete outer folds retain partial
descriptive rows but no complete mean outer loss or complete strategy status.
Empty cohorts remain distinct from zero error.

`strategy-assessment.json` and the report explicitly record
`not_estimated_crossfit_dependency` for uncertainty. No bootstrap interval
from fixed cross-fit rows is presented as uncertainty of the selection
procedure: overlapping training sets, refitting and candidate choice would
need a separate, justified inferential protocol. Ordinary fixed-candidate
metric/paired intervals and conformal intervals retain their own scopes and
assumptions. Both synthetic selection examples emit the new diagnostic files.

## Whole-group selection retraining sensitivity

`resample_selection_procedure()` repeats the registered selection/fitting
procedure under a `SelectionResamplingPlan`. Optional run registrations use:

```json
{
  "method": "whole_group_bootstrap_retraining_sensitivity_v1",
  "protocol": "learned",
  "seed": 20261023,
  "n_resamples": 16,
  "minimum_groups": 8
}
```

The referenced fixed/learned selection protocol must be registered in the run.
`minimum_groups` gates the original independent-group roster. Each draw samples
the original number of whole groups with replacement. The original effective
source/profile grouping, including its explicit source fallback, is frozen
before drawing. Original identities are retained for grouping; occurrence IDs
only distinguish repeated samples/observations. Thus copies of a group cannot
enter different folds or inflate independent training-group evidence. Unequal
group sizes retain equal weight per sample occurrence.

Every draw rebuilds the registered folds using their existing seed and reruns
candidate selection, inner training, outer refitting and outer assessment.
Eligibility and fixed PTF predictions are cached; they contain no learned
preprocessing in the currently supported contracts. Independent approximation
fitting and descriptive reports are not part of the chosen prediction rule.
Draws with insufficient distinct groups, missing coverage or failed fits remain
explicit, with no retries or conditioning on successful draws.

`selection-resampling.json` retains multiplicities (including zero), original
group membership, occurrence-to-original sample/observation maps, derived data
checksums, and complete repeated selection evidence. Internal occurrence views
are not independently published canonical datasets; replay starts from the
parent run snapshots and registered draw law. A local seeded generator and
canonical ordering preserve reproducibility without changing global RNG state.
The report gives attempted/complete counts and retains
`not_estimated_retraining_sensitivity_only`. No confidence level or inferential
interval is accepted by this sensitivity protocol. See the
[synthetic retraining run](../../evaluation/examples/synthetic_retraining/README.md).

The [inference qualification note](../../docs/src/contributing/ptfkit-eval-inference.md)
records primary statistical sources, the unequal-group estimand issue, and
the still-unfinished requirements for full selection-process confidence
intervals. Retraining trajectories provide infrastructure and evidence for
that work; they do not replace it.

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

## Grouped PTF prediction intervals

Optional `prediction_intervals` run registrations use
`fixed_group_max_split_conformal_v1` for a predeclared fixed candidate.
Explicit training, calibration, and test source/profile groups must be
disjoint. Each calibration group must have every registered pressure for
every declared sample. Its score is the maximum absolute residual over that
whole grid. The half-width is the score at exact rank
`ceil((G + 1) * confidence_level)` among G calibration groups. Incomplete
grids, too few groups, or a rank exceeding G return `insufficient_evidence`.
There is no interpolated quantile or implicit group removal.

Test forecasts use predictors and the registered pressure grid without test
observations. Whole-group exchangeability and a fixed prediction rule and
observation design are required for simultaneous group/grid coverage; this
does not establish conditional coverage for every soil type. Intervals are
not clipped. These PTF intervals remain separate from metric confidence
intervals, fitted-family conditional uncertainty, and applicability domains.
Runs retain `prediction-intervals.json` and a dedicated report section.
The [standalone synthetic example](../../evaluation/examples/synthetic_conformal/README.md)
includes hand-calculated scores, finite-rank bounds, and an unlabelled test source.

## Empirical input domains and composite seams

`assess_retention_applicability()` implements the versioned descriptive
`training_input_envelope_v1` protocol. An `EmpiricalDomainPlan` registers one
candidate, disjoint training/test source or source-local profile groups, and
a minimum count of training groups with complete compatible inputs. There is
no implicit profile fallback. The optional `empirical_domains` run section uses
the same fields:

```json
{
  "method": "training_input_envelope_v1",
  "candidate_id": "clapp",
  "training_groups": [["source_a", ""], ["source_b", ""]],
  "test_groups": [["source_c", ""]],
  "minimum_training_groups": 2,
  "grouping": "source"
}
```

Only registered training predictors establish inclusive numeric minima/maxima
in manifest units and observed categorical names. Incomplete training vectors
remain explicit exclusions; no partial vector supplies a bound. Each composite
member has separate bounds, complete training-sample lineage, group counts,
and test-input assessments. The diagnostic does not access observations or
execute the PTF. Test inputs never expand its envelope. Too few usable training
groups produce `insufficient_evidence`; incompatible test inputs retain their
binding reasons. Constant training predictors have equal inclusive bounds.

`inside` describes marginal input support only. It does not establish joint
support, similarity to the publication's development population, accuracy,
uncertainty coverage, or validated pressure support. Results do not change
eligibility, selection, or prediction intervals. These explicitly registered
roles are separate from the optional fold-specific diagnostic below. Runs retain
`empirical-domains.json` and a dedicated report section.

Nested selection may additionally register `selection.empirical_domains`:

```json
{
  "method": "nested_training_input_envelope_v1",
  "minimum_training_groups": 2,
  "composite_rule": "all_registered_members"
}
```

`diagnose_nested_applicability()` runs after selection choices are locked.
Each inner envelope uses only inner training inputs and assesses inner
validation inputs; each outer envelope uses outer training inputs and assesses
outer test inputs. Grouping follows the identity-only split, including its
explicit whole-roster source fallback. Every candidate in the selection roster
is diagnosed; output flags the selected outer candidates without choosing again.
For composites, all registered members must support a sample for `inside`.
Input exclusions and insufficient training evidence precede `outside`/`inside`.
This conservative sample rule is independent of observed pressure availability.

`nested-applicability.json` retains complete member envelopes, sample labels,
and four strata: `inside`, `outside`, `excluded_input`, `insufficient_evidence`.
Errors use exactly the selection roster's common comparison cohort. Missing
targets stay in sample denominators; empty strata have no errors. Each stratum
retains sample-balanced descriptive metrics with the registered cluster
confidence calculation and per-sample log-pressure losses with their failures.
The mean log-pressure loss has no confidence interval in this diagnostic.
Metric intervals condition on the retained folds/envelopes and do not repeat
domain fitting or model selection. They are exploratory fold-stratum summaries,
not independent repeated experiments or uncertainty for the selection process.
Domain evidence never changes predictions, eligibility, selection, or conformal
calibration. The synthetic example enables this diagnostic.

`diagnose_composite_seams()` uses predictors only to evaluate both members at
each hard switch and both endpoints of each blend transition. The versioned
`exact_transition_member_contrast_v1` output retains canonical kPa/volume
fractions, right-minus-left differences, member predictions, normalized input
traces, and explicit failures. Both members are inspected even at zero routing
weight, without changing ordinary routed prediction eligibility. It also works
for samples without observed targets. Hard-switch differences describe jumps
when both member curves are continuous there; blend endpoint differences are
member disagreement, not jumps in the blended curve. This checks registered
transitions rather than certifying global continuity or monotonicity.
Composite runs automatically retain `composite-seams.json` and a report table.
The synthetic retention example demonstrates both new artifact types.

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


`select_grouped_forecast_candidates` runs the learned nested selector on supplied
`RetentionCandidateComparisons`, a complete `GroupedSample` roster, fixed
`candidate_kinds`, and a `LearnedSelectionPlan`. It checks canonical contracts,
roster/profile agreement and atomic learned members. Callers own scientific
eligibility and must supply forecasts that have not been fitted using held-out
targets. Native run selection retains its additional registered PTF provenance
checks. Samples without forecasts remain in coverage denominators.

The repository experiment `evaluation/experiments/group_ratio/` uses this entry
point for exact finite-state estimand and bootstrap-computability diagnostics.
It produces no confidence interval or coverage qualification.


`resample_grouped_forecasts` applies explicit `GroupMultiplicity` counts to a
complete sample/group roster and eligible forecast records. Pass the resolved
`source` or `profile` grouping; resolve missing-profile fallback beforehand.
The result includes copied samples/candidates and an original-to-copy sample map.
All copies retain their original source/profile group, including samples without
eligible forecasts. This shares occurrence materialization with native run
retraining. The helper defines neither a resampling probability law nor an
interval. The exhaustive experiment additionally checks informative missing
targets against full latent-population risk oracles.


`evaluation/experiments/switch_instability/` adds exact finite-grid hard-switch
identification diagnostics. Full fit/failure trajectories distinguish conditional
successful-fit risk, risk mass on success, and an unconditional risk that is
undefined when the registered procedure can fail. Complete-dataset outer error
and per-strategy bootstrap computability remain separate. This research tooling
qualifies no confidence interval and uses no invented native PTF predictions.


`bound_conditional_outer_risks` accepts complete `ConditionalOuterFoldLoss`
records and a `ConditionalOuterRiskPlan` declaring the IID nonempty-group
population, value-independent partition, prior loss/group-size bounds, grouping,
loss and confidence level. It checks disjoint test folds, training complements
and observed bounds, then applies simultaneous group Hoeffding numerator and
denominator bounds. The output covers conditional fitted outer-rule risks and
their equal-fold mean under those assumptions, despite shared training sets.

This target differs from observed sample-weighted CV, average algorithm risk,
and final all-data model risk. No success-conditioned or automatic cross-strategy
familywise guarantee is asserted. Callers own population/provenance assumptions;
complete test losses are required. The optional `conditional_outer_risk` run array now explicitly enables the policy.
Derivation and exact calibration: `evaluation/experiments/conditional_risk/`.


Native conditional risk policies identify a registered `fixed`/`learned`
protocol and `atomic`/`ensemble` strategy, the population/grouping, prior sample
loss and group-size bounds, a common family confidence level, assumptions and
method. The selection loss is inherited exactly; an alternative loss cannot be
supplied. Duplicate protocol/strategy policies and inconsistent family levels
are rejected. Grouping must match resolved selection grouping, including any
explicit source fallback. See `evaluation/examples/synthetic_conditional_risk/`
for a generated IID population with known bounds and a complete run plan.

`assess_selection_conditional_risks` validates original sample/group membership,
outer partitions, retained fit training roles, the eligible common observation
grid and reproduced complete losses. Partial coverage, failed choices/fits and
observed population-bound violations retain unavailable intervals and reasons.
The original number of registered policies, including failures, controls the
simultaneous allocation. `conditional-outer-risk.json` and the verified Markdown
report preserve these results separately from descriptive CV/metric uncertainty.
The existing strategy-assessment and retraining-sensitivity statuses retain their
original targets; averaged-over-training full-process inference remains pending.
