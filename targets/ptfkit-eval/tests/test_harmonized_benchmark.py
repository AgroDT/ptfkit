"""Real native execution distinguishes harmonized eligibility from raw readiness."""

import copy
import runpy
from pathlib import Path
from typing import cast

import pytest
from ptfkit import get_manifest

from ptfkit_eval.documents import plain
from ptfkit_eval.harmonization import EvidenceTier, EvidenceValue


def helpers() -> dict:
    root = Path(__file__).resolve().parents[3]
    with pytest.MonkeyPatch.context() as patch:
        patch.syspath_prepend(str(root))
        return runpy.run_path(str(root / 'evaluation/experiments/meta_v3_3/harmonized.py'))


def fixture() -> tuple[dict, dict, list[dict], dict]:
    manifest = cast('dict', plain(get_manifest()))
    function = next(
        f for f in manifest['functions'] if f['id'] == 'calc_ptf_gunarathna2019_vwc10_set1'
    )
    output = function['outputs'][0]
    coverage = {
        'functions': [
            {
                'id': function['id'],
                'source': 'gunarathna2019',
                'inputs': function['inputs'],
                'outputs': [{'quantity': output['measurement']['quantity']}],
            }
        ]
    }
    support = {
        function['id']: {
            'curves': [],
            'fixed_outputs': [
                {'output': output['name'], 'suction_kpa': 10, 'measurement': output['measurement']}
            ],
        }
    }
    measurement = copy.deepcopy(function['inputs'][0]['measurement'])
    measurement['unit'] = 'mass_fraction'
    dataset = {
        'dataset_id': 'test-measurements',
        'target': {
            'quantity': 'volumetric_water_content',
            'unit': 'volume_fraction',
            'material_basis': 'soil',
            'denominator_basis': 'bulk_volume',
        },
        'samples': [
            {
                'source_id': 'study',
                'sample_id': 'a',
                'profile_id': None,
                'features': [
                    {
                        'id': 'sand',
                        'kind': 'numeric',
                        'value': 0.5,
                        'origin': 'measured',
                        'review_status': 'confirmed',
                        'source_cells': ['P2'],
                        'measurement': measurement,
                    }
                ],
            }
        ],
        'observations': [
            {
                'source_id': 'study',
                'sample_id': 'a',
                'id': f'obs-{p}',
                'suction_kpa': p,
                'value': value,
                'review_status': 'confirmed',
                'origin': 'measured',
                'quality_flags': [],
                'source_cells': [f'WRC:{p}'],
            }
            for p, value in ((1, 0.4), (100, 0.2))
        ],
    }
    return coverage, support, [dataset], manifest


def test_fixed_target_runs_with_converted_sand_and_no_carbon_density_or_profile():
    coverage, support, datasets, manifest = fixture()
    before = copy.deepcopy(datasets)
    matrix, predictions = helpers()['evaluate_catalog'](coverage, support, datasets, manifest)
    assert len(matrix) == len(predictions) == 1
    assert matrix[0]['view'] == 'harmonized'
    assert matrix[0]['execution_status'] == 'executed'
    point = predictions[0]
    assert point['observed'] == pytest.approx(0.3)  # Halfway in log pressure between 1 and 100.
    assert point['predicted'] == pytest.approx(0.2952)  # Published 0.4802 - 0.0037 * 50.
    assert point['target_evidence']['tier'] == 'reconstructed'
    assert point['predictor_evidence']['sand']['tier'] == 'converted'
    assert datasets == before


def test_predictor_contract_matching_does_not_require_identical_feature_names():
    coverage, support, datasets, manifest = fixture()
    datasets[0]['samples'][0]['features'][0]['id'] = 'reported_sand_fraction'
    matrix, points = helpers()['evaluate_catalog'](coverage, support, datasets, manifest)
    assert matrix[0]['view'] == 'harmonized'
    assert len(points) == 1
    assert points[0]['predicted'] == pytest.approx(0.2952)


@pytest.mark.parametrize('defect', ['missing', 'wrong_psd', 'unknown_basis', 'outside_range'])
def test_unsupported_combinations_never_reach_native_execution(
    defect: str, monkeypatch: pytest.MonkeyPatch
):
    coverage, support, datasets, manifest = fixture()
    dataset = datasets[0]
    feature = dataset['samples'][0]['features'][0]
    if defect == 'missing':
        dataset['samples'][0]['features'] = []
    elif defect == 'wrong_psd':
        feature['measurement']['particle_size']['lower']['value'] = 100
    elif defect == 'unknown_basis':
        feature['measurement']['basis']['material'] = 'unspecified'
    else:
        dataset['observations'] = dataset['observations'][:1]
    namespace = helpers()

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail('Unsupported scientific combination was executed')

    monkeypatch.setitem(namespace['evaluate_catalog'].__globals__, 'evaluate_candidate', forbidden)
    matrix, predictions = namespace['evaluate_catalog'](coverage, support, datasets, manifest)
    assert matrix[0]['view'] == 'unsupported'
    assert matrix[0]['reasons']
    assert predictions == []


def test_reporting_rejects_changed_strict_values():
    coverage, support, datasets, manifest = fixture()
    namespace = helpers()
    matrix, points = namespace['evaluate_catalog'](coverage, support, datasets, manifest)
    strict = [{**points[0], 'observed': 0.31}]
    with pytest.raises(ValueError, match='changed or lost'):
        namespace['reporting'](coverage, support, matrix, points, strict)


def test_approximate_predictor_is_classified_separately_and_not_scored():
    coverage, support, datasets, manifest = fixture()
    feature = datasets[0]['samples'][0]['features'][0]
    feature['origin'] = 'derived'
    feature['harmonization'] = EvidenceValue(
        0.5, EvidenceTier.APPROXIMATE, 'exploratory_example', ('P2',)
    )
    namespace = helpers()
    matrix, points = namespace['evaluate_catalog'](coverage, support, datasets, manifest)
    assert matrix[0]['view'] == 'exploratory'
    assert matrix[0]['predictors']['sand']['tier'] == 'approximate'
    assert points == []


def test_main_ensembles_reject_approximate_member_evidence():
    coverage, support, datasets, manifest = fixture()
    namespace = helpers()
    _, points = namespace['evaluate_catalog'](coverage, support, datasets, manifest)
    assert len(points) == 1
    points[0]['predictor_evidence']['sand']['tier'] = 'approximate'
    with pytest.raises(ValueError, match='without approximate'):
        namespace['ensemble_pools'](points)
