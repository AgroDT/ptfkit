import math
from dataclasses import replace

import pytest

from ptfkit_eval import RetentionComparison, RetentionMetricsError, summarize_retention_errors


POINT = RetentionComparison('source', 'sample', 10.0, 0.5, 0.375)


def test_weights_samples_equally_and_takes_square_root_after_aggregation():
    summary = summarize_retention_errors(
        [
            POINT,
            replace(POINT, suction_kpa=100, predicted=0.875),
            replace(POINT, sample_id='other', predicted=0.25),
        ]
    )

    assert (summary.source_count, summary.sample_count, summary.point_count) == (1, 2, 3)
    # Sample errors are [-1/8, 3/8] and [-1/4], each sample carrying half the mass.
    assert summary.metrics.mean_error == pytest.approx(-1 / 16)
    assert summary.metrics.mean_absolute_error == pytest.approx(1 / 4)
    assert summary.metrics.root_mean_squared_error == pytest.approx(math.sqrt(18) / 16)
    assert summary.metrics.median_absolute_error == pytest.approx(1 / 4)
    sample = summary.samples[1]
    assert (sample.source_id, sample.sample_id, sample.point_count) == ('source', 'sample', 2)
    assert (sample.minimum_suction_kpa, sample.maximum_suction_kpa) == (10, 100)
    assert sample.metrics.mean_error == pytest.approx(1 / 8)
    assert sample.metrics.mean_absolute_error == pytest.approx(1 / 4)
    assert sample.metrics.root_mean_squared_error == pytest.approx(math.sqrt(5) / 8)
    assert sample.metrics.median_absolute_error == pytest.approx(1 / 4)


def test_dense_resampling_of_the_same_error_distribution_preserves_sample_weight():
    sparse = [POINT, replace(POINT, sample_id='other', predicted=0.75)]
    dense = [*sparse, *(replace(POINT, suction_kpa=float(axis)) for axis in range(11, 50))]

    assert summarize_retention_errors(dense).metrics == summarize_retention_errors(sparse).metrics


def test_source_local_identifiers_do_not_merge_and_order_does_not_change_results():
    points = [POINT, replace(POINT, source_id='another', predicted=0.75)]
    summary = summarize_retention_errors(iter(points))

    assert (summary.source_count, summary.sample_count) == (2, 2)
    assert [sample.source_id for sample in summary.samples] == ['another', 'source']
    assert summary == summarize_retention_errors(reversed(points))
    assert summary.metrics.mean_error == pytest.approx(1 / 16)
    assert summary.metrics.median_absolute_error == pytest.approx(3 / 16)


def test_keeps_finite_unphysical_predictions_without_clipping():
    summary = summarize_retention_errors([replace(POINT, predicted=-0.25)])

    assert summary.metrics.mean_error == pytest.approx(-0.75)
    assert summary.metrics.mean_absolute_error == pytest.approx(0.75)
    assert summary.metrics.root_mean_squared_error == pytest.approx(0.75)
    assert summary.metrics.median_absolute_error == pytest.approx(0.75)


@pytest.mark.parametrize(
    'point',
    [
        replace(POINT, source_id=' '),
        replace(POINT, sample_id=''),
        replace(POINT, suction_kpa=-1),
        replace(POINT, suction_kpa=math.inf),
        replace(POINT, observed=math.nan),
        replace(POINT, observed=-0.01),
        replace(POINT, observed=1.01),
        replace(POINT, predicted=math.inf),
        replace(POINT, predicted=1e308),
        replace(POINT, observed=True),
        replace(POINT, profile_id=' '),
    ],
)
def test_rejects_invalid_points_instead_of_silently_changing_the_cohort(point: RetentionComparison):
    with pytest.raises(RetentionMetricsError):
        summarize_retention_errors([POINT, point])


def test_rejects_duplicate_pressure_even_when_values_differ():
    with pytest.raises(RetentionMetricsError, match='Duplicate'):
        summarize_retention_errors([POINT, replace(POINT, predicted=0.75)])


def test_rejects_empty_cohorts():
    with pytest.raises(RetentionMetricsError):
        summarize_retention_errors([])
