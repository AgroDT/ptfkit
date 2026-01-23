r"""Rawls & Brakensiek, 1985 - USA (WRC, HCC).

Reference:
    Rawls, W. J., & Brakensiek, D. L. (1985). Prediction of soil water properties for hydrologic
    modeling. In E. B. Jones & T. J. Ward (Eds.), Proc. Symp. Watershed Management in the Eighties,
    Denver, CO, 30 Apr.-1 May 1985 (pp. 293-299). American Society of Civil Engineers, New York.

$h(\theta)$ model

:   full WRC, VG, BC, BD

$k(h)$ model

:   VGM, Campbell model

Territory

:   USA

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import calc_ptf_rawls1985_ufunc


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'Rawls1985PTFResult',
    'calc_ptf_rawls1985',
]


T = TypeVar('T')


class Rawls1985PTFResult(NamedTuple, Generic[T]):
    """The results of calculating the PTF by Rawls & Brakensiek, 1985.

    Attributes:
        theta_s: volumetric saturated soil water content (θs) (cm³/cm³)
        theta_r: volumetric residual soil water content (θr) (cm³/cm³)
        a_vg: fitting parameter of the van Genuchten equation (α) (cm⁻¹)
        n_vg: fitting parameter of the van Genuchten equation (n)
        k_sat: saturated hydraulic conductivity (Ks) (m/s)
        l_vgm: pore connectivity/tortuosity parameter (L)

    """  # noqa: RUF002

    theta_s: T
    theta_r: T
    a_vg: T
    n_vg: T
    k_sat: T
    l_vgm: T


@overload
def calc_ptf_rawls1985(
    *,
    sand: float,
    clay: float,
    bulk_density: float,
) -> Rawls1985PTFResult[floating]: ...


@overload
def calc_ptf_rawls1985(
    *,
    sand: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    out: Rawls1985PTFResult[NDArray[floating]] | None = None,
) -> Rawls1985PTFResult[NDArray[floating]]: ...


def calc_ptf_rawls1985(
    *,
    sand,
    clay,
    bulk_density,
    out=None,
):
    """Calculate PTF for soils of USA.

    Arguments:
        sand: sand content, 0.5-1 mm (%)
        clay: clay content, <0.002 mm (%)
        bulk_density: bulk density (g/cm^3)
        out: PTF results

    Returns:
        PTF results

    """
    out = tuple(out) if out else (None, None, None, None, None, None)

    res = calc_ptf_rawls1985_ufunc(sand, clay, bulk_density, out=out)

    return Rawls1985PTFResult(*res)
