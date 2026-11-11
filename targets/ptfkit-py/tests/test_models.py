"""Independent hand-specified container protects the public loader contract."""

import hashlib
import json
import struct
import sys
import threading
from pathlib import Path

import numpy as np
import pytest

from ptfkit import _models
from ptfkit import zhang_schaap2017 as api
from ptfkit.models import Model, ModelFormatError, ModelInputError, ModelIntegrityError
from ptfkit.zhang_schaap2017 import Rosetta3, Rosetta3Statistics


SHA = '7b160f19c85818a5995d9154563a44a8edd8e63f44d961542a4ca5d3b3a0e5ec'


def affine_bytes() -> bytes:
    data = b'PTFKNN01' + struct.pack('<6I', 1, 2, 1, 2, 1, 0)
    for kind, params in [(0, (0.0, 0.0, 0.0)), (0, (0.0, 0.0, 0.0)), (5, (2.0, -1.0, 0.0))]:
        data += struct.pack('<I3d', kind, *params)
    return data + struct.pack('<2Q6d', 0, 6, 2.0, 1.0, 1.0, -1.0, 2.0, 0.0)


def test_owned_authenticated_model(tmp_path: Path):
    """Hand arithmetic: (2*3+4+1)*2-1=21; (-3+2*4)*2-1=9."""
    data = affine_bytes()
    assert hashlib.sha256(data).hexdigest() == SHA
    path = tmp_path / 'model.ptfm'
    path.write_bytes(data)
    model = Model.load(path, SHA)
    path.write_bytes(b'changed after loading')
    assert model.predict_network(0, [3, 4]) == [(21.0,), (9.0,)]
    assert model.sha256 == SHA
    assert model.network_count == 1
    assert model.network_shape(0) == (2, 1, 2)
    with pytest.raises(ModelIntegrityError):
        Rosetta3(model)
    with pytest.raises(ModelInputError):
        model.predict_network(1, [3, 4])
    with pytest.raises(ModelInputError):
        model.predict_network(0, [3])
    with pytest.raises(ModelInputError):
        model.predict_network(0, [float('nan'), 4])
    with pytest.raises(FileNotFoundError):
        Model.load(tmp_path / 'missing.ptfm', SHA)


def test_bad_digest_and_malformed_authenticated_container():
    data = affine_bytes()
    changed = data[:-1] + bytes([data[-1] ^ 1])
    with pytest.raises(ModelIntegrityError):
        Model.from_bytes(changed, SHA)
    for size in range(len(data)):
        prefix = data[:size]
        with pytest.raises(ModelFormatError):
            Model.from_bytes(prefix, hashlib.sha256(prefix).hexdigest())
    for offset in (0, 8, 12, 16, 20, 24, 28, 32, 116, 124):
        changed = bytearray(data)
        changed[offset] = 255
        with pytest.raises(ModelFormatError):
            Model.from_bytes(bytes(changed), hashlib.sha256(changed).hexdigest())
    changed = data[:132] + struct.pack('<d', float('nan')) + data[140:]
    with pytest.raises(ModelFormatError):
        Model.from_bytes(changed, hashlib.sha256(changed).hexdigest())
    with pytest.raises(ModelFormatError):
        Model.from_bytes(data, 'not a digest')


def test_bundled_rosetta_matches_upstream_without_a_model_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.chdir(tmp_path)
    result = Rosetta3().calc_ptf_zhang2017_mod2(sand=30, silt=30, clay=40)
    # Frozen upstream case mod2_arith_clay_loam, not a value from the ptfkit engine.
    assert result.mean == pytest.approx(
        [
            0.11921313412479762,
            0.4348486578079577,
            0.009109686083606867,
            1.3094213646469939,
            8.74047181417013,
            1.3099307799553759,
            -1.009187960743742,
        ],
        rel=1e-12,
        abs=1e-11,
    )
    assert result.stddev == pytest.approx(
        [
            0.009022699466985867,
            0.010140469075525323,
            0.0022509742698824248,
            0.0366504620061113,
            2.930411333703784,
            0.843530623042398,
            1.547848314232419,
        ],
        rel=1e-12,
        abs=1e-11,
    )


@pytest.fixture(scope='module')
def rosetta_model():
    return Rosetta3()


@pytest.mark.parametrize('level', [2, 3, 4, 5])
@pytest.mark.parametrize('mode', [0, 1, 2])
def test_named_rosetta_broadcasts_against_upstream(rosetta_model: Rosetta3, level: int, mode: int):
    reference = Path(__file__).resolve().parents[3] / 'specs/models/rosetta3/reference.json'
    cases = json.loads(reference.read_text(encoding='utf-8'))['cases']
    cases = [
        case
        for case in cases
        if case['level'] == level and case['mode'] == ('arith', 'log', 'geo')[mode]
    ]
    assert len(cases) == 10
    names = ('sand', 'silt', 'clay', 'bulk_density', 'theta_33', 'theta_1500')[: level + 1]
    method = getattr(rosetta_model, f'calc_ptf_zhang2017_mod{level}')
    for case in cases:
        inputs = dict(zip(names, case['inputs'], strict=True))
        scalar = method(**inputs, estimate=mode)
        assert scalar.mean + scalar.stddev == pytest.approx(
            case['mean'] + case['std'], rel=1e-12, abs=1e-11, nan_ok=True
        )
    # Two distinct upstream samples occupy rows; columns broadcast a scalar.
    batch = {
        name: np.array([case['inputs'][i] for case in cases[:2]][::-1])[::-1, None]
        for i, name in enumerate(names)
    }
    batch['clay'] = np.repeat(batch['clay'], 3, axis=1)
    out = Rosetta3Statistics(*(np.empty((3, 4))[::-1, ::-2].T for _ in range(14)))
    result = method(**batch, estimate=mode, out=out)
    expected = np.array([case['mean'] + case['std'] for case in cases[:2]])
    for i, (actual, target) in enumerate(zip(result.mean + result.stddev, out, strict=True)):
        assert actual is target
        np.testing.assert_allclose(
            actual, np.repeat(expected[:, i, None], 3, axis=1), rtol=1e-12, atol=1e-11
        )


def test_named_rosetta_rejects_invalid_samples_and_shapes(rosetta_model: Rosetta3):
    method = rosetta_model.calc_ptf_zhang2017_mod2
    with pytest.raises(ModelInputError):
        method(sand=[30, 30], silt=[30, float('nan')], clay=40)
    with pytest.raises(ValueError, match='shape mismatch'):
        method(sand=[30, 30], silt=[30, 30, 30], clay=40)
    with pytest.raises(ValueError, match='out must contain'):
        method(sand=30, silt=30, clay=40, out=(np.empty(2),))  # ty: ignore[invalid-argument-type]
    empty = method(sand=[], silt=30, clay=40)
    assert all(np.shape(field) == (0,) for field in empty.mean + empty.stddev)


def test_rosetta_native_batch_uses_named_outputs_without_full_result_allocation(
    rosetta_model: Rosetta3, monkeypatch: pytest.MonkeyPatch
):

    # The independent frozen upstream oracle is also checked by the scalar test above.
    expected = [
        0.11921313412479762,
        0.4348486578079577,
        0.009109686083606867,
        1.3094213646469939,
        8.74047181417013,
        1.3099307799553759,
        -1.009187960743742,
        0.009022699466985867,
        0.010140469075525323,
        0.0022509742698824248,
        0.0366504620061113,
        2.930411333703784,
        0.843530623042398,
        1.547848314232419,
    ]
    storage = np.empty((6, 14))
    out = Rosetta3Statistics(*(storage[::-2, i] for i in range(14)))

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail('batch inference allocated a full result or called the scalar bridge')

    monkeypatch.setattr(np, 'empty', forbidden)
    monkeypatch.setattr(_models, 'rosetta3', forbidden)
    result = rosetta_model.calc_ptf_zhang2017_mod2(sand=[30] * 3, silt=30, clay=40, out=out)
    monkeypatch.undo()
    assert isinstance(result, tuple)
    assert result._fields == out._fields
    for actual, target, value in zip(result, out, expected, strict=True):
        assert actual is target
        np.testing.assert_allclose(actual, value, rtol=1e-12, atol=1e-11)


def test_rosetta_batch_preserves_overlapping_predictors(rosetta_model: Rosetta3):
    sand = np.full(3, 30.0)
    out = Rosetta3Statistics(sand[::-1], *(np.empty(3) for _ in range(13)))
    result = rosetta_model.calc_ptf_zhang2017_mod2(sand=sand, silt=30, clay=40, out=out)
    np.testing.assert_allclose(result.theta_r_mean, 0.11921313412479762, rtol=1e-12, atol=1e-11)
    np.testing.assert_allclose(result.k_0_mean, 1.3099307799553759, rtol=1e-12, atol=1e-11)


def test_rosetta_rejects_unusable_output_buffers(rosetta_model: Rosetta3):
    method = rosetta_model.calc_ptf_zhang2017_mod2
    for out in [
        Rosetta3Statistics(*(np.empty(2, dtype=np.int64) for _ in range(14))),
        Rosetta3Statistics(*(np.broadcast_to(0.0, (2,)) for _ in range(14))),
    ]:
        with pytest.raises(ValueError, match='writable floating-point'):
            method(sand=[30, 30], silt=30, clay=40, out=out)  # ty: ignore[invalid-argument-type]
    shared = np.empty(2)
    with pytest.raises(ValueError, match='overlap'):
        method(
            sand=[30, 30], silt=30, clay=40, out=Rosetta3Statistics(*(shared for _ in range(14)))
        )


def test_rosetta_public_interface_is_method_only():
    assert not hasattr(Rosetta3, 'predict')
    for level in range(2, 6):
        assert not hasattr(api, f'calc_ptf_zhang2017_mod{level}')


def test_rosetta_converts_float32_output_buffers(rosetta_model: Rosetta3):
    out = Rosetta3Statistics(*(np.empty(2, dtype=np.float32) for _ in range(14)))
    result = rosetta_model.calc_ptf_zhang2017_mod2(sand=[30, 30], silt=30, clay=40, out=out)
    assert result is out
    np.testing.assert_allclose(result.theta_r_mean, 0.11921313412479762, rtol=1e-6)
    np.testing.assert_allclose(result.k_0_mean, 1.3099307799553759, rtol=1e-6)


def test_rosetta_native_batch_releases_the_gil(rosetta_model: Rosetta3):
    inputs = [np.full(512, value) for value in (30.0, 30.0, 40.0)]
    outputs = Rosetta3Statistics(*(np.empty(512) for _ in range(14)))
    parked, start, progressed = threading.Event(), threading.Event(), threading.Event()

    def worker() -> None:
        parked.set()
        start.wait()
        progressed.set()

    thread = threading.Thread(target=worker)
    thread.start()
    parked.wait()
    interval = sys.getswitchinterval()
    try:
        # Prevent periodic Python thread switches from satisfying the assertion.
        sys.setswitchinterval(60)
        start.set()
        assert not progressed.is_set()
        _models.rosetta3_batch(rosetta_model.model.native_handle, 2, 0, inputs, outputs)
        assert progressed.is_set()
    finally:
        sys.setswitchinterval(interval)
        start.set()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    ('level', 'inputs', 'valid'),
    [
        (2, [39, 40, 20], True),
        (2, [41, 40, 20], True),
        (2, [38.99, 40, 20], False),
        (2, [41.01, 40, 20], False),
        (3, [40, 40, 20, 0.5], True),
        (3, [40, 40, 20, 2.0], True),
        (3, [40, 40, 20, 2.01], False),
        (5, [40, 40, 20, 1.4, 0.3, 0.3], False),
        (4, [40, 40, 20, 1.4], False),
        *[(2, [value, 40, 20], False) for value in [float('nan'), float('inf'), -float('inf')]],
        (0, [40, 40, 20], False),
    ],
)
def test_generated_rosetta_validation_boundaries(
    rosetta_model: Rosetta3, level: int, inputs: list[float], *, valid: bool
):
    if valid:
        values = _models.rosetta3(rosetta_model.model.native_handle, level, 0, inputs)
        assert len(values) == 14
    else:
        with pytest.raises(ModelInputError):
            _models.rosetta3(rosetta_model.model.native_handle, level, 0, inputs)
