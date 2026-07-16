from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.jabro1992 import calc_ptf_jabro1992


GOLDEN = json.loads(Path('tests/golden/calc_ptf_jabro1992.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', GOLDEN['cases'], ids=[case['id'] for case in GOLDEN['cases']])
def test_calc_ptf_jabro1992_scalar(case: dict[str, object]):
    result = calc_ptf_jabro1992(**case['inputs'])

    assert result == pytest.approx(
        case['expected']['k_sat'],
        rel=GOLDEN['rtol'],
        abs=GOLDEN['atol'],
    )


def test_calc_ptf_jabro1992_array():
    cases = GOLDEN['cases']
    result = calc_ptf_jabro1992(
        silt=np.array([case['inputs']['silt'] for case in cases]),
        clay=np.array([case['inputs']['clay'] for case in cases]),
        bulk_density=np.array([case['inputs']['bulk_density'] for case in cases]),
    )
    expected = np.array([case['expected']['k_sat'] for case in cases])

    npt.assert_allclose(result, expected, rtol=GOLDEN['rtol'], atol=GOLDEN['atol'])


def test_calc_ptf_jabro1992_broadcasting():
    result = calc_ptf_jabro1992(
        silt=np.array([10.0, 38.72]),
        clay=np.array([5.0, 11.05]),
        bulk_density=1.42,
    )
    expected = np.array([
        calc_ptf_jabro1992(silt=10.0, clay=5.0, bulk_density=1.42),
        calc_ptf_jabro1992(silt=38.72, clay=11.05, bulk_density=1.42),
    ])

    npt.assert_allclose(result, expected, rtol=GOLDEN['rtol'], atol=GOLDEN['atol'])


def test_calc_ptf_jabro1992_out():
    out = np.empty(2, dtype=float)
    result = calc_ptf_jabro1992(
        silt=np.array([10.0, 38.72]),
        clay=np.array([5.0, 11.05]),
        bulk_density=np.array([1.26, 1.42]),
        out=out,
    )

    assert result is out
    npt.assert_allclose(
        out,
        np.array([0.0003849640675896946, 9.804037952717678e-06]),
        rtol=GOLDEN['rtol'],
        atol=GOLDEN['atol'],
    )
