r"""Santra & Das, 2008 - India (WRC, $K_{sat}$).

Reference:
    Santra, P., & Das, B. S. (2008). Pedotransfer functions for soil hydraulic properties developed
    from a hilly watershed of Eastern India. Geoderma, 146(3-4), 439-448.
    [DOI: 10.1016/j.geoderma.2008.06.019](https://www.sciencedirect.com/science/article/pii/S001670610800178X)

$h(\theta)$ model

:   part of VG parameters

$k(h)$ model

:   $K_{sat}$

Territory

:   India

Dataset

:   BSI-HYD, SOTER-IGP, Chilika database (India), UNSODA

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import calc_ptf_santra2008_ufunc


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'Santra2008PTFResult',
    'calc_ptf_santra2008',
]


T = TypeVar('T')


class Santra2008PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Santra & Das, 2008.

    Attributes:
        a_vg: fitting parameter of the van Genuchten equation (α) (cm⁻¹)
        n_vg: fitting parameter of the van Genuchten equation (n)
        k_sat: saturated hydraulic conductivity (Ks) (m/s)

    """  # noqa: RUF002

    a_vg: T
    n_vg: T
    k_sat: T


@overload
def calc_ptf_santra2008(
    *,
    silt: float,
    clay: float,
    bulk_density: float,
    soil_organic_carbon: float,
    ph: float,
    altitude: float,
) -> Santra2008PTFResult[floating]: ...


@overload
def calc_ptf_santra2008(
    *,
    silt: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    soil_organic_carbon: ArrayLike,
    ph: ArrayLike,
    altitude: ArrayLike,
    out: Santra2008PTFResult[NDArray[floating]] | None = None,
) -> Santra2008PTFResult[NDArray[floating]]: ...


def calc_ptf_santra2008(
    *,
    silt,
    clay,
    bulk_density,
    soil_organic_carbon,
    ph,
    altitude,
    out=None,
):
    """Calculate PTF for soils of India.

    Arguments:
        silt: silt content, 0.002-0.05 mm (%)
        clay: clay content, <0.002 mm (%)
        bulk_density: bulk density (ρb) (g/cm^3)
        soil_organic_carbon: soil organic carbon content (OC) (%)
        ph: pH
        altitude: altitude above sea level (elevation) (m)
        out: PTF results

    Returns:
        PTF results

    """  # noqa: RUF002
    out = tuple(out) if out else (None, None, None)

    res = calc_ptf_santra2008_ufunc(
        silt, clay, bulk_density, soil_organic_carbon, ph, altitude, out=out
    )

    return Santra2008PTFResult(*res)
