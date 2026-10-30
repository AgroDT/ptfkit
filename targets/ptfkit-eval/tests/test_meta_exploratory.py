"""Protect explicit approximate scenarios without granting main eligibility."""

import copy
import importlib
import json
from pathlib import Path
from types import ModuleType

import pytest
from openpyxl import Workbook
from test_harmonized_benchmark import fixture

from ptfkit_eval.harmonization import EvidenceTier, EvidenceValue


def modules() -> tuple[ModuleType, ModuleType]:
    root = Path(__file__).resolve().parents[3]
    with pytest.MonkeyPatch.context() as patch:
        patch.syspath_prepend(str(root))
        return (
            importlib.import_module('evaluation.experiments.meta_v3_3.exploratory'),
            importlib.import_module('evaluation.experiments.meta_v3_3.exploratory_inputs'),
        )


def registration() -> dict:
    root = Path(__file__).resolve().parents[3]
    return json.loads(
        (root / 'evaluation/experiments/meta_v3_3/exploratory-policies.json').read_bytes()
    )


def raw() -> dict:
    return {
        'worksheet': 'samples',
        'row': 2,
        'clay_upper_um': 1,
        'values': {'M': 30, 'N': 10, 'O': 40, 'P': 50, 'Q': 1.5, 'R': 2},
    }


def test_psd_scenarios_distinguish_proxy_from_adjacent_log_interpolation():
    _, inputs = modules()
    before = raw()
    proxy = inputs.texture_predictors(before, 'reported_boundary_proxy', registration())
    interpolated = inputs.texture_predictors(before, 'log_psd', registration())
    assert proxy['clay'].value == 10
    # CDF(1)=10, CDF(10)=30; log10(2)=0.3010299956639812.
    assert interpolated['clay'].value == pytest.approx(16.020599913279625)
    assert interpolated['silt'].value == pytest.approx(33.979400086720375)
    assert interpolated['sand'].value == 50
    assert dict(interpolated['clay'].details)['neighboring_diameters_um'] == (1, 10)
    assert all(value.tier == EvidenceTier.APPROXIMATE for value in interpolated.values())
    assert before == raw()


def test_texture_closure_is_explicit_and_missing_tail_is_not_extrapolated():
    _, inputs = modules()
    row = raw()
    row['values'].pop('O')
    result = inputs.texture_predictors(row, 'reported_boundary_proxy', registration())
    assert result['silt'].value == 40
    assert result['silt'].parents[0].policy == 'meta_texture_closure_v1'
    row['values'] = {'N': 10}
    assert inputs.texture_predictors(row, 'log_psd', registration()) == {}
    assert (
        inputs.texture_predictors(row, 'reported_boundary_proxy', registration())['clay'].value
        == 10
    )


def test_target_conversion_retains_experimental_parent_and_assumed_density():
    _, inputs = modules()
    observed = EvidenceValue(
        0.3, EvidenceTier.RECONSTRUCTED, 'wrc_log10_adjacent_v1', ('WRC:1', 'WRC:100')
    )
    original = {
        'quantity': 'volumetric_water_content',
        'unit': 'volume_fraction',
        'denominator_basis': 'bulk_volume',
        'material_basis': 'unspecified',
    }
    required = {
        'quantity': 'gravimetric_water_content',
        'unit': 'mass_fraction',
        'denominator_basis': 'dry_soil_mass',
        'material_basis': 'fine_earth',
    }
    result = inputs.approximate_target(observed, original, required, raw(), registration())
    assert result is not None
    assert result.value == pytest.approx(0.2)
    assert result.tier == EvidenceTier.APPROXIMATE
    assert result.parents[0].parents[0] is observed
    assert dict(result.parents[0].details)['water_density_g_cm3'] == 1.0
    assert 'samples!Q2' in result.sources
    row = raw()
    row['values'].pop('Q')
    assert inputs.approximate_target(observed, original, required, row, registration()) is None


def test_organic_derivation_uses_registered_factor_without_replacing_reported_values():
    _, inputs = modules()
    matter = inputs.organic(raw(), 'organic_matter', registration())
    assert matter is not None
    assert matter.value == pytest.approx(3.448)
    assert matter.tier == EvidenceTier.APPROXIMATE
    row = raw()
    row['values']['S'] = 5
    reported = inputs.organic(row, 'organic_matter', registration())
    assert reported is not None
    assert reported.value == 5
    assert dict(reported.details)['factor'] == 1


def test_exploratory_native_execution_is_isolated_from_main_eligibility():
    experiment, _ = modules()
    coverage, support, datasets, manifest = fixture()
    dataset = datasets[0]
    dataset['samples'][0]['features'] = []
    dataset['target']['material_basis'] = 'unspecified'
    before = copy.deepcopy(datasets)
    matrix, points = experiment.evaluate_scenario(
        coverage,
        support,
        datasets,
        {('study', 'a'): raw()},
        manifest,
        scenario='log_psd',
        registration=registration(),
    )
    assert matrix[0]['view'] == 'exploratory'
    assert len(points) == 1
    assert points[0]['predicted'] == pytest.approx(0.2952)  # 0.4802 - 0.0037 * 50.
    assert points[0]['observed'] == pytest.approx(0.3)
    assert points[0]['recommendation_eligible'] is False
    assert points[0]['target_evidence']['tier'] == 'approximate'
    assert points[0]['predictor_evidence']['sand']['tier'] == 'approximate'
    main_matrix, main_points = experiment.main_benchmark.evaluate_catalog(
        coverage, support, datasets, manifest
    )
    assert main_matrix[0]['view'] == 'unsupported'
    assert main_points == []
    assert datasets == before


def test_missing_target_density_never_reaches_native_execution(monkeypatch: pytest.MonkeyPatch):
    experiment, _ = modules()
    coverage, support, datasets, manifest = fixture()
    datasets[0]['target'].update(
        quantity='gravimetric_water_content',
        unit='mass_fraction',
        denominator_basis='dry_soil_mass',
    )
    row = raw()
    row['values'].pop('Q')

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail('Missing sample density reached native execution')

    monkeypatch.setattr(experiment, 'evaluate_candidate', forbidden)
    matrix, points = experiment.evaluate_scenario(
        coverage,
        support,
        datasets,
        {('study', 'a'): row},
        manifest,
        scenario='log_psd',
        registration=registration(),
    )
    assert matrix[0]['view'] == 'unsupported'
    assert matrix[0]['reasons'] == ['missing_sample_density_for_target_conversion']
    assert points == []


def test_main_eligible_combinations_are_references_and_not_reexecuted(
    monkeypatch: pytest.MonkeyPatch,
):
    experiment, _ = modules()
    coverage, support, datasets, manifest = fixture()
    _, reference = experiment.main_benchmark.evaluate_catalog(coverage, support, datasets, manifest)
    assert len(reference) == 1

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail('Main-eligible combination was included in exploratory scoring')

    monkeypatch.setattr(experiment, 'evaluate_candidate', forbidden)
    matrix, points = experiment.evaluate_scenario(
        coverage,
        support,
        datasets,
        {('study', 'a'): raw()},
        manifest,
        scenario='log_psd',
        registration=registration(),
    )
    assert matrix[0]['view'] == 'main_reference'
    assert points == []


def test_paired_sensitivity_uses_common_coordinates_instead_of_changed_coverage():
    experiment, _ = modules()
    base = {
        'function': 'f',
        'target_pool': 'p',
        'source_id': 's',
        'sample_id': 'a',
        'profile_id': None,
        'suction_kpa': 10,
        'observed': 0,
        'water_quantity': 'volumetric_water_content',
    }
    points = [
        {**base, 'scenario': 'reported_boundary_proxy', 'predicted': 0.1},
        {**base, 'scenario': 'log_psd', 'predicted': 0.2},
        {**base, 'scenario': 'reported_boundary_proxy', 'sample_id': 'unmatched', 'predicted': 100},
    ]
    result = experiment.paired_sensitivity(points, registration())
    assert len(result) == 1
    assert result[0]['common_points'] == 1
    assert result[0]['difference_right_minus_left']['root_mean_squared_error'] == pytest.approx(0.1)
    assert result[0]['recommendation'] is None


def test_raw_join_rejects_changed_identity_and_honors_source_local_boundary(tmp_path: Path):
    experiment, _ = modules()
    book = Workbook()
    sheet = book.active
    sheet.title = 'samples'
    sheet.append(['sample_id', 'number', 'source'])
    sheet.append(['a', 1, 'study'])
    path = tmp_path / 'predictors.xlsx'
    book.save(path)
    book.close()
    audit = {'eligibility': [{'source': 'study', 'sample_id': 'a', 'sample_key': 'samples!2'}]}
    mapping = {
        'worksheets': [{'id': 'samples_master', 'name': 'samples'}],
        'predictor_bindings': [
            {
                'input': 'clay',
                'column': 'N',
                'measurement_overrides': [
                    {
                        'sample_rows': [{'first': 2, 'last': 2}],
                        'measurement': {'particle_size': {'upper': 2}},
                    }
                ],
            }
        ],
    }
    rows = experiment.raw_rows(path, audit, mapping)
    assert rows['study', 'a']['clay_upper_um'] == 2
    audit['eligibility'][0]['sample_id'] = 'different'
    with pytest.raises(ValueError, match='identity differs'):
        experiment.raw_rows(path, audit, mapping)


def test_density_conversion_does_not_clip_impossible_volumetric_targets():
    _, inputs = modules()
    observed = EvidenceValue(2, EvidenceTier.STRICT, 'measured', ('WRC:10',))
    original = {'quantity': 'gravimetric_water_content', 'material_basis': 'soil'}
    required = {'quantity': 'volumetric_water_content', 'material_basis': 'soil'}
    with pytest.raises(ValueError, match='bounds'):
        inputs.approximate_target(observed, original, required, raw(), registration())
