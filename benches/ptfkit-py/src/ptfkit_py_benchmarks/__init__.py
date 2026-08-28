from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from ptfkit._ptfkit import (
    calc_ptf_dharumarajan2019_infiltration_batch,
    calc_ptf_dharumarajan2019_infiltration_batch_avx512,
    calc_ptf_li2007_batch,
    calc_ptf_li2007_batch_avx512,
    calc_ptf_li2007_batch_avx512_u35,
    calc_ptf_li2007_batch_u35,
)
from ptfkit.dharumarajan2019 import calc_ptf_dharumarajan2019_infiltration
from ptfkit.li2007 import Li2007PTFResult, calc_ptf_li2007
from ptfkit.mayr1999 import Mayr1999PTFResult, calc_ptf_mayr1999


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset', type=Path)
    parser.add_argument('warmups', type=int)
    parser.add_argument('limit', type=int, nargs='?')
    return parser.parse_args()


def print_record(case: str, samples: int, elapsed_ns: int) -> None:
    print(
        json.dumps(
            {
                'target': 'python',
                'case': case,
                'samples': samples,
                'elapsed_ns': elapsed_ns,
            }
        )
    )


def main() -> None:
    arguments = parse_arguments()
    dataset_dir: Path = arguments.dataset
    sand = np.load(dataset_dir / 'sand.npy')
    silt = np.load(dataset_dir / 'silt.npy')
    clay = np.load(dataset_dir / 'clay.npy')
    bulk_density = np.load(dataset_dir / 'bulk_density.npy')
    organic_carbon = np.load(dataset_dir / 'organic_carbon.npy')
    samples = arguments.limit or len(sand)
    sand, silt, clay = sand[:samples], silt[:samples], clay[:samples]
    bulk_density, organic_carbon = bulk_density[:samples], organic_carbon[:samples]

    infiltration = np.empty(samples, dtype=np.float64)
    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_dharumarajan2019_infiltration(sand=sand, silt=silt, clay=clay, out=infiltration)
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = infiltration.sum()
            print_record('dharumarajan2019_infiltration', samples, elapsed_ns)

    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_dharumarajan2019_infiltration_batch(sand, silt, clay, out=infiltration)
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = infiltration.sum()
            print_record('dharumarajan2019_infiltration_batch', samples, elapsed_ns)

    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_dharumarajan2019_infiltration_batch_avx512(sand, silt, clay, out=infiltration)
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = infiltration.sum()
            print_record('dharumarajan2019_infiltration_batch_avx512', samples, elapsed_ns)

    mayr_out = Mayr1999PTFResult(*(np.empty(samples, dtype=np.float64) for _ in range(3)))
    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_mayr1999(
            sand=sand,
            silt=silt,
            clay=clay,
            bulk_density=bulk_density,
            organic_carbon=organic_carbon,
            out=mayr_out,
        )
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = sum(output.sum() for output in mayr_out)
            print_record('mayr1999', samples, elapsed_ns)

    li_out = Li2007PTFResult(*(np.empty(samples, dtype=np.float64) for _ in range(4)))
    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_li2007(
            sand=sand,
            silt=silt,
            clay=clay,
            bulk_density=bulk_density,
            soil_organic_matter=organic_carbon,
            out=li_out,
        )
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = sum(output.sum() for output in li_out)
            print_record('li2007', samples, elapsed_ns)

    li_batch_out = Li2007PTFResult(*(np.empty(samples, dtype=np.float64) for _ in range(4)))
    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_li2007_batch(
            sand,
            silt,
            clay,
            bulk_density,
            organic_carbon,
            out=tuple(li_batch_out),
        )
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = sum(output.sum() for output in li_batch_out)
            print_record('li2007_batch', samples, elapsed_ns)

    li_batch_u35_out = Li2007PTFResult(*(np.empty(samples, dtype=np.float64) for _ in range(4)))
    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_li2007_batch_u35(
            sand,
            silt,
            clay,
            bulk_density,
            organic_carbon,
            out=tuple(li_batch_u35_out),
        )
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = sum(output.sum() for output in li_batch_u35_out)
            print_record('li2007_batch_u35', samples, elapsed_ns)

    li_batch_avx512_out = Li2007PTFResult(*(np.empty(samples, dtype=np.float64) for _ in range(4)))
    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_li2007_batch_avx512(
            sand,
            silt,
            clay,
            bulk_density,
            organic_carbon,
            out=tuple(li_batch_avx512_out),
        )
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = sum(output.sum() for output in li_batch_avx512_out)
            print_record('li2007_batch_avx512', samples, elapsed_ns)

    li_batch_avx512_u35_out = Li2007PTFResult(
        *(np.empty(samples, dtype=np.float64) for _ in range(4))
    )
    for iteration in range(arguments.warmups + 1):
        started = time.perf_counter_ns()
        calc_ptf_li2007_batch_avx512_u35(
            sand,
            silt,
            clay,
            bulk_density,
            organic_carbon,
            out=tuple(li_batch_avx512_u35_out),
        )
        elapsed_ns = time.perf_counter_ns() - started
        if iteration == arguments.warmups:
            _ = sum(output.sum() for output in li_batch_avx512_u35_out)
            print_record('li2007_batch_avx512_u35', samples, elapsed_ns)
