"""Inventory evaluation-contract gaps without inferring scientific descriptors."""

# ruff: noqa: INP001, T201 - Standalone audit entry point with console summary.

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml


def audit(root: Path) -> dict:  # noqa: C901, PLR0915 - One reconciled inventory transaction.
    """Resolve specification references and reconcile against the generated manifest."""
    specs = (root / 'specs').resolve()
    documents = {}
    hashes = {}

    def read(path: Path) -> dict:
        path = path.resolve()
        if not path.is_relative_to(specs):
            message = 'Specification references must stay within specs.'
            raise ValueError(message)
        if path not in documents:
            raw = path.read_bytes()
            documents[path] = yaml.safe_load(raw)
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(raw).hexdigest()
        return documents[path]

    def resolve(value: dict, path: Path, trail: tuple = ()) -> dict:
        if '$ref' not in value:
            return value
        reference = value['$ref']
        identity = (path, reference)
        if identity in trail:
            message = 'Cyclic specification reference.'
            raise ValueError(message)
        filename, _, fragment = reference.partition('#')
        target_path = (path.parent / filename).resolve() if filename else path
        target = read(target_path)
        for part in fragment.lstrip('/').split('/') if fragment else []:
            target = target[part.replace('~1', '/').replace('~0', '~')]
        resolved = resolve(target, target_path, (*trail, identity))
        return {**resolved, **{key: item for key, item in value.items() if key != '$ref'}}

    manifest_path = root / 'targets/ptfkit-py/src/ptfkit/_manifest.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    emitted = {item['id'] for item in manifest['functions']}
    omitted = {item['id'] for item in manifest['coverage']['omitted_functions']}
    records = []
    statuses = Counter()
    for path in sorted((specs / 'functions').glob('*.yaml')):
        document = read(path)
        for function in document['functions']:
            statuses[function['status']] += 1
            if function['status'] != 'implemented':
                continue
            inputs = [resolve(item, path) for item in function['inputs']]
            outputs = resolve(function['outputs'], path)
            fields = outputs['fields'] if outputs['type'] == 'record' else [outputs]
            missing = [
                f'inputs.{item["name"]}.measurement'
                for item in inputs
                if 'unit' in item and item.get('measurement') is None
            ]
            missing.extend(
                f'outputs.{item["name"]}.measurement'
                for item in fields
                if item.get('measurement') is None
            )
            name = function['name']
            if (not missing) != (name in emitted) or (bool(missing) != (name in omitted)):
                message = f'Manifest and specification coverage disagree: {name}'
                raise ValueError(message)
            records.append(
                {
                    'id': name,
                    'source': path.stem,
                    'specification': path.relative_to(root).as_posix(),
                    'prediction_target': function.get('scope', {}).get('prediction_target'),
                    'models': function.get('scope', {}).get('models', {}),
                    'manifest_eligible': name in emitted,
                    'missing_measurement_paths': missing,
                    'inputs': [
                        {
                            'name': item['name'],
                            'unit': item.get('unit'),
                            'measurement': item.get('measurement'),
                            'reference': original.get('$ref'),
                        }
                        for original, item in zip(function['inputs'], inputs, strict=True)
                    ],
                    'outputs': [
                        {
                            'name': item['name'],
                            'quantity': item.get('quantity'),
                            'unit': item.get('unit'),
                            'measurement': item.get('measurement'),
                        }
                        for item in fields
                    ],
                }
            )
    records.sort(key=lambda item: item['id'])
    if {item['id'] for item in records} != emitted | omitted:
        message = 'Manifest does not account for exactly all implemented functions.'
        raise ValueError(message)
    quantities = Counter(
        quantity
        for item in records
        for quantity in {field['quantity'] for field in item['outputs']}
    )
    return {
        'schema_version': 1,
        'scope': 'metadata_readiness_not_dataset_eligibility_or_scientific_review',
        'source_specification_count': len(list((specs / 'functions').glob('*.yaml'))),
        'functions_by_status': dict(sorted(statuses.items())),
        'implemented_functions': len(records),
        'manifest_functions': len(emitted),
        'omitted_functions': len(omitted),
        'missing_numeric_input_descriptors': sum(
            path.startswith('inputs.')
            for item in records
            for path in item['missing_measurement_paths']
        ),
        'missing_output_descriptors': sum(
            path.startswith('outputs.')
            for item in records
            for path in item['missing_measurement_paths']
        ),
        'functions_by_output_quantity_overlapping': dict(sorted(quantities.items())),
        'manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
        'specification_sha256': dict(sorted(hashes.items())),
        'functions': records,
    }


def main() -> None:
    """Write a deterministic coverage inventory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.root.resolve())
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key
                not in {
                    'functions',
                    'specification_sha256',
                }
            },
            indent=2,
        )
    )


if __name__ == '__main__':
    main()
