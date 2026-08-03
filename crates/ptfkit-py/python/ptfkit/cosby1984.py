r"""Cosby et al., 1984 - USA, univariate hydraulic parameter statistics.

Reference:
    Cosby, B. J., Hornberger, G. M., Clapp, R. B., & Ginn, T. R. (1984).
    A statistical exploration of the relationships of soil moisture characteristics
    to the physical properties of soils. Water Resources Research, 20(6), 682-690.

$h(\theta)$ model

:   Power function moisture characteristic

$k(h)$ model

:   Saturated hydraulic conductivity parameter statistics

Territory

:   United States

Dataset

:   1448 soil samples from Holtan et al. (1968) and Rawls et al. (1976), as described
    by Cosby et al. (1984).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

import numpy as np

from ptfkit._rust import calc_ptf_cosby1984_univariate as _calc_ptf_cosby1984_univariate
from ptfkit._vectorize import vectorize_namedtuple_result


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = ['Cosby1984UnivariatePTFResult', 'calc_ptf_cosby1984_univariate']


T = TypeVar('T')


class Cosby1984UnivariatePTFResult(NamedTuple, Generic[T]):
    """The results of calculating the pilot PTF by Cosby et al., 1984.

    Attributes:
        mean_b: mean slope of the moisture characteristic (dimensionless)
        mean_log_psi_s: mean log saturation matric potential (reported log value)
        mean_log_k_sat: mean log saturated hydraulic conductivity (reported log value)
        mean_theta_s: mean saturated water content (% volume/volume)
        sd_b: standard deviation of b (dimensionless)
        sd_log_k_sat: standard deviation of log saturated hydraulic conductivity
        sd_theta_s: standard deviation of saturated water content (% volume/volume)

    """

    mean_b: T
    mean_log_psi_s: T
    mean_log_k_sat: T
    mean_theta_s: T
    sd_b: T
    sd_log_k_sat: T
    sd_theta_s: T


@overload
def calc_ptf_cosby1984_univariate(
    *,
    sand: float,
    silt: float,
    clay: float,
) -> Cosby1984UnivariatePTFResult[floating]: ...


@overload
def calc_ptf_cosby1984_univariate(
    *,
    sand: ArrayLike,
    silt: ArrayLike,
    clay: ArrayLike,
    out: Cosby1984UnivariatePTFResult[NDArray[floating]] | None = None,
) -> Cosby1984UnivariatePTFResult[NDArray[floating]]: ...


def _calc_scalar(
    sand: float,
    silt: float,
    clay: float,
) -> tuple[float, float, float, float, float, float, float]:
    return _calc_ptf_cosby1984_univariate(sand, silt, clay)


def calc_ptf_cosby1984_univariate(
    *,
    sand: float | ArrayLike,
    silt: float | ArrayLike,
    clay: float | ArrayLike,
    out: Cosby1984UnivariatePTFResult[NDArray[floating]] | None = None,
) -> Cosby1984UnivariatePTFResult[floating] | Cosby1984UnivariatePTFResult[NDArray[floating]]:
    """Estimate Cosby et al. (1984) univariate hydraulic parameter statistics.

    Args:
        sand: sand content (%)
        silt: silt content (%)
        clay: clay content (%)
        out: optional PTF result arrays

    Returns:
        PTF result fields in the order declared by `Cosby1984UnivariatePTFResult`.

    """
    return vectorize_namedtuple_result(
        _calc_scalar,
        _calc_array,
        Cosby1984UnivariatePTFResult,
        sand,
        silt,
        clay,
        out=out,
    )


def _calc_array(
    sand: NDArray[floating],
    silt: NDArray[floating],
    clay: NDArray[floating],
) -> tuple[NDArray[floating], ...]:
    sand_arr, silt_arr, clay_arr = np.broadcast_arrays(sand, silt, clay)
    return (
        2.91 + 0.159 * clay_arr,
        1.88 - 0.0131 * sand_arr,
        -0.884 + 0.0153 * sand_arr,
        48.9 - 0.126 * sand_arr,
        1.34 + 0.0500 * clay_arr,
        0.459 + 0.00321 * silt_arr,
        7.73 - 0.0730 * clay_arr,
    )
