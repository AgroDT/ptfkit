"""Unequal-size independent groups with analytically known ensemble weights."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Literal

from _run_fixtures import dataset_document, write_run_fixture

from ptfkit_eval import (
    ConvexPairPlan,
    FixedSelectionPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionRunResult,
    execute_retention_run,
    load_retention_run_plan,
    select_learned_retention_candidates,
)


def resampling_result(
    directory: Path,
    *,
    grouping: Literal['source', 'profile'] = 'source',
    source_fallback: bool = False,
) -> RetentionRunResult:
    dataset = json.loads(json.dumps(dataset_document()))
    sample, observation = dataset['samples'][0], dataset['observations'][0]
    dataset['samples'] = [
        {
            **sample,
            'source_id': f'source_{index}',
            'sample_id': sample_id,
            'profile_id': None if source_fallback and index == 0 else 'profile_one',
        }
        for index in range(8)
        for sample_id in (('one', 'two') if index == 0 else ('one',))
    ]
    dataset['observations'] = [
        {
            **observation,
            'id': f'{sample["source_id"]}_{sample["sample_id"]}_{pressure}',
            'source_id': sample['source_id'],
            'sample_id': sample['sample_id'],
            'suction_kpa': pressure,
            'value': 0.75 if sample['source_id'] == 'source_0' else 0.25,
        }
        for sample in dataset['samples']
        for pressure in (1, 100)
    ]
    result = execute_retention_run(
        load_retention_run_plan(write_run_fixture(directory, dataset=dataset))
    )
    points = []
    for point in result.points:
        assert point.comparison is not None
        predicted = 0.75 if point.candidate_id == 'sand_a' else 0.25
        points.append(replace(point, comparison=replace(point.comparison, predicted=predicted)))
    result = replace(result, points=tuple(points))
    fixed = FixedSelectionPlan(
        candidate_ids=('sand_a', 'sand_b'),
        folds=NestedGroupPlan(
            seed=27,
            outer_folds=3,
            inner_folds=2,
            grouping=grouping,
            missing_profiles='source' if source_fallback else 'reject',
        ),
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
    )
    plan = LearnedSelectionPlan(
        fixed=fixed,
        ensembles=(
            ConvexPairPlan(
                id='trained',
                left_candidate_id='sand_a',
                right_candidate_id='sand_b',
                minimum_training_groups=2,
                minimum_mean_squared_contrast=1e-12,
            ),
        ),
    )
    return replace(result, learned_selection=select_learned_retention_candidates(result, plan=plan))
