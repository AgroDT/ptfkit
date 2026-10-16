# ruff: noqa: ANN401, EM101, EM102, INP001, PLC0415, T201, TRY003
"""Export a fitted scikit-learn RandomForestRegressor to ptfkit JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any


IDENTIFIER = re.compile(r'^[a-z][a-z0-9_]*$')
SHA256_HEX_LENGTH = 64


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--name', required=True)
    parser.add_argument('--features', required=True, nargs='+')
    parser.add_argument('--expected-sha256', required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def validate_cli(args: argparse.Namespace) -> str:
    if not args.model.is_file():
        raise ValueError(f'model is not a readable file: {args.model}')
    if not IDENTIFIER.fullmatch(args.name):
        raise ValueError('name must match ^[a-z][a-z0-9_]*$')
    if not args.features or len(set(args.features)) != len(args.features):
        raise ValueError('features must be non-empty and unique')
    for feature in args.features:
        if not IDENTIFIER.fullmatch(feature):
            raise ValueError(f'feature must be lower snake case: {feature}')
    expected = args.expected_sha256.lower()
    if len(expected) != SHA256_HEX_LENGTH or any(
        character not in '0123456789abcdef' for character in expected
    ):
        raise ValueError('expected SHA-256 must contain 64 hexadecimal digits')
    actual = sha256(args.model)
    if actual != expected:
        raise ValueError(f'model SHA-256 mismatch: expected {expected}, found {actual}')
    return actual


def export_estimator(
    estimator: Any, args: argparse.Namespace, source_sha256: str
) -> dict[str, Any]:
    estimator_type = type(estimator)
    if (
        estimator_type.__name__ != 'RandomForestRegressor'
        or not estimator_type.__module__.startswith('sklearn.ensemble')
    ):
        raise TypeError('model must be a fitted sklearn RandomForestRegressor')
    if int(estimator.n_features_in_) != len(args.features):
        message = (
            f'model expects {estimator.n_features_in_} features, '
            f'received {len(args.features)} names'
        )
        raise ValueError(message)
    if int(estimator.n_outputs_) != 1:
        raise ValueError('only single-output regressors are supported')
    if not estimator.estimators_:
        raise ValueError('random forest must contain at least one fitted tree')

    trees = []
    for index, fitted_tree in enumerate(estimator.estimators_):
        tree = fitted_tree.tree_
        if int(tree.n_outputs) != 1 or tuple(tree.value.shape[1:]) != (1, 1):
            raise ValueError(f'tree {index} is not a single-output regression tree')
        missing = getattr(tree, 'missing_go_to_left', None)
        if missing is not None and bool(missing.any()):
            raise ValueError(f'tree {index} contains learned missing-value routing')
        trees.append(
            {
                'children_left': [int(value) for value in tree.children_left],
                'children_right': [int(value) for value in tree.children_right],
                'features': [int(value) for value in tree.feature],
                'thresholds': [float(value) for value in tree.threshold],
                'values': [float(value) for value in tree.value[:, 0, 0]],
            }
        )
    return {
        'format_version': 1,
        'name': args.name,
        'source_sha256': source_sha256,
        'features': args.features,
        'aggregation': 'mean',
        'trees': trees,
    }


def compact_json(payload: dict[str, Any]) -> str:
    def quoted(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, allow_nan=False)

    lines = [
        '{',
        f'  "format_version": {payload["format_version"]},',
        f'  "name": {quoted(payload["name"])},',
        f'  "source_sha256": {quoted(payload["source_sha256"])},',
        f'  "features": {quoted(payload["features"])},',
        f'  "aggregation": {quoted(payload["aggregation"])},',
        '  "trees": [',
    ]
    trees = payload['trees']
    for index, tree in enumerate(trees):
        lines.extend(
            [
                '    {',
                f'      "children_left": {quoted(tree["children_left"])},',
                f'      "children_right": {quoted(tree["children_right"])},',
                f'      "features": {quoted(tree["features"])},',
                f'      "thresholds": {quoted(tree["thresholds"])},',
                f'      "values": {quoted(tree["values"])}',
                '    }' + (',' if index + 1 < len(trees) else ''),
            ]
        )
    lines.extend(['  ]', '}'])
    return '\n'.join(lines) + '\n'


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent, text=True)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as output:
            output.write(text)
        Path(temporary).replace(path)
    except BaseException:
        with suppress(FileNotFoundError):
            Path(temporary).unlink()
        raise


def main() -> None:
    args = parse_args()
    source_sha256 = validate_cli(args)
    import joblib

    estimator = joblib.load(args.model)
    payload = export_estimator(estimator, args, source_sha256)
    atomic_write(args.output, compact_json(payload))
    print(
        f'exported {len(payload["trees"])} trees and '
        f'{sum(len(tree["features"]) for tree in payload["trees"])} nodes to {args.output}'
    )


if __name__ == '__main__':
    main()
