from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.li2007 import Li2007PTFResult, calc_ptf_li2007


GOLDEN = json.loads(Path('tests/golden/calc_ptf_li2007.json').read_text(encoding='utf-8'))
FIELDS = tuple(GOLDEN['units'].keys())[5:]


@pytest.mark.parametrize('case', GOLDEN['cases'], ids=[case['id'] for case in GOLDEN['cases']])
def test_calc_ptf_li2007_scalar(case: dict[str, object]):
    result = calc_ptf_li2007(**case['inputs'])

    assert isinstance(result, Li2007PTFResult)
    for field in FIELDS:
        assert getattr(result, field) == pytest.approx(
            case['expected'][field],
            rel=GOLDEN['rtol'],
            abs=GOLDEN['atol'],
        )


def test_calc_ptf_li2007_array():
    cases = GOLDEN['cases']
    result = calc_ptf_li2007(
        sand=np.array([case['inputs']['sand'] for case in cases]),
        silt=np.array([case['inputs']['silt'] for case in cases]),
        clay=np.array([case['inputs']['clay'] for case in cases]),
        soil_organic_matter=np.array([
            case['inputs']['soil_organic_matter'] for case in cases
        ]),
        bulk_density=np.array([case['inputs']['bulk_density'] for case in cases]),
    )

    for field in FIELDS:
        expected = np.array([case['expected'][field] for case in cases])
        npt.assert_allclose(
            getattr(result, field),
            expected,
            rtol=GOLDEN['rtol'],
            atol=GOLDEN['atol'],
        )


def test_calc_ptf_li2007_broadcasting():
    result = calc_ptf_li2007(
        sand=np.array([85.0, 50.23]),
        silt=np.array([10.0, 38.72]),
        clay=np.array([5.0, 11.05]),
        soil_organic_matter=0.65,
        bulk_density=np.array([1.20, 1.42]),
    )
    expected = [
        calc_ptf_li2007(
            sand=85.0,
            silt=10.0,
            clay=5.0,
            soil_organic_matter=0.65,
            bulk_density=1.20,
        ),
        calc_ptf_li2007(
            sand=50.23,
            silt=38.72,
            clay=11.05,
            soil_organic_matter=0.65,
            bulk_density=1.42,
        ),
    ]

    for field in FIELDS:
        npt.assert_allclose(
            getattr(result, field),
            np.array([getattr(item, field) for item in expected]),
            rtol=GOLDEN['rtol'],
            atol=GOLDEN['atol'],
        )


def test_calc_ptf_li2007_out():
    out = Li2007PTFResult(*(np.empty(2, dtype=float) for _ in FIELDS))
    result = calc_ptf_li2007(
        sand=np.array([85.0, 50.23]),
        silt=np.array([10.0, 38.72]),
        clay=np.array([5.0, 11.05]),
        soil_organic_matter=np.array([0.21, 0.65]),
        bulk_density=np.array([1.20, 1.42]),
        out=out,
    )

    assert result is not out
    for result_field, out_field in zip(result, out, strict=True):
        assert result_field is out_field

    npt.assert_allclose(
        result.theta_s,
        np.array([0.5256803583157499, 0.49659526127697506]),
        rtol=GOLDEN['rtol'],
        atol=GOLDEN['atol'],
    )
    npt.assert_allclose(
        result.k_sat,
        np.array([6.549110367333547e-06, 4.5117324656202257e-07]),
        rtol=GOLDEN['rtol'],
        atol=GOLDEN['atol'],
    )
