r"""Puckett et al., 1985 - USA (WRC, $K_{sat}$).

Reference:
    Puckett, W. E., Dane, J. H., & Hajek, B. F. (1985). Physical and mineralogical data to determine
    soil hydraulic properties. Soil Science Society of America Journal, 49(4), 831-836.
    [DOI: 10.2136/sssaj1985.03615995004900040008x](https://sci-hub.ru/10.2136/sssaj1985.03615995004900040008x)

$h(\theta)$ model
:   full WRC

$k(h)$ model

:   $K_{sat}$

Territory

:   Lower Coastal Plain of Alabama, USA

Dataset

:   from Soil Conservation Service personnel
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import calc_ptf_puckett1985_ufunc


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'Puckett1985PTFResult',
    'calc_ptf_puckett1985',
]


T = TypeVar('T')


class Puckett1985PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Puckett et al., 1985.

    Attributes:
        theta_0: volumetric soil water content at 0 kPa (cm³/cm³)
        theta_1: volumetric soil water content at -1 kPa (cm³/cm³)
        theta_5: volumetric soil water content at -5 kPa (cm³/cm³)
        theta_10: volumetric soil water content at -10 kPa (cm³/cm³)
        theta_30: volumetric soil water content at -30 kPa (cm³/cm³)
        theta_60: volumetric soil water content at -60 kPa (cm³/cm³)
        theta_100: volumetric soil water content at -100 kPa (cm³/cm³)
        theta_500: volumetric soil water content at -500 kPa (cm³/cm³)
        theta_1000: volumetric soil water content at -1000 kPa (cm³/cm³)
        theta_1500: volumetric soil water content at -1500 kPa (cm³/cm³)
        k_sat: saturated hydraulic conductivity (m/s)

    """

    theta_0: T
    theta_1: T
    theta_5: T
    theta_10: T
    theta_30: T
    theta_60: T
    theta_100: T
    theta_500: T
    theta_1000: T
    theta_1500: T
    k_sat: T


@overload
def calc_ptf_puckett1985(
    *,
    sand: float,
    fine_sand: float,
    clay: float,
    bulk_density: float,
    porosity: float,
) -> Puckett1985PTFResult[floating]: ...


@overload
def calc_ptf_puckett1985(
    *,
    sand: ArrayLike,
    fine_sand: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    porosity: ArrayLike,
    out: Puckett1985PTFResult[NDArray[floating]] | None = None,
) -> Puckett1985PTFResult[NDArray[floating]]: ...


def calc_ptf_puckett1985(
    *,
    sand,
    fine_sand,
    clay,
    bulk_density,
    porosity,
    out=None,
):
    """Calculate PTF for soils of Lower Coastal Plain of Alabama, USA.

    Arguments:
        sand: sand content, 0.5-2 mm (%)
        fine_sand: fine sand content, 0.106-0.25 mm (%)
        clay: clay content, <0.002 mm (%)
        bulk_density: bulk density (g/cm^3)
        porosity: porosity (cm³/cm³)
        out: PTF results

    Returns:
        PTF results

    """
    out = tuple(out) if out else (None, None, None, None, None, None, None, None, None, None, None)

    res = calc_ptf_puckett1985_ufunc(sand, fine_sand, clay, bulk_density, porosity, out=out)

    return Puckett1985PTFResult(*res)
