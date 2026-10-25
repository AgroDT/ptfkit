"""Protect mass-basis evaluation without silently changing volume-basis contracts."""

import json
import sys
from dataclasses import replace
from pathlib import Path
from types import ModuleType

import pytest
from _run_fixtures import dataset_document, write_run_fixture
from ptfkit import get_manifest

from ptfkit_eval import (
    ClusterBootstrapPlan,
    ConformalPlanError,
    EvaluationDocumentError,
    GroupedConformalPlan,
    RetentionComparison,
    RetentionFitError,
    RetentionFitPlan,
    RetentionMetricsError,
    RetentionSeriesPoint,
    TargetSpec,
    bootstrap_retention_errors,
    diagnose_retention_run,
    diagnose_retention_series,
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    read_retention_run_report,
    summarize_retention_errors,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


MASS_TARGET = {
    'quantity': 'gravimetric_water_content',
    'unit': 'mass_fraction',
    'material_basis': 'soil',
    'denominator_basis': 'dry_soil_mass',
}


@pytest.mark.parametrize('family', ['van_genuchten_mualem_v1', 'brooks_corey_v1'])
def test_volume_only_approximation_contracts_reject_mass_targets_before_solving(family: str):
    target = TargetSpec('gravimetric_water_content', 'mass_fraction', 'soil', 'dry_soil_mass')
    with pytest.raises(RetentionFitError, match='canonical volumetric'):
        RetentionFitPlan(
            family_id=family,
            target=target,
            parameters=(),
            seed=7,
            minimum_log10_span=2,
        )


def test_volume_only_conformal_protocol_rejects_mass_targets():
    target = TargetSpec('gravimetric_water_content', 'mass_fraction', 'soil', 'dry_soil_mass')
    with pytest.raises(ConformalPlanError, match='canonical volumetric'):
        GroupedConformalPlan(
            candidate_id='mass',
            protocol_id='test',
            target=target,
            calibration_groups=(),
            training_groups=(),
            test_groups=(),
            pressure_grid_kpa=(33,),
        )


@pytest.mark.parametrize(
    'changes',
    [{'schema_version': 1}, {'unit': 'volume_fraction'}, {'denominator_basis': 'bulk_volume'}],
)
def test_gravimetric_contract_requires_version_two_and_matching_unit_and_basis(changes: dict):
    document = json.loads(json.dumps(dataset_document()))
    document.update(schema_version=2, target=dict(MASS_TARGET))
    document['observations'][0]['value'] = 1.25
    assert load_retention_dataset(document).target.quantity == 'gravimetric_water_content'
    if 'schema_version' in changes:
        document.update(changes)
    else:
        document['target'].update(changes)
    with pytest.raises(EvaluationDocumentError):
        load_retention_dataset(document)


def test_mass_metrics_and_cluster_intervals_retain_values_above_one_and_reject_mixed_quantities():
    points = tuple(
        RetentionComparison(
            source, 'one', 33, 1.25, 1.5, water_quantity='gravimetric_water_content'
        )
        for source in ('a', 'b')
    )
    summary = summarize_retention_errors(points)
    assert summary.water_quantity == 'gravimetric_water_content'
    assert summary.metrics.mean_error == 0.25
    assert summary.metrics.root_mean_squared_error == 0.25
    result = bootstrap_retention_errors(
        points,
        plan=ClusterBootstrapPlan(seed=9, minimum_groups=2, n_resamples=16),
    )
    assert result.intervals is not None
    assert result.intervals.mean_error.lower == result.intervals.mean_error.upper == 0.25
    with pytest.raises(RetentionMetricsError, match='share one water quantity'):
        summarize_retention_errors(
            (points[0], replace(points[1], observed=0.5, water_quantity='volumetric_water_content'))
        )
    with pytest.raises(RetentionMetricsError, match='volume fraction'):
        summarize_retention_errors((replace(points[0], water_quantity='volumetric_water_content'),))


def test_mass_quality_has_no_universal_upper_bound_but_preserves_negative_and_monotonicity_flags():
    points = (RetentionSeriesPoint(1, 1.5, 'wet'), RetentionSeriesPoint(33, 1.25, 'dry'))
    assert (
        diagnose_retention_series(points, water_quantity='gravimetric_water_content').diagnostics
        == ()
    )
    assert len(diagnose_retention_series(points).diagnostics) == 2
    invalid = (RetentionSeriesPoint(1, -0.1, 'negative'), RetentionSeriesPoint(33, 0.1, 'increase'))
    findings = diagnose_retention_series(invalid, water_quantity='gravimetric_water_content')
    assert [item.code for item in findings.diagnostics] == [
        'water_outside_physical_bounds',
        'increasing_water_with_suction',
    ]


def test_native_fixed_mass_output_converts_percent_and_publishes_mass_metrics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    # A test-only fixed function isolates unit conversion from any scientific PTF formula.
    module = ModuleType('synthetic_mass_function')
    module.__dict__['fixed_mass'] = lambda: 150.0
    monkeypatch.setitem(sys.modules, module.__name__, module)
    manifest = json.loads(canonical_json(get_manifest()))
    manifest['functions'].append(
        {
            'id': 'fixed_mass',
            'module': module.__name__,
            'callable': 'fixed_mass',
            'models': {'h_theta': None, 'k_h': None},
            'inputs': [],
            'outputs': [
                {
                    'name': 'water',
                    'kind': 'numeric',
                    'measurement': {
                        'quantity': 'gravimetric_water_content',
                        'unit': 'mass_percent',
                        'basis': {'material': 'soil', 'denominator': 'dry_soil_mass'},
                        'role': 'prediction',
                        'method': None,
                        'conditions': [
                            {
                                'quantity': 'matric_potential',
                                'value': 33,
                                'unit': 'kilopascal',
                                'convention': 'magnitude',
                            }
                        ],
                    },
                }
            ],
        }
    )
    dataset = json.loads(json.dumps(dataset_document()))
    dataset.update(schema_version=2, target=dict(MASS_TARGET))
    dataset['observations'] = [
        {**dataset['observations'][index], 'suction_kpa': 33, 'value': water}
        for index, water in ((0, 1.25), (2, 1.75))
    ]
    evaluation: dict[str, object] = {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'mass',
                'kind': 'function_point',
                'function': 'fixed_mass',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'linear',
                },
                'target': dict(MASS_TARGET),
                'prediction': {'kind': 'fixed_output', 'name': 'water'},
            }
        ],
    }
    path = write_run_fixture(tmp_path / 'inputs', dataset=dataset, evaluation=evaluation)
    document = json.loads(path.read_bytes())
    document['protocol']['bindings'] = {'fixed_mass': {}}
    path.write_bytes(canonical_json(document))
    result = execute_retention_run(load_retention_run_plan(path, manifest=manifest))
    assert len(result.points) == 2
    assert all(point.eligible for point in result.points)
    for point in result.points:
        assert point.comparison is not None
        assert point.comparison.predicted == 1.5
        assert point.comparison.water_quantity == 'gravimetric_water_content'
    assert len(result.cohorts) == 2
    for cohort in result.cohorts:
        assert cohort.cohort.summary is not None
        assert cohort.cohort.summary.metrics.mean_error == 0
        assert cohort.cohort.summary.metrics.root_mean_squared_error == 0.25
    assert all(not item.quality.diagnostics for item in diagnose_retention_run(result))
    output = write_retention_run(result, tmp_path / 'published')
    assert 'mass fractions' in read_retention_run_report(output)
