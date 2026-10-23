"""Controlled held-out prediction states for diagnostic and strategy contracts."""

import json
from dataclasses import replace
from pathlib import Path

from _run_fixtures import dataset_document, evaluation_document, write_run_fixture

from ptfkit_eval import (
    ConvexPairPlan,
    FixedSelectionPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionRunResult,
    execute_retention_run,
    load_retention_run_plan,
    select_fixed_retention_candidates,
    select_learned_retention_candidates,
)


FIXED = FixedSelectionPlan(
    candidate_ids=('sand_a', 'sand_b', 'ensemble'),
    folds=NestedGroupPlan(seed=27, outer_folds=3, inner_folds=2),
    loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
    minimum_coverage=0.5,
)
LEARNED = LearnedSelectionPlan(
    fixed=replace(FIXED, candidate_ids=('sand_a', 'sand_b')),
    ensembles=(
        ConvexPairPlan(
            id='trained',
            left_candidate_id='sand_a',
            right_candidate_id='sand_b',
            minimum_training_groups=1,
            minimum_mean_squared_contrast=1e-12,
        ),
    ),
)


def diagnostic_result(
    directory: Path, *, missing_target: bool = False, outside_pressure: bool = False
) -> RetentionRunResult:
    """Six sources with constant binary-fraction errors and exact pressure grids."""
    dataset = json.loads(json.dumps(dataset_document()))
    template, observation = dataset['samples'][0], dataset['observations'][0]
    dataset['samples'] = [{**template, 'source_id': f'source_{index}'} for index in range(6)]
    grid = (1, 10, 100, 1000) if outside_pressure else (1, 10, 100)
    dataset['observations'] = [
        {
            **observation,
            'id': f'{index}_{pressure}',
            'source_id': f'source_{index}',
            'suction_kpa': pressure,
            'value': 0.5,
        }
        for index in range(6)
        if not (missing_target and index == 5)
        for pressure in grid
    ]
    evaluation = json.loads(json.dumps(evaluation_document()))
    atomic = evaluation['candidates'][0]
    evaluation['candidates'].append(
        {
            'id': 'ensemble',
            'kind': 'range_gated_curve',
            'axis': atomic['axis'],
            'target': atomic['target'],
            'members': [
                {
                    'id': name,
                    'function': atomic['function'],
                    'prediction': atomic['prediction'],
                    'interval': {
                        'lower': {'value': lower, 'inclusive': inclusive},
                        'upper': {'value': upper, 'inclusive': True},
                    },
                }
                for name, lower, upper, inclusive in (
                    ('wet', 1, 10, True),
                    ('dry', 10, 1000, False),
                )
            ],
            'routing': {'gap': 'reject', 'extrapolation': 'reject', 'transitions': []},
            'provenance': {'kind': 'fixed', 'source': 'Controlled diagnostic fixture.'},
        }
    )
    result = execute_retention_run(
        load_retention_run_plan(
            write_run_fixture(directory, dataset=dataset, evaluation=evaluation)
        )
    )
    points = []
    for point in result.points:
        assert point.comparison is not None
        assert point.prediction is not None
        predicted = {'sand_a': 0.625, 'sand_b': 0.75, 'ensemble': 0.75}[point.candidate_id]
        if point.suction_kpa == 1000:
            predicted = 1.5
        points.append(
            replace(
                point,
                comparison=replace(point.comparison, predicted=predicted),
                prediction=replace(
                    point.prediction,
                    value=predicted,
                    contributions=tuple(
                        replace(item, value=predicted) for item in point.prediction.contributions
                    ),
                ),
            )
        )
    result = replace(result, points=tuple(points))
    return replace(
        result,
        selection=select_fixed_retention_candidates(result, plan=FIXED),
        learned_selection=select_learned_retention_candidates(result, plan=LEARNED),
    )
