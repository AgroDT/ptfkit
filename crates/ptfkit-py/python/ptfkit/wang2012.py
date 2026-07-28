r"""Wang et al., 2012 - China, Loess Plateau ($K_{sat}$, FC (-33 kPa), SSWC (Qs)).

Reference:
    Wang, Y., Shao, M. A., & Liu, Z. (2012). Pedotransfer functions for predicting soil hydraulic
    properties of the Chinese Loess Plateau. Soil Science, 177(7), 424-432.
    [DOI: 10.1097/ss.0b013e318255a449](https://doi.org/10.1097/ss.0b013e318255a449)

$h(\theta)$ model

:   FC (-33 kPa), SSWC (Qs)

$k(h)$ model

:   $K_{sat}$

Territory

:   Loess Plateau, China
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import (
    calc_ptf_wang2012_ufunc,
)


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'Wang2012PTFResult',
    'calc_ptf_wang2012',
]


T = TypeVar('T')


class Wang2012PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Wang et al., 2012.

    Attributes:
        theta_s: saturated soil-water content (SSWC) (cm^3/cm^3)
        theta_fc: soil-water content at field capacity (FC) (cm^3/cm^3)
        k_sat: saturated hydraulic conductivity (Ks) (m/s)

    """

    theta_s: T
    theta_fc: T
    k_sat: T


@overload
def calc_ptf_wang2012(
    *,
    sand: float,
    silt: float,
    clay: float,
    bulk_density: float,
    soil_organic_carbon: float,
    altitude: float,
) -> Wang2012PTFResult[floating]: ...


@overload
def calc_ptf_wang2012(
    *,
    sand: ArrayLike,
    silt: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    soil_organic_carbon: ArrayLike,
    altitude: ArrayLike,
    out: Wang2012PTFResult[NDArray[floating]] | None = None,
) -> Wang2012PTFResult[NDArray[floating]]: ...


def calc_ptf_wang2012(
    *, sand, silt, clay, bulk_density, soil_organic_carbon, altitude, out=None
) -> Wang2012PTFResult:
    """Calculate PTF for soils of Loess Plateau, China.

    Args:
        sand: sand content, 0.5-1 mm (%)
        silt: silt content, 0.002-0.05 mm (%)
        clay: clay content, <0.002 mm (%)
        bulk_density: bulk density (BD) (g/cm^3)
        soil_organic_carbon: soil organic carbon content (SOC) (%)
        altitude: altitude above sea level (m)
        out: PTF results

    Returns:
        PTF results

    """

    out = tuple(out) if out else (None, None, None)

    res = calc_ptf_wang2012_ufunc(
        sand, silt, clay, bulk_density, soil_organic_carbon, altitude, out=out
    )

    return Wang2012PTFResult(*res)
