"""Catalog refresh, strict rediscovery and compact comparative benchmark report."""

# ruff: noqa: INP001 - Repository experiment helpers.

from __future__ import annotations

import importlib
import pkgutil

import ptfkit

from evaluation.experiments.catalog_coverage.audit import audit
from evaluation.experiments.meta_v3_3 import campaign_contracts as contracts
from evaluation.experiments.meta_v3_3 import comparative
from evaluation.experiments.meta_v3_3.harmonized import evaluate_catalog


def public_api_audit(catalog: list[dict]) -> dict:
    """Independently discover callable public wrappers, including manifest omissions."""
    discovered = set()
    expected = {(f['source'], f.get('public_api', {}).get('name', f['id'])) for f in catalog}
    for item in pkgutil.iter_modules(ptfkit.__path__):
        if item.name.startswith('_'):
            continue
        module = importlib.import_module('ptfkit.' + item.name)
        discovered.update(
            (item.name, name)
            for name in vars(module)
            if (name.startswith('calc_ptf_') or (item.name, name) in expected)
            and callable(getattr(module, name))
        )
    if discovered != expected:
        message = (
            f'Public API/specification mismatch: missing={sorted(expected - discovered)}; '
            f'unaccounted={sorted(discovered - expected)}'
        )
        raise ValueError(message)
    return {
        'public_callable_count': len(discovered),
        'specification_parity': True,
        'implemented_specifications': sum(f['status'] == 'implemented' for f in catalog),
        'public_with_other_specification_status': [
            {'function': f['id'], 'status': f['status']}
            for f in catalog
            if f['status'] != 'implemented'
        ],
    }


def catalog_refresh(catalog: list[dict], previous: dict) -> dict:
    old = {f.get('id', f.get('function')) for f in previous['functions']}
    current = {f['id'] for f in catalog}
    return {
        'previous_count': len(old),
        'current_count': len(current),
        'newly_discovered_functions': sorted(current - old),
        'removed_functions': sorted(old - current),
    }


def ladder_delta(ladder: list[dict], previous: dict) -> list[dict]:
    old = {r['evidence_ceiling']: r['functions_executable'] for r in previous['assumption_ladder']}
    return [
        {
            **r,
            'previous': old.get(r['evidence_ceiling']),
            'delta_from_previous': (
                r['functions_executable'] - old[r['evidence_ceiling']]
                if r['evidence_ceiling'] in old
                else None
            ),
        }
        for r in ladder
    ]


def refresh_strict(context: dict) -> None:
    """Reapply existing public binding/adapter gates to all current functions.

    E0 preserves the historical strict-policy definition (including reviewed
    class coordinates and exact unit conversions). Reconstructed target points
    and approximate predictors never enter this view.
    """
    context['public_api_audit'] = public_api_audit(context['catalog'])
    coverage = audit(context['root'])
    covered = {f['id'] for f in coverage['functions']}
    coverage['functions'].extend(
        {**f, 'outputs': f['fields']} for f in context['catalog'] if f['id'] not in covered
    )
    matrix, predictions = evaluate_catalog(
        coverage, context['support'], context['datasets'], context['manifest']
    )
    strict = []
    allowed = {'strict', 'converted', 'derived'}
    for p in predictions:
        if p['target_evidence']['tier'] not in allowed or any(
            proof['tier'] not in allowed for proof in p['predictor_evidence'].values()
        ):
            continue
        strict.append(
            {
                **p,
                'scenario': 'strict',
                'route': 'strict_observed',
                'pressure_kpa': p['suction_kpa'],
                'quantity': p['water_quantity'],
                'minimum_tier': 'E0',
            }
        )
    context['strict_matrix'] = matrix
    context['strict_points'] = strict
    context['strict_ids'] = {p['function'] for p in strict}
    strict_keys = {
        (p['function'], p['source_id'], p['sample_id'], p['target_pool']) for p in strict
    }
    for row in matrix:
        row['strict_eligible'] = (
            row['function'],
            row['source_id'],
            row['sample_id'],
            row['target_pool'],
        ) in strict_keys


def function_audit(context: dict, records: list[dict], summary: dict) -> list[dict]:
    by_function = {r['function']: r for r in summary['functions']}
    blockers = {r['function']: r for r in summary['final_blockers']['functions']}
    return [
        {
            **by_function[f['id']],
            'source': f['source'],
            'specification': f['specification'],
            'predictor_requirements': f['inputs'],
            'target_bindings': contracts.targets(f, context['support']),
            'strict_executable': f['id'] in context['strict_ids'],
            'blocker_decision': blockers[f['id']],
            'execution_blockers': sorted(
                {reason for r in records if r['function'] == f['id'] for reason in r['reasons']}
            ),
            'dataset_status': 'executable'
            if by_function[f['id']]['scored']
            else 'unbenchmarkable_on_fixed_dataset_under_current_policies',
        }
        for f in context['catalog']
    ]


def render(report: dict) -> str:
    refresh = report['catalog_refresh']
    lines = [
        '# ptfkit catalog benchmark',
        '',
        (
            f'Catalog: {refresh["previous_count"]} → {refresh["current_count"]}. '
            f'Strict executable: {report["strict_coverage"]}; exploratory excluding strict: '
            f'{report["exploratory_coverage_excluding_strict"]}.'
        ),
        '',
        (
            'The dataset is fixed. No manual metadata recovery or new scientific policy is used. '
            'Rankings and ensemble selection are descriptive; '
            'they do not establish generalization.'
        ),
        '',
        (
            f'Public API discovery is reconciled against source specifications: '
            f'{refresh.get("implemented_specifications", refresh["current_count"])} implemented; '
            f'{len(refresh.get("public_with_other_specification_status", []))} public wrappers '
            'with another specification status. These wrappers remain in the denominator '
            'and pass through the same existing policies.'
        ),
        '',
        'Newly discovered functions:',
        '',
        *[f'- `{f}`' for f in refresh['newly_discovered_functions']],
        '',
        '| Tier | Executable PTF | Δ from previous |',
        '| --- | ---: | ---: |',
        *[
            f'| {r["evidence_ceiling"]} | {r["functions_executable"]} | '
            f'{r["delta_from_previous"]} |'
            for r in report['assumption_ladder']
        ],
        '',
        (
            'E0 denotes the existing strict policy, including reviewed class coordinates. '
            'Higher tiers are cumulative executable-function counts.'
        ),
        '',
        '| Blocker | Functions |',
        '| --- | ---: |',
    ]
    lines.extend(
        f'| {group["next_blocker_class"]} | {group["functions_blocked"]} |'
        for group in report['final_blockers']['funnel']
    )
    lines += [
        '',
        'Exact common cohort comparisons:',
        '',
        (
            '| Scenario / route / pool | Candidates | Points / samples / profiles / sources | '
            'Best atomic RMSE | Best ensemble RMSE | Δ RMSE |'
        ),
        '| --- | ---: | --- | ---: | ---: | ---: |',
    ]
    for pool in report['comparative_benchmark']:
        label = f'{pool["scenario"]} / {pool["route"]} / {pool["target_pool"]}'
        best = pool.get('best_atomic_vs_ensemble')
        if best:
            lines.append(
                f'| {label} | {len(pool["members"])} | {pool["points"]} / {pool["samples"]} / '
                f'{pool["profiles"]} / {pool["sources"]} | '
                f'{best["atomic"]["metrics"]["rmse"]:.6g} | '
                f'{best["ensemble"]["metrics"]["rmse"]:.6g} | '
                f'{best["delta_rmse_ensemble_minus_atomic"]:+.6g} |'
            )
        else:
            lines.append(
                f'| {label} | {len(pool["members"])} | '
                'empty common cohort; see pair comparisons | — | — | — |'
            )
    lines += [
        '',
        (
            'Coverage uses the union of executable coordinates within each scenario/route/pool. '
            'Dataset sample coverage is also reported against all retained canonical samples. '
            'RMSE, MAE and bias weight samples equally; median absolute error and residual Pearson '
            'correlations weight points equally. Unknown profile IDs are counted separately.'
        ),
        '',
        'Ranking sensitivity:',
        '',
        '| Comparison | Pools tested | Pools with ordering changes | Changed pair orderings |',
        '| --- | ---: | ---: | ---: |',
    ]
    for name, rows in report['ranking_robustness'].items():
        computed = [r for r in rows if r['status'] == 'computed']
        lines.append(
            f'| {name} | {len(computed)} | '
            f'{sum(bool(r["changed_pair_orderings"]) for r in computed)} | '
            f'{sum(len(r["changed_pair_orderings"]) for r in computed)} |'
        )
    lines += ['', '<details><summary>Atomic performance and complementarity</summary>', '']
    for pool in report['comparative_benchmark']:
        lines.extend(performance_lines(pool))
    lines += ['</details>', '', '<details><summary>Rank changes</summary>', '']
    for name, rows in report['ranking_robustness'].items():
        for row in rows:
            changes = {f: d for f, d in row.get('rank_changes', {}).items() if d}
            if changes:
                lines += [
                    (
                        f'{name}: {row["target_pool"]}; {row["variants"]}; '
                        f'{row["common_points"]} common points.'
                    ),
                    '',
                    ', '.join(f'`{f}`: {d:+}' for f, d in changes.items()),
                    '',
                    (
                        f'Changed pair orderings: {len(row["changed_pair_orderings"])}; '
                        'full pairs are retained in summary.json.'
                    ),
                    '',
                ]
    lines += ['</details>', '']
    diagnostics = report['target_evidence_diagnostics']
    lines += [
        (
            'Primary target strata: '
            f'{diagnostics["interpolated_only"]["executions"]} interpolated; '
            f'{diagnostics["exact_observation_only"]["executions"]} exact observed; '
            f'{diagnostics["direct_property_executions"]} direct-property executions. '
            'Each stratum has separate common-cohort metrics and PSD sensitivity in '
            '`summary.json` → `target_evidence_diagnostics`. '
            'Errors from different target strata are never ranked against each other.'
        ),
        '',
    ]
    lines += [
        '',
        (
            'Target-route comparisons keep coordinates fixed and score each route against its own '
            'declared targets. Accepted-fit routes remain diagnostics. '
            'Interpolation never extrapolates.'
        ),
        '',
        (
            'The reduced ensemble selects candidates at or below median atomic RMSE with absolute '
            'residual correlation below 0.8. Selection uses this cohort and is descriptive only. '
            'Learned convex pairs retain the existing grouped evidence gates '
            'in `summary.json` → `ensembles`.'
        ),
        '',
        (
            'Pareto comparisons use common-cohort RMSE, absolute bias, maximal coverage '
            'and the highest required tier on the cohort. A 1% relative error tolerance '
            'prevents negligible improvements '
            'from dominating a model with lower assumption burden.'
        ),
        '',
        (
            'Full metrics, ranks, residual correlations, Pareto members, '
            'exact coordinates, rank changes, '
            'pair ordering changes and per-function predictor/blocker audits: '
            '`summary.json` → `comparative_benchmark`, `ranking_robustness`, `function_audit`. '
            'Predictions and eligibility decisions are retained in separate JSON artifacts.'
        ),
        '',
    ]
    return '\n'.join(lines)


def performance_lines(pool: dict) -> list[str]:
    """Keep full atomic metrics readable without expanding the compact overview."""
    lines = [f'{pool["scenario"]} / {pool["route"]} / {pool["target_pool"]}', '']
    if pool['status'] != 'computed':
        pairs = pool.get('pairwise_cohorts', [])
        computed = sum(p['comparison']['status'] == 'computed' for p in pairs)
        lines += [
            (
                f'Empty roster common cohort; {computed}/{len(pairs)} exact pair cohorts are '
                'executable. Full pair metrics and ensemble comparisons are retained separately '
                'in summary.json. They do not form a shared leaderboard.'
            ),
            '',
        ]
        return lines
    lines += [
        (
            '| Rank | Atomic PTF | RMSE | MAE | Bias | Median AE | Pool coverage | '
            'Dataset sample coverage | Min / required tier |'
        ),
        '| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |',
    ]
    for rank, row in enumerate(pool['ranking'], 1):
        m = row['metrics']
        dataset_coverage = row.get('dataset_sample_coverage')
        coverage = f'{dataset_coverage:.3f}' if dataset_coverage is not None else 'unavailable'
        lines.append(
            f'| {rank} | `{row["function"]}` | {m["rmse"]:.6g} | {m["mae"]:.6g} | '
            f'{m["bias"]:.6g} | {m["median_absolute_error"]:.6g} | {row["coverage"]:.3f} | '
            f'{coverage} | {row["minimum_tier"]} / {row["required_tier"]} |'
        )
    lines += ['', 'Pareto: ' + ', '.join(f'`{f}`' for f in pool['pareto']) + '.', '']
    best = pool.get('best_atomic_vs_ensemble')
    if best:
        ensemble = best['ensemble']
        lines += [
            (
                f'Best atomic: `{best["atomic"]["function"]}`; best ensemble: '
                f'{ensemble["algorithm"]} ({", ".join(ensemble["members"])}).'
            ),
            '',
        ]
    pairs = [r for r in pool['residual_correlations'] if r['correlation'] is not None]
    pairs.sort(key=lambda r: abs(r['correlation']))
    lines += ['Lowest absolute residual correlations (descriptive):', '']
    lines += [f'- `{r["left"]}` / `{r["right"]}`: {r["correlation"]:.4f}' for r in pairs[:3]] or [
        'Insufficient points or constant residuals.'
    ]
    return [*lines, '']


def target_diagnostics(points: list[dict]) -> dict:
    """Expose interpolated and exact target strata without comparing different cohorts."""

    def policies(proof: dict) -> set[str]:
        return {proof['policy']} | {key for parent in proof['parents'] for key in policies(parent)}

    interpolated, exact, properties = [], [], []
    for p in points:
        if p['quantity'] == 'dry_bulk_density':
            properties.append(p)
        elif 'log_pressure_linear_interpolation_v1' in policies(p['target_evidence']):
            interpolated.append(p)
        else:
            exact.append(p)
    return {
        'interpolated_only': {
            'executions': len(interpolated),
            'comparisons': comparative.analyze(interpolated),
            'scenario_robustness': comparative.robustness(interpolated, dimension='scenario'),
        },
        'exact_observation_only': {
            'executions': len(exact),
            'comparisons': comparative.analyze(exact),
            'scenario_robustness': comparative.robustness(exact, dimension='scenario'),
        },
        'direct_property_executions': len(properties),
        'interpretation': (
            'Each stratum has its own exact common cohorts; no cross-stratum error ranking.'
        ),
    }
