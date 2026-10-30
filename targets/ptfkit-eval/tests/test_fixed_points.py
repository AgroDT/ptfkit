import copy
import hashlib
import json
from pathlib import Path
from typing import cast

import pytest
from _run_fixtures import dataset_document, write_run_fixture
from ptfkit import get_manifest

from ptfkit_eval import (
    CurveExecutionError,
    EvaluationDocumentError,
    FixedPointPrediction,
    FunctionPointCandidate,
    PlanValidationError,
    evaluate_candidate,
    execute_retention_run,
    load_evaluation_plan,
    load_retention_run_plan,
)
from ptfkit_eval.documents import plain


def _evaluation() -> dict[str, object]:
    return {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': f'point_{pressure}',
                'kind': 'function_point',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'linear',
                },
                'target': {
                    'quantity': 'volumetric_water_content',
                    'unit': 'volume_fraction',
                    'material_basis': 'soil',
                    'denominator_basis': 'bulk_volume',
                },
                'function': f'calc_ptf_gunarathna2019_vwc{pressure}_set1',
                'prediction': {'kind': 'fixed_output', 'name': f'theta_{pressure}'},
            }
            for pressure in (10, 33, 1500)
        ],
    }


@pytest.mark.parametrize(('pressure', 'expected'), [(10, 0.2952), (33, 0.2607), (1500, 0.1926)])
def test_executes_scalar_public_outputs_only_at_the_manifest_pressure(
    pressure: int, expected: float
):
    plan = load_evaluation_plan(_evaluation())
    candidate = next(
        candidate for candidate in plan.candidates if candidate.id == f'point_{pressure}'
    )
    assert isinstance(candidate, FunctionPointCandidate)
    assert isinstance(candidate.curve.prediction, FixedPointPrediction)
    assert candidate.curve.prediction.method == 'pressure_plate'

    # Hand substitution of 50 percent sand into the reviewed Table 3 Set 1 regressions.
    result = evaluate_candidate(candidate, [float(pressure)], {'sand': 50.0})
    assert result.points[0].value == pytest.approx(expected)
    with pytest.raises(CurveExecutionError, match='another pressure'):
        evaluate_candidate(candidate, [pressure + 0.01], {'sand': 50.0})


def _write_point_fixture(directory: Path) -> Path:
    document = json.loads(json.dumps(dataset_document()))
    document['target']['material_basis'] = 'soil'
    document['method'] = 'pressure_plate'
    for sample in document['samples']:
        sample['features'] = [
            {
                'id': 'sand',
                'kind': 'numeric',
                'value': 50.0,
                'review_status': 'confirmed',
                'origin': 'synthetic',
                'source_cells': ['synthetic!A1'],
                'measurement': {
                    'quantity': 'particle_mass_fraction',
                    'unit': 'mass_percent',
                    'basis': {'material': 'fine_earth', 'denominator': 'dry_mass'},
                    'method': 'sieve_analysis',
                    'conditions': [],
                    'particle_size': {
                        'unit': 'micrometer',
                        'lower': {'value': 50, 'inclusive': True},
                        'upper': {'value': 2000, 'inclusive': False},
                    },
                },
            }
        ]
    document['observations'] = [
        {
            'id': f'{source}_{pressure}',
            'source_id': source,
            'sample_id': 'one',
            'suction_kpa': pressure,
            'value': 0.25,
            'origin': 'synthetic',
            'review_status': 'confirmed',
            'quality_flags': [],
            'source_cells': ['synthetic!B1'],
        }
        for source in ('a', 'b')
        for pressure in (10, 33, 1500)
    ]
    path = write_run_fixture(directory, dataset=document, evaluation=_evaluation())
    run = json.loads(path.read_text('utf-8'))
    run['protocol']['observation_method'] = 'pressure_plate'
    run['protocol']['bindings'] = {
        f'calc_ptf_gunarathna2019_vwc{pressure}_set1': {'sand': 'sand'}
        for pressure in (10, 33, 1500)
    }
    path.write_text(json.dumps(run), encoding='utf-8')
    return path


def test_run_accounts_for_pressure_mismatches_without_interpolating_or_hiding_candidates(
    tmp_path: Path,
):
    result = execute_retention_run(load_retention_run_plan(_write_point_fixture(tmp_path)))

    assert len(result.points) == 18
    assert sum(point.eligible for point in result.points) == 6
    excluded = [point for point in result.points if not point.eligible]
    assert len(excluded) == 12
    assert all(point.reasons == ('pressure_condition_mismatch',) for point in excluded)
    assert all(point.prediction is None for point in excluded)
    maximal = [item for item in result.cohorts if item.cohort.kind == 'maximal']
    common = [item for item in result.cohorts if item.cohort.kind == 'common']
    assert [len(item.cohort.comparisons) for item in maximal] == [2, 2, 2]
    assert all(item.confidence.status == 'computed' for item in maximal)
    assert all(item.cohort.status == 'empty_cohort' for item in common)


def test_run_rejects_a_target_method_name_mismatch(tmp_path: Path):
    path = _write_point_fixture(tmp_path)
    dataset = json.loads((tmp_path / 'dataset.json').read_text('utf-8'))
    dataset['method'] = 'hanging_column'
    contents = json.dumps(dataset).encode('utf-8')
    (tmp_path / 'dataset.json').write_bytes(contents)
    run = json.loads(path.read_text('utf-8'))
    run['dataset']['sha256'] = hashlib.sha256(contents).hexdigest()
    run['protocol']['observation_method'] = 'hanging_column'
    path.write_text(json.dumps(run), encoding='utf-8')
    with pytest.raises(EvaluationDocumentError, match='Fixed-output observation method'):
        load_retention_run_plan(path)


@pytest.mark.parametrize(
    'conditions',
    [
        [],
        [{'quantity': 'temperature', 'value': 20}],
        [
            {
                'quantity': 'matric_potential',
                'unit': 'kilopascal',
                'value': -10,
                'convention': 'signed',
            }
        ],
    ],
)
def test_resolver_rejects_unproven_or_unsupported_pressure_conditions(conditions: list[object]):
    manifest = cast('dict[str, object]', plain(get_manifest()))
    mutable = json.loads(json.dumps(manifest))
    for function in mutable['functions']:
        if function['id'] == 'calc_ptf_gunarathna2019_vwc10_set1':
            function['outputs'][0]['measurement']['conditions'] = copy.deepcopy(conditions)
    with pytest.raises(PlanValidationError) as error:
        load_evaluation_plan(_evaluation(), manifest=mutable)
    assert any(
        diagnostic.code == 'point.unsupported_conditions' for diagnostic in error.value.diagnostics
    )
