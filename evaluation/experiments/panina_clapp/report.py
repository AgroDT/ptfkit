"""Publish a descriptive decision report from the verified Panina pilot artifacts."""

# ruff: noqa: INP001 - Standalone research entry point.

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from ptfkit_eval import read_retention_run_report
from ptfkit_eval.documents import canonical_json, document_hash


def _approximation_summary(path: Path, dataset: dict, dataset_bytes: bytes) -> dict:
    document = json.loads(path.read_bytes())
    if (
        document['dataset'] != dataset
        or document['dataset_sha256'] != document_hash(dataset)
        or document['dataset_file_sha256'] != hashlib.sha256(dataset_bytes).hexdigest()
    ):
        message = 'Approximation fits must use the exact evaluated dataset.'
        raise ValueError(message)
    families = {
        'van_genuchten_mualem_v1',
        'van_genuchten_m1_v1',
        'brooks_corey_v1',
        'clapp1978_gradual_air_entry_v1',
    }
    expected = {
        (sample['source_id'], sample['sample_id'], family)
        for sample in dataset['samples']
        for family in families
    }
    identities = [
        (record['source_id'], record['sample_id'], record['fit']['plan']['family_id'])
        for record in document['results']
    ]
    if set(identities) != expected or len(identities) != len(expected):
        message = (
            'Approximation fits require every selected sample and all four families exactly once.'
        )
        raise ValueError(message)
    rows = []
    for record in document['results']:
        fit = record['fit']
        observations = [
            {
                'reference': point['id'],
                'suction_kpa': point['suction_kpa'],
                'water_content': point['value'],
            }
            for point in dataset['observations']
            if (point['source_id'], point['sample_id'])
            == (record['source_id'], record['sample_id'])
        ]
        if sorted(fit['observations'], key=lambda p: p['reference']) != sorted(
            observations, key=lambda p: p['reference']
        ):
            message = 'Approximation observations differ from the evaluated measurements.'
            raise ValueError(message)
        fitted_observations = [point['observation'] for point in fit['points']]
        if (
            fit['status'] == 'fitted'
            and sorted(fitted_observations, key=lambda p: p['reference'])
            != sorted(observations, key=lambda p: p['reference'])
        ) or (fit['status'] == 'failed' and (fit['points'] or fit['parameters'])):
            message = 'Accepted fits must cover the evaluated curve; failed fits have no estimates.'
            raise ValueError(message)
        errors = [
            point['fitted_value'] - point['observation']['water_content'] for point in fit['points']
        ]
        pressures = [point['suction_kpa'] for point in observations]
        rows.append(
            {
                'source_id': record['source_id'],
                'sample_id': record['sample_id'],
                'family': fit['plan']['family_id'],
                'status': fit['status'],
                'reason': fit['reason'],
                'observation_count': len(observations),
                'pressure_range_kpa': [min(pressures), max(pressures)],
                'parameters': fit['parameters'],
                'rmse': math.sqrt(math.fsum(error**2 for error in errors) / len(errors))
                if errors
                else None,
                'mae': math.fsum(abs(error) for error in errors) / len(errors) if errors else None,
                'identifiability': fit['identifiability'],
                'curve_quality': record['quality'],
                'uncertainty_support': record['uncertainty_support'],
                'parameter_ci_available': bool(fit['parameters'])
                and all(
                    parameter['parameter_interval'] is not None for parameter in fit['parameters']
                ),
                'mean_curve_ci_available': bool(fit['points']),
                'conditional_prediction_interval_available': bool(fit['points']),
            }
        )
    return {
        'artifact_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'dataset_sha256': document['dataset_sha256'],
        'fit_summary': document['summary'],
        'interval_qualification': 'conditional_local_linear_iid_student_t; '
        'residual_assumptions_and_coverage_not_validated',
        'rows': rows,
    }


def _approximation_table(approximation: dict | None) -> list[str]:
    lines = [
        (
            '| Sample | Family | Status | N | Pressure range (kPa) | Parameters | '
            'RMSE | MAE | Parameter CI | Diagnostics |'
        ),
        '| --- | --- | --- | ---: | --- | --- | ---: | ---: | --- | --- |',
    ]
    if approximation is None:
        return [
            *lines,
            '| not assessed | - | not assessed | - | - | - | - | - | - | no artifact |',
        ]
    for row in approximation['rows']:
        parameters = (
            '; '.join(f'{p["name"]}={p["value"]:.6g} {p["unit"]}' for p in row['parameters'])
            or 'not fitted'
        )
        low, high = row['pressure_range_kpa']
        rmse = 'not estimated' if row['rmse'] is None else f'{row["rmse"]:.6g}'
        mae = 'not estimated' if row['mae'] is None else f'{row["mae"]:.6g}'
        diagnostics = [row['reason'] or 'accepted']
        identity = row['identifiability']
        if identity:
            diagnostics.append(f'rank={identity["jacobian_rank"]}/{identity["parameter_count"]}')
            condition = identity['scaled_condition_number']
            diagnostics.append(
                'condition=' + ('unavailable' if condition is None else f'{condition:.3g}')
            )
            if identity['boundary_parameters']:
                diagnostics.append('boundary=' + ','.join(identity['boundary_parameters']))
        support = row['uncertainty_support']
        for key, label in (
            ('parameter_intervals_outside_bounds', 'parameter CI outside box'),
            ('mean_intervals_outside_physical_bounds', 'mean CI outside [0,1]'),
            ('prediction_intervals_outside_physical_bounds', 'prediction interval outside [0,1]'),
        ):
            if support.get(key):
                diagnostics.append(f'{label}: {len(support[key])}')
        diagnostic = '; '.join(diagnostics)
        ci = 'conditional' if row['parameter_ci_available'] else 'unavailable'
        lines.append(
            f'| {row["sample_id"]} | {row["family"]} | {row["status"]} | '
            f'{row["observation_count"]} | {low:.6g} to {high:.6g} | {parameters} | '
            f'{rmse} | {mae} | {ci} | '
            f'{diagnostic} |'
        )
    return lines


def publish(run: Path, review_path: Path, output: Path, *, fits_path: Path | None = None) -> None:
    """Keep descriptive performance separate from unavailable selection evidence."""
    read_retention_run_report(run)
    review_bytes = review_path.read_bytes()
    review = json.loads(review_bytes)
    dataset_bytes = (run / 'dataset.json').read_bytes()
    dataset = json.loads(dataset_bytes)
    approximation = _approximation_summary(fits_path, dataset, dataset_bytes) if fits_path else None
    manifest = json.loads((run / 'run-manifest.json').read_bytes())
    plan = json.loads((run / 'evaluation-plan.json').read_bytes())
    review_hash = hashlib.sha256(review_bytes).hexdigest()
    if (
        dataset['dataset_id'] != 'meta-v3-3-panina-gray-forest-clapp-reviewed'
        or {item['function'] for item in plan['candidates']} != {'calc_ptf_clapp1978'}
        or len(plan['candidates']) != 1
        or not any(
            item['id'] == 'clapp_source_review' and item['sha256'] == review_hash
            for item in dataset['source_files']
        )
    ):
        message = 'This report requires the exact source-reviewed fixed Clapp pilot.'
        raise ValueError(message)
    cohorts = json.loads((run / 'cohorts.json').read_bytes())
    coverage = json.loads((run / 'coverage.json').read_bytes())['candidates'][0]
    profiles = {(s['source_id'], s['profile_id']) for s in dataset['samples']}
    if len(profiles) != 1 or any(profile is None for _, profile in profiles):
        message = 'Reassess selection feasibility when the reviewed profile roster changes.'
        raise ValueError(message)
    pressures = [point['suction_kpa'] for point in cohorts[0]['cohort']['comparisons']]
    unavailable = {'status': 'insufficient_evidence', 'reason': 'one_profile_one_atomic_candidate'}
    result = {
        'schema_version': 1,
        'scope': 'descriptive_real_data_pilot_not_complete_selection_vertical_slice',
        'dataset_id': dataset['dataset_id'],
        'protocol_id': manifest['protocol_id'],
        'run_id': manifest['run_id'],
        'input_hashes': manifest['input_hashes'],
        'source_review_sha256': review_hash,
        'catalog_assessment': 'not_complete; only the source-reviewed Clapp pilot is executed',
        'atomic_functions_executed': ['calc_ptf_clapp1978'],
        'coverage': coverage,
        'coverage_denominator': 'selected source-reviewed subset, not the whole workbook',
        'coverage_fraction': coverage['eligible_point_count'] / coverage['observation_count'],
        'source_review_counts': {
            key: review[key]
            for key in (
                'candidate_count',
                'eligible_count',
                'unsupported_class_count',
                'unresolved_count',
            )
        },
        'source_review_exclusions': [
            {key: source[key] for key in ('source_id', 'status', 'candidate_count', 'evidence')}
            for source in review['sources']
        ],
        'cohorts': [
            {
                'kind': item['cohort']['kind'],
                'sample_count': item['confidence']['summary']['sample_count'],
                'observation_count': item['confidence']['summary']['point_count'],
                'metrics': item['confidence']['summary']['metrics'],
                'performance_uncertainty': {
                    key: item['confidence'][key]
                    for key in ('status', 'reason', 'group_count', 'intervals')
                },
            }
            for item in cohorts
        ],
        'validated_pressure_range': {
            'unit': 'kilopascal',
            'convention': 'matric_suction_magnitude',
            'minimum': min(pressures),
            'maximum': max(pressures),
            'scope': 'observed experimental points; no continuous-domain adequacy claim',
        },
        'applicability_domain': {
            'reviewed_predictor': 'source-reported USDA silt loam; mineral soil',
            'numeric_predictor_domain': 'not_assessed; categorical PTF',
            'transfer_to_other_profiles': 'insufficient_evidence',
        },
        'selected_in_fold': [],
        'selection_stability': unavailable,
        'strategy_outer_performance': unavailable,
        'final_recommended_atomic': unavailable,
        'final_recommended_ensemble': unavailable,
        'ensemble_execution': {
            'status': 'insufficient_evidence',
            'reason': 'no_registered_ensemble_with_multiple_eligible_atomic_members_in_this_pilot',
        },
        'approximation_parameter_uncertainty': {'status': 'not_assessed'},
        'mean_curve_confidence_interval': {'status': 'not_assessed'},
        'prediction_interval': {'status': 'not_assessed'},
        'retention_approximations': approximation,
        'next_source_review': {
            'source': 'Bolotov 2014',
            'reason': 'already normalized measurements and three published profiles',
            'evidence': 'meta_v3_3.clapp-source-review.json; Bolotov 2014 Figures 4-6',
            'minimum_source_level_blockers': [
                (
                    'Establish a source-backed USDA class for each exact matched horizon; Russian '
                    'texture names and the published laser fractions do not establish that class.'
                ),
                (
                    'Bind each retained canonical identity to its published profile and mineral '
                    'material evidence, preserving exact depth and observation lineage.'
                ),
            ],
            'selection_blocker_after_source_review': 'Three profiles within one study do not '
            'by themselves establish enough independent groups for nested selection. Register '
            'the intended prediction population and feasible grouped split before assessment.',
            'stop_condition': 'Keep the source blocked if the required class evidence cannot '
            'be recovered; do not translate Russian classes or infer predictors from targets.',
        },
    }
    if approximation is not None:
        for name in (
            'approximation_parameter_uncertainty',
            'mean_curve_confidence_interval',
            'prediction_interval',
        ):
            result[name] = {
                'status': 'conditional_approximation_only',
                'qualification': approximation['interval_qualification'],
                'ptf_uncertainty': 'not_estimated',
            }
    rows = []
    for cohort in result['cohorts']:
        metrics = cohort['metrics']
        rows.append(
            f'| Clapp1978 | {cohort["kind"]} | {cohort["sample_count"]} | '
            f'{cohort["observation_count"]} | {result["coverage_fraction"]:.1%} | '
            f'{metrics["mean_absolute_error"]:.9f} | {metrics["root_mean_squared_error"]:.9f} | '
            f'{metrics["mean_error"]:.9f} | insufficient_evidence: one profile |'
        )
    text = '\n'.join(
        [
            '# meta_v3.3 real-data decision report',
            '',
            f'Dataset: `{result["dataset_id"]}`. Protocol: `{result["protocol_id"]}`.',
            '',
            (
                'Status: **incomplete selection vertical slice**. The verified fixed Clapp pilot '
                'executes normalization export, source-reviewed input binding, eligibility, '
                'native prediction, maximal/common cohorts and descriptive metrics. Selection '
                'and final recommendations remain blocked.'
            ),
            '',
            (
                '| Atomic PTF | Cohort | Samples | Observations | Coverage | '
                'MAE | RMSE | ME/bias | Metric CI |'
            ),
            '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |',
            *rows,
            '',
            (
                'Water content and errors use volume fractions; bias = predicted minus observed. '
                'Every sample has equal total weight. Coverage uses the six selected horizons, '
                'not all workbook records. All six horizons belong to one profile and one source.'
            ),
            '',
            (
                f'Experimental validation points span {min(pressures):.9g} to '
                f'{max(pressures):.9g} kPa matric suction magnitude. This observed range does not '
                'establish continuous pressure-domain adequacy. Applicability evidence covers '
                'the reviewed mineral material and source-reported USDA silt-loam class.'
            ),
            '',
            (
                'The published class review considered 24 raw texture candidates: six eligible '
                'Panina gray-forest horizons, six unsupported silt-class horizons, and twelve '
                'unresolved candidates from Badenko, Bolotov and Moiseev. The full current PTF '
                'catalog has not been assessed by this pilot.'
            ),
            '',
            (
                '`selected_in_fold`: empty; `selection_stability`, `strategy_outer_performance`, '
                '`final_recommended_atomic` and `final_recommended_ensemble`: '
                '**insufficient_evidence**. '
                'One profile cannot supply disjoint grouped training and test sets. The executed '
                'candidate roster contains one atomic PTF and no eligible registered ensemble. '
                'Clapp is an evaluated fixed candidate, not a selected winner.'
            ),
            '',
            (
                'Performance uncertainty is withheld by the registered five-group evidence gate. '
                'The pressure range and applicability diagnostics are separate from all intervals.'
            ),
            '',
            (
                'Retention approximations fit each measured horizon independently. These are '
                'in-sample approximation errors, not PTF validation errors or model selection. '
                'The engineering bounds, three starts and seed 7123 reuse the measured-retention '
                'experiment policy; failed fits retain their reasons. Workbook-stored fitted '
                'parameters are never used.'
            ),
            '',
            *_approximation_table(approximation),
            '',
            (
                'Accepted parameter, mean-curve and conditional individual-observation '
                'intervals are stored in the fit artifact. They assume local linearity and iid '
                'homoscedastic residuals. These assumptions and interval coverage have not been '
                'validated for this dataset. Intervals are not clipped; support violations remain '
                'diagnostics. No interval estimates PTF prediction uncertainty. Without a supplied '
                'fit artifact all three approximation interval types are not assessed.'
            ),
            '',
            (
                'Next focused source review: **Bolotov 2014**. Recover source-backed USDA classes '
                'for exact horizons, then bind profile/material evidence and depth lineage. '
                'Published Russian texture descriptors and laser fractions currently do not supply '
                'the required class. Retain this blocker if the original evidence is unavailable. '
                'Even after input review, three profiles in one study do not establish sufficient '
                'independent replication for the desired nested assessment. Resolve the population '
                'and grouped split before running selection; do not split horizons into folds.'
            ),
            '',
            f'Verified run ID: `{manifest["run_id"]}`. Source review SHA256: `{review_hash}`.',
            '',
            (
                'The companion JSON retains input hashes, coverage, reviewed exclusions, metrics '
                'and separate evidence statuses. Raw measurements remain in local run artifacts.'
            ),
            '',
        ]
    )
    output.mkdir(parents=True, exist_ok=False)
    (output / 'summary.json').write_bytes(canonical_json(result))
    (output / 'report.md').write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument(
        '--review',
        type=Path,
        default=Path('evaluation/datasets/meta_v3_3.clapp-source-review.json'),
    )
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fits', type=Path)
    arguments = parser.parse_args()
    publish(arguments.run, arguments.review, arguments.output, fits_path=arguments.fits)
