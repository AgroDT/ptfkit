import json
from pathlib import Path

import pytest
from _run_fixtures import dataset_document

from ptfkit_eval import EvaluationDocumentError, load_retention_dataset
from ptfkit_eval.documents import load_document


@pytest.mark.parametrize(
    ('contents', 'suffix'),
    [
        ('{"value": 1, "value": 2}', '.json'),
        ('value: 1\nvalue: 2\n', '.yaml'),
        ('value: &cycle [*cycle]\n', '.yaml'),
        ('base: &base {value: 1}\ncopy: {<<: *base}\n', '.yaml'),
        ('{"value": NaN}', '.json'),
        ('value: .inf\n', '.yaml'),
        ('2026-10-23: value\n', '.yaml'),
    ],
)
def test_rejects_ambiguous_or_nonportable_document_values(
    tmp_path: Path, contents: str, suffix: str
):
    path = tmp_path / f'input{suffix}'
    path.write_text(contents, encoding='utf-8')
    with pytest.raises(EvaluationDocumentError):
        load_document(path)


def test_measured_records_require_checksum_bound_source_file_lineage():
    document = json.loads(json.dumps(dataset_document()))
    feature = document['samples'][0]['features'][0]
    feature['origin'] = 'measured'
    with pytest.raises(EvaluationDocumentError, match='source_file'):
        load_retention_dataset(document)
    document['source_files'] = [{'id': 'workbook', 'filename': 'external.xlsx', 'sha256': 'a' * 64}]
    feature['source_file'] = 'workbook'
    loaded = load_retention_dataset(document)
    assert loaded.dataset_id == 'synthetic_sand'
