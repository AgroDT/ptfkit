import runpy
from fractions import Fraction
from pathlib import Path

import pytest


@pytest.mark.parametrize('size', [1, 3])
def test_exact_conditional_risk_coverage_is_simultaneous_and_nonvacuous(size: int):
    script = (
        Path(__file__).resolve().parents[3] / 'evaluation/experiments/conditional_risk/calibrate.py'
    )
    result = runpy.run_path(str(script))['calibrate'](groups_per_fold=20, high_group_size=size)
    assert len(result['cases']) == 441
    assert sum(Fraction(case['probability']) for case in result['cases']) == 1
    assert Fraction(result['simultaneous_coverage_probability']) >= Fraction(19, 20)
    assert Fraction(result['mixture_coverage_probability']) >= Fraction(19, 20)
    # A method always returning the full prior range would pass coverage alone.
    assert Fraction(result['nonvacuous_interval_probability']) > Fraction(1, 2)
    for case in result['cases']:
        first, second = case['high_group_counts']
        # Independent rational oracle for the model trained on the opposite fold.
        constants = [Fraction(count * size, count * size + 20 - count) for count in (second, first)]
        risks = [(constant**2 + size * (1 - constant) ** 2) / (1 + size) for constant in constants]
        assert [Fraction(value) for value in case['conditional_fold_risks']] == risks
        assert Fraction(case['true_equal_fold_mean_risk']) == sum(risks) / 2
    assert result['target'] == 'equal_fold_mean_conditional_sample_risk'
