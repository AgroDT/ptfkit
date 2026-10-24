import math
import runpy
from pathlib import Path

import numpy as np
import pytest


def test_retention_coverage_generator_has_independent_family_specific_values():
    script = (
        Path(__file__).resolve().parents[3]
        / 'evaluation/experiments/retention_coverage/calibrate.py'
    )
    namespace = runpy.run_path(str(script))
    mean = namespace['mean_curve']
    index = list(namespace['AXIS']).index(10)
    for family, expected in (
        ('van_genuchten_mualem_v1', 0.1 + 0.4 / math.sqrt(2)),
        ('van_genuchten_m1_v1', 0.3),
        ('brooks_corey_v1', 0.5),
        ('clapp1978_gradual_air_entry_v1', 0.5 / 10**0.25),
    ):
        curve = mean(family, 0.5)
        assert curve[0] == pytest.approx(0.5)
        assert curve[index] == pytest.approx(expected)
    between = mean('brooks_corey_v1', 0.5, axis=np.array([0, 7.5, 30]), air_entry=7.5)
    assert between == pytest.approx([0.5, 0.5, 0.3])


def test_retention_coverage_keeps_failures_and_coverage_denominators():
    script = (
        Path(__file__).resolve().parents[3]
        / 'evaluation/experiments/retention_coverage/calibrate.py'
    )
    calibrate = runpy.run_path(str(script))['calibrate']
    output = calibrate(repetitions=1, seed=17)
    assert output == calibrate(repetitions=1, seed=17)
    assert len(output['records']) == len(output['summaries']) == 8
    assert {item['truth'] for item in output['summaries']} == {0.3, 0.5}
    for summary in output['summaries']:
        counts = summary['counts']
        assert counts['generated'] == 1
        assert (
            counts.get('fitted', 0)
            + counts.get('failed', 0)
            + counts.get('invalid_physical_sample', 0)
            == 1
        )
        assert counts.get('assessed', 0) + counts.get('unavailable', 0) == counts.get('fitted', 0)
        assert 0 <= counts.get('covered', 0) <= counts.get('assessed', 0)
    assert any(item.get('fit', {}).get('status') == 'failed' for item in output['records'])
