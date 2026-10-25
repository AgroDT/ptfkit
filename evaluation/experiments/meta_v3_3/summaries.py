"""Workbook-wide accounting and descriptive summaries without scientific imputation."""

# ruff: noqa: INP001 - Standalone experiment helpers.

from __future__ import annotations

import math
from collections import Counter, defaultdict
from typing import cast

from ptfkit_eval import RetentionComparison, summarize_retention_errors
from ptfkit_eval.artifacts import artifact_value
from ptfkit_eval.contracts import (
    PlanValidationError,
    default_model_adapter_specs,
    load_evaluation_plan,
)
from ptfkit_eval.documents import object_mapping, object_records, plain
from ptfkit_eval.execution import convert_value


def catalog_support(manifest: dict) -> dict:
    """Discover registered curves and exact-pressure outputs through current contracts."""
    support = {}
    for function in object_records(manifest['functions']):
        fid = function['id']
        curves = []
        for adapter in default_model_adapter_specs().values():
            candidate = {
                'id': 'audit',
                'kind': 'function_curve',
                'function': fid,
                'axis': {
                    'quantity': adapter.axis_quantity,
                    'unit': 'kilopascal',
                    'convention': adapter.axis_convention,
                    'transform': 'log10',
                },
                'target': {
                    'quantity': adapter.target_quantity,
                    'unit': adapter.target_unit,
                    'material_basis': adapter.target_material_basis,
                    'denominator_basis': adapter.target_denominator_basis,
                },
                'prediction': {'id': adapter.id, 'kind': 'model_adapter'},
            }
            try:
                load_evaluation_plan(
                    {
                        'schema_version': 2,
                        'ptfkit_manifest_schema_version': 1,
                        'candidates': [candidate],
                    },
                    manifest=manifest,
                )
            except PlanValidationError:
                continue
            curves.append(candidate)
        outputs = []
        for output in object_records(function['outputs']):
            measurement = object_mapping(output['measurement'])
            if (
                measurement['quantity']
                not in ('volumetric_water_content', 'gravimetric_water_content')
                or measurement['role'] != 'prediction'
            ):
                continue
            conditions = object_records(measurement.get('conditions', ()))
            pressure = None
            if len(conditions) == 1 and (
                conditions[0]['quantity'] == 'matric_potential'
                and conditions[0]['convention'] == 'magnitude'
            ):
                pressure = convert_value(
                    cast('float', conditions[0]['value']),
                    cast('str', conditions[0]['unit']),
                    'kilopascal',
                    manifest=manifest,
                )
            outputs.append(
                {
                    'output': output['name'],
                    'measurement': plain(measurement),
                    'suction_kpa': pressure,
                }
            )
        support[fid] = {'curves': curves, 'fixed_outputs': outputs}
    return support


def reconcile_rows(normalization: dict) -> list[dict]:
    """Require exactly one disposition for every populated retention-sheet row."""
    rows = []
    for section, status in (
        ('observations', 'normalized'),
        ('fitted_parameters', 'stored_parameter_not_observation'),
        ('exclusions', 'excluded'),
    ):
        rows.extend({'status': status, **record} for record in normalization[section])
    identities = [row['row'] for row in rows]
    if (
        len(set(identities)) != len(rows)
        or len(rows) != normalization['summary']['total_data_rows']
    ):
        message = 'Every populated retention row must have exactly one disposition.'
        raise ValueError(message)
    return sorted(rows, key=lambda row: row['row'])


def source_readiness(mapping: dict, rows: list[dict]) -> list[dict]:
    """Attribute rows through retained sheet coordinates, including confirmed identity repairs."""
    records = []
    claimed = set()
    physical = {rule['source']: rule for rule in mapping['retention_source_rules']}
    for reconstruction in mapping['retention_reconstruction_rules']:
        source = reconstruction['long_source']
        # Raw source cells are authoritative for accounting, even when normalization
        # repaired the source/sample namespace. They are not independent soil IDs.
        selected = [row for row in rows if row['raw_source'] == source]
        claimed.update(row['row'] for row in selected)
        rules = physical[source]['observations']
        reasons = Counter(row.get('reason') for row in selected if row['status'] == 'excluded')
        blockers = sorted({b for row in selected for b in row.get('blockers', [])})
        normalized = [row for row in selected if row['status'] == 'normalized']
        records.append(
            {
                'source_id': reconstruction['id'],
                'raw_source': source,
                'master_source': reconstruction['master_source'],
                'review_status': 'confirmed_measurements'
                if normalized and not reasons
                else 'partially_normalized'
                if normalized
                else 'blocked'
                if rules
                else 'parameters_only',
                'profile_count': None,
                'profile_status': 'unresolved',
                'normalized_samples': len(
                    {(row['source'], row['sample_id']) for row in normalized}
                ),
                'normalized_observations': len(normalized),
                'excluded_observations': sum(reasons.values()),
                'stored_parameters': sum(
                    row['status'] == 'stored_parameter_not_observation' for row in selected
                ),
                'exclusion_reasons': dict(sorted(reasons.items())),
                'blockers': blockers,
                'physical_rules': rules,
                'identity_evidence': reconstruction['evidence'],
                'identity_status': reconstruction['status'],
                'material_basis': {'status': 'unresolved', 'value': None},
            }
        )
    if claimed != {row['row'] for row in rows}:
        message = 'Source readiness must account for every retained raw source label.'
        raise ValueError(message)
    return records


def eligibility_matrix(  # noqa: C901, PLR0912, PLR0915 - Reconcile one complete cross product.
    coverage: dict,
    predictors: dict,
    datasets: list[dict],
    evaluated: list[dict],
    support: dict | None = None,
) -> list[dict]:
    """Retain the full implemented-function by master-row by canonical-target product."""
    roster = {}
    audited = {}
    for item in predictors['eligibility']:
        key = item['sample_key']
        identity = (item['source'], item['sample_id'])
        if key in roster and roster[key] != identity:
            message = 'One master row cannot have conflicting identities.'
            raise ValueError(message)
        roster[key] = identity
        if (key, item['function']) in audited:
            message = 'Predictor eligibility must be unique per function/master row.'
            raise ValueError(message)
        audited[key, item['function']] = item
    if len(roster) != predictors['summary']['candidate_sample_count']:
        message = 'Predictor roster count differs from its audit summary.'
        raise ValueError(message)
    identity_counts = Counter(roster.values())
    executions = {
        (r['source_id'], r['sample_id'], r['function'], r['target']): r for r in evaluated
    }
    if len(executions) != len(evaluated):
        message = 'Evaluated function/sample/target records must be unique.'
        raise ValueError(message)
    rows = []
    consumed = set()
    for dataset in datasets:
        quantity = dataset['target']['quantity']
        available = Counter((p['source_id'], p['sample_id']) for p in dataset['observations'])
        unmatched = set(available) - set(roster.values())
        if unmatched:
            message = 'Canonical samples require an exact audited master identity.'
            raise ValueError(message)
        for key, (source, sample) in sorted(roster.items()):
            for function in coverage['functions']:
                fid = function['id']
                reasons = []
                details = {}
                if support is not None and fid in support:
                    contract = support[fid]
                    curves = [c for c in contract['curves'] if c['target']['quantity'] == quantity]
                    fixed = [
                        o
                        for o in contract['fixed_outputs']
                        if o['measurement']['quantity'] == quantity
                    ]
                    details['curve_adapters'] = [c['prediction']['id'] for c in curves]
                    details['fixed_outputs'] = fixed
                    if not curves and not fixed:
                        reasons.append('unsupported_adapter_or_prediction_target')
                    if (
                        not curves
                        and fixed
                        and not any(
                            p['suction_kpa'] == o['suction_kpa']
                            for p in dataset['observations']
                            if (p['source_id'], p['sample_id']) == (source, sample)
                            for o in fixed
                            if o['suction_kpa'] is not None
                        )
                    ):
                        reasons.append('exact_pressure_target_unavailable')
                if not available[source, sample]:
                    reasons.append('target_unavailable')
                if identity_counts[source, sample] != 1:
                    reasons.append('ambiguous_sample_identity')
                if not function['manifest_eligible']:
                    reasons.append('unresolved_measurement_contract')
                    details['missing_measurement_paths'] = function['missing_measurement_paths']
                else:
                    audit = audited.get((key, fid))
                    if audit is None:
                        message = 'Every manifest function requires a predictor audit on every row.'
                        raise ValueError(message)
                    reasons.extend(audit['reasons'])
                    details['predictor_eligible'] = audit['eligible']
                    if audit['eligible']:
                        # A raw predictor audit cannot establish source material,
                        # observation method or adapter applicability.
                        reasons.append('source_target_protocol_review_required')
                execution_key = (source, sample, fid, quantity)
                execution = executions.get(execution_key)
                if execution is not None:
                    if not function['manifest_eligible']:
                        message = (
                            'Executed functions must have complete public measurement contracts.'
                        )
                        raise ValueError(message)
                    if not available[source, sample] or identity_counts[source, sample] != 1:
                        message = 'Executed predictions require a unique observed master identity.'
                        raise ValueError(message)
                    consumed.add(execution_key)
                    reasons = []
                    details = {'evaluation': execution}
                rows.append(
                    {
                        'master_key': key,
                        'source_id': source,
                        'sample_id': sample,
                        'function': fid,
                        'target': quantity,
                        'observation_count': available[source, sample],
                        'status': 'eligible_and_evaluated' if execution is not None else 'blocked',
                        'scientific_status': 'eligible'
                        if execution is not None
                        else 'scientifically_incompatible'
                        if set(reasons)
                        & {
                            'measurement_contract_mismatch',
                            'particle_size_mismatch',
                            'outside_published_domain',
                            'incompatible_target',
                        }
                        else 'unresolved',
                        'reasons': sorted(set(reasons)),
                        'details': details,
                    }
                )
    if consumed != set(executions):
        message = 'Every executed prediction must appear in the eligibility matrix.'
        raise ValueError(message)
    return rows


def blocker_impact(matrix: list[dict]) -> dict:
    """Rank unresolved combinations; report joint-blocker ceilings separately from sole gaps."""
    groups = defaultdict(list)
    counts = Counter()
    source_groups = defaultdict(list)
    for row in matrix:
        state = row['scientific_status']
        counts['currently_evaluated' if row['status'] == 'eligible_and_evaluated' else state] += 1
        if state == 'unresolved':
            if not set(row['reasons']) & {
                'unresolved_measurement_contract',
                'unsupported_adapter_or_prediction_target',
            }:
                source_groups[row['source_id']].append(row)
            for reason in row['reasons']:
                groups[reason].append(row)
    records = [
        {
            'blocker': reason,
            'affected_rows': len({r['master_key'] for r in rows}),
            'affected_functions': len({r['function'] for r in rows}),
            'blocked_combinations': len(rows),
            'potential_gain_upper_bound': len(rows),
            'sole_blocker_combinations': sum(r['reasons'] == [reason] for r in rows),
            'co_blockers': dict(
                sorted(
                    Counter(
                        other for row in rows for other in row['reasons'] if other != reason
                    ).items()
                )
            ),
        }
        for reason, rows in groups.items()
    ]
    return {
        'policy': 'unresolved_combination_ceiling_not_expected_scoring_gain',
        'coverage': {
            'currently_evaluated': counts['currently_evaluated'],
            'scientifically_incompatible': counts['scientifically_incompatible'],
            'unresolved_but_potentially_evaluable': counts['unresolved'],
            'structurally_impossible': 0,
        },
        'structural_scope': (
            'No permanent structural impossibility is established by missing adapters, '
            'missing metadata, missing bindings or absent canonical observations. '
            'Unresolved is a review ceiling, not confirmed theoretical applicability.'
        ),
        'ranked_blockers': sorted(
            records,
            key=lambda r: (
                -r['potential_gain_upper_bound'],
                -r['sole_blocker_combinations'],
                r['blocker'],
            ),
        ),
        'ranked_source_reviews': sorted(
            (
                {
                    'source_id': source,
                    'potential_combinations_upper_bound': len(rows),
                    'affected_rows': len({r['master_key'] for r in rows}),
                    'affected_functions': len({r['function'] for r in rows}),
                    'blockers': dict(
                        sorted(Counter(reason for row in rows for reason in row['reasons']).items())
                    ),
                    'unresolved_claim_count': len({b for row in rows for b in row['reasons']}),
                    'unlock_efficiency_upper_bound': len(rows)
                    / len({b for row in rows for b in row['reasons']}),
                }
                for source, rows in source_groups.items()
            ),
            key=lambda r: (-r['potential_combinations_upper_bound'], r['source_id']),
        ),
    }


def function_priorities(coverage: dict, matrix: list[dict]) -> list[dict]:
    """Expose minimal predictor contracts and conditional ceilings for the entire catalog."""
    groups = defaultdict(list)
    for row in matrix:
        groups[row['function']].append(row)
    records = []
    for function in coverage['functions']:
        rows = groups[function['id']]
        potential = [
            r
            for r in rows
            if r['observation_count']
            and not set(r['reasons'])
            & {
                'unresolved_measurement_contract',
                'unsupported_adapter_or_prediction_target',
                'exact_pressure_target_unavailable',
            }
        ]
        blockers = Counter(b for r in potential for b in r['reasons'])
        records.append(
            {
                'function': function['id'],
                'required_predictors': [i['name'] for i in function['inputs']],
                'predictor_count': len(function['inputs']),
                'manifest_eligible': function['manifest_eligible'],
                'potential_compatible_rows': len({r['master_key'] for r in potential}),
                'evaluated_combinations': sum(
                    r['status'] == 'eligible_and_evaluated' for r in rows
                ),
                'main_blocker': blockers.most_common(1)[0][0]
                if blockers
                else (
                    'unresolved_measurement_contract'
                    if not function['manifest_eligible']
                    else 'no_remaining_gap_in_supported_observed_rows'
                    if potential
                    else 'no_supported_exact_observed_target'
                ),
                'unresolved_claim_count': len(blockers),
                'expected_unlock_cost': 'public_measurement_contract_review'
                if not function['manifest_eligible']
                else 'source_review_of_listed_claims',
                'policy': 'conditional_row_ceiling_not_confirmed_compatibility',
            }
        )
    return sorted(
        records,
        key=lambda r: (
            not r['manifest_eligible'],
            r['unresolved_claim_count'] or 999,
            -r['potential_compatible_rows'],
            r['predictor_count'],
            r['function'],
        ),
    )


# Prespecified descriptive regions in kPa; no change to any selection loss.
PRESSURE_REGIONS = (
    ('wet', 0.0, 10.0),
    ('intermediate', 10.0, 1500.0),
    ('dry', 1500.0, None),
)


def region_metrics(comparisons: list[dict]) -> dict:
    """Partition exact observed coordinates; boundaries belong to the region on their right."""
    rows = []
    for name, lower, upper in PRESSURE_REGIONS:
        points = [
            RetentionComparison(**p)
            for p in comparisons
            if lower <= p['suction_kpa'] and (upper is None or p['suction_kpa'] < upper)
        ]
        rows.append(
            {
                'region': name,
                'lower_inclusive_kpa': lower,
                'upper_exclusive_kpa': upper,
                'status': 'descriptive' if points else 'no_observations',
                'summary': artifact_value(summarize_retention_errors(points)) if points else None,
            }
        )
    return {'policy': 'wrc_pressure_regions_kpa_v1', 'selection_criterion': False, 'regions': rows}


def approximation_summary(fits: dict) -> dict:
    """Keep accepted-fit errors separate from failed fits and optimizer start counts."""
    groups = defaultdict(list)
    samples = []
    for record in fits['results']:
        fit = record['fit']
        errors = [p['fitted_value'] - p['observation']['water_content'] for p in fit['points']]
        pressures = [p['suction_kpa'] for p in fit['observations']]
        sample = {
            'source_id': record['source_id'],
            'sample_id': record['sample_id'],
            'family': fit['plan']['family_id'],
            'status': fit['status'],
            'reason': fit['reason'],
            'observation_count': len(pressures),
            'pressure_range_kpa': [min(pressures), max(pressures)],
            'optimizer_start_count': len(fit['attempts']),
            'rmse': math.sqrt(math.fsum(e**2 for e in errors) / len(errors)) if errors else None,
            'mae': math.fsum(abs(e) for e in errors) / len(errors) if errors else None,
            'me': math.fsum(errors) / len(errors) if errors else None,
            'parameters': fit['parameters'],
            'identifiability': fit['identifiability'],
            'uncertainty_support': record['uncertainty_support'],
        }
        samples.append(sample)
        groups[sample['family']].append(sample)
    families = []
    for family, records in sorted(groups.items()):
        accepted = [r for r in records if r['status'] == 'fitted']
        rmses = [r['rmse'] for r in accepted]
        families.append(
            {
                'family': family,
                'fit_attempts': len(records),
                'accepted_fits': len(accepted),
                'rejected_fits': len(records) - len(accepted),
                'optimizer_starts': sum(r['optimizer_start_count'] for r in records),
                'accepted_rmse_range': [min(rmses), max(rmses)] if rmses else None,
                'rejection_reasons': dict(
                    sorted(Counter(r['reason'] for r in records if r['status'] != 'fitted').items())
                ),
            }
        )
    return {'family_count': len(families), 'families': families, 'samples': samples}


def count_only_checkpoint(summary: dict) -> dict:
    """Exclude raw rows, individual fitted parameters and local sample identities."""
    return {
        'schema_version': 1,
        'protocol': summary['protocol'],
        'status': summary['status'],
        'workbook_sha256': summary['workbook_sha256'],
        'mapping_sha256': summary['mapping_sha256'],
        'manifest_sha256': summary['manifest_sha256'],
        'followup_sha256': summary['followup_sha256'],
        'implementation_sha256': summary['implementation_sha256'],
        'matrix_record_count': summary['matrix_record_count'],
        'blocker_impact': summary['blocker_impact'],
        'function_priorities': summary['function_priorities'],
        'class_comparison': {
            **{k: v for k, v in summary['class_comparison'].items() if k != 'cohorts'},
            'cohorts': [
                {
                    **{k: v for k, v in r.items() if k not in ('confidence', 'cohort')},
                    'metrics': r['cohort']['summary']['metrics'],
                    'sample_count': r['cohort']['summary']['sample_count'],
                    'point_count': r['cohort']['summary']['point_count'],
                    'uncertainty_status': r['confidence']['status'],
                }
                for r in summary['class_comparison']['cohorts']
            ],
        },
        'priority_source_audit': summary['priority_source_audit'],
        'retention_accounting': summary['row_accounting'],
        'workbook_scope': {
            **{
                key: summary['workbook_scope'][key]
                for key in (
                    'sheet_count',
                    'populated_row_count',
                    'status_counts',
                )
            },
            'unreviewed_master_sources': [
                {
                    key: source[key]
                    for key in (
                        'raw_source',
                        'row_count',
                        'status',
                        'tail_populated_cell_count',
                    )
                }
                for source in summary['workbook_scope']['unreviewed_master_sources']
            ],
        },
        'source_counts': [
            {
                key: source[key]
                for key in (
                    'source_id',
                    'review_status',
                    'normalized_samples',
                    'normalized_observations',
                    'excluded_observations',
                    'stored_parameters',
                    'exclusion_reasons',
                    'blockers',
                )
            }
            for source in summary['sources']
        ],
        'functions': summary['functions'],
        **(
            {'function_audit_counts': summary['function_audit']['counts']}
            if 'function_audit' in summary
            else {}
        ),
        **(
            {
                'ensemble_comparison': {
                    key: value
                    for key, value in summary['ensemble_comparison'].items()
                    if key not in ('learned_selection', 'input_sha256')
                },
                'ensemble_learning': {
                    'status': summary['ensemble_comparison']['learned_selection']['status'],
                    'reason': summary['ensemble_comparison']['learned_selection']['splits'][
                        'reason'
                    ],
                },
            }
            if 'ensemble_comparison' in summary
            else {}
        ),
        'approximation_families': summary['approximations']['families'],
        'performance': summary['native_evaluation']['cohorts'],
        'selection': dict.fromkeys(
            ('final_recommended_atomic', 'final_recommended_ensemble', 'selection_stability'),
            summary['class_comparison']['selection'],
        ),
    }
