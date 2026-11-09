import copy
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from openpyxl import Workbook

from ptfkit_eval import (
    DatasetMapping,
    PredictorAuditError,
    audit_predictor_workbook,
    write_predictor_audit_summary,
)


def _workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'master'
    sheet.append(['sample_id', 'sample_number', 'source', 'texture', 'density'])
    sheet.append(['control', 0.1, 'source_a', 'axis', '< 2 um'])
    sheet.append(['source_a_1', 1, 'source_a', 'Raw sand', 1.2])
    sheet.append(['source_a_2', 2, 'source_a', 'Unmapped', None])
    sheet.append(['source_a_3', 3, 'source_a', None, 1.3])
    workbook.save(path)
    workbook.close()


def _mapping(
    path: Path,
    bindings: Sequence[Mapping[str, object]],
    *,
    density_measurement: Mapping[str, object] | None = None,
) -> DatasetMapping:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    columns = [
        {'column': 'A', 'role': 'sample_id', 'status': 'derived'},
        {'column': 'B', 'role': 'sample_number', 'status': 'confirmed'},
        {'column': 'C', 'role': 'source', 'status': 'confirmed'},
        {
            'column': 'D',
            'source_header': 'texture',
            'role': 'texture_class',
            'status': 'blocked',
        },
        {
            'column': 'E',
            'source_header': 'density',
            'role': 'dry_bulk_density',
            'status': 'blocked',
            'measurement': density_measurement or {'quantity': 'dry_bulk_density', 'unit': None},
        },
    ]
    reconstruction = {
        'master_worksheet': 'master',
        'blocks': [
            {
                'axis_row': 2,
                'first_sample_row': 3,
                'last_sample_row': 5,
                'first_column': 'F',
                'last_column': 'F',
            }
        ],
        'parameter_block': None,
    }
    return DatasetMapping(
        dataset_id='test',
        status='draft_blocked',
        source_filename=path.name,
        source_sha256=digest,
        document={
            'worksheets': [{'name': 'master', 'columns': columns}],
            'retention_reconstruction_rules': [reconstruction],
            'predictor_bindings': bindings,
        },
        inventory={},
        retention_profile={},
    )


def _categorical_manifest() -> dict[str, object]:
    return {
        'schema_version': 1,
        'functions': [
            {
                'id': 'texture_ptf',
                'inputs': [
                    {
                        'name': 'soil_texture',
                        'kind': 'categorical',
                        'enum': {
                            'values': [
                                {'value': 'sand'},
                                {'value': 'clay'},
                            ]
                        },
                    }
                ],
            }
        ],
    }


def test_audits_only_declared_sample_rows_and_requires_reviewed_categories(tmp_path: Path):
    path = tmp_path / 'predictors.xlsx'
    _workbook(path)
    bindings = [
        {
            'function': 'texture_ptf',
            'input': 'soil_texture',
            'worksheet': 'master',
            'column': 'D',
            'status': 'confirmed',
            'blockers': [],
            'category_map': [
                {
                    'raw': 'Raw sand',
                    'value': 'sand',
                    'status': 'confirmed',
                    'evidence': 'Fixture crosswalk.',
                }
            ],
            'evidence': 'Fixture binding.',
        }
    ]

    result = audit_predictor_workbook(
        path,
        _mapping(path, bindings),
        manifest=_categorical_manifest(),
    )

    assert [value.sample_key for value in result.values] == [
        'master!3',
        'master!4',
        'master!5',
    ]
    assert [(value.value, value.status) for value in result.values] == [
        ('sand', 'compatible'),
        (None, 'unknown_category'),
        (None, 'missing_input'),
    ]
    assert [(item.sample_key, item.eligible, item.reasons) for item in result.eligibility] == [
        ('master!3', True, ()),
        ('master!4', False, ('unknown_category',)),
        ('master!5', False, ('missing_input',)),
    ]
    assert result.summary.candidate_sample_count == 3
    assert result.summary.function_audits[0].complete_input_sample_count == 2
    assert result.summary.function_audits[0].eligible_sample_count == 1
    assert result.summary.binding_audits[0].populated_count == 2
    assert result.summary.binding_audits[0].compatible_count == 1


def test_blocked_binding_preserves_values_but_never_makes_them_eligible(tmp_path: Path):
    path = tmp_path / 'predictors.xlsx'
    _workbook(path)
    manifest = {
        'schema_version': 1,
        'functions': [
            {
                'id': 'density_ptf',
                'inputs': [
                    {
                        'name': 'bulk_density',
                        'kind': 'numeric',
                        'measurement': {
                            'quantity': 'dry_bulk_density',
                            'unit': 'gram_per_cubic_centimeter',
                            'basis': {'material': 'soil', 'denominator': 'bulk_volume'},
                        },
                    }
                ],
            }
        ],
    }
    bindings = [
        {
            'function': 'density_ptf',
            'input': 'bulk_density',
            'worksheet': 'master',
            'column': 'E',
            'status': 'blocked',
            'blockers': ['density_units'],
            'evidence': 'Fixture blocker.',
        }
    ]

    result = audit_predictor_workbook(path, _mapping(path, bindings), manifest=manifest)

    assert [value.raw_value for value in result.values] == [1.2, None, 1.3]
    assert [value.value for value in result.values] == [None, None, None]
    assert [value.status for value in result.values] == [
        'binding_blocked',
        'missing_input',
        'binding_blocked',
    ]
    assert result.summary.function_audits[0].complete_input_sample_count == 2
    assert result.summary.function_audits[0].eligible_sample_count == 0
    assert [(item.label, item.count) for item in result.summary.exclusion_reasons] == [
        ('density_units', 2),
        ('missing_input', 1),
    ]


def test_confirmed_numeric_binding_requires_the_manifest_measurement_method(tmp_path: Path):
    path = tmp_path / 'predictors.xlsx'
    _workbook(path)
    manifest = {
        'schema_version': 1,
        'functions': [
            {
                'id': 'density_ptf',
                'inputs': [
                    {
                        'name': 'bulk_density',
                        'kind': 'numeric',
                        'measurement': {
                            'quantity': 'dry_bulk_density',
                            'unit': 'gram_per_cubic_centimeter',
                            'basis': {'material': 'mineral_soil', 'denominator': 'bulk_volume'},
                            'particle_size': None,
                            'conditions': [],
                            'method': 'core_method',
                        },
                    }
                ],
            }
        ],
    }
    bindings = [
        {
            'function': 'density_ptf',
            'input': 'bulk_density',
            'worksheet': 'master',
            'column': 'E',
            'status': 'confirmed',
            'blockers': [],
            'evidence': 'Fixture binding.',
        }
    ]
    measurement = {
        'quantity': 'dry_bulk_density',
        'unit': 'gram_per_cubic_centimeter',
        'material_basis': 'mineral_soil',
        'denominator_basis': 'bulk_volume',
        'particle_size': None,
        'conditions': [],
        'method': 'different_method',
    }

    result = audit_predictor_workbook(
        path,
        _mapping(path, bindings, density_measurement=measurement),
        manifest=manifest,
    )

    assert [value.status for value in result.values] == [
        'measurement_contract_mismatch',
        'missing_input',
        'measurement_contract_mismatch',
    ]
    assert result.summary.function_audits[0].eligible_sample_count == 0

    measurement['method'] = 'core_method'
    compatible = audit_predictor_workbook(
        path,
        _mapping(path, bindings, density_measurement=measurement),
        manifest=manifest,
    )

    assert [(value.value, value.status) for value in compatible.values] == [
        (1.2, 'compatible'),
        (None, 'missing_input'),
        (1.3, 'compatible'),
    ]
    assert compatible.summary.function_audits[0].eligible_sample_count == 2


def test_source_local_measurement_override_does_not_treat_below_one_as_below_two(
    tmp_path: Path,
):
    path = tmp_path / 'predictors.xlsx'
    _workbook(path)
    expected_measurement = {
        'quantity': 'particle_mass_fraction',
        'unit': 'mass_percent',
        'basis': {'material': 'fine_earth', 'denominator': 'dry_mass'},
        'particle_size': {
            'unit': 'micrometer',
            'lower': None,
            'upper': {'value': 2, 'inclusive': False},
        },
        'conditions': [],
        'method': None,
    }
    actual_measurement = {
        'quantity': 'particle_mass_fraction',
        'unit': 'mass_percent',
        'material_basis': 'fine_earth',
        'denominator_basis': 'dry_mass',
        'particle_size': {
            'unit': 'micrometer',
            'lower': None,
            'upper': 1,
            'lower_inclusive': False,
            'upper_inclusive': False,
        },
        'conditions': [],
        'method': None,
    }
    override_measurement = copy.deepcopy(actual_measurement)
    override_particle_size = override_measurement['particle_size']
    assert isinstance(override_particle_size, dict)
    override_particle_size['upper'] = 2
    manifest = {
        'schema_version': 1,
        'functions': [
            {
                'id': 'clay_ptf',
                'inputs': [
                    {
                        'name': 'clay',
                        'kind': 'numeric',
                        'measurement': expected_measurement,
                    }
                ],
            }
        ],
    }
    bindings: list[dict[str, object]] = [
        {
            'function': 'clay_ptf',
            'input': 'clay',
            'worksheet': 'master',
            'column': 'E',
            'status': 'blocked',
            'blockers': ['particle_size_schemes'],
            'measurement_overrides': [
                {
                    'sample_rows': [{'first': 3, 'last': 3}],
                    'measurement': override_measurement,
                    'source_headers': [
                        {
                            'worksheet': 'master',
                            'column': 'E',
                            'row': 2,
                            'value': '< 2 um',
                        }
                    ],
                    'evidence': 'Fixture source-local header.',
                }
            ],
            'evidence': 'Fixture binding.',
        }
    ]

    result = audit_predictor_workbook(
        path,
        _mapping(path, bindings, density_measurement=actual_measurement),
        manifest=manifest,
    )

    audit = result.summary.binding_audits[0]
    assert audit.populated_count == 2
    assert audit.measurement_compatible_count == 1
    assert audit.particle_size_compatible_count == 1
    assert result.values[0].source_cells == ('master!E3', 'master!E2')
    assert result.values[2].source_cells == ('master!E5',)

    wrong_header = copy.deepcopy(bindings)
    wrong_overrides = wrong_header[0]['measurement_overrides']
    assert isinstance(wrong_overrides, list)
    wrong_override = wrong_overrides[0]
    assert isinstance(wrong_override, dict)
    source_headers = wrong_override['source_headers']
    assert isinstance(source_headers, list)
    source_header = source_headers[0]
    assert isinstance(source_header, dict)
    source_header['value'] = '< 1 um'
    with pytest.raises(PredictorAuditError, match='Source-local predictor header'):
        audit_predictor_workbook(
            path,
            _mapping(path, wrong_header, density_measurement=actual_measurement),
            manifest=manifest,
        )


def test_summary_is_deterministic_and_omits_raw_predictor_values(tmp_path: Path):
    path = tmp_path / 'predictors.xlsx'
    _workbook(path)
    bindings = [
        {
            'function': 'texture_ptf',
            'input': 'soil_texture',
            'worksheet': 'master',
            'column': 'D',
            'status': 'blocked',
            'blockers': ['texture_classification'],
            'evidence': 'Fixture blocker.',
        }
    ]
    result = audit_predictor_workbook(
        path,
        _mapping(path, bindings),
        manifest=_categorical_manifest(),
    )
    first = tmp_path / 'first.json'
    second = tmp_path / 'second.json'

    write_predictor_audit_summary(result, first)
    write_predictor_audit_summary(result, second)

    assert first.read_bytes() == second.read_bytes()
    document = json.loads(first.read_text(encoding='utf-8'))
    assert document['candidate_sample_count'] == 3
    assert 'Raw sand' not in first.read_text(encoding='utf-8')
    assert 'Unmapped' not in first.read_text(encoding='utf-8')


def test_rejects_workbook_not_bound_to_mapping_checksum(tmp_path: Path):
    path = tmp_path / 'predictors.xlsx'
    _workbook(path)
    mapping = _mapping(path, [])
    changed = tmp_path / path.name
    changed.write_bytes(path.read_bytes() + b'changed')

    with pytest.raises(PredictorAuditError, match='checksum'):
        audit_predictor_workbook(changed, mapping, manifest=_categorical_manifest())


def test_rejects_binding_that_is_absent_from_public_manifest(tmp_path: Path):
    path = tmp_path / 'predictors.xlsx'
    _workbook(path)
    bindings = [
        {
            'function': 'invented_ptf',
            'input': 'soil_texture',
            'worksheet': 'master',
            'column': 'D',
            'status': 'blocked',
            'blockers': ['texture_classification'],
            'evidence': 'Fixture typo.',
        }
    ]

    with pytest.raises(PredictorAuditError, match=r'invented_ptf\.soil_texture'):
        audit_predictor_workbook(
            path,
            _mapping(path, bindings),
            manifest=_categorical_manifest(),
        )
