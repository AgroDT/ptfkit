from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.cosby1984 import Cosby1984UnivariatePTFResult, calc_ptf_cosby1984_univariate


GOLDEN = json.loads(
    Path('tests/golden/calc_ptf_cosby1984_univariate.json').read_text(encoding='utf-8')
)
FIELDS = tuple(GOLDEN['units'].keys())[3:]


@pytest.mark.parametrize('case', GOLDEN['cases'], ids=[case['id'] for case in GOLDEN['cases']])
def test_calc_ptf_cosby1984_univariate_scalar(case: dict[str, object]):
    result = calc_ptf_cosby1984_univariate(**case['inputs'])

    assert isinstance(result, Cosby1984UnivariatePTFResult)
    for field in FIELDS:
        assert getattr(result, field) == pytest.approx(
            case['expected'][field],
            rel=GOLDEN['rtol'],
            abs=GOLDEN['atol'],
        )


def test_calc_ptf_cosby1984_univariate_array():
    cases = GOLDEN['cases']

    result = calc_ptf_cosby1984_univariate(
        sand=np.array([case['inputs']['sand'] for case in cases]),
        silt=np.array([case['inputs']['silt'] for case in cases]),
        clay=np.array([case['inputs']['clay'] for case in cases]),
    )

    for field in FIELDS:
        expected = np.array([case['expected'][field] for case in cases])
        npt.assert_allclose(
            getattr(result, field),
            expected,
            rtol=GOLDEN['rtol'],
            atol=GOLDEN['atol'],
        )


def test_calc_ptf_cosby1984_univariate_broadcasting():
    result = calc_ptf_cosby1984_univariate(
        sand=np.array([50.0, 80.0]),
        silt=30.0,
        clay=np.array([20.0, 5.0]),
    )

    npt.assert_allclose(result.mean_b, np.array([6.09, 3.705]), rtol=GOLDEN['rtol'])
    npt.assert_allclose(result.sd_log_k_sat, np.array([0.5553, 0.5553]), rtol=GOLDEN['rtol'])


def test_calc_ptf_cosby1984_univariate_out():
    out = Cosby1984UnivariatePTFResult(*(np.empty(2, dtype=float) for _ in FIELDS))
    result = calc_ptf_cosby1984_univariate(
        sand=np.array([50.0, 80.0]),
        silt=np.array([30.0, 15.0]),
        clay=np.array([20.0, 5.0]),
        out=out,
    )

    assert result is not out
    for result_field, out_field in zip(result, out, strict=True):
        assert result_field is out_field

    npt.assert_allclose(result.mean_theta_s, np.array([42.6, 38.82]), rtol=GOLDEN['rtol'])
    npt.assert_allclose(result.sd_theta_s, np.array([6.27, 7.365]), rtol=GOLDEN['rtol'])
