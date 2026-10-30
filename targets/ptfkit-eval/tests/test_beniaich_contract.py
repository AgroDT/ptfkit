"""Independent source cases for manifest-driven gravimetric PTF evaluation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from _run_fixtures import dataset_document, write_run_fixture

from ptfkit_eval import (
    FixedPointPrediction,
    FunctionCurveCandidate,
    PlanValidationError,
    execute_retention_run,
    load_evaluation_plan,
    load_retention_run_plan,
)
from ptfkit_eval.documents import canonical_json


if TYPE_CHECKING:
    from pathlib import Path

    from ptfkit_eval import RetentionRunResult


TARGET = {
    'quantity': 'gravimetric_water_content',
    'unit': 'mass_fraction',
    'material_basis': 'fine_earth',
    'denominator_basis': 'dry_soil_mass',
}
METHOD = 'klute1986_disturbed_ring_retention'


def _evaluation(function: str, output: str = 'water_field_capacity') -> dict:
    return {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'retention',
                'kind': 'function_point',
                'function': function,
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'linear',
                },
                'target': dict(TARGET),
                'prediction': {'kind': 'fixed_output', 'name': output},
            }
        ],
    }


def _run(
    tmp_path: Path,
    *,
    method: str = 'bouyoucos1962_hydrometer_hexametaphosphate_5_percent',
    clay_upper: float = 2,
    origin: str = 'synthetic',
    organic_matter: bool = False,
    organic_quantity: str = 'organic_matter_content',
) -> RetentionRunResult:
    input_name = 'soil_organic_matter' if organic_matter else 'clay'
    function = 'calc_ptf_beniaich2023_slr6' if organic_matter else 'calc_ptf_beniaich2023_slr1'
    dataset = json.loads(json.dumps(dataset_document()))
    dataset.update(schema_version=2, target=dict(TARGET), method=METHOD)
    dataset['source_files'] = [{'id': 'fixture', 'filename': 'fixture.json', 'sha256': 'a' * 64}]
    for sample in dataset['samples']:
        sample['features'] = [
            {
                'id': input_name,
                'kind': 'numeric',
                'value': 2 if organic_matter else 20,
                'review_status': 'confirmed',
                'origin': origin,
                'source_file': 'fixture',
                'source_cells': ['fixture!A1'],
                'measurement': {
                    'quantity': organic_quantity if organic_matter else 'particle_mass_fraction',
                    'unit': 'mass_percent',
                    'basis': {'material': 'fine_earth', 'denominator': 'dry_mass'},
                    'method': method,
                    'conditions': [],
                    'particle_size': None
                    if organic_matter
                    else {
                        'unit': 'micrometer',
                        'lower': None,
                        'upper': {'value': clay_upper, 'inclusive': False},
                    },
                },
            }
        ]
    for index, point in enumerate(dataset['observations']):
        point.update(
            suction_kpa=33 if index % 2 == 0 else 1500, value=0.2 if index % 2 == 0 else 0.1
        )
    path = write_run_fixture(tmp_path, dataset=dataset, evaluation=_evaluation(function))
    document = json.loads(path.read_bytes())
    document['protocol'].update(
        observation_method=METHOD, bindings={function: {input_name: input_name}}
    )
    path.write_bytes(canonical_json(document))
    return execute_retention_run(load_retention_run_plan(path))


@pytest.mark.parametrize(
    'name', [*(f'slr{i}' for i in range(1, 7)), *(f'mlr{i}' for i in range(1, 6))]
)
def test_reviewed_regressions_resolve_both_explicit_pressure_outputs(name: str):
    for output, pressure in [('water_field_capacity', 33), ('water_wilting_point', 1500)]:
        candidate = load_evaluation_plan(_evaluation(f'calc_ptf_beniaich2023_{name}', output))
        resolved = candidate.candidates[0]
        assert isinstance(resolved, FunctionCurveCandidate)
        assert isinstance(resolved.curve.prediction, FixedPointPrediction)
        assert resolved.curve.prediction.axis_value == pressure


def test_capillary_saturation_is_not_assigned_an_unreported_zero_pressure():
    with pytest.raises(PlanValidationError) as caught:
        load_evaluation_plan(_evaluation('calc_ptf_beniaich2023_slr1', 'water_saturation'))
    assert any('condition' in item.code for item in caught.value.diagnostics)


def test_native_clay_regression_preserves_table_five_scale_and_pressure_support(tmp_path: Path):
    result = _run(tmp_path)
    scored = [point for point in result.points if point.eligible]
    assert len(scored) == 2
    for point in scored:
        assert point.comparison is not None
        # Table 5: (10.277 + 0.365 * 20) percent = 0.17577 g/g.
        assert point.comparison.predicted == pytest.approx(0.17577)
        assert point.comparison.water_quantity == 'gravimetric_water_content'
    assert all(
        'pressure_condition_mismatch' in point.reasons
        for point in result.points
        if not point.eligible
    )
    for cohort in result.cohorts:
        assert cohort.cohort.summary is not None
        assert cohort.cohort.summary.metrics.mean_error == pytest.approx(-0.02423)
        assert cohort.cohort.summary.metrics.root_mean_squared_error == pytest.approx(0.02423)


def test_organic_matter_quantity_is_not_interchanged_with_organic_carbon(tmp_path: Path):
    result = _run(
        tmp_path / 'matter', organic_matter=True, method='walkley_black_carbon_times_1_724'
    )
    scored = [point for point in result.points if point.eligible]
    assert len(scored) == 2
    for point in scored:
        assert point.comparison is not None
        # Table 5: (21.331 + 1.339 * 2) / 100 = 0.24009 g/g.
        assert point.comparison.predicted == pytest.approx(0.24009)
    carbon = _run(
        tmp_path / 'carbon',
        organic_matter=True,
        method='walkley_black_carbon_times_1_724',
        organic_quantity='organic_carbon_content',
    )
    assert not any(point.eligible for point in carbon.points)
    assert any('quantity_mismatch' in point.reasons for point in carbon.points)


@pytest.mark.parametrize(
    ('changes', 'reason'),
    [
        ({'method': 'laser_diffraction'}, 'method_mismatch'),
        ({'clay_upper': 1}, 'particle_boundary_mismatch'),
        ({'origin': 'derived'}, 'unverified_derivation'),
    ],
)
def test_incompatible_or_unverified_predictors_remain_excluded(
    tmp_path: Path,
    changes: dict,
    reason: str,
):
    result = _run(tmp_path, **changes)
    assert len(result.points) == 4
    assert not any(point.eligible for point in result.points)
    assert any(reason in point.reasons for point in result.points)
