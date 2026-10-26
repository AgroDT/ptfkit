"""Protect catalog adapters, explicit approximation boundaries and common cohorts."""

import copy
import importlib
import json
from pathlib import Path
from types import ModuleType

import pytest
from openpyxl import Workbook

from ptfkit_eval.harmonization import EvidenceTier, EvidenceValue


@pytest.fixture
def campaign(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    root = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root))
    return importlib.import_module('evaluation.experiments.meta_v3_3.campaign')


@pytest.fixture
def catalog(campaign: ModuleType) -> dict:
    root = Path(__file__).resolve().parents[3]
    return {f['id']: f for f in campaign.contracts.load_catalog(root)}


def registration():
    root = Path(__file__).resolve().parents[3]
    return json.loads(
        (root / 'evaluation/experiments/meta_v3_3/exploratory-policies.json').read_bytes()
    )


@pytest.mark.parametrize(
    'description',
    [
        'water at 10-33 kPa',
        'water at 10 to 33 kPa',
        'water at 33 and 1500 kPa',
        'water at 33, 1500 kPa',
        'field capacity',
    ],
)
def test_ambiguous_coordinates_are_not_invented(campaign: ModuleType, description: str):
    assert campaign.contracts.explicit_pressure(description) is None


def test_pressure_sign_and_thousands_separator(campaign: ModuleType):
    assert campaign.contracts.explicit_pressure('Water content at \u22121,500 kPa') == 1500


def test_unknown_physics_overrides_output_quantity_label(campaign: ModuleType, catalog: dict):
    functions = [
        f
        for name, f in catalog.items()
        if name.startswith('calc_ptf_dharumarajan') and 'infiltration' not in name
    ]
    assert len(functions) == 4
    for function in functions:
        assert campaign.contracts.unknown_water_basis(function)
        assert campaign.contracts.targets(function, {}) == []
    for name, function in catalog.items():
        if name.startswith('calc_ptf_pidgeon'):
            assert campaign.contracts.targets(function, {}) == []


def test_native_public_alias_and_percent_units(campaign: ModuleType, catalog: dict):
    # Rawls 1982 theta_1500: (2.6 + .5*5.12 + 1.58*.1) / 100.
    function = catalog['calc_ptf_rawls1982_theta_1500']
    target = campaign.contracts.targets(function, {})[0]
    value = campaign.contracts.predicted(
        function, target, {'clay': 5.12, 'organic_matter': 0.1}, campaign.get_manifest()
    )
    assert value == pytest.approx(0.05318)


def test_copied_retention_anchors_are_not_scored_as_predictions(
    campaign: ModuleType, catalog: dict
):
    targets = campaign.contracts.targets(catalog['calc_ptf_rawls1982_full_wrc'], {})
    pressures = {target['pressure_kpa'] for target in targets}
    assert 10 in pressures
    assert 33 not in pressures
    assert 1500 not in pressures


def test_each_catalog_function_gets_a_decision_without_measurement_bridge(
    campaign: ModuleType, catalog: dict, monkeypatch: pytest.MonkeyPatch
):
    dataset, _ = measured_dataset()

    def forbidden(*_: object) -> None:
        pytest.fail('Disabled measurement bridge must not call the native function.')

    monkeypatch.setattr(campaign.contracts, 'predicted', forbidden)
    context = {
        'catalog': list(catalog.values()),
        'support': {},
        'public_ids': set(),
        'datasets': [dataset],
        'rows': {},
        'fits': {},
        'old_registration': registration(),
    }
    stage = {
        'id': 'no_bridge',
        'legacy': False,
        'representative': False,
        'water_predictors': False,
        'density_link': False,
    }
    records, points = campaign.evaluate(
        context, stage, 'log_psd', 'log_pressure_linear_interpolation_v1'
    )
    assert not points
    assert {row['function'] for row in records} == set(catalog)
    assert catalog
    assert all(row['reasons'] for row in records)


def sample_class(label: str = 'sand') -> dict:
    return {
        'features': [
            {
                'kind': 'categorical',
                'review_status': 'confirmed',
                'origin': 'measured',
                'category_system': 'test.UsdaTextureClass',
                'source_cells': ['paper:class'],
                'value': label,
            }
        ]
    }


def test_class_imputation_preserves_known_fractions_and_provenance(campaign: ModuleType):
    # Sand 90 + clay 2 leaves exactly silt 8 on the closed 1% grid.
    sand = EvidenceValue(90, EvidenceTier.STRICT, 'measured', ('sand:1',))
    clay = EvidenceValue(2, EvidenceTier.STRICT, 'measured', ('clay:1',))
    result = campaign.inputs.class_psd(sample_class(), {'sand': sand, 'clay': clay})
    assert result['sand'] is sand
    assert result['clay'] is clay
    assert result['silt'].value == 8
    assert result['silt'].tier == EvidenceTier.APPROXIMATE
    assert dict(result['silt'].details)['lattice_point_count'] == 1
    assert result['silt'].parents[1:] == (sand, clay)
    incompatible = sample_class('clay')
    assert campaign.inputs.class_psd(incompatible, {'sand': sand, 'clay': clay}) == {
        'sand': sand,
        'clay': clay,
    }
    unreviewed = sample_class()
    unreviewed['features'][0]['category_system'] = 'RussianTexture'
    assert campaign.inputs.class_psd(unreviewed, {}) == {}


def test_source_particle_intervals_normalize_units_and_descending_bounds(campaign: ModuleType):
    assert campaign.inputs.interval({'name': 'fine', 'description': 'smaller than 0.002 mm'}) == (
        0,
        2,
    )
    assert campaign.inputs.interval({'name': 'fine_sand', 'description': '0.25-0.05 mm'}) == (
        50,
        250,
    )


@pytest.mark.parametrize(
    ('adapter', 'fields', 'output', 'pressure', 'expected'),
    [
        (
            'logistic_pressure_scale_v1',
            [
                {'name': 'theta', 'quantity': 'volumetric_water_content', 'unit': 'volume_percent'},
                {'name': 'm', 'quantity': 'varallyai_m'},
                {'name': 'pf', 'quantity': 'varallyai_pf_star'},
            ],
            {'theta': 50, 'm': 1, 'pf': 2},
            9.80665,
            0.25,
        ),
        (
            'hutson_cass_dry_v1',
            [
                {
                    'name': 'theta',
                    'quantity': 'volumetric_water_content',
                    'unit': 'volume_fraction',
                },
                {'name': 'a', 'quantity': 'matric_potential'},
                {'name': 'b', 'quantity': 'hutson_cass_b'},
            ],
            {'theta': 0.5, 'a': 100, 'b': 2},
            39.2266,
            0.25,
        ),
    ],
)
def test_generic_curve_adapters_have_independent_hand_oracles(
    campaign: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    *,
    adapter: str,
    fields: list[dict],
    output: dict,
    pressure: float,
    expected: float,
):
    # Logistic: head=100, pF*=2, m=1. HC: head/a=4, b=2.
    monkeypatch.setattr(campaign.contracts, 'native_outputs', lambda *_: output)
    target = {'adapter': adapter, 'pressure_kpa': pressure}
    function = {'fields': fields}
    assert campaign.contracts.predicted(
        function, target, {}, campaign.get_manifest()
    ) == pytest.approx(expected)
    if adapter == 'hutson_cass_dry_v1':
        with pytest.raises(ValueError, match='wet-branch'):
            campaign.contracts.predicted(
                function, {**target, 'pressure_kpa': 9.80665}, {}, campaign.get_manifest()
            )


def measured_dataset():
    sample = {'source_id': 'source', 'sample_id': 'a', 'features': []}
    target = {
        'quantity': 'volumetric_water_content',
        'unit': 'volume_fraction',
        'denominator_basis': 'bulk_volume',
        'material_basis': 'unspecified',
    }
    observations = [
        {
            **sample,
            'id': name,
            'suction_kpa': p,
            'value': v,
            'source_cells': [name],
            'origin': 'measured',
            'review_status': 'confirmed',
            'quality_flags': [],
        }
        for name, p, v in [('lo', 1, 0.5), ('hi', 100, 0.104)]
    ]
    return {'target': target, 'samples': [sample], 'observations': observations}, sample


def test_interpolation_and_fit_are_distinct_and_never_extrapolate(campaign: ModuleType):
    dataset, sample = measured_dataset()
    route = 'log_pressure_linear_interpolation_v1'
    observed, reason = campaign.targets.reconstruct(dataset, sample, 10, route, {})
    assert reason is None
    assert observed.value == pytest.approx(0.302)  # Halfway in log pressure.
    assert observed.tier == EvidenceTier.RECONSTRUCTED
    assert [dict(v.details)['suction_kpa'] for v in observed.parents] == [1, 100]
    fit_route = 'brooks_corey_v1'
    fit = {
        'family': fit_route,
        'parameters': {
            'theta_r': 0.1,
            'theta_s': 0.5,
            'air_entry': 1,
            'lambda': 1,
        },
        'pressure_range_kpa': [1, 100],
        'status': 'fitted',
        'fit_sha256': 'fit',
    }
    fits = {('source', 'a', fit_route): fit}
    fitted, reason = campaign.targets.reconstruct(dataset, sample, 10, fit_route, fits)
    assert reason is None
    assert fitted.value == pytest.approx(0.14)  # .1 + (.5-.1)/10.
    assert dict(fitted.details)['fit_minus_interpolation'] == pytest.approx(-0.162)
    exact, _ = campaign.targets.reconstruct(dataset, sample, 1, fit_route, fits)
    assert exact.tier == EvidenceTier.RECONSTRUCTED
    for selected in (route, fit_route):
        value, reason = campaign.targets.reconstruct(dataset, sample, 101, selected, fits)
        assert value is None
        assert reason == 'target_pressure_outside_measured_range'
    value, reason = campaign.targets.reconstruct(dataset, sample, 10, route, {}, interpolate=False)
    assert value is None
    assert reason == 'target_requires_interpolation'


def test_accepted_fits_require_matching_experimental_values_and_references(campaign: ModuleType):
    dataset, sample = measured_dataset()
    fit = {
        'plan': {'family_id': 'brooks_corey_v1'},
        'status': 'fitted',
        'parameters': [],
        'observations': [
            {'suction_kpa': 1, 'water_content': 0.5, 'reference': 'lo'},
            {'suction_kpa': 100, 'water_content': 0.104, 'reference': 'hi'},
        ],
    }
    artifact: dict = {'results': [{**sample, 'fit': fit}]}
    assert len(campaign.targets.accepted_fit_index(artifact, [dataset])) == 1
    for field, value in [('water_content', 0.2), ('reference', 'another_sample')]:
        changed = copy.deepcopy(artifact)
        changed['results'][0]['fit']['observations'][0][field] = value
        assert campaign.targets.accepted_fit_index(changed, [dataset]) == {}
    fit['status'] = 'rejected'
    assert campaign.targets.accepted_fit_index(artifact, [dataset]) == {}


def test_density_requires_exact_identity_and_rejects_formula_averages(
    campaign: ModuleType, tmp_path: Path
):
    book = Workbook()
    sheet = book.active
    sheet.append(['source', 'sample_id', 'density'])
    sheet.append(['source', 'a', 1.4])
    sheet.append(['another_source', 'b', 1.7])
    sheet.append(['source', 'c', '=(1.4+1.6)/2'])
    path = tmp_path / 'density.xlsx'
    book.save(path)
    rows: dict = {('source', name): {'values': {}, 'formulas': {}} for name in ('a', 'b', 'c')}
    mapping = {
        'worksheets': [
            {
                'id': 'samples_master',
                'columns': [
                    {'role': 'source', 'source_header': 'source'},
                    {'role': 'dry_bulk_density', 'source_header': 'density'},
                ],
            }
        ]
    }
    result = campaign.targets.discover_density(path, rows, mapping)
    assert result['linked_samples'] == 1
    assert rows['source', 'a']['linked_density'].value == 1.4
    assert rows['source', 'a']['linked_density'].sources == ('Sheet!C2',)
    assert 'linked_density' not in rows['source', 'b']
    assert 'linked_density' not in rows['source', 'c']
    averaged = {'values': {'Q': 1.5}, 'formulas': {'Q': '=(1.4+1.6)/2'}}
    assert campaign.inputs.density(averaged, registration()) is None


def point(
    fid: str, scenario: str, predicted: float, sample: str = 'a', observed: float = 0
) -> dict:
    return {
        'function': fid,
        'scenario': scenario,
        'predicted': predicted,
        'observed': observed,
        'source_id': 'source',
        'sample_id': sample,
        'pressure_kpa': 33,
        'route': 'interpolation',
        'target_pool': 'volume:33',
        'profile_id': None,
        'quantity': 'volumetric_water_content',
        'minimum_tier': 'E4',
        'target_evidence': {'tier': 'reconstructed'},
    }


def test_common_cohort_rejects_observation_mismatch_and_duplicates(campaign: ModuleType):
    comparisons = campaign.comparisons
    a = point('a', 'left', 0.1)
    b = point('b', 'left', 0.2, observed=0.3)
    with pytest.raises(ValueError, match='identical observed'):
        comparisons.comparative_tables([a, b], campaign.metrics)
    with pytest.raises(ValueError, match='Duplicate'):
        comparisons.index([a, a])


def test_scenario_rank_reversal_uses_exact_shared_cohort(campaign: ModuleType):
    points = [
        point('a', 'left', 0.1),
        point('a', 'right', 0.3),
        point('b', 'left', 0.2),
        point('b', 'right', 0.15),
        point('a', 'left', 100, sample='unmatched'),
    ]
    result = campaign.comparisons.scenario_sensitivity(points, ['left', 'right'], campaign.metrics)
    ranking = result['rankings'][0]
    assert ranking['common_points'] == 1
    assert ranking['rankings'] == {'left': ['a', 'b'], 'right': ['b', 'a']}
    assert ranking['changed_pair_orderings'] == [['a', 'b']]
    assert ranking['unstable'] is True
    assert ranking['recommendation'] is None


def test_equal_mean_uses_common_samples_and_missing_profiles_block_learning(
    campaign: ModuleType, monkeypatch: pytest.MonkeyPatch
):
    def forbidden(*_: object) -> None:
        pytest.fail('Missing profile groups must prevent learned weights.')

    monkeypatch.setattr(campaign.comparisons, 'grouped_compare', forbidden)
    points = [
        point('a', 'left', 0.1, observed=0.2),
        point('b', 'left', 0.3, observed=0.2),
        point('a', 'left', 100, sample='unmatched'),
    ]
    report = campaign.comparisons.ensembles(points, campaign.metrics)[0]
    assert report['common_points'] == 1
    assert report['equal_means'][0]['metrics']['rmse'] == pytest.approx(0, abs=1e-15)
    assert report['learned']['status'] == 'insufficient_independent_profile_groups'
    assert report['training_observation_tiers'] == ['reconstructed']
    assert report['recommendation_eligible'] is False


def test_single_candidate_cannot_establish_ranking_stability(campaign: ModuleType):
    points = [point('a', 'left', 0.1), point('a', 'right', 0.1)]
    report = campaign.comparisons.scenario_sensitivity(points, ['left', 'right'], campaign.metrics)
    assert report['rankings'][0]['status'] == 'insufficient_candidates'


def test_blocker_funnel_selects_nearest_sample_without_collapsing_missing_inputs(
    campaign: ModuleType,
):
    records = [
        {
            'function': 'a',
            'reasons': ['missing_predictor:sand', 'missing_predictor:silt'],
            'source_id': 'source',
            'sample_id': 'a',
            'target_pool': '33',
        },
        {
            'function': 'a',
            'reasons': ['computational_domain:silt'],
            'source_id': 'source',
            'sample_id': 'b',
            'target_pool': '33',
        },
        {'function': 'b', 'reasons': ['operational_target_absent']},
    ]
    funnel = campaign.reporting.blocker_funnel(
        [{'id': 'a'}, {'id': 'b'}, {'id': 'c'}], records, {'c'}
    )
    decisions = {f['function']: f for f in funnel['functions']}
    assert decisions['a']['next_blocker'] == 'unacceptable_domain_or_unregistered_derivation'
    assert decisions['b']['next_blocker'] == 'target_absent'
    assert decisions['c']['status'] == 'executable'
    assert sum(g['functions_blocked'] for g in funnel['funnel']) == 2


def test_missing_foreign_taxonomy_is_not_a_usda_policy_opportunity(campaign: ModuleType):
    records = [
        {
            'function': 'foreign_class',
            'reasons': ['missing_predictor:soil_class'],
            'source_id': 'source',
            'sample_id': 'a',
            'target_pool': '33',
            'reported_usda_class_available': True,
            'usda_class_policy_supported': False,
        }
    ]
    funnel = campaign.reporting.blocker_funnel([{'id': 'foreign_class'}], records, set())
    group = funnel['funnel'][0]
    assert group['one_policy_opportunity_functions'] == 0
    assert group['can_be_approximated_reproducibly'] == 'no_current_defensible_route'
