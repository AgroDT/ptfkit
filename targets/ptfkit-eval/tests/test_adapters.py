import pytest

from ptfkit_eval import (
    ModelEvaluationError,
    evaluate_clapp1978_h_theta,
    evaluate_vereecken1989_h_theta,
)


SAND_PARAMETERS = {
    'b': 4.05,
    'saturation_suction': 3.50,
    'saturated_water_content': 0.395,
}


def test_clapp1978_curve_passes_through_saturation_and_the_inflection_point():
    inflection_suction = 3.50 * 0.92**-4.05

    assert evaluate_clapp1978_h_theta(SAND_PARAMETERS, 0.0) == pytest.approx(0.395)
    assert evaluate_clapp1978_h_theta(SAND_PARAMETERS, inflection_suction) == pytest.approx(
        0.395 * 0.92
    )


def test_clapp1978_dry_branch_inverts_the_published_power_curve():
    suction_at_half_wetness = 3.50 * 2.0**4.05

    assert evaluate_clapp1978_h_theta(SAND_PARAMETERS, suction_at_half_wetness) == pytest.approx(
        0.395 * 0.5
    )


def test_clapp1978_gradual_air_entry_is_not_a_clipped_power_curve():
    assert evaluate_clapp1978_h_theta(SAND_PARAMETERS, 3.50) == pytest.approx(0.377515843614512)


@pytest.mark.parametrize(
    ('parameters', 'suction', 'message'),
    [
        ({**SAND_PARAMETERS, 'b': 0.0}, 10.0, 'b must be positive'),
        ({**SAND_PARAMETERS, 'saturated_water_content': 1.0}, 10.0, 'between zero and one'),
        (SAND_PARAMETERS, -1.0, 'nonnegative magnitude'),
    ],
)
def test_clapp1978_rejects_values_outside_its_computational_domain(
    parameters: dict[str, float], suction: float, message: str
):
    with pytest.raises(ModelEvaluationError, match=message):
        evaluate_clapp1978_h_theta(parameters, suction)


VEREECKEN_PARAMETERS = {
    'theta_r': 0.1,
    'theta_s': 0.5,
    'alpha': 0.01,
    'n': 2.0,
}


def test_vereecken1989_uses_the_published_reduced_van_genuchten_model():
    assert evaluate_vereecken1989_h_theta(VEREECKEN_PARAMETERS, 0.0) == pytest.approx(0.5)
    assert evaluate_vereecken1989_h_theta(VEREECKEN_PARAMETERS, 100.0) == pytest.approx(0.3)


@pytest.mark.parametrize(
    ('parameters', 'suction', 'message'),
    [
        ({**VEREECKEN_PARAMETERS, 'theta_r': 0.5}, 10.0, 'theta_r < theta_s'),
        ({**VEREECKEN_PARAMETERS, 'alpha': 0.0}, 10.0, 'alpha must be positive'),
        ({**VEREECKEN_PARAMETERS, 'n': 0.0}, 10.0, 'n must be positive'),
        (VEREECKEN_PARAMETERS, -1.0, 'nonnegative magnitude'),
    ],
)
def test_vereecken1989_rejects_values_outside_its_computational_domain(
    parameters: dict[str, float], suction: float, message: str
):
    with pytest.raises(ModelEvaluationError, match=message):
        evaluate_vereecken1989_h_theta(parameters, suction)
