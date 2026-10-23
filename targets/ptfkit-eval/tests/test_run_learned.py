import json
from dataclasses import replace
from pathlib import Path

import pytest

from ptfkit_eval import (
    ConvexPairFit,
    EvaluationDocumentError,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


EXAMPLE = Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_retention/run.json'


def test_public_run_trains_convex_weights_and_replays_all_evidence(tmp_path: Path):
    plan = load_retention_run_plan(EXAMPLE)
    plan = replace(plan, approximations=(), bootstrap=replace(plan.bootstrap, n_resamples=16))
    result = execute_retention_run(plan)
    learned = result.learned_selection
    assert learned is not None
    assert learned.status == 'computed'
    assert len(learned.folds) == 3
    fits = [
        evidence.fit
        for fold in learned.folds
        for score in fold.ensemble.inner_scores
        for evidence in score.folds
        if evidence.fit is not None
    ]
    assert len(fits) == 6
    assert all(isinstance(fit, ConvexPairFit) and fit.left_weight is not None for fit in fits)
    baseline = execute_retention_run(replace(plan, learned_selection=None))
    assert result.points == baseline.points
    assert result.selection == baseline.selection
    output = write_retention_run(result, tmp_path / 'run')
    assert 'Nested convex ensemble selection' in read_retention_run_report(output)
    saved = json.loads((output / 'learned-selection.json').read_text('utf-8'))
    assert saved['status'] == 'computed'
    assert len(saved['folds']) == 3
    replay_plan = load_retention_run_plan(output / 'run-plan.json')
    # The persisted document retains the original approximation/bootstrap registration;
    # neither changes learned selection's training or scoring path.
    replay = execute_retention_run(
        replace(replay_plan, approximations=(), bootstrap=replace(plan.bootstrap, n_resamples=16))
    )
    assert replay.learned_selection == result.learned_selection


@pytest.mark.parametrize(
    'change',
    [
        'unknown_member',
        'composite_member',
        'collision',
        'duplicate',
        'unsupported_domains',
        'method',
    ],
)
def test_learned_run_registration_is_rejected_before_execution(change: str):
    plan = load_retention_run_plan(EXAMPLE)
    document = json.loads(canonical_json(plan.document))
    learned = document['learned_selection']
    ensemble = learned['ensembles'][0]
    if change == 'unknown_member':
        ensemble['left_candidate_id'] = 'absent'
    elif change == 'composite_member':
        ensemble['left_candidate_id'] = 'fixed_blend'
    elif change == 'collision':
        ensemble['id'] = 'clapp'
    elif change == 'duplicate':
        learned['ensembles'].append(dict(ensemble))
    elif change == 'unsupported_domains':
        learned['fixed_selection']['empirical_domains'] = document['selection']['empirical_domains']
    else:
        ensemble['method'] = 'fit_to_test_targets'
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(document, base_directory=EXAMPLE.parent)
