import copy
from typing import TYPE_CHECKING, cast

import pytest
from ptfkit import get_manifest

from ptfkit_eval import RunInputTrace, bind_retention_inputs


if TYPE_CHECKING:
    from collections.abc import Mapping


SAND_FEATURE: dict[str, object] = {
    'id': 'sand_fraction',
    'kind': 'numeric',
    'value': 0.5,
    'origin': 'measured',
    'review_status': 'confirmed',
    'source_cells': ('soil!A5',),
    'measurement': {
        'quantity': 'particle_mass_fraction',
        'unit': 'mass_fraction',
        'basis': {'material': 'fine_earth', 'denominator': 'dry_mass'},
        'method': 'sieve_analysis',
        'conditions': (),
        'particle_size': {
            'unit': 'micrometer',
            'lower': {'value': 50.0, 'inclusive': True},
            'upper': {'value': 2000.0, 'inclusive': False},
        },
    },
}


def _bind(feature: dict[str, object]) -> RunInputTrace:
    manifest = get_manifest()
    functions = cast('tuple[Mapping[str, object], ...]', manifest['functions'])
    function = next(
        item for item in functions if item['id'] == 'calc_ptf_gunarathna2019_vwc10_set1'
    )
    return bind_retention_inputs(
        function, {'features': (feature,)}, {'sand': 'sand_fraction'}, manifest=manifest
    )[0]


def test_converts_quantity_compatible_fraction_and_retains_raw_value_and_cells():
    trace = _bind(copy.deepcopy(SAND_FEATURE))

    assert trace.raw_value == 0.5
    assert trace.value == pytest.approx(50.0)
    assert (trace.source_unit, trace.target_unit) == ('mass_fraction', 'mass_percent')
    assert trace.source_cells == ('soil!A5',)
    assert trace.compatibility == 'unit_converted'
    assert trace.reasons == ()
    assert trace.reported_applicability == 'not_assessed'


@pytest.mark.parametrize(
    ('change', 'code'),
    [
        ({'quantity': 'volumetric_water_content'}, 'quantity_mismatch'),
        ({'method': 'laser_diffraction'}, 'method_mismatch'),
        ({'basis': {'material': 'whole_soil', 'denominator': 'dry_mass'}}, 'basis_mismatch'),
        ({'unit': 'volume_fraction'}, 'unit_mismatch'),
        ({'particle_size': None}, 'particle_boundary_mismatch'),
        ({'conditions': ({'quantity': 'temperature', 'value': 20},)}, 'conditions_mismatch'),
    ],
)
def test_measurement_names_and_convertible_numbers_do_not_override_physical_incompatibility(
    change: dict[str, object],
    code: str,
):
    feature = copy.deepcopy(SAND_FEATURE)
    cast('dict[str, object]', feature['measurement']).update(change)
    trace = _bind(feature)

    assert trace.compatibility == 'incompatible'
    assert code in trace.reasons
    assert trace.value is None


@pytest.mark.parametrize(
    ('value', 'eligible'), [(0.052, True), (0.99, True), (0.051, False), (0.991, False)]
)
def test_checks_domain_after_conversion(value: float, *, eligible: bool):
    trace = _bind({**copy.deepcopy(SAND_FEATURE), 'value': value})

    assert trace.value == pytest.approx(value * 100)
    assert (not trace.reasons) is eligible
    if not eligible:
        assert trace.reasons == ('outside_computational_domain',)


@pytest.mark.parametrize(
    ('change', 'code'),
    [
        ({'value': None}, 'missing_input'),
        ({'review_status': 'blocked'}, 'unreviewed_input'),
        ({'origin': 'estimated'}, 'estimated_input_not_allowed'),
        ({'origin': 'derived'}, 'unverified_derivation'),
    ],
)
def test_unreviewed_missing_and_unverified_values_are_not_promoted(
    change: dict[str, object],
    code: str,
):
    trace = _bind({**copy.deepcopy(SAND_FEATURE), **change})
    assert trace.reasons == (code,)
    assert trace.compatibility == 'incompatible'
