import pytest

from ptfkit.tiwary2014 import calc_ptf_tiwary2014_bsr, calc_ptf_tiwary2014_igp


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'clay': 54.9,  # Clay 35.1-84.6 63.525
                'ph': 7.6,  # pH 6.3-9.1 8.215
                'cation_exchange_capacity': 61.6,  # CEC 27.5-71.7 48.9
                'esp': 7.3,  # ESP 0.3-44.1 4.866
                'emp': 21.4,  # EMP 11.0-71.0 28.7
                'excm': 3.32,  # Exchangeable Ca/Mg 0.3-11.1 2.507
            },
            (41.1729, 36.8273, 21.6976, 5.373367e-06),
        ),
        pytest.param(
            {
                'clay': 63.525,
                'ph': 8.215,
                'cation_exchange_capacity': 48.9,
                'esp': 4.866,
                'emp': 28.7,
                'excm': 2.507,
            },
            (37.723929, 33.051026, 17.879436, 2.632166e-06),
        ),  # mean k_sat for BSR = 2.627778e-06
    ],
)
def test_valid_bsr(
    inputs: dict[str, float],
    expected: tuple,
):
    res = calc_ptf_tiwary2014_bsr(**inputs)
    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 0.001


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'sand': 37.3,  # Sand 1.2-80.6 37.266
                'clay': 54.9,
                'cation_exchange_capacity': 48.9,
                'bulk_density': 1.674,  # BD 1.3-2.0 1.674
                'esp': 4.6,
                'emp': 28.7,
            },
            (35.4449, 30.9885, 17.8406, 5.103578e-07),
        ),
        pytest.param(
            {
                'sand': 27.1,
                'clay': 49.7,
                'cation_exchange_capacity': 63.5,
                'bulk_density': 1.464,
                'esp': 2.6,
                'emp': 23.2,
            },
            (38.2137, 34.6727, 21.6972, 5.377411e-07),
        ),  # mean k_sat for IGP = 4.777778e-07
    ],
)
def test_valid_igp(
    inputs: dict[str, float],
    expected: tuple,
):
    res = calc_ptf_tiwary2014_igp(**inputs)
    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 0.001
