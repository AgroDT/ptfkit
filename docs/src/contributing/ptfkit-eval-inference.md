# Strategy uncertainty: evidence and qualification

Status: research and retraining infrastructure in progress, 2026-10-23.
Bounded conditional outer-rule risk is implemented through low-level and native
opt-in APIs. Native independent-block training-law inference repeats the complete
registered learned selector, with explicit training/failure targets. The current
strategy artifact retains `not_estimated_crossfit_dependency`; the retraining
artifact retains `not_estimated_retraining_sensitivity_only`.

## Primary-source evidence

[Bengio and Grandvalet (2004)](https://www.jmlr.org/papers/v5/grandvalet04a.html)
establish that a universally unbiased variance estimator for K-fold CV does not
exist under unrestricted distributions. They explain why ignoring error
covariances can underestimate variance. This result does not say that all
confidence procedures under stated assumptions are impossible.

[Bates, Hastie, and Tibshirani](https://arxiv.org/pdf/2104.00673) develop a
nested-CV MSE estimator using a fresh holdout and an unbiased holdout-error
identity. The paper distinguishes the risk conditional on a fitted training
dataset from risk averaged over new training datasets. Its setup uses i.i.d.
observations and ordinary mean loss. Its statistical NCV construction is not
the same operation as using inner CV to tune candidates. Applying its learner
definition to our complete tuning procedure would require assessing that
procedure inside the inference resampling, including its internal selection.

[Schulz-Kümpel et al. (2025)](https://data.mlr.press/assets/pdf/v02-6.pdf)
benchmark multiple generalization-error CI methods and discuss limitations
around integrated tuning and algorithmic randomness. Their benchmark requires
i.i.d. data. It supplies useful candidates and empirical evidence, not a
qualification result for unequal-size publication/profile groups in ptfkit.

## The estimand in this evaluator

The following is our application-specific analysis, not a claimed extension
proved by those publications.

For a fresh independent group, let `N` be its number of eligible samples and
`S(A(D))` the sum of their registered log-pressure losses for the rule trained
and selected from `D`. The sample-weighted population target is

```text
R_sample(A(D)) = E[S(A(D)) | D] / E[N].
```

Here `N` follows the predeclared common-cohort eligibility rule, independently
of trained choices. An undefined prediction/fit needs a separate failure policy;
it cannot silently redefine this population by being dropped.
Its conditional-on-training and averaged-over-training versions are different
targets. Our held-out point estimate is a ratio of sums over observed samples,
not an equal-weight mean of source means. Missing targets and coverage gates
also require an explicit population/eligibility interpretation. Neither source
exchangeability nor representativeness follows from having source identifiers.

For an exact counterexample, suppose independent groups are equally likely to
be A (one sample of loss zero) or B (three samples of loss one). The population
sample-weighted risk is `E[S]/E[N] = (3/2)/2 = 3/4`. With two held-out groups:

| Draw | Number of samples | Total loss | Sample-weighted estimate |
| --- | ---: | ---: | ---: |
| AA | 2 | 0 | 0 |
| AB | 4 | 3 | 3/4 |
| BA | 4 | 3 | 3/4 |
| BB | 6 | 6 | 1 |

The expected finite-holdout ratio is `5/8`, not `3/4`. An equal-group mean
targets `1/2`, also not `3/4`. Thus a group-level plug-in must address both
the independent unit and the normalization; replacing sample weights with
source weights silently changes the target. Equal group sizes remove this
particular ratio issue, but do not by themselves qualify an inference pipeline.

## Implemented retraining substrate

`whole_group_bootstrap_retraining_sensitivity_v1` draws whole original groups
with replacement and repeats registered candidate selection and ensemble
fitting. Multiplicity repeats sample/observation occurrences while preserving
original source/profile identities. All copies of one original group therefore
stay together in every fold and count once for group evidence gates. Unequal
group sizes retain their sample-occurrence weights.

The original effective grouping, including explicit source fallback, is frozen
before drawing. Fold assignment is rebuilt with the registered fold seed.
Every attempted draw is retained, including insufficient distinct groups,
coverage failures and nonidentifiable fits. Failed draws are neither discarded
nor redrawn until successful. Original-to-occurrence maps and derived dataset
checksums make the computation auditable from parent snapshots.

Eligibility and fixed PTF predictions are cached because the currently supported
atomic functions have no learned preprocessing. Target-dependent candidate
selection, convex weights and switch grids are recomputed. Independent
reference fits, reports and physical diagnostics are not part of the selected
prediction rule and are not retrained. The output is a trajectory, not a
confidence interval or a substitute for a qualified inferential procedure.

## Outstanding qualification work

Before registering a full CI, specify and verify:

- Conditional fitted-rule risk versus average algorithm risk, and the effective
  training size to which the interval refers.
- Independent group population, group-size/eligibility design, and preservation
  of the sample-weighted target under unequal and informative group sizes.
- All learning and tuning inside the assessed algorithm, with every duplicate
  original group isolated from its own holdout across every nesting level.
- A justified variance/MSE or distributional calculation; required moments,
  stability or bounded-loss assumptions cannot be inferred from observed data.
- Treatment of failed fits and insufficient groups without changing the draw
  law by conditioning on successful replicates.
- Independent analytic or exhaustive oracles plus coverage experiments across
  varying group sizes, unequal pressure grids, candidate instability, boundary
  ties, missing targets and limited independent-group counts.

Publication-source review and real-data scientific eligibility remain separate
requirements. They are not resolved by resampling or a nominal confidence level.


The executable `evaluation/experiments/group_ratio/` experiment
now checks these distinctions through the actual learned selection core. Its
independent exact oracles show a sample-weighted cross-fit expectation differing
from the risk of a rule trained on two IID groups under informative group sizes.
Its complete bootstrap probability is 2/9, and successful draws alone have zero
spread. This is an estimand/computability diagnostic, not an interval or coverage
qualification; all failed draws remain accounted for.


The independent `evaluation/experiments/switch_instability/` diagnostic adds
finite-grid identification failure. With equal-sized groups, half of two-group
training samples tie, so the registered ensemble has no unconditional model
risk under its failure policy. Its conditional successful-fit risk is 1/16.
Only one quarter of original three-group datasets have every outer fit succeed,
and those datasets have zero ensemble outer loss. This selective-completion
law must not be mistaken for zero population risk. With sizes 1/3, all fits
succeed but the expected outer statistic still differs from the two-group
training-law risk. Full fit/failure evidence and exact independent oracles are
retained; no interval is qualified.


## Bounded conditional outer-rule risk

`bound_conditional_outer_risks` implements
`simultaneous_group_hoeffding_conditional_outer_risk_v1`. The complete derivation
and exact coverage experiment are in `evaluation/experiments/conditional_risk/`.
The starting point is [Hoeffding (1963)](https://doi.org/10.1080/01621459.1963.10500830).
The ratio and cross-fit construction are our application-specific derivation.

The declared population has IID nonempty groups, value-independent fold
assignment, prior sample-loss/group-size bounds and complete observed test
losses. K conditional group-sum numerator events and one all-group size event
receive alpha/(K+1) each. Integrating numerator tail bounds over training and
taking their union with the denominator event needs no independence between
folds. Positive denominator bounds produce simultaneous intervals for
`E[S_j | training_j] / E[N]` and their equal-fold mean. Observed maxima cannot
establish population bounds. Arbitrary selection/tuning stays within training.

This conditional fitted-rule target differs from observed sample-weighted CV,
average algorithm risk and a final all-data model. Coverage is over original
group draws, not conditional on successful output. One invocation covers one
specified strategy; separate strategy calls do not supply familywise coverage.
Malformed partitions, incomplete losses and observed bound violations are
rejected. Callers own population assertions and fitted-rule provenance.

Four exact binary-group experiments and actual nested convex-selector tests
verify the implementation. Native coverage/provenance adapters, explicit run registration and failed-fit
reporting are now integrated with simultaneous allocation across policies. Scientific population
assumptions and real-workbook confidence claims remain unestablished.


Native `conditional_outer_risk` registrations form a frozen family of q unique
protocol/strategy policies sharing one confidence level. Policy numerator and
denominator events receive alpha/[q(K+1)]. Failed policies remain in q, without
success-conditioned reallocation. The low-level plan carries q as
`simultaneous_policy_count`, avoiding rounded adjusted-confidence arithmetic.
Every requested policy retains either complete bounds or explicit fit, coverage
or population-bound failure evidence. Eligible observations and full original
sample/group coverage are verified before native inference. The generated
`evaluation/examples/synthetic_conditional_risk/` population supplies actual
IID draws with prior size/loss bounds; real-workbook assumptions remain unresolved.


## Independent training-law blocks

`independent_blocks_group_hoeffding_training_law_v1` now provides low-level
average-training inference from disjoint independent training/test blocks. The
complete derivation is in `evaluation/experiments/training_law_risk/README.md`.
For every block, repeat the whole named learner on T training groups and use
H independent test groups. Population bounds and value-independent role
allocation remain explicit assumptions; data-derived tuning shared across blocks
would invalidate the construction.

Three concentration events bound successful-training loss mass, population
group size and training success probability. Failed training contributes zero
to the defined mass variable, while its test sample/group counts remain in the
normalization. It is not assigned a zero model error. Success/failure, success-
weighted population risk and successful-training mean risk are separate targets.
An unconditional model-risk interval requires a prior total-learner assertion;
observed success alone is insufficient. A contradicted assertion suppresses
inference. Unknown successful-block test losses cannot become training failures.

Exact multinomial experiments retain every block-count state and test joint
unconditional coverage. Issuance of a successful-training risk interval and its
joint error/issuance probability are reported separately, without nominal
coverage claims conditional on issuance. Identity-only disjoint-block allocation
and complete-selector reruns are implemented, with native policy schemas,
portable block provenance and a separate simultaneous strategy family.
This does not convert the existing overlapping-fold statistic into an IID
training-risk estimator or transfer T-group risk to a larger final model.

Conditional outer-rule validation now reconstructs the full original nested
split and verifies every eligible in-domain pressure. Loss/fit metadata cannot
hide coordinated role changes or interior-point removal. Out-of-domain pressure
diagnostics do not change the registered loss target.


The renewed online review is recorded in
[the source review](ptfkit-eval-source-review.md). Published statistical results,
hydraulic evaluation practices, model-specific errata and unavailable workbook
measurement evidence remain distinct. Identity-only allocation assumes
value-independent administrative identifiers; hashing a value-encoded identifier
would not establish the required sampling law.


Native `independent_training_risk` now allocates complete original-group blocks,
repeats inner selection/refitting and preserves every attempted training. Its
q-policy concentration allocation includes failed strategies without reallocating
their budget. All block roles, inner scores, fits, predictions and test losses
are retained with original forecast inputs. A test coverage failure suppresses
inference; it cannot become a training failure. Global source/profile fallback
is frozen before allocation. Parent CV choices/fits do not enter this learner.

The public supplied-forecast adapter uses the same selector core and leaves
scientific forecast provenance with its caller. Native execution additionally
checks registered member provenance. The implemented training procedure has no
learned preprocessing; reference approximation fits and empirical-domain
reporting remain separate diagnostics. Independent administrative IDs and prior
population bounds remain assumptions, not consequences of successful execution.
The twelve-group example uses only two independent blocks, giving uninformative
bounds. It is a replay/provenance demonstration. Exact kernel calibration and
selector leakage/oracle tests provide complementary evidence; real-workbook
coverage and scientific compatibility are still unestablished.


The exact `evaluation/experiments/selector_training_law/` calibration now pushes
all ordered training/test state triples through the complete public selector.
For the informative four-state population, the T=2 switch learner has success
23/32, risk mass 11/256 and successful-training sample risk 11/184. The 64
actual local cases collapse to six sufficient states and 6,188 exact 12-block
count states. This particular learner's permutation invariance justifies the
convolution; it is not assumed for arbitrary tuned algorithms. All actual
input/refit/failure traces and exact probabilities are retained. No failed
training is dropped or assigned a zero-error model.


Paired independent-block inference now targets the left-minus-right sample-risk
difference on joint training success, retaining asymmetric fit failures. It
maps complete per-model sample losses to a bounded shifted difference and uses
the qualified three-event kernel, then transforms intervals algebraically.
It never subtracts marginal successful-training risk intervals with different
conditioning events. The exact informative-size selector population has joint
success 23/32, signed risk mass 23/512 and successful difference 1/16, versus
1559/23552 when subtracting marginal successful-training risks. Native paired
registration and full two-rule block provenance are integrated. This comparison
has its own confidence allocation; no joint coverage with separate policy
families is implied. The derivation and exact calibration are recorded in
`evaluation/experiments/selector_training_law/paired-risk.md`.


The finite-grid learned blend uses the same complete training/assessment and
independent/paired risk paths as other registered two-curve learners. Its exact
mathematical law is checked separately in `evaluation/experiments/blend_training_law/`.
On a five-pressure finite support, mismatch loss is 1/64. All normalized block
statistics match the checked switch law, and every risk endpoint scales by the
binary factor 1/8. The informative targets are success=23/32, mass=11/2048 and
successful-training sample risk=11/1472. Actual blend refits, failed identification
and complete original-group roles are retained. No endpoint parameter interval,
physical monotonicity guarantee or real-workbook population qualification follows.


Point assessment now separately registers sample-balanced MAE/MSE of the same
log-loss-trained complete learner. A sample is scored only on its complete
original fixed-roster common grid inside the selection domain, with equal
weights within that sample. Missing selected predictions retain the full test
roster and suppress inference; they never become training failures. The family
budget counts all registered strategy/metric pairs, including failed learners.
The independent-block kernel applies to their declared bounded nonnegative
sample scores without changing its three-event proof or assumptions.

For MSE, monotonic square-root transformation yields pooled RMSE intervals:
sqrt(E_T[R_MSE(T) | training success]); it is not
E_T[sqrt(R_MSE(T)) | training success]. The unconditional counterpart requires
prior totality. MAE receives no square-root transformation. Paired point-risk
comparisons target differences of the registered MAE/MSE risks on joint success,
not differences of RMSE or of differently conditioned marginal means. Exact
finite-population point calibration accompanies the blend experiment; its
informative truths are MAE=11/460 and MSE=11/1840 on successful training.

The registered nonlinear pressure sigmoid is another finite training-only grid
learner. Its independent mathematical control uses two fixed atomics 1 and 0,
center 10 kPa and steepness ln(2) or 2*ln(2). Their three-pressure rational curves
have symmetric mismatch loss 2/225 under weights (1/4,1/2,1/4). All 8/64 actual
training/test triples verify the sample-majority rule and retained identification
failures before the 91/6,188 twelve-block count-state convolution. A prior 1/64
bound safely exceeds all support losses. Informative truths are success=23/32,
mass=11/3600 and successful-training risk=22/5175. Exact probability coverage is
checked against independently computed binomial success tails; model losses and
CI endpoints use explicitly tolerated floating arithmetic. Neither center nor
steepness receives a parameter confidence interval from that calculation.
