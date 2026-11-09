"""Inventory source-reported binding evidence without granting native eligibility."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import openpyxl


ARCHIVE_SHA256 = 'e9164c2f74e9ad75033b99248b0eee7ba426230150a499a6e6b3a285eebcf618'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = args.archive.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256:
        message = 'The reviewed HYBRAS archive checksum does not match.'
        raise ValueError(message)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        name = next(n for n in archive.namelist() if n.endswith('HYBRAS_COMPLETE_V1.xlsx'))
        workbook = openpyxl.load_workbook(
            io.BytesIO(archive.read(name)), read_only=True, data_only=True
        )
    rows = list(workbook['HYBRAS'].iter_rows(values_only=True))[3:]
    workbook.close()
    columns = {
        'horizon': 7,
        'texture': 11,
        'texture_method': 134,
        'particle_size_fractions': 135,
        'carbon_organic_matter_method': 136,
        'bulk_density_method': 137,
    }
    # A strict lexical shortlist is not a reviewed material-basis assignment.
    shortlist = [
        row
        for row in rows
        if isinstance(row[7], str) and re.fullmatch(r'[ABE][a-z]*[0-9]*', row[7])
    ]
    report = {
        'schema_version': 1,
        'scope': 'binding_evidence_inventory_not_dataset_eligibility',
        'archive_sha256': ARCHIVE_SHA256,
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'samples': len(rows),
        'source_columns_zero_based': columns,
        'reported_values': {
            key: dict(sorted(Counter('' if r[i] is None else str(r[i]) for r in rows).items()))
            for key, i in columns.items()
        },
        'strict_single_master_horizon_shortlist': {
            'pattern': '[ABE][a-z]*[0-9]*',
            'samples': len(shortlist),
            'profiles': len({r[5] for r in shortlist}),
            'scope': 'full_archive_before_positive_pressure_cohort_join',
            'eligibility': 'not_granted',
        },
        'primary_horizon_reference': 'https://www.nrcs.usda.gov/sites/default/files/2022-09/SSM-ch3.pdf',
        'review_findings': [
            'NRCS identifies A, E and B master horizons as mineral horizons.',
            'Missing, transitional, compound and annotated horizon labels need separate review.',
            'A mineral horizon does not establish a fine-earth target preparation.',
            (
                'All bulk-density method cells say volumetric ring; temperature, duration and core '
                'volume required by the current Vereecken contract are not specified there.'
            ),
            (
                'Reported texture categories require a reviewed USDA class crosswalk before Clapp '
                'execution; this inventory does not derive categories from numeric fractions.'
            ),
            (
                'Carbon methods differ: modified, spectrophotometric and unspecified methods must '
                'not be silently equated to the required Walkley-Black method.'
            ),
        ],
    }
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=True, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
