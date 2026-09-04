from _helpers import is_close


def test_comparator_accepts_below_and_rejects_above_tolerance():
    expected = 2.0
    tolerance = 1e-12 + 1e-5 * abs(expected)

    assert is_close(expected + tolerance * 0.5, expected)
    assert not is_close(expected + tolerance * 2.0, expected)


def test_comparator_adds_published_precision_tolerance():
    assert is_close(1.244, 1.24, 0.005)
