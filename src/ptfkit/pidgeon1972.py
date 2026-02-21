r"""Pidgeon, 1972 - Uganda, ferrallitic soils (FC, PWP, AWC, EAWC).

Reference:
    PIDGEON, J. D. (1972). THE MEASUREMENT AND PREDICTION OF AVAILABLE WATER CAPACITY OF FERRALLITIC
    SOILS IN UGANDA. Journal of Soil Science, 23(4), 431-441.
    [DOI: 10.1111/j.1365-2389.1972.tb01674.x](https://doi.org/10.1111/j.1365-2389.1972.tb01674.x)


Territory

:   Uganda (non-alluvial ferrallitic soils with kaolinitic/illitic clay fraction)

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

from ptfkit._core import (
    calc_ptf_pidgeon1972_awc_ons_ufunc,
    calc_ptf_pidgeon1972_awc_usd_ufunc,
    calc_ptf_pidgeon1972_eawc_ufunc,
    calc_ptf_pidgeon1972_fc_ufunc,
    calc_ptf_pidgeon1972_pwp_ufunc,
)


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'calc_ptf_pidgeon1972_awc',
    'calc_ptf_pidgeon1972_eawc',
    'calc_ptf_pidgeon1972_fc',
    'calc_ptf_pidgeon1972_pwp',
]


@overload
def calc_ptf_pidgeon1972_fc(
    *,
    silt: float,
    clay: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_fc(
    *,
    silt: ArrayLike,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_fc(
    *,
    silt,
    clay,
    organic_matter,
    out=None,
):
    """Calculate field capacity for Ugandan ferrallitic soils.

    Equation (4). Uses particle-size method 2 (silt, clay) and organic matter.

    Args:
        silt: silt content (2-20 um) (%)
        clay: clay content (<2 um) (%)
        organic_matter: organic matter content (%)
        out: field capacity (w/w %) (FC)

    Returns:
        field capacity (w/w %)

    """
    return calc_ptf_pidgeon1972_fc_ufunc(silt, clay, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_pwp(
    *,
    silt: float,
    clay: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_pwp(
    *,
    silt: ArrayLike,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_pwp(
    *,
    silt,
    clay,
    organic_matter,
    out=None,
):
    """Calculate permanent wilting point for Ugandan ferrallitic soils.

    Equation (5). Uses particle-size method 2 (silt, clay) and organic matter.

    Args:
        silt: silt content (2-20 um) (%)
        clay: clay content (<2 um) (%)
        organic_matter: organic matter content (%)
        out: permanent wilting point (w/w %) (PWP)

    Returns:
        permanent wilting point (w/w %)

    """
    return calc_ptf_pidgeon1972_pwp_ufunc(silt, clay, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_awc(
    *,
    clay: float,
    organic_matter: float,
    method: Literal['ultrasonic_dispersion', 'overnight_shaking'],
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_awc(
    *,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    method: Literal['ultrasonic_dispersion', 'overnight_shaking'],
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_awc(
    *,
    clay,
    organic_matter,
    method,
    out=None,
):
    """Calculate available water capacity for Ugandan ferrallitic soils.

    Equation (6). Uses particle-size method 1 (ultrasonic dispersion) and organic matter.
    Equation (8). Uses particle-size method 2 (overnight shaking) and organic matter.

    Args:
        clay: clay content (<2 um) (%)
        organic_matter: organic matter content (%)
        method: particle-size method
        out: available water capacity (mm/m) (AWC)

    Returns:
        available water capacity (mm/m)

    """
    if method == 'ultrasonic_dispersion':
        return calc_ptf_pidgeon1972_awc_usd_ufunc(clay, organic_matter, out=out)

    if method == 'overnight_shaking':
        return calc_ptf_pidgeon1972_awc_ons_ufunc(clay, organic_matter, out=out)

    msg = 'method must be "ultrasonic_dispersion" or "overnight_shaking"'
    raise ValueError(msg)


@overload
def calc_ptf_pidgeon1972_eawc(
    *,
    silt: float,
    clay: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_eawc(
    *,
    silt: ArrayLike,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_eawc(
    *,
    silt,
    clay,
    organic_matter,
    out=None,
):
    """Calculate easily available water capacity for Ugandan ferrallitic soils.

    Equation (7). Uses particle-size method 2 (silt, clay) and organic matter.

    Args:
        silt: silt content (2-20 um) (%)
        clay: clay content (<2 um) (%)
        organic_matter: organic matter content (%)
        out: easily available water capacity (mm/m) (EAWC)

    Returns:
        easily available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_eawc_ufunc(silt, clay, organic_matter, out=out)
