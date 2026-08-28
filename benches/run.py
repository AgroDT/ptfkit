#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# ///

from __future__ import annotations

import argparse
import json
import shlex
import statistics
import subprocess
import sys
import tarfile
from collections import defaultdict
from pathlib import Path


TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterable

    type BenchmarkRecord = dict[str, int | str]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run cross-target ptfkit benchmarks.')
    parser.add_argument('--warmups', type=int, default=3)
    parser.add_argument('--iterations', type=int, default=10)
    parser.add_argument('--limit', type=int)
    return parser.parse_args()


def extract_dataset(root: Path) -> Path:
    fixtures_dir = root / 'fixtures'
    archive = fixtures_dir / 'soilgrids.tar.zst'
    target_dir = fixtures_dir / 'soilgrids'

    if not target_dir.joinpath('manifest.json').is_file():
        print('Extracting', archive)
        with tarfile.open(archive, 'r:zst') as tar:
            tar.extractall(target_dir, filter='data')

    return target_dir


class Runner:
    __slots__ = ('_dataset_dir', '_limit', '_warmups')

    def __init__(
        self,
        dataset_dir: Path,
        arguments: argparse.Namespace,
    ) -> None:
        self._dataset_dir = shlex.quote(str(dataset_dir))
        self._warmups = str(arguments.warmups)
        limit: int | None = arguments.limit
        self._limit = None if limit is None else str(limit)

    def __call__(self, name: str, command: Path, iteration: int) -> Iterable[BenchmarkRecord]:
        args = [shlex.quote(str(command)), self._dataset_dir, self._warmups]
        if limit := self._limit:
            args.append(limit)
        # Commands come from the fixed target map below.
        completed = subprocess.run(  # noqa: S603
            args,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            print(completed.stderr, file=sys.stderr, end='')
            raise SystemExit(completed.returncode)
        if completed.stderr:
            print(completed.stderr, file=sys.stderr, end='')

        for line in completed.stdout.splitlines():
            record: BenchmarkRecord = json.loads(line)
            record['target'] = name
            record['iteration'] = iteration
            yield record


def print_table(case: str, records: list[BenchmarkRecord]) -> None:
    grouped: dict[str, list[float]] = defaultdict(list)
    samples = int(records[0]['samples'])
    for record in records:
        grouped[str(record['target'])].append(float(record['elapsed_ns']))
    c_mean = statistics.mean(grouped['c'])
    print(f'\n{case} ({samples:,} samples)')
    header = (
        f'{"target":<14} {"median ms":>11} {"mean ms":>11} {"stddev ms":>11} '
        f'{"min ms":>11} {"max ms":>11} {"ns/element":>12} '
        f'{"M elements/s":>14} {"% of C":>8}'
    )
    print(header)
    for target, elapsed in grouped.items():
        mean = statistics.mean(elapsed)
        stddev = statistics.stdev(elapsed) if len(elapsed) > 1 else 0.0
        print(
            f'{target:<14} {statistics.median(elapsed) / 1e6:11.3f} {mean / 1e6:11.3f} '
            f'{stddev / 1e6:11.3f} {min(elapsed) / 1e6:11.3f} {max(elapsed) / 1e6:11.3f} '
            f'{mean / samples:12.2f} {samples * 1e3 / mean:14.2f} {mean / c_mean * 1e2:8.2f}x'
        )


def main() -> None:
    arguments = parse_arguments()
    root = Path(__file__).parent.relative_to(Path.cwd())
    dataset_dir = extract_dataset(root)
    run_target = Runner(dataset_dir, arguments)
    # rs_prefix = root.joinpath('ptfkit-rs', 'target')
    native_prefix = root.joinpath('ptfkit-native', 'build')
    targets = [
        ('c', native_prefix / 'ptfkit-c-benchmarks'),
        # ('cpp', native_prefix / 'ptfkit-cpp-benchmarks'),
        ('python', root.joinpath('ptfkit-py', '.venv', 'bin', 'ptfkit-py-benchmarks')),
        # ('rust-inline', rs_prefix.joinpath('inline', 'release', 'ptfkit-rs-benchmarks')),
        # ('rust-no-inline', rs_prefix.joinpath('no-inline', 'release', 'ptfkit-rs-benchmarks')),
    ]
    records = []
    for iteration in range(arguments.iterations):
        print(f'Iteration{iteration + 1: 3}: ', end='')
        offset = iteration % len(targets)
        for name, command in targets[offset:] + targets[:offset]:
            print(name, end=' ', flush=True)
            records.extend(run_target(name, command, iteration))
        print()
    by_case: dict[str, list[BenchmarkRecord]] = defaultdict(list)
    for record in records:
        by_case[str(record['case'])].append(record)
    for case, case_records in by_case.items():
        print_table(case, case_records)


if __name__ == '__main__':
    main()
