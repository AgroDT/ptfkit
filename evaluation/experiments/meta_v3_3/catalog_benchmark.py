"""Rebuild the fixed evaluation resource and compare the current public PTF catalog."""

# ruff: noqa: INP001 - Repository benchmark entry point.

from __future__ import annotations

import argparse
from pathlib import Path

from evaluation.experiments.meta_v3_3 import benchmark, campaign, harmonized


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook', type=Path, required=True)
    parser.add_argument('--paper', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--previous', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    resource = args.output / 'resource'
    main_view = args.output / 'harmonized'
    benchmark.run(args.workbook, args.paper, resource)
    harmonized.run(resource, main_view)
    campaign.run(resource, main_view, args.workbook, args.output / 'comparison', args.previous)


if __name__ == '__main__':
    main()
