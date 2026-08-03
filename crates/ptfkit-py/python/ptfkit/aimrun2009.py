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

import numpy as np

from ptfkit._rust import calc_ptf_aimrun2009 as _calc_ptf_aimrun2009
from ptfkit._vectorize import vectorize_scalar_result


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
    clay: float | ArrayLike,
    bulk_density: float | ArrayLike,
    organic_matter: float | ArrayLike,
    gmd: float | ArrayLike,
    out: ArrayLike | None = None,
) -> floating | NDArray[floating]:
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
    return vectorize_scalar_result(
        _calc_scalar,
        _calc_array,
        clay,
        bulk_density,
        organic_matter,
        gmd,
        out=out,
    )


def _calc_scalar(
    clay: float,
    bulk_density: float,
    organic_matter: float,
    gmd: float,
) -> float:
    return _calc_ptf_aimrun2009(clay, bulk_density, organic_matter, gmd)


def _calc_array(
    clay: NDArray[floating],
    bulk_density: NDArray[floating],
    organic_matter: NDArray[floating],
    gmd: NDArray[floating],
) -> NDArray[floating]:
    clay_arr, bulk_density_arr, organic_matter_arr, gmd_arr = np.broadcast_arrays(
        clay,
        bulk_density,
        organic_matter,
        gmd,
    )
    result = (
        np.exp(
            -2.368
            + 3.846 * bulk_density_arr
            + 0.091 * organic_matter_arr
            - 6.203 * np.log(bulk_density_arr)
            - 0.343 * np.log(organic_matter_arr)
            - 2.334 * np.log(clay_arr)
            - 0.411 * np.log(gmd_arr)
        )
        / 86400.0
    )
    return np.asarray(result, dtype=float)
