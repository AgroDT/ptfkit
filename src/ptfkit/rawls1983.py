r"""Rawls et al., 1983 - USA (WRC).

Reference:
    Rawls, W. J., Brakensiek, D. L., & Soni, B. (1983).
    Agricultural management effects on soil water processes Part I:
    Soil water retention and Green and Ampt infiltration parameters. Transactions
    of the ASAE, 26(6), 1747-1752.

$h(\theta)$ model

:   full WRC

Territory

:   USA

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import calc_full_wrc_rawls1983_ufunc


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'Rawls1983PTFResult',
    'calc_full_wrc_rawls1983',
]


T = TypeVar('T')


class Rawls1983PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Rawls et al., 1983.

    Attributes:
        theta_20: volumetric soil water content at -200 cm (cm³/cm³)
        theta_33: volumetric soil water content at -330 cm (cm³/cm³)
        theta_60: volumetric soil water content at -600 cm (cm³/cm³)
        theta_100: volumetric soil water content at -1000 cm (cm³/cm³)
        theta_200: volumetric soil water content at -2000 cm (cm³/cm³)
        theta_400: volumetric soil water content at -4000 cm (cm³/cm³)
        theta_700: volumetric soil water content at -7000 cm (cm³/cm³)
        theta_1000: volumetric soil water content at -10000 cm (cm³/cm³)
        theta_1500: volumetric soil water content at -15000 cm (cm³/cm³)

    """

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
def calc_full_wrc_rawls1983(
    *,
    sand: float,
    clay: float,
    organic_matter: float,
    bulk_density: float,
) -> Rawls1983PTFResult[floating]: ...


@overload
def calc_full_wrc_rawls1983(
    *,
    sand: ArrayLike,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    bulk_density: ArrayLike,
    out: Rawls1983PTFResult[NDArray[floating]] | None = None,
) -> Rawls1983PTFResult[NDArray[floating]]: ...


def calc_full_wrc_rawls1983(
    *,
    sand,
    clay,
    organic_matter,
    bulk_density,
    out=None,
):
    """Calculate PTF for soils of USA.

    Arguments:
        sand: sand content, 0.5-2 mm (%)
        clay: clay content, <0.002 mm (%)
        organic_matter: organic matter content (%)
        bulk_density: bulk density (g/cm^3)
        out: PTF results

    Returns:
        PTF results

    """
    out = tuple(out) if out else (None, None, None, None, None, None, None, None, None)

    res = calc_full_wrc_rawls1983_ufunc(sand, clay, organic_matter, bulk_density, out=out)

    return Rawls1983PTFResult(*res)
