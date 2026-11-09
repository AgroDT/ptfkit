from dataclasses import replace
from fractions import Fraction
from typing import Literal

import pytest

from ptfkit_eval import (
    BlendGridFit,
    BlendGridPlan,
    EvaluationDocumentError,
    FixedSelectionPlan,
    GroupedSample,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    select_grouped_forecast_candidates,
)


LOSS = LogPressureLossPlan(lower_suction_kpa=0.1, upper_suction_kpa=100000, minimum_points=7)
BLEND = BlendGridPlan(
    id='trained_blend',
    left_candidate_id='high',
    right_candidate_id='low',
    interval_grid_kpa=((1, 10000), (10, 1000)),
    transform='log10',
    weighting='linear',
    minimum_training_groups=1,
    minimum_loss_gap=1e-12,
)
PLAN = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('high', 'low'),
        loss=LOSS,
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
    ),
    ensembles=(BLEND,),
    method='nested_two_curve_selection_v1',
)
TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')
KINDS: dict[str, Literal['atomic', 'ensemble']] = {'high': 'atomic', 'low': 'atomic'}


def fixture(weighting: Literal['linear', 'smoothstep'] = 'linear'):
    samples = tuple(GroupedSample(f'g{i}', 'sample') for i in range(6))
    # Log-axis positions at 10/100/1000 are exactly 1/4, 1/2 and 3/4.
    values = (0.75, 0.75, 5 / 8, 0.5, 3 / 8, 0.25, 0.25)
    if weighting == 'smoothstep':
        values = (0.75, 0.75, 43 / 64, 0.5, 21 / 64, 0.25, 0.25)
    candidates = tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id='mathematical_blends',
            protocol_id='fixed_grid',
            target=TARGET,
            comparisons=tuple(
                RetentionComparison(s.source_id, s.sample_id, pressure, observed, value)
                for s in samples
                for pressure, observed in zip(
                    (0.1, 1, 10, 100, 1000, 10000, 100000), values, strict=True
                )
            ),
        )
        for identifier, value in (('high', 0.75), ('low', 0.25))
    )
    return samples, candidates, values


@pytest.mark.parametrize('weighting', ['linear', 'smoothstep'])
def test_inner_search_and_outer_refit_recover_the_predeclared_blend_with_exact_loss_oracles(
    weighting: Literal['linear', 'smoothstep'],
):
    samples, candidates, values = fixture(weighting)
    plan = replace(PLAN, ensembles=(replace(BLEND, weighting=weighting),))
    result = select_grouped_forecast_candidates(
        candidates, samples=samples, candidate_kinds=KINDS, plan=plan
    )
    assert result.status == 'computed'
    for fold in result.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, BlendGridFit)
        assert fit.interval_kpa == (1, 10000)
        assert fit.training_loss == 0
        assert fit.loss_gap == pytest.approx(1 / 192 if weighting == 'linear' else 25 / 12288)
        assert fit.training_sample_count == fit.usable_group_count == 4
        assert fit.training_groups == result.splits.folds[fold.fold_id].training_groups
        assert [(s.interval_kpa, s.mean_training_loss) for s in fit.scores] == [
            ((1, 10000), 0),
            ((10, 1000), pytest.approx(fit.loss_gap)),
        ]
        assert fold.ensemble.assessment is not None
        assert fold.ensemble.assessment.mean_loss == 0
        assert [p.predicted for p in fold.ensemble.predictions] == list(values) * 2
        for inner in fold.ensemble.inner_scores[0].folds:
            assert isinstance(inner.fit, BlendGridFit)
            assert inner.fit.interval_kpa == (1, 10000)
            assert inner.fit.training_sample_count == 2


def test_untouched_outer_targets_cannot_choose_a_blend_interval_or_retrain_it():
    samples, candidates, _ = fixture()
    before = select_grouped_forecast_candidates(
        candidates, samples=samples, candidate_kinds=KINDS, plan=PLAN
    )
    held_out = set(before.splits.folds[0].test_groups)
    changed = tuple(
        replace(
            c,
            comparisons=tuple(
                replace(p, observed=1 - p.observed) if (p.source_id, '') in held_out else p
                for p in c.comparisons
            ),
        )
        for c in candidates
    )
    after = select_grouped_forecast_candidates(
        changed, samples=samples, candidate_kinds=KINDS, plan=PLAN
    )
    assert before.folds[0].ensemble.outer_fit == after.folds[0].ensemble.outer_fit
    assert before.folds[0].ensemble.inner_scores == after.folds[0].ensemble.inner_scores
    assert after.folds[0].ensemble.assessment is not None
    assert after.folds[0].ensemble.assessment.mean_loss is not None
    assert after.folds[0].ensemble.assessment.mean_loss > 0


def test_linear_axis_is_respected_instead_of_silently_using_log_pressure_weights():
    samples, candidates, _ = fixture()
    targets = {
        pressure: float(
            Fraction(3, 4)
            if pressure <= 1
            else Fraction(1, 4)
            if pressure >= 10000
            else Fraction(3, 4) - Fraction(1, 2) * (Fraction(pressure) - 1) / 9999
        )
        for pressure in (0.1, 1, 10, 100, 1000, 10000, 100000)
    }
    candidates = tuple(
        replace(
            c, comparisons=tuple(replace(p, observed=targets[p.suction_kpa]) for p in c.comparisons)
        )
        for c in candidates
    )
    plan = replace(PLAN, ensembles=(replace(BLEND, transform='linear'),))
    result = select_grouped_forecast_candidates(
        candidates, samples=samples, candidate_kinds=KINDS, plan=plan
    )
    for fold in result.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, BlendGridFit)
        assert fit.interval_kpa == (1, 10000)
        assert fit.training_loss == pytest.approx(0, abs=1e-30)
        for point in fold.ensemble.predictions:
            assert point.predicted == pytest.approx(targets[point.suction_kpa], abs=1e-15)


def test_indistinguishable_member_forecasts_do_not_default_a_transition_interval():
    samples, candidates, _ = fixture()
    same = tuple(
        replace(c, comparisons=tuple(replace(p, predicted=0.5) for p in c.comparisons))
        for c in candidates
    )
    result = select_grouped_forecast_candidates(
        same, samples=samples, candidate_kinds=KINDS, plan=PLAN
    )
    for fold in result.folds:
        assert fold.ensemble.candidate_id is None
        assert fold.ensemble.reason == 'insufficient_inner_evidence'
        for inner in fold.ensemble.inner_scores[0].folds:
            assert isinstance(inner.fit, BlendGridFit)
            assert inner.fit.interval_kpa is None
            assert inner.fit.reason == 'unidentifiable_blend_interval'
            assert inner.fit.loss_gap == 0
            assert len(inner.fit.scores) == 2


@pytest.mark.parametrize(
    'change', ['duplicate', 'inverted', 'weighting', 'axis', 'gap', 'domain', 'method']
)
def test_blend_registration_rejects_ambiguous_or_unregistered_scientific_choices(change: str):
    changes = {
        'duplicate': {'interval_grid_kpa': ((1, 10000), (1, 10000))},
        'inverted': {'interval_grid_kpa': ((100, 1), (10, 1000))},
        'weighting': {'weighting': 'automatic'},
        'axis': {'transform': 'sqrt'},
        'gap': {'minimum_loss_gap': 0},
    }
    if change == 'domain':
        target, fields = (
            PLAN,
            {'ensembles': (replace(BLEND, interval_grid_kpa=((0.1, 10), (10, 100))),)},
        )
    elif change == 'method':
        target, fields = PLAN, {'method': 'nested_convex_pair_selection_v1'}
    else:
        target, fields = BLEND, changes[change]
    with pytest.raises(EvaluationDocumentError):
        replace(target, **fields)
