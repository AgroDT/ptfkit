"""Aimrun & Amin, 2009 - Malaysia ($K_{sat}$).

Reference:
    Aimrun, W., Amin, M.S.M. Pedo-transfer function for saturated hydraulic conductivity of lowland
    paddy soils. Paddy Water Environ 7, 217-225 (2009).
    [DOI: 10.1007/s10333-009-0165-y](https://doi.org/10.1007/s10333-009-0165-y)

$k(h)$ model

:   $K_{sat}$

Territory

:   Tanjung Karang Rice Irrigation Project located on a flat coastal plain in the Integrated
    Agricultural Development Area (IADA Barat Laut Selangor), Malaysia
"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ptfkit._core import calc_ptf_aimrun2009_ufunc


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = ['calc_ptf_aimrun2009']


@overload
def calc_ptf_aimrun2009(
    *,
    clay: float,
    bulk_density: float,
    organic_matter: float,
    gmd: float,
) -> floating: ...


@overload
def calc_ptf_aimrun2009(
    *,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    organic_matter: ArrayLike,
    gmd: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_aimrun2009(
    *,
    clay,
    bulk_density,
    organic_matter,
    gmd,
    out=None,
):
    """Calculate PTF for clayey rice soils with compacted subsoil.

    Args:
        clay: clay content, <2 um (C) (%)
        bulk_density: dry bulk density (Db) (g/cm^3)
        organic_matter: organic matter content (OM) (%)
        gmd: geometric mean diameter of texture (mm)
        out: saturated hydraulic conductivity (ksat, Ks), (m/s)

    Returns:
        saturated hydraulic conductivity (ksat, Ks) (m/s)

    """
    return calc_ptf_aimrun2009_ufunc(clay, bulk_density, organic_matter, gmd, out=out)
