import json
import math
from pathlib import Path

import pytest
from _run_fixtures import dataset_document, write_run_fixture

from ptfkit_eval import (
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)


def _fit_configuration() -> dict[str, object]:
    return {
        'family_id': 'van_genuchten_mualem_v1',
        'parameters': [
            {'name': 'theta_r', 'lower': 0, 'upper': 0.2, 'initial': 0.05},
            {'name': 'theta_s', 'lower': 0.3, 'upper': 0.8, 'initial': 0.45},
            {'name': 'alpha', 'lower': 0.01, 'upper': 1, 'initial': 0.08},
            {'name': 'n', 'lower': 1.1, 'upper': 4, 'initial': 1.8},
        ],
        'seed': 17,
        'minimum_log10_span': 2,
        'n_starts': 2,
        'max_evaluations': 2000,
        'optimizer_tolerance': 1e-10,
        'boundary_tolerance': 1e-6,
        'rank_tolerance': 1e-10,
        'maximum_condition_number': 1e10,
        'objective_agreement_tolerance': 1e-10,
        'parameter_agreement_tolerance': 1e-3,
        'confidence_level': 0.95,
        'method': 'bounded_trf_uniform_multistart_v1',
        'uncertainty_method': 'local_linear_iid_student_t_v1',
    }


def test_reference_fitting_is_independent_of_ptf_input_eligibility_and_replays(tmp_path: Path):
    dataset = json.loads(json.dumps(dataset_document()))
    dataset['samples'][0]['features'][0]['review_status'] = 'blocked'
    dataset['observations'] = [
        {
            'id': f'{source}_{h}',
            'source_id': source,
            'sample_id': 'one',
            'suction_kpa': h,
            'value': 0.1 + 0.4 / math.sqrt(1 + (h / 10) ** 2),
            'origin': 'synthetic',
            'review_status': 'confirmed',
            'quality_flags': [],
            'source_cells': ['synthetic!A1'],
        }
        for source in ('a', 'b')
        for h in (0, 0.1, 1, 10, 100, 1000)
    ]
    dataset['observations'].append(
        {
            **dataset['observations'][0],
            'id': 'flagged',
            'suction_kpa': 17,
            'value': 0.9,
            'quality_flags': ['unreviewed_artifact'],
        }
    )
    path = write_run_fixture(tmp_path / 'inputs', dataset=dataset)
    run = json.loads(path.read_text('utf-8'))
    run['approximations'] = [_fit_configuration()]
    path.write_text(json.dumps(run), encoding='utf-8')
    result = execute_retention_run(load_retention_run_plan(path))
    fits = {item.source_id: item for item in result.approximations}

    assert not any(point.eligible for point in result.points if point.source_id == 'a')
    assert fits['a'].fit.status == 'fitted'
    assert fits['a'].excluded_observation_ids == ('flagged',)
    assert {
        parameter.name: parameter.value for parameter in fits['a'].fit.parameters
    } == pytest.approx({'theta_r': 0.1, 'theta_s': 0.5, 'alpha': 0.1, 'n': 2}, abs=1e-5)
    assert fits['without_target'].fit.reason == 'insufficient_observations'
    destination = write_retention_run(result, tmp_path / 'output')
    assert (destination / 'approximations.json').is_file()
    assert 'Reference approximation fits' in read_retention_run_report(destination)
    replay = execute_retention_run(load_retention_run_plan(destination / 'run-plan.json'))
    assert replay.approximations == result.approximations
