import json
from pathlib import Path

import pytest
from _run_fixtures import HALF_WETNESS_KPA, dataset_document, write_run_fixture

from ptfkit_eval import (
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)


def _fixture(directory: Path, *, test_targets: bool = False) -> Path:
    dataset = json.loads(json.dumps(dataset_document()))
    template = dataset['samples'][0]
    sources = [f'cal_{index}' for index in range(9)]
    dataset['samples'] = [{**template, 'source_id': source} for source in (*sources, 'test')]
    dataset['observations'] = [
        {
            'id': f'{source}_{index}',
            'source_id': source,
            'sample_id': 'one',
            'suction_kpa': pressure,
            'value': truth + 0.01 * (source_index + 1),
            'origin': 'synthetic',
            'review_status': 'confirmed',
            'quality_flags': [],
            'source_cells': [f'{source}!A{index + 1}'],
        }
        for source_index, source in enumerate(sources)
        for index, (pressure, truth) in enumerate(((0, 0.395), (HALF_WETNESS_KPA, 0.1975)))
    ]
    if test_targets:
        dataset['observations'].extend(
            [
                {
                    **dataset['observations'][0],
                    'id': f'held_out_{index}',
                    'source_id': 'test',
                    'suction_kpa': pressure,
                    'value': value,
                    'quality_flags': ['test_target_unavailable'],
                }
                for index, (pressure, value) in enumerate(((0, 0), (HALF_WETNESS_KPA, 1)))
            ]
        )
    path = write_run_fixture(directory, dataset=dataset)
    document = json.loads(path.read_text('utf-8'))
    document['prediction_intervals'] = [
        {
            'method': 'fixed_group_max_split_conformal_v1',
            'candidate_id': 'sand_a',
            'training_groups': [],
            'calibration_groups': [[source, ''] for source in sources],
            'test_groups': [['test', '']],
            'pressure_grid_kpa': [0, HALF_WETNESS_KPA],
            'confidence_level': 0.9,
            'minimum_calibration_groups': 9,
            'grouping': 'source',
        }
    ]
    path.write_text(json.dumps(document), encoding='utf-8')
    return path


def test_intervals_for_unlabelled_test_samples_do_not_consume_test_targets(tmp_path: Path):
    first = execute_retention_run(load_retention_run_plan(_fixture(tmp_path / 'first')))
    changed = execute_retention_run(
        load_retention_run_plan(_fixture(tmp_path / 'changed', test_targets=True))
    )
    interval_result = first.prediction_intervals[0]

    assert interval_result.status == 'computed'
    assert interval_result == changed.prediction_intervals[0]
    assert interval_result.calibration.half_width == pytest.approx(0.09)
    assert [point.predicted for point in interval_result.forecasts] == pytest.approx(
        [0.395, 0.1975]
    )
    assert [item.lower for item in interval_result.intervals] == pytest.approx([0.305, 0.1075])
    assert [item.upper for item in interval_result.intervals] == pytest.approx([0.485, 0.2875])
    assert all(point.prediction is None for point in changed.points if point.source_id == 'test')
    output = write_retention_run(first, tmp_path / 'output')
    assert (output / 'prediction-intervals.json').is_file()
    assert 'PTF prediction intervals' in read_retention_run_report(output)
    replay = execute_retention_run(load_retention_run_plan(output / 'run-plan.json'))
    assert replay.prediction_intervals == first.prediction_intervals
