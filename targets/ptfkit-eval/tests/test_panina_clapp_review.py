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


def test_reviewed_classes_unlock_cosby_and_keep_exact_common_pressure_support(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    root = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root))
    comparison = runpy.run_path(str(root / 'evaluation/experiments/meta_v3_3/class_comparison.py'))
    document, review, paper = _fixture()
    # One wet point cannot be predicted by the registered Cosby dry branch;
    # both the wet and dry observations must remain in the input denominator.
    document['observations'] = [
        {**document['observations'][0], 'id': 'wet', 'suction_kpa': 0.1},
        {**document['observations'][0], 'id': 'dry', 'suction_kpa': 1000},
    ]
    review['canonical_dataset_sha256'] = document_hash(document)
    for name, raw in (
        ('dataset.json', json.dumps(document).encode()),
        ('review.json', json.dumps(review).encode()),
        ('paper.pdf', paper),
    ):
        (tmp_path / name).write_bytes(raw)
    _namespace()['run'](
        tmp_path / 'dataset.json',
        tmp_path / 'review.json',
        tmp_path / 'paper.pdf',
        tmp_path / 'clapp',
    )
    artifacts, summary = comparison['run'](tmp_path / 'clapp', tmp_path / 'comparison')
    dataset = json.loads((artifacts / 'dataset.json').read_bytes())
    features = dataset['samples'][0]['features']
    # Cosby Table 2 silt-loam coordinates; independent of the derivation helper.
    assert [(f['id'], f['value'], f['origin']) for f in features[1:]] == [
        ('sand', 17, 'derived'),
        ('silt', 70, 'derived'),
        ('clay', 13, 'derived'),
    ]
    assert all(f['derivation']['source_feature'] == 'texture' for f in features[1:])
    assert [p['id'] for p in dataset['observations']] == ['wet', 'dry']
    coverage = {r['candidate_id']: r for r in summary['coverage']['candidates']}
    assert coverage['clapp']['eligible_point_count'] == 2
    assert coverage['cosby']['observation_count'] == 2
    assert coverage['cosby']['eligible_point_count'] == 1
    cohorts = {(r['candidate_id'], r['kind']): r for r in summary['cohorts']}
    assert cohorts['clapp', 'maximal']['pressure_support_kpa'] == [0.1, 1000]
    for candidate in ('clapp', 'cosby'):
        common = cohorts[candidate, 'common']
        assert common['pressure_support_kpa'] == [1000]
        assert common['cohort']['summary']['point_count'] == 1
        assert common['confidence']['status'] == 'insufficient_evidence'
    assert summary['profile_count'] == 1
    assert summary['selection']['status'] == 'insufficient_evidence'
    invalid = copy.deepcopy(dataset)
    invalid['samples'][0]['features'] = features[:1]
    invalid['samples'][0]['features'][0]['origin'] = 'estimated'
    with pytest.raises(ValueError, match='reviewed measured USDA'):
        comparison['add_class_coordinates'](invalid)


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


def test_decision_report_keeps_fit_errors_intervals_and_selection_evidence_separate(tmp_path: Path):
    document, review, paper = _fixture()
    second = {**document['observations'][0], 'id': 'second', 'suction_kpa': 10000}
    document['observations'].append(second)
    review['canonical_dataset_sha256'] = document_hash(document)
    review.update(candidate_count=2, unsupported_class_count=0, unresolved_count=1, sources=[])
    dataset_path, review_path, paper_path = (
        tmp_path / name for name in ('dataset.json', 'review.json', 'paper.pdf')
    )
    dataset_path.write_text(json.dumps(document), encoding='utf-8')
    review_path.write_text(json.dumps(review), encoding='utf-8')
    paper_path.write_bytes(paper)
    artifacts = _namespace()['run'](dataset_path, review_path, paper_path, tmp_path / 'run')
    dataset_bytes = (artifacts / 'dataset.json').read_bytes()
    evaluated = json.loads(dataset_bytes)
    # Serialized fitter outputs are the reporting input. Residuals -0.03 and +0.04
    # give MAE 0.035 and RMSE sqrt(0.00125), independently of the native PTF.
    observations = [
        {'reference': 'keep', 'suction_kpa': 1000, 'water_content': 0.4},
        {'reference': 'second', 'suction_kpa': 10000, 'water_content': 0.4},
    ]
    parameter = {
        'name': 'theta_s',
        'value': 0.5,
        'unit': 'volume_fraction',
        'parameter_interval': {'lower': -0.1, 'upper': 1.2},
    }
    records: list[dict] = []
    for family in (
        'van_genuchten_mualem_v1',
        'van_genuchten_m1_v1',
        'brooks_corey_v1',
        'clapp1978_gradual_air_entry_v1',
    ):
        accepted = family == 'van_genuchten_mualem_v1'
        records.append(
            {
                'source_id': 'source',
                'sample_id': 'keep',
                'quality': {'diagnostics': []},
                'uncertainty_support': {'parameter_intervals_outside_bounds': ['theta_s']},
                'fit': {
                    'plan': {'family_id': family},
                    'observations': observations,
                    'status': 'fitted' if accepted else 'failed',
                    'reason': None if accepted else 'boundary_solution',
                    'parameters': [parameter] if accepted else [],
                    'identifiability': None,
                    'points': [
                        {'observation': point, 'fitted_value': value}
                        for point, value in zip(observations, (0.37, 0.44), strict=True)
                    ]
                    if accepted
                    else [],
                },
            }
        )
    fits = {
        'dataset': evaluated,
        'dataset_sha256': document_hash(evaluated),
        'dataset_file_sha256': hashlib.sha256(dataset_bytes).hexdigest(),
        'summary': [],
        'results': records,
    }
    fits_path = tmp_path / 'fits.json'
    fits_path.write_text(json.dumps(fits), encoding='utf-8')
    namespace = runpy.run_path(
        str(Path(__file__).resolve().parents[3] / 'evaluation/experiments/panina_clapp/report.py')
    )
    output = tmp_path / 'decision'
    namespace['publish'](artifacts, review_path, output, fits_path=fits_path)
    summary = json.loads((output / 'summary.json').read_bytes())
    rows = summary['retention_approximations']['rows']
    assert len(rows) == 4
    assert rows[0]['mae'] == pytest.approx(0.035)
    assert rows[0]['rmse'] == pytest.approx(0.00125**0.5)
    assert rows[0]['parameters'][0]['parameter_interval'] == {'lower': -0.1, 'upper': 1.2}
    assert rows[0]['parameter_ci_available']
    assert rows[1]['rmse'] is None
    assert not rows[1]['parameter_ci_available']
    assert rows[1]['reason'] == 'boundary_solution'
    assert summary['selected_in_fold'] == []
    assert summary['final_recommended_atomic']['status'] == 'insufficient_evidence'
    assert summary['final_recommended_ensemble']['status'] == 'insufficient_evidence'
    assert summary['cohorts'][0]['performance_uncertainty']['intervals'] is None
    text = (output / 'report.md').read_text(encoding='utf-8')
    assert '| Atomic PTF |' in text
    assert '| Sample | Family |' in text
    assert 'conditional' in text
    # Hash-matching headers cannot mask wrong curve values or a duplicated fit.
    for changed, reason in (
        ({**fits, 'dataset_file_sha256': '0' * 64}, 'exact evaluated dataset'),
        ({**fits, 'results': records + records[:1]}, 'exactly once'),
    ):
        fits_path.write_text(json.dumps(changed), encoding='utf-8')
        with pytest.raises(ValueError, match=reason):
            namespace['publish'](artifacts, review_path, tmp_path / 'rejected', fits_path=fits_path)
        assert not (tmp_path / 'rejected').exists()
    records[0]['fit']['observations'] = [dict(point) for point in observations]
    records[0]['fit']['observations'][0]['water_content'] = 0.9
    fits_path.write_text(json.dumps(fits), encoding='utf-8')
    with pytest.raises(ValueError, match='observations differ'):
        namespace['publish'](artifacts, review_path, tmp_path / 'rejected', fits_path=fits_path)
