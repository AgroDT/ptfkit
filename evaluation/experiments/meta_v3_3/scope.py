"""Expose populated workbook rows beyond the reviewed long-form retention export."""

# ruff: noqa: INP001 - Standalone experiment helpers.

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from openpyxl.workbook.workbook import Workbook


_MASTER_SOURCE_COLUMN = 3
_MASTER_METHOD_COLUMN = 4
_MASTER_ENCODING_COLUMN = 23


def workbook_scope(  # noqa: C901 - Coordinate-level accounting across declared sheet roles.
    book: Workbook, mapping: dict, dispositions: list[dict], keys: set[str]
) -> dict:
    """Inventory exact row coordinates without inferring samples from numeric markers."""
    master = next(s['name'] for s in mapping['worksheets'] if s['id'] == 'samples_master')
    long_sheet = dispositions[0]['sheet_name']
    long_status = {r['row']: r['status'] for r in dispositions}
    controls = {
        (rule['master_worksheet'], block['axis_row'])
        for rule in mapping['retention_reconstruction_rules']
        for block in rule['blocks']
    }
    headers = {
        (sheet['name'], row)
        for sheet in mapping['worksheets']
        for block in sheet['header_rows']
        for row in block
    }
    rows = []
    groups = defaultdict(list)
    for sheet in book.worksheets:
        for number, cells in enumerate(sheet.iter_rows(), 1):
            populated = [cell.column_letter for cell in cells if cell.value is not None]
            if not populated:
                continue
            key = f'{sheet.title}!{number}'
            status = 'unresolved_row_role_and_measurement_contract'
            if (sheet.title, number) in headers:
                status = 'declared_header'
            if (sheet.title, number) in controls:
                status = 'declared_retention_axis_not_sample'
            if key in keys:
                status = 'audited_retention_master_row'
            if sheet.title == long_sheet and number in long_status:
                status = long_status[number]
            raw_source = None
            if sheet.title == master and len(cells) >= _MASTER_SOURCE_COLUMN:
                raw_source = cells[_MASTER_SOURCE_COLUMN - 1].value
            row = {
                'sheet': sheet.title,
                'row': number,
                'key': key,
                'status': status,
                'populated_columns': populated,
                'raw_master_source': raw_source,
            }
            if sheet.title == master:
                row['reported_method'] = (
                    cells[_MASTER_METHOD_COLUMN - 1].value
                    if len(cells) >= _MASTER_METHOD_COLUMN
                    else None
                )
                row['reported_encoding'] = (
                    cells[_MASTER_ENCODING_COLUMN - 1].value
                    if len(cells) >= _MASTER_ENCODING_COLUMN
                    else None
                )
                row['tail_populated_cell_count'] = sum(
                    c.value is not None for c in cells[_MASTER_ENCODING_COLUMN:]
                )
            rows.append(row)
            if raw_source is not None and status == 'unresolved_row_role_and_measurement_contract':
                groups[str(raw_source)].append(row)
    return {
        'schema_version': 1,
        'policy': 'populated_row_coordinates_no_sample_or_quantity_inference_v1',
        'sheet_count': len(book.worksheets),
        'populated_row_count': len(rows),
        'status_counts': dict(sorted(Counter(r['status'] for r in rows).items())),
        'rows': rows,
        'unreviewed_master_sources': [
            {
                'raw_source': source,
                'row_count': len(records),
                'rows': [r['row'] for r in records],
                'status': 'source_schema_and_row_roles_unresolved',
                'sample_count': None,
                'profile_count': None,
                'reported_methods': sorted(
                    {str(r['reported_method']) for r in records if r['reported_method'] is not None}
                ),
                'reported_encodings': sorted(
                    {
                        str(r['reported_encoding'])
                        for r in records
                        if r['reported_encoding'] is not None
                    }
                ),
                'tail_populated_cell_count': sum(r['tail_populated_cell_count'] for r in records),
            }
            for source, records in sorted(groups.items())
        ],
    }
