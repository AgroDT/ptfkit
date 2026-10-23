import math
from decimal import Decimal, localcontext

import pytest

from ptfkit_eval import (
    ModelEvaluationError,
    RetentionFamilyError,
    evaluate_clapp1978_h_theta,
    evaluate_retention_family,
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


def clapp_decimal_oracle(b: float, scale: float, suction: float) -> float:
    with localcontext() as context:
        context.prec = 450
        shape, q = Decimal(b), Decimal(suction) / Decimal(scale)
        wetness_i = Decimal(23) / 25
        head_i = wetness_i ** (-shape)
        if q >= head_i:
            wetness = q ** (-1 / shape)
        else:
            gap = 1 - wetness_i
            a = head_i / gap**2 - head_i * shape / (wetness_i * gap)
            n = 2 * wetness_i - head_i * shape / (a * wetness_i) - 1
            discriminant = (n + 1) ** 2 - 4 * (n + q / a)
            wetness = (n + 1 + discriminant.sqrt()) / 2
        return float(Decimal('0.4') * wetness)


@pytest.mark.parametrize(
    ('shape', 'scale', 'suction'),
    [
        (4, 1e308, 1e307),
        (4, 1e-308, 1e308),
        (4, 1e-308, 5e-309),
        (4, 1, 0.5),
        (4, 1e308, 5e307),
        (math.nextafter(11.5, 0), 1, 0.5),
        (math.nextafter(11.5, 0), 1e308, 1e308),
        (1e-320, 1, 1),
    ],
)
def test_clapp_preserves_the_published_curve_across_pressure_scales_and_shape_limits(
    shape: float,
    scale: float,
    suction: float,
):
    parameters = {'b': shape, 'saturation_suction': scale, 'saturated_water_content': 0.4}
    expected = clapp_decimal_oracle(shape, scale, suction)
    actual = evaluate_clapp1978_h_theta(parameters, suction)
    assert math.isfinite(actual)
    # abs=0 prevents a dry-branch zero from passing for a tiny but representable result.
    assert actual == pytest.approx(expected, rel=2e-13, abs=0)


@pytest.mark.parametrize('shape', [11.5, 12, 100])
@pytest.mark.parametrize('suction', [0, 100])
def test_clapp_rejects_a_globally_undefined_gradual_air_entry_branch_at_every_pressure(
    shape: float,
    suction: float,
):
    with pytest.raises(ModelEvaluationError, match=r'b < 11\.5'):
        evaluate_clapp1978_h_theta({**SAND_PARAMETERS, 'b': shape}, suction)


@pytest.mark.parametrize(('alpha', 'suction'), [(1e308, 1e308), (1e-308, 1e-308), (1e-308, 1e308)])
def test_vereecken_does_not_saturate_before_applying_a_small_positive_exponent(
    alpha: float,
    suction: float,
):
    parameters = {**VEREECKEN_PARAMETERS, 'alpha': alpha, 'n': 0.001}
    with localcontext() as context:
        context.prec = 100
        power = (Decimal(alpha) * Decimal(suction)) ** Decimal(parameters['n'])
        expected = float(Decimal('0.1') + Decimal('0.4') / (1 + power))
    actual = evaluate_vereecken1989_h_theta(parameters, suction)
    assert 0.1 < expected < 0.5
    assert actual == pytest.approx(expected, rel=1e-14, abs=1e-15)


@pytest.mark.parametrize(('scale', 'suction'), [(1e308, 1e307), (1e-308, 1e308)])
def test_canonical_clapp_family_preserves_pressure_ratio_without_overflowing_unit_conversion(
    scale: float,
    suction: float,
):
    values = evaluate_retention_family(
        'clapp1978_gradual_air_entry_v1',
        {'theta_s': 0.4, 'saturation_suction': scale, 'b': 4},
        [suction],
    )
    assert values[0] == pytest.approx(clapp_decimal_oracle(4, scale, suction), rel=2e-13, abs=0)


@pytest.mark.parametrize(
    'parameters',
    [
        {'theta_s': 0.4, 'saturation_suction': 1, 'b': 11.5},
        {'theta_s': 0.4, 'saturation_suction': 0, 'b': 4},
        {'theta_s': 1, 'saturation_suction': 1, 'b': 4},
    ],
)
@pytest.mark.parametrize('pressures', [[], [100]])
def test_canonical_clapp_rejects_invalid_global_shape_even_on_empty_or_dry_grid(
    pressures: list[float],
    parameters: dict[str, float],
):
    with pytest.raises(RetentionFamilyError, match='Clapp gradual air entry'):
        evaluate_retention_family(
            'clapp1978_gradual_air_entry_v1',
            parameters,
            pressures,
        )


@pytest.mark.parametrize(('alpha', 'suction'), [(3, 1 / 3), (10, 0.1), (1e308, 1e-308)])
def test_reduced_van_genuchten_preserves_exact_product_residual_before_large_exponent(
    alpha: float,
    suction: float,
):
    shape = 1e16
    with localcontext() as context:
        context.prec = 100
        power = (Decimal(alpha) * Decimal(suction)) ** Decimal(shape)
        expected = float(Decimal('0.1') + Decimal('0.4') / (1 + power))
    parameters = {**VEREECKEN_PARAMETERS, 'alpha': alpha, 'n': shape}
    scalar = evaluate_vereecken1989_h_theta(parameters, suction)
    vector = evaluate_retention_family('van_genuchten_m1_v1', parameters, [suction])
    assert abs(expected - 0.3) > 0.01
    assert scalar == pytest.approx(expected, rel=1e-14)
    assert vector[0] == pytest.approx(expected, rel=1e-14)


@pytest.mark.filterwarnings('error::RuntimeWarning')
@pytest.mark.parametrize('family', ['van_genuchten_m1_v1', 'van_genuchten_mualem_v1'])
@pytest.mark.parametrize(
    ('alpha', 'suction', 'expected'), [(1e308, 1e308, 0.1), (1e-308, 1e-308, 0.5)]
)
def test_vector_van_genuchten_extreme_powers_return_defined_limits_without_range_warnings(
    family: str,
    alpha: float,
    suction: float,
    expected: float,
):
    parameters = {**VEREECKEN_PARAMETERS, 'alpha': alpha, 'n': 1e308}
    value = evaluate_retention_family(family, parameters, [suction])[0]
    assert value == expected
    assert evaluate_vereecken1989_h_theta(parameters, suction) == expected
