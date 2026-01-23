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

from ptfkit._core import calc_ptf_li2007_ufunc


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
    sand,
    silt,
    clay,
    bulk_density,
    soil_organic_matter,
    out=None,
):
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

    out = tuple(out) if out else (None, None, None, None)

    res = calc_ptf_li2007_ufunc(sand, silt, clay, bulk_density, soil_organic_matter, out=out)

    return Li2007PTFResult(*res)
