import copy
import math
import runpy
from pathlib import Path

import pytest

from ptfkit_eval import (
    FitParameterRange,
    RetentionFitPlan,
    RetentionSeriesPoint,
    TargetSpec,
    fit_retention_family,
)


def test_policy_comparison_preserves_failures_and_rejects_incomparable_inputs():
    script = (
        Path(__file__).resolve().parents[3] / 'evaluation/experiments/measured_retention/compare.py'
    )
    compare = runpy.run_path(str(script))['compare']
    baseline: dict = {
        'dataset_sha256': 'a' * 64,
        'results': [
            {
                'source_id': 'source',
                'sample_id': 'sample',
                'fit': {
                    'plan': {'family_id': 'brooks_corey_v1'},
                    'observations': [0.4],
                    'status': 'fitted',
                    'reason': None,
                    'attempts': [{'converged': True, 'sum_squared_error': 1.0}],
                },
                'profile_optimality': {'status': 'lower_objective_found'},
            }
        ],
    }
    candidate = copy.deepcopy(baseline)
    record = candidate['results'][0]
    record['fit']['plan']['restart_policy'] = 'brooks_corey_interval_solves_v1'
    record['fit']['status'], record['fit']['reason'] = 'failed', 'boundary_solution'
    record['fit']['attempts'][0]['sum_squared_error'] = 0.5
    record['profile_optimality'] = None
    result = compare(baseline, candidate)['families'][0]
    assert result['counts'] == {
        'samples': 1,
        'fitted_to_failed': 1,
        'comparable_objectives': 1,
        'improved_objectives': 1,
        'worsened_objectives': 0,
        'baseline_profile_counterexamples': 1,
        'candidate_profile_counterexamples': 0,
    }
    assert result['candidate_reasons'] == {'boundary_solution': 1}
    record['fit']['observations'] = []
    with pytest.raises(ValueError, match='identical observations'):
        compare(baseline, candidate)


def test_refit_audit_profiles_every_parameter_against_the_refitted_objective():
    script = (
        Path(__file__).resolve().parents[3] / 'evaluation/experiments/measured_retention/fit.py'
    )
    audit = runpy.run_path(str(script))['_audit_refit']
    plan = RetentionFitPlan(
        family_id='brooks_corey_v1',
        target=TargetSpec(
            'volumetric_water_content', 'volume_fraction', 'unspecified', 'bulk_volume'
        ),
        seed=7123,
        minimum_log10_span=2,
        parameters=(
            FitParameterRange('theta_r', 0, 0.2, 0.05),
            FitParameterRange('theta_s', 0.3, 0.8, 0.45),
            FitParameterRange('air_entry', 1, 30, 7),
            FitParameterRange('lambda', 0.1, 2, 0.8),
        ),
    )
    points = tuple(
        RetentionSeriesPoint(h, 0.5 if h <= 10 else 0.1 + 0.4 * math.sqrt(10 / h), str(h))
        for h in (0, 0.1, 1, 5, 20, 50, 100, 1000, 10000)
    )
    result = fit_retention_family(points, plan=plan)
    assert result.status == 'fitted'
    output = audit(result, 3)
    profiles = output['parameter_profiles']
    assert [item['profile']['parameter_name'] for item in profiles] == [
        'theta_r',
        'theta_s',
        'air_entry',
        'lambda',
    ]
    for item, bounds in zip(profiles, plan.parameters, strict=True):
        profile = item['profile']
        assert profile['residual_degrees_of_freedom'] == 5
        assert profile['parameter_bounds'] == [bounds.lower, bounds.upper]
        assert profile['baseline_sum_squared_error'] == pytest.approx(0, abs=1e-15)
        assert profile['points'][0]['fixed_value'] == bounds.lower
        assert profile['points'][-1]['fixed_value'] == bounds.upper
        assert item['optimality']['status'] == 'no_improvement_detected'
    assert output['uncertainty_support']['status'] == 'diagnosed'
    assert audit(None, 3) is None
    assert audit(fit_retention_family([], plan=plan), 3) is None
