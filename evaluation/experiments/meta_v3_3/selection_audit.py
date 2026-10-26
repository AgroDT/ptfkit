"""Target-focused workbook rescan and private observation ledger for model selection."""

# ruff: noqa: INP001, PLR2004, E501 - Pinned workbook coordinates and labels.

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import TYPE_CHECKING

import yaml
from openpyxl.utils import column_index_from_string
from ptfkit_eval import load_dataset_mapping, normalize_retention_workbook

from evaluation.experiments.meta_v3_3 import workbook_semantic as semantic
from evaluation.experiments.meta_v3_3.deep_unlock import scan_workbook


if TYPE_CHECKING:
    from pathlib import Path

    from openpyxl.workbook.workbook import Workbook


CONDUCTIVITY_LABELS = (
    'ksat',
    'k_sat',
    'hydraulic conductivity',
    'water permeability',
    'гидропровод',
    'фильтрац',
    'водопроницаем',
    'кф',
    'к ф',
)
SEMANTIC_WRC_BLOCKS = {
    'sapozhnikov_1987': 'gravimetric_water_content',
    'pestonova_2007': 'gravimetric_water_content',
    'manucharova_2012': 'gravimetric_water_content',
    'sidorova_2016': 'volumetric_water_content',
    'shein_2018': 'volumetric_water_content',
}


def additional_wrc(context: dict, book: Workbook) -> tuple[list[dict], list[dict]]:
    """Release explicit W/Q observations using audited wide identities, not label aliases."""
    mapping = yaml.safe_load((context['root'] / 'evaluation/datasets/meta_v3_3.yaml').read_bytes())
    accepted, decisions = [], []
    for rule in mapping['retention_reconstruction_rules']:
        if rule['id'] not in SEMANTIC_WRC_BLOCKS:
            continue
        basis = SEMANTIC_WRC_BLOCKS[rule['id']]
        dataset = {
            'dataset_id': 'selection-E5-' + rule['id'],
            'target': {
                'quantity': basis,
                'unit': 'mass_fraction' if basis.startswith('gravimetric') else 'volume_fraction',
                'denominator_basis': 'dry_soil_mass'
                if basis.startswith('gravimetric')
                else 'bulk_volume',
                'material_basis': 'unspecified',
            },
            'samples': [],
            'observations': [],
        }
        sheet = book[rule['master_worksheet']]
        for block in rule['blocks']:
            for number in range(block['first_sample_row'], block['last_sample_row'] + 1):
                sample_id, source = sheet[f'A{number}'].value, sheet[f'C{number}'].value
                dataset['samples'].append(
                    {'sample_id': sample_id, 'source_id': source, 'features': []}
                )
                for column in range(
                    column_index_from_string(block['first_column']),
                    column_index_from_string(block['last_column']) + 1,
                ):
                    water = sheet.cell(number, column)
                    axis = sheet.cell(block['axis_row'], column)
                    raw, pressure = water.value, axis.value
                    reason = None
                    if not semantic.numeric(raw) or raw <= 0:
                        reason = 'missing_or_declared_zero_placeholder'
                    elif (
                        not semantic.numeric(pressure)
                        or pressure < 0
                        or any(p['master_value'] == pressure for p in rule['pressure_replacements'])
                    ):
                        reason = 'ambiguous_saturation_or_pressure_marker'
                    elif basis == 'volumetric_water_content' and raw > 1:
                        reason = 'water_fraction_outside_physical_bounds'
                    decision = {
                        'water_cell': f'{sheet.title}!{water.coordinate}',
                        'pressure_cell': f'{sheet.title}!{axis.coordinate}',
                        'raw_water': raw,
                        'raw_pressure': pressure,
                        'sample_id': sample_id,
                        'source_id': source,
                        'rule': rule['id'],
                        'status': reason or 'accepted_E5_workbook_semantics',
                    }
                    decisions.append(decision)
                    if reason:
                        continue
                    p = pressure if rule['id'] == 'manucharova_2012' else 10**pressure * 0.0980665
                    observation = {
                        'id': dataset['dataset_id'] + ':' + water.coordinate,
                        'source_id': source,
                        'sample_id': sample_id,
                        'profile_id': None,
                        'horizon': sheet[f'I{number}'].value,
                        'pressure_kpa': p,
                        'observed': raw,
                        'basis': basis,
                        'source_cells': [decision['water_cell'], decision['pressure_cell']],
                        'origin': 'workbook_reported_E5_semantics',
                        'raw_pressure': pressure,
                        'raw_pressure_encoding': 'kPa'
                        if rule['id'] == 'manucharova_2012'
                        else 'pF',
                        'raw_water': raw,
                        'raw_water_encoding': 'wide_fraction; long_percent_crosswalk',
                        'dataset_id': dataset['dataset_id'],
                        'normalization_status': 'derived_units_from_original_observation',
                        'assumptions': [
                            'Use explicit workbook W/Q water basis and audited wide fraction/long percent equivalence.',
                            'Interpret the workbook pressure label as suction magnitude; experimental method remains unconfirmed.',
                        ],
                    }
                    accepted.append(observation)
                    dataset['observations'].append(
                        {
                            'id': observation['id'],
                            'source_id': source,
                            'sample_id': sample_id,
                            'suction_kpa': p,
                            'value': raw,
                            'source_cells': observation['source_cells'],
                            'origin': 'measured',
                            'review_status': 'E5_workbook_semantics',
                        }
                    )
        context['datasets'].append(dataset)
    return accepted, decisions


def thesis_wrc(context: dict, book: Workbook) -> tuple[list[dict], list[dict]]:
    """Read explicit pF/W% and metre-head/Q pairs; no unit guess for unlabelled axes."""
    sheet = book.worksheets[6]
    blocks = [
        (2, 3, 36, 43, 'pF', 'gravimetric_water_content', 0.01),
        (86, 87, 35, 47, 'pF', 'gravimetric_water_content', 1),
    ]
    blocks.extend(
        (r, r + 1, 36, sheet.max_column, 'meter_water_head', 'volumetric_water_content', 1)
        for r in range(4, 32, 2)
    )
    accepted, decisions = [], []
    by_basis = {}
    existing = {(s['source_id'], s['sample_id']) for d in context['datasets'] for s in d['samples']}
    for axis_row, number, first, last, pressure_unit, basis, factor in blocks:
        source, sample = sheet[f'C{number}'].value, sheet[f'A{number}'].value
        if not isinstance(source, str) or not isinstance(sample, str):
            continue
        if (source, sample) in existing:
            decisions.append({'row': number, 'status': 'duplicate_identity_already_in_ledger'})
            continue
        dataset = by_basis.setdefault(
            basis,
            {
                'dataset_id': 'selection-E5-thesis-' + basis,
                'target': {
                    'quantity': basis,
                    'unit': 'mass_fraction'
                    if basis.startswith('gravimetric')
                    else 'volume_fraction',
                    'denominator_basis': 'dry_soil_mass'
                    if basis.startswith('gravimetric')
                    else 'bulk_volume',
                    'material_basis': 'unspecified',
                },
                'samples': [],
                'observations': [],
            },
        )
        dataset['samples'].append({'sample_id': sample, 'source_id': source, 'features': []})
        heads = Counter(
            sheet.cell(axis_row, c).value
            for c in range(first, last + 1)
            if semantic.numeric(sheet.cell(axis_row, c).value)
            and semantic.numeric(sheet.cell(number, c).value)
        )
        for c in range(first, last + 1):
            axis, water = sheet.cell(axis_row, c), sheet.cell(number, c)
            if not semantic.numeric(water.value) or not semantic.numeric(axis.value):
                continue
            reason = (
                'repeated_head_without_independent_measurement_evidence'
                if heads[axis.value] > 1
                else 'invalid_water_or_head'
                if axis.value < 0
                or water.value * factor < 0
                or (basis == 'volumetric_water_content' and water.value * factor > 1)
                else None
            )
            record = {
                'pressure_cell': f'{sheet.title}!{axis.coordinate}',
                'water_cell': f'{sheet.title}!{water.coordinate}',
                'raw_pressure': axis.value,
                'raw_water': water.value,
                'source_id': source,
                'sample_id': sample,
                'status': reason or 'accepted_E5_explicit_axis_and_water_basis',
            }
            decisions.append(record)
            if reason:
                continue
            pressure = 10**axis.value * 0.0980665 if pressure_unit == 'pF' else axis.value * 9.80665
            observed = water.value * factor
            o = {
                'id': dataset['dataset_id'] + ':' + water.coordinate,
                'source_id': source,
                'sample_id': sample,
                'profile_id': sheet[f'K{number}'].value,
                'horizon': sheet[f'L{number}'].value,
                'pressure_kpa': pressure,
                'observed': observed,
                'basis': basis,
                'source_cells': [record['water_cell'], record['pressure_cell']],
                'origin': 'workbook_reported_measurement_origin_unconfirmed',
                'raw_pressure': axis.value,
                'raw_pressure_encoding': pressure_unit,
                'raw_water': water.value,
                'raw_water_encoding': 'W%'
                if factor == 0.01
                else 'Q_assumed_fraction'
                if basis.startswith('volumetric')
                else 'W_g_per_g',
                'dataset_id': dataset['dataset_id'],
                'predictor_workbook_row': f'{sheet.title}!{number}',
                'normalization_status': 'derived_units_from_original_workbook_pair',
                'assumptions': [
                    'Workbook-reported pair treated as an observation under E5; origin/laboratory method unconfirmed.',
                    'Q values interpreted as fractions in this explicitly metre-head block; no claim of source-validated scale.',
                ],
            }
            accepted.append(o)
            dataset['observations'].append(
                {
                    'id': o['id'],
                    'source_id': source,
                    'sample_id': sample,
                    'suction_kpa': pressure,
                    'value': observed,
                    'source_cells': o['source_cells'],
                    'origin': 'measured',
                    'review_status': 'E5_workbook_semantics',
                }
            )
    context['datasets'].extend(by_basis.values())
    return accepted, decisions


def inventory(points: list[dict]) -> dict:
    pressures = [p['pressure_kpa'] for p in points if p.get('pressure_kpa') is not None]
    return {
        'observations': len(points),
        'samples': len({(p['source_id'], p['sample_id']) for p in points}),
        'sources': len({p['source_id'] for p in points}),
        'profiles': len({(p['source_id'], p['profile_id']) for p in points if p.get('profile_id')}),
        'samples_without_profile': len(
            {(p['source_id'], p['sample_id']) for p in points if not p.get('profile_id')}
        ),
        'horizons': len(
            {(p['source_id'], p['sample_id'], p['horizon']) for p in points if p.get('horizon')}
        ),
        'pressure_range_kpa': [min(pressures), max(pressures)] if pressures else None,
        'basis_counts': dict(Counter(p.get('basis', 'ksat') for p in points)),
    }


def rescan(
    context: dict, workbook: Path, book: Workbook, formulas: Workbook
) -> tuple[dict, list[dict], list[dict]]:
    """Revisit all cells, including comments/hidden views, before any scoring."""
    scan = scan_workbook(workbook)
    normalized = normalize_retention_workbook(
        workbook, load_dataset_mapping(context['root'] / 'evaluation/datasets/meta_v3_3.yaml')
    )
    rows = semantic.workbook_rows(book, formulas)
    master = {(r['source_id'], r['sample_id']): r for r in rows if r['sheet_index'] == 0}
    observations = []
    for dataset in context['datasets']:
        samples = {(s['source_id'], s['sample_id']): s for s in dataset['samples']}
        for o in dataset['observations']:
            key = o['source_id'], o['sample_id']
            sample, row = samples[key], master.get(key)
            long_cells = [
                c for c in o['source_cells'] if c.startswith(book.worksheets[1].title + '!G')
            ]
            number = int(long_cells[0].rsplit('G', 1)[1]) if len(long_cells) == 1 else None
            observations.append(
                {
                    'id': dataset['dataset_id'] + ':' + o['id'],
                    'source_id': key[0],
                    'sample_id': key[1],
                    'profile_id': sample.get('profile_id'),
                    'horizon': row['values']['I'] if row else None,
                    'pressure_kpa': o['suction_kpa'],
                    'observed': o['value'],
                    'basis': dataset['target']['quantity'],
                    'source_cells': o['source_cells'],
                    'origin': o.get('origin'),
                    'raw_pressure': book.worksheets[1][f'F{number}'].value if number else None,
                    'raw_pressure_encoding': book.worksheets[1][f'E{number}'].value
                    if number
                    else None,
                    'raw_water': book.worksheets[1][f'G{number}'].value if number else None,
                    'raw_water_encoding': book.worksheets[1][f'D{number}'].value
                    if number
                    else None,
                    'dataset_id': dataset['dataset_id'],
                }
            )
    new_wrc, wrc_decisions = additional_wrc(context, book)
    observations.extend(new_wrc)
    extra, thesis_decisions = thesis_wrc(context, book)
    observations.extend(extra)
    # The new scan reveals five master Kf values repeated in the thesis block.
    # Differing horizon boundaries prohibit transferring predictors between these views.
    # Keep the existing thesis records once and retain the alternate addresses as candidates.
    additions = []
    sheet = book.worksheets[0]
    for number in range(333, 336):
        row = master[sheet[f'C{number}'].value, sheet[f'A{number}'].value]
        value = sheet[f'AB{number}'].value
        if semantic.numeric(value):
            item = semantic.proof(
                value * 0.01 / 86400,
                'permissive Ksat',
                (f'{sheet.title}!AB{number}',),
                original_value=value,
                original_unit_label=sheet['AB332'].value,
                canonical_unit='meter_per_second',
                conversion_factor=0.01 / 86400,
                interpretation_status='workbook_semantic_assumption',
                measurement_method='unknown_or_not_recorded',
                origin='not_recorded',
            )
            row['properties']['ksat'] = item
            additions.append(row)
    ksat: list[dict] = []
    for row in rows:
        if 'ksat' not in row['properties']:
            continue
        proof = row['properties']['ksat'].document()
        ksat.append(
            {
                'id': proof['sources'][0],
                'source_id': row['source_id'],
                'sample_id': row['sample_id'],
                'profile_id': None,
                'horizon': row['values']['I'],
                'observed': proof['value'],
                'source_cells': proof['sources'],
                'block': 'master_cm_day'
                if row in additions
                else 'thesis_m_day'
                if row['row'] <= 40
                else 'thesis_cm_min_assumed'
                if row['row'] <= 71
                else 'thesis_cm_day',
                'evidence': proof,
                'basis': 'ksat',
                'pressure_kpa': None,
                'origin': 'workbook_reported_method_and_measurement_origin_unconfirmed',
            }
        )
    labels = []
    for cell in scan['cells']:
        text = (str(cell['value']) + ' ' + str(cell.get('comment') or '')).casefold()
        if any(label in text for label in CONDUCTIVITY_LABELS):
            labels.append(cell)
    return (
        {
            'workbook_scan': scan,
            'sheets': scan['sheets'],
            'conductivity_label_hits': labels,
            'wrc': inventory(observations),
            'wrc_by_basis': {
                basis: inventory([o for o in observations if o['basis'] == basis])
                for basis in ('volumetric_water_content', 'gravimetric_water_content')
            },
            'ksat': inventory(ksat),
            'normalization': asdict(normalized.summary),
            'normalization_observations': [asdict(o) for o in normalized.observations],
            'normalization_exclusions': [asdict(o) for o in normalized.exclusions],
            'fitted_parameters_excluded': len(normalized.fitted_parameters),
            'additional_wrc_decisions': wrc_decisions,
            'thesis_wrc_decisions': thesis_decisions,
            'additional_wrc': inventory(new_wrc + extra),
            'ksat_block_counts': dict(Counter(p['block'] for p in ksat)),
            'ksat_original_units': dict(
                Counter(p['evidence']['details']['original_unit_label'] for p in ksat)
            ),
            'ksat_range_m_s': [min(p['observed'] for p in ksat), max(p['observed'] for p in ksat)],
            'additional_block_decisions': [
                {
                    'sheet_index': 0,
                    'header': 'AC49',
                    'cells': 'AC50:AC54',
                    'count': 5,
                    'status': 'possible_duplicate_of_thesis_m_day_excluded_from_pooled_N',
                    'reason': 'Identical five conductivity/density/carbon values; inconsistent depth boundaries. No independent replicate evidence.',
                },
                {
                    'sheet_index': 0,
                    'header': 'AB332',
                    'cells': 'AB333:AB335',
                    'count': 3,
                    'status': 'accepted_E5_workbook_reported_origin_unknown',
                },
                {
                    'sheet_index': 0,
                    'header': 'AB336',
                    'cells': 'AB337:AB342',
                    'count': 6,
                    'status': 'excluded_explicit_Rosetta_predictions',
                },
            ],
            'completeness': 'All used cells rescanned. All interpretable released WRC and explicit eligible conductivity blocks accounted for; unresolved WRC quantity/axis/origin rows remain exclusions, not proof of absent measurements.',
            'wide_views': 'Reviewed wide-to-long crosswalks in dataset mapping; repeated views are provenance, never independent N. Fitted Qs/Qr and porosity are not saturation observations.',
        },
        observations + ksat,
        rows,
    )
