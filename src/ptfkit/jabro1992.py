"""Jabro, 1992 - USA ($K_{sat}$).

Reference:
    Jabro, J. D. (1992). Estimation of saturated hydraulic conductivity of soils from particle size
    distribution and bulk density data. Transactions of the ASAE, 35(2), 557-560.
    [DOI: 10.13031/2013.28633](https://sci-hub.ru/10.13031/2013.28633)

$k(h)$ model

:   $K_{sat}$

Territory

:   USA

Dataset

:   Southern Cooperation Series Bulletins (Dan et al., 1983; Nofziger et al.,
    1983; Quisenberry et al., 1987), 350 samples
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ptfkit._core import calc_ptf_jabro1992_ufunc


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'calc_ptf_jabro1992',
]


@overload
def calc_ptf_jabro1992(
    *,
    silt: float,
    clay: float,
    bulk_density: float,
) -> floating: ...


@overload
def calc_ptf_jabro1992(
    *,
    silt: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_jabro1992(
    *,
    silt,
    clay,
    bulk_density,
    out=None,
):
    """Calculate PTF for soils of USA.

    Arguments:
        silt: silt content, 0.002-0.05 mm (%)
        clay: clay content, <0.002 mm (%)
        bulk_density: bulk density (Bd) (g/cm^3)
        out: saturated hydraulic conductivity (m/s)

    Returns:
        saturated hydraulic conductivity (m/s)

    """
    return calc_ptf_jabro1992_ufunc(silt, clay, bulk_density, out=out)
