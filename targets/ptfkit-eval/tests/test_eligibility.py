import math
from typing import cast

import pytest

from ptfkit_eval import (
    ComputationalDomainError,
    DomainBound,
    assess_computational_domain,
)


def _measurement(
    lower: tuple[float, bool] | None,
    upper: tuple[float, bool] | None,
) -> dict[str, object]:
    return {
        'computational_domain': {
            'lower': None if lower is None else {'value': lower[0], 'inclusive': lower[1]},
            'upper': None if upper is None else {'value': upper[0], 'inclusive': upper[1]},
        }
    }


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (5.199, False),
        (5.2, True),
        (50.0, True),
        (99.0, True),
        (99.001, False),
    ],
)
def test_assesses_the_inclusive_gunarathna_sand_domain(value: float, expected: bool):
    decision = assess_computational_domain(value, _measurement((5.2, True), (99.0, True)))

    assert decision.value == value
    assert decision.within is expected
    assert decision.lower == DomainBound(5.2, True)
    assert decision.upper == DomainBound(99.0, True)


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        (-1.0, False),
        (0.0, False),
        (0.5, True),
        (1.0, False),
        (2.0, False),
    ],
)
def test_honors_exclusive_boundaries(value: float, expected: bool):
    decision = assess_computational_domain(value, _measurement((0.0, False), (1.0, False)))

    assert decision.within is expected


def test_supports_unbounded_and_one_sided_domains():
    absent = assess_computational_domain(-100.0, {})
    lower_only = assess_computational_domain(0.0, _measurement((0.0, True), None))
    upper_only = assess_computational_domain(10.0, _measurement(None, (10.0, False)))

    assert absent.within is True
    assert (absent.lower, absent.upper) == (None, None)
    assert lower_only.within is True
    assert upper_only.within is False


@pytest.mark.parametrize(
    'domain',
    [
        [],
        {'lower': None},
        {'lower': 0.0, 'upper': None},
        {'lower': {'value': 0.0, 'inclusive': 'yes'}, 'upper': None},
        {'lower': {'value': math.inf, 'inclusive': True}, 'upper': None},
        {
            'lower': {'value': 2.0, 'inclusive': True},
            'upper': {'value': 1.0, 'inclusive': True},
        },
        {
            'lower': {'value': 1.0, 'inclusive': False},
            'upper': {'value': 1.0, 'inclusive': True},
        },
    ],
)
def test_rejects_malformed_or_empty_domains(domain: object):
    with pytest.raises(ComputationalDomainError):
        assess_computational_domain(0.5, {'computational_domain': domain})


@pytest.mark.parametrize('value', [True, math.nan, math.inf, -math.inf])
def test_rejects_non_finite_candidate_values(value: object):
    with pytest.raises(ComputationalDomainError, match='finite number'):
        assess_computational_domain(cast('float', value), {})
