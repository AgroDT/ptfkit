r"""Tiwary et al., 2014 - India, Indo-Gangetic Plains (IGP).

and Black Soil Region (BSR) (-33, -100, -1500 kPa, $K_{sat}$).
Reference:
    Tiwary, P., Patil, N. G., Bhattacharyya, T., Chandran,
    P., Ray, S. K., Karthikeyan, K., & Thakre, S. (2014).
    Pedotransfer functions: a tool for estimating hydraulic properties
    of two major soil types of India. Current Science, 107, 1431-1439.
    [DOI: 10.1080/00103624.2015.1089265](https://doi.org/10.1080/00103624.2015.1089265)


$h(\theta)$ model

:   -33, -100, -1500 kPa

$k(h)$ model

:   $K_{sat}$

Territory

:   Indo-Gangetic Plains (IGP) and Black Soil Region (BSR), India

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import (
    calc_ptf_tiwary2014_bsr_ufunc,
    calc_ptf_tiwary2014_igp_ufunc,
)


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'Tiwary2014PTFResult',
    'calc_ptf_tiwary2014_bsr',
    'calc_ptf_tiwary2014_igp',
]


T = TypeVar('T')


class Tiwary2014PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Tiwary et al., 2014.

    Arguments:
        w_33: gravimetric soil water content at -33 kPa (MC33) (%)
        w_100: gravimetric soil water content at -100 kPa (MC100) (%)
        w_1500: gravimetric soil water content at -1500 kPa (MC1500) (%)
        k_sat: saturated hydraulic conductivity (sHC) (m/s)

    """

    w_33: T
    w_100: T
    w_1500: T
    k_sat: T


@overload
def calc_ptf_tiwary2014_igp(
    *,
    sand: float,
    clay: float,
    bulk_density: float,
    cation_exchange_capacity: float,
    esp: float,
    emp: float,
) -> Tiwary2014PTFResult[floating]: ...


@overload
def calc_ptf_tiwary2014_igp(
    *,
    sand: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    cation_exchange_capacity: ArrayLike,
    esp: ArrayLike,
    emp: ArrayLike,
    out: Tiwary2014PTFResult[NDArray[floating]] | None = None,
) -> Tiwary2014PTFResult[NDArray[floating]]: ...


def calc_ptf_tiwary2014_igp(
    *,
    sand,
    clay,
    bulk_density,
    cation_exchange_capacity,
    esp,
    emp,
    out=None,
) -> Tiwary2014PTFResult:
    """PTF for soil of Indo-Gangetic Plains (IGP), India.

    Arguments:
        sand: sand content, 0.5-2 mm (%)
        clay: clay content, <0.002 mm (%)
        bulk_density: bulk density (BD) (g/cm^3)
        cation_exchange_capacity: cation exchange capacity (CEC) (meq/100g soil)
        esp: exchangeable sodium percentage (%)
        emp: exchangeable magnesium percentage (%)
        out: PTF results

    Returns:
        PTF results

    """

    out = tuple(out) if out else (None, None, None, None)

    res = calc_ptf_tiwary2014_igp_ufunc(
        sand, clay, bulk_density, cation_exchange_capacity, esp, emp, out=out
    )

    return Tiwary2014PTFResult(*res)


@overload
def calc_ptf_tiwary2014_bsr(
    *,
    clay: float,
    ph: float,
    cation_exchange_capacity: float,
    esp: float,
    emp: float,
    excm: float,
) -> Tiwary2014PTFResult[floating]: ...


@overload
def calc_ptf_tiwary2014_bsr(
    *,
    clay: ArrayLike,
    ph: ArrayLike,
    cation_exchange_capacity: ArrayLike,
    esp: ArrayLike,
    emp: ArrayLike,
    excm: ArrayLike,
    out: Tiwary2014PTFResult[NDArray[floating]] | None = None,
) -> Tiwary2014PTFResult[NDArray[floating]]: ...


def calc_ptf_tiwary2014_bsr(
    *, clay, ph, cation_exchange_capacity, esp, emp, excm, out=None
) -> Tiwary2014PTFResult:
    """PTF for soils of the black soil region (BSR), India.

    Arguments:
        clay: clay content, <0.002 mm (%)
        ph: pH
        cation_exchange_capacity: cation exchange capacity (CEC) (meq/100g soil)
        esp: exchangeable sodium percentage (%)
        emp: exchangeable magnesium percentage (%)
        excm: exchangeable Ca/Mg ratio (exchangeable Ca/Mg)
        out: PTF results

    Returns:
        PTF results

    """

    out = tuple(out) if out else (None, None, None, None)

    res = calc_ptf_tiwary2014_bsr_ufunc(clay, ph, cation_exchange_capacity, esp, emp, excm, out=out)

    return Tiwary2014PTFResult(*res)
