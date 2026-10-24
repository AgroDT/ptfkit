import json
import math
import runpy
from pathlib import Path

import pytest


def _namespace() -> dict:
    return runpy.run_path(
        str(
            Path(__file__).resolve().parents[3]
            / 'evaluation/experiments/retention_coverage/expanded.py'
        )
    )


def test_coverage_statistics_have_independent_binomial_and_interval_oracles():
    statistics = _namespace()['coverage_statistics']
    result = statistics(9, 10, 34)
    assert result['conditional_coverage'] == 0.9
    assert result['monte_carlo_standard_error'] == pytest.approx(math.sqrt(0.9 * 0.1 / 10))
    assert result['undercoverage_p_value'] == pytest.approx(1 - 0.95**10)
    assert result['familywise_test_threshold'] == pytest.approx(0.05 / 34)
    assert not result['adequacy_established']
    perfect = statistics(10, 10, 34)
    assert perfect['simulation_probability_interval'] == pytest.approx([0.025**0.1, 1])
    empty_successes = statistics(0, 10, 34)
    assert empty_successes['undercoverage_p_value'] == pytest.approx(0.05**10, rel=1e-12, abs=0)
    assert empty_successes['undercoverage_flag']
    assert empty_successes['simulation_probability_interval'] == pytest.approx([0, 1 - 0.025**0.1])
    assert statistics(0, 0, 34)['status'] == 'no_assessed_regions'
    with pytest.raises(ValueError, match='counts'):
        statistics(11, 10, 34)


def test_expanded_study_resumes_exact_cells_and_rejects_corrupt_artifacts(tmp_path: Path):
    namespace = _namespace()
    script = (
        Path(__file__).resolve().parents[3]
        / 'evaluation/experiments/retention_coverage/expanded-plan.json'
    )
    plan = json.loads(script.read_bytes())
    cell = next(cell for cell in plan['cells'] if cell['truth'] == 0.5)
    cell['repetitions'] = 2
    plan['cells'], plan['comparison_count'] = [cell], 1
    path = tmp_path / 'plan.json'
    path.write_text(json.dumps(plan), encoding='utf-8')
    output = tmp_path / 'artifacts'
    first = namespace['run_study'](path, output)
    before = {file.name: file.read_bytes() for file in output.iterdir()}
    assert first['summaries'][0]['counts']['generated'] == 2
    assert namespace['run_study'](path, output) == first
    assert {file.name: file.read_bytes() for file in output.iterdir()} == before
    cell_path = output / f'{cell["id"]}.json'
    envelope = json.loads(cell_path.read_bytes())
    envelope['payload']['records'][0]['repetition'] = 999
    cell_path.write_text(json.dumps(envelope), encoding='utf-8')
    with pytest.raises(ValueError, match='resumed cell'):
        namespace['run_study'](path, output)


def test_study_cell_streams_are_distinct_and_independent_of_execution_order():
    namespace = _namespace()
    directory = Path(__file__).resolve().parents[3] / 'evaluation/experiments/retention_coverage'
    plan = json.loads((directory / 'expanded-plan.json').read_bytes())
    first = dict(next(cell for cell in plan['cells'] if cell['truth'] == 0.5))
    first['repetitions'] = 1
    second = {**first, 'id': first['id'] + '__independent'}
    generator = runpy.run_path(str(directory / 'calibrate.py'))
    run = namespace['_run_cell']
    first_then = run(first, {}, plan['seed'], generator)
    second_then = run(second, {}, plan['seed'], generator)
    assert run(second, {}, plan['seed'], generator) == second_then
    assert run(first, {}, plan['seed'], generator) == first_then
    assert (
        first_then['records'][0]['fit']['observations']
        != second_then['records'][0]['fit']['observations']
    )
