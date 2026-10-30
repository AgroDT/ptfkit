"""Independent hand-specified container protects the public loader contract."""

import hashlib
import struct
from pathlib import Path

import pytest

from ptfkit.models import Model, ModelFormatError, ModelInputError, ModelIntegrityError
from ptfkit.zhang_schaap2017 import Rosetta3


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
    result = Rosetta3().predict(2, [30, 30, 40])
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
