"""Command-line access to inspection, normalization, plans, runs, and reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .artifacts import artifact_value, read_retention_run_report, write_retention_run
from .contracts import load_evaluation_plan
from .datasets import load_dataset_mapping
from .documents import canonical_json, load_document
from .normalization import normalize_retention_workbook
from .run_plans import load_retention_run_plan
from .runner import execute_retention_run
from .workbooks import inspect_workbook


if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Execute an explicit local command and return its process exit status."""
    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        _execute(arguments)
    except (ValueError, OSError) as error:
        parser.exit(2, f'ptfkit-eval: {error}\n')
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='ptfkit-eval')
    subcommands = parser.add_subparsers(dest='command', required=True)
    for command, help_text in (
        ('inspect', 'Inventory a workbook without copying measurement rows.'),
        ('normalize', 'Normalize under reviewed mapping rules and emit a count-only summary.'),
        ('plan', 'Validate an evaluation plan or checksum-bound retention run plan.'),
        ('run', 'Execute a checksum-bound canonical retention run.'),
        ('report', 'Verify a run directory and display its persisted report.'),
    ):
        command_parser = subcommands.add_parser(command, help=help_text)
        command_parser.add_argument('source', type=Path)
        if command != 'report':
            command_parser.add_argument('--output', type=Path, required=command == 'run')
        if command == 'normalize':
            command_parser.add_argument('--mapping', type=Path, required=True)
    return parser


def _execute(arguments: argparse.Namespace) -> None:
    if arguments.command == 'report':
        sys.stdout.write(read_retention_run_report(arguments.source))
    elif arguments.command == 'run':
        plan = load_retention_run_plan(arguments.source)
        result = execute_retention_run(plan)
        destination = write_retention_run(result, arguments.output)
        sys.stdout.write(f'{destination}\n')
    elif arguments.command == 'plan':
        document = load_document(arguments.source)
        if 'evaluation_plan' in document:
            plan = load_retention_run_plan(arguments.source)
            _emit(
                {'status': 'valid', 'kind': 'retention_run', 'input_hashes': plan.input_hashes},
                arguments.output,
            )
        else:
            evaluation = load_evaluation_plan(document)
            _emit(
                {
                    'status': 'valid',
                    'kind': 'evaluation_plan',
                    'candidates': [candidate.id for candidate in evaluation.candidates],
                },
                arguments.output,
            )
    elif arguments.command == 'normalize':
        result = normalize_retention_workbook(
            arguments.source, load_dataset_mapping(arguments.mapping)
        )
        _emit(artifact_value(result.summary), arguments.output)
    else:
        _emit(artifact_value(inspect_workbook(arguments.source)), arguments.output)


def _emit(value: object, output: Path | None) -> None:
    contents = canonical_json(value)
    if output is None:
        sys.stdout.write(contents.decode('utf-8'))
    else:
        with output.open('xb') as stream:
            stream.write(contents)
