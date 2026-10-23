import json
from dataclasses import replace
from pathlib import Path

import pytest
from _run_fixtures import evaluation_document, write_run_fixture

from ptfkit_eval import (
    EvaluationDocumentError,
    RetentionBootstrapError,
    compare_retention_run_pairs,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)


def _plan_document(directory: Path) -> dict[str, object]:
    path = write_run_fixture(directory)
    document = json.loads(path.read_text('utf-8'))
    document['paired_comparisons'] = [
        {
            'method': 'paired_cluster_percentile_linear_v1',
            'left_candidate_id': 'sand_a',
            'right_candidate_id': 'sand_b',
            'cohort': 'run_common',
        }
    ]
    return document


def test_registered_pair_uses_public_run_predictions_and_replays(tmp_path: Path):
    document = _plan_document(tmp_path / 'inputs')
    result = execute_retention_run(
        load_retention_run_plan(document, base_directory=tmp_path / 'inputs')
    )
    assert len(result.paired_comparisons) == 1
    pair = result.paired_comparisons[0]
    assert pair.status == 'computed'
    assert pair.left.candidate_id == 'sand_a'
    assert pair.right.candidate_id == 'sand_b'
    assert pair.differences is not None
    assert pair.differences.root_mean_squared_error == 0
    assert pair.intervals is not None
    assert (
        pair.intervals.root_mean_squared_error.lower,
        pair.intervals.root_mean_squared_error.upper,
    ) == (0, 0)
    output = write_retention_run(result, tmp_path / 'run')
    assert 'Paired candidate differences' in read_retention_run_report(output)
    artifact = json.loads((output / 'paired-comparisons.json').read_text('utf-8'))
    assert artifact[0]['left']['candidate_id'] == 'sand_a'
    assert artifact[0]['intervals']['root_mean_squared_error'] == {'lower': 0, 'upper': 0}
    replay = execute_retention_run(load_retention_run_plan(output / 'run-plan.json'))
    assert replay.paired_comparisons == result.paired_comparisons


def test_empty_third_candidate_prevents_pair_only_common_cohort_substitution(tmp_path: Path):
    document = _plan_document(tmp_path)
    evaluation = evaluation_document()
    candidates = json.loads(json.dumps(evaluation))['candidates']
    candidates.append({**candidates[0], 'id': 'empty'})
    # Rewrite the fixture and bind its changed candidate document through its checksum.
    path = write_run_fixture(tmp_path, evaluation={**evaluation, 'candidates': candidates})
    fresh = json.loads(path.read_text('utf-8'))
    fresh['paired_comparisons'] = document['paired_comparisons']
    result = execute_retention_run(load_retention_run_plan(fresh, base_directory=tmp_path))
    assert all(point.comparison is not None for point in result.points)
    points = tuple(
        replace(point, comparison=None, prediction=None, reasons=('execution_failed',))
        if point.candidate_id == 'empty'
        else point
        for point in result.points
    )
    pairs = compare_retention_run_pairs(replace(result, points=points))
    assert len(pairs) == 1
    assert pairs[0].reason == 'empty_cohort'
    assert pairs[0].left.comparisons == pairs[0].right.comparisons == ()
    assert pairs[0].intervals is None


@pytest.mark.parametrize('change', ['unknown', 'self', 'duplicate', 'reverse', 'cohort', 'method'])
def test_invalid_pair_registrations_are_rejected(tmp_path: Path, change: str):
    document = json.loads(json.dumps(_plan_document(tmp_path)))
    policy = document['paired_comparisons'][0]
    if change == 'unknown':
        policy['left_candidate_id'] = 'unknown'
    elif change == 'self':
        policy['right_candidate_id'] = 'sand_a'
    elif change == 'duplicate':
        document['paired_comparisons'].append(dict(policy))
    elif change == 'reverse':
        document['paired_comparisons'].append(
            {**policy, 'left_candidate_id': 'sand_b', 'right_candidate_id': 'sand_a'}
        )
    elif change == 'cohort':
        policy['cohort'] = 'maximal'
    else:
        policy['method'] = 'independent_bootstrap'
    with pytest.raises((EvaluationDocumentError, RetentionBootstrapError)):
        load_retention_run_plan(document, base_directory=tmp_path)
