"""Protect source identity and unchanged-target contracts of the HYBRAS overlay."""

import copy
import hashlib
import runpy
from collections.abc import Callable
from pathlib import Path

import pytest

from ptfkit_eval.documents import canonical_json


def _overlay() -> Callable[[dict, dict], tuple[dict, dict]]:
    return runpy.run_path(
        str(Path(__file__).resolve().parents[3] / 'evaluation/experiments/hybras/run_clapp.py')
    )['overlay']


def _fixture() -> tuple[dict, dict]:
    source = 'hybras-study-' + hashlib.sha256(canonical_json(['study', None])).hexdigest()[:16]
    rows = {}
    samples = []
    observations = []
    for code, horizon, texture in (
        (1, 'Bt1', 'franco argilo-siltoso'),
        (2, 'O', 'argila'),
        (3, 'A', 'silte'),
        (4, 'AB', 'areia'),
        (5, None, 'areia'),
        (6, 'E', 'areia franca'),
    ):
        row = [None] * 38
        row[0], row[5], row[7], row[11], row[36] = code, 9, horizon, texture, 'study'
        rows[code] = (code + 3, tuple(row))
        sample = {
            'source_id': source,
            'sample_id': f'hybras-horizon-{code}',
            'profile_id': 'hybras-profile-9',
            'features': [],
        }
        samples.append(sample)
        observations.append(
            {
                **{k: sample[k] for k in ('source_id', 'sample_id')},
                'id': f'point-{code}',
                'suction_kpa': 33.0484105,
                'value': 0.17 + code / 100,
                'source_cells': [f'RAWRET_lines!A{code}:H{code}'],
            }
        )
    document = {
        'samples': samples,
        'observations': observations,
        'target': {'material_basis': 'unspecified', 'unit': 'volume_fraction'},
    }
    return document, rows


def test_overlay_uses_reported_classes_excludes_unreviewed_horizons_and_preserves_points():
    document, rows = _fixture()
    before = copy.deepcopy(document)
    subset, review = _overlay()(document, rows)
    assert document == before
    assert [s['sample_id'] for s in subset['samples']] == ['hybras-horizon-1', 'hybras-horizon-6']
    assert [s['features'][0]['value'] for s in subset['samples']] == [
        'silty clay loam',
        'loamy sand',
    ]
    assert subset['samples'][0]['features'][0]['source_cells'] == ['HYBRAS!L4']
    assert subset['samples'][0]['features'][0]['origin'] == 'measured'
    assert subset['observations'] == [before['observations'][0], before['observations'][5]]
    assert subset['target']['material_basis'] == 'mineral_soil'
    assert review['profiles'] == 1
    assert review['exclusions'] == {
        'horizon_not_in_reviewed_single_master_subset': 3,
        'unreviewed_texture_label': 1,
    }


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('profile_id', 'hybras-profile-10'),
        ('source_id', 'another-study'),
    ],
)
def test_overlay_rejects_source_or_profile_mismatch(field: str, value: str):
    document, rows = _fixture()
    document['samples'][0][field] = value
    with pytest.raises(ValueError, match='identity does not match'):
        _overlay()(document, rows)


def test_independent_verifier_inverts_the_gradual_air_entry_parabola():
    root = Path(__file__).resolve().parents[3]
    namespace = runpy.run_path(str(root / 'evaluation/experiments/hybras/summarize_clapp.py'))
    water = namespace['published_water']
    # Source equations 1/3, Table 2 sand: W=.96 gives this head by 50-digit
    # decimal evaluation of the quadratic's midpoint value and endpoint slope.
    assert water('sand', 3.247557198080535328) == pytest.approx(0.3792, abs=2e-15)
    assert water('sand', 0) == pytest.approx(0.395, abs=2e-15)
    assert water('sand', 3.5 * 2**4.05) == pytest.approx(0.1975, abs=2e-15)
