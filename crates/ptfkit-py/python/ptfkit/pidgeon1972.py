r"""Pidgeon, 1972 - Uganda, ferrallitic soils (FC, PWP, AWC, EAWC).

Reference:
    PIDGEON, J. D. (1972). THE MEASUREMENT AND PREDICTION OF AVAILABLE WATER CAPACITY OF FERRALLITIC
    SOILS IN UGANDA. Journal of Soil Science, 23(4), 431-441.
    [DOI: 10.1111/j.1365-2389.1972.tb01674.x](https://doi.org/10.1111/j.1365-2389.1972.tb01674.x)


Territory

:   Uganda (non-alluvial ferrallitic soils with kaolinitic/illitic clay fraction)

"""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ptfkit._core import (
    calc_ptf_pidgeon1972_awc_coarse_sand_ufunc,
    calc_ptf_pidgeon1972_awc_fine_sand_ufunc,
    calc_ptf_pidgeon1972_awc_sand_om_ufunc,
    calc_ptf_pidgeon1972_awc_usd_ufunc,
    calc_ptf_pidgeon1972_awc_very_fine_sand_ufunc,
    calc_ptf_pidgeon1972_eawc_coarse_sand_om_ufunc,
    calc_ptf_pidgeon1972_eawc_fine_sand_om_ufunc,
    calc_ptf_pidgeon1972_eawc_sand_om_ufunc,
    calc_ptf_pidgeon1972_eawc_sand_ufunc,
    calc_ptf_pidgeon1972_eawc_ufunc,
    calc_ptf_pidgeon1972_fc_sand_om_ufunc,
    calc_ptf_pidgeon1972_fc_sand_ufunc,
    calc_ptf_pidgeon1972_fc_ufunc,
    calc_ptf_pidgeon1972_fc_vol_sand_om_ufunc,
    calc_ptf_pidgeon1972_pwp_sand_om_ufunc,
    calc_ptf_pidgeon1972_pwp_sand_ufunc,
    calc_ptf_pidgeon1972_pwp_ufunc,
)


if TYPE_CHECKING:
    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


__all__ = [
    'calc_ptf_pidgeon1972_awc',
    'calc_ptf_pidgeon1972_awc_coarse_sand',
    'calc_ptf_pidgeon1972_awc_fine_sand',
    'calc_ptf_pidgeon1972_awc_sand_organic_matter',
    'calc_ptf_pidgeon1972_awc_very_fine_sand',
    'calc_ptf_pidgeon1972_eawc',
    'calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter',
    'calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter',
    'calc_ptf_pidgeon1972_eawc_sand',
    'calc_ptf_pidgeon1972_eawc_sand_organic_matter',
    'calc_ptf_pidgeon1972_fc',
    'calc_ptf_pidgeon1972_fc_sand',
    'calc_ptf_pidgeon1972_fc_sand_organic_matter',
    'calc_ptf_pidgeon1972_fc_vol_sand_organic_matter',
    'calc_ptf_pidgeon1972_pwp',
    'calc_ptf_pidgeon1972_pwp_sand',
    'calc_ptf_pidgeon1972_pwp_sand_organic_matter',
]


@overload
def calc_ptf_pidgeon1972_fc(
    *,
    silt: float,
    clay: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_fc(
    *,
    silt: ArrayLike,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_fc(
    *,
    silt,
    clay,
    organic_matter,
    out=None,
):
    """Calculate field capacity for Ugandan ferrallitic soils.

    Equation (4). Uses particle-size method 2 (silt, clay) and organic matter.

    Args:
        silt: silt content (2-20 um) (%)
        clay: clay content (<2 um) (%)
        organic_matter: organic matter content (%)
        out: field capacity (w/w %) (FC)

    Returns:
        field capacity (w/w %)

    """
    return calc_ptf_pidgeon1972_fc_ufunc(silt, clay, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_fc_sand(
    *,
    sand: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_fc_sand(
    *,
    sand: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_fc_sand(
    *,
    sand,
    out=None,
):
    """Calculate field capacity from sand.

    Regression in Table 3 (FC w/w%, Sand (2)).

    Args:
        sand: sand content (%)
        out: field capacity (w/w %) (FC)

    Returns:
        field capacity (w/w %)

    """
    return calc_ptf_pidgeon1972_fc_sand_ufunc(sand, out=out)


@overload
def calc_ptf_pidgeon1972_fc_sand_organic_matter(
    *,
    sand: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_fc_sand_organic_matter(
    *,
    sand: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_fc_sand_organic_matter(
    *,
    sand,
    organic_matter,
    out=None,
):
    """Calculate field capacity from sand and organic matter.

    Best regression for FC (w/w%) with this input set (Table 3, Sand (2) + OM).

    Args:
        sand: sand content (%)
        organic_matter: organic matter content (%)
        out: field capacity (w/w %) (FC)

    Returns:
        field capacity (w/w %)

    """
    return calc_ptf_pidgeon1972_fc_sand_om_ufunc(sand, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_fc_vol_sand_organic_matter(
    *,
    sand: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_fc_vol_sand_organic_matter(
    *,
    sand: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_fc_vol_sand_organic_matter(
    *,
    sand,
    organic_matter,
    out=None,
):
    """Calculate field capacity (volume basis) from sand and organic matter.

    Regression in Table 3 (FC v/v%).

    Args:
        sand: sand content (%)
        organic_matter: organic matter content (%)
        out: field capacity (v/v %) (FC)

    Returns:
        field capacity (v/v %)

    """
    return calc_ptf_pidgeon1972_fc_vol_sand_om_ufunc(sand, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_pwp(
    *,
    silt: float,
    clay: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_pwp(
    *,
    silt: ArrayLike,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_pwp(
    *,
    silt,
    clay,
    organic_matter,
    out=None,
):
    """Calculate permanent wilting point for Ugandan ferrallitic soils.

    Equation (5). Uses particle-size method 2 (silt, clay) and organic matter.

    Args:
        silt: silt content (2-20 um) (%)
        clay: clay content (<2 um) (%)
        organic_matter: organic matter content (%)
        out: permanent wilting point (w/w %) (PWP)

    Returns:
        permanent wilting point (w/w %)

    """
    return calc_ptf_pidgeon1972_pwp_ufunc(silt, clay, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_pwp_sand(
    *,
    sand: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_pwp_sand(
    *,
    sand: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_pwp_sand(
    *,
    sand,
    out=None,
):
    """Calculate permanent wilting point from sand.

    Best regression for PWP (w/w%) with sand-only input (Table 3, Sand (1)).

    Args:
        sand: sand content (%)
        out: permanent wilting point (w/w %) (PWP)

    Returns:
        permanent wilting point (w/w %)

    """
    return calc_ptf_pidgeon1972_pwp_sand_ufunc(sand, out=out)


@overload
def calc_ptf_pidgeon1972_pwp_sand_organic_matter(
    *,
    sand: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_pwp_sand_organic_matter(
    *,
    sand: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_pwp_sand_organic_matter(
    *,
    sand,
    organic_matter,
    out=None,
):
    """Calculate permanent wilting point from sand and organic matter.

    Best regression for PWP (w/w%) with this input set (Table 3, Sand (2) + OM).

    Args:
        sand: sand content (%)
        organic_matter: organic matter content (%)
        out: permanent wilting point (w/w %) (PWP)

    Returns:
        permanent wilting point (w/w %)

    """
    return calc_ptf_pidgeon1972_pwp_sand_om_ufunc(sand, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_awc(
    *,
    clay: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_awc(
    *,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_awc(
    *,
    clay,
    organic_matter,
    out=None,
):
    """Calculate available water capacity for Ugandan ferrallitic soils.

    Equation (6). Uses particle-size method 1 (ultrasonic dispersion) and organic matter.
    Equation (8) is excluded because this input set is duplicated and has lower accuracy.

    Args:
        clay: clay content (<2 um) (%)
        organic_matter: organic matter content (%)
        out: available water capacity (mm/m) (AWC)

    Returns:
        available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_awc_usd_ufunc(clay, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_awc_sand_organic_matter(
    *,
    sand: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_awc_sand_organic_matter(
    *,
    sand: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_awc_sand_organic_matter(
    *,
    sand,
    organic_matter,
    out=None,
):
    """Calculate available water capacity from sand and organic matter.

    Regression in Table 3 (AWC mm/m, Sand (2) + OM).

    Args:
        sand: sand content (%)
        organic_matter: organic matter content (%)
        out: available water capacity (mm/m) (AWC)

    Returns:
        available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_awc_sand_om_ufunc(sand, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_awc_coarse_sand(
    *,
    coarse_sand: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_awc_coarse_sand(
    *,
    coarse_sand: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_awc_coarse_sand(
    *,
    coarse_sand,
    out=None,
):
    """Calculate available water capacity from coarse sand.

    Regression in Table 3 (AWC mm/m, Coarse Sand (1)).

    Args:
        coarse_sand: coarse sand content (%)
        out: available water capacity (mm/m) (AWC)

    Returns:
        available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_awc_coarse_sand_ufunc(coarse_sand, out=out)


@overload
def calc_ptf_pidgeon1972_awc_fine_sand(
    *,
    fine_sand: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_awc_fine_sand(
    *,
    fine_sand: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_awc_fine_sand(
    *,
    fine_sand,
    out=None,
):
    """Calculate available water capacity from fine sand.

    Regression in Table 3 (AWC mm/m, Fine Sand (1)).

    Args:
        fine_sand: fine sand content (%)
        out: available water capacity (mm/m) (AWC)

    Returns:
        available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_awc_fine_sand_ufunc(fine_sand, out=out)


@overload
def calc_ptf_pidgeon1972_awc_very_fine_sand(
    *,
    very_fine_sand: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_awc_very_fine_sand(
    *,
    very_fine_sand: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_awc_very_fine_sand(
    *,
    very_fine_sand,
    out=None,
):
    """Calculate available water capacity from very fine sand.

    Regression in Table 3 (AWC mm/m, Very Fine Sand (1)).

    Args:
        very_fine_sand: very fine sand content (%)
        out: available water capacity (mm/m) (AWC)

    Returns:
        available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_awc_very_fine_sand_ufunc(very_fine_sand, out=out)


@overload
def calc_ptf_pidgeon1972_eawc(
    *,
    silt: float,
    clay: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_eawc(
    *,
    silt: ArrayLike,
    clay: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_eawc(
    *,
    silt,
    clay,
    organic_matter,
    out=None,
):
    """Calculate easily available water capacity for Ugandan ferrallitic soils.

    Equation (7). Uses particle-size method 2 (silt, clay) and organic matter.

    Args:
        silt: silt content (2-20 um) (%)
        clay: clay content (<2 um) (%)
        organic_matter: organic matter content (%)
        out: easily available water capacity (mm/m) (EAWC)

    Returns:
        easily available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_eawc_ufunc(silt, clay, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_eawc_sand(
    *,
    sand: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_eawc_sand(
    *,
    sand: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_eawc_sand(
    *,
    sand,
    out=None,
):
    """Calculate easily available water capacity from sand.

    Regression in Table 3 (EAWC mm/m, Sand (2)).

    Args:
        sand: sand content (%)
        out: easily available water capacity (mm/m) (EAWC)

    Returns:
        easily available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_eawc_sand_ufunc(sand, out=out)


@overload
def calc_ptf_pidgeon1972_eawc_sand_organic_matter(
    *,
    sand: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_eawc_sand_organic_matter(
    *,
    sand: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_eawc_sand_organic_matter(
    *,
    sand,
    organic_matter,
    out=None,
):
    """Calculate easily available water capacity from sand and organic matter.

    Regression in Table 3 (EAWC mm/m, Sand (1) + OM).

    Args:
        sand: sand content (%)
        organic_matter: organic matter content (%)
        out: easily available water capacity (mm/m) (EAWC)

    Returns:
        easily available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_eawc_sand_om_ufunc(sand, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter(
    *,
    coarse_sand: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter(
    *,
    coarse_sand: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter(
    *,
    coarse_sand,
    organic_matter,
    out=None,
):
    """Calculate easily available water capacity from coarse sand and organic matter.

    Regression in Table 3 (EAWC mm/m, Coarse Sand (1) + OM).

    Args:
        coarse_sand: coarse sand content (%)
        organic_matter: organic matter content (%)
        out: easily available water capacity (mm/m) (EAWC)

    Returns:
        easily available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_eawc_coarse_sand_om_ufunc(coarse_sand, organic_matter, out=out)


@overload
def calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter(
    *,
    fine_sand: float,
    organic_matter: float,
) -> floating: ...


@overload
def calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter(
    *,
    fine_sand: ArrayLike,
    organic_matter: ArrayLike,
    out: ArrayLike | None = None,
) -> NDArray[floating]: ...


def calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter(
    *,
    fine_sand,
    organic_matter,
    out=None,
):
    """Calculate easily available water capacity from fine sand and organic matter.

    Regression in Table 3 (EAWC mm/m, Fine Sand (1) + OM).

    Args:
        fine_sand: fine sand content (%)
        organic_matter: organic matter content (%)
        out: easily available water capacity (mm/m) (EAWC)

    Returns:
        easily available water capacity (mm/m)

    """
    return calc_ptf_pidgeon1972_eawc_fine_sand_om_ufunc(fine_sand, organic_matter, out=out)
