from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.aimrun2009 import calc_ptf_aimrun2009


GOLDEN = json.loads(Path('tests/golden/calc_ptf_aimrun2009.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('case', GOLDEN['cases'], ids=[case['id'] for case in GOLDEN['cases']])
def test_calc_ptf_aimrun2009_scalar(case: dict[str, object]):
    result = calc_ptf_aimrun2009(**case['inputs'])

    assert result == pytest.approx(
        case['expected']['k_sat'],
        rel=GOLDEN['rtol'],
        abs=GOLDEN['atol'],
    )


def test_calc_ptf_aimrun2009_array():
    cases = GOLDEN['cases']
    result = calc_ptf_aimrun2009(
        clay=np.array([case['inputs']['clay'] for case in cases]),
        bulk_density=np.array([case['inputs']['bulk_density'] for case in cases]),
        organic_matter=np.array([case['inputs']['organic_matter'] for case in cases]),
        gmd=np.array([case['inputs']['gmd'] for case in cases]),
    )
    expected = np.array([case['expected']['k_sat'] for case in cases])

    npt.assert_allclose(result, expected, rtol=GOLDEN['rtol'], atol=GOLDEN['atol'])


def test_calc_ptf_aimrun2009_broadcasting():
    result = calc_ptf_aimrun2009(
        clay=np.array([43.88, 50.21]),
        bulk_density=np.array([0.94, 1.19]),
        organic_matter=8.55,
        gmd=np.array([0.010, 0.007]),
    )
    expected = np.array([
        calc_ptf_aimrun2009(
            clay=43.88,
            bulk_density=0.94,
            organic_matter=8.55,
            gmd=0.010,
        ),
        calc_ptf_aimrun2009(
            clay=50.21,
            bulk_density=1.19,
            organic_matter=8.55,
            gmd=0.007,
        ),
    ])

    npt.assert_allclose(result, expected, rtol=GOLDEN['rtol'], atol=GOLDEN['atol'])


def test_calc_ptf_aimrun2009_out():
    out = np.empty(2, dtype=float)
    result = calc_ptf_aimrun2009(
        clay=np.array([43.88, 50.21]),
        bulk_density=np.array([0.94, 1.19]),
        organic_matter=np.array([12.07, 8.55]),
        gmd=np.array([0.010, 0.007]),
        out=out,
    )

    assert result is out
    npt.assert_allclose(
        out,
        np.array([7.358406556179513e-08, 3.07872446717209e-08]),
        rtol=GOLDEN['rtol'],
        atol=GOLDEN['atol'],
    )
