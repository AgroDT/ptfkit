import math
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    FixedSelectionPlan,
    GroupedSample,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    SigmoidGridFit,
    SigmoidGridPlan,
    TargetSpec,
    select_grouped_forecast_candidates,
    sigmoid_left_weight,
)


SLOPE = math.log(3)
GATE = SigmoidGridPlan(
    id='sigmoid',
    left_candidate_id='high',
    right_candidate_id='low',
    parameter_grid=((10, 2 * SLOPE), (1, SLOPE), (10, SLOPE)),
    minimum_training_groups=1,
    minimum_loss_gap=1e-12,
)
LOSS = LogPressureLossPlan(lower_suction_kpa=0.1, upper_suction_kpa=1000, minimum_points=5)
SELECTOR = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('high', 'low'),
        loss=LOSS,
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
    ),
    ensembles=(GATE,),
    method='nested_two_curve_selection_v1',
)
SAMPLES = tuple(GroupedSample(f'group{i}', 's0') for i in range(12))
WEIGHTS = (Fraction(9, 10), Fraction(3, 4), Fraction(1, 2), Fraction(1, 4), Fraction(1, 10))


def forecasts():
    return tuple(
        RetentionCandidateComparisons(
            candidate_id=name,
            dataset_id='controlled',
            protocol_id='pressure_sigmoid',
            target=TargetSpec(
                'volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume'
            ),
            comparisons=tuple(
                RetentionComparison(
                    s.source_id, s.sample_id, p, float(Fraction(1, 4) + weight / 2), prediction
                )
                for s in SAMPLES
                for p, weight in zip((0.1, 1, 10, 100, 1000), WEIGHTS, strict=True)
            ),
        )
        for name, prediction in (('high', 0.75), ('low', 0.25))
    )


def select(
    candidates: tuple[RetentionCandidateComparisons, ...] | None = None,
    plan: LearnedSelectionPlan = SELECTOR,
):
    return select_grouped_forecast_candidates(
        forecasts() if candidates is None else candidates,
        samples=SAMPLES,
        candidate_kinds={'high': 'atomic', 'low': 'atomic'},
        plan=plan,
    )


def test_sigmoid_gate_uses_base10_pressure_logit_and_rational_weight_oracle():
    actual = [sigmoid_left_weight(p, (10, SLOPE)) for p in (0.1, 1, 10, 100, 1000)]
    assert actual == pytest.approx([float(w) for w in WEIGHTS], rel=1e-14, abs=1e-15)
    assert sigmoid_left_weight(0, (10, SLOPE)) == 1
    assert sigmoid_left_weight(10, (10, 1e308)) == 0.5
    assert sigmoid_left_weight(1e308, (1e-308, 1e308)) == 0
    assert sigmoid_left_weight(1e-308, (1e308, 1e308)) == 1


def test_adjacent_large_pressures_keep_their_distinct_logit():
    center = 1e100
    pressure = math.nextafter(center, math.inf)
    with localcontext() as context:
        context.prec = 90
        z = Decimal('1e15') * (Decimal(pressure) / Decimal(center)).ln() / Decimal(10).ln()
        expected = float(1 / (1 + z.exp()))
    actual = sigmoid_left_weight(pressure, (center, 1e15))
    assert actual == pytest.approx(expected, rel=1e-14)
    assert actual < 0.49


def test_nested_sigmoid_search_recovers_exact_gate_and_hand_grid_objectives():
    result = select()
    alternative_weights = {
        (1, SLOPE): tuple(
            Fraction(1, 1 + Fraction(3) ** exponent) for exponent in (-1, 0, 1, 2, 3)
        ),
        (10, 2 * SLOPE): (
            Fraction(81, 82),
            Fraction(9, 10),
            Fraction(1, 2),
            Fraction(1, 10),
            Fraction(1, 82),
        ),
        (10, SLOPE): WEIGHTS,
    }
    objectives = {
        pair: sum(
            (a - b) ** 2 * w / 4
            for a, b, w in zip(
                weights,
                WEIGHTS,
                (Fraction(1, 8), Fraction(1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(1, 8)),
                strict=True,
            )
        )
        for pair, weights in alternative_weights.items()
    }
    for fold in result.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, SigmoidGridFit)
        assert fit.parameters == (10, SLOPE)
        assert fit.training_loss == pytest.approx(0, abs=1e-28)
        assert fit.loss_gap == pytest.approx(float(sorted(objectives.values())[1]), rel=1e-13)
        assert fit.training_groups == result.splits.folds[fold.fold_id].training_groups
        assert {s.parameters: s.mean_training_loss for s in fit.scores} == pytest.approx(
            {key: float(value) for key, value in objectives.items()}, abs=1e-28, rel=1e-13
        )
        assert len(fold.ensemble.predictions) == 20
        assert all(abs(p.predicted - p.observed) < 1e-14 for p in fold.ensemble.predictions)


def test_heldout_targets_cannot_change_sigmoid_inner_choices_or_outer_refit():
    before = select()
    heldout = {
        key
        for group in before.splits.groups
        if group.group_id in before.splits.folds[0].test_groups
        for key in group.samples
    }
    changed = tuple(
        replace(
            c,
            comparisons=tuple(
                replace(p, observed=0.9) if (p.source_id, p.sample_id) in heldout else p
                for p in c.comparisons
            ),
        )
        for c in forecasts()
    )
    after = select(changed)
    assert before.folds[0].ensemble.outer_fit == after.folds[0].ensemble.outer_fit
    assert before.folds[0].ensemble.inner_scores == after.folds[0].ensemble.inner_scores
    assert before.folds[0].ensemble.assessment != after.folds[0].ensemble.assessment


def test_indistinguishable_members_retain_sigmoid_identification_failure():
    candidates = forecasts()
    identical = tuple(
        replace(c, comparisons=tuple(replace(p, predicted=0.5) for p in c.comparisons))
        for c in candidates
    )
    result = select(identical)
    for fold in result.folds:
        assert fold.ensemble.candidate_id is None
        assert fold.ensemble.reason == 'insufficient_inner_evidence'
        assert not fold.ensemble.predictions
        for inner in fold.ensemble.inner_scores[0].folds:
            fit = inner.fit
            assert isinstance(fit, SigmoidGridFit)
            assert fit.parameters is None
            assert fit.loss_gap == 0
            assert fit.reason == 'unidentifiable_sigmoid_parameters'
            assert len(fit.scores) == 3


@pytest.mark.parametrize(
    'parameters',
    [
        ((1, 1),),
        ((1, 1), (1, 1)),
        ((0, 1), (10, 1)),
        ((1, 0), (10, 1)),
        ((1, math.inf), (10, 1)),
        ((True, 1), (10, 1)),
    ],
)
def test_invalid_registered_sigmoid_parameters_are_rejected(
    parameters: tuple[tuple[float, float], ...],
):
    with pytest.raises(EvaluationDocumentError):
        replace(GATE, parameter_grid=parameters)


@pytest.mark.parametrize('center', [0.1, 1000, 10000])
def test_sigmoid_centers_must_be_strictly_inside_registered_selection_domain(center: float):
    with pytest.raises(EvaluationDocumentError, match='center'):
        replace(SELECTOR, ensembles=(replace(GATE, parameter_grid=((center, 1), (10, 1))),))
