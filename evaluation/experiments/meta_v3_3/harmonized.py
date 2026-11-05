"""Opt-in catalog-wide harmonized benchmark alongside the unchanged strict artifacts."""

# ruff: noqa: INP001 - Standalone reproducible experiment.

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import replace
from itertools import combinations
from pathlib import Path
from typing import cast

from ptfkit_eval import evaluate_candidate, load_evaluation_plan, read_retention_run_report
from ptfkit_eval.artifacts import artifact_value
from ptfkit_eval.cohorts import RetentionCandidateComparisons, build_retention_cohorts
from ptfkit_eval.contracts import FunctionCurveCandidate, TargetSpec
from ptfkit_eval.documents import canonical_json, document_hash, plain
from ptfkit_eval.folds import GroupedSample
from ptfkit_eval.harmonization import (
    EvidenceTier,
    EvidenceValue,
    policy_registry,
    reconstruct_water,
)
from ptfkit_eval.harmonized_inputs import resolve_harmonized_input
from ptfkit_eval.input_bindings import bind_retention_inputs
from ptfkit_eval.metrics import RetentionComparison, summarize_retention_errors

from evaluation.experiments.catalog_coverage.audit import audit
from evaluation.experiments.meta_v3_3.atomic_campaign import pool_id, targets
from evaluation.experiments.meta_v3_3.ensembles import compare
from ptfkit import get_manifest


_MINIMUM_MEMBERS = 2
_MINIMUM_PROFILES = 3


def catalog_targets(function: dict, support: dict) -> list[dict]:
    """Include fixed-pressure pools served by a registered continuous curve adapter."""
    result = targets(function, support)
    curves = support.get(function['id'], {}).get('curves', [])
    if len(curves) == 1:
        existing = {pool_id(target) for target in result}
        for pressure in (10, 33, 1500):
            target = {
                'quantity': curves[0]['target']['quantity'],
                'kind': 'fixed_pressure',
                'pressure_kpa': pressure,
                'via_curve': True,
            }
            if pool_id(target) not in existing:
                result.append(target)
    return sorted(result, key=pool_id)


def _write(output: Path, name: str, document: object) -> None:
    with (output / name).open('xb') as stream:
        stream.write(canonical_json(document))


def _same_numeric_quantity(binding: dict, feature: dict) -> bool:
    expected, actual = binding.get('measurement'), feature.get('measurement')
    if not expected or not actual or feature.get('kind') != 'numeric':
        return False
    return all(
        actual.get(key) == expected.get(key)
        for key in ('quantity', 'basis', 'particle_size', 'conditions')
    ) and (not expected.get('method') or actual.get('method') == expected['method'])


def _inputs(  # noqa: C901 - Resolve and retain independent predictor rejection reasons.
    function: dict, sample: dict, manifest: dict
) -> tuple[dict, dict, list[str]]:
    """Evaluate only the requested predictors, preserving strict binder decisions."""
    bindings = {}
    for binding in function['inputs']:
        matches = [f for f in sample['features'] if f['id'] == binding['name']]
        if not matches:
            matches = [
                f
                for f in sample['features']
                if _same_numeric_quantity(binding, f)
                or (
                    binding.get('kind') == 'categorical'
                    and f.get('category_system') == binding.get('enum', {}).get('id')
                )
            ]
        if len(matches) == 1:
            bindings[binding['name']] = matches[0]['id']
    traces = bind_retention_inputs(function, sample, bindings, manifest=manifest)
    indexed = {trace.input: trace for trace in traces}
    features = {f['id']: f for f in sample['features']}
    values, evidence, reasons = {}, {}, []
    for binding in function['inputs']:
        name = binding['name']
        trace = indexed.get(name)
        if trace is None:
            reasons.append(f'missing_predictor:{name}')
            continue
        feature = features[trace.feature_id]
        sources = tuple(feature.get('source_cells', ())) or (f'feature:{trace.feature_id}',)
        if not trace.reasons:
            tier = EvidenceTier.DERIVED if feature['origin'] == 'derived' else EvidenceTier.STRICT
            if trace.compatibility == 'unit_converted' and tier == EvidenceTier.STRICT:
                tier = EvidenceTier.CONVERTED
            proof = EvidenceValue(
                cast('float | str', trace.value),
                tier,
                feature.get('derivation', {}).get('method', 'reviewed_feature_v1'),
                sources,
                (
                    ('measurement', feature.get('measurement')),
                    ('source_value', feature['value']),
                    ('source_unit', trace.source_unit),
                    ('target_unit', trace.target_unit),
                ),
            )
        elif feature.get('harmonization') and feature['review_status'] == 'confirmed':
            # New derivations arrive as explicit EvidenceValue objects in the in-memory API;
            # persisted unverified dicts cannot self-authorize a derived feature.
            proof = feature['harmonization']
            if not isinstance(proof, EvidenceValue):
                reasons.append(f'unverified_harmonization:{name}')
                continue
            proof, blockers = resolve_harmonized_input(
                binding, proof, feature.get('measurement', {}), manifest=manifest
            )
            if blockers or proof is None:
                reasons.extend(f'{reason}:{name}' for reason in blockers)
                continue
        else:
            reasons.extend(f'{reason}:{name}' for reason in trace.reasons)
            continue
        values[name], evidence[name] = proof.value, proof.document()
    return values, evidence, reasons


def _target_points(
    dataset: dict, sample: dict, target: dict
) -> tuple[list[tuple[float, EvidenceValue]], list[str]]:
    if dataset['target']['quantity'] != target['quantity']:
        return [], ['target_quantity_mismatch']
    points = [
        o
        for o in dataset['observations']
        if (o['source_id'], o['sample_id']) == (sample['source_id'], sample['sample_id'])
    ]
    supported = [
        (
            o['suction_kpa'],
            EvidenceValue(
                o['value'],
                EvidenceTier.STRICT,
                'reviewed_observation_v1',
                tuple(o['source_cells']),
                (('observation_id', o['id']), ('origin', o['origin'])),
            ),
        )
        for o in points
        if o['review_status'] == 'confirmed'
        and o['origin'] == 'measured'
        and not o['quality_flags']
    ]
    if target['kind'] == 'operational':
        return [], ['unsupported_operational_target']
    try:
        # Validate duplicates and canonical water bounds before any execution.
        if target['kind'] == 'fixed_pressure':
            value = reconstruct_water(
                supported, target['pressure_kpa'], water_quantity=target['quantity']
            )
            return ([(target['pressure_kpa'], value)] if value else []), (
                [] if value else ['outside_measured_wrc_range']
            )
        if supported:
            reconstruct_water(supported, supported[0][0], water_quantity=target['quantity'])
    except ValueError:
        return [], ['ambiguous_or_invalid_measured_wrc']
    lower, upper = target.get('pressure_range_kpa', [0, float('inf')])
    return [(p, v) for p, v in supported if lower <= p <= upper], []


def _candidate(
    function: dict, target: dict, support: dict, manifest: dict
) -> tuple[FunctionCurveCandidate | None, list[str]]:
    available = support.get(function['id'], {})
    if target['kind'] == 'curve' or target.get('via_curve'):
        curves = available.get('curves', [])
        definition = curves[0] if len(curves) == 1 else None
    elif target['kind'] == 'fixed_pressure':
        outputs = [
            point
            for point in available.get('fixed_outputs', [])
            if point['suction_kpa'] == target['pressure_kpa']
            and point['measurement']['quantity'] == target['quantity']
        ]
        if len(outputs) != 1:
            return None, ['missing_executable_target_contract']
        point = outputs[0]
        measurement = point['measurement']
        definition = {
            'id': function['id'],
            'kind': 'function_point',
            'function': function['id'],
            'axis': {
                'quantity': 'matric_potential',
                'unit': 'kilopascal',
                'convention': 'magnitude',
                'transform': 'log10',
            },
            'target': {
                'quantity': target['quantity'],
                'unit': measurement['unit'],
                'material_basis': measurement['basis']['material'],
                'denominator_basis': measurement['basis']['denominator'],
            },
            'prediction': {'kind': 'fixed_output', 'name': point['output']},
        }
    else:
        return None, ['unsupported_operational_target']
    if definition is None:
        return None, ['missing_executable_target_contract']
    plan = load_evaluation_plan(
        {'schema_version': 1, 'ptfkit_manifest_schema_version': 1, 'candidates': [definition]},
        manifest=manifest,
    )
    return cast('FunctionCurveCandidate', plan.candidates[0]), []


def evaluate_catalog(  # noqa: C901 - Each combination retains its independent decision.
    coverage: dict, support: dict, datasets: list[dict], manifest: dict
) -> tuple[list[dict], list[dict]]:
    """Account for every catalog function/sample/target without source-wide eligibility gates."""
    public = {f['id']: f for f in manifest['functions']}
    matrix, predictions = [], []
    for function in coverage['functions']:
        fid = function['id']
        for target in catalog_targets(function, support):
            candidate, candidate_reasons = _candidate(function, target, support, manifest)
            for dataset in datasets:
                for sample in dataset['samples']:
                    values, evidence, reasons = ({}, {}, ['missing_public_measurement_contract'])
                    if fid in public:
                        values, evidence, reasons = _inputs(public[fid], sample, manifest)
                    points, target_reasons = _target_points(dataset, sample, target)
                    reasons = [*candidate_reasons, *reasons, *target_reasons]
                    if candidate is not None and dict(dataset['target']) != artifact_value(
                        candidate.target
                    ):
                        reasons.append('target_physical_contract_mismatch')
                    if not points:
                        reasons.append('no_supported_target_observations')
                    approximate = any(v['tier'] == 'approximate' for v in evidence.values())
                    view = (
                        'unsupported' if reasons else 'exploratory' if approximate else 'harmonized'
                    )
                    record: dict = {
                        'function': fid,
                        'dataset_id': dataset['dataset_id'],
                        'source_id': sample['source_id'],
                        'sample_id': sample['sample_id'],
                        'profile_id': sample.get('profile_id'),
                        'target_pool': pool_id(target),
                        'requested_pressure_kpa': target.get('pressure_kpa'),
                        'view': view,
                        'reasons': sorted(set(reasons)),
                        'predictors': evidence,
                        'target_count': len(points),
                        'target_evidence': [value.document() for _, value in points],
                        'execution_status': 'not_executed',
                    }
                    matrix.append(record)
                    if view != 'harmonized' or candidate is None:
                        continue
                    for pressure, observation in points:
                        try:
                            result = evaluate_candidate(
                                candidate, [pressure], values, manifest=manifest
                            )
                        except (ValueError, ArithmeticError) as error:
                            record['execution_status'] = 'failed'
                            record.setdefault('execution_errors', []).append(
                                type(error).__name__ + ': ' + str(error)
                            )
                            continue
                        record['execution_status'] = (
                            'executed'
                            if record['execution_status'] != 'failed'
                            else 'partially_executed'
                        )
                        predictions.append(
                            {
                                **{
                                    k: record[k]
                                    for k in (
                                        'function',
                                        'dataset_id',
                                        'source_id',
                                        'sample_id',
                                        'profile_id',
                                        'target_pool',
                                    )
                                },
                                'suction_kpa': pressure,
                                'observed': observation.value,
                                'predicted': result.points[0].value,
                                'water_quantity': target['quantity'],
                                'target_evidence': observation.document(),
                                'predictor_evidence': evidence,
                                'view': 'harmonized',
                                'target_contract': artifact_value(candidate.target),
                                'exact_observation_existed': observation.tier
                                == EvidenceTier.STRICT,
                            }
                        )
    return matrix, predictions


def _metrics(points: list[dict]) -> dict | None:
    if not points:
        return None
    summary = artifact_value(summarize_retention_errors(_comparisons(points)))
    return cast('dict', summary)['metrics']


def _comparisons(points: list[dict]) -> tuple[RetentionComparison, ...]:
    return tuple(
        RetentionComparison(
            **{
                key: p[key]
                for key in (
                    'source_id',
                    'sample_id',
                    'profile_id',
                    'suction_kpa',
                    'observed',
                    'predicted',
                    'water_quantity',
                )
            }
        )
        for p in points
    )


def ensemble_pools(predictions: list[dict]) -> list[dict]:
    """Reuse existing means/convex learning per physical target and pressure pool."""
    for point in predictions:
        tiers = {
            value['tier']
            for value in [point['target_evidence'], *point['predictor_evidence'].values()]
        }
        if point['view'] != 'harmonized' or tiers & {'approximate', 'unsupported'}:
            message = 'Main ensembles require harmonized evidence without approximate members.'
            raise ValueError(message)
    pools = defaultdict(list)
    for point in predictions:
        pools[(point['target_pool'], document_hash(point['target_contract']))].append(point)
    result = []
    for (pool, _), points in sorted(pools.items()):
        functions = sorted({p['function'] for p in points})
        if len(functions) < _MINIMUM_MEMBERS:
            continue
        records = tuple(
            RetentionCandidateComparisons(
                candidate_id=fid,
                dataset_id='harmonized',
                protocol_id='registered_harmonization_v1',
                target=TargetSpec(**points[0]['target_contract']),
                comparisons=_comparisons([p for p in points if p['function'] == fid]),
            )
            for fid in functions
        )
        sample_index = {
            (p['source_id'], p['sample_id']): GroupedSample(
                p['source_id'], p['sample_id'], p['profile_id']
            )
            for p in points
        }
        provenance = {
            fid: sorted(
                {
                    v['tier']
                    for p in points
                    if p['function'] == fid
                    for v in [p['target_evidence'], *p['predictor_evidence'].values()]
                }
            )
            for fid in functions
        }
        profiles = {(s.source_id, s.profile_id) for s in sample_index.values() if s.profile_id}
        if len(profiles) >= _MINIMUM_PROFILES and all(s.profile_id for s in sample_index.values()):
            summary = compare(records, tuple(sample_index.values()))
        else:
            cohorts = build_retention_cohorts(records)
            common = {c.candidate_id: c.comparisons for c in cohorts.common}
            means = []
            for left, right in combinations(functions, 2):
                paired = tuple(
                    replace(a, predicted=(a.predicted + b.predicted) / 2)
                    for a, b in zip(common[left], common[right], strict=True)
                )
                means.append(
                    {
                        'members': [left, right],
                        'weights': [0.5, 0.5],
                        'metrics': artifact_value(summarize_retention_errors(paired))
                        if paired
                        else None,
                    }
                )
            summary = {
                'status': 'descriptive',
                'means': means,
                'learned_status': 'insufficient_independent_profiles',
                'recommendation': None,
            }
        result.append(
            {
                'target_pool': pool,
                'view': 'harmonized',
                'members': provenance,
                'training_observation_tiers': sorted(
                    {p['target_evidence']['tier'] for p in points}
                ),
                'assessment': summary,
            }
        )
    return result


def fixed_pressure_inventory(matrix: list[dict]) -> list[dict]:
    """Deduplicate released target evidence across functions, including blocked predictors."""
    indexed = {}
    for row in matrix:
        if row['requested_pressure_kpa'] is None:
            continue
        for evidence in row['target_evidence']:
            identity = (row['dataset_id'], row['source_id'], row['sample_id'], row['target_pool'])
            indexed[identity] = {
                **{
                    key: row[key]
                    for key in (
                        'dataset_id',
                        'source_id',
                        'sample_id',
                        'target_pool',
                        'requested_pressure_kpa',
                        'profile_id',
                    )
                },
                'evidence': evidence,
                'exact_observation_existed': evidence['tier'] == 'strict',
            }
    return list(indexed.values())


def run(reference: Path, output: Path) -> dict:  # noqa: PLR0915 - One artifact transaction.
    """Verify strict artifacts, preserve them and write a separate reproducible view."""
    root = Path(__file__).resolve().parents[3]
    strict = reference / 'native-class-comparison/artifacts'
    read_retention_run_report(strict)
    manifest = cast('dict', plain(get_manifest()))
    coverage = audit(root)
    generated = json.loads((root / 'targets/ptfkit-py/src/ptfkit/_manifest.json').read_bytes())
    if document_hash(manifest) != document_hash(generated):
        message = 'Installed and generated manifests must agree.'
        raise ValueError(message)
    installed = json.loads((strict / 'ptfkit-manifest.json').read_bytes())
    if document_hash(installed) != document_hash(manifest):
        message = 'Strict reference and installed manifests must agree.'
        raise ValueError(message)
    support = json.loads((reference / 'catalog-support.json').read_bytes())
    datasets = [
        json.loads((reference / f'canonical-{name}.json').read_bytes())
        for name in ('volume', 'mass')
    ]
    reviewed = json.loads((strict / 'dataset.json').read_bytes())
    reviewed_ids = {(s['source_id'], s['sample_id']) for s in reviewed['samples']}
    # Keep reviewed contracts and predictors intact; never promote global unknown material basis.
    for dataset in datasets:
        dataset['samples'] = [
            s for s in dataset['samples'] if (s['source_id'], s['sample_id']) not in reviewed_ids
        ]
        dataset['observations'] = [
            o
            for o in dataset['observations']
            if (o['source_id'], o['sample_id']) not in reviewed_ids
        ]
    datasets.append(reviewed)
    output.mkdir(parents=True, exist_ok=False)
    registration = policy_registry()
    _write(output, 'policies.json', registration)
    matrix, predictions = evaluate_catalog(coverage, support, datasets, manifest)
    evaluation = json.loads((strict / 'evaluation-plan.json').read_bytes())
    candidate_functions = {c['id']: c['function'] for c in evaluation['candidates']}
    strict_predictions = []
    for row in json.loads((strict / 'cohorts.json').read_bytes()):
        cohort = row['cohort']
        if cohort['kind'] == 'maximal':
            strict_predictions.extend(
                {'function': candidate_functions[cohort['candidate_id']], **p}
                for p in cohort['comparisons']
            )
    strict_samples = {(p['function'], p['source_id'], p['sample_id']) for p in strict_predictions}
    for row in matrix:
        row['strict_eligible'] = (
            row['target_pool'].startswith('curve:')
            and (row['function'], row['source_id'], row['sample_id']) in strict_samples
        )
        row['harmonized_eligible'] = row['view'] == 'harmonized'
        row['exploratory_eligible'] = row['view'] == 'exploratory'
        if row['strict_eligible']:
            row['view'] = 'strict'
    reconstructed = fixed_pressure_inventory(matrix)
    _write(output, 'fixed-pressure-targets.json', reconstructed)
    report = reporting(coverage, support, matrix, predictions, strict_predictions)
    report['fixed_pressure_targets'] = {
        pool: dict(
            Counter(p['evidence']['tier'] for p in reconstructed if p['target_pool'] == pool)
        )
        for pool in sorted({p['target_pool'] for p in reconstructed})
    }
    report['ensembles'] = ensemble_pools(predictions)
    report['input_sha256'] = {
        str(path.relative_to(reference)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [
            strict / 'dataset.json',
            strict / 'cohorts.json',
            reference / 'canonical-volume.json',
            reference / 'canonical-mass.json',
            reference / 'catalog-support.json',
            reference / 'eligibility-matrix.json',
        ]
    }
    report['policy_sha256'] = registration['sha256']
    report['implementation_sha256'] = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            Path(__file__),
            root / 'targets/ptfkit-eval/src/ptfkit_eval/harmonization.py',
            root / 'targets/ptfkit-eval/src/ptfkit_eval/harmonized_inputs.py',
        ]
    }
    _write(output, 'harmonized-matrix.json', matrix)
    _write(output, 'harmonized-predictions.json', predictions)
    _write(output, 'strict-predictions.json', strict_predictions)
    (output / 'strict-matrix.json').write_bytes(
        (reference / 'eligibility-matrix.json').read_bytes()
    )
    _write(output, 'summary.json', report)
    _write(output, 'count-summary.json', count_summary(report))
    (output / 'report.md').write_text(render(report), encoding='utf-8')
    _write(
        output,
        'artifact-hashes.json',
        {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())},
    )
    return report


def count_summary(report: dict) -> dict:
    """Keep publication counts and errors separate from private sample-level exports."""
    summary = {key: value for key, value in report.items() if key != 'ensembles'}
    summary['ensembles'] = [
        {
            **{
                key: row[key]
                for key in ('target_pool', 'view', 'members', 'training_observation_tiers')
            },
            'status': row['assessment']['status'],
            'learning_status': row['assessment'].get(
                'learned_status', row['assessment'].get('evidence_status')
            ),
            'recommendation': None,
        }
        for row in report['ensembles']
    ]
    return summary


def reporting(
    coverage: dict, support: dict, matrix: list[dict], predictions: list[dict], strict: list[dict]
) -> dict:
    """Stratify metrics by physical pool and assess strict-value preservation."""
    functions, pools = [], defaultdict(set)
    for function in coverage['functions']:
        fid = function['id']
        for target in catalog_targets(function, support):
            pools[pool_id(target)].add(fid)
        rows = [r for r in matrix if r['function'] == fid]
        points = [p for p in predictions if p['function'] == fid]
        baseline = [p for p in strict if p['function'] == fid]
        index = {
            (p['source_id'], p['sample_id'], p['suction_kpa'], p['water_quantity']): p
            for p in points
        }
        matched = [
            index.get((p['source_id'], p['sample_id'], p['suction_kpa'], p['water_quantity']))
            for p in baseline
        ]
        preserved = bool(baseline) and all(
            b is not None and b['observed'] == a['observed'] and b['predicted'] == a['predicted']
            for a, b in zip(baseline, matched, strict=True)
        )
        if baseline and not preserved:
            message = f'Harmonization changed or lost a strict prediction: {fid}'
            raise ValueError(message)
        functions.append(
            {
                'function': fid,
                'strict_n': len({(p['source_id'], p['sample_id']) for p in baseline}),
                'harmonized_n': len({(p['source_id'], p['sample_id']) for p in points}),
                'reconstructed_targets': sum(
                    p['target_evidence']['tier'] == 'reconstructed' for p in points
                ),
                'derived_predictors': len(
                    {
                        (p['source_id'], p['sample_id'], name)
                        for p in points
                        for name, value in p['predictor_evidence'].items()
                        if value['tier'] == 'derived'
                    }
                ),
                'blockers': dict(Counter(reason for r in rows for reason in r['reasons'])),
                'metrics_by_pool': {
                    pool: _metrics([p for p in points if p['target_pool'] == pool])
                    for pool in sorted({p['target_pool'] for p in points})
                },
                'strict_subset_preserved': preserved if baseline else None,
                'sensitivity': {
                    'strict_only': _metrics(baseline),
                    'harmonized_on_strict_subset': _metrics([p for p in matched if p is not None]),
                    'difference_on_strict_subset': 0.0 if preserved else None,
                },
            }
        )
    pool_reports = []
    for pool, ids in sorted(pools.items()):
        points = [p for p in predictions if p['target_pool'] == pool]
        # Existing strict forecasts are curves; fixed-pressure records must not be inferred.
        strict_ids = {
            p['function']
            for p in strict
            if pool.startswith('curve:') and pool.endswith(p['water_quantity'])
        } & ids
        pool_reports.append(
            {
                'target': pool,
                'catalog_ptfs': len(ids),
                'strict_scored': len(strict_ids),
                'harmonized_scored': len({p['function'] for p in points}),
                'samples': len({(p['source_id'], p['sample_id']) for p in points}),
                'profiles': len(
                    {(p['source_id'], p['profile_id']) for p in points if p['profile_id']}
                ),
            }
        )
    strict_count = sum(f['strict_n'] > 0 for f in functions)
    harmonized_count = sum(f['harmonized_n'] > 0 for f in functions)
    return {
        'schema_version': 1,
        'protocol': 'registered_harmonization_v1',
        'implemented_functions': len(functions),
        'strict_scored_functions': strict_count,
        'harmonized_scored_functions': harmonized_count,
        'coverage_milestone_met': harmonized_count > strict_count,
        'status': 'completed_with_unresolved_predictor_contracts',
        'matrix_counts': dict(Counter(r['view'] for r in matrix)),
        'functions': functions,
        'target_pools': pool_reports,
        'approximate_in_main_leaderboard': False,
        'exploratory_executed': False,
        'limitations': [
            (
                'Unknown units, material/mass basis and PSD boundaries cannot be recovered '
                'by deterministic transformation.'
            ),
            (
                'No source-wide review gate is imposed; only the predictors and target '
                'needed by a function are checked.'
            ),
            (
                'Missing legacy measurement contracts remain unsupported; discovery target '
                'names do not grant execution.'
            ),
            'Per-pool metrics are descriptive; no new final recommendation is authorized.',
        ],
    }


def render(report: dict) -> str:
    lines = [
        '# Harmonized benchmark',
        '',
        (
            f'Catalog: {report["implemented_functions"]}; '
            f'strict scored: {report["strict_scored_functions"]}; '
            f'harmonized scored: {report["harmonized_scored_functions"]}.'
        ),
        '',
        (
            f'Coverage milestone met: {report["coverage_milestone_met"]}. '
            'Approximate observations are excluded.'
        ),
        '',
        (
            '| PTF / pool | Strict N | Harmonized N | Reconstructed targets | '
            'Derived predictors | RMSE | MAE | Bias |'
        ),
        '|---|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for f in report['functions']:
        for pool, metrics in (f['metrics_by_pool'] or {'unsupported': None}).items():
            values = [
                f'{metrics[k]:.6g}' if metrics else '—'
                for k in ('root_mean_squared_error', 'mean_absolute_error', 'mean_error')
            ]
            lines.append(
                '| '
                + ' | '.join(
                    map(
                        str,
                        [
                            f'{f["function"]} / {pool}',
                            f['strict_n'],
                            f['harmonized_n'],
                            f['reconstructed_targets'],
                            f['derived_predictors'],
                            *values,
                        ],
                    )
                )
                + ' |'
            )
    lines.extend(
        [
            '',
            (
                'Function counts span all pools; errors are reported '
                'separately for each physical pool.'
            ),
            '',
            '| Target | Catalog PTFs | Strict scored | Harmonized scored | Samples | Profiles |',
            '|---|---:|---:|---:|---:|---:|',
        ]
    )
    lines.extend(
        '| '
        + ' | '.join(
            map(
                str,
                [
                    p['target'],
                    p['catalog_ptfs'],
                    p['strict_scored'],
                    p['harmonized_scored'],
                    p['samples'],
                    p['profiles'],
                ],
            )
        )
        + ' |'
        for p in report['target_pools']
    )
    lines.extend(['', *report['limitations'], ''])
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.benchmark, args.output)


if __name__ == '__main__':
    main()
