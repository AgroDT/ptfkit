# meta_v3.3 real-data benchmark

Status: **source review incomplete**. Every retained retention-sheet row and
implemented function has an auditable disposition. This accounting does not
certify that all recoverable source evidence has been exhausted. Master-sheet
blocks outside the reviewed retention reconstruction have explicit unresolved
row dispositions in `workbook-scope.json`; they are not silently called samples.

## Workbook scope

{scope_counts}

| Additional raw master source | Rows requiring review | Sample/profile status |
| --- | ---: | --- |
{unreviewed_sources}

These are exact raw source labels, not confirmed publications or independent
groups. Retention curves, hydrological constants, model parameters and derived
values require separate source-backed schemas. Repeated numeric coordinates
must not be averaged into unique experimental observations. The presence of
an author/year label or a plausible value does not resolve these roles.

## Dataset coverage

| Source | Reviewed profiles | Normalized samples | Observations | Status | Main blockers |
| --- | ---: | ---: | ---: | --- | --- |
{sources}

Source partitions and sample identifiers do not establish independent
replication. Unreviewed profiles are never replaced by sample-level grouping.

## Function coverage

| PTF | Eligible samples | Evaluated samples | Blocked samples | Main reasons |
| --- | ---: | ---: | ---: | --- |
{functions}

Reason counts use function/sample/target combinations and can overlap. The full
matrix includes both canonical water quantities and all audited master rows.
Contract gaps are explicit, including functions omitted from the manifest.

## Minimal predictor contracts

Potential rows have a canonical observation and a registered curve or an exact
fixed-pressure output. Counts are conditional ceilings, not confirmed eligibility.
Cost counts distinct unresolved blocker types as an operational heuristic.
All implemented functions remain visible, including those requiring public
measurement-contract review. Published classes can support the registered Cosby
Table 2 derivation independently of measured particle-size fractions.

| Function | Required predictors | Potential compatible rows | Main blocker | Expected unlock cost |
| --- | --- | ---: | --- | --- |
{predictor_priority}

## PTF performance

| Dataset/source | PTF | Samples | Observations | Coverage | RMSE | MAE | ME | CI/status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
{performance}

Errors use volume fractions, prediction minus observation and equal total weight
per sample. These are fixed-candidate descriptive results. Subset coverage is
distinct from workbook coverage. Both maximal and common cohorts are retained.
The class-comparison summary retains exact pressure support, candidate coverage,
wet/intermediate/dry diagnostics and uncertainty status for every cohort.
Cosby uses derived Table 2 class coordinates and only the registered dry branch.

## Selection

| Dataset | Best atomic | Stability | Best ensemble | Stability | Evidence status |
| --- | --- | --- | --- | --- | --- |
| Reviewed Panina | insufficient_evidence | not estimated | insufficient_evidence | not estimated | one profile and two compatible atomic candidates |

Neither candidate is a selected winner. Nested assessment, final selection/refit
and ensemble training require independent reviewed profile/source groups and a
justified grouped protocol. No outer-test leaderboard is used.

## Approximation families

| Family | Fit attempts | Accepted fits | Rejected fits | Accepted RMSE range | Reasons |
| --- | ---: | ---: | ---: | --- | --- |
{fits}

A fit attempt is one sample/family pair; optimizer starts are counted separately
in JSON. All confirmed volumetric curves use the unchanged measured-retention
boxes and seeded multistart policy. Gravimetric curves have explicit
unsupported-family-target records. No density conversion is inferred.

Fit errors are in-sample approximation diagnostics. Parameter intervals,
mean-curve confidence intervals and conditional individual-observation prediction
intervals are stored separately in `approximation-fits.json`. They assume local
linearity and iid homoscedastic residuals; coverage is not validated. Intervals
are never clipped. Workbook-stored parameters are not observed targets.

## WRC pressure diagnostics

Policy `wrc_pressure_regions_kpa_v1`: wet [0,10), intermediate [10,1500), dry
[1500,infinity) kPa. Region summaries retain equal sample weights and exact
coordinates. They do not change selection loss. Empty regions have
`no_observations`.

| Region | Samples | Observations | RMSE | MAE | ME |
| --- | ---: | ---: | ---: | ---: | ---: |
{regions}

## Remaining blockers

Coverage of the audited function/master-row/target product: `{coverage_counts}`.
Scientific status is stored separately from execution status. A confirmed
measurement mismatch is incompatible; an unreviewed contract is unresolved.
Missing adapters or canonical targets do not prove permanent structural
impossibility. Unresolved counts are review ceilings, not confirmed applicability.

| Blocker | Affected rows | Affected functions | Blocked combinations | Potential gain if resolved |
| --- | ---: | ---: | ---: | --- |
{impact}

The upper bound assumes all co-blockers are resolved too. The sole-gap count
only counts combinations with no other recorded blocker; it still requires
scientific validation and successful prediction. Blocker counts overlap and
must not be summed. Additional master blocks below are outside this audited
sample roster; their row counts cannot be multiplied into scoring coverage.

Source-review priority within the audited roster excludes combinations needing
new public measurement contracts or new adapters. The first row is the next
source for review under this conditional ceiling. It is not a guarantee that
the missing properties or compatible experiments exist in that source.

| Source | Affected rows | Affected functions | Potential combinations ceiling |
| --- | ---: | ---: | ---: |
{source_priority}

## Priority source reconstruction

| Raw source | Master rows | Exact cross-sheet IDs | Identical ordered vectors | Released points | Remaining claims |
| --- | ---: | ---: | ---: | ---: | --- |
{priority_audit}

Literal IDs establish transfer identity between workbook views only. They do
not prove experimental sample identity or independent replication. Vector
comparisons include empty and control rows. Numerical candidate matches never
authorize joins. The local `priority-source-audit.json` preserves row labels,
metadata coordinates, exact value multisets and duplicate vectors. Missing
pressure-to-water binding is not repaired by pairing adjacent rows.

## Source observation exclusions

Ranking is an upper bound on recoverable row coverage, not a promise of
independent profiles or compatible PTFs. Physical and identity evidence must
both be resolved before release.

{blockers}

See `source-readiness.json` for source-specific physical and identity claims,
`row-accounting.json` for exact cell lineage, and `eligibility-matrix.json` for
every implemented function. Raw data remain local.
