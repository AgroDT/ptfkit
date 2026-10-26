"""Function-first coverage, exclusive blocker funnels and evidence burdens."""

# ruff: noqa: INP001 - Standalone experiment reporting.

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


LEVELS = ('E0', 'E1', 'E2', 'E3', 'E4')
_APPROXIMABLE = {
    'evaluator_contract_or_adapter',
    'particle_size_predictor_missing',
    'retention_predictor_unavailable',
    'target_requires_interpolation',
    'organic_predictor_missing',
    'texture_class_unavailable',
}


def policy_ids(proof: dict) -> set[str]:
    return {proof['policy']} | {name for p in proof['parents'] for name in policy_ids(p)}


def category(reason: str) -> str:  # noqa: C901, PLR0911, PLR0912 - Exclusive, named scientific blocker categories.
    if reason == 'unknown_output_water_basis':
        return 'unacceptable_physical_semantics'
    if reason in (
        'measurement_contract_adapter_absent',
        'model_variant_or_target_adapter_unresolved',
        'implementation_adapter_failure',
        'wet_branch_adapter_absent',
    ):
        return 'evaluator_contract_or_adapter'
    if reason in (
        'operational_target_absent',
        'target_property_absent',
        'target_observations_absent',
    ):
        return 'target_absent'
    if reason in ('same_sample_density_missing', 'density_conversion_policy_disabled'):
        return 'same_sample_density_missing'
    if reason.startswith('missing_predictor:'):
        name = reason.partition(':')[2]
        if name == 'bulk_density':
            return 'bulk_density_missing'
        if name in ('sand', 'silt', 'clay', 'fine_sand', 'fine_fraction', 'fine_sand_fraction'):
            return 'particle_size_predictor_missing'
        if name in ('soil_texture', 'soil_class'):
            return 'texture_class_unavailable'
        if name in ('theta_33', 'theta_1500'):
            return 'retention_predictor_unavailable'
        if name in (
            'soc',
            'carbon',
            'organic_carbon',
            'soil_organic_carbon',
            'organic_matter',
            'soil_organic_matter',
        ):
            return 'organic_predictor_missing'
        return 'required_predictor_not_inventoried'
    if reason.startswith('unresolved_predictor_unit'):
        return 'input_unit_or_semantics_unresolved'
    if reason.startswith('computational_domain') or reason in (
        'native_domain_or_adapter_failure',
        'cosby_requires_reviewed_class_midpoint_coordinates',
    ):
        return 'unacceptable_domain_or_unregistered_derivation'
    if reason == 'target_pressure_outside_measured_range':
        return 'target_pressure_unavailable_no_extrapolation'
    if reason == 'target_requires_interpolation':
        return 'target_requires_interpolation'
    return reason


def blocker_funnel(catalog: list[dict], records: list[dict], scored: set[str]) -> dict:
    """Assign one next blocker to each unscored function; retain every detailed reason."""
    indexed = defaultdict(list)
    for row in records:
        indexed[row['function']].append(row)
    decisions = []
    grouped: defaultdict[str, dict] = defaultdict(
        lambda: {
            'functions': [],
            'samples': set(),
            'executions': set(),
            'one_policy_functions': set(),
        }
    )
    for function in catalog:
        fid = function['id']
        if fid in scored:
            decisions.append({'function': fid, 'next_blocker': None, 'status': 'executable'})
            continue
        rows = indexed[fid]
        candidates = [
            (row, {category(reason) for reason in row['reasons']}) for row in rows if row['reasons']
        ]
        minimum = min((len(set(row['reasons'])) for row, _ in candidates), default=1)
        nearest = [
            (row, reasons) for row, reasons in candidates if len(set(row['reasons'])) == minimum
        ]
        counts = Counter(reason for _, reasons in nearest for reason in reasons)
        blocker = (
            min(counts, key=lambda key: (-counts[key], key)) if counts else 'unresolved_execution'
        )
        relevant = [row for row, reasons in nearest if blocker in reasons]
        group = grouped[blocker]
        group['functions'].append(fid)
        for row in relevant:
            if row.get('source_id'):
                identity = (row['source_id'], row['sample_id'])
                group['samples'].add(identity)
                group['executions'].add((fid, *identity, row['target_pool']))
        if blocker in _APPROXIMABLE and any(
            reasons == {blocker}
            and row.get('source_id')
            and (
                blocker != 'particle_size_predictor_missing'
                or row.get('reported_usda_class_available')
            )
            and (blocker != 'texture_class_unavailable' or row.get('usda_class_policy_supported'))
            for row, reasons in nearest
        ):
            group['one_policy_functions'].add(fid)
        decisions.append(
            {
                'function': fid,
                'next_blocker': blocker,
                'status': 'blocked',
                'nearest_blocker_count': minimum,
                'all_reasons': sorted({reason for row in rows for reason in row['reasons']}),
                'nearest_samples': len(
                    {
                        (row.get('source_id'), row.get('sample_id'))
                        for row in relevant
                        if row.get('source_id')
                    }
                ),
            }
        )
    groups: list[dict] = []
    for reason, group in grouped.items():
        groups.append(
            {
                'next_blocker_class': reason,
                'functions_blocked': len(group['functions']),
                'functions': sorted(group['functions']),
                'potential_samples': len(group['samples']),
                'potential_executions': len(group['executions']),
                'one_policy_opportunity_functions': len(group['one_policy_functions']),
                'can_be_approximated_reproducibly': 'conditional_on_registered_evidence'
                if group['one_policy_functions']
                else 'same_sample_measurement_required'
                if 'density_missing' in reason
                else 'no_current_defensible_route',
            }
        )
    groups.sort(
        key=lambda row: (
            -row['one_policy_opportunity_functions'],
            -row['functions_blocked'],
            row['next_blocker_class'],
        )
    )
    buckets = Counter()
    for decision in decisions:
        reason = decision['next_blocker']
        if isinstance(reason, str):
            bucket = (
                'target'
                if reason == 'target_absent'
                else 'evaluator'
                if reason == 'evaluator_contract_or_adapter'
                else 'unacceptable_assumptions'
                if reason.startswith('unacceptable')
                else 'data'
            )
            buckets[bucket] += 1
    return {
        'functions': decisions,
        'funnel': groups,
        'exclusive_blocker_buckets': {
            name: buckets[name]
            for name in ('data', 'target', 'evaluator', 'unacceptable_assumptions')
        },
        'blocked_function_count': len(catalog) - len(scored),
        'potential_policy_counts_are_upper_bounds': True,
    }


def summarize(
    catalog: list[dict],
    records: list[dict],
    points: list[dict],
    strict_ids: set[str],
    metric: Callable[[list[dict]], dict | None],
) -> dict:
    """Keep minimal assumptions and descriptive coverage separate from comparative ranking."""
    functions: list[dict] = []
    for function in catalog:
        fid = function['id']
        selected = [p for p in points if p['function'] == fid]
        minimum = (
            'E0' if fid in strict_ids else min((p['minimum_tier'] for p in selected), default=None)
        )
        functions.append(
            {
                'function': fid,
                'minimum_tier': minimum,
                'samples': len({(p['source_id'], p['sample_id']) for p in selected}),
                'combinations': len(
                    {(p['source_id'], p['sample_id'], p['target_pool']) for p in selected}
                ),
                'scenario_executions': len(selected),
                'scored': bool(selected) or fid in strict_ids,
            }
        )
    groups = defaultdict(list)
    for point in points:
        groups[point['function'], point['scenario'], point['target_pool']].append(point)
    burden = []
    derived_policies = {
        'usda_class_conditional_psd_v1',
        'exploratory_derived_texture_class',
        'depth_interval_midpoint_cm_v1',
        'retention_predictor_v1',
        'psd_exact_rebin_v1',
        'texture_closure_v1',
        'meta_texture_closure_v1',
    }
    for (fid, scenario, pool), selected in sorted(groups.items()):
        derived, approximate = set(), set()
        for p in selected:
            for name, proof in p['predictor_evidence'].items():
                identity = (p['source_id'], p['sample_id'], name)
                if (
                    policy_ids(proof) & derived_policies
                    or proof['details'].get('origin') == 'derived'
                ):
                    derived.add(identity)
                if proof['tier'] == 'approximate':
                    approximate.add(identity)
        burden.append(
            {
                'function': fid,
                'scenario': scenario,
                'target_pool': pool,
                'samples': len({(p['source_id'], p['sample_id']) for p in selected}),
                'minimum_tier': min(p['minimum_tier'] for p in selected),
                'derived_inputs': len(derived),
                'approximate_inputs': len(approximate),
                'reconstructed_targets': sum(
                    bool(
                        policy_ids(p['target_evidence'])
                        & {
                            'log_pressure_linear_interpolation_v1',
                            'accepted_fit_target_v1',
                            'wrc_log10_adjacent_v1',
                        }
                    )
                    for p in selected
                ),
                'metrics': metric(selected),
                'recommendation_eligible': False,
            }
        )
    ladder = [
        {
            'evidence_ceiling': level,
            'functions_executable': sum(
                f['minimum_tier'] is not None and f['minimum_tier'] <= level for f in functions
            ),
            'exploratory_excluding_strict': sum(
                f['minimum_tier'] is not None
                and f['minimum_tier'] <= level
                and f['function'] not in strict_ids
                for f in functions
            ),
        }
        for level in LEVELS
    ]
    scored = {f['function'] for f in functions if f['scored']}
    pools = []
    for scenario, pool in sorted({(p['scenario'], p['target_pool']) for p in points}):
        selected = [p for p in points if p['scenario'] == scenario and p['target_pool'] == pool]
        pools.append(
            {
                'scenario': scenario,
                'target_pool': pool,
                'functions': len({p['function'] for p in selected}),
                'samples': len({(p['source_id'], p['sample_id']) for p in selected}),
                'combinations': len(selected),
                'profiles': len(
                    {(p['source_id'], p['profile_id']) for p in selected if p['profile_id']}
                ),
            }
        )
    return {
        'functions': functions,
        'assumption_burden': burden,
        'assumption_ladder': ladder,
        'strict_coverage': len(strict_ids),
        'all_function_coverage': len(scored),
        'exploratory_coverage_excluding_strict': len(scored - strict_ids),
        'samples': len({(p['source_id'], p['sample_id']) for p in points}),
        'unique_function_sample_target_combinations': len(
            {(p['function'], p['source_id'], p['sample_id'], p['target_pool']) for p in points}
        ),
        'scenario_executions': len(points),
        'target_pools': pools,
        'final_blockers': blocker_funnel(catalog, records, scored),
        'recommendation': None,
        'main_leaderboard_eligible': False,
    }


def _table(headers: tuple[str, ...], rows: Iterable[tuple]) -> list[str]:
    return [
        '| ' + ' | '.join(headers) + ' |',
        '|' + '|'.join('---' for _ in headers) + '|',
        *('| ' + ' | '.join(map(str, row)) + ' |' for row in rows),
    ]


def render(report: dict) -> str:
    lines = [
        '# Catalog exploratory expansion',
        '',
        (
            f'Strict: {report["strict_coverage"]}/{report["catalog_count"]}; '
            f'exploratory excluding strict: '
            f'{report["exploratory_coverage_excluding_strict"]}/{report["catalog_count"]}.'
        ),
        (
            f'Samples: {report["samples"]}; unique function/sample/target combinations: '
            f'{report["unique_function_sample_target_combinations"]}; '
            f'scenario executions: {report["scenario_executions"]}.'
        ),
        '',
        'Exploratory results remain excluded from the main leaderboard and final recommendations.',
        '',
        '## Assumption ladder',
        '',
    ]
    lines += _table(
        ('Ceiling', 'Functions', 'Exploratory excluding strict'),
        (
            (r['evidence_ceiling'], r['functions_executable'], r['exploratory_excluding_strict'])
            for r in report['assumption_ladder']
        ),
    )
    lines += [
        '',
        (
            'E0 reapplies the strict policy to the current catalog. E1-E4 ceilings are cumulative. '
            'E4 includes combined target reconstruction and predictor/material assumptions.'
        ),
        '',
        '## Policy stages',
        '',
    ]
    lines += _table(
        ('Stage', 'All functions', 'New functions', 'Executions'),
        (
            (s['stage'], len(s['functions']), len(s['new_functions']), s['combinations'])
            for s in report['stages']
        ),
    )
    lines += [
        '',
        '## Policy contributions',
        '',
        (
            'Leave-one-policy-out effects are conditional on the complete policy set '
            'and are not additive.'
        ),
        '',
    ]
    lines += _table(
        ('Disabled group', 'Functions lost', 'Functions remaining', 'Executions'),
        (
            (
                r['disabled_policy_group'],
                r['lost_function_count'],
                r['remaining_functions'],
                r['executions'],
            )
            for r in report['policy_contributions']
        ),
    )
    for label, funnel in [
        ('Initial blocker funnel', report['initial_blockers']),
        ('Final blocker funnel', report['final_blockers']),
    ]:
        lines += ['', '## ' + label, '']
        keys = (
            'next_blocker_class',
            'functions_blocked',
            'potential_samples',
            'potential_executions',
            'one_policy_opportunity_functions',
            'can_be_approximated_reproducibly',
        )
        lines += _table(
            (
                'Next blocker',
                'Functions',
                'Potential samples',
                'Potential executions',
                'One-policy opportunities',
                'Reproducible approximation?',
            ),
            (tuple(r[k] for k in keys) for r in funnel['funnel']),
        )
    lines += ['', '## Target pools', '']
    lines += _table(
        ('Scenario', 'Pool', 'Functions', 'Samples', 'Executions'),
        (
            (r['scenario'], r['target_pool'], r['functions'], r['samples'], r['combinations'])
            for r in report['target_pools']
        ),
    )
    lines += ['', '## Scenario sensitivity and fit diagnostics', '']
    lines += _table(
        ('Route', 'Pool', 'Common points', 'Ranking status', 'Changed pair orderings'),
        (
            (
                r['route'],
                r['target_pool'],
                r.get('common_points', 0),
                r['status'],
                len(r.get('changed_pair_orderings', [])),
            )
            for r in report['scenario_sensitivity']['rankings']
        ),
    )
    diagnostic = report['fit_disagreement']
    lines += [
        '',
        (
            f'Accepted fits: {report["accepted_fits"]}. Diagnostic executions: '
            f'{diagnostic["executions"]}; differences above the registered '
            f'{diagnostic["threshold_original_volume_fraction"]:g} original volume-fraction '
            f'threshold: {diagnostic["above_threshold"]}. '
            'Fit targets remain separate from interpolation.'
        ),
        '',
        '## Same-sample density',
        '',
    ]
    keys = (
        'source_id',
        'mass_basis_samples',
        'mass_basis_points',
        'same_sample_density_available',
        'convertible',
        'missing_density',
    )
    lines += _table(
        ('Source', 'Mass samples', 'Points', 'Same-sample density', 'Convertible', 'Missing'),
        (tuple(r[k] for k in keys) for r in report['density_audit']),
    )
    lines += [
        '',
        '## Assumption burden',
        '',
        'These are per-model descriptive errors; compare models only in the common-cohort tables.',
        '',
    ]
    keys = (
        'function',
        'scenario',
        'samples',
        'target_pool',
        'minimum_tier',
        'derived_inputs',
        'reconstructed_targets',
        'approximate_inputs',
    )
    rows = [
        (*tuple(r[k] for k in keys), *(f'{r["metrics"][k]:.6g}' for k in ('rmse', 'mae', 'bias')))
        for r in report['assumption_burden']
    ]
    rows += [
        (f['function'], 'unavailable', 0, 'not_scored', 'unsupported', 0, 0, 0, '-', '-', '-')
        for f in report['functions']
        if not f['scored']
    ]
    lines += _table(
        (
            'PTF',
            'Scenario',
            'Samples',
            'Target pool',
            'Minimum tier',
            'Derived inputs',
            'Reconstructed targets',
            'Approximate inputs',
            'RMSE',
            'MAE',
            'Bias',
        ),
        rows,
    )
    lines += ['', '## Last blockers', '']
    lines += _table(
        ('PTF', 'Next blocker', 'Nearest blocker count'),
        (
            (r['function'], r['next_blocker'], r['nearest_blocker_count'])
            for r in report['final_blockers']['functions']
            if r['next_blocker']
        ),
    )
    lines += [
        '',
        '## Interpretation',
        '',
        (
            'Common-cohort metrics, paired scenario sensitivity, ranking stability, accepted-fit '
            'diagnostics and ensemble evidence are recorded separately in summary.json.'
        ),
        (
            'No unknown water denominator, operational FC pressure, population-average density '
            'or taxonomic identity is invented.'
        ),
        '',
    ]
    return '\n'.join(lines)
