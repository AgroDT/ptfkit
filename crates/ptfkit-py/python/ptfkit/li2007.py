r"""Li et al., 2007 - China, Fengqiu County soils in the North China Plain (WRC, $K_{sat}$).

Reference:
    Li, Y., Chen, D., White, R. E., Zhu, A., & Zhang, J. (2007).
    Estimating soil hydraulic properties of Fengqiu County soils in
    the North China Plain using pedo-transfer functions.
    Geoderma, 138(3-4), 261-271.
    [DOI: 10.1016/j.geoderma.2006.11.018](https://doi.org/10.1016/j.geoderma.2006.11.018)

$h(\theta)$ model

:   VG

$k(h)$ model

:   $K_{sat}$

Territory

:   Fengqiu County soils in the North China Plain, China
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

import numpy as np

from ptfkit._vectorize import vectorize_namedtuple_result


try:
    from ptfkit._rust import calc_ptf_li2007 as _calc_ptf_li2007
except ImportError:  # pragma: no cover - used until the Rust extension is built.
    _calc_ptf_li2007 = None


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = ['Li2007PTFResult', 'calc_ptf_li2007']


T = TypeVar('T')


class Li2007PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Li et al., 2007.

    Attributes:
        theta_s: saturated water content (θs) (cm^3/cm^3)
        a_vg: fitting parameter of the van Genuchten equation, inversely related to the air-entry
              suction (α) (cm^-1)
        n_vg: fitting parameter of the van Genuchten equation, that characterizes the pore-size
              distribution (n)
        k_sat: saturated hydraulic conductivity (Ks) (m/s)

    """  # noqa: RUF002

    theta_s: T
    a_vg: T
    n_vg: T
    k_sat: T


@overload
def calc_ptf_li2007(
    *,
    sand: float,
    silt: float,
    clay: float,
    bulk_density: float,
    soil_organic_matter: float,
) -> Li2007PTFResult[floating]: ...


@overload
def calc_ptf_li2007(
    *,
    sand: ArrayLike,
    silt: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    soil_organic_matter: ArrayLike,
    out: Li2007PTFResult[NDArray[floating]] | None = None,
) -> Li2007PTFResult[NDArray[floating]]: ...


def calc_ptf_li2007(
    *,
    sand: float | ArrayLike,
    silt: float | ArrayLike,
    clay: float | ArrayLike,
    bulk_density: float | ArrayLike,
    soil_organic_matter: float | ArrayLike,
    out: Li2007PTFResult[NDArray[floating]] | None = None,
) -> Li2007PTFResult[floating] | Li2007PTFResult[NDArray[floating]]:
    """Calculate PTF for Fengqiu County soils in the North China Plain, China.

    Arguments:
        sand: sand content, 0.02-2 mm (%)
        silt: silt content, 0.02-0.002 mm (%)
        clay: clay content, <0.002 mm (%)
        bulk_density: bulk density (BD) (g/cm^3)
        soil_organic_matter: soil organic matter content (SOM) (%)
        out: PTF results

    Returns:
        PTF results

    """
    return vectorize_namedtuple_result(
        _calc_scalar,
        _calc_array,
        Li2007PTFResult,
        sand,
        silt,
        clay,
        bulk_density,
        soil_organic_matter,
        out=out,
    )


def _calc_scalar(
    sand: float,
    silt: float,
    clay: float,
    bulk_density: float,
    soil_organic_matter: float,
) -> tuple[float, float, float, float]:
    if _calc_ptf_li2007 is not None:
        return _calc_ptf_li2007(
            sand,
            silt,
            clay,
            bulk_density,
            soil_organic_matter,
        )

    sand_ln = np.log(sand)
    silt_ln = np.log(silt)
    clay_ln = np.log(clay)
    soil_organic_matter_ln = np.log(soil_organic_matter)
    bulk_density_ln = np.log(bulk_density)
    theta_s = np.exp(
        -1.531
        + 0.212 * sand_ln
        + 0.006 * silt
        - 0.051 * soil_organic_matter
        - 0.566 * bulk_density_ln
    )
    a_vg = np.exp(
        -67.408
        - 0.040 * silt
        - 0.670 * silt_ln
        - 2.189 * soil_organic_matter
        + 1.410 * soil_organic_matter_ln
        + 78.400 * bulk_density
        - 121.331 * bulk_density_ln
    )
    n_vg = (
        1.488
        + 0.002 * silt_ln
        + 0.013 * clay
        - 0.248 * clay_ln
        + 0.048 * soil_organic_matter_ln
        + 0.451 * bulk_density_ln
    )
    k_sat = (
        np.exp(
            13.262
            - 1.914 * sand_ln
            - 0.974 * silt_ln
            - 0.058 * clay
            - 1.709 * soil_organic_matter_ln
            + 2.885 * soil_organic_matter
            - 8.026 * bulk_density_ln
        )
        / 8640000.0
    )
    return (theta_s, a_vg, n_vg, k_sat)


def _calc_array(
    sand: NDArray[floating],
    silt: NDArray[floating],
    clay: NDArray[floating],
    bulk_density: NDArray[floating],
    soil_organic_matter: NDArray[floating],
) -> tuple[NDArray[floating], ...]:
    sand_arr, silt_arr, clay_arr, bulk_density_arr, soil_organic_matter_arr = np.broadcast_arrays(
        sand,
        silt,
        clay,
        bulk_density,
        soil_organic_matter,
    )
    sand_ln = np.log(sand_arr)
    silt_ln = np.log(silt_arr)
    clay_ln = np.log(clay_arr)
    soil_organic_matter_ln = np.log(soil_organic_matter_arr)
    bulk_density_ln = np.log(bulk_density_arr)
    return (
        np.exp(
            -1.531
            + 0.212 * sand_ln
            + 0.006 * silt_arr
            - 0.051 * soil_organic_matter_arr
            - 0.566 * bulk_density_ln
        ),
        np.exp(
            -67.408
            - 0.040 * silt_arr
            - 0.670 * silt_ln
            - 2.189 * soil_organic_matter_arr
            + 1.410 * soil_organic_matter_ln
            + 78.400 * bulk_density_arr
            - 121.331 * bulk_density_ln
        ),
        1.488
        + 0.002 * silt_ln
        + 0.013 * clay_arr
        - 0.248 * clay_ln
        + 0.048 * soil_organic_matter_ln
        + 0.451 * bulk_density_ln,
        np.exp(
            13.262
            - 1.914 * sand_ln
            - 0.974 * silt_ln
            - 0.058 * clay_arr
            - 1.709 * soil_organic_matter_ln
            + 2.885 * soil_organic_matter_arr
            - 8.026 * bulk_density_ln
        )
        / 8640000.0,
    )
