"""Separate scientific readiness from implementation gaps for every implemented PTF."""

# ruff: noqa: INP001 - Standalone experiment helpers.

from __future__ import annotations

import json
from collections import Counter, defaultdict


# Candidate columns are discovery leads, never bindings or measurement crosswalks.
# Roles are defined in meta_v3_3.yaml; aliases below only group review work.
INPUT_ROLES = {
    'sand': 'sand_fraction',
    'silt': 'silt_fraction',
    'clay': 'clay_fraction',
    'bulk_density': 'dry_bulk_density',
    'carbon': 'organic_carbon',
    'organic_carbon': 'organic_carbon',
    'soil_organic_carbon': 'organic_carbon',
    'soc': 'organic_carbon',
    'organic_matter': 'humus_content',
    'soil_organic_matter': 'humus_content',
    'soil_texture': 'texture_class',
    'depth': 'depth_interval',
    'mean_depth': 'depth_interval',
    'ph': 'ph',
    'porosity': 'porosity',
    'total_porosity': 'porosity',
}


def audit(
    coverage: dict,
    matrix: list[dict],
    mapping: dict,
    support: dict,
    candidate_values: dict | None = None,
) -> dict:
    """Audit the mapped workbook scope without treating absent adapters as science.

    A missing mapped role is unresolved discovery, not proof that no cell in
    the workbook contains a quantity. In particular no permanent impossibility
    is inferred from unheaded PSD blocks or source-specific trailing columns.
    """
    columns = {
        c['role']: c
        for s in mapping['worksheets']
        if s['id'] == 'samples_master'
        for c in s['columns']
    }
    indexed = defaultdict(list)
    for row in matrix:
        indexed[row['function']].append(row)
    records: list[dict] = []
    groups = defaultdict(list)
    for function in coverage['functions']:
        fid = function['id']
        rows = indexed[fid]
        scored = {r['master_key'] for r in rows if r['status'] == 'eligible_and_evaluated'}
        eligible = scored | {r['master_key'] for r in rows if r['scientific_status'] == 'eligible'}
        implementation_only = bool(eligible) and not scored
        definitions: list[dict] = []
        for item in function['inputs']:
            role = INPUT_ROLES.get(item['name'])
            column = columns.get(role)
            definitions.append(
                {
                    **item,
                    'candidate_role': role,
                    'candidate_column': column['column'] if column else None,
                    'availability': 'candidate_requires_measurement_review'
                    if column
                    else 'not_inventoried',
                    'binding_authorized': False,
                }
            )
        available = support.get(fid, {})
        implementation = []
        if not function['manifest_eligible']:
            implementation.append('public_measurement_contract')
        if not available.get('curves') and not available.get('fixed_outputs'):
            implementation.append('target_adapter_or_binding')
        if any('missing_input_binding' in r['reasons'] for r in rows):
            implementation.append('input_binding')
        scientific = sorted(
            {
                reason
                for r in rows
                for reason in r['reasons']
                if reason
                not in {
                    'unresolved_measurement_contract',
                    'unsupported_adapter_or_prediction_target',
                    'missing_input_binding',
                }
            }
        )
        # Source review has confirmed no additional Panina numeric predictor
        # contract. Table-2 coordinates are authorized for Cosby alone.
        panina = 'scored' if scored else 'requires_additional_scientific_review'
        signature = ', '.join(sorted(i['name'] for i in function['inputs']))
        groups[signature].append(fid)
        uninventoried = [i['name'] for i in definitions if i['availability'] == 'not_inventoried']
        quantities = sorted({o['quantity'] for o in function['outputs'] if o['quantity']})
        main_blocker = (
            'predictor_not_inventoried:' + ','.join(uninventoried)
            if uninventoried
            else 'source_specific_predictor_definitions'
        )
        if not set(quantities) & {'volumetric_water_content', 'gravimetric_water_content'}:
            main_blocker = 'observed_target_not_reviewed:' + ','.join(quantities)
        elif 'exact_pressure_target_unavailable' in scientific:
            main_blocker = 'exact_pressure_target_and_predictor_review'
        records.append(
            {
                'function': fid,
                'source': function['source'],
                'target': function['prediction_target'],
                'output_quantities': quantities,
                'required_predictors': [i['name'] for i in function['inputs']],
                'predictor_definitions': definitions,
                'input_signature': signature,
                'current_eligible_samples': len(eligible),
                'real_data_scored_samples': len(scored),
                'main_blocker': None
                if scored
                else 'execution_or_binding'
                if implementation_only
                else main_blocker,
                'scientific_blockers': []
                if eligible
                else scientific or ['source_specific_input_and_target_evidence'],
                'implementation_blockers': implementation,
                'implementation_only_blocked': implementation_only,
                'panina_support': panina,
                'panina_additional_predictors': []
                if scored
                else [i['name'] for i in function['inputs']],
                'not_inventoried_predictors': uninventoried,
                'single_claim_unlock': 'not_established',
                'meta_impossibility': 'not_established',
                'unlock_priority': 'already_scored' if scored else 'review_shared_input_signature',
            }
        )
    scored_ids = {r['function'] for r in records if r['real_data_scored_samples']}
    record_index = {r['function']: r for r in records}
    source_impacts = []
    for source in sorted({r['source_id'] for r in matrix}):
        potential = [
            r
            for r in matrix
            if r['source_id'] == source
            and r['observation_count']
            and r['scientific_status'] != 'scientifically_incompatible'
            and 'exact_pressure_target_unavailable' not in r['reasons']
            and r['target'] in record_index[r['function']]['output_quantities']
            and not record_index[r['function']]['not_inventoried_predictors']
            and (
                candidate_values is None
                or all(
                    candidate_values.get(r['master_key'], {}).get(i['candidate_column']) is not None
                    for i in record_index[r['function']]['predictor_definitions']
                )
            )
        ]
        new_ids = sorted({r['function'] for r in potential} - scored_ids)
        source_impacts.append(
            {
                'source_id': source,
                'new_functions_upper_bound': len(new_ids),
                'new_functions': new_ids,
                'new_scoring_combinations_upper_bound': sum(
                    r['status'] != 'eligible_and_evaluated' for r in potential
                ),
                'status': 'conditional_on_all_predictor_target_and_implementation_claims',
            }
        )
    return {
        'scope': 'all_implemented_functions_mapped_workbook_and_reviewed_panina_overlay',
        'counts': {
            'implemented': len(records),
            'real_data_scored': len(scored_ids),
            'implementation_only_blocked': sum(r['implementation_only_blocked'] for r in records),
            'scientifically_blocked': sum(not r['current_eligible_samples'] for r in records),
            'with_implementation_coblockers': sum(
                bool(r['implementation_blockers'])
                for r in records
                if not r['current_eligible_samples']
            ),
            'with_not_inventoried_predictors': sum(
                bool(r['not_inventoried_predictors'])
                for r in records
                if not r['current_eligible_samples']
            ),
            'proven_impossible_on_meta': 0,
            'additional_panina_implementation_only_unlocks': 0,
        },
        'functions': records,
        'input_families': [
            {
                'signature': signature,
                'functions': ids,
                'count': len(ids),
                'blocker': 'review_source_specific_definitions_jointly_before_binding',
            }
            for signature, ids in sorted(groups.items())
        ],
        'source_impacts': sorted(
            source_impacts,
            key=lambda r: (
                -r['new_functions_upper_bound'],
                -r['new_scoring_combinations_upper_bound'],
                r['source_id'],
            ),
        ),
        'source_ceiling_policy': (
            'requires_populated_candidate_columns_and_matching_output_quantity; '
            'excludes_uninventoried_inputs; exact_pressure_constraints_where_registered; '
            'missing_output_contracts_still_need_review'
        ),
        'status_counts': dict(Counter(r['panina_support'] for r in records)),
    }


def target_pools(coverage: dict, support: dict, ensemble: dict) -> list[dict]:
    """Inventory curve and exact-pressure pools separately from other output families."""
    pools = defaultdict(set)
    for function in coverage['functions']:
        fid = function['id']
        contract = support.get(fid, {})
        for curve in contract.get('curves', []):
            pools[f'wrc:{curve["target"]["quantity"]}'].add(fid)
        for point in contract.get('fixed_outputs', []):
            if point['suction_kpa'] is not None:
                pools[f'{point["measurement"]["quantity"]}:{point["suction_kpa"]:g}kPa'].add(fid)
        for quantity in {o['quantity'] for o in function['outputs'] if o['quantity']}:
            if quantity not in ('volumetric_water_content', 'gravimetric_water_content'):
                pools[f'other:{quantity}'].add(fid)
    return [
        {
            'target': name,
            'catalog_functions': sorted(ids),
            'scored_atomic_count': sum(r['kind'] == 'atomic' for r in ensemble['candidates'])
            if name == 'wrc:volumetric_water_content'
            else 0,
            'common_n': ensemble['candidates'][0]['common_n']
            if name == 'wrc:volumetric_water_content'
            else 0,
            'status': 'descriptive'
            if name == 'wrc:volumetric_water_content'
            else 'not_scored_requires_scientific_review',
        }
        for name, ids in sorted(pools.items())
    ]


def render(document: dict, ensemble: dict) -> str:
    """Expose coverage, performance and ensemble value as distinct questions."""
    lines = [
        '# Function coverage audit',
        '',
        'Candidate columns and name aliases are review leads, never authorized bindings.',
        'Not inventoried means absent from the mapped roles, not proven absent from the workbook.',
        'Cosby Table 2 coordinates cannot replace measured particle fractions for other PTFs.',
        '',
        '## Coverage',
        '',
        f'Counts: `{json.dumps(document["counts"], sort_keys=True)}`.',
        '',
        (
            '| Function | Target | Required predictors | Predictor definitions | '
            'Current eligible samples | Main blocker | Can Panina support it? | Unlock priority |'
        ),
        '| --- | --- | --- | --- | ---: | --- | --- | --- |',
    ]
    for row in document['functions']:
        definitions = []
        for item in row['predictor_definitions']:
            descriptor = (
                json.dumps(item['measurement'], sort_keys=True)
                if item['measurement']
                else item.get('description') or item['unit']
            )
            definitions.append(
                f'{item["name"]}: {descriptor}; candidate={item["candidate_column"]}'
            )
        cells = [
            row['function'],
            row['target'],
            ', '.join(row['required_predictors']),
            '; '.join(definitions),
            row['current_eligible_samples'],
            row['main_blocker'] or 'scored',
            row['panina_support'],
            row['unlock_priority'],
        ]
        lines.append(
            '| ' + ' | '.join(str(c).replace('|', '\\|').replace('\n', ' ') for c in cells) + ' |'
        )
    lines += [
        '',
        '## Shared input families',
        '',
        '| Signature | Functions | Shared review |',
        '| --- | --- | --- |',
    ]
    lines += [
        f'| {r["signature"]} | {", ".join(r["functions"])} | {r["blocker"]} |'
        for r in document['input_families']
    ]
    lines += [
        '',
        '## Performance',
        '',
        (
            'The current volumetric WRC pool contains two atomic candidates. '
            'Fixed-pressure pools have no scored candidates: no exact 10, 33 or 1500 kPa '
            'Panina observations. Other output quantities remain inventoried, '
            'without claimed scores.'
        ),
        '',
        '## Ensemble value',
        '',
        '| Candidate | Kind | Common N | Coverage | RMSE | MAE | Bias | Status |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |',
    ]
    for r in ensemble['candidates']:
        m = r['metrics']
        lines.append(
            f'| {r["id"]} | {r["kind"]} | {r["common_n"]} | {r["coverage"]} | '
            f'{m["root_mean_squared_error"]:.10f} | {m["mean_absolute_error"]:.10f} | '
            f'{m["mean_error"]:.10f} | {r["status"]} |'
        )
    lines += [
        '',
        (
            '| Target | Best atomic | Best ensemble | Delta RMSE '
            '(ensemble minus atomic) | Evidence status |'
        ),
        '| --- | --- | --- | ---: | --- |',
        (
            f'| volumetric WRC | {ensemble["best_atomic"]} | {ensemble["best_ensemble"]} | '
            f'{ensemble["delta_rmse_ensemble_minus_atomic"]:.10f} | {ensemble["evidence_status"]} |'
        ),
        '',
        (
            'The fixed mean uses weights 0.5/0.5. Trained convex and learned blend assessment '
            'require independent profile groups; no full-data weights are fitted as a fallback.'
        ),
        '',
        '## Source unlock ceilings',
        '',
        (
            'These broad ceilings include implementation and scientific co-blockers. '
            'They are not source-only gains or expected releases.'
        ),
        '',
        '| Source | New PTF upper bound | New combinations upper bound |',
        '| --- | ---: | ---: |',
    ]
    lines += [
        f'| {r["source_id"]} | {r["new_functions_upper_bound"]} | '
        f'{r["new_scoring_combinations_upper_bound"]} |'
        for r in document['source_impacts']
    ]
    lines += [
        '',
        '## Target pools',
        '',
        '| Target | Catalog candidates | Scored atomic | Common N | Status |',
        '| --- | ---: | ---: | ---: | --- |',
    ]
    lines += [
        f'| {r["target"]} | {len(r["catalog_functions"])} | '
        f'{r["scored_atomic_count"]} | {r["common_n"]} | {r["status"]} |'
        for r in document.get('target_pools', [])
    ]
    return '\n'.join(lines) + '\n'
