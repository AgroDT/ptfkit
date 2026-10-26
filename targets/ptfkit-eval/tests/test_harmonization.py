"""Protect evidence separation and hand-computed transformation boundaries."""

import copy
import math
from typing import cast

import pytest
from ptfkit import get_manifest

from ptfkit_eval.documents import plain
from ptfkit_eval.harmonization import (
    EvidenceTier,
    EvidenceValue,
    benchmark_view,
    carbon_conversion,
    complementary_texture,
    convert_evidence,
    derive_porosity,
    psd_fraction,
    reconstruct_water,
    usda_texture,
)
from ptfkit_eval.harmonized_inputs import resolve_harmonized_input


def measured(value: float, source: str = 'laboratory:1') -> EvidenceValue:
    return EvidenceValue(value, EvidenceTier.STRICT, 'measured', (source,))


def test_log_pressure_interpolation_uses_adjacent_points_and_preserves_exact_observations():
    low, middle, high = measured(0.5, 'a'), measured(0.3, 'b'), measured(0.1, 'c')
    points = [(1, low), (10, middle), (100, high)]
    assert reconstruct_water(points, 10) is middle
    result = reconstruct_water(points, math.sqrt(1000), fitted_alternative=0.21)
    assert result is not None
    assert result.value == pytest.approx(0.2)
    assert result.tier == EvidenceTier.RECONSTRUCTED
    assert result.sources == ('b', 'c')
    details = result.document()['details']
    assert details['neighboring_pressures_kpa'] == [10, 100]
    assert details['interpolation_span_kpa'] == 90
    assert details['interpolation_span_log10'] == 1
    assert details['exact_observation_existed'] is False
    assert details['fitted_family_alternative'] == 0.21
    assert middle.value == 0.3


def test_reconstruction_never_extrapolates_or_uses_zero_in_logarithm():
    points = [(0, measured(0.6)), (1, measured(0.5)), (100, measured(0.1))]
    assert reconstruct_water(points, 0) is points[0][1]
    assert reconstruct_water(points, 0.5) is None
    assert reconstruct_water(points, 101) is None
    with pytest.raises(ValueError, match='unique'):
        reconstruct_water([*points, (1, measured(0.4))], 10)
    with pytest.raises(ValueError, match='bounds'):
        reconstruct_water([(1, measured(50)), (100, measured(10))], 10)


def test_gravimetric_reconstruction_preserves_mass_ratios_above_one():
    points = [(1, measured(2)), (100, measured(1))]
    result = reconstruct_water(points, 10, water_quantity='gravimetric_water_content')
    assert result is not None
    assert result.value == 1.5
    assert result.tier == EvidenceTier.RECONSTRUCTED
    with pytest.raises(ValueError, match='bounds'):
        reconstruct_water(points, 10, water_quantity='volumetric_water_content')


def test_tier_cannot_be_promoted_by_conversion_or_derivation():
    approximate = EvidenceValue(2.0, EvidenceTier.APPROXIMATE, 'assumed_carbon', ('cell:R2',))
    result = carbon_conversion(
        approximate, factor=1.724, direction='oc_to_om', authorization='explicit example relation'
    )
    assert result.value == pytest.approx(3.448)
    assert result.tier == EvidenceTier.APPROXIMATE
    assert benchmark_view([result], strict_eligible=True) == 'exploratory'
    assert benchmark_view([measured(1)]) == 'harmonized'
    assert benchmark_view([measured(1)], strict_eligible=True) == 'strict'
    with pytest.raises(ValueError, match='upgrade'):
        EvidenceValue(3.448, EvidenceTier.DERIVED, 'forged', ('cell:R2',), parents=(approximate,))
    with pytest.raises(ValueError, match='authorization'):
        carbon_conversion(measured(2), factor=1.724, direction='oc_to_om', authorization='')
    converted = convert_evidence(approximate, 'mass_percent', 'mass_fraction')
    assert converted.value == pytest.approx(0.02)
    assert converted.tier == EvidenceTier.APPROXIMATE


def test_deterministic_derivations_retain_formula_and_reject_unknown_basis():
    result = derive_porosity(
        measured(1.3), measured(2.6), basis='fine_earth', unit='gram_per_cubic_centimeter'
    )
    assert result.value == 0.5
    assert result.tier == EvidenceTier.DERIVED
    assert (
        result.document()['details']['formula']
        == 'porosity = 1 - dry_bulk_density / particle_density'
    )
    with pytest.raises(ValueError, match='basis'):
        derive_porosity(measured(1.3), measured(2.6), basis='unspecified', unit='g/cm3')
    closure = complementary_texture(
        measured(40), measured(35), basis='dry_mass_fine_earth', closed=True
    )
    assert closure.value == 25
    with pytest.raises(ValueError, match='closed'):
        complementary_texture(measured(40), measured(35), basis='dry_mass_fine_earth', closed=False)
    with pytest.raises(ValueError, match='exceed'):
        complementary_texture(measured(80), measured(35), basis='dry_mass_fine_earth', closed=True)


@pytest.mark.parametrize(
    ('fractions', 'texture'),
    [
        ((92, 5, 3), 'sand'),
        ((80, 15, 5), 'loamy sand'),
        ((65, 25, 10), 'sandy loam'),
        ((40, 40, 20), 'loam'),
        ((20, 65, 15), 'silt loam'),
        ((5, 90, 5), 'silt'),
        ((60, 10, 30), 'sandy clay loam'),
        ((30, 35, 35), 'clay loam'),
        ((10, 55, 35), 'silty clay loam'),
        ((55, 5, 40), 'sandy clay'),
        ((10, 45, 45), 'silty clay'),
        ((25, 25, 50), 'clay'),
    ],
)
def test_usda_triangle_interior_classes(fractions: tuple, texture: str):
    # USDA Soil Survey Manual (2017), Chapter 3, Figure 3-7 and class definitions.
    result = usda_texture(
        *(measured(value) for value in fractions),
        basis='dry_mass_fine_earth',
        boundaries_um=(2, 50, 2000),
    )
    assert result.value == texture
    assert result.tier == EvidenceTier.DERIVED


def test_psd_distinguishes_exact_rebin_resolved_interpolation_and_broad_assumption():
    cumulative = [
        (0, measured(0)),
        (1, measured(10)),
        (5, measured(30)),
        (50, measured(60)),
        (2000, measured(100)),
    ]
    exact = psd_fraction(cumulative, 50, 2000, basis='dry_mass_fine_earth')
    assert exact is not None
    assert exact.value == 40
    assert exact.tier == EvidenceTier.DERIVED
    resolved = psd_fraction(cumulative, 0, math.sqrt(5), basis='dry_mass_fine_earth')
    assert resolved is not None
    assert resolved.value == pytest.approx(20)
    assert resolved.tier == EvidenceTier.RECONSTRUCTED
    assert psd_fraction(cumulative, 0, 10, basis='dry_mass_fine_earth') is None
    broad = psd_fraction(
        cumulative, 0, math.sqrt(250), basis='dry_mass_fine_earth', allow_approximate=True
    )
    assert broad is not None
    assert broad.value == pytest.approx(45)
    assert broad.tier == EvidenceTier.APPROXIMATE
    assert benchmark_view([broad]) == 'exploratory'
    with pytest.raises(ValueError, match='monotone'):
        psd_fraction([(1, measured(20)), (5, measured(10))], 1, 5, basis='dry_mass_fine_earth')


def test_predictor_resolution_converts_units_without_changing_boundaries_or_method():
    manifest = cast('dict', plain(get_manifest()))
    function = next(
        f for f in manifest['functions'] if f['id'] == 'calc_ptf_gunarathna2019_vwc10_set1'
    )
    binding = function['inputs'][0]
    measurement = copy.deepcopy(binding['measurement'])
    measurement['unit'] = 'mass_fraction'
    result, blockers = resolve_harmonized_input(
        binding, measured(0.5), measurement, manifest=manifest
    )
    assert blockers == ()
    assert result is not None
    assert result.value == 50
    assert result.tier == EvidenceTier.CONVERTED
    measurement['particle_size']['upper']['value'] = 1000
    result, blockers = resolve_harmonized_input(
        binding, measured(0.5), measurement, manifest=manifest
    )
    assert result is None
    assert 'predictor_particle_size_mismatch' in blockers
    measurement = copy.deepcopy(binding['measurement'])
    measurement['method'] = 'unknown'
    result, blockers = resolve_harmonized_input(
        binding, measured(50), measurement, manifest=manifest
    )
    assert result is None
    assert 'predictor_method_mismatch' in blockers


def test_trace_freezes_nested_details_and_is_independent_of_caller_mutation():
    source = {'unit': 'mass_percent'}
    value = EvidenceValue(
        50, EvidenceTier.STRICT, 'measured', ('cell:P2',), (('measurement', source),)
    )
    source['unit'] = 'mass_fraction'
    assert value.document()['details']['measurement']['unit'] == 'mass_percent'
