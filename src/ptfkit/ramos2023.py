r"""Ramos et al., 2023 - Portugal (WRC, HCC).

Reference:
    Ramos, T. B., Darouich, H., & Gonçalves, M. C. (2023). Development and functional evaluation of
    pedotransfer functions for estimating soil hydraulic properties in Portuguese soils:
    Implications for soil water dynamics. Geoderma Regional, 35, e00717.
    [DOI: 10.1016/j.geodrs.2023.e00717](https://doi.org/10.1016/j.geodrs.2023.e00717)

$h(\theta)$ model

:   VG

$k(h)$ model

:   MVG

Dataset

:   PROPSOLO soil database (Gonçalves et al., 2011);
    697 horizons/layers from 330 soil profiles across Portugal (1977-2011)

Territory

:   Portugal
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload

from ptfkit._core import (
    calc_ptf_ramos2023_allfcwp_ufunc,
    calc_ptf_ramos2023_sscbdgmd_ufunc,
    calc_ptf_ramos2023_sscd_ufunc,
    calc_ptf_ramos2023_sscgmd_ufunc,
)


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'Ramos2023PTFResult',
    'calc_ptf_ramos2023_allfcwp',
    'calc_ptf_ramos2023_sscbdgmd',
    'calc_ptf_ramos2023_sscd',
    'calc_ptf_ramos2023_sscgmd',
]


T = TypeVar('T')


class Ramos2023PTFResult(NamedTuple, Generic[T]):
    r"""The results of calculating the PTF by Ramos et al., 2023.

    Attributes:
        theta_s: saturated water content (θs) (cm^3/cm^3)
        theta_r: residual water content (θr) (cm^3/cm^3)
        a_vg: empirical shape parameter (α)
        n_vg: empirical shape parameter
        k_sat: saturated hydraulic conductivity (Ks) (m/s)
        l_vgm: pore connectivity/tortuosity parameter (ℓ, λ)

    """  # noqa: RUF002

    theta_s: T
    theta_r: T
    a_vg: T
    n_vg: T
    k_sat: T
    l_vgm: T


@overload
def calc_ptf_ramos2023_sscd(
    *,
    coarse_sand: float,
    fine_sand: float,
    silt: float,
    clay: float,
    depth: float,
) -> Ramos2023PTFResult[floating]: ...


@overload
def calc_ptf_ramos2023_sscd(
    *,
    coarse_sand: ArrayLike,
    fine_sand: ArrayLike,
    silt: ArrayLike,
    clay: ArrayLike,
    depth: ArrayLike,
    out: Ramos2023PTFResult[NDArray[floating]] | None = None,
) -> Ramos2023PTFResult[NDArray[floating]]: ...


def calc_ptf_ramos2023_sscd(
    *,
    coarse_sand,
    fine_sand,
    silt,
    clay,
    depth,
    out=None,
) -> Ramos2023PTFResult:
    """Calculate PTF for Portuguese soils.

    Model 1. Input: SSCD - Sand (coarse and fine), Silt, Clay, Depth.

    Arguments:
        coarse_sand: coarse sand content, 200-2000 um (CS) (%)
        fine_sand: fine sand content, 20-200 um (FS) (%)
        silt: silt content, 2-20 um (Si) (%)
        clay: clay content, <2 um (C) (%)
        depth: mean soil layer depth (Z) (cm)
        out: PTF results

    Returns:
        PTF results

    """

    out = tuple(out) if out else (None, None, None, None, None, None)

    res = calc_ptf_ramos2023_sscd_ufunc(coarse_sand, fine_sand, silt, clay, depth, out=out)

    return Ramos2023PTFResult(*res)


@overload
def calc_ptf_ramos2023_sscgmd(
    *,
    coarse_sand: float,
    fine_sand: float,
    silt: float,
    clay: float,
    gmd: float,
    gsd: float,
) -> Ramos2023PTFResult[floating]: ...


@overload
def calc_ptf_ramos2023_sscgmd(
    *,
    coarse_sand: ArrayLike,
    fine_sand: ArrayLike,
    silt: ArrayLike,
    clay: ArrayLike,
    gmd: ArrayLike,
    gsd: ArrayLike,
    out: Ramos2023PTFResult[NDArray[floating]] | None = None,
) -> Ramos2023PTFResult[NDArray[floating]]: ...


def calc_ptf_ramos2023_sscgmd(
    *,
    coarse_sand,
    fine_sand,
    silt,
    clay,
    gmd,
    gsd,
    out=None,
) -> Ramos2023PTFResult:
    """Calculate PTF for Portuguese soils.

    Model 2. Input: SSCGMD - Sand (coarse and fine), Silt, Clay, GMD (and GSD).

    Arguments:
        coarse_sand: coarse sand content, 200-2000 um (CS) (%)
        fine_sand: fine sand content, 20-200 um (FS) (%)
        silt: silt content, 2-20 um (Si) (%)
        clay: clay content, <2 um (C) (%)
        gmd: mean particle diameter (GPD) (mm)
        gsd: geometrical standard deviation
        out: PTF results

    Returns:
        PTF results

    """

    out = tuple(out) if out else (None, None, None, None, None, None)

    res = calc_ptf_ramos2023_sscgmd_ufunc(coarse_sand, fine_sand, silt, clay, gmd, gsd, out=out)

    return Ramos2023PTFResult(*res)


@overload
def calc_ptf_ramos2023_sscbdgmd(
    *,
    fine_sand: float,
    silt: float,
    clay: float,
    depth: float,
    bulk_density: float,
    gmd: float,
    gsd: float,
) -> Ramos2023PTFResult[floating]: ...


@overload
def calc_ptf_ramos2023_sscbdgmd(
    *,
    fine_sand: ArrayLike,
    silt: ArrayLike,
    clay: ArrayLike,
    depth: ArrayLike,
    bulk_density: ArrayLike,
    gmd: ArrayLike,
    gsd: ArrayLike,
    out: Ramos2023PTFResult[NDArray[floating]] | None = None,
) -> Ramos2023PTFResult[NDArray[floating]]: ...


def calc_ptf_ramos2023_sscbdgmd(
    *,
    fine_sand,
    silt,
    clay,
    depth,
    bulk_density,
    gmd,
    gsd,
    out=None,
) -> Ramos2023PTFResult:
    """Calculate PTF for Portuguese soils.

    Model 3. Input: SSCBDGMD - Sand (fine only), Silt, Clay, Bulk Density, GMD (and GSD) and depth.

    Arguments:
        fine_sand: fine sand content, 20-200 um (FS) (%)
        silt: silt content, 2-20 um (Si) (%)
        clay: clay content, <2 um (C) (%)
        depth: mean soil layer depth (Z) (cm)
        bulk_density: bulk density (BD) (g/cm^3)
        gmd: mean particle diameter (GPD) (mm)
        gsd: geometrical standard deviation
        out: PTF results

    Returns:
        PTF results

    """

    out = tuple(out) if out else (None, None, None, None, None, None)

    res = calc_ptf_ramos2023_sscbdgmd_ufunc(
        fine_sand,
        silt,
        clay,
        depth,
        bulk_density,
        gmd,
        gsd,
        out=out,
    )

    return Ramos2023PTFResult(*res)


@overload
def calc_ptf_ramos2023_allfcwp(
    *,
    fine_sand: float,
    silt: float,
    clay: float,
    bulk_density: float,
    gmd: float,
    gsd: float,
    theta_33: float,
    theta_1580: float,
) -> Ramos2023PTFResult[floating]: ...


@overload
def calc_ptf_ramos2023_allfcwp(
    *,
    fine_sand: ArrayLike,
    silt: ArrayLike,
    clay: ArrayLike,
    bulk_density: ArrayLike,
    gmd: ArrayLike,
    gsd: ArrayLike,
    theta_33: ArrayLike,
    theta_1580: ArrayLike,
    out: Ramos2023PTFResult[NDArray[floating]] | None = None,
) -> Ramos2023PTFResult[NDArray[floating]]: ...


def calc_ptf_ramos2023_allfcwp(
    *,
    fine_sand,
    silt,
    clay,
    bulk_density,
    gmd,
    gsd,
    theta_33,
    theta_1580,
    out=None,
) -> Ramos2023PTFResult:
    """Calculate PTF for Portuguese soils.

    Model 4. Input: ALLFCWP - all SSCBDGMD (Sand (fine only), Silt, Clay, Bulk Density, GMD (and
    GSD), but without depth), Field Capacity (theta_33), Wilting Point (theta_1580).

    Arguments:
        fine_sand: fine sand content, 20-200 um (FS) (%)
        silt: silt content, 2-20 um (Si) (%)
        clay: clay content, <2 um (C) (%)
        bulk_density: bulk density (BD) (g/cm^3)
        gmd: mean particle diameter (GPD) (mm)
        gsd: geometrical standard deviation
        theta_33: soil water content at 33 kpa matric heads (θ33) (cm^3/cm^3)
        theta_1580: soil water content at 1580 kpa matric heads (θ1580) (cm^3/cm^3)
        out: PTF results

    Returns:
        PTF results

    """

    out = tuple(out) if out else (None, None, None, None, None, None)

    res = calc_ptf_ramos2023_allfcwp_ufunc(
        fine_sand,
        silt,
        clay,
        bulk_density,
        gmd,
        gsd,
        theta_33,
        theta_1580,
        out=out,
    )

    return Ramos2023PTFResult(*res)
