import json
import math
import runpy
from decimal import Decimal
from pathlib import Path

import pytest

from ptfkit_eval import execute_retention_run, load_retention_run_plan


GENERATOR = (
    Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_training_risk/generate.py'
)


def test_larger_constructed_population_supplies_actual_independent_blocks_and_nonvacuous_bounds(
    tmp_path: Path,
):
    generate = runpy.run_path(str(GENERATOR))['generate']
    source = generate(tmp_path / 'inputs', n_blocks=20, metric_resamples=2)
    plan = load_retention_run_plan(source)
    assert str(plan.dataset.document['dataset_id']).endswith('_seed_20261023')
    result = execute_retention_run(plan)
    for policy in result.independent_training_risk:
        groups = [
            group
            for block in policy.blocks
            for group in (*block.roles.training_groups, *block.roles.test_groups)
        ]
        assert len(groups) == len({g.group_id for g in groups}) == 120
        assert len({sample for g in groups for sample in g.samples}) == 240
        assert all(len(g.samples) == 2 for g in groups)
        assert policy.bound.training_failure_count == 0
        assert policy.bound.test_sample_count == 80
        assert policy.bound.plan.training_groups_per_block == 4
        success = policy.bound.training_success_probability_interval
        assert success is not None
        # Three two-sided events, q=2, alpha=.05, n=20. Observed success
        # alone does not make the prior failure probability exactly zero.
        radius = float((Decimal(240).ln() / 40).sqrt())
        assert success.lower == pytest.approx(1 - radius)
        assert success.upper == 1
        risk = policy.bound.successful_training_mean_risk_interval
        assert risk is not None
        assert 0 <= risk.lower < risk.upper < 1
        assert policy.bound.unconditional_model_risk_interval is None
    ensemble = result.independent_training_risk[1]
    assert all(b.selection.folds[0].ensemble.outer_fit is not None for b in ensemble.blocks)
    generation = json.loads((source.parent / 'generation.json').read_text(encoding='utf-8'))
    assert generation['population_seed'] == 20261023
    assert generation['original_group_count'] == 120


def test_population_and_allocation_seeds_are_separate_reproducible_input_choices(tmp_path: Path):
    generate = runpy.run_path(str(GENERATOR))['generate']
    first = generate(tmp_path / 'first', n_blocks=2, metric_resamples=2)
    replay = generate(tmp_path / 'replay', n_blocks=2, metric_resamples=2)
    changed_allocation = generate(
        tmp_path / 'allocation', n_blocks=2, allocation_seed=72, metric_resamples=2
    )
    changed_population = generate(
        tmp_path / 'population', n_blocks=2, population_seed=17, metric_resamples=2
    )
    for name in ('dataset.json', 'evaluation_plan.json', 'run.json', 'generation.json'):
        assert (first.parent / name).read_bytes() == (replay.parent / name).read_bytes()
    assert (first.parent / 'dataset.json').read_bytes() == (
        changed_allocation.parent / 'dataset.json'
    ).read_bytes()
    assert (first.parent / 'dataset.json').read_bytes() != (
        changed_population.parent / 'dataset.json'
    ).read_bytes()
    original_data = json.loads((first.parent / 'dataset.json').read_text(encoding='utf-8'))
    changed_data = json.loads(
        (changed_population.parent / 'dataset.json').read_text(encoding='utf-8')
    )
    assert [row['value'] for row in original_data['observations']] != [
        row['value'] for row in changed_data['observations']
    ]
    before = load_retention_run_plan(first)
    after = load_retention_run_plan(changed_allocation)
    assert [p.seed for p in before.independent_training_risk] == [71, 71]
    assert [p.seed for p in after.independent_training_risk] == [72, 72]


def test_point_generator_preserves_population_and_supplies_nonvacuous_four_policy_bounds(
    tmp_path: Path,
):
    generate = runpy.run_path(str(GENERATOR))['generate']
    ordinary = generate(tmp_path / 'ordinary', n_blocks=20, metric_resamples=2)
    source = generate(
        tmp_path / 'points', n_blocks=20, metric_resamples=2, point_metrics=True, paired=True
    )
    assert (ordinary.parent / 'dataset.json').read_bytes() == (
        source.parent / 'dataset.json'
    ).read_bytes()
    result = execute_retention_run(load_retention_run_plan(source))
    assert len(result.point_training_risk) == 4
    assert not result.independent_training_risk
    for item in result.point_training_risk:
        assert item.bound.training_failure_count == 0
        assert item.bound.test_sample_count == 80
        success = item.bound.training_success_probability_interval
        risk = item.bound.successful_training_mean_risk_interval
        assert success is not None
        assert risk is not None
        assert success.lower == pytest.approx(1 - float((Decimal(480).ln() / 40).sqrt()))
        assert 0 <= risk.lower < risk.upper < 1
        if item.assessment_loss.metric == 'mse':
            rmse = item.successful_training_pooled_rmse_interval
            assert rmse is not None
            assert rmse.lower == pytest.approx(math.sqrt(risk.lower))
            assert rmse.upper == pytest.approx(math.sqrt(risk.upper))
        assert item.unconditional_pooled_rmse_interval is None
    paired = result.paired_training_risk
    assert paired is not None
    assert paired.bound.plan.bounds.simultaneous_policy_count == 1
    assert paired.bound.joint_success_mean_risk_difference_interval is not None
    generation = json.loads((source.parent / 'generation.json').read_text(encoding='utf-8'))
    assert generation['point_metrics'] is True
    assert generation['paired'] is True
