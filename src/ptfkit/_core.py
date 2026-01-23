import numpy as np


TYPE_CHECKING = False
if TYPE_CHECKING:
    import Cython as cython  # pragma: no cover  # noqa: N813
else:
    import cython


M_PER_DAY_TO_M_PER_SEC = 1 / 86400
CM_PER_MIN_TO_M_PER_SEC = 1 / 6000
CM_PER_HOUR_TO_M_PER_SEC = 1 / 360000
CM_PER_DAY_TO_M_PER_SEC = 1 / 8640000
MM_PER_MIN_TO_M_PER_SEC = 1 / 60000
MM_PER_HOUR_TO_M_PER_SEC = 1 / 3600000
CM_TO_M = 1 / 100
PERCENTS_TO_G_PER_KG = 10


@cython.ufunc
@cython.cfunc
def calc_ptf_aimrun2009_ufunc(
    clay: cython.double,
    bulk_density: cython.double,
    organic_matter: cython.double,
    gmd: cython.double,
) -> cython.double:
    k_sat_m_per_day = np.exp(
        -2.368
        + 3.846 * bulk_density
        + 0.091 * organic_matter
        - 6.203 * np.log(bulk_density)
        - 0.343 * np.log(organic_matter)
        - 2.334 * np.log(clay)
        - 0.411 * np.log(gmd)
    )
    return k_sat_m_per_day * M_PER_DAY_TO_M_PER_SEC


@cython.ufunc
@cython.cfunc
def calc_ptf_li2007_ufunc(
    sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    soil_organic_matter: cython.double,
) -> tuple[cython.double, cython.double, cython.double, cython.double]:
    sand_ln = np.log(sand)
    silt_ln = np.log(silt)
    soil_organic_matter_ln = np.log(soil_organic_matter)
    bulk_density_ln = np.log(bulk_density)
    theta_s = np.exp(
        -1.531
        + 0.212 * sand_ln
        + 0.006 * silt
        - 0.051 * soil_organic_matter
        - 0.566 * bulk_density_ln
    )  # fmt: skip
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
        - 0.248 * np.log(clay)
        + 0.048 * soil_organic_matter_ln
        + 0.451 * bulk_density_ln
    )
    k_sat_cm_per_day = np.exp(
        13.262
        - 1.914 * sand_ln
        - 0.974 * silt_ln
        - 0.058 * clay
        - 1.709 * soil_organic_matter_ln
        + 2.885 * soil_organic_matter
        - 8.026 * bulk_density_ln
    )
    k_sat = k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC

    return theta_s, a_vg, n_vg, k_sat


@cython.ufunc
@cython.cfunc
def calc_ptf_qiao2018_ufunc(
    sand: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    soil_organic_carbon: cython.double,
) -> tuple[cython.double, cython.double, cython.double, cython.double]:
    bulk_density_inv = bulk_density**-1
    bulk_density_square = bulk_density**2
    theta_s = (
        -0.779
        - 0.608 * bulk_density_square
        + 0.016 * np.log(sand)
        + 1.712 * bulk_density
        - 0.000027 * sand**2
    )
    a_vg = 0.012 + 0.0002 * sand - 0.007 * bulk_density
    n_vg = (
        5.507
        + 6.966 * clay**-1
        - 7.272 * bulk_density_square
        + 0.186 * soil_organic_carbon**-1
        - 4.399 * bulk_density_inv
    )
    k_sat_cm_per_min = (
        -1.523 + 1.685 * bulk_density_inv + 0.0004 * sand + 0.996 * np.log(bulk_density)
    )
    k_sat = k_sat_cm_per_min * CM_PER_MIN_TO_M_PER_SEC

    return theta_s, a_vg, n_vg, k_sat


@cython.ufunc
@cython.cfunc
def calc_bulk_density_for_ptf_bai2022_ufunc(
    sand: cython.double,
    clay: cython.double,
    slope: cython.double,
) -> cython.double:
    return -0.281 + 0.004 * sand + 1.343 * slope + 0.008 * clay


@cython.ufunc
@cython.cfunc
def calc_ptf_bai2022_without_depth_ufunc(
    sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    altitude: cython.double,
    slope: cython.double,
    aspect: cython.double,
    precipitation: cython.double,
) -> tuple[cython.double, cython.double, cython.double, cython.double, cython.double]:
    clay_ln = np.log(clay)
    slope_inv = slope**-1
    theta_s = np.exp(
        -4.947 + 1.922 * slope + 0.062 * aspect + 0.004 * precipitation + 0.001 * altitude
    )
    theta_r = (
        -0.310
        + 0.022 * clay_ln
        + 1.386 * np.log(slope)
        - 0.158 * np.log(precipitation)
        + 91.188 * altitude**-1
        - 35.231 * precipitation**-1
        + 1.302 * slope_inv
    )
    a_vg = np.exp(
        14.915 + 7.033 * slope + 0.007 * precipitation + 0.001 * altitude + 0.212 * aspect
    )
    n_vg = 1.149 + 0.021 * sand + 0.020 * silt - 0.667 * slope - 0.001 * precipitation
    k_sat_cm_per_min = (
        0.147
        - 0.049 * clay_ln
        + 1.806 * 10e-7 * precipitation**2
        + 0.120 * bulk_density**-1
        - 0.174 * slope_inv
        + 3.369 * 10e-5 * altitude
        + 0.002 * clay
    )
    k_sat = k_sat_cm_per_min * CM_PER_MIN_TO_M_PER_SEC

    return theta_s, theta_r, a_vg, n_vg, k_sat


@cython.ufunc
@cython.cfunc
def calc_ptf_bai2022_with_depth_ufunc(
    sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    depth: cython.double,
    altitude: cython.double,
    slope: cython.double,
    precipitation: cython.double,
) -> tuple[cython.double, cython.double, cython.double, cython.double, cython.double]:
    clay_inv = clay**-1
    precipitation_square = precipitation**2
    theta_s = np.exp(
        -2.287
        - 0.380 * clay_inv
        - 0.677 * bulk_density**2
        + 0.100 * np.log(altitude)
        + 1.589 * bulk_density
        - 9.540 * 10e-5 * depth
    )
    theta_r = (
        0.095
        + 0.020 * np.log(clay)
        + 72.552 * altitude**-1
        - 2.722 * 10e-7 * precipitation_square
        - 26.869 * precipitation**-1
        + 5.168 * 10e-8 * depth**2
    )
    a_vg = np.exp(
        -12.675
        - 0.002 * depth
        + 0.007 * precipitation
        + 0.001 * altitude
        + 4.887 * slope
        - 0.007 * silt
    )
    n_vg = (
        1.028
        + 0.022 * sand
        + 0.021 * silt
        - 0.610 * slope
        - 0.001 * precipitation
        + 7.463 * 10e-5 * depth
    )
    k_sat_cm_per_min = (
        0.018
        + 0.310 * depth**-1
        + 0.125 * clay_inv
        + 0.104 * bulk_density**-1
        - 0.135 * slope**-1
        + 2.781 * 10e-5 * altitude
        + 1.159 * 10e-7 * precipitation_square
    )
    k_sat = k_sat_cm_per_min * CM_PER_MIN_TO_M_PER_SEC

    return theta_s, theta_r, a_vg, n_vg, k_sat


@cython.ufunc
@cython.cfunc
def calc_theta_1500_rawls1982_ufunc(
    clay: cython.double,
    organic_matter: cython.double,
) -> cython.double:
    return 0.0260 + 0.0050 * clay + 0.0158 * organic_matter


@cython.ufunc
@cython.cfunc
def calc_theta_33_rawls1982_ufunc(
    sand: cython.double,
    organic_matter: cython.double,
    theta_1500: cython.double,
) -> cython.double:
    return 0.2391 - 0.0019 * sand + 0.0210 * organic_matter + 0.72 * theta_1500


@cython.ufunc
@cython.cfunc
def calc_full_wrc_rawls1982_ufunc(
    sand: cython.double,
    organic_matter: cython.double,
    bulk_density: cython.double,
    theta_33: cython.double,
    theta_1500: cython.double,
) -> tuple[
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
]:
    theta_4 = (
        0.1829
        - 0.0246 * organic_matter
        - 0.0376 * bulk_density
        + 1.89 * theta_33
        - 1.38 * theta_1500
    )

    theta_7 = (
        0.8888
        - 0.0003 * sand
        - 0.0107 * organic_matter
        + 1.53 * theta_33
        - 0.81 * theta_1500
    )  # fmt: skip

    theta_10 = (
        0.0619
        - 0.0002 * sand
        - 0.0067 * organic_matter
        + 1.34 * theta_33
        - 0.51 * theta_1500
    )  # fmt: skip

    theta_20 = 0.0319 - 0.0002 * sand + 1.01 * theta_33 - 0.06 * theta_1500

    theta_60 = 0.0136 - 0.0091 * bulk_density + 0.66 * theta_33 + 0.39 * theta_1500

    theta_100 = -0.0034 + 0.0022 * organic_matter + 0.52 * theta_33 + 0.54 * theta_1500

    theta_200 = -0.0043 + 0.0026 * organic_matter + 0.36 * theta_33 + 0.69 * theta_1500

    theta_400 = -0.0038 + 0.0026 * organic_matter + 0.24 * theta_33 + 0.79 * theta_1500

    theta_700 = -0.0027 + 0.0024 * organic_matter + 0.16 * theta_33 + 0.86 * theta_1500

    theta_1000 = -0.0019 + 0.0022 * organic_matter + 0.11 * theta_33 + 0.89 * theta_1500

    return (
        theta_4,
        theta_7,
        theta_10,
        theta_20,
        theta_33,
        theta_60,
        theta_100,
        theta_200,
        theta_400,
        theta_700,
        theta_1000,
        theta_1500,
    )


@cython.ufunc
@cython.cfunc
def calc_full_wrc_rawls1983_ufunc(
    sand: cython.double,
    clay: cython.double,
    organic_matter: cython.double,
    bulk_density: cython.double,
) -> tuple[
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
]:
    theta_20 = (
        0.4180
        - 0.0021 * sand
        + 0.0035 * clay
        + 0.0232 * organic_matter
        - 0.0859 * bulk_density
    )  # fmt: skip

    theta_33 = (
        0.3486
        - 0.0018 * sand
        + 0.0039 * clay
        + 0.0228 * organic_matter
        - 0.0738 * bulk_density
    )  # fmt: skip

    theta_60 = (
        0.2819
        - 0.0014 * sand
        + 0.0042 * clay
        + 0.0216 * organic_matter
        - 0.0612 * bulk_density
    )  # fmt: skip

    theta_100 = (
        0.2352
        - 0.0012 * sand
        + 0.0043 * clay
        + 0.0202 * organic_matter
        - 0.0517 * bulk_density
    )  # fmt: skip

    theta_200 = (
        0.1837
        - 0.0009 * sand
        + 0.0044 * clay
        + 0.0181 * organic_matter
        - 0.0407 * bulk_density
    )  # fmt: skip

    theta_400 = (
        0.1426
        - 0.0007 * sand
        + 0.0045 * clay
        + 0.0160 * organic_matter
        - 0.0315 * bulk_density
    )  # fmt: skip

    theta_700 = (
        0.1155
        - 0.0005 * sand
        + 0.0045 * clay
        + 0.0143 * organic_matter
        - 0.0253 * bulk_density
    )  # fmt: skip

    theta_1000 = (
        0.1005
        - 0.0004 * sand
        + 0.0045 * clay
        + 0.0133 * organic_matter
        - 0.0218 * bulk_density
    )  # fmt: skip

    theta_1500 = (
        0.0854
        - 0.0004 * sand
        + 0.0044 * clay
        + 0.0122 * organic_matter
        - 0.0182 * bulk_density
    )  # fmt: skip

    return (
        theta_20,
        theta_33,
        theta_60,
        theta_100,
        theta_200,
        theta_400,
        theta_700,
        theta_1000,
        theta_1500,
    )


@cython.ufunc
@cython.cfunc
def calc_ptf_rawls1985_ufunc(
    sand: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
) -> tuple[
    cython.double, cython.double, cython.double, cython.double, cython.double, cython.double
]:
    porosity = 1.0 - bulk_density / 2.65

    porosity_square = porosity * porosity
    clay_square = clay * clay
    sand_square = sand * sand
    sand_porosity = sand * porosity
    sand_square_porosity_square = sand_square * porosity_square
    clay_square_porosity_square = clay_square * porosity_square
    clay_square_porosity = clay_square * porosity
    sand_square_porosity = sand_square * porosity
    sand_square_clay = sand_square * clay
    clay_porosity_square = clay * porosity_square

    hb = np.exp(
        5.3396738
        + 0.1845038 * clay
        - 2.48394546 * porosity
        - 0.00213853 * clay_square
        - 0.04356349 * sand_porosity
        - 0.61745089 * clay * porosity
        + 0.00143598 * sand_square_porosity_square
        - 0.00855375 * clay_square_porosity_square
        - 0.00001282 * sand_square_clay
        + 0.00895359 * clay_square_porosity
        - 0.00072472 * sand_square_porosity
        + 0.0000054 * clay_square * sand
        + 0.5002806 * clay_porosity_square
    )

    a_vg = 1.0 / hb

    n_vg = 1.0 + np.exp(
        -0.7842831
        + 0.0177544 * sand
        - 1.062498 * porosity
        - 0.00005304 * sand_square
        - 0.00273493 * clay_square
        + 1.11134946 * porosity_square
        - 0.03088295 * sand_porosity
        + 0.00026587 * sand_square_porosity_square
        - 0.00610522 * clay_square_porosity_square
        - 0.00000235 * sand_square_clay
        + 0.00798746 * clay_square_porosity
        - 0.0067449 * clay_porosity_square
    )

    theta_r = (
        -0.0182482
        + 0.00087269 * sand
        + 0.00513488 * clay
        + 0.02939286 * porosity
        - 0.00015395 * clay_square
        - 0.0010827 * sand_porosity
        - 0.00018233 * clay_square_porosity_square
        + 0.00030703 * clay_square_porosity
        - 0.0023584 * clay_porosity_square
    )

    k_sat_cm_per_day = 24.0 * np.exp(
        19.52348 * porosity
        - 8.96847
        - 0.028212 * clay
        + 0.00018107 * sand_square
        - 0.0094125 * clay_square
        - 8.395215 * porosity_square
        + 0.077718 * sand_porosity
        - 0.00298 * sand_square_porosity_square
        - 0.019492 * clay_square_porosity_square
        + 0.0000173 * sand_square_clay
        + 0.02733 * clay_square_porosity
        + 0.001434 * sand_square_porosity
        - 0.0000035 * sand * clay_square
    )

    k_sat = k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC

    l_vgm = 0.5

    theta_s = porosity

    return theta_s, theta_r, a_vg, n_vg, k_sat, l_vgm


@cython.ufunc
@cython.cfunc
def calc_ptf_puckett1985_ufunc(
    sand: cython.double,
    fine_sand: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    porosity: cython.double,
) -> tuple[
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
]:
    theta_0 = (
        0.264 * bulk_density
        + 1.60 * porosity
        - 0.706
    )  # fmt: skip

    theta_1 = (
        0.318 * bulk_density
        + 1.69 * porosity
        - 0.834
    )  # fmt: skip

    theta_5 = (
        1.930e-3 * fine_sand
        - 3.57e-3 * sand
        + 1.82e-3 * clay
        + 0.410
    )  # fmt: skip

    theta_10 = (
        0.712e-3 * fine_sand
        - 3.83e-3 * sand
        + 2.43e-3 * clay
        + 0.415
    )  # fmt: skip

    theta_30 = (
        0.059e-3 * fine_sand
        - 3.48e-3 * sand
        + 3.21e-3 * clay
        + 0.365
    )  # fmt: skip

    theta_60 = (
        0.003e-3 * fine_sand
        - 3.19e-3 * sand
        + 3.51e-3 * clay
        + 0.330
    )  # fmt: skip

    theta_100 = (
        0.019e-3 * fine_sand
        - 3.02e-3 * sand
        + 3.62e-3 * clay
        + 0.310
    )  # fmt: skip

    theta_500 = (
        0.140e-3 * fine_sand
        - 2.62e-3 * sand
        + 3.75e-3 * clay
        + 0.265
    )  # fmt: skip

    theta_1000 = (
        0.197e-3 * fine_sand
        - 2.44e-3 * sand
        + 3.78e-3 * clay
        + 0.264
    )  # fmt: skip

    theta_1500 = (
        0.254e-3 * fine_sand
        - 2.39e-3 * sand
        + 3.80e-3 * clay
        + 0.239
    )  # fmt: skip

    k_sat = 4.36e-5 * np.exp(-0.1975 * clay)

    return (
        theta_0,
        theta_1,
        theta_5,
        theta_10,
        theta_30,
        theta_60,
        theta_100,
        theta_500,
        theta_1000,
        theta_1500,
        k_sat,
    )


@cython.ufunc
@cython.cfunc
def calc_ptf_kalumba2020_ufunc(
    sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    stoniness: cython.double,
    bulk_density: cython.double,
    depth: cython.double,
    organic_matter: cython.double,
    electrical_conductivity: cython.double,
    ph: cython.double,
    nitrogen_content: cython.double,
    altitude: cython.double,
) -> tuple[
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
    cython.double,
]:
    theta_pf0_0 = (
        1.090
        - 0.073 * sand
        - 0.052 * silt
        - 0.024 * stoniness
        + 0.181 * nitrogen_content
        - 0.360 * electrical_conductivity
        - 0.003 * ph
        - 0.319 * bulk_density
        - 1.17 * np.exp(-4) * altitude
    )

    theta_pf1_0 = (
        0.948
        - 0.101 * sand
        - 0.098 * silt
        - 0.034 * stoniness
        + 0.350 * nitrogen_content
        - 0.340 * electrical_conductivity
        - 0.005 * ph
        - 0.273 * bulk_density
        - 4.83 * np.exp(-5) * altitude
    )

    theta_pf2_0 = (
        2.276
        - 1.781 * sand
        - 1.487 * clay
        - 1.712 * silt
        - 0.022 * stoniness
        + 0.900 * nitrogen_content
        + 0.317 * electrical_conductivity
        - 0.010 * ph
        - 0.056 * bulk_density
        + 3.06 * np.exp(-4) * depth
        - 2.21 * np.exp(-4) * altitude
    )

    theta_pf2_8 = (
        2.610
        - 2.401 * sand
        - 2.026 * clay
        - 2.320 * silt
        - 0.022 * stoniness
        + 0.887 * nitrogen_content
        + 0.595 * electrical_conductivity
        + 0.014 * organic_matter
        + 0.029 * bulk_density
        + 4.17 * np.exp(-4) * depth
        - 2.43 * np.exp(-4) * altitude
    )

    theta_pf3_4 = (
        2.522
        - 2.347 * sand
        - 1.957 * clay
        - 2.282 * silt
        - 0.023 * stoniness
        + 0.787 * nitrogen_content
        + 0.703 * electrical_conductivity
        + 0.016 * organic_matter
        + 0.027 * bulk_density
        + 5.31 * np.exp(-4) * depth
        - 2.30 * np.exp(-4) * altitude
    )

    theta_pf4_2 = (
        1.972
        - 1.811 * sand
        - 1.430 * clay
        - 1.761 * silt
        - 0.023 * stoniness
        + 0.623 * nitrogen_content
        + 0.754 * electrical_conductivity
        + 0.015 * organic_matter
        + 3.81 * np.exp(-4) * depth
        - 1.79 * np.exp(-4) * altitude
    )

    k_sat_mm_per_hour = (
        3.86 * np.exp(2)
        + 1.70 * np.exp(2) * sand
        + 4.83e2 * np.exp(2) * stoniness
        - 4.26 * np.exp(2) * nitrogen_content
        - 2.37 * np.exp(2) * bulk_density
    )
    k_sat = k_sat_mm_per_hour * MM_PER_HOUR_TO_M_PER_SEC

    return theta_pf0_0, theta_pf1_0, theta_pf2_0, theta_pf2_8, theta_pf3_4, theta_pf4_2, k_sat


@cython.ufunc
@cython.cfunc
def calc_ptf_santra2008_ufunc(
    silt: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    soil_organic_carbon: cython.double,
    ph: cython.double,
    altitude: cython.double,
) -> tuple[cython.double, cython.double, cython.double]:
    k_sat_cm_per_day = np.exp(
        8.0963
        - 2.6414 * bulk_density
        - 0.0314 * silt
        - 0.0456 * clay
        + 0.0167 * ph
        + 0.0317 * altitude
    )

    k_sat = k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC

    a_vg = np.exp(
        3.1368
        - 4.0908 * bulk_density
        - 0.0518 * silt
        + 0.0058 * clay
        + 0.2111 * ph
    )  # fmt: skip

    n_vg = (
        1.4399
        + 0.0583 * bulk_density
        - 0.0312 * soil_organic_carbon
        - 0.0017 * silt
        - 0.0023 * clay
        - 0.0247 * ph
    )

    return a_vg, n_vg, k_sat


@cython.ufunc
@cython.cfunc
def calc_ptf_jabro1992_ufunc(
    silt: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
) -> cython.double:
    k_sat_cm_per_hour = 10 ** (
        9.56 - 0.81 * np.log10(silt) - 1.09 * np.log10(clay) - 4.64 * bulk_density
    )
    return k_sat_cm_per_hour * CM_PER_HOUR_TO_M_PER_SEC


@cython.ufunc
@cython.cfunc
def calc_ptf_ramos2023_sscd_ufunc(
    coarse_sand: cython.double,
    fine_sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    depth: cython.double,
) -> tuple[
    cython.double, cython.double, cython.double, cython.double, cython.double, cython.double
]:
    depth_in_m = depth * CM_TO_M
    theta_s = 0.556 - 2.0 * 10e-3 * (coarse_sand + fine_sand) - 2.53 * 10e-4 * depth_in_m
    theta_r = 0.025 + 2.0 * 10e-3 * clay
    a_vg = np.exp(-1.164 - 1.8 * 10e-2 * silt + 1.0 * 10e-2 * clay - 1.0 * 10e-3 * depth_in_m)
    n_vg = 1.417 - 6.0 * 10e-3 * clay + 1.0 * 10e-3 * depth_in_m - 2.0 * 10e-3 * silt
    k_sat_cm_per_day = np.exp(2.329 - 1.1 * 10e-2 * silt)
    k_sat = k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC
    l_vgm = -11.334 + 1.06 * 10e-1 * (coarse_sand + fine_sand)

    return theta_s, theta_r, a_vg, n_vg, k_sat, l_vgm


@cython.ufunc
@cython.cfunc
def calc_ptf_ramos2023_sscgmd_ufunc(
    coarse_sand: cython.double,
    fine_sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    gmd: cython.double,
    gsd: cython.double,
) -> tuple[
    cython.double, cython.double, cython.double, cython.double, cython.double, cython.double
]:
    theta_s = (
        0.3551
        + 7.7 * 10e-4 * coarse_sand
        + 1.98 * 10e-3 * silt
        + 2.95 * 10e-3 * clay
        - 5.01 * 10e-3 * gsd
    )
    theta_r = 0.0103 + 1.5 * 10e-3 * clay + 1.6 * 10e-3 * gsd
    a_vg = np.exp(
        0.3383 - 5.6 * 10e-3 * coarse_sand - 1.05 * 10e-2 * fine_sand - 2.47 * 10e-2 * silt
    )
    n_vg = np.exp(0.00169 + 9.9 * 10e-4 * fine_sand + 1.2 * 10e-3 * silt + 4.56 * 10e-1 * gmd)
    k_sat_cm_per_day = np.exp(
        3.2755 - 1.87 * 10e-2 * fine_sand - 1.32 * 10e-2 * silt - 6.48 * 10e-2 * gsd
    )
    k_sat = k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC
    l_vgm = 0.376 - 1.29 * 10e-1 * silt - 7.3 * 10e-3 * clay - 1.45 * 10e-1 * gsd

    return theta_s, theta_r, a_vg, n_vg, k_sat, l_vgm


@cython.ufunc
@cython.cfunc
def calc_ptf_ramos2023_sscbdgmd_ufunc(
    fine_sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    depth: cython.double,
    bulk_density: cython.double,
    gmd: cython.double,
    gsd: cython.double,
) -> tuple[
    cython.double, cython.double, cython.double, cython.double, cython.double, cython.double
]:
    theta_s = (
        0.883 + 1.46 * 10e-3 * clay - 3.19 * 10e-1 * bulk_density - 1.34 * 10e-4 * depth * CM_TO_M
    )
    theta_r = 0.01 + 1.49 * 10e-3 * clay + 1.62 * 10e-3 * gsd
    a_vg = np.exp(
        0.018
        - 8.55 * 10e-3 * fine_sand
        - 2.40 * 10e-2 * silt
        - 7.98 * 10e-1 * gmd
        - 3.1 * 10e-1 * bulk_density
    )
    n_vg = np.exp(
        0.146
        - 7.50 * 10e-4 * clay
        + 3.16 * 10e-1 * gmd
        - 1.84 * 10e-3 * gsd
        - 2.6 * 10e-2 * bulk_density
    )
    k_sat_cm_per_day = np.exp(
        5.352
        - 1.90 * 10e-2 * fine_sand
        - 1.54 * 10e-2 * silt
        - 9.11 * 10e-3 * clay
        - 3.22 * 10e-2 * gsd
        - 1.411 * bulk_density
    )
    k_sat = k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC
    l_vgm = 0.376 - 1.29 * 10e-1 * silt - 7.3 * 10e-2 * clay - 1.45 * 10e-1 * gsd

    return theta_s, theta_r, a_vg, n_vg, k_sat, l_vgm


@cython.ufunc
@cython.cfunc
def calc_ptf_ramos2023_allfcwp_ufunc(
    fine_sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    gmd: cython.double,
    gsd: cython.double,
    theta_33: cython.double,
    theta_1580: cython.double,
) -> tuple[
    cython.double, cython.double, cython.double, cython.double, cython.double, cython.double
]:
    theta_s = (
        0.754
        + 5.60 * 10e-4 * clay
        + 1.79 * 10e-1 * gmd
        - 2.85 * 10e-1 * bulk_density
        + 2.16 * 10e-1 * theta_33
        + 1.44 * 10e-1 * theta_1580
    )
    theta_r = 0.041 + 1.0 * 10e-3 * gsd - 1.63 * 10e-1 * theta_33 + 4.67 * 10e-1 * theta_1580
    a_vg = np.exp(
        1.66 + 1.99 * 10e-2 * gsd - 1.317 * bulk_density - 8.786 * theta_33 + 8.049 * theta_1580
    )
    n_vg = np.exp(
        0.073
        + 6.27 * 10e-4 * fine_sand
        + 1.01 * 10e-3 * silt
        + 1.21 * 10e-3 * clay
        + 2.33 * 10e-1 * gmd
        - 4.25 * 10e-1 * theta_1580
    )
    k_sat_cm_per_day = np.exp(
        7.178
        - 1.27 * 10e-2 * fine_sand
        - 3.52 * 10e-2 * gsd
        - 2.138 * bulk_density
        - 8.989 * theta_33
        + 6.699 * theta_1580
    )
    k_sat = k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC
    l_vgm = 0.166 - 6.2 * 10e-2 * silt - 23.917 * theta_1580

    return theta_s, theta_r, a_vg, n_vg, k_sat, l_vgm


@cython.ufunc
@cython.cfunc
def calc_ptf_tiwary2014_igp_ufunc(
    sand: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    cation_exchange_capacity: cython.double,
    esp: cython.double,
    emp: cython.double,
) -> tuple[cython.double, cython.double, cython.double, cython.double]:
    w_33 = 2.583 + 0.346 * cation_exchange_capacity + 0.249 * clay + 0.494 * esp
    w_100 = -1.918 + 0.383 * cation_exchange_capacity + 0.228 * clay + 0.361 * esp
    w_1500 = 0.541 + 0.306 * cation_exchange_capacity + 0.146 * esp + 0.058 * emp
    k_sat_mm_per_hour = 4.079 + 0.047 * sand - 0.054 * esp - 2.238 * bulk_density
    k_sat = k_sat_mm_per_hour * MM_PER_HOUR_TO_M_PER_SEC

    return w_33, w_100, w_1500, k_sat


@cython.ufunc
@cython.cfunc
def calc_ptf_tiwary2014_bsr_ufunc(
    clay: cython.double,
    ph: cython.double,
    cation_exchange_capacity: cython.double,
    esp: cython.double,
    emp: cython.double,
    excm: cython.double,
) -> tuple[cython.double, cython.double, cython.double, cython.double]:
    w_33 = 2.583 + 0.346 * cation_exchange_capacity + 0.249 * clay + 0.494 * esp
    w_100 = -1.918 + 0.383 * cation_exchange_capacity + 0.228 * clay + 0.361 * esp
    w_1500 = 0.541 + 0.306 * cation_exchange_capacity + 0.146 * esp + 0.058 * emp
    k_sat_mm_per_hour = 120.637 - 13.094 * ph - 0.102 * clay + 1.151 * excm
    k_sat = k_sat_mm_per_hour * MM_PER_HOUR_TO_M_PER_SEC

    return w_33, w_100, w_1500, k_sat


@cython.ufunc
@cython.cfunc
def calc_ptf_wang2012_ufunc(
    sand: cython.double,
    silt: cython.double,
    clay: cython.double,
    bulk_density: cython.double,
    soil_organic_carbon: cython.double,
    altitude: cython.double,
) -> tuple[cython.double, cython.double, cython.double]:
    soil_organic_carbon_in_g_per_kg = soil_organic_carbon * PERCENTS_TO_G_PER_KG
    sand_lg = np.log10(sand)
    sand_inv = sand**-1
    soil_organic_carbon_inv = soil_organic_carbon_in_g_per_kg**-1
    bulk_density_square = bulk_density**2
    k_sat_cm_per_day = 10 ** (
        1.173
        + 0.038 * silt
        + 0.690 * sand_lg
        + 0.865 * sand_inv
        - 0.030 * bulk_density * silt
        - 0.00000995 * soil_organic_carbon_in_g_per_kg * altitude
    )
    k_sat = k_sat_cm_per_day * CM_PER_DAY_TO_M_PER_SEC
    theta_fc = (
        46.481
        - 4.757 * soil_organic_carbon_in_g_per_kg
        - 14.028 * np.log10(clay)
        - 13.991 * sand_lg
        + 42.261 * np.log10(soil_organic_carbon_in_g_per_kg)
        - 11.763 * sand_inv
        + 19.198 * soil_organic_carbon_inv
        - 5.448 * bulk_density_square
        + 0.044 * soil_organic_carbon_in_g_per_kg**2
        + 1.975 * bulk_density * soil_organic_carbon_in_g_per_kg
    )
    theta_s = (
        98.813
        - 21.555 * bulk_density**-1
        - 39.735 * silt**-1
        - 2.091 * sand_inv
        + 3.247 * soil_organic_carbon_inv
        - 17.096 * bulk_density_square
    )

    return theta_s, theta_fc, k_sat
