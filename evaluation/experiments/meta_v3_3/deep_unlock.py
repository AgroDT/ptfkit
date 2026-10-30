"""Independent workbook discovery and catalog-wide, sample-specific unlock audit.

The cell inventory is private. The Markdown report contains counts, specification
semantics and candidate addresses, never measurements or sample identities.
"""

# ruff: noqa: INP001, SLF001, RUF001, E501, ISC004 - Workbook labels and Markdown tables.

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date, datetime, time
from pathlib import Path

from openpyxl import load_workbook
from ptfkit_eval.documents import canonical_json

from evaluation.experiments.meta_v3_3 import campaign
from evaluation.experiments.meta_v3_3 import campaign_contracts as contracts
from evaluation.experiments.meta_v3_3 import campaign_targets as targets
from evaluation.experiments.meta_v3_3 import exploratory as prior


ALIASES = {
    'bulk_density': ('bulk density', 'плотность почвы', 'плотность сложения'),
    'particle_density': ('particle density', 'плотность тв', 'плотность  тв', 'плотность тверд'),
    'porosity': ('porosity', 'пористость', 'порозность'),
    'organic_carbon': ('organic carbon', 'с орг', 'c орг'),
    'organic_matter': ('organic matter', 'органическое', 'органич', 'гумус'),
    'clay': ('clay', 'глина', 'ил (', '<0,002', '< 2'),
    'sand': ('sand', 'песок'),
    'silt': ('silt', 'пыль'),
    'depth': ('depth', 'глубина'),
    'ph': ('ph', 'рн'),
    'elevation': ('elevation', 'высота', 'высот'),
    'nitrogen': ('nitrogen', 'азот'),
    'electrical_conductivity': ('electrical', 'электропровод', 'засолен'),
    'stoniness': ('stoniness', 'gravel', 'щеб', 'каменист', 'скелет'),
    'saturated_hydraulic_conductivity': ('ksat', 'k_sat', 'гидропровод', 'фильтрац'),
    'infiltration_rate': ('infiltration', 'впитыван', 'инфильтрац'),
    'field_capacity': ('field capacity', 'полевая влаго', 'нв', 'наименьш'),
    'permanent_wilting_point': ('wilting', 'влажность завяд', 'вз'),
    'plasticity': ('plastic', 'пластич', 'текуч'),
    'moisture_equivalent': ('moisture equivalent', 'эквивалент'),
}
CANONICAL = {
    'soil_organic_carbon': 'organic_carbon',
    'carbon': 'organic_carbon',
    'soc': 'organic_carbon',
    'soil_organic_matter': 'organic_matter',
    'mean_depth': 'depth',
    'total_porosity': 'porosity',
    'clay_content': 'clay',
}
TARGET_CANDIDATES = {
    'saturated hydraulic conductivity': 'saturated_hydraulic_conductivity',
    'bulk density': 'bulk_density',
    'porosity': 'porosity',
    'plasticity properties': 'plasticity',
    'moisture equivalent': 'moisture_equivalent',
    'infiltration': 'infiltration_rate',
}
# These experimental properties cannot be reconstructed from water-retention
# measurements. Absence applies to this workbook, not to the source literature.
DIRECT_ONLY_FAMILIES = {
    'plasticity properties',
    'moisture equivalent',
    'infiltration',
    'unsaturated conductivity',
}
FAMILIES = (
    'water content at specified pressure/suction',
    'full water-retention curve',
    'retention-model parameters',
    'available water / available water capacity',
    'field capacity',
    'wilting point',
    'moisture equivalent',
    'saturated hydraulic conductivity',
    'unsaturated conductivity',
    'infiltration',
    'bulk density',
    'porosity',
    'plasticity properties',
    'other',
)


def cell_value(value: object) -> object:
    return (
        {'excel_type': type(value).__name__, 'iso8601': value.isoformat()}
        if isinstance(value, (date, datetime, time))
        else value
    )


def scan_workbook(path: Path) -> dict:
    """Visit every used cell in every view, without consulting the mapped schema."""
    formulas = load_workbook(path, data_only=False)
    cached = load_workbook(path, data_only=True)
    sheets, cells, candidates = [], [], []
    for sheet in formulas:
        count = 0
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None and cell.comment is None:
                    continue
                count += 1
                text = str(cell.value or '')
                comment = cell.comment.text if cell.comment else None
                record = {
                    'sheet': sheet.title,
                    'cell': cell.coordinate,
                    'value': cell_value(cell.value),
                    'cached': cell_value(cached[sheet.title][cell.coordinate].value),
                    'formula': cell.data_type == 'f',
                    'comment': comment,
                    'row_hidden': bool(sheet.row_dimensions[cell.row].hidden),
                    'column_hidden': bool(sheet.column_dimensions[cell.column_letter].hidden),
                }
                cells.append(record)
                if cell.data_type == 'f':
                    continue
                searchable = (text + ' ' + (comment or '')).casefold()
                for quantity, synonyms in ALIASES.items():
                    if any(word in searchable for word in synonyms):
                        below = [
                            {
                                'cell': sheet.cell(r, cell.column).coordinate,
                                'value': cell_value(sheet.cell(r, cell.column).value),
                            }
                            for r in range(cell.row + 1, sheet.max_row + 1)
                            if sheet.cell(r, cell.column).value is not None
                        ]
                        candidates.append(
                            {
                                'quantity': quantity,
                                'location': f'{sheet.title}!{cell.coordinate}',
                                'label': text,
                                'following_populated_cells': below,
                                'scientific_status': 'candidate_only; identity_units_protocol_origin_unconfirmed',
                            }
                        )
        sheets.append(
            {
                'sheet': sheet.title,
                'state': sheet.sheet_state,
                'dimensions': sheet.calculate_dimension(),
                'visited_cells': sheet.max_row * sheet.max_column,
                'nonempty_or_commented_cells': count,
                'merged_ranges': [str(r) for r in sheet.merged_cells.ranges],
                'hidden_rows': [r for r, d in sheet.row_dimensions.items() if d.hidden],
                'hidden_columns': [c for c, d in sheet.column_dimensions.items() if d.hidden],
                'formula_count': sum(c['formula'] for c in cells if c['sheet'] == sheet.title),
                'comment_count': sum(
                    c['comment'] is not None for c in cells if c['sheet'] == sheet.title
                ),
            }
        )
    formulas.close()
    cached.close()
    return {'sheets': sheets, 'cells': cells, 'candidates': candidates}


def families(function: dict) -> list[str]:  # noqa: C901, PLR0912 - Distinct source target families.
    result = set()
    model = function.get('scope', {}).get('models', {}).get('h_theta')
    if model and 'point' not in str(model).lower() and 'regression' not in str(model).lower():
        result.add('retention-model parameters')
    for field in function['fields']:
        quantity = field.get('quantity', '')
        description = field.get('description', '').lower()
        if quantity in contracts.WATER:
            if 'plastic' in description:
                result.add('plasticity properties')
            elif 'difference' in description or 'available' in description:
                result.add(FAMILIES[3])
            elif contracts.explicit_pressure(description) is not None or 'saturat' in description:
                result.add(FAMILIES[0])
            elif 'field capacity' in description:
                result.add('field capacity')
            elif 'wilting' in description:
                result.add('wilting point')
            elif 'equivalent' in description:
                result.add('moisture equivalent')
            elif 'porosity' in description:
                result.add('porosity')
            elif 'supplied' in description:
                result.add('full water-retention curve')
            else:
                result.add('retention-model parameters')
        elif quantity == 'available_water_capacity':
            result.add(FAMILIES[3])
        elif quantity == 'saturated_hydraulic_conductivity':
            result.add('saturated hydraulic conductivity')
        elif quantity == 'unsaturated_hydraulic_conductivity':
            result.add('unsaturated conductivity')
        elif quantity == 'dry_bulk_density':
            result.add('bulk density')
        elif 'plastic' in quantity:
            result.add('plasticity properties')
        elif 'infiltration' in quantity:
            result.add('infiltration')
    return sorted(result or {'other'})


def support_audit(context: dict, functions: list[dict]) -> list[dict]:
    """Retain pressure gaps for every sample; never infer a global exclusion."""
    result = []
    for function in functions:
        bindings = contracts.targets(function, context['support'])
        for target in bindings:
            for pressure in target.get('component_pressures_kpa', [target.get('pressure_kpa')]):
                if pressure is None:
                    continue
                samples = []
                for dataset in context['datasets']:
                    for sample in dataset['samples']:
                        series = targets.measured_series(dataset, sample)
                        if not series:
                            continue
                        low, high = min(p for p, _ in series), max(p for p, _ in series)
                        samples.append(
                            {
                                'source_id': sample['source_id'],
                                'sample_id': sample['sample_id'],
                                'min_kpa': low,
                                'max_kpa': high,
                                'inside_support': low <= pressure <= high,
                                'gap_kpa': max(low - pressure, pressure - high, 0),
                            }
                        )
                result.append(
                    {'function': function['id'], 'pressure_kpa': pressure, 'samples': samples}
                )
    return result


def predictor_audit(catalog: list[dict], scan: dict, baseline: dict) -> list[dict]:
    requirements = defaultdict(list)
    proofs = defaultdict(set)
    missing = defaultdict(set)
    sole = defaultdict(set)
    for function in catalog:
        for binding in function['inputs']:
            requirements[binding['name']].append(
                {
                    'function': function['id'],
                    'contract': binding,
                }
            )
    for row in baseline:
        for name in row.get('predictors', {}):
            proofs[name].add(row['function'])
        for reason in row.get('reasons', []):
            if reason.startswith('missing_predictor:'):
                name = reason.partition(':')[2]
                missing[name].add(row['function'])
                if len(row['reasons']) == 1:
                    sole[name].add(row['function'])
    result = []
    for name, required in sorted(requirements.items(), key=lambda p: (-len(p[1]), p[0])):
        canonical = CANONICAL.get(name, name)
        candidates = sorted(
            {c['location'] for c in scan['candidates'] if c['quantity'] == canonical}
        )
        result.append(
            {
                'predictor': name,
                'function_count': len(required),
                'requirements': required,
                'existing_evidence_function_count': len(proofs[name]),
                'missing_function_count': len(missing[name]),
                'sole_gap_function_count': len(sole[name]),
                'candidate_locations': candidates,
                'scientific_status': 'existing_sample_specific_evidence'
                if proofs[name]
                else 'candidate_requires_contract_review'
                if candidates
                else 'no_lexical_candidate; not_a_proof_of_absence',
            }
        )
    return result


def render(report: dict) -> str:
    lines = [
        '# ptfkit deep unlock audit',
        '',
        f'Catalog: {report["catalog_count"]}. Confirmed execution: **44 → {report["executable"]}**.',
        '',
        'Discovery used all workbook sheets and used cells independently of the mapped schema. '
        'Candidate labels never authorize a binding. The frozen baseline and strict benchmark remain unchanged. '
        'The maximum across unreviewed workbook evidence remains unresolved.',
        '',
        '## Decisions',
        '',
        '| Decision | Functions |',
        '| --- | ---: |',
    ]
    lines.extend(f'| {k} | {v} |' for k, v in sorted(report['decisions'].items()))
    lines += ['', '## Unlock attribution', '', '| Mechanism | New functions |', '| --- | ---: |']
    lines.extend(f'| {k} | {v} |' for k, v in report['attribution'].items())
    lines += [
        '',
        '## Original target_absent decomposition',
        '',
        'Families overlap for multi-output functions. Potential means a target route exists; '
        'predictors and physical contracts may still block execution. Definitely absent denotes '
        'experimental plasticity, moisture-equivalent, infiltration or unsaturated-conductivity '
        'targets with no corresponding populated measurement block in the full cell inventory '
        'and no deterministic derivation from WRC. It does not denote absence from the literature. '
        'All other unresolved definitions remain unresolved.',
        '',
        '| Target family | Functions | Potentially derivable from current data | Definitely absent |',
        '| --- | ---: | ---: | ---: |',
    ]
    lines.extend(
        f'| {r["family"]} | {r["functions"]} | {r["potential"]} | {r["definitely_absent"]} |'
        for r in report['target_families']
    )
    lines += [
        '',
        '## Workbook second pass',
        '',
        '| Sheet | Used cells visited | Populated/commented | Formulas | Comments | Hidden rows/columns |',
        '| --- | ---: | ---: | ---: | ---: | --- |',
    ]
    for r in report['workbook_sheets']:
        lines.append(
            f'| {r["sheet"]} | {r["visited_cells"]} | {r["nonempty_or_commented_cells"]} | '
            f'{r["formula_count"]} | {r["comment_count"]} | {len(r["hidden_rows"])}/{len(r["hidden_columns"])} |'
        )
    lines += [
        '',
        'Every cell, cached formula value, comment, merged range, visibility flag and '
        'candidate column block is retained in the private scan artifact. Numeric points, '
        'sample labels and publication links are not reinterpreted as measurements. '
        'Repeated blocks and units embedded below headers remain separate candidates.',
        '',
        'The dissertation view contains filled Ksat blocks and particle-density columns. '
        'Ksat units change by block (including m/day, an ambiguous cm/min label, and cm/day). '
        'Particle density, aggregate properties and porosity need identity, unit, '
        'measurement-origin and material review. These candidates invalidate a blanket '
        'claim that conductivity or particle density is absent, but release no new targets.',
        '',
        '## Reverse predictor search',
        '',
        'Names are retained exactly; the private inventory also stores every distinct source '
        'contract, so identical names do not imply identical particle-size bounds or protocols.',
        '',
        '| Predictor | Functions requiring it | Inventoried evidence? | Candidate workbook locations | Scientific status |',
        '| --- | ---: | --- | --- | --- |',
    ]
    for r in report['predictors']:
        lines.append(
            f'| `{r["predictor"]}` | {r["function_count"]} | '
            f'{r["existing_evidence_function_count"]} functions | '
            f'{", ".join(r["candidate_locations"]) or "none found"} | {r["scientific_status"]} |'
        )
    lines += [
        '',
        'Predictor impact in the frozen baseline (overlapping function sets):',
        '',
        '| Predictor | Functions with a missing-input decision | Functions with a sole-input gap on some sample |',
        '| --- | ---: | ---: |',
    ]
    lines.extend(
        f'| `{r["predictor"]}` | {r["missing_function_count"]} | {r["sole_gap_function_count"]} |'
        for r in sorted(
            report['predictors'],
            key=lambda r: (-r['sole_gap_function_count'], -r['missing_function_count']),
        )
        if r['missing_function_count']
    )
    lines += [
        '',
        '## Deterministic predictor routes',
        '',
        '| Transformation | Disposition |',
        '| --- | --- |',
        '| Depth interval → midpoint | Existing approximate policy; source depth definition still required |',
        '| OC ↔ OM | Existing exploratory factor; empirical relation, not a physical identity |',
        '| Bulk + particle density → porosity | Generic identity 1 − rho_b/rho_s; candidate particle-density binding unconfirmed |',
        '| PSD → USDA class | Existing policy; preserve particle bounds, closure and inherited evidence |',
        '| Complementary PSD fraction | Require common material basis and valid measured closure; never fill incompatible cutoffs |',
        '| WRC → pressure-defined water predictor | General unit mapping; same sample, in-range only, conditional validation |',
        '',
        '## Original eight pressure blockers',
        '',
        'Each row aggregates the private per-sample support and gap audit. An in-range target '
        'does not remove missing predictors. No sample is required to represent the entire source.',
        '',
        '| Function | Requested kPa | Observed min–max kPa | In-range samples | Minimum outside gap kPa |',
        '| --- | ---: | --- | ---: | ---: |',
    ]
    for r in report['pressure_blockers']:
        samples = r['samples']
        outside = [s['gap_kpa'] for s in samples if not s['inside_support']]
        lines.append(
            f'| `{r["function"]}` | {r["pressure_kpa"]:g} | '
            f'{min(s["min_kpa"] for s in samples):g}–{max(s["max_kpa"] for s in samples):g} | '
            f'{sum(s["inside_support"] for s in samples)} | {min(outside, default=0):g} |'
        )
    lines += [
        '',
        '## Public wrappers with another specification status',
        '',
        'All 44 wrappers remain in the denominator and are evaluated without a status exclusion. '
        'Their source specifications contain implementation variables and verification cases; '
        'the public wrappers dispatch to native ufuncs. They are callable PTFs. '
        'A compound output is identified separately from a convenience wrapper. '
        'Ready-for-implementation status is preserved and is not promoted to validated semantics.',
        '',
        '| Wrapper assessment | Functions |',
        '| --- | ---: |',
        f'| Callable PTF with status other than implemented | {sum(f["specification_status"] != "implemented" and f["wrapper_kind"] == "genuine_callable_ptf" for f in report["functions"])} |',
        f'| Benchmarkable on at least one sample | {sum(f["specification_status"] != "implemented" and f["samples"] > 0 for f in report["functions"])} |',
        f'| Compound target | {sum(f["specification_status"] != "implemented" and f["composite_target"] for f in report["functions"])} |',
        f'| Incomplete implementation contract | {sum(f["specification_status"] != "implemented" and f["wrapper_kind"] == "implementation_contract_incomplete" for f in report["functions"])} |',
        '',
        '## All function decisions',
        '',
        'Output descriptions are copied from registered specifications. Multiple families '
        'and unresolved semantics are retained; a callable wrapper is not scientific validation.',
        '',
        '| Function | Specification status / wrapper | Output semantics | Decision | Samples after mapping |',
        '| --- | --- | --- | --- | ---: |',
    ]
    for r in report['functions']:
        semantics = '; '.join(f'{f["name"]}: {f.get("description", "")}' for f in r['outputs'])
        lines.append(
            f'| `{r["function"]}` | {r["specification_status"]} / {r["wrapper_kind"]} | '
            f'{semantics.replace("|", "/")} | {r["decision"]} | {r["samples"]} |'
        )
    lines += [
        '',
        '## Reproduction and limits',
        '',
        'Use `python -m evaluation.experiments.meta_v3_3.deep_unlock --help` in the locked '
        'evaluation environment. Run discovery before the isolated campaign; use '
        '`--comparison` to attach the completed campaign. Full private outputs retain '
        'cell evidence, per-sample support, contracts, function decisions and SHA-256 inventory. '
        'No new workbook property is automatically bound. No operational FC/PWP, moisture '
        'equivalent, uncertain material basis, or unspecified model variant is inferred.',
        '',
    ]
    return '\n'.join(lines)


def aggregate_report(report: dict) -> dict:
    """Project private support diagnostics to publishable counts and contract metadata."""
    pressure = []
    for row in report['pressure_blockers']:
        samples = row['samples']
        pressure.append(
            {
                'function': row['function'],
                'pressure_kpa': row['pressure_kpa'],
                'assessed_samples': len(samples),
                'in_range_samples': sum(s['inside_support'] for s in samples),
                'observed_min_kpa': min(s['min_kpa'] for s in samples),
                'observed_max_kpa': max(s['max_kpa'] for s in samples),
                'minimum_outside_gap_kpa': min(
                    (s['gap_kpa'] for s in samples if not s['inside_support']), default=0
                ),
            }
        )
    return {
        **{
            key: value
            for key, value in report.items()
            if key not in ('pressure_blockers', 'predictors')
        },
        'pressure_blockers': pressure,
        'predictors': [
            {key: value for key, value in row.items() if key != 'requirements'}
            for row in report['predictors']
        ],
        'scope': 'aggregate_counts_and_source_contracts; no_private_measurements_or_sample_identities',
        'workbook_coverage_ceiling': 'unresolved_until_candidate_contracts_are_reviewed',
    }


def run(args: argparse.Namespace) -> dict:  # noqa: C901, PLR0912, PLR0915 - One audit transaction.
    output = args.output.resolve()
    inputs = [args.baseline, args.benchmark, args.harmonized]
    if any(output.is_relative_to(p.resolve()) for p in inputs):
        message = 'Audit output must be separate from all pinned inputs.'
        raise ValueError(message)
    baseline = json.loads((args.baseline / 'summary.json').read_bytes())
    baseline_hashes = prior.verify_artifacts(args.baseline)
    context = campaign.prepare(args.benchmark, args.harmonized, args.workbook)
    scan = scan_workbook(args.workbook)
    old_records = json.loads((args.baseline / 'matrix.json').read_bytes())
    predictors = predictor_audit(context['catalog'], scan, old_records)
    old = {r['function']: r for r in baseline['final_blockers']['functions']}
    before = {r['function'] for r in baseline['functions'] if r['scored']} | context['strict_ids']
    # Baseline records preserve the exact historical mappings, independent of current code.
    frozen_bindings = {r['function']: r['target_bindings'] for r in baseline['function_audit']}
    records, points = [], []
    stage = context['registration']['stages'][-1]
    for scenario in context['registration']['psd_scenarios']:
        r, p = campaign.evaluate(
            context, stage, scenario, context['registration']['primary_target_route']
        )
        records.extend(r)
        points.extend(p)
    after = {p['function'] for p in points} | context['strict_ids']
    if not before <= after:
        message = 'Proposed mappings lost baseline executable functions.'
        raise ValueError(message)
    sample_sets = defaultdict(set)
    for p in points:
        sample_sets[p['function']].add((p['source_id'], p['sample_id']))
    functions: list[dict] = []
    for function in context['catalog']:
        fid = function['id']
        binding = contracts.targets(function, context['support'])
        required = [p for p in predictors if any(r['function'] == fid for r in p['requirements'])]
        output_families = families(function)
        target_candidates = sorted(
            {
                c['location']
                for c in scan['candidates']
                if c['quantity'] in {TARGET_CANDIDATES.get(family) for family in output_families}
            }
        )
        if fid in before:
            decision = 'current_executable'
        elif fid in after:
            decision = 'unlockable_after_generic_semantic_mapping'
        elif set(output_families) <= DIRECT_ONLY_FAMILIES and not binding:
            decision = 'genuinely_target_absent_in_audited_workbook'
        elif target_candidates or any(
            p['candidate_locations'] and not p['existing_evidence_function_count'] for p in required
        ):
            decision = 'candidate_requiring_workbook_evidence'
        elif old[fid]['next_blocker'] == 'unacceptable_physical_semantics':
            decision = 'physically_incompatible_or_unresolved'
        elif binding:
            decision = 'predictor_or_support_unresolved'
        else:
            decision = 'target_contract_or_workbook_evidence_unresolved'
        functions.append(
            {
                'function': fid,
                'specification': function['specification'],
                'specification_status': function['status'],
                'wrapper_kind': 'genuine_callable_ptf'
                if function.get('implementation', {}).get('variables')
                else 'implementation_contract_incomplete',
                'scientific_review': 'implemented_specification'
                if function['status'] == 'implemented'
                else 'source_status_not_implemented; not_validated_by_callability',
                'verification_case_count': len(function.get('verification_cases', [])),
                'composite_target': any(t['kind'] == 'pressure_difference' for t in binding),
                'candidate_target_locations': target_candidates,
                'outputs': function['fields'],
                'families': output_families,
                'baseline_blocker': old[fid]['next_blocker'],
                'baseline_bindings': frozen_bindings[fid],
                'proposed_bindings': binding,
                'decision': decision,
                'samples': len(sample_sets[fid]),
                'remaining_reasons': sorted(
                    {reason for r in records if r['function'] == fid for reason in r['reasons']}
                ),
            }
        )
    target_families = []
    for family in FAMILIES:
        selected = [
            f
            for f in functions
            if f['baseline_blocker'] == 'target_absent' and family in f['families']
        ]
        target_families.append(
            {
                'family': family,
                'functions': len(selected),
                'potential': sum(bool(f['proposed_bindings']) for f in selected),
                'definitely_absent': sum(
                    f['decision'] == 'genuinely_target_absent_in_audited_workbook' for f in selected
                ),
            }
        )
    pressure = support_audit(
        context,
        [
            f
            for f in context['catalog']
            if old[f['id']]['next_blocker'] == 'target_pressure_unavailable_no_extrapolation'
        ],
    )
    attribution = Counter()
    mechanisms = {}
    point_policies = defaultdict(set)
    for point in points:
        point_policies[point['function']].update(
            proof['policy'] for proof in point['predictor_evidence'].values()
        )
    for f in functions:
        if f['function'] in after - before:
            mechanism = (
                'compound target derivation'
                if any(t['kind'] == 'pressure_difference' for t in f['proposed_bindings'])
                else 'other'
                if 'retention_predictor_terminology_v2' in point_policies[f['function']]
                or any(
                    t['adapter'] == 'explicit_vg_mualem_signature_v1'
                    for t in f['proposed_bindings']
                )
                else 'generalized pressure mapping'
            )
            attribution[mechanism] += 1
            mechanisms[f['function']] = {
                'mechanism': mechanism,
                'adapters': sorted({t['adapter'] for t in f['proposed_bindings']}),
                'predictor_policies': sorted(point_policies[f['function']]),
            }
    for mechanism in (
        'generalized pressure mapping',
        'newly inventoried workbook target',
        'newly inventoried predictor',
        'compound target derivation',
        'partial-sample eligibility',
        'other',
    ):
        attribution.setdefault(mechanism, 0)
    report = {
        'protocol': 'deep_unlock_audit_v1',
        'catalog_count': len(functions),
        'baseline_executable': len(before),
        'executable': len(after),
        'new_functions': sorted(after - before),
        'decisions': dict(Counter(f['decision'] for f in functions)),
        'attribution': dict(attribution),
        'unlock_mechanisms': mechanisms,
        'functions': functions,
        'target_families': target_families,
        'predictors': predictors,
        'workbook_sheets': scan['sheets'],
        'pressure_blockers': pressure,
        'strict_executable': len(context['strict_ids']),
        'discovery_status': 'confirmed_generic_routes; workbook_candidates_not_bound',
        'existing_policy_unlocks_without_mapping_changes': 0,
        'strict_benchmark_changed': False,
        'input_sha256': {
            'baseline': prior._hash(args.baseline / 'summary.json'),
            'workbook': prior._hash(args.workbook),
        },
        'implementation_sha256': {
            p.name: prior._hash(p) for p in sorted(Path(__file__).parent.glob('*.py'))
        },
        'specification_sha256': {
            p.relative_to(context['root']).as_posix(): prior._hash(p)
            for p in sorted((context['root'] / 'specs').rglob('*.yaml'))
        },
    }
    if args.comparison:
        compared = json.loads((args.comparison / 'summary.json').read_bytes())
        if {r['function'] for r in compared['functions'] if r['scored']} | context[
            'strict_ids'
        ] != after:
            message = 'Completed campaign and audit execution disagree.'
            raise ValueError(message)
        report['completed_campaign_sha256'] = prior._hash(args.comparison / 'summary.json')
        report['completed_campaign'] = {
            'catalog_count': compared['catalog_count'],
            'all_function_coverage': compared['all_function_coverage'],
            'strict_coverage': compared['strict_coverage'],
            'assumption_ladder': compared['assumption_ladder'],
            'blocker_counts': compared['final_blockers']['counts']
            if 'counts' in compared['final_blockers']
            else {
                key: sum(f['next_blocker'] == key for f in compared['final_blockers']['functions'])
                for key in sorted(
                    {
                        f['next_blocker']
                        for f in compared['final_blockers']['functions']
                        if f['next_blocker'] is not None
                    }
                )
            },
            'main_artifacts_unchanged': compared['main_artifacts_unchanged'],
        }
    output.mkdir(parents=True, exist_ok=False)
    for name, value in [
        ('workbook-scan', scan),
        ('report', report),
        ('matrix', records),
        ('predictions', points),
    ]:
        (output / (name + '.json')).write_bytes(canonical_json(value))
    (output / 'aggregate-summary.json').write_bytes(canonical_json(aggregate_report(report)))
    (output / 'report.md').write_text(render(report), encoding='utf-8')
    if baseline_hashes != prior.verify_artifacts(args.baseline):
        message = 'Baseline artifacts changed during discovery.'
        raise ValueError(message)
    (output / 'artifact-hashes.json').write_bytes(
        canonical_json({p.name: prior._hash(p) for p in sorted(output.iterdir())})
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('baseline', 'benchmark', 'harmonized', 'workbook', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--comparison', type=Path)
    args = parser.parse_args()
    report = run(args)
    print(  # noqa: T201 - Command-line audit result.
        json.dumps(
            {k: report[k] for k in ('catalog_count', 'executable', 'decisions', 'new_functions')},
            indent=2,
        )
    )


if __name__ == '__main__':
    main()
