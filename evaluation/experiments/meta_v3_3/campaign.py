"""Expand exploratory coverage through shared source-contract and evidence policies."""

# ruff: noqa: INP001, SLF001 - Reuse pinned experiment helpers without changing main behavior.

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import cast

import ptfkit._ptfkit as native_extension
import yaml
from ptfkit import get_manifest
from ptfkit_eval.documents import canonical_json, plain
from ptfkit_eval.harmonization import EvidenceValue
from ptfkit_eval.water import canonical_water_contract

from evaluation.experiments.meta_v3_3 import campaign_comparisons as comparisons
from evaluation.experiments.meta_v3_3 import campaign_contracts as contracts
from evaluation.experiments.meta_v3_3 import campaign_inputs as inputs
from evaluation.experiments.meta_v3_3 import campaign_reporting as reporting
from evaluation.experiments.meta_v3_3 import campaign_targets as targets
from evaluation.experiments.meta_v3_3 import comparative, rolling
from evaluation.experiments.meta_v3_3 import exploratory as prior
from evaluation.experiments.meta_v3_3.summaries import catalog_support


def metrics(points: list[dict]) -> dict | None:
    """Compute finite same-unit descriptive errors with equal sample weight."""
    if not points:
        return None
    groups = defaultdict(list)
    identities = set()
    for p in points:
        identity = (p['source_id'], p['sample_id'], p['pressure_kpa'])
        if identity in identities:
            message = 'Duplicate function/sample/target coordinate in a metric cohort.'
            raise ValueError(message)
        identities.add(identity)
        groups[identity[:2]].append(p['predicted'] - p['observed'])
    means = [math.fsum(v) / len(v) for v in groups.values()]
    absolute = [math.fsum(abs(x) for x in v) / len(v) for v in groups.values()]
    squares = [math.fsum(x * x for x in v) / len(v) for v in groups.values()]
    return {
        'rmse': math.sqrt(math.fsum(squares) / len(squares)),
        'mae': math.fsum(absolute) / len(absolute),
        'bias': math.fsum(means) / len(means),
    }


def _required(target: dict, function: dict, dataset: dict) -> dict:
    if target['adapter'] == 'existing_model_adapter_v1':
        return dict(target['curve']['target'])
    field = next((f for f in function['fields'] if f['name'] == target.get('field')), None)
    measurement = field.get('measurement') if field else None
    return {
        'quantity': target['quantity'],
        'unit': 'volume_fraction'
        if target['quantity'] == 'volumetric_water_content'
        else 'mass_fraction',
        'denominator_basis': 'bulk_volume'
        if target['quantity'] == 'volumetric_water_content'
        else 'dry_soil_mass',
        'material_basis': measurement['basis']['material']
        if measurement
        else dataset['target']['material_basis'],
    }


def water_predictors(
    function: dict,
    dataset: dict,
    sample: dict,
    row: dict | None,
    registration: dict,
    *,
    enabled: bool,
    interpolate: bool = True,
) -> dict[str, EvidenceValue]:
    if not enabled:
        return {}
    result = {}
    for binding in function['inputs']:
        description = binding.get('description', '')
        pressure = contracts.explicit_pressure(description)
        if pressure is None or not any(
            word in description.lower()
            for word in ('water content', 'moisture content', 'moisture retention')
        ):
            continue
        value, reason = targets.reconstruct(
            dataset,
            sample,
            pressure,
            'log_pressure_linear_interpolation_v1',
            {},
            interpolate=interpolate,
        )
        if reason or value is None:
            continue
        quantity = (
            'gravimetric_water_content'
            if 'gravimetric' in description.lower()
            else ('volumetric_water_content' if 'volumetric' in description.lower() else None)
        )
        if quantity is None:
            continue
        unit, denominator = canonical_water_contract(quantity)
        required = {
            'quantity': quantity,
            'unit': unit,
            'denominator_basis': denominator,
            'material_basis': dataset['target']['material_basis'],
        }
        value, reason = targets.convert_target(
            value, dataset['target'], required, row, registration
        )
        if value:
            result[binding['name']] = EvidenceValue(
                value.value,
                value.tier,
                'retention_predictor_v1'
                if 'water content' in description.lower()
                else 'retention_predictor_terminology_v2',
                value.sources,
                (('requested_pressure_kpa', pressure), ('conditional_retention_input', True)),
                (value,),
            )
    return result


def tier(proofs: dict, target: dict, *, bridge: bool) -> str:
    def policies(value: dict) -> set[str]:
        return {value['policy']} | {key for parent in value['parents'] for key in policies(parent)}

    all_values = [target, *proofs.values()]
    approximate = bridge or any(v['tier'] == 'approximate' for v in all_values)
    reconstructed = any('reconstruct' in v['tier'] for v in all_values)
    material = any(
        p in {'same_sample_water_basis_conversion_v1', 'meta_target_material_v1'}
        for v in all_values
        for p in policies(v)
    )
    if approximate:
        return 'E4' if reconstructed or material else 'E3'
    if reconstructed:
        return 'E2'
    return 'E1' if any(v['tier'] in ('converted', 'derived') for v in all_values) else 'E0'


def evaluate(  # noqa: C901, PLR0912, PLR0915 - Independent per-coordinate scientific decisions.
    context: dict, stage: dict, scenario: str, route: str
) -> tuple[list[dict], list[dict]]:
    """Revisit every current function, including unsupported target contracts."""
    records, points = [], []
    disabled = context.get('disabled', set())
    for function in context['catalog']:
        fid = function['id']
        target_list = contracts.targets(function, context['support'])
        if not target_list:
            reason = (
                'unknown_output_water_basis'
                if contracts.unknown_water_basis(function)
                else (
                    'model_variant_or_target_adapter_unresolved'
                    if any(
                        f.get('quantity')
                        in {
                            'van_genuchten_alpha',
                            'van_genuchten_n',
                            'varallyai_m',
                            'hutson_cass_b',
                        }
                        for f in function['fields']
                    )
                    else 'operational_target_absent'
                )
            )
            records.append(
                {
                    'function': fid,
                    'stage': stage['id'],
                    'scenario': scenario,
                    'route': route,
                    'status': 'blocked',
                    'reasons': [reason],
                    'potential_samples': 0,
                }
            )
            continue
        bridge = fid not in context['public_ids']
        for dataset in context['datasets']:
            for sample in dataset['samples']:
                identity = (sample['source_id'], sample['sample_id'])
                row = context['rows'].get(identity)
                if row and not stage['density_link'] and row.get('linked_density'):
                    row = {k: v for k, v in row.items() if k != 'linked_density'}
                water = water_predictors(
                    function,
                    dataset,
                    sample,
                    row,
                    context['old_registration'],
                    enabled=stage['water_predictors'] and 'water_predictors' not in disabled,
                    interpolate='interpolation' not in disabled,
                )
                values, proofs, input_reasons = inputs.resolve_inputs(
                    function,
                    sample,
                    row,
                    scenario,
                    context['old_registration'],
                    representative=stage['representative'] and 'class_psd' not in disabled,
                    water_inputs=water,
                    organic_conversion='oc_om' not in disabled,
                    depth_derivation='depth' not in disabled,
                    derive_texture_class='usda_class' not in disabled,
                    organic_aliases='oc_om' not in disabled,
                    axis_inputs={t['axis_input'] for t in target_list if 'axis_input' in t},
                )
                for target in target_list:
                    reasons = list(input_reasons)
                    record = {
                        'function': fid,
                        'stage': stage['id'],
                        'scenario': scenario,
                        'route': route,
                        'source_id': identity[0],
                        'sample_id': identity[1],
                        'profile_id': sample.get('profile_id'),
                        'target_pool': contracts.pool_id(target),
                        'status': 'blocked',
                        'reasons': reasons,
                        'adapter': target['adapter'],
                        'public_measurement_contract': not bridge,
                        'reported_usda_class_available': inputs.reported_class(sample) is not None,
                        'usda_class_policy_supported': any(
                            i.get('_ref_type') == 'UsdaTextureClass' for i in function['inputs']
                        ),
                        'predictors': proofs,
                        'potential_samples': 1,
                    }
                    records.append(record)
                    if bridge and (not stage['legacy'] or 'spec_adapters' in disabled):
                        reasons.append('measurement_contract_adapter_absent')
                    if 'axis_input' in target:
                        binding = next(
                            i for i in function['inputs'] if i['name'] == target['axis_input']
                        )
                        axis_value = contracts.axis_value(target)
                        if not inputs.legacy_domain(axis_value, binding):
                            reasons.append('computational_domain:' + binding['name'])
                    if target['quantity'] == 'dry_bulk_density':
                        if route != 'log_pressure_linear_interpolation_v1':
                            reasons.append('fit_target_route_not_applicable')
                            continue
                        observed = inputs.density(row, context['old_registration']) if row else None
                        if observed is None:
                            reasons.append('target_property_absent')
                        target_reason = None
                    else:
                        observed, target_reason = reconstruct_target(
                            context,
                            function,
                            target,
                            dataset,
                            sample,
                            row=row,
                            route=route,
                            disabled=disabled,
                        )
                    if target_reason:
                        reasons.append(target_reason)
                    if observed is None or reasons:
                        record['reasons'] = sorted(set(reasons))
                        continue
                    record['target_evidence'] = observed.document()
                    try:
                        prediction = contracts.predicted(
                            function, target, values, context['manifest']
                        )
                        prediction = finite_prediction(prediction)
                    except (ValueError, ArithmeticError, TypeError) as error:
                        record['reasons'] = [
                            'implementation_adapter_failure'
                            if isinstance(error, TypeError)
                            else 'wet_branch_adapter_absent'
                            if 'No wet-branch' in str(error)
                            else 'native_domain_or_adapter_failure'
                        ]
                        record['execution_error'] = type(error).__name__ + ': ' + str(error)
                        continue
                    record['status'] = 'executed'
                    level = tier(proofs, observed.document(), bridge=bridge)
                    record['minimum_tier'] = level
                    points.append(
                        {
                            'function': fid,
                            'scenario': scenario,
                            'route': route,
                            'source_id': identity[0],
                            'sample_id': identity[1],
                            'profile_id': sample.get('profile_id'),
                            'pressure_kpa': target.get('pressure_kpa'),
                            'target_pool': contracts.pool_id(target),
                            'quantity': target['quantity'],
                            'observed': observed.value,
                            'predicted': prediction,
                            'minimum_tier': level,
                            'predictor_evidence': proofs,
                            'target_evidence': observed.document(),
                            'adapter': target['adapter'],
                            'source_specification': function['specification'],
                            'recommendation_eligible': False,
                        }
                    )
    expected = {f['id'] for f in context['catalog']}
    if len(expected) != len(context['catalog']) or {r['function'] for r in records} != expected:
        message = 'Every catalog function must have an explicit execution or blocker decision.'
        raise ValueError(message)
    return records, points


def reconstruct_target(
    context: dict,
    function: dict,
    target: dict,
    dataset: dict,
    sample: dict,
    *,
    row: dict | None,
    route: str,
    disabled: set,
) -> tuple[EvidenceValue | None, str | None]:
    pressures = target.get('component_pressures_kpa', [target.get('pressure_kpa')])
    parents = []
    for pressure in pressures:
        value, reason = targets.reconstruct(
            dataset,
            sample,
            pressure,
            route,
            context['fits'],
            interpolate='interpolation' not in disabled,
        )
        if value:
            value, reason = targets.convert_target(
                value,
                dataset['target'],
                _required(target, function, dataset),
                row,
                context['old_registration'],
                density_conversion='density_conversion' not in disabled,
            )
        if value is None or reason:
            return None, reason
        parents.append(value)
    if target['kind'] != 'pressure_difference':
        return parents[0], None
    difference = cast('float', parents[0].value) - cast('float', parents[1].value)
    if not 0 <= difference <= 1:
        return None, 'physically_invalid_pressure_difference'
    return EvidenceValue(
        difference,
        max(
            parents,
            key=lambda p: {
                'strict': 0,
                'converted': 1,
                'derived': 2,
                'reconstructed': 3,
                'approximate': 4,
            }.get(str(p.tier), 4),
        ).tier,
        'explicit_pressure_difference_v1',
        tuple(sorted({s for p in parents for s in p.sources})),
        (('component_pressures_kpa', tuple(pressures)), ('formula', 'theta(A) - theta(B)')),
        tuple(parents),
    ), None


def finite_prediction(value: float) -> float:
    if not math.isfinite(value):
        message = 'Nonfinite selected prediction.'
        raise ValueError(message)
    return value


def prepare(reference: Path, main: Path, workbook: Path) -> dict:
    root = Path(__file__).resolve().parents[3]
    hashes = {
        'strict': prior.verify_artifacts(reference),
        'harmonized': prior.verify_artifacts(main),
    }
    main_summary = json.loads((main / 'summary.json').read_bytes())
    if any(
        prior._hash(reference / name) != expected
        for name, expected in main_summary['input_sha256'].items()
    ):
        message = 'The harmonized run does not match the supplied strict benchmark.'
        raise ValueError(message)
    summary = json.loads((reference / 'summary.json').read_bytes())
    if prior._hash(workbook) != summary['workbook_sha256']:
        message = 'Workbook does not match the pinned benchmark.'
        raise ValueError(message)
    datasets = [
        json.loads((reference / f'canonical-{name}.json').read_bytes())
        for name in ('volume', 'mass')
    ]
    fit_artifact = json.loads((reference / 'approximation-fits.json').read_bytes())
    if fit_artifact['dataset'] != datasets[0]:
        message = 'Fit artifact uses a different canonical volume dataset.'
        raise ValueError(message)
    reviewed = json.loads(
        (reference / 'native-class-comparison/artifacts/dataset.json').read_bytes()
    )
    identities = {(s['source_id'], s['sample_id']) for s in reviewed['samples']}
    for dataset in datasets:
        dataset['samples'] = [
            s for s in dataset['samples'] if (s['source_id'], s['sample_id']) not in identities
        ]
        dataset['observations'] = [
            o for o in dataset['observations'] if (o['source_id'], o['sample_id']) not in identities
        ]
    datasets.append(reviewed)
    mapping = yaml.safe_load((root / 'evaluation/datasets/meta_v3_3.yaml').read_bytes())
    rows = prior.raw_rows(
        workbook, json.loads((reference / 'predictor-audit.json').read_bytes()), mapping
    )
    retained = {(s['source_id'], s['sample_id']) for d in datasets for s in d['samples']}
    rows = {key: value for key, value in rows.items() if key in retained}
    targets.record_formulas(workbook, rows)
    linked = targets.discover_density(workbook, rows, mapping)
    manifest = cast('dict', plain(get_manifest()))
    if manifest != json.loads((root / 'targets/ptfkit-py/src/ptfkit/_manifest.json').read_bytes()):
        message = 'Installed and generated manifests must agree.'
        raise ValueError(message)
    context = {
        'catalog': contracts.load_catalog(root),
        'manifest': manifest,
        'public_ids': {f['id'] for f in manifest['functions']},
        'support': catalog_support(manifest),
        'datasets': datasets,
        'rows': rows,
        'fits': targets.accepted_fit_index(fit_artifact, datasets),
        'old_registration': json.loads(
            Path(__file__).with_name('exploratory-policies.json').read_bytes()
        ),
        'registration': json.loads(Path(__file__).with_name('campaign-policies.json').read_bytes()),
        'density_links': linked,
        'input_hashes': hashes,
        'root': root,
        'strict_ids': {
            r['function'] for r in json.loads((main / 'strict-predictions.json').read_bytes())
        },
    }
    rolling.refresh_strict(context)
    return context


def run(  # noqa: PLR0915 - One complete catalog/ablation artifact transaction.
    reference: Path, main: Path, workbook: Path, output: Path, previous: Path | None = None
) -> dict:
    if any(output.resolve().is_relative_to(p.resolve()) for p in (reference, main)):
        message = 'Campaign output must be separate from the pinned main benchmarks.'
        raise ValueError(message)
    context = prepare(reference, main, workbook)
    baseline_path = (
        previous or context['root'] / 'evaluation/datasets/meta_v3_3.campaign-summary.json'
    )
    baseline = json.loads(baseline_path.read_bytes())
    output.mkdir(parents=True, exist_ok=False)
    (output / 'policies.json').write_bytes(canonical_json(context['registration']))
    (output / 'inherited-policies.json').write_bytes(canonical_json(context['old_registration']))
    (output / 'catalog-contracts.json').write_bytes(
        canonical_json(
            [
                {
                    'function': function['id'],
                    'specification': function['specification'],
                    'public_api': function.get('public_api'),
                    'predictor_names': [binding['name'] for binding in function['inputs']],
                    'target_bindings': contracts.targets(function, context['support']),
                }
                for function in context['catalog']
            ]
        )
    )
    stages: list[dict] = []
    previous_functions = set()
    final_records, final_points = [], []
    initial_blockers = None
    for stage in context['registration']['stages']:
        records, points = [], []
        for scenario in context['registration']['psd_scenarios']:
            r, p = evaluate(
                context, stage, scenario, context['registration']['primary_target_route']
            )
            records.extend(r)
            points.extend(p)
        stage_functions = {p['function'] for p in points} | context['strict_ids']
        stages.append(
            {
                'stage': stage['id'],
                'assessed_catalog_functions': len({r['function'] for r in records}),
                'functions': sorted(stage_functions),
                'new_functions': sorted(stage_functions - previous_functions),
                'combinations': len(points),
            }
        )
        previous_functions = stage_functions
        (output / (stage['id'] + '-coverage.json')).write_bytes(canonical_json(stages[-1]))
        if stage == context['registration']['stages'][0]:
            (output / 'initial-matrix.json').write_bytes(canonical_json(records))
            initial_blockers = reporting.blocker_funnel(
                context['catalog'], records, stage_functions
            )
        final_records, final_points = records, points
    (output / 'matrix.json').write_bytes(canonical_json(final_records))
    (output / 'predictions.json').write_bytes(canonical_json(final_points))
    (output / 'strict-matrix.json').write_bytes(canonical_json(context['strict_matrix']))
    (output / 'strict-predictions.json').write_bytes(canonical_json(context['strict_points']))
    primary = reporting.summarize(
        context['catalog'], final_records, final_points, context['strict_ids'], metrics
    )
    diagnostic_points, diagnostic_coverage = [], []
    final_stage = context['registration']['stages'][-1]
    for route in context['registration']['diagnostic_target_routes']:
        selected = []
        for scenario in context['registration']['psd_scenarios']:
            records, points = evaluate(context, final_stage, scenario, route)
            selected.extend(points)
        diagnostic_points.extend(selected)
        diagnostic_coverage.append(
            {
                'route': route,
                'scored_functions': sorted({p['function'] for p in selected}),
                'executions': len(selected),
            }
        )
    (output / 'accepted-fit-predictions.json').write_bytes(canonical_json(diagnostic_points))
    ablations = []
    for disabled in (
        'spec_adapters',
        'class_psd',
        'interpolation',
        'water_predictors',
        'density_conversion',
        'oc_om',
        'usda_class',
        'depth',
    ):
        selected = []
        for scenario in context['registration']['psd_scenarios']:
            _, points = evaluate(
                {**context, 'disabled': {disabled}},
                final_stage,
                scenario,
                context['registration']['primary_target_route'],
            )
            selected.extend(points)
        available = {p['function'] for p in selected} | context['strict_ids']
        lost = sorted(previous_functions - available)
        ablations.append(
            {
                'disabled_policy_group': disabled,
                'remaining_functions': len(available),
                'lost_functions': lost,
                'lost_function_count': len(lost),
                'executions': len(selected),
                'effects_are_not_additive': True,
            }
        )
        (output / ('ablation-' + disabled + '.json')).write_bytes(canonical_json(ablations[-1]))
    all_comparisons = [*final_points, *diagnostic_points]
    summary: dict = {
        **primary,
        'protocol': context['registration']['protocol'],
        'stages': stages,
        'catalog_count': len(context['catalog']),
        'initial_blockers': initial_blockers,
        'policy_contributions': ablations,
        'accepted_fit_routes': diagnostic_coverage,
        'density_links': context['density_links'],
        'density_audit': targets.density_audit(
            context['datasets'], context['rows'], context['old_registration']
        ),
        'accepted_fits': len(context['fits']),
        'recommendation': None,
    }
    summary['common_cohort_comparisons'] = comparisons.comparative_tables(all_comparisons, metrics)
    summary['scenario_sensitivity'] = comparisons.scenario_sensitivity(
        all_comparisons, context['registration']['psd_scenarios'], metrics
    )
    summary['ensembles'] = comparisons.ensembles(all_comparisons, metrics)
    summary['catalog_refresh'] = rolling.catalog_refresh(context['catalog'], baseline)
    summary['catalog_refresh'].update(context['public_api_audit'])
    summary['assumption_ladder'] = rolling.ladder_delta(summary['assumption_ladder'], baseline)
    summary['comparative_benchmark'] = comparative.analyze(
        [*all_comparisons, *context['strict_points']],
        dataset_samples=len(
            {(s['source_id'], s['sample_id']) for d in context['datasets'] for s in d['samples']}
        ),
    )
    summary['ranking_robustness'] = {
        'psd_scenarios': comparative.robustness(all_comparisons, dimension='scenario'),
        'target_routes': comparative.robustness(all_comparisons, dimension='route'),
    }
    summary['function_audit'] = rolling.function_audit(context, final_records, summary)
    summary['target_evidence_diagnostics'] = rolling.target_diagnostics(final_points)
    disagreements = [
        {
            'function': p['function'],
            'scenario': p['scenario'],
            'route': p['route'],
            'source_id': p['source_id'],
            'sample_id': p['sample_id'],
            'target_pool': p['target_pool'],
            'original_basis_disagreement': next(
                (
                    v['details']['fit_minus_interpolation']
                    for v in walk_evidence(p['target_evidence'])
                    if v['policy'] == 'accepted_fit_target_v1'
                ),
                None,
            ),
        }
        for p in diagnostic_points
    ]
    threshold = context['registration']['fit_disagreement_volume_fraction_threshold']
    summary['fit_disagreement'] = {
        'threshold_original_volume_fraction': threshold,
        'executions': len(disagreements),
        'above_threshold': sum(
            abs(p['original_basis_disagreement']) > threshold
            for p in disagreements
            if p['original_basis_disagreement'] is not None
        ),
        'maximum_absolute': max(
            (
                abs(p['original_basis_disagreement'])
                for p in disagreements
                if p['original_basis_disagreement'] is not None
            ),
            default=None,
        ),
    }
    (output / 'fit-disagreement.json').write_bytes(canonical_json(disagreements))
    summary['input_sha256'] = {
        **context['input_hashes'],
        'workbook': prior._hash(workbook),
        'previous_exploratory_summary': prior._hash(
            context['root'] / 'evaluation/datasets/meta_v3_3.exploratory-summary.json'
        ),
        'mapping': prior._hash(context['root'] / 'evaluation/datasets/meta_v3_3.yaml'),
        'previous_benchmark': prior._hash(baseline_path),
        'manifest': prior._hash(context['root'] / 'targets/ptfkit-py/src/ptfkit/_manifest.json'),
    }
    summary['implementation_sha256'] = {
        p.relative_to(context['root']).as_posix(): prior._hash(p)
        for p in sorted(Path(__file__).parent.glob('*.py'))
    }
    summary['specification_sha256'] = {
        p.relative_to(context['root']).as_posix(): prior._hash(p)
        for p in sorted((context['root'] / 'specs').rglob('*.yaml'))
    }
    summary['native_extension_sha256'] = prior._hash(Path(native_extension.__file__))
    if context['input_hashes'] != {
        'strict': prior.verify_artifacts(reference),
        'harmonized': prior.verify_artifacts(main),
    }:
        message = 'Pinned strict/harmonized artifacts changed during the campaign.'
        raise ValueError(message)
    summary['main_artifacts_unchanged'] = True
    summary['new_functions_since_previous_exploratory'] = sorted(
        previous_functions - set(stages[0]['functions'])
    )
    (output / 'summary.json').write_bytes(canonical_json(summary))
    (output / 'report.md').write_text(reporting.render(summary), encoding='utf-8')
    (output / 'benchmark.md').write_text(rolling.render(summary), encoding='utf-8')
    (output / 'artifact-hashes.json').write_bytes(
        canonical_json({p.name: prior._hash(p) for p in sorted(output.iterdir())})
    )
    return summary


def walk_evidence(proof: dict) -> list[dict]:
    return [proof, *(v for parent in proof['parents'] for v in walk_evidence(parent))]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--harmonized', type=Path, required=True)
    parser.add_argument('--workbook', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument(
        '--previous', type=Path, help='Previous completed summary for catalog/tier deltas'
    )
    args = parser.parse_args()
    run(args.benchmark, args.harmonized, args.workbook, args.output, args.previous)


if __name__ == '__main__':
    main()
