import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from openpyxl import Workbook

from ptfkit_eval import (
    DatasetMapping,
    RetentionNormalizationError,
    normalize_retention_workbook,
    write_retention_normalization_summary,
)


HEADERS = [
    'sample_id',
    'source',
    'sample_number',
    'Формат данных влажности почвы',
    'Формат данных давления влаги',
    'Переменная/Давление влаги',
    'Значение/Содержание влаги',
]


def _workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'ОГХ'
    sheet.append(HEADERS)
    sheet.append(['a_1', 'a', 1, 'W', 'pF', 2, 25])
    sheet.append(['a_1', 'a', 1, 'W', 'pF', 1, 0.25])
    sheet.append(['b_2', 'b', 2, 'Q', 'kPa', -33, 0.5])
    sheet.append(['c_3', 'c', 3, 'W', 'pF', 2, 25])
    sheet.append(['p_4', 'p', 4, 'VGN', None, 'Qr', 0.05])
    sheet.append(['a_5', 'a', 5, 'W', 'pF', 2, 125])
    sheet.append(['x_6', 'x', 6, 'X', 'pF', 2, 20])
    sheet.append(['missing', None, 7, 'W', 'pF', 2, 20])
    sheet.append(['stale_cached_id', 'a', 8, 'W', 'pF', 2, 25])
    workbook.save(path)
    workbook.close()


def _rule(
    *,
    source: str,
    water_encoding: str,
    pressure_encoding: str,
    status: str,
    water_quantity: str,
    water_unit: str | None,
    canonical_water_unit: str,
    pressure_representation: str,
    pressure_convention: str | None,
    blockers: list[str],
) -> dict[str, object]:
    return {
        'source': source,
        'observations': [
            {
                'water_encoding': water_encoding,
                'pressure_encoding': pressure_encoding,
                'status': status,
                'water_quantity': water_quantity,
                'water_unit': water_unit,
                'canonical_water_unit': canonical_water_unit,
                'pressure_representation': pressure_representation,
                'pressure_convention': pressure_convention,
                'canonical_pressure_unit': 'kilopascal',
                'blockers': blockers,
                'evidence': 'Test evidence.',
            }
        ],
    }


def _mapping(path: Path) -> DatasetMapping:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rules = [
        _rule(
            source='a',
            water_encoding='W',
            pressure_encoding='pF',
            status='confirmed',
            water_quantity='gravimetric_water_content',
            water_unit='mass_percent',
            canonical_water_unit='mass_fraction',
            pressure_representation='pf_log10_centimeter_water_head',
            pressure_convention='magnitude',
            blockers=[],
        ),
        _rule(
            source='b',
            water_encoding='Q',
            pressure_encoding='kPa',
            status='confirmed',
            water_quantity='volumetric_water_content',
            water_unit='volume_fraction',
            canonical_water_unit='volume_fraction',
            pressure_representation='kilopascal',
            pressure_convention='negative',
            blockers=[],
        ),
        _rule(
            source='c',
            water_encoding='W',
            pressure_encoding='pF',
            status='blocked',
            water_quantity='gravimetric_water_content',
            water_unit=None,
            canonical_water_unit='mass_fraction',
            pressure_representation='pf_log10_centimeter_water_head',
            pressure_convention=None,
            blockers=['water_scale_by_source'],
        ),
    ]
    profile = {
        'sheet_name': 'ОГХ',
        'total_data_rows': 9,
        'observation_count': 6,
        'fitted_parameter_count': 1,
        'unclassified_count': 1,
        'missing_source_count': 1,
    }
    return DatasetMapping(
        dataset_id='test',
        status='draft_blocked',
        source_filename=path.name,
        source_sha256=digest,
        document={
            'identity': {
                'source_aliases': [
                    {
                        'worksheet': 'ОГХ',
                        'raw': 'a',
                        'canonical': 'canonical_a',
                        'status': 'confirmed',
                        'evidence': 'Test evidence.',
                    }
                ],
                'sample_crosswalks': [
                    {
                        'worksheet': 'ОГХ',
                        'raw_sample_id': 'a_1',
                        'canonical_sample_id': 'canonical_a_9',
                        'canonical_source': 'canonical_a',
                        'canonical_sample_number': 9,
                        'evidence_cells': ['Данные!X2:Y2'],
                        'status': 'confirmed',
                        'evidence': 'Test evidence.',
                    }
                ],
            },
            'retention_source_rules': rules,
        },
        inventory={},
        retention_profile=profile,
    )


def test_normalizes_only_confirmed_rules_and_balances_every_row(tmp_path: Path):
    path = tmp_path / 'retention.xlsx'
    _workbook(path)

    result = normalize_retention_workbook(path, _mapping(path))

    assert result.summary.total_data_rows == 9
    assert result.summary.input_observation_count == 6
    assert result.summary.normalized_observation_count == 3
    assert result.summary.excluded_observation_count == 3
    assert result.summary.fitted_parameter_count == 1
    assert result.summary.unclassified_exclusion_count == 1
    assert result.summary.missing_source_exclusion_count == 1

    first, second, third = result.observations
    assert first.pressure_kilopascal == pytest.approx(9.80665)
    assert first.sample_id == 'canonical_a_9'
    assert first.source == 'canonical_a'
    assert first.sample_number == 9
    assert first.pressure_quantity == 'matric_potential'
    assert first.pressure_unit == 'kilopascal'
    assert first.pressure_convention == 'magnitude'
    assert first.water_content == pytest.approx(0.25)
    assert first.water_unit == 'mass_fraction'
    assert first.water_basis == 'dry_soil_mass'
    assert first.source_cells == (
        *(f'ОГХ!{column}2' for column in 'ABCDEFG'),
        'Данные!X2:Y2',
    )
    assert second.water_content == pytest.approx(0.0025)
    assert third.pressure_kilopascal == pytest.approx(33)
    assert third.water_content == pytest.approx(0.5)
    assert third.water_unit == 'volume_fraction'
    assert third.water_basis == 'bulk_volume'

    assert [
        (item.model_family, item.parameter_name, item.value) for item in result.fitted_parameters
    ] == [('van_genuchten', 'Qr', 0.05)]
    assert [(item.row, item.reason) for item in result.exclusions] == [
        (5, 'source_rule_blocked'),
        (7, 'water_content_out_of_range'),
        (8, 'unclassified_water_encoding'),
        (9, 'missing_source'),
        (10, 'sample_identity_mismatch'),
    ]
    assert [(item.label, item.count) for item in result.summary.blocker_counts] == [
        ('retention_reconstruction', 1),
        ('water_scale_by_source', 1),
    ]


def test_summary_is_stable_and_does_not_redistribute_measurements(tmp_path: Path):
    path = tmp_path / 'retention.xlsx'
    _workbook(path)
    result = normalize_retention_workbook(path, _mapping(path))
    first = tmp_path / 'first.json'
    second = tmp_path / 'second.json'

    write_retention_normalization_summary(result, first)
    write_retention_normalization_summary(result, second)

    assert first.read_bytes() == second.read_bytes()
    document = json.loads(first.read_text(encoding='utf-8'))
    assert document['normalized_observation_count'] == 3
    assert '9.80665' not in first.read_text(encoding='utf-8')
    assert '0.05' not in first.read_text(encoding='utf-8')


def test_rejects_workbook_bytes_not_bound_to_the_mapping(tmp_path: Path):
    path = tmp_path / 'retention.xlsx'
    _workbook(path)
    mapping = _mapping(path)
    changed_path = tmp_path / 'changed.xlsx'
    changed_path.write_bytes(path.read_bytes() + b'changed')
    changed_mapping = DatasetMapping(
        dataset_id=mapping.dataset_id,
        status=mapping.status,
        source_filename=changed_path.name,
        source_sha256=mapping.source_sha256,
        document=mapping.document,
        inventory=mapping.inventory,
        retention_profile=mapping.retention_profile,
    )

    with pytest.raises(RetentionNormalizationError, match='checksum'):
        normalize_retention_workbook(changed_path, changed_mapping)


@pytest.mark.parametrize(
    ('representation', 'encoding', 'axis', 'convention', 'expected'),
    [
        ('log10_kilopascal', 'pF', -1, 'magnitude', 0.1),
        ('log10_kilopascal', 'pF', 0, 'magnitude', 1),
        ('log10_kilopascal', 'pF', 3, 'magnitude', 1000),
        ('log10_kilopascal', 'pF', 2, 'negative', None),
        ('log10_kilopascal', 'pF', 400, 'magnitude', None),
        ('megapascal', 'mPa', 0.001, 'magnitude', 1),
        ('megapascal', 'mPa', 140, 'magnitude', 140000),
        ('megapascal', 'mPa', -0.01, 'negative', 10),
        ('megapascal', 'mPa', -0.01, 'magnitude', None),
        ('megapascal', 'mPa', 1e308, 'magnitude', None),
    ],
)
def test_reviewed_pressure_representation_overrides_raw_label(
    tmp_path: Path,
    *,
    representation: str,
    encoding: str,
    axis: float,
    convention: str,
    expected: float | None,
):
    path = tmp_path / 'log-pressure.xlsx'
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = '\u041e\u0413\u0425'
    sheet.append(HEADERS)
    sheet.append(['b_2', 'b', 2, 'Q', encoding, axis, 0.5])
    workbook.save(path)
    workbook.close()
    mapping = _mapping(path)
    document = dict(mapping.document)
    document['retention_source_rules'] = [
        _rule(
            source='b',
            water_encoding='Q',
            pressure_encoding=encoding,
            status='confirmed',
            water_quantity='volumetric_water_content',
            water_unit='volume_fraction',
            canonical_water_unit='volume_fraction',
            pressure_representation=representation,
            pressure_convention=convention,
            blockers=[],
        )
    ]
    mapping = replace(
        mapping,
        document=document,
        retention_profile={
            'sheet_name': '\u041e\u0413\u0425',
            'total_data_rows': 1,
            'observation_count': 1,
            'fitted_parameter_count': 0,
            'unclassified_count': 0,
            'missing_source_count': 0,
        },
    )

    result = normalize_retention_workbook(path, mapping)

    if expected is None:
        assert result.observations == ()
        assert [item.reason for item in result.exclusions] == ['pressure_convention_mismatch']
        return
    assert len(result.observations) == 1
    observation = result.observations[0]
    assert observation.pressure_encoding == encoding
    assert observation.raw_pressure == axis
    assert observation.pressure_kilopascal == pytest.approx(expected)
    assert observation.water_content == 0.5
    assert observation.water_quantity == 'volumetric_water_content'
    assert observation.water_unit == 'volume_fraction'
    assert observation.water_basis == 'bulk_volume'
