import math

import pytest

from ptfkit_eval import (
    BlendTransition,
    Contribution,
    HardSwitchTransition,
    Interval,
    RangeGatedRouter,
    RoutingError,
)


def test_blends_over_log_pressure_and_routes_outside_the_overlap():
    router = RangeGatedRouter(
        members={
            'wet': Interval(0.1, 33.0),
            'dry': Interval(10.0, 1500.0),
        },
        transitions=(BlendTransition('wet', 'dry', Interval(10.0, 33.0), weighting='linear'),),
        transform='log10',
    )

    assert router.route(1.0) == (Contribution('wet', 1.0),)
    assert router.route(10.0) == (Contribution('wet', 1.0), Contribution('dry', 0.0))
    midpoint = router.route(math.sqrt(330.0))
    assert midpoint[0].weight == pytest.approx(0.5)
    assert midpoint[1].weight == pytest.approx(0.5)
    assert router.route(33.0) == (Contribution('wet', 0.0), Contribution('dry', 1.0))
    assert router.route(100.0) == (Contribution('dry', 1.0),)


def test_rejects_a_hard_switch_outside_the_member_overlap():
    with pytest.raises(ValueError, match='hard-switch value'):
        RangeGatedRouter(
            members={
                'wet': Interval(0.1, 10.0),
                'dry': Interval(20.0, 1500.0),
            },
            transitions=(HardSwitchTransition('wet', 'dry', 10.0, 'right'),),
        )


def test_hard_switch_has_an_explicit_boundary_owner():
    router = RangeGatedRouter(
        members={
            'wet': Interval(0.1, 33.0),
            'dry': Interval(10.0, 1500.0),
        },
        transitions=(HardSwitchTransition('wet', 'dry', 20.0, 'right'),),
    )

    assert router.route(19.0) == (Contribution('wet', 1.0),)
    assert router.route(20.0) == (Contribution('dry', 1.0),)
    assert router.route(21.0) == (Contribution('dry', 1.0),)


def test_rejects_a_gap_when_members_have_no_transition_overlap():
    router = RangeGatedRouter(
        members={
            'wet': Interval(0.1, 10.0, upper_inclusive=False),
            'dry': Interval(20.0, 1500.0),
        },
        transitions=(),
    )

    with pytest.raises(RoutingError, match='No composite member covers'):
        router.route(15.0)


def test_rejects_a_blend_interval_outside_both_member_ranges():
    with pytest.raises(ValueError, match='contained in both member intervals'):
        RangeGatedRouter(
            members={
                'wet': Interval(0.1, 20.0),
                'dry': Interval(10.0, 1500.0),
            },
            transitions=(BlendTransition('wet', 'dry', Interval(10.0, 33.0)),),
        )


def test_rejects_nonpositive_ranges_on_a_log_axis():
    with pytest.raises(ValueError, match='positive member intervals'):
        RangeGatedRouter(
            members={
                'wet': Interval(-1.0, 33.0),
                'dry': Interval(10.0, 1500.0),
            },
            transitions=(BlendTransition('wet', 'dry', Interval(10.0, 33.0)),),
            transform='log10',
        )


def test_rejects_multiple_routing_rules_for_the_same_member_pair():
    with pytest.raises(ValueError, match='Multiple transitions'):
        RangeGatedRouter(
            members={
                'wet': Interval(0.1, 33.0),
                'dry': Interval(10.0, 1500.0),
            },
            transitions=(
                HardSwitchTransition('wet', 'dry', 20.0, 'right'),
                BlendTransition('wet', 'dry', Interval(10.0, 33.0)),
            ),
        )
