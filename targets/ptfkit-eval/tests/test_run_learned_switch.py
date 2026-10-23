import json
import math
from dataclasses import replace
from pathlib import Path

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    HardSwitchGridFit,
    RetentionRunResult,
    diagnose_learned_switch_seams,
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


EXAMPLE = Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_hard_switch/run.json'


@pytest.fixture(scope='module')
def switch_result() -> RetentionRunResult:
    return execute_retention_run(load_retention_run_plan(EXAMPLE))


def test_public_switch_pipeline_has_fitted_seams_domains_and_portable_replay(
    tmp_path: Path, switch_result: RetentionRunResult
):
    result = switch_result
    assert result.learned_selection is not None
    assert result.learned_selection.method == 'nested_two_curve_selection_v1'
    assert result.learned_selection.protocols[1].status == 'computed'
    assert [
        fold.ensemble.outer_fit.switch_suction_kpa
        for fold in result.learned_selection.folds
        if isinstance(fold.ensemble.outer_fit, HardSwitchGridFit)
    ] == [1, 10, 1]
    assert len(result.learned_seams) == 12
    keys = {(seam.left.source_id, seam.left.sample_id) for seam in result.learned_seams}
    assert len(keys) == 12
    assert result.learned_applicability is not None
    assert len(result.learned_applicability.folds) == 24
    output = write_retention_run(result, tmp_path / 'run')
    report = read_retention_run_report(output)
    assert 'Nested two-curve ensemble selection' in report
    assert 'Fitted hard-switch diagnostics' in report
    artifact = json.loads((output / 'learned-seams.json').read_text('utf-8'))
    assert len(artifact) == 12
    assert {row['suction_kpa'] for row in artifact} == {1, 10}
    replay = execute_retention_run(load_retention_run_plan(output / 'run-plan.json'))
    assert replay.learned_selection == result.learned_selection
    assert replay.learned_seams == result.learned_seams
    assert replay.learned_applicability == result.learned_applicability


def test_fitted_seam_values_and_sign_follow_specification_equations(
    switch_result: RetentionRunResult,
):
    result = switch_result
    seams = [seam for seam in result.learned_seams if seam.suction_kpa == 10]
    assert len(seams) == 4
    for seam in seams:
        # Independent Clapp Table 2 sandy-loam values and Vereecken Table 7
        # regressions applied to the example's explicitly declared features.
        sample_index = int(seam.left.sample_id[-1]) - 1
        source_index = ord(seam.left.source_id[-1]) - ord('a')
        sand, density = 55 + source_index + sample_index, 1.35 + sample_index / 100
        alpha = math.exp(-2.486 + 0.025 * sand - 0.351 - 2.617 * density - 0.023 * 15)
        n = math.exp(0.053 - 0.009 * sand - 0.013 * 15 + 0.00015 * sand * sand)
        theta_s = 0.81 - 0.283 * density + 0.001 * 15
        right = 0.104 + (theta_s - 0.104) / (1 + (alpha * 10 / 0.0980665) ** n)
        left = 0.435 * (7.18 * 0.0980665 / 10) ** (1 / 4.9)
        assert seam.status == 'computed'
        assert seam.left.predicted == pytest.approx(left)
        assert seam.right.predicted == pytest.approx(right)
        assert abs(right - left) > 1e-3
        assert seam.right_minus_left == pytest.approx(right - left)
        assert seam.left.input_traces[0].source_cells
        assert seam.right.input_traces[0].source_cells


def test_locked_seam_diagnostics_do_not_consume_observations_or_refit_boundaries(
    switch_result: RetentionRunResult,
):
    result = switch_result
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    dataset['observations'] = []
    changed = replace(result, plan=replace(result.plan, dataset=load_retention_dataset(dataset)))
    assert diagnose_learned_switch_seams(changed) == result.learned_seams
    assert changed.learned_selection == result.learned_selection


def test_missing_member_input_stays_visible_at_a_locked_seam(switch_result: RetentionRunResult):
    result = switch_result
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    first = result.learned_seams[0]
    key = (first.left.source_id, first.left.sample_id)
    for sample in dataset['samples']:
        if (sample['source_id'], sample['sample_id']) == key:
            for feature in sample['features']:
                if feature['id'] == 'carbon':
                    feature['value'] = None
    changed = replace(result, plan=replace(result.plan, dataset=load_retention_dataset(dataset)))
    diagnostics = diagnose_learned_switch_seams(changed)
    assert len(diagnostics) == 12
    failed = next(seam for seam in diagnostics if (seam.left.source_id, seam.left.sample_id) == key)
    assert failed.suction_kpa == first.suction_kpa
    assert failed.status == 'unavailable'
    assert failed.left.predicted is not None
    assert failed.right.predicted is None
    assert failed.right.reasons == ('missing_input',)
    assert failed.right_minus_left is None


@pytest.mark.parametrize(
    'change', ['older_protocol', 'outside_domain', 'duplicate_grid', 'unknown_owner']
)
def test_invalid_switch_documents_fail_plan_validation(change: str):
    plan = load_retention_run_plan(EXAMPLE)
    document = json.loads(canonical_json(plan.document))
    learned = document['learned_selection']
    switch = learned['ensembles'][0]
    if change == 'older_protocol':
        learned['method'] = 'nested_convex_pair_selection_v1'
    elif change == 'outside_domain':
        switch['boundary_grid_kpa'] = [0.01, 10]
    elif change == 'duplicate_grid':
        switch['boundary_grid_kpa'] = [10, 10]
    else:
        switch['boundary_member'] = 'nearest'
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(document, base_directory=EXAMPLE.parent)
