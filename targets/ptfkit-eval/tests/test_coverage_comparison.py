"""Protect coverage, identical-coordinate comparisons and source-held-out gates."""

import math

import pytest
from evaluation.experiments.meta_v3_3 import model_selection as original
from evaluation.experiments.meta_v3_3 import pointwise_wrc as wrc
from evaluation.experiments.meta_v3_3.coverage_comparison import compare, deduplicate
from evaluation.experiments.meta_v3_3.coverage_reports import combined_coverage


def point(source: str, sample: str, pressure: float, error: float = 0) -> dict:
    return {
        'source_id': source,
        'sample_id': sample,
        'pressure_kpa': pressure,
        'basis': 'volumetric_water_content',
        'observed': 0.2,
        'predicted': 0.2 + error,
    }


def indexed(points: list[dict]) -> dict:
    return {wrc.identity(p): p for p in points}


def test_different_maximum_supports_do_not_turn_a_small_intersection_into_a_leader():
    ledger = [point('x', 'a', h) for h in (1, 10, 100)]
    indices = {
        'a': indexed([point('x', 'a', 1, 0.4), point('x', 'a', 10, 0.1)]),
        'b': indexed([point('x', 'a', 10, 0.2), point('x', 'a', 100, 0)]),
    }
    result = compare(indices, ledger, wrc.score, wrc.identity)
    assert result['maximum_points'] == 2
    assert result['matched_cohort']['points'] == 1
    assert result['matched_ranking'][0]['sample_balanced_rmse'] == pytest.approx(0.1)
    assert result['qualification'] == 'maximum_coverage_models_have_different_supports'
    assert result['leader'] is None


def test_source_sensitive_pooled_winner_is_not_called_an_established_leader():
    ledger = [point(s, s, 10) for s in ('x', 'y', 'z')]
    indices = {
        name: indexed([point(s, s, 10, e) for s, e in zip(('x', 'y', 'z'), errors, strict=True)])
        for name, errors in [('a', (0, 0.3, 0.3)), ('b', (0.2, 0, 0))]
    }
    result = compare(indices, ledger, wrc.score, wrc.identity)
    assert result['coverage_candidate']['model'] == 'b'
    assert result['coverage_candidate']['sample_balanced_rmse'] == pytest.approx(
        math.sqrt(0.04 / 3)
    )
    assert result['source_sensitivity'][0]['training_choice'] == 'b'
    assert result['source_sensitivity'][0]['held_out_best'] == 'a'
    assert result['qualification'] == 'source_sensitive_no_established_leader'
    assert result['leader'] is None


def test_full_ledger_leader_requires_common_coverage_and_consistency_on_every_source():
    ledger = [point(s, s, 10) for s in ('x', 'y', 'z')]
    indices = {
        name: indexed([point(s, s, 10, e) for s in ('x', 'y', 'z')])
        for name, e in [('a', 0.1), ('b', 0.2)]
    }
    result = compare(indices, ledger, wrc.score, wrc.identity)
    assert result['full_ledger_leader']['model'] == 'a'
    assert result['held_out_selection_score']['sample_balanced_rmse'] == pytest.approx(0.1)
    assert len(result['source_sensitivity']) == 3
    extended = compare(indices, [*ledger, point('q', 'q', 10)], wrc.score, wrc.identity)
    assert extended['leader']['model'] == 'a'
    assert extended['full_ledger_leader'] is None
    assert extended['uncovered_points_at_maximum'] == 1


def test_one_source_or_a_numerical_tie_never_establishes_a_leader():
    ledger = [point('x', 'a', 10), point('x', 'b', 10)]
    indices = {
        name: indexed([point('x', s, 10, e) for s in ('a', 'b')])
        for name, e in [('a', 0.1), ('b', 0.2)]
    }
    result = compare(indices, ledger, wrc.score, wrc.identity)
    assert result['qualification'] == 'insufficient_independent_sources'
    assert result['leader'] is None
    indices['b'] = indices['a']
    result = compare(indices, ledger, wrc.score, wrc.identity)
    assert result['qualification'] == 'no_unique_matched_accuracy_leader'
    assert result['coverage_candidate'] is None


def test_comparison_rejects_changed_observations_on_an_otherwise_identical_coordinate():
    measured = point('x', 'a', 10)
    with pytest.raises(ValueError, match='experimental coordinate and target'):
        compare(
            {'a': indexed([{**measured, 'observed': 0.3}])}, [measured], wrc.score, wrc.identity
        )


def test_combined_coverage_counts_bases_without_pooling_their_errors():
    volume = point('x', 'a', 10)
    mass = {**point('y', 'b', 10), 'basis': 'gravimetric_water_content', 'observed': 0.1}
    result = combined_coverage([{**volume, 'function': 'a'}], [volume, mass], set())
    assert result['total_points'] == 2
    assert result['ranking'][0]['points'] == 1
    assert result['ranking'][0]['missing_points'] == 1
    assert result['ranking'][0]['coverage'] == 0.5
    assert result['ranking'][0]['volumetric_points'] == 1
    assert result['ranking'][0]['gravimetric_points'] == 0
    assert not result['single_general_function_covers_all_points']
    assert 'sample_balanced_rmse' not in result['ranking'][0]


def test_legacy_basis_conversion_is_opt_in_and_requires_actual_same_record_density(
    monkeypatch: pytest.MonkeyPatch,
):
    function = {
        'id': 'controlled',
        'inputs': [],
        'source': 'controlled',
        'specification': 'controlled.yaml',
        'status': 'implemented',
    }
    target = {'quantity': 'volumetric_water_content', 'adapter': 'explicit_vg_mualem_signature_v1'}
    monkeypatch.setattr(original, 'candidate_targets', lambda *_: ([target], []))
    monkeypatch.setattr(original, 'families', lambda *_: [])
    monkeypatch.setattr(original, 'resolve_selection_inputs', lambda *_a, **_kw: ({}, {}, [], 'E5'))
    monkeypatch.setattr(original.semantic, 'prediction', lambda *_: 0.28)
    observation = {
        **point('x', 'a', 10),
        'basis': 'gravimetric_water_content',
        'id': 'target',
        'observed': 0.2,
    }
    row = {
        'source_id': 'x',
        'sample_id': 'a',
        'worksheet': 'master',
        'row': 2,
        'sheet_index': 0,
        'values': {'Q': 1.4},
        'value_cells': {'Q': ['master!Q2']},
        'properties': {},
    }
    context = {'catalog': [function], 'datasets': [], 'old_registration': {}}
    old, _ = original.predict(context, [observation], [row])
    assert old == []
    predictions, _ = original.predict(
        context, [observation], [row], allow_water_basis_conversion=True
    )
    assert len(predictions) == 1
    assert predictions[0]['predicted'] == pytest.approx(0.2)
    assert predictions[0]['water_basis_conversion']['sources'] == ['master!Q2']
    row['formulas'] = {'Q': '=(1.4+1.59)/2'}
    calculated, _ = original.predict(
        context, [observation], [row], allow_water_basis_conversion=True
    )
    assert calculated == []
    row['formulas'] = {}
    row['values']['Q'] = None
    missing, audit = original.predict(
        context, [observation], [row], allow_water_basis_conversion=True
    )
    assert missing == []
    assert audit[0]['failure_counts']['missing_same_record_density_for_water_basis_conversion'] == 1


def test_overlapping_native_paths_are_counted_once_and_conflicts_are_rejected():
    first = {**point('x', 'a', 10), 'function': 'same'}
    duplicate = {**first, 'route_type': 'recovered_inputs'}
    retained, count = deduplicate([first, duplicate], wrc.identity)
    assert retained == [first]
    assert count == 1
    with pytest.raises(ValueError, match='execution paths disagree'):
        deduplicate([first, {**duplicate, 'predicted': 0.3}], wrc.identity)
