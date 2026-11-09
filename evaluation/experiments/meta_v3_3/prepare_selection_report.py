"""Export existing selection evidence without rerunning PTFs or inventing fits.

Run from the repository root:
uv run --no-project --with matplotlib python \
    evaluation/experiments/meta_v3_3/prepare_selection_report.py
"""

# ruff: noqa: INP001, E501, RUF001 - Standalone report with scientific notation and Markdown links.

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'evaluation/datasets/meta_v3_3.model-selection-summary.json'
OUTPUT = Path(__file__).parent / 'final_results'
FAMILIES = (
    'van_genuchten_mualem_v1',
    'van_genuchten_m1_v1',
    'brooks_corey_v1',
    'clapp1978_gradual_air_entry_v1',
)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_selection(data: dict) -> list[dict]:
    rows = []
    for basis in ('volumetric_water_content', 'gravimetric_water_content', 'ksat'):
        analysis = data['analyses'][basis]
        cohorts = [('primary', analysis['primary'])]
        if basis == 'ksat':
            cohorts.append(('maximum_coverage', analysis['widest_cohort']))
        for cohort_id, cohort in cohorts:
            candidates = [('atomic', row['function'], row) for row in cohort['ranking']]
            if basis != 'ksat':
                candidates.extend(
                    ('ensemble', name, score) for name, score in analysis['ensembles'].items()
                )
            for kind, name, score in candidates:
                pressure = score['pressure_range_kpa']
                rows.append(
                    {
                        'target': basis,
                        'cohort': cohort_id,
                        'kind': kind,
                        'model': name,
                        'metric_unit': 'log10_ratio'
                        if basis == 'ksat'
                        else ('m3/m3' if basis == 'volumetric_water_content' else 'kg/kg'),
                        'rmse': score['rmse'],
                        'mae': score['mae'],
                        'bias_prediction_minus_observation': score['bias'],
                        'samples': score['samples'],
                        'observations': score['observations'],
                        'sources': score['sources'],
                        'pressure_min_kpa': pressure[0] if pressure else None,
                        'pressure_max_kpa': pressure[1] if pressure else None,
                        'fraction_within_factor_2': score.get('factor_2'),
                        'fraction_within_factor_5': score.get('factor_5'),
                        'fraction_within_factor_10': score.get('factor_10'),
                        'status': 'existing_exploratory_E5_result',
                    }
                )
    return rows


def figure(data: dict) -> None:
    import matplotlib as mpl  # noqa: PLC0415 - Optional for --data-only exports.

    mpl.use('Agg')
    import matplotlib.pyplot as plt  # noqa: PLC0415 - Select the backend before pyplot.

    plt.rcParams.update(
        {
            'font.size': 10,
            'svg.fonttype': 'none',
            'svg.hashsalt': 'ptfkit',
            'axes.spines.top': False,
            'axes.spines.right': False,
            'font.family': 'DejaVu Sans',
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(15, 8.4))
    analyses = data['analyses']
    configurations = [
        ('volumetric_water_content', 'primary', 'A  Volumetric WRC', 'RMSE (m³/m³)', 5),
        ('ksat', 'primary', 'B  Ksat: broad-roster common cohort', 'RMSE (log₁₀ Ksat)', 5),
        ('gravimetric_water_content', 'primary', 'C  Gravimetric WRC', 'RMSE (kg/kg)', 3),
        ('ksat', 'widest_cohort', 'D  Ksat: maximum-coverage cohort', 'RMSE (log₁₀ Ksat)', 3),
    ]
    for ax, (basis, cohort_key, title, unit, count) in zip(axes.flat, configurations, strict=True):
        cohort = analyses[basis][cohort_key]
        records = cohort['ranking'][:count]
        names = [
            r['function']
            .removeprefix('calc_ptf_')
            .replace('ferrerjulia2004_', '')
            .replace('varallyai1982_', 'Varallyai ')
            .replace('chakraborty2011_', 'Chakraborty ')
            .replace('_', ' ')
            for r in records
        ]
        names = [f'{name} (N={r["samples"]})' for name, r in zip(names, records, strict=True)]
        values = [r['rmse'] for r in records]
        if basis != 'ksat':
            names.append(f'Mean ensemble (N={cohort["samples"]}; pooled)')
            values.append(analyses[basis]['ensembles']['mean']['rmse'])
        colors = ['#16766d'] + ['#9eafbc'] * (len(records) - 1)
        if basis != 'ksat':
            colors.append('#c58833')
        ax.barh(range(len(values)), values, color=colors, height=0.62)
        ax.set_yticks(range(len(values)), names)
        ax.invert_yaxis()
        if basis == 'ksat':
            ax.set_ylim(len(values) + 0.7, -0.7)
        ax.set_xlabel(unit)
        ax.set_title(
            f'{title}\nN = {cohort["samples"]} samples; {cohort["observations"]} observations',
            loc='left',
            fontsize=11,
            pad=12,
        )
        ax.set_xlim(0, max(values) * 1.25)
        for i, value in enumerate(values):
            ax.text(value + max(values) * 0.02, i, f'{value:.4f}', va='center', fontsize=9)
        ax.xaxis.grid(visible=True, alpha=0.15)
        ax.set_axisbelow(True)
        if basis == 'ksat' and cohort_key == 'widest_cohort':
            ax.set_xscale('symlog', linthresh=1)
            ax.text(
                0.98,
                0.04,
                'Dane–Puckett recommended for coverage\nWithin ×2 / ×5: 30.8% / 71.8%\nNonlinear axis; block sensitivity retained',
                transform=ax.transAxes,
                ha='right',
                va='bottom',
                fontsize=9,
            )
        elif basis == 'ksat':
            ax.text(
                0.98,
                0.02,
                'Gleyic cambisol sand: common-cohort winner\nWithin ×2 / ×5: 80.0% / 96.7%',
                transform=ax.transAxes,
                ha='right',
                fontsize=9,
            )
    fig.suptitle('ptfkit: existing PTF selection evidence', x=0.04, ha='left', fontsize=17)
    fig.text(
        0.04,
        0.025,
        'Compare models within each panel only. Different cohorts and water bases are separate.\n'
        'Ensemble gains are pooled; no ensemble meets the registered robustness rule. '
        'Exploratory benchmark, meta_v3.3; results are dataset-specific.',
        fontsize=9,
    )
    fig.tight_layout(rect=(0.02, 0.09, 0.99, 0.94), h_pad=3, w_pad=3)
    for extension in ('png', 'svg'):
        fig.savefig(
            OUTPUT / 'figures' / f'figure_1_ptf_selection.{extension}',
            dpi=220,
            facecolor='white',
            metadata={'Date': None} if extension == 'svg' else None,
        )
    plt.close(fig)


def report(data: dict) -> str:
    analyses = data['analyses']
    lines = [
        '# ptfkit benchmark results — selection complete; approximation pending',
        '',
        (
            '**Status:** Part A reuses the existing verified aggregate checkpoint. Part B cannot '
            'be calculated in this checkout: the full workbook and private WRC ledger/run artifacts '
            'are absent. No full-ledger approximation results or presentation are claimed.'
        ),
        '',
        '## Dataset and interpretation',
        '',
        (
            'The existing selection ledger contains 1,701 WRC points in 142 sample records '
            '(1,069 volumetric; 632 gravimetric), 19 source labels and one explicitly identified '
            'profile; 136 sample records lack profile IDs. Ksat contains 39 observations across '
            'three source labels and four source/unit blocks. These are workbook records, not '
            'independently verified laboratory measurements. The full WRC ledger is larger than '
            'the PTF-compatible cohorts below.'
        ),
        '',
        (
            'WRC RMSE is sqrt(mean across samples of within-sample mean squared error); MAE '
            'and bias also weight samples equally. Bias is prediction minus observation. Ksat '
            'errors are log10(prediction/observation). Cohort-specific errors must not be ranked '
            'across different rows or water bases. Reported pressure limits describe observed '
            'support, not confidence intervals or uniformly validated interpolation domains.'
        ),
        '',
        '## PTF selection',
        '',
        '| Target / cohort | Selected function | RMSE | MAE | Bias | Samples / points | Pressure (kPa) |',
        '|---|---|---:|---:|---:|---:|---|',
    ]
    for basis, key, label in [
        ('volumetric_water_content', 'primary', 'Volumetric, m³/m³'),
        ('gravimetric_water_content', 'primary', 'Gravimetric, kg/kg'),
        ('ksat', 'primary', 'Ksat common cohort, log10'),
        ('ksat', 'widest_cohort', 'Ksat maximum coverage, log10'),
    ]:
        score = analyses[basis][key]['ranking'][0]
        pressure = score['pressure_range_kpa']
        limits = f'{pressure[0]:.5g}–{pressure[1]:.6g}' if pressure else '—'
        lines.append(
            f'| {label} | `{score["function"]}` | {score["rmse"]:.6f} | '
            f'{score["mae"]:.6f} | {score["bias"]:+.6f} | '
            f'{score["samples"]} / {score["observations"]} | {limits} |'
        )
    lines.extend(
        [
            '',
            (
                'Varallyai chernozem A is close to B on the same 17-sample cohort '
                '(RMSE 0.042692 versus 0.042122); meadow, chernozem C and Clapp yield '
                '0.067764, 0.068704 and 0.087605. B ranks second in both source-omission '
                'rankings, so its pooled win is not evidence of dominance under source shift. '
                'The wider three-model common cohort also favors B (30 samples, 608 points, '
                'RMSE 0.045390); this is a separate comparison.'
            ),
            '',
            (
                'Chakraborty eq4 has only eight samples and one source on the primary gravimetric '
                'cohort. Eq1 is essentially tied (0.090029 versus 0.089888); eq4 ranks first in '
                '54.4% of sample bootstrap draws. This supports a tentative dataset-specific '
                'candidate, not a strong distinction between the equations.'
            ),
            '',
            '### Ensembles',
            '',
            '| Basis | Best atomic RMSE | Mean pooled RMSE | Relative change | Held-out evidence |',
            '|---|---:|---:|---:|---|',
        ]
    )
    for basis, label, evidence in [
        (
            'volumetric_water_content',
            'Volumetric',
            'Mean beats pooled-best atomic in 1/2 source folds; nested reduced RMSE 0.063124',
        ),
        (
            'gravimetric_water_content',
            'Gravimetric',
            'Mean beats pooled-best atomic in 84.4% of 499 evaluable out-of-bag draws; one source only',
        ),
    ]:
        a = analyses[basis]
        atomic, blend = a['primary']['ranking'][0]['rmse'], a['ensembles']['mean']['rmse']
        lines.append(
            f'| {label} | {atomic:.6f} | {blend:.6f} | '
            f'{100 * (blend / atomic - 1):+.2f}% | {evidence} |'
        )
    lines.extend(
        [
            '',
            (
                'The registered robustness rule requires at least 1% pooled improvement and lower '
                'error in every held-out evaluation against both the training-selected and pooled-best '
                'atomic comparators. No ensemble passes. In the two volumetric source folds, mean '
                'ensemble RMSE is 0.042417 / 0.033509 versus pooled-best atomic 0.041308 / '
                '0.043576. The reduced ensemble reselects members inside training folds; its held-out '
                'RMSE 0.063124 must not be confused with its full-data RMSE 0.040081. Gravimetric '
                'out-of-bag evidence is within-source, not external source validation.'
            ),
            '',
            '### Ksat coverage and block sensitivity',
            '',
            (
                'Gleyic cambisol sand reaches factors ×2/×5/×10 on 80.0%/96.7%/100.0% of '
                'the 30-sample common cohort. Dane–Puckett reaches 30.8%/71.8%/79.5% on '
                'the separate 39-sample maximum-coverage cohort. The latter is the coverage '
                'recommendation, with substantial block sensitivity; it is not a universally '
                'block-stable winner. No Ksat ensemble is constructed.'
            ),
            '',
            '| Block | N | Dane–Puckett RMSE(log10) | Bias(log10) | Within ×2 / ×5 |',
            '|---|---:|---:|---:|---:|',
        ]
    )
    for block, scores in analyses['ksat']['widest_cohort']['block_metrics'].items():
        score = next(s for s in scores if s['function'].endswith('_dane_puckett'))
        lines.append(
            f'| {block} | {score["samples"]} | {score["rmse"]:.6f} | '
            f'{score["bias"]:+.6f} | {score["factor_2"]:.1%} / {score["factor_5"]:.1%} |'
        )
    lines.extend(
        [
            '',
            (
                'Dane–Puckett wins the remaining-data ranking after three of four block omissions. '
                'Omitting the 30-sample cm/min-assumed block changes the winner to Wosten Table 5 '
                '(nine remaining samples). This omission sensitivity is different from independent '
                'prediction on the omitted block. Full remaining and held-out rankings are retained '
                'in the JSON. The literal unit `cm/smin` was interpreted as cm/min; methods and '
                'measurement origins remain unconfirmed. Class-specific Ferrer-Julia regressions '
                'are E5 applicability extrapolations: FAO classes are not established by this workbook.'
            ),
            '',
            '## Analytical WRC approximation: pending original observations',
            '',
            (
                'The registry contains exactly four families: van Genuchten–Mualem, van Genuchten '
                'm=1, Brooks–Corey and Clapp gradual-air-entry. No additional family is needed. '
                'The registry currently declares volumetric contracts; gravimetric fits require an '
                'explicit mass-basis fitting path, rather than relabeling a volumetric fit or silently '
                'converting without measured same-sample bulk density.'
            ),
            '',
            (
                'No full-ledger fit success rates, AICc/BIC comparisons, pressure-dependent errors, '
                'bootstrap intervals or approximation winners can be recovered from PTF aggregates. '
                'The old six-sample pilot is not a substitute. Blank fields in '
                '`wrc_approximation_summary.csv` mean not assessed, never zero errors or zero success.'
            ),
            '',
            (
                'For completion, fit each sample and basis independently, preserve convergence, '
                'N, pressure support, parameters, boundary and physical checks, Jacobian diagnostics, '
                'RMSE/MAE/bias/R² and information criteria. Strict acceptance must require convergence, '
                'physical parameters, positive residual degrees of freedom, finite predictions, no '
                'critical bound hit and no degenerate fit. Show relaxed descriptive success separately '
                'where boundary/identifiability exclusions dominate. AICc is undefined when N ≤ k+1; '
                'a residual-variance parameter must be counted consistently. Compare families on '
                'the same sample/point sets and disclose acceptance-induced cohort differences.'
            ),
            '',
            (
                'Use the existing pressure regions: wet [0,10), intermediate [10,1500), dry '
                '[1500,∞) kPa. Report sample/point N, median and 95th-percentile absolute error '
                'and bias per region. Report observed support min/max and 5–95% separately from '
                'uncertainty. Resample entire samples for pressure-bin bootstrap bands; retain '
                'within-sample points together. Distinguish empirical residual intervals from '
                'confidence bands for residual summaries and from parameter intervals. Residuals '
                'at fitted points describe in-sample approximation; they do not establish prospective '
                'out-of-sample prediction coverage. No practical pressure trust range is asserted yet.'
            ),
            '',
            '## Artifacts and provenance',
            '',
            '- `ptf_selection_summary.csv`: all primary atomic rankings, WRC ensembles and maximum-coverage Ksat ranking.',
            '- `benchmark_aggregates.json`: original complete selection aggregates plus explicit completion status.',
            '- `wrc_approximation_summary.csv`: eight explicitly pending family/basis rows.',
            '- `figures/figure_1_ptf_selection.png` and `.svg`: separate comparable panels.',
            '- Figure 2 and `ptfkit_benchmark_summary.pptx` remain pending; the requested order is calculations, figures, then PPTX.',
            '',
            (
                'Sources: [MODEL-SELECTION.md](../MODEL-SELECTION.md), '
                '[WORKBOOK-SEMANTIC.md](../WORKBOOK-SEMANTIC.md), '
                '[aggregate checkpoint](../../../datasets/meta_v3_3.model-selection-summary.json). '
                'The source checkpoint SHA-256 is retained in the JSON. No PTF was unlocked, '
                'recalibrated or rerun for this export.'
            ),
            '',
            (
                'Reproduce Part A from the repository root with '
                '`uv run --no-project --with matplotlib python '
                'evaluation/experiments/meta_v3_3/prepare_selection_report.py`.'
            ),
            '',
            'Exploratory benchmark, meta_v3.3; results are dataset-specific.',
            '',
        ]
    )
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--data-only', action='store_true', help='Export tables and report without plotting.'
    )
    args = parser.parse_args()
    data = json.loads(SOURCE.read_bytes())
    (OUTPUT / 'figures').mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT / 'ptf_selection_summary.csv', export_selection(data))
    pending = [
        {
            'basis': basis,
            'family': family,
            'status': 'not_assessed_missing_original_data',
            'attempted_samples': None,
            'strict_success_rate': None,
            'relaxed_success_rate': None,
            'median_rmse': None,
            'median_mae': None,
            'median_delta_aicc': None,
            'median_delta_bic': None,
            'support_min_kpa': None,
            'support_max_kpa': None,
            'support_p05_kpa': None,
            'support_p95_kpa': None,
        }
        for basis in ('volumetric_water_content', 'gravimetric_water_content')
        for family in FAMILIES
    ]
    write_csv(OUTPUT / 'wrc_approximation_summary.csv', pending)
    aggregate = {
        'status': 'partial_selection_complete_approximation_blocked',
        'source_path': SOURCE.relative_to(ROOT).as_posix(),
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'selection': data,
        'approximation': {'status': 'not_assessed_missing_original_data', 'families': pending},
        'presentation': {'status': 'pending_completed_calculations_and_figures'},
    }
    (OUTPUT / 'benchmark_aggregates.json').write_text(
        json.dumps(aggregate, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8'
    )
    (OUTPUT / 'FINAL-RESULTS.md').write_text(report(data), encoding='utf-8')
    if not args.data_only:
        figure(data)
    inventory = {
        p.relative_to(OUTPUT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(OUTPUT.rglob('*'))
        if p.is_file() and p.name != 'artifact-hashes.json'
    }
    (OUTPUT / 'artifact-hashes.json').write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )


if __name__ == '__main__':
    main()
