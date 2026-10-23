import pytest

from ptfkit_eval import ParticleSizeInterval, exact_particle_size_cover


def _interval(
    lower: float | None,
    upper: float | None,
    *,
    lower_inclusive: bool = False,
    upper_inclusive: bool = False,
) -> ParticleSizeInterval:
    return ParticleSizeInterval(
        lower=lower,
        upper=upper,
        lower_inclusive=lower_inclusive,
        upper_inclusive=upper_inclusive,
    )


BELOW_TWO = _interval(None, 2)


def test_accepts_direct_or_exactly_partitioned_particle_interval():
    below_one = _interval(None, 1)
    one_to_two = _interval(1, 2, lower_inclusive=True)
    direct = _interval(None, 2)

    assert exact_particle_size_cover(BELOW_TWO, (below_one, one_to_two)) == (0, 1)
    assert exact_particle_size_cover(BELOW_TWO, (below_one, one_to_two, direct)) == (2,)


def test_does_not_substitute_below_one_micrometre_for_below_two():
    below_one = _interval(None, 1)

    assert exact_particle_size_cover(BELOW_TWO, (below_one,)) is None


@pytest.mark.parametrize(
    ('below_one', 'one_to_two'),
    [
        (_interval(None, 1), _interval(1, 2)),
        (_interval(None, 1), _interval(1.0001, 2, lower_inclusive=True)),
        (_interval(None, 1), _interval(0.9999, 2, lower_inclusive=True)),
        (
            _interval(None, 1, upper_inclusive=True),
            _interval(1, 2, lower_inclusive=True),
        ),
    ],
)
def test_rejects_boundary_gaps_and_overlaps(
    below_one: ParticleSizeInterval, one_to_two: ParticleSizeInterval
):
    assert exact_particle_size_cover(BELOW_TWO, (below_one, one_to_two)) is None


@pytest.mark.parametrize(
    ('lower', 'upper'),
    [(-1, 2), (2, 2), (3, 2), (float('nan'), 2), (0, float('inf'))],
)
def test_rejects_invalid_particle_intervals(lower: float, upper: float):
    with pytest.raises(ValueError, match='Particle-size'):
        _interval(lower, upper, lower_inclusive=True)
