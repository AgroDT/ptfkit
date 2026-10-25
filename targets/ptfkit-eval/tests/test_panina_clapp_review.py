import copy
import hashlib
import json
import runpy
from pathlib import Path

import pytest

from ptfkit_eval.documents import document_hash


def _fixture() -> tuple[dict, dict, bytes]:
    paper = b'reviewed paper fixture'
    document: dict = {
        'schema_version': 1,
        'dataset_id': 'fixture',
        'kind': 'measured',
        'method': 'measured retention',
        'target': {
            'quantity': 'volumetric_water_content',
            'unit': 'volume_fraction',
            'material_basis': 'unspecified',
            'denominator_basis': 'bulk_volume',
        },
        'source_files': [{'id': 'workbook', 'filename': 'fixture.xlsx', 'sha256': 'a' * 64}],
        'samples': [
            {'source_id': 'source', 'sample_id': name, 'profile_id': None, 'features': []}
            for name in ('keep', 'omit')
        ],
        'observations': [
            {
                'id': name,
                'source_id': 'source',
                'sample_id': name,
                'suction_kpa': 1000,
                'value': 0.4,
                'origin': 'measured',
                'review_status': 'confirmed',
                'quality_flags': [],
                'source_file': 'workbook',
                'source_cells': ['\u0414\u0430\u043d\u043d\u044b\u0435!A211:C211'],
            }
            for name in ('keep', 'omit')
        ],
    }
    review: dict = {
        'canonical_dataset_sha256': document_hash(document),
        'workbook_sha256': 'a' * 64,
        'paper': {
            'id': 'paper',
            'filename': 'paper.pdf',
            'sha256': hashlib.sha256(paper).hexdigest(),
        },
        'eligible_count': 1,
        'selected_samples': [
            {
                'source_id': 'source',
                'sample_id': 'keep',
                'texture': 'silt loam',
                'material_basis': 'mineral_soil',
                'profile_id': 'shared_profile',
                'category_system': 'clapp1978.UsdaTextureClass',
                'source_locations': ['Table 17'],
                'master_row': 211,
            }
        ],
    }
    return document, review, paper


def _namespace() -> dict:
    return runpy.run_path(
        str(Path(__file__).resolve().parents[3] / 'evaluation/experiments/panina_clapp/run.py')
    )


def test_reviewed_subset_preserves_targets_and_rejects_unsupported_class_or_paper():
    build = _namespace()['build_subset']
    document, review, paper = _fixture()
    before = copy.deepcopy(document)
    subset = build(document, json.dumps(review).encode(), paper)
    assert document == before
    assert subset['observations'] == document['observations'][:1]
    assert len(subset['samples']) == 1
    assert subset['samples'][0]['features'][0]['value'] == 'silt loam'
    assert subset['samples'][0]['features'][0]['origin'] == 'measured'
    assert subset['samples'][0]['features'][0]['source_file'] == 'paper'
    assert subset['target']['material_basis'] == 'mineral_soil'
    with pytest.raises(ValueError, match='source PDF'):
        build(document, json.dumps(review).encode(), b'changed')
    review['selected_samples'][0]['texture'] = 'silt'
    with pytest.raises(ValueError, match='unsupported'):
        build(document, json.dumps(review).encode(), paper)


def test_reviewed_clapp_run_uses_public_curve_and_withholds_single_profile_intervals(
    tmp_path: Path,
):
    namespace = _namespace()
    document, review, paper = _fixture()
    dataset_path, review_path, paper_path = (
        tmp_path / name for name in ('dataset.json', 'review.json', 'paper.pdf')
    )
    dataset_path.write_text(json.dumps(document), encoding='utf-8')
    review_path.write_text(json.dumps(review), encoding='utf-8')
    paper_path.write_bytes(paper)
    output = tmp_path / 'output'
    artifacts = namespace['run'](dataset_path, review_path, paper_path, output)
    decisions = json.loads((artifacts / 'point-decisions.json').read_bytes())
    # Published Clapp Table 2 silt-loam values: theta_s=0.485, psi_s=56.6 cm, b=5.3.
    expected = 0.485 * (56.6 * 0.0980665 / 1000) ** (1 / 5.3)
    assert len(decisions) == 1
    assert decisions[0]['eligible']
    assert decisions[0]['prediction']['value'] == pytest.approx(expected)
    report = (artifacts / 'report.md').read_text(encoding='utf-8')
    assert 'too_few_groups' in report
    with pytest.raises(FileExistsError):
        namespace['run'](dataset_path, review_path, paper_path, output)
