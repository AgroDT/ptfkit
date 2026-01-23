import pytest

from ptfkit.aimrun2009 import calc_ptf_aimrun2009


@pytest.mark.parametrize(
    ('clay', 'bd', 'om', 'gmd', 'expected'),
    [
        pytest.param(43.88, 0.94, 12.07, 0.010, 7.358407e-08, id='mean topsoil layer'),
        pytest.param(50.21, 1.19, 8.55, 0.007, 3.078724e-08, id='mean hardpan layer'),
        pytest.param(58.81, 1.13, 5.12, 0.005, 2.334305e-08, id='mean subsoil layer'),
        pytest.param(47.50, 1.08, 1.43, 0.008, 3.831169e-08, id='min organic matter'),
    ],
)
def test_calc_ptf_aimrun2009(clay: float, bd: float, om: float, gmd: float, expected: float):
    res = calc_ptf_aimrun2009(clay=clay, bulk_density=bd, organic_matter=om, gmd=gmd)
    assert abs(res - expected) < 1e-10
