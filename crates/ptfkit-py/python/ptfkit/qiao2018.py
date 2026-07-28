r"""Qiao et al., 2018 - China, Loess Plateau (WRC, $K_{sat}$).

Reference:
    Qiao, J., Zhu, Y., Jia, X., Huang, L., & Shao, M. A. (2018).
    Development of pedotransfer functions for soil hydraulic properties
    in the critical zone on the Loess Plateau, China. Hydrological
    Processes, 32(18), 2915-2921.
    [DOI: 10.1002/hyp.13216](https://doi.org/10.1002/hyp.13216)

$h(\theta)$ model

:   VG

$k(h)$ model

:   $K_{sat}$

Territory

:   Loess Plateau, China

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import calc_ptf_qiao2018_ufunc


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = ['Qiao2018PTFResult', 'calc_ptf_qiao2018']


T = TypeVar('T')


class Qiao2018PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Qiao et ai., 2018.

    Attributes:
        theta_s: the saturated soil water content (θs) (cm^3/cm^3)
        a_vg: a fitting parameter related to the inverse of the air entry pressure (α) (cm^-1)
        n_vg: a fitting parameter related to the soil pore distribution (n)
        k_sat: saturated hydraulic conductivity (Ks) (m/s)

    """  # noqa: RUF002

    theta_s: T
    a_vg: T
    n_vg: T
    k_sat: T


@overload
def calc_ptf_qiao2018(
    *,
    sand: float,
    clay: float,
    bulk_density: float,
    soil_organic_carbon: float,
) -> Qiao2018PTFResult[floating]: ...


@overload
def calc_ptf_qiao2018(
    *,
    sand: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    soil_organic_carbon: ArrayLike,
    out: Qiao2018PTFResult[NDArray[floating]] | None = None,
) -> Qiao2018PTFResult[NDArray[floating]]: ...


def calc_ptf_qiao2018(
    *,
    sand,
    clay,
    bulk_density,
    soil_organic_carbon,
    out=None,
) -> Qiao2018PTFResult:
    """Calculate PTF for soils of Loess Plateau, China.

    Args:
        sand: sand content
        clay: clay content
        bulk_density: bulk_density
        soil_organic_carbon: soil organic carbon content
        out: PTF results

    Returns:
        PTF results

    """

    out = tuple(out) if out else (None, None, None, None)

    res = calc_ptf_qiao2018_ufunc(sand, clay, bulk_density, soil_organic_carbon, out=out)

    return Qiao2018PTFResult(*res)
