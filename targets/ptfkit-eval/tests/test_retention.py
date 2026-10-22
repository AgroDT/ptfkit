import hashlib
import json
from pathlib import Path

import pytest
from openpyxl import Workbook

from ptfkit_eval import (
    RetentionProfileError,
    profile_retention_workbook,
    write_retention_profile,
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
    sheet.append(['a_1', 'a', 1, 'W', 'pF', 0, 0.25])
    sheet.append(['a_1', 'a', 1, 'W', 'pF', 1, 1.0])
    sheet.append(['a_1', 'a', 1, 'W', 'pF', 2, 25.0])
    sheet.append(['a_1', 'a', 1, 'VGN', None, 'Qr', 0.05])
    sheet.append(['a_1', 'a', 1, 'VGN', None, 'Qs', 0.45])
    sheet.append(['b_3', 'b', 3, '?', 'kPa', -33, 0.5])
    sheet.append(['b_3', 'b', 3, 'X', 'unknown', 'text', '-'])
    sheet.append(['missing', None, 4, 'W', 'pF', 2, 20])
    sheet.append(['b_missing', 'b', None, 'Q', 'pF', 'bad', None])
    workbook.save(path)
    workbook.close()


def test_profiles_row_roles_and_numeric_evidence_without_inferring_units(tmp_path: Path):
    path = tmp_path / 'retention.xlsx'
    _workbook(path)

    profile = profile_retention_workbook(path)

    assert profile.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert profile.total_data_rows == 9
    assert profile.source_count == 2
    assert profile.observation_count == 5
    assert profile.fitted_parameter_count == 2
    assert profile.unclassified_count == 1
    assert profile.missing_source_count == 1

    source_a = profile.sources[0]
    assert source_a.source == 'a'
    assert source_a.sample_count == 1
    assert source_a.observation_count == 3
    assert [(item.label, item.count) for item in source_a.fitted_parameters] == [
        ('Qr', 1),
        ('Qs', 1),
    ]
    encoding = source_a.encodings[0]
    assert (encoding.water_encoding, encoding.pressure_encoding) == ('W', 'pF')
    assert (encoding.first_row, encoding.last_row) == (2, 4)
    assert encoding.water_values.minimum == 0.25
    assert encoding.water_values.maximum == 25.0
    assert encoding.water_values.at_most_one_count == 2
    assert encoding.water_values.above_one_count == 1

    source_b = profile.sources[1]
    assert source_b.missing_sample_number_count == 1
    assert [(item.label, item.count) for item in source_b.unclassified_encodings] == [('X', 1)]
    unknown_water = source_b.encodings[0]
    assert unknown_water.water_encoding == '?'
    assert unknown_water.pressure_values.negative_count == 1
    volumetric = source_b.encodings[1]
    assert volumetric.water_encoding == 'Q'
    assert volumetric.pressure_values.nonnumeric_count == 1
    assert volumetric.water_values.missing_count == 1


def test_profile_json_is_stable_and_excludes_the_source_path(tmp_path: Path):
    private_directory = tmp_path / 'private'
    private_directory.mkdir()
    workbook_path = private_directory / 'retention.xlsx'
    _workbook(workbook_path)
    profile = profile_retention_workbook(workbook_path)
    first = tmp_path / 'first.json'
    second = tmp_path / 'second.json'

    write_retention_profile(profile, first)
    write_retention_profile(profile, second)

    assert first.read_bytes() == second.read_bytes()
    document = json.loads(first.read_text(encoding='utf-8'))
    assert document['source_filename'] == 'retention.xlsx'
    assert str(private_directory) not in first.read_text(encoding='utf-8')


def test_rejects_a_shifted_retention_layout(tmp_path: Path):
    path = tmp_path / 'shifted.xlsx'
    _workbook(path)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'ОГХ'
    sheet.append([*HEADERS[:-1], 'unexpected'])
    workbook.save(path)
    workbook.close()

    with pytest.raises(RetentionProfileError, match='columns B:G'):
        profile_retention_workbook(path)
