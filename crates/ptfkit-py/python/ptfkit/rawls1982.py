r"""Rawls et al., 1982 - USA, RAWLS PTF (WRC).

Reference:
    Rawls, W. J., Brakensiek, D. L., & Saxton, K. E. (1982). Estimation of soil water properties.
    Transactions of the ASAE, 25(5), 1316-1320.
    [DOI: 10.13031/2013.33720](https://sci-hub.ru/10.13031/2013.33720)

$h(\theta)$ model

:   full WRC

Territory

:   USA

Dataset

:   RAWLS literature and data search for water retention and related soil information produced
    26 sources of data for 1,323 soils with about 5,350 horizons from 32 states.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import (
    calc_full_wrc_rawls1982_ufunc,
    calc_theta_33_rawls1982_ufunc,
    calc_theta_1500_rawls1982_ufunc,
)


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'Rawls1982PTFResult',
    'calc_full_wrc_rawls1982',
    'calc_theta_33_rawls1982',
    'calc_theta_1500_rawls1982',
]


T = TypeVar('T')


class Rawls1982PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Rawls et al., 1982.

    Attributes:
        theta_4: volumetric soil water content at -4 kPa (cm³/cm³)
        theta_7: volumetric soil water content at -7 kPa (cm³/cm³)
        theta_10: volumetric soil water content at -10 kPa (cm³/cm³)
        theta_20: volumetric soil water content at -20 kPa (cm³/cm³)
        theta_33: volumetric soil water content at -33 kPa (cm³/cm³)
        theta_60: volumetric soil water content at -60 kPa (cm³/cm³)
        theta_100: volumetric soil water content at -100 kPa (cm³/cm³)
        theta_200: volumetric soil water content at -200 kPa (cm³/cm³)
        theta_400: volumetric soil water content at -400 kPa (cm³/cm³)
        theta_700: volumetric soil water content at -700 kPa (cm³/cm³)
        theta_1000: volumetric soil water content at -1000 kPa (cm³/cm³)
        theta_1500: volumetric soil water content at -1500 kPa (cm³/cm³)

    """

    theta_4: T
    theta_7: T
    theta_10: T
    theta_20: T
    theta_33: T
    theta_60: T
    theta_100: T
    theta_200: T
    theta_400: T
    theta_700: T
    theta_1000: T
    theta_1500: T


@overload
def calc_theta_1500_rawls1982(
    *,
    clay: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_theta_1500_rawls1982(
    *,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_theta_1500_rawls1982(
    *,
    clay,
    organic_matter,
    out=None,
):
    """Calculate the value of theta_1500 for soils of USA.

    Use this function if the value of theta_1500 is not measured.

    Arguments:
        clay: clay content, <0.002 mm (%)
        organic_matter: organic matter content (%)
        out: volumetric soil water content at -1500 kPa (cm³/cm³)

    Returns:
        volumetric soil water content at -1500 kPa (cm³/cm³)

    """
    return calc_theta_1500_rawls1982_ufunc(clay, organic_matter, out=out)


@overload
def calc_theta_33_rawls1982(
    *, sand: float, organic_matter: float, theta_1500: float
) -> floating: ...


@overload
def calc_theta_33_rawls1982(
    *,
    sand: ArrayLike,
    organic_matter: ArrayLike,
    theta_1500: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_theta_33_rawls1982(
    *,
    sand,
    organic_matter,
    theta_1500,
    out=None,
):
    """Calculate the value of theta_33 for soils of USA.

    Use this function if the value of theta_33 is not measured.

    Arguments:
        sand: sand content, 0.5-2 mm (%)
        organic_matter: organic matter content (%)
        theta_1500: volumetric soil water content at -1500 kPa (cm³/cm³)
        out: volumetric soil water content at -33 kPa (cm³/cm³)

    Returns:
        volumetric soil water content at -33 kPa (cm³/cm³)

    """
    return calc_theta_33_rawls1982_ufunc(sand, organic_matter, theta_1500, out=out)


@overload
def calc_full_wrc_rawls1982(
    *,
    sand: float,
    organic_matter: float,
    bulk_density: float,
    theta_33: float,
    theta_1500: float,
) -> Rawls1982PTFResult[floating]: ...


@overload
def calc_full_wrc_rawls1982(
    *,
    sand: ArrayLike,
    organic_matter: ArrayLike,
    bulk_density: ArrayLike,
    theta_33: ArrayLike,
    theta_1500: ArrayLike,
    out: Rawls1982PTFResult[NDArray[floating]] | None = None,
) -> Rawls1982PTFResult[NDArray[floating]]: ...


def calc_full_wrc_rawls1982(
    *,
    sand,
    organic_matter,
    bulk_density,
    theta_33,
    theta_1500,
    out=None,
):
    """Calculate PTF for soils of USA.

    Arguments:
        sand: sand content, 0.5-2 mm (%)
        organic_matter: organic matter content (%)
        bulk_density: bulk density (g/cm^3)
        theta_33: volumetric soil water content at -33 kPa (cm³/cm³)
        theta_1500: volumetric soil water content at -1500 kPa (cm³/cm³)
        out: PTF results

    Returns:
        PTF results

    """
    out = (
        tuple(out)
        if out
        else (None, None, None, None, None, None, None, None, None, None, None, None)
    )

    res = calc_full_wrc_rawls1982_ufunc(
        sand, organic_matter, bulk_density, theta_33, theta_1500, out=out
    )

    return Rawls1982PTFResult(*res)
