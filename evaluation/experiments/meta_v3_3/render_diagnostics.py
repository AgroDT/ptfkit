"""Render PNG diagnostics from validated forecasts and saved fits, without refitting.

Outputs contain private sample identifiers and stay in ignored local storage.
"""

# ruff: noqa: INP001, E501, PLR0915, PLR0917, PLR0912, C901, RUF001 - Scientific plotting and annotations.

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import textwrap
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from zipfile import ZIP_DEFLATED, ZipFile

import matplotlib as mpl
import numpy as np


mpl.use('Agg')
import matplotlib.pyplot as plt

from evaluation.experiments.meta_v3_3 import model_selection as selection
from evaluation.experiments.meta_v3_3.final_approximation import predict


ROOT = Path(__file__).resolve().parents[3]
PUBLIC = Path(__file__).parent / 'final_results'
PRIVATE = ROOT / 'local/meta-final-benchmark'
REPLAY = ROOT / 'local/meta-diagnostic-replay'
OUTPUT = PRIVATE / 'diagnostics'
FAMILIES = (
    'van_genuchten_mualem_v1',
    'van_genuchten_m1_v1',
    'brooks_corey_v1',
    'clapp1978_gradual_air_entry_v1',
)
NAMES = dict(zip(FAMILIES, ('VG–Mualem', 'VG m=1', 'Brooks–Corey', 'Clapp'), strict=True))
COLORS = dict(zip(FAMILIES, ('#3876a6', '#16766d', '#c58833', '#9368a0'), strict=True))
COLUMNS = (
    'category',
    'target',
    'function_or_family',
    'cohort',
    'samples',
    'observations',
    'RMSE',
    'MAE',
    'bias',
    'strict_success',
    'relaxed_success',
    'file_path',
)


def read(path: Path) -> object:
    return json.loads(path.read_bytes())


def slug(value: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]+', '_', value).strip('_')


def sample_stem(key: tuple) -> str:
    digest = hashlib.sha256(json.dumps(key, ensure_ascii=True).encode()).hexdigest()[:10]
    return f'{slug(str(key[2]))[:65] or "sample"}_{digest}'


def basis_info(basis: str) -> tuple[str, str, str]:
    return (
        ('volumetric', 'm³/m³', 'Volumetric')
        if basis.startswith('volumetric')
        else ('gravimetric', 'kg/kg', 'Gravimetric')
    )


def canvas(title: str, annotation: str) -> tuple:
    fig = plt.figure(figsize=(11.5, 6.9))
    ax = fig.add_axes((0.09, 0.14, 0.51, 0.73))
    fig.suptitle(title, fontsize=14, x=0.07, ha='left', y=0.97)
    fig.text(0.65, 0.86, annotation, fontsize=9.5, va='top', linespacing=1.55)
    ax.grid(visible=True, alpha=0.16)
    return fig, ax


def save(fig: plt.Figure, relative: Path) -> str:
    path = OUTPUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, facecolor='white')
    plt.close(fig)
    return relative.as_posix()


def scatter(
    ax: plt.Axes, points: list[dict], unit: str, *, fitted: bool = False, ksat: bool = False
) -> None:
    observed = np.array([p['observed'] for p in points])
    predicted = np.array([p['predicted'] for p in points])
    ax.scatter(
        observed, predicted, s=13, alpha=0.42, color='#287889', edgecolors='none', rasterized=True
    )
    low, high = (
        float(min(observed.min(), predicted.min())),
        float(max(observed.max(), predicted.max())),
    )
    if ksat:
        if low <= 0:
            msg = 'Ksat log axes require positive points.'
            raise ValueError(msg)
        low, high = low / 1.5, high * 1.5
        ax.set_xscale('log')
        ax.set_yscale('log')
        x = np.geomspace(low, high, 400)
        for factor, color in ((2, '#319a67'), (5, '#d09a2f'), (10, '#a773b8')):
            for multiplier in (factor, 1 / factor):
                ax.plot(
                    x,
                    x * multiplier,
                    '--',
                    color=color,
                    lw=0.9,
                    alpha=0.8,
                    label=f'×{factor} bounds' if multiplier == factor else None,
                )
    else:
        pad = max((high - low) * 0.06, 0.01)
        low, high = min(0, low - pad), high + pad
    ax.plot([low, high], [low, high], color='#263a4a', lw=1.1, label='1:1')
    ax.set(
        xlim=(low, high),
        ylim=(low, high),
        xlabel=f'Measured {unit}',
        ylabel=f'{"Fitted" if fitted else "Predicted"} {unit}',
    )
    ax.set_aspect('equal', adjustable='box')
    ax.legend(fontsize=8, loc='upper left')


def index_row(
    category: str, target: str, name: str, cohort: str, score: dict, path: str, **extra: object
) -> dict:
    return dict(
        zip(
            COLUMNS,
            (
                category,
                target,
                name,
                cohort,
                score['samples'],
                score['observations'],
                score['rmse'],
                score['mae'],
                score['bias'],
                extra.get('strict', ''),
                extra.get('relaxed', ''),
                path,
            ),
            strict=True,
        )
    )


def check_metrics(actual: dict, expected: dict) -> None:
    for field in ('rmse', 'mae', 'bias', 'samples', 'observations'):
        if not math.isclose(actual[field], expected[field], rel_tol=1e-11, abs_tol=1e-13):
            msg = f'Diagnostic metric differs from benchmark: {field}.'
            raise ValueError(msg)


def ptf_plots(points: list[dict], analyses: dict) -> list[dict]:
    rows = []
    for basis in ('volumetric_water_content', 'gravimetric_water_content', 'ksat'):
        analysis = analyses[basis]
        ksat = basis == 'ksat'
        indices = defaultdict(dict)
        for point in points:
            if point['basis'] == basis and not point['water_conditioned']:
                indices[point['function']][point['id']] = point
        for fid in list(indices):
            keys = selection.eligible_keys(set(indices[fid]), indices[fid], ksat=ksat)
            indices[fid] = {k: indices[fid][k] for k in sorted(keys)}
        indices = {f: i for f, i in indices.items() if i}
        if set(indices) != set(analysis['coverage']):
            msg = 'Diagnostic roster differs from the scored benchmark roster.'
            raise ValueError(msg)
        cohorts = [('primary', analysis['primary'])]
        if ksat:
            cohorts.append(('maximum_coverage', analysis['widest_cohort']))
        cohorts.extend(
            (f'compatible_{i:02d}', c) for i, c in enumerate(analysis['compatible_cohorts'], 1)
        )
        jobs = {}
        for cohort_id, cohort in cohorts:
            for score in cohort['ranking']:
                fid = score['function']
                key = fid, tuple(cohort['keys'])
                if key in jobs:
                    jobs[key]['aliases'].append(cohort_id)
                else:
                    jobs[key] = {'score': score, 'aliases': [cohort_id]}
        for fid, index in indices.items():
            key = fid, tuple(sorted(index))
            if key not in jobs:
                jobs[key] = {
                    'score': selection.scored(list(index.values()), ksat=ksat),
                    'aliases': ['maximum_function_support'],
                }
        for (fid, keys), job in jobs.items():
            selected = [indices[fid][k] for k in keys]
            score = selection.scored(selected, ksat=ksat)
            check_metrics(score, job['score'])
            cohort = ' / '.join(job['aliases'])
            cohort_hash = hashlib.sha256(json.dumps(keys).encode()).hexdigest()[:8]
            cohort_label = f'{cohort} [{cohort_hash}]'
            short = fid.removeprefix('calc_ptf_')
            annotation = (
                textwrap.fill(fid, 42, break_long_words=True, break_on_hyphens=False) + '\n\n'
            )
            annotation += textwrap.fill(f'Cohort: {cohort_label}', 42) + '\n'
            annotation += (
                'Route: ' + selected[0].get('route_type', 'original registered PTF route') + '\n'
            )
            annotation += f'Samples: {score["samples"]}\nObservations: {score["observations"]}\n'
            suffix = ' (log10)' if ksat else ''
            annotation += '\n'.join(
                f'{label}{suffix}: {score[field]:.6f}'
                for label, field in (('RMSE', 'rmse'), ('MAE', 'mae'), ('Bias', 'bias'))
            )
            if ksat:
                annotation += '\n\n' + '\n'.join(
                    f'Within ×{factor}: {score[f"factor_{factor}"]:.1%}' for factor in (2, 5, 10)
                )
                blocks = Counter(p['block'] for p in selected)
                annotation += '\n\nBlocks (observations):\n' + '\n'.join(
                    f'{block}: {n}' for block, n in sorted(blocks.items())
                )
                folder, unit = 'Ksat', 'Ksat (m/s)'
            else:
                _, unit, label = basis_info(basis)
                folder = f'{label.lower()}_WRC'
                annotation += (
                    f'\n\nWater basis: {label.lower()}\nUnit: {unit}\nEqual sample weights'
                )
            fig, ax = canvas('Measured vs predicted\n' + short, annotation)
            scatter(ax, selected, unit, ksat=ksat)
            fig.text(
                0.09,
                0.035,
                'Compare errors only on identical cohorts and water bases. Workbook/E5 limitations apply.',
                fontsize=8.5,
            )
            path = save(
                fig, Path('PTF') / folder / f'{short}_{job["aliases"][0]}_{cohort_hash}.png'
            )
            rows.append(index_row('PTF', basis, fid, cohort_label, score, path))
    return rows


def approximation_plots(fits: list[dict], aggregates: dict) -> list[dict]:
    rows = []
    usable = [r for r in fits if r['relaxed_accepted']]
    by_sample = defaultdict(dict)
    for record in fits:
        by_sample[record['basis'], record['source_id'], record['sample_id']][record['family']] = (
            record
        )
    for basis, aggregate in aggregates.items():
        folder, unit, label = basis_info(basis)
        for summary in aggregate['summary']:
            family = summary['family']
            records = [r for r in usable if r['basis'] == basis and r['family'] == family]
            if len(records) != summary['paired_relaxed_samples']:
                msg = 'Approximation cohort differs from paired relaxed cohort.'
                raise ValueError(msg)
            points = [p for r in records for p in r['points']]
            for metric in ('rmse', 'mae'):
                if not math.isclose(
                    median(r[metric] for r in records), summary['median_' + metric], rel_tol=1e-12
                ):
                    msg = 'Stored approximation median differs from benchmark.'
                    raise ValueError(msg)
            bias = median(r['bias'] for r in records)
            annotation = family + f'\n\nWater basis: {label.lower()} ({unit})\n'
            annotation += f'Eligible samples: {summary["eligible_samples"]}\nStrict success: {summary["strict_successes"]}/{summary["eligible_samples"]}\nRelaxed success: {summary["relaxed_successes"]}/{summary["eligible_samples"]}\nObservations: {len(points)}\n\n'
            annotation += f'Median sample RMSE: {summary["median_rmse"]:.6f}\nMedian sample MAE: {summary["median_mae"]:.6f}\nMedian sample bias: {bias:+.6f}\n'
            annotation += f'\nMedian ΔAICc: {summary["median_delta_aicc"]:.4g} (N={summary["aicc_paired_samples"]})\nMedian ΔBIC: {summary["median_delta_bic"]:.4g} (N={summary["bic_paired_samples"]})\n\nCohort: paired relaxed success\nAll four families; same samples/points'
            fig, ax = canvas(
                f'Measured vs fitted — {NAMES[family]}\n{label} water content', annotation
            )
            scatter(ax, points, f'water content ({unit})', fitted=True)
            fig.text(
                0.09,
                0.035,
                'Descriptive fits to these measured data; this is not independent PTF validation.',
                fontsize=9,
            )
            path = save(fig, Path('APPROXIMATION') / folder / f'{family}.png')
            score = {
                'samples': len(records),
                'observations': len(points),
                'rmse': summary['median_rmse'],
                'mae': summary['median_mae'],
                'bias': bias,
            }
            rows.append(
                index_row(
                    'APPROXIMATION',
                    basis,
                    family,
                    'paired_relaxed_success',
                    score,
                    path,
                    strict=summary['strict_successes'],
                    relaxed=summary['relaxed_successes'],
                )
            )
    for key, family_records in sorted(by_sample.items()):
        accepted = [family_records[f] for f in FAMILIES if family_records[f]['relaxed_accepted']]
        if not accepted:
            continue
        basis, source, sample = key
        _, unit, label = basis_info(basis)
        measured = accepted[0]['points']
        positive = [p['pressure_kpa'] for p in measured if p['pressure_kpa'] > 0]
        zero_coordinate = min(positive) / 3
        lower = zero_coordinate if any(p['pressure_kpa'] == 0 for p in measured) else min(positive)
        pressures = np.geomspace(lower, max(positive), 450)
        scale = 1 if basis.startswith('volumetric') else 5
        fig, ax = plt.subplots(figsize=(9.7, 6.3))
        ax.scatter(
            [p['pressure_kpa'] or zero_coordinate for p in measured],
            [p['observed'] for p in measured],
            c='#182c3a',
            s=30,
            zorder=5,
            label='Measured WRC points',
        )
        for family in FAMILIES:
            record = family_records[family]
            if not record['relaxed_accepted']:
                ax.plot([], [], color=COLORS[family], label=f'{NAMES[family]}: no accepted fit')
                continue
            h = (
                np.concatenate(([0], pressures))
                if any(p['pressure_kpa'] == 0 for p in measured)
                else pressures
            )
            values = predict(family, record['parameters'], h, scale)
            stored = predict(
                family,
                record['parameters'],
                np.array([p['pressure_kpa'] for p in record['points']]),
                scale,
            )
            if not np.allclose(
                stored, [p['predicted'] for p in record['points']], rtol=1e-10, atol=1e-12
            ):
                msg = 'Re-evaluated saved curve differs from stored fitted points.'
                raise ValueError(msg)
            display_h = np.where(h == 0, zero_coordinate, h)
            status = 'strict' if record['strict_accepted'] else 'relaxed only'
            ax.plot(
                display_h,
                values,
                color=COLORS[family],
                lw=1.7,
                ls='-' if record['strict_accepted'] else '--',
                label=f'{NAMES[family]}: RMSE={record["rmse"]:.5f}; {status}',
            )
        ax.set_xscale('log')
        ax.set(
            xlabel='Suction magnitude (kPa)',
            ylabel=f'{label} water content ({unit})',
            title='Measured WRC and fitted curves\n'
            + '\n'.join(textwrap.wrap(f'Sample: {sample} | Source: {source}', 95)),
        )
        ax.grid(visible=True, alpha=0.18)
        ax.legend(fontsize=9)
        foot = 'Curves evaluated from saved parameters; no refitting. Same-data descriptive approximation.'
        if any(p['pressure_kpa'] == 0 for p in measured):
            foot += f'\nZero suction displayed at {zero_coordinate:.3g} kPa (left of observed positive support).'
        fig.text(0.08, 0.025, foot, fontsize=8)
        fig.tight_layout(rect=(0, 0.08, 1, 1))
        path = save(fig, Path('APPROXIMATION/per_sample') / f'{sample_stem(key)}.png')
        for record in accepted:
            score = {
                'samples': 1,
                'observations': record['n'],
                **{m: record[m] for m in ('rmse', 'mae', 'bias')},
            }
            rows.append(
                index_row(
                    'APPROXIMATION',
                    basis,
                    record['family'],
                    f'sample:{source}/{sample}',
                    score,
                    path,
                    strict=int(record['strict_accepted']),
                    relaxed=1,
                )
            )
    return rows


def main() -> None:
    frozen = read(PUBLIC / 'benchmark_aggregates.json')
    fit_path = PRIVATE / 'approximation-fits.json'
    if (
        hashlib.sha256(fit_path.read_bytes()).hexdigest()
        != frozen['approximation']['private_fit_artifact_sha256']
    ):
        msg = 'Saved fit artifact differs from the final benchmark.'
        raise ValueError(msg)
    if not read(REPLAY / 'validation.json')['all_published_analyses_identical']:
        msg = 'Forecast replay has not passed benchmark validation.'
        raise ValueError(msg)
    fits = read(fit_path)['results']
    OUTPUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            'font.size': 10,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'font.family': 'DejaVu Sans',
        }
    )
    rows = ptf_plots(read(REPLAY / 'predictions.json'), read(REPLAY / 'analyses.json'))
    rows.extend(approximation_plots(fits, frozen['approximation']['aggregates']))
    with (OUTPUT / 'diagnostic_index.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    shutil.copyfile(PUBLIC / 'ENSEMBLE-METHODOLOGY.md', OUTPUT / 'ENSEMBLE-METHODOLOGY.md')
    exclusions = PUBLIC / 'NONPARTICIPATING-FUNCTIONS.md'
    if exclusions.exists():
        shutil.copyfile(exclusions, OUTPUT / exclusions.name)
    readme = """# ptfkit diagnostic images

`PTF/` contains measured-vs-predicted diagnostics for all scored independent PTFs,
separately for volumetric WRC, gravimetric WRC and Ksat. Predictions were replayed
from the pinned workbook using the existing implementation; all published
selection analyses matched the final benchmark exactly. No PTF was recalibrated.
Water-conditioned functions are excluded from independent PTF diagnostics.

`APPROXIMATION/volumetric/` and `gravimetric/` contain measured-vs-fitted plots for
all four registered WRC families on the paired relaxed-success cohorts.
`per_sample/` contains one image per usable sample, with all four saved curves;
dashed curves labelled "relaxed only" failed strict acceptance. These parameters
were fitted to the displayed observations, so the errors describe approximation,
not independent predictive performance. No fitting was repeated.

WRC PTF RMSE, MAE and bias use equal sample weights, matching the benchmark.
Approximation overview metrics are medians of per-sample metrics, including bias;
per-sample index rows contain that sample's metrics. Success counts use eligible
fits as the denominator; information-criterion deltas use their stated common N.
Bias is predicted/fitted minus measured. Ksat metrics use log10(predicted/measured).
Ksat is plotted in m/s on two logarithmic axes. Dashed factor ×2, ×5 and ×10
bounds enclose predictions between measured/factor and measured*factor; fractions
report points inside each band. Block observation counts appear on each Ksat plot.

Every distinct compatible cohort and each function's maximum scored support are
retained. Identical function/observation sets share one image with cohort aliases;
the short cohort hash identifies its observation set. Counts and errors can differ
between cohorts: do not rank errors across different cohorts or water bases.
Workbook origins, unit assumptions and E5 applicability limitations remain those
of FINAL-RESULTS.md; no new selection conclusion is introduced.

`diagnostic_index.csv` lists every image. Per-sample images have four rows (one
per family) sharing a file path; other images have one row. File paths are relative
to this directory. Sample filenames use a safe ASCII stem plus an identity hash;
full source/sample IDs remain on the images and in the index. Zero suction cannot
appear on a logarithmic axis: its point and curve endpoint are placed left of the
smallest positive observed suction at the explicitly stated display coordinate.
That endpoint is evaluated at zero, not at its display coordinate.

Reproduction from the repository root after `uv sync --project targets/ptfkit-eval`:

```sh
uv run --project targets/ptfkit-eval --no-sync python -B -m evaluation.experiments.meta_v3_3.replay_diagnostic_predictions
uv run --project targets/ptfkit-eval --no-sync --with matplotlib python -B -m evaluation.experiments.meta_v3_3.render_diagnostics
```

The replay output directory must be new. Private inputs and outputs remain under
`local/`; the archive contains this diagnostic directory only. The source PDF and
historical frozen resource directories were unavailable; replay reapplied the
persisted source-review JSON and verified the workbook and canonical dataset.
Existing benchmark conclusions, presentation and figures were not modified.
"""
    (OUTPUT / 'README.md').write_text(readme, encoding='utf-8')
    pngs = sorted(OUTPUT.rglob('*.png'))
    if {r['file_path'] for r in rows} != {p.relative_to(OUTPUT).as_posix() for p in pngs}:
        msg = 'Index and rendered PNG inventory differ.'
        raise ValueError(msg)
    with ZipFile(PRIVATE / 'ptfkit-diagnostics.zip', 'w', compression=ZIP_DEFLATED) as archive:
        for path in sorted(OUTPUT.rglob('*')):
            if path.is_file():
                archive.write(path, (Path('diagnostics') / path.relative_to(OUTPUT)).as_posix())
    print(  # noqa: T201 - Command result.
        f'{len(pngs)} PNG images; {len(rows)} index rows; archive: {PRIVATE / "ptfkit-diagnostics.zip"}',
        flush=True,
    )


if __name__ == '__main__':
    main()
