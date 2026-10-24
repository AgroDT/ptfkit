import copy
import json
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
import yaml
from jsonschema import Draft202012Validator

from ptfkit_eval import DatasetMappingValidationError, load_dataset_mapping


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
MAPPING_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.yaml'
INVENTORY_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.inventory.json'
PROFILE_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.retention-profile.json'
SUMMARY_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.normalization-summary.json'
RECONSTRUCTION_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.reconstruction-audit.json'
PREDICTOR_PATH = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.predictor-audit.json'


def _mapping_document() -> dict[str, object]:
    loaded = yaml.safe_load(MAPPING_PATH.read_text(encoding='utf-8'))
    assert isinstance(loaded, dict)
    return loaded


def _inventory_document() -> dict[str, object]:
    loaded = json.loads(INVENTORY_PATH.read_text(encoding='utf-8'))
    assert isinstance(loaded, dict)
    return loaded


def _profile_document() -> dict[str, object]:
    loaded = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))
    assert isinstance(loaded, dict)
    return loaded


def test_dataset_mapping_schema_is_valid():
    resource = files('ptfkit_eval').joinpath('schemas/dataset-mapping.schema.json')
    schema = json.loads(resource.read_text(encoding='utf-8'))

    Draft202012Validator.check_schema(schema)


def test_meta_mapping_is_inventory_bound_and_keeps_ambiguities_explicit():
    mapping = load_dataset_mapping(MAPPING_PATH)

    assert mapping.dataset_id == 'meta_v3_3'
    assert mapping.status == 'draft_blocked'
    assert mapping.source_sha256 == (
        '1322bf65b1ca0130085015209858a443d1ee82a7e2ae69232321cd8ede361e68'
    )

    encoding_values = cast('Sequence[Mapping[str, object]]', mapping.document['encodings'])
    encodings = {str(encoding['id']): encoding for encoding in encoding_values}
    assert encodings['water_w']['status'] == 'blocked'
    water_measurement = cast('Mapping[str, object]', encodings['water_w']['measurement'])
    assert water_measurement['unit'] is None
    assert encodings['pressure_mpa_label']['status'] == 'blocked'
    assert encodings['fitted_vgn']['status'] == 'confirmed'
    assert mapping.document['reviewed_corrections'] == ()

    source_rule_values = cast(
        'Sequence[Mapping[str, object]]', mapping.document['retention_source_rules']
    )
    assert len(source_rule_values) == 27
    observation_rules = [
        cast('Mapping[str, object]', rule)
        for source_rule in source_rule_values
        for rule in cast('Sequence[object]', source_rule['observations'])
    ]
    assert len(observation_rules) == 26
    assert [rule['status'] for rule in observation_rules].count('confirmed') == 11
    assert [rule['status'] for rule in observation_rules].count('blocked') == 15
    assert {rule['water_unit'] for rule in observation_rules} == {
        None,
        'mass_percent',
        'mass_fraction',
        'volume_fraction',
        'volume_percent',
    }

    identity = cast('Mapping[str, object]', mapping.document['identity'])
    crosswalks = cast('Sequence[Mapping[str, object]]', identity['sample_crosswalks'])
    assert len(crosswalks) == 62
    chestnova_two = next(item for item in crosswalks if item['raw_sample_id'] == '2017_Честнова_2')
    assert chestnova_two['canonical_sample_id'] == '2017_честнова_9'
    assert chestnova_two['canonical_sample_number'] == 9
    assert chestnova_two['evidence_cells'] == ('Данные!X227:AJ227', 'Данные!X236:AJ236')

    reconstruction_rules = cast(
        'Sequence[Mapping[str, object]]',
        mapping.document['retention_reconstruction_rules'],
    )
    assert [rule['id'] for rule in reconstruction_rules] == [
        'sapozhnikov_1987',
        'sapozhnikov_1988',
        'gumatov_1991',
        'gumatov_1992',
        'khaydapova_2001',
        'kokareva_2007',
        'pestonova_2007',
        'umarova_2008',
        'shvarov_2008',
        'smagin_2009',
        'chudinova_2009',
        'shein_2011',
        'sadovnikova_2011',
        'vasyukov_2012',
        'manucharova_2012',
        'shein_2012',
        'badenko_2013',
        'bolotov_2014',
        'makarychev_2014_1',
        'makarychev_2014_2',
        'makarychev_2014_3',
        'panina_2015',
        'sidorova_2016',
        'chestnova_2017',
        'makarychev_2018',
        'moiseev_2018',
        'shein_2018',
    ]
    chestnova = next(rule for rule in reconstruction_rules if rule['id'] == 'chestnova_2017')
    panina = next(rule for rule in reconstruction_rules if rule['id'] == 'panina_2015')
    assert chestnova['status'] == 'confirmed'
    assert chestnova['parameter_block'] is None
    assert panina['status'] == 'blocked'
    assert panina['water_scale_status'] == 'confirmed'

    predictor_bindings = cast(
        'Sequence[Mapping[str, object]]', mapping.document['predictor_bindings']
    )
    assert [
        (binding['function'], binding['input'], binding['column'], binding['blockers'])
        for binding in predictor_bindings
    ] == [
        ('calc_ptf_clapp1978', 'soil_texture', 'L', ('texture_classification',)),
        (
            'calc_ptf_gunarathna2019_vwc10_set1',
            'sand',
            'P',
            ('particle_size_schemes',),
        ),
        (
            'calc_ptf_gunarathna2019_vwc33_set1',
            'sand',
            'P',
            ('particle_size_schemes',),
        ),
        (
            'calc_ptf_gunarathna2019_vwc1500_set1',
            'sand',
            'P',
            ('particle_size_schemes',),
        ),
        ('calc_ptf_vereecken1989', 'sand', 'P', ('particle_size_schemes',)),
        ('calc_ptf_vereecken1989', 'clay', 'N', ('particle_size_schemes',)),
        ('calc_ptf_vereecken1989', 'carbon', 'R', ('organic_property_provenance',)),
        ('calc_ptf_vereecken1989', 'bulk_density', 'Q', ('density_units',)),
    ]
    clay_binding = next(
        binding
        for binding in predictor_bindings
        if binding['function'] == 'calc_ptf_vereecken1989' and binding['input'] == 'clay'
    )
    overrides = cast('Sequence[Mapping[str, object]]', clay_binding['measurement_overrides'])
    assert len(overrides) == 1
    assert overrides[0]['source_headers'] == (
        {'worksheet': 'Данные', 'column': 'N', 'row': 210, 'value': '< 2 um'},
    )
    override_measurement = cast('Mapping[str, object]', overrides[0]['measurement'])
    assert cast('Mapping[str, object]', override_measurement['particle_size'])['upper'] == 2

    with pytest.raises(TypeError):
        cast('dict[str, object]', mapping.document)['dataset'] = {}


def test_sapozhnikov_review_confirms_identity_and_water_quantity_only():
    mapping = load_dataset_mapping(MAPPING_PATH)
    identity = cast('Mapping[str, object]', mapping.document['identity'])
    aliases = cast('Sequence[Mapping[str, object]]', identity['source_aliases'])
    alias = next(item for item in aliases if item['raw'] == '1988_сапожников')
    assert alias['canonical'] == '1988_Сапожников'
    assert alias['status'] == 'confirmed'

    source_rules = cast(
        'Sequence[Mapping[str, object]]', mapping.document['retention_source_rules']
    )
    source = next(item for item in source_rules if item['source'] == '1988_сапожников')
    observations = cast('Sequence[Mapping[str, object]]', source['observations'])
    assert len(observations) == 1
    observation = observations[0]
    assert observation['water_quantity'] == 'gravimetric_water_content'
    assert observation['water_unit'] is None
    assert observation['canonical_water_unit'] == 'mass_fraction'
    assert observation['blockers'] == (
        'water_scale_by_source',
        'pressure_convention_by_source',
    )

    reconstruction_rules = cast(
        'Sequence[Mapping[str, object]]',
        mapping.document['retention_reconstruction_rules'],
    )
    reconstruction = next(item for item in reconstruction_rules if item['id'] == 'sapozhnikov_1988')
    assert reconstruction['status'] == 'blocked'
    assert reconstruction['blockers'] == observation['blockers']


def test_rejects_checksum_drift_in_the_inventory():
    mapping = _mapping_document()
    inventory = _inventory_document()
    inventory['sha256'] = '0' * 64

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(mapping, inventory=inventory, retention_profile=_profile_document())

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        ('$.source.sha256', 'inventory.source_mismatch')
    ]


def test_rejects_an_unmapped_workbook_sheet():
    mapping = _mapping_document()
    worksheets = mapping['worksheets']
    assert isinstance(worksheets, list)
    mapping['worksheets'] = worksheets[:-1]

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert any(
        item.code == 'inventory.unmapped_sheet' and 'диссертации_ссылки' in item.message
        for item in captured.value.diagnostics
    )


def test_active_mapping_cannot_retain_scientific_blockers():
    mapping = copy.deepcopy(_mapping_document())
    dataset = mapping['dataset']
    assert isinstance(dataset, dict)
    dataset['status'] = 'active'

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert any(item.code == 'mapping.active_with_blockers' for item in captured.value.diagnostics)


def test_rejects_an_encoding_reference_to_an_unknown_blocker():
    mapping = _mapping_document()
    encodings = mapping['encodings']
    assert isinstance(encodings, list)
    first = encodings[0]
    assert isinstance(first, dict)
    first['blockers'] = ['invented_blocker']

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        ('$.encodings[0].blockers', 'mapping.unknown_blocker')
    ]


def test_confirmed_predictor_binding_cannot_retain_a_blocker():
    mapping = _mapping_document()
    bindings = mapping['predictor_bindings']
    assert isinstance(bindings, list)
    binding = bindings[0]
    assert isinstance(binding, dict)
    binding['status'] = 'confirmed'

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        (
            '$.predictor_bindings[0].blockers',
            'mapping.confirmed_predictor_binding_has_blockers',
        )
    ]


def test_rejects_overlapping_source_local_measurement_overrides():
    mapping = _mapping_document()
    bindings = mapping['predictor_bindings']
    assert isinstance(bindings, list)
    clay = next(
        binding
        for binding in bindings
        if isinstance(binding, dict) and binding.get('input') == 'clay'
    )
    overrides = clay['measurement_overrides']
    assert isinstance(overrides, list)
    duplicate = copy.deepcopy(overrides[0])
    duplicate['sample_rows'] = [{'first': 216, 'last': 218}]
    overrides.append(duplicate)

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert any(
        item.code == 'mapping.overlapping_measurement_override'
        for item in captured.value.diagnostics
    )


def test_rejects_retention_profile_checksum_drift():
    profile = _profile_document()
    profile['sha256'] = '0' * 64

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            _mapping_document(),
            inventory=_inventory_document(),
            retention_profile=profile,
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        ('$retention_profile.sha256', 'profile.source_mismatch')
    ]


def test_rejects_a_missing_source_rule_even_when_other_rules_are_valid():
    mapping = _mapping_document()
    rules = mapping['retention_source_rules']
    assert isinstance(rules, list)
    removed = rules.pop()
    assert isinstance(removed, dict)

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        ('$.retention_source_rules', 'mapping.missing_retention_source_rule')
    ]
    assert repr(removed['source']) in captured.value.diagnostics[0].message


def test_rejects_confirming_a_rule_without_explicit_units_and_convention():
    mapping = _mapping_document()
    rules = mapping['retention_source_rules']
    assert isinstance(rules, list)
    first = rules[0]
    assert isinstance(first, dict)
    observations = first['observations']
    assert isinstance(observations, list)
    rule = observations[0]
    assert isinstance(rule, dict)
    rule['status'] = 'confirmed'
    rule['blockers'] = []

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        (
            '$.retention_source_rules[0].observations[0]',
            'mapping.incomplete_confirmed_retention_rule',
        )
    ]


def test_rejects_a_crosswalk_whose_canonical_fields_disagree():
    mapping = _mapping_document()
    identity = mapping['identity']
    assert isinstance(identity, dict)
    crosswalks = identity['sample_crosswalks']
    assert isinstance(crosswalks, list)
    first = crosswalks[0]
    assert isinstance(first, dict)
    first['canonical_sample_number'] = 99

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        (
            '$.identity.sample_crosswalks[0].canonical_sample_id',
            'mapping.inconsistent_sample_crosswalk',
        )
    ]


def test_rejects_confirmed_reconstruction_with_proposed_transforms():
    mapping = _mapping_document()
    rules = mapping['retention_reconstruction_rules']
    assert isinstance(rules, list)
    panina_index, panina = next(
        (index, rule)
        for index, rule in enumerate(rules)
        if isinstance(rule, dict) and rule.get('id') == 'panina_2015'
    )
    assert isinstance(panina, dict)
    panina['status'] = 'confirmed'
    panina['blockers'] = []

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        (
            f'$.retention_reconstruction_rules[{panina_index}]',
            'mapping.confirmed_reconstruction_rule_has_proposals',
        )
    ]


def test_rejects_confirmed_reconstruction_with_proposed_axis_override():
    mapping = _mapping_document()
    rules = mapping['retention_reconstruction_rules']
    assert isinstance(rules, list)
    chudinova_index, chudinova = next(
        (index, rule)
        for index, rule in enumerate(rules)
        if isinstance(rule, dict) and rule.get('id') == 'chudinova_2009'
    )
    assert isinstance(chudinova, dict)
    chudinova['status'] = 'confirmed'
    chudinova['blockers'] = []

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        (
            f'$.retention_reconstruction_rules[{chudinova_index}]',
            'mapping.confirmed_reconstruction_rule_has_proposals',
        )
    ]


def test_rejects_duplicate_reconstruction_coverage_for_one_long_source():
    mapping = _mapping_document()
    rules = mapping['retention_reconstruction_rules']
    assert isinstance(rules, list)
    duplicate = copy.deepcopy(rules[0])
    assert isinstance(duplicate, dict)
    duplicate['id'] = 'duplicate_source_rule'
    rules.append(duplicate)

    with pytest.raises(DatasetMappingValidationError) as captured:
        load_dataset_mapping(
            mapping,
            inventory=_inventory_document(),
            retention_profile=_profile_document(),
        )

    assert [(item.path, item.code) for item in captured.value.diagnostics] == [
        (
            '$.retention_reconstruction_rules',
            'mapping.duplicate_retention_reconstruction_source',
        )
    ]


def test_normalization_summary_balances_the_bound_profile_without_measurements():
    profile = _profile_document()
    summary = json.loads(SUMMARY_PATH.read_text(encoding='utf-8'))

    assert summary['sha256'] == profile['sha256']
    assert summary['source_filename'] == profile['source_filename']
    assert summary['sheet_name'] == profile['sheet_name']
    assert summary['total_data_rows'] == profile['total_data_rows']
    assert (
        summary['normalized_observation_count'] + summary['excluded_observation_count']
        == profile['observation_count']
    )
    assert summary['fitted_parameter_count'] == profile['fitted_parameter_count']
    assert summary['unclassified_exclusion_count'] == profile['unclassified_count']
    assert summary['missing_source_exclusion_count'] == profile['missing_source_count']
    assert 'observations' not in summary
    assert 'fitted_parameters' not in summary


def test_reconstruction_audit_keeps_point_integrity_separate_from_identity():
    audit = json.loads(RECONSTRUCTION_PATH.read_text(encoding='utf-8'))

    assert audit['rule_count'] == 27
    assert audit['profile_source_count'] == 27
    assert audit['unaudited_source_count'] == 0
    assert audit['unaudited_sources'] == []
    assert audit['reconstructable_rule_count'] == 21
    assert audit['normalization_ready_rule_count'] == 6
    rules = {rule['rule_id']: rule for rule in audit['rules']}
    assert sum(rule['matched_point_count'] for rule in rules.values()) == 1741
    chestnova = rules['chestnova_2017']
    assert chestnova['matched_point_count'] == 130
    assert chestnova['identity_status'] == 'exact_unique'
    assert chestnova['normalization_ready'] is True
    gumatov = rules['gumatov_1991']
    assert gumatov['matched_point_count'] == 190
    assert gumatov['wide_missing_water_count'] == 19
    assert gumatov['identity_status'] == 'exact_unique'
    assert gumatov['reconstructable'] is True
    sapozhnikov = rules['sapozhnikov_1988']
    assert sapozhnikov['matched_point_count'] == 108
    assert sapozhnikov['proposed_pressure_replacement_count'] == 1
    assert sapozhnikov['identity_status'] == 'exact_unique'
    assert sapozhnikov['blockers'] == [
        'water_scale_by_source',
        'pressure_convention_by_source',
    ]
    khaydapova = rules['khaydapova_2001']
    assert khaydapova['point_multiset_status'] == 'exact'
    assert khaydapova['resolved_group_count'] == 0
    assert khaydapova['unresolved_group_count'] == 7
    assert khaydapova['reconstructable'] is False
    panina = rules['panina_2015']
    assert panina['matched_point_count'] == 132
    assert panina['point_multiset_status'] == 'exact'
    assert panina['ambiguous_row_match_count'] == 6
    assert panina['resolved_group_count'] == 1
    assert panina['unresolved_group_count'] == 26
    assert panina['matched_parameter_count'] == 48
    assert panina['parameter_multiset_status'] == 'exact'
    assert panina['resolved_parameter_group_count'] == 2
    assert panina['unresolved_parameter_group_count'] == 18
    assert panina['identity_status'] == 'unresolved'
    assert panina['parameter_identity_status'] == 'unresolved'
    assert panina['reconstructable'] is False
    sidorova = rules['sidorova_2016']
    assert sidorova['matched_point_count'] == 17
    assert sidorova['wide_missing_water_count'] == 5
    assert sidorova['identity_status'] == 'exact_unique'
    makarychev = rules['makarychev_2018']
    assert makarychev['matched_point_count'] == 96
    assert makarychev['resolved_group_count'] == 16
    assert makarychev['identity_status'] == 'exact_unique'


def test_reconstruction_audit_covers_special_source_structures():
    audit = json.loads(RECONSTRUCTION_PATH.read_text(encoding='utf-8'))
    rules = {rule['rule_id']: rule for rule in audit['rules']}

    kokareva = rules['kokareva_2007']
    assert kokareva['point_multiset_status'] == 'not_applicable'
    assert kokareva['observation_reconstructable'] is None
    assert kokareva['matched_parameter_count'] == 20
    assert kokareva['parameter_identity_status'] == 'exact_unique'
    assert kokareva['parameter_reconstructable'] is True
    assert kokareva['reconstructable'] is True

    bolotov = rules['bolotov_2014']
    assert bolotov['matched_point_count'] == 168
    assert bolotov['wide_missing_water_count'] == 1
    assert bolotov['long_missing_water_count'] == 1
    assert bolotov['identity_status'] == 'exact_unique'

    makarychev = rules['makarychev_2014_2']
    assert makarychev['matched_point_count'] == 35
    assert makarychev['identity_status'] == 'exact_unique'

    umarova = rules['umarova_2008']
    assert umarova['wide_missing_water_count'] == 22
    assert umarova['excluded_wide_water_count'] == 7
    assert umarova['reconstructable'] is True

    shvarov = rules['shvarov_2008']
    assert shvarov['matched_point_count'] == 105
    assert shvarov['long_only_point_count'] == 14
    assert shvarov['reconstructable'] is False

    chudinova = rules['chudinova_2009']
    assert chudinova['axis_override_count'] == 6
    assert chudinova['proposed_axis_override_count'] == 6
    assert chudinova['reconstructable'] is True


def test_predictor_audit_covers_every_declared_retention_sample_without_values():
    audit = json.loads(PREDICTOR_PATH.read_text(encoding='utf-8'))

    assert audit['schema_version'] == 2
    assert audit['public_function_count'] == 5
    assert audit['candidate_sample_count'] == 206
    assert audit['function_audits'] == [
        {
            'function': 'calc_ptf_clapp1978',
            'input_count': 1,
            'candidate_sample_count': 206,
            'complete_input_sample_count': 89,
            'eligible_sample_count': 0,
            'excluded_sample_count': 206,
        },
        {
            'function': 'calc_ptf_gunarathna2019_vwc10_set1',
            'input_count': 1,
            'candidate_sample_count': 206,
            'complete_input_sample_count': 51,
            'eligible_sample_count': 0,
            'excluded_sample_count': 206,
        },
        {
            'function': 'calc_ptf_gunarathna2019_vwc1500_set1',
            'input_count': 1,
            'candidate_sample_count': 206,
            'complete_input_sample_count': 51,
            'eligible_sample_count': 0,
            'excluded_sample_count': 206,
        },
        {
            'function': 'calc_ptf_gunarathna2019_vwc33_set1',
            'input_count': 1,
            'candidate_sample_count': 206,
            'complete_input_sample_count': 51,
            'eligible_sample_count': 0,
            'excluded_sample_count': 206,
        },
        {
            'function': 'calc_ptf_vereecken1989',
            'input_count': 4,
            'candidate_sample_count': 206,
            'complete_input_sample_count': 34,
            'eligible_sample_count': 0,
            'excluded_sample_count': 206,
        },
    ]
    assert audit['binding_audits'][0]['populated_count'] == 89
    assert audit['binding_audits'][0]['missing_count'] == 117
    assert audit['binding_audits'][0]['compatible_count'] == 0
    gunarathna_audits = [
        item
        for item in audit['binding_audits']
        if item['function'].startswith('calc_ptf_gunarathna2019_')
    ]
    assert len(gunarathna_audits) == 3
    assert {
        (
            item['populated_count'],
            item['measurement_compatible_count'],
            item['particle_size_compatible_count'],
        )
        for item in gunarathna_audits
    } == {(51, 0, 0)}
    clay_audit = next(
        item
        for item in audit['binding_audits']
        if item['function'] == 'calc_ptf_vereecken1989' and item['input'] == 'clay'
    )
    assert clay_audit['populated_count'] == 85
    assert clay_audit['measurement_compatible_count'] == 0
    assert clay_audit['particle_size_compatible_count'] == 12
    assert audit['exclusion_reasons'] == [
        {'label': 'density_units', 'count': 95},
        {'label': 'missing_input', 'count': 754},
        {'label': 'organic_property_provenance', 'count': 125},
        {'label': 'particle_size_schemes', 'count': 238},
        {'label': 'texture_classification', 'count': 89},
    ]
    assert 'values' not in audit
    assert 'eligibility' not in audit


def test_bolotov_primary_review_keeps_pressure_override_and_curve_identity():
    mapping = load_dataset_mapping(MAPPING_PATH)
    source_rules = cast(
        'Sequence[Mapping[str, object]]', mapping.document['retention_source_rules']
    )
    source = next(
        item
        for item in source_rules
        if item['source'] == '2014_\u0411\u043e\u043b\u043e\u0442\u043e\u0432'
    )
    (rule,) = cast('Sequence[Mapping[str, object]]', source['observations'])
    assert rule['status'] == 'confirmed'
    assert rule['water_unit'] == 'volume_fraction'
    assert rule['pressure_encoding'] == 'pF'
    assert rule['pressure_representation'] == 'log10_kilopascal'
    assert rule['pressure_convention'] == 'magnitude'
    identity = cast('Mapping[str, object]', mapping.document['identity'])
    rows = cast('Sequence[Mapping[str, object]]', identity['sample_crosswalks'])
    crosswalks = {item['raw_sample_id']: item for item in rows}
    # Lexical long-sheet ordering is not the master profile order.
    prefix = '2014_\u0411\u043e\u043b\u043e\u0442\u043e\u0432'
    assert crosswalks[prefix + '_10']['canonical_sample_number'] == 4
    assert crosswalks[prefix + '_2']['canonical_sample_number'] == 7
    assert crosswalks[prefix + '_5']['canonical_sample_number'] == 10
    audit = json.loads(RECONSTRUCTION_PATH.read_text(encoding='utf-8'))
    bolotov = next(item for item in audit['rules'] if item['rule_id'] == 'bolotov_2014')
    assert bolotov['normalization_ready'] is True
    assert bolotov['matching_confirmed_crosswalk_count'] == 12
    assert bolotov['wide_missing_water_count'] == 1
    assert bolotov['long_missing_water_count'] == 1


@pytest.mark.parametrize('defect', ['missing', 'duplicate', 'coordinate', 'source', 'identity'])
def test_panina_row_review_contract_rejects_incomplete_or_inconsistent_policy(defect: str):
    document = _mapping_document()
    policies = document['retention_row_reviews']
    assert isinstance(policies, list)
    policy = policies[0]
    decisions = policy['decisions']
    if defect == 'missing':
        del document['retention_row_reviews']
    elif defect == 'duplicate':
        decisions.append(copy.deepcopy(decisions[0]))
    elif defect == 'coordinate':
        decisions[0]['row'] = decisions[1]['row']
    elif defect == 'source':
        policy['source'] = 'unreviewed'
    else:
        release = next(item for item in decisions if 'canonical_sample_id' in item)
        release['canonical_sample_id'] = 'wrong'
    with pytest.raises(DatasetMappingValidationError) as error:
        load_dataset_mapping(
            document, inventory=_inventory_document(), retention_profile=_profile_document()
        )
    assert any('retention_row_review' in item.code for item in error.value.diagnostics)


def test_panina_releases_only_unique_nonsaturation_rows():
    document = _mapping_document()
    policies = document['retention_row_reviews']
    assert isinstance(policies, list)
    decisions = policies[0]['decisions']
    assert len(decisions) == 132
    assert sum('canonical_sample_id' in item for item in decisions) == 116
    assert (
        sum(item.get('exclusion_reason') == 'unreviewed_pressure_value' for item in decisions) == 12
    )
    assert (
        sum(item.get('exclusion_reason') == 'ambiguous_sample_identity' for item in decisions) == 4
    )
    by_row = {item['row']: item for item in decisions}
    assert by_row[1379]['exclusion_reason'] == 'ambiguous_sample_identity'
    assert by_row[1372]['exclusion_reason'] == 'unreviewed_pressure_value'
    assert by_row[1373]['canonical_sample_number'] == 1
    summary = json.loads(SUMMARY_PATH.read_text(encoding='utf-8'))
    assert summary['normalized_observation_count'] == 1036
    assert summary['excluded_observation_count'] == 719


def test_other_partial_sources_preserve_ambiguous_and_omitted_points():
    document = _mapping_document()
    policies = document['retention_row_reviews']
    assert isinstance(policies, list)
    badenko, umarova = policies[1:3]
    assert len(badenko['decisions']) == 108
    assert sum('canonical_sample_id' in item for item in badenko['decisions']) == 106
    assert {item['row'] for item in badenko['decisions'] if 'exclusion_reason' in item} == {
        1000,
        1086,
    }
    assert len(umarova['decisions']) == 81
    assert all('canonical_sample_id' in item for item in umarova['decisions'])
    rules = document['retention_reconstruction_rules']
    assert isinstance(rules, list)
    reconstruction = next(item for item in rules if item['id'] == 'umarova_2008')
    assert reconstruction['expected_missing_water_count'] == 22
    assert len(reconstruction['wide_excluded_cells']) == 7
    assert reconstruction['status'] == 'blocked'


def test_sadovnikova_review_preserves_weight_basis_and_quarantines_pressure_placeholders():
    document = _mapping_document()
    policies = document['retention_row_reviews']
    assert isinstance(policies, list)
    policy = policies[3]
    decisions = policy['decisions']
    assert len(decisions) == 63
    assert sum('canonical_sample_id' in item for item in decisions) == 61
    assert {
        (item['row'], item['exclusion_reason']) for item in decisions if 'exclusion_reason' in item
    } == {(778, 'unreviewed_pressure_value'), (793, 'unreviewed_pressure_value')}
    sources = document['retention_source_rules']
    assert isinstance(sources, list)
    source = next(item for item in sources if item['source'] == policy['source'])
    (rule,) = source['observations']
    assert rule['water_quantity'] == 'gravimetric_water_content'
    assert rule['water_unit'] == 'mass_percent'
    assert rule['pressure_representation'] == 'log10_kilopascal'
    assert rule['requires_row_review'] is True
    assert rule['status'] == 'confirmed'


def test_moiseev_primary_table_releases_experiments_and_excludes_statistic_columns():
    document = _mapping_document()
    policies = document['retention_row_reviews']
    assert isinstance(policies, list)
    decisions = policies[4]['decisions']
    assert len(decisions) == 29
    assert sum('canonical_sample_id' in item for item in decisions) == 23
    excluded = {
        item['row']: item['exclusion_reason'] for item in decisions if 'exclusion_reason' in item
    }
    assert excluded == {
        1795: 'unreviewed_pressure_value',
        1797: 'non_observation_table_value',
        1805: 'unreviewed_pressure_value',
        1807: 'non_observation_table_value',
        1814: 'unreviewed_pressure_value',
        1816: 'non_observation_table_value',
    }
    sources = document['retention_source_rules']
    assert isinstance(sources, list)
    source = next(item for item in sources if item['source'] == policies[4]['source'])
    (rule,) = source['observations']
    assert rule['water_unit'] == 'volume_percent'
    assert rule['pressure_representation'] == 'pf_log10_centimeter_water_head'
    assert rule['requires_row_review'] is True


@pytest.mark.parametrize(
    ('rule_id', 'quantity', 'unit'),
    [
        ('vasyukov_2012', 'volumetric_water_content', 'volume_fraction'),
        ('pestonova_2007', 'gravimetric_water_content', 'mass_percent'),
    ],
)
def test_known_water_basis_does_not_establish_an_unlabelled_pressure_unit(
    rule_id: str, quantity: str, unit: str
):
    document = _mapping_document()
    rules = document['retention_reconstruction_rules']
    assert isinstance(rules, list)
    reconstruction = next(item for item in rules if item['id'] == rule_id)
    sources = document['retention_source_rules']
    assert isinstance(sources, list)
    source = next(item for item in sources if item['source'] == reconstruction['long_source'])
    (rule,) = source['observations']
    assert rule['water_quantity'] == quantity
    assert rule['water_unit'] == unit
    assert rule['pressure_encoding'] == 'pF'
    assert rule['pressure_representation'] is None
    assert rule['pressure_convention'] is None
    assert rule['status'] == 'blocked'
    assert rule['blockers'] == ['pressure_convention_by_source']
    assert reconstruction['status'] == 'blocked'


@pytest.mark.parametrize(
    ('rule_id', 'water_unit'),
    [('shvarov_2008', 'mass_percent'), ('shein_2012', 'volume_fraction')],
)
def test_physical_units_cannot_release_unreviewed_retention_provenance(
    rule_id: str, water_unit: str
):
    document = _mapping_document()
    reconstructions = document['retention_reconstruction_rules']
    assert isinstance(reconstructions, list)
    reconstruction = next(item for item in reconstructions if item['id'] == rule_id)
    sources = document['retention_source_rules']
    assert isinstance(sources, list)
    source = next(item for item in sources if item['source'] == reconstruction['long_source'])
    (rule,) = source['observations']
    assert rule['status'] == 'blocked'
    assert 'retention_observation_provenance' in rule['blockers']
    assert 'retention_observation_provenance' in reconstruction['blockers']

    rule.update(
        status='confirmed',
        water_unit=water_unit,
        pressure_convention='magnitude',
        blockers=['retention_observation_provenance'],
    )
    with pytest.raises(DatasetMappingValidationError) as error:
        load_dataset_mapping(
            document, inventory=_inventory_document(), retention_profile=_profile_document()
        )
    assert any(
        item.code == 'mapping.confirmed_retention_rule_has_blockers'
        for item in error.value.diagnostics
    )


def test_real_quality_artifact_exports_counts_without_measurement_records():
    path = REPOSITORY_ROOT / 'evaluation/datasets/meta_v3_3.quality-summary.json'
    summary = json.loads(path.read_text(encoding='utf-8'))
    assert set(summary) == {
        'schema_version',
        'dataset_id',
        'source_filename',
        'workbook_sha256',
        'mapping_sha256',
        'normalized_observation_count',
        'normalized_sample_count',
        'monotonicity_tolerance_volume_fraction',
        'scope',
        'scoring_eligibility',
        'sources',
    }
    assert summary['workbook_sha256'] == _profile_document()['sha256']
    assert summary['scoring_eligibility'] == 'not_established_by_this_report'
    assert summary['monotonicity_tolerance_volume_fraction'] == 0
    allowed_counts = {
        'normalized_sample_count',
        'normalized_observation_count',
        'gravimetric_sample_count',
        'volumetric_sample_count',
        'diagnosed_volumetric_sample_count',
        'unsupported_semantics_sample_count',
        'duplicate_pressure_sample_count',
        'increasing_water_sample_count',
        'increasing_water_adjacent_pair_count',
        'outside_volume_bounds_sample_count',
    }
    for source in summary['sources']:
        assert set(source) <= {'source', *allowed_counts}
        assert all(
            type(value) is int and value >= 0 for key, value in source.items() if key != 'source'
        )
    assert sum(source['normalized_observation_count'] for source in summary['sources']) == 1036
    assert sum(source['normalized_sample_count'] for source in summary['sources']) == 109
    assert (
        sum(source.get('diagnosed_volumetric_sample_count', 0) for source in summary['sources'])
        == 59
    )
