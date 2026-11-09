"""Publish the expanded selection, complete second-chance audit and PNG package."""

# ruff: noqa: INP001, E501, C901, PLR0912, PLR0915, PLR2004, RUF001, PERF401 - Scientific report prose and plotting.

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import textwrap
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from evaluation.experiments.meta_v3_3 import expanded_routes as routes
from evaluation.experiments.meta_v3_3 import model_selection as original
from evaluation.experiments.meta_v3_3 import render_diagnostics as render
from evaluation.experiments.meta_v3_3.expanded_participation import (
    BASES,
    OUTPUT,
    PUBLIC,
    ROOT,
    read,
)
from evaluation.experiments.meta_v3_3.final_approximation import json_write


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def participation_audit(
    points: list[dict], analyses: dict, metadata: dict, registry: dict, secondary: list[dict]
) -> tuple[list[dict], dict]:
    scope = read(OUTPUT / 'scope.json')
    failures = read(OUTPUT / 'failures.json')
    baseline = read(OUTPUT / 'baseline/benchmark_aggregates.json')
    all_scored = set().union(*(set(analyses[b]['coverage']) for b in BASES))
    scored_points = []
    for basis in BASES:
        for fid in analyses[basis]['coverage']:
            index = {p['id']: p for p in points if p['basis'] == basis and p['function'] == fid}
            keys = original.eligible_keys(set(index), index, ksat=basis == 'ksat')
            scored_points.extend(index[k] for k in keys)
    contributors = set()
    for point in scored_points:
        fid = point['function']
        if fid in registry['families']:
            family = registry['families'][fid]
            support = routes.supporting_pressures(
                point['native_pressure_support_kpa'], point['pressure_kpa']
            )
            used = sorted(
                {m['function'] for m in family['members'] if m['target']['pressure_kpa'] in support}
            )
            point['native_member_functions_used'] = used
            contributors.update(used)
        else:
            contributors.add(fid)
    old = set(scope['previously_scored'])
    newly_scored = contributors - old
    point_ids = {p['function'] for p in secondary}
    mechanisms = Counter()
    for fid in newly_scored:
        mechanism = (
            metadata[fid]['mechanism']
            if fid in metadata
            else 'Fixed-pressure family reconstruction'
        )
        mechanisms[mechanism] += 1
    decisions = []
    previous = {r['function']: r for r in baseline['selection']['catalog']}
    for fid in scope['reconsidered']:
        record = previous[fid]
        reason, dispositions = '', []
        candidate_models = [
            model
            for model in all_scored
            if model == fid
            or (
                model in registry['families']
                and fid in {m['function'] for m in registry['families'][model]['members']}
            )
        ]
        if fid in contributors:
            dispositions.append('now_scored_full_wrc')
            reason = 'Independent full-WRC predictions contribute on at least one eligible observed-pressure cohort.'
        if fid in analyses['ksat']['coverage']:
            dispositions.append('now_scored_ksat')
        if fid in point_ids:
            dispositions.append('now_scored_point_target')
            if not reason:
                reason = 'Native-pressure secondary scoring only; insufficient valid/supporting native coordinates for independent full-WRC scoring.'
        if not dispositions:
            if fid in registry['unresolved']:
                reason = registry['unresolved'][fid]
                dispositions = [
                    'user_decision_required'
                    if 'needs_user_decision' in reason
                    else 'still_missing_predictor'
                ]
            elif fid.startswith('calc_ptf_pidgeon1972_') or fid == 'calc_ptf_saxton2006_salinity':
                dispositions = ['excluded_other_target']
                reason = 'AWC/extended AWC or osmotic potential is not an absolute matric WRC water content; retained in the audit but not evaluated, as requested.'
            elif fid in ('calc_ptf_saxton2006_tension_dry', 'calc_ptf_saxton2006_tension_wet'):
                dispositions = ['still_missing_predictor']
                reason = 'The independent Saxton base anchors could not be combined with valid inputs, this segment support and actual same-record density where conversion is needed; no measured-water anchors were substituted.'
            elif any(k.startswith('missing_predictor') for k in failures.get(fid, {})):
                dispositions = ['still_missing_predictor']
                reason = (
                    'No admissible independent same-record values for: '
                    + ', '.join(
                        sorted(
                            k.split(':', 1)[1]
                            for k in failures[fid]
                            if k.startswith('missing_predictor')
                        )
                    )
                    + '.'
                )
            elif any('domain' in k or 'nonphysical' in k for k in failures.get(fid, {})):
                dispositions = ['still_physical_domain_failure']
                reason = 'Recovered values or evaluated outputs fail registered domain/physical checks; no clipping or formula changes.'
            elif any('insufficient_native' in k for k in failures.get(fid, {})):
                dispositions = ['insufficient_native_pressure_points']
                reason = 'No sample provides at least three valid native pressures plus overlapping scored observations.'
            else:
                dispositions = ['still_adapter_unresolved']
                reason = 'No unambiguous independent target route with available same-record inputs and observed support.'
        decisions.append(
            {
                'function': fid,
                'previous_disposition': record['wrc_disposition'],
                'previous_group': 'failed_executable'
                if record['wrc_targets'] or record['ksat_targets']
                else record['wrc_disposition'],
                'dispositions': dispositions,
                'reason': reason,
                'scored_candidates': sorted(candidate_models),
                'failure_counts': failures.get(fid, {}),
                'secondary_points': sum(p['function'] == fid for p in secondary),
            }
        )
    if len(decisions) != 119 or {r['function'] for r in decisions} != set(scope['reconsidered']):
        message = 'Every formerly excluded function in the three requested groups must have a disposition.'
        raise ValueError(message)
    stats = {
        'old_participating_functions': 58,
        'newly_participating_functions': len(newly_scored),
        'final_participating_functions': len(old | contributors),
        'new_functions': sorted(newly_scored),
        'full_wrc_ksat_candidate_count': len(all_scored),
        'new_family_candidates': sorted(k for k in all_scored if k in registry['families']),
        'secondary_point_functions': len(point_ids),
        'secondary_point_only_functions': len(point_ids - contributors - old),
        'all_scored_including_secondary_functions': len(old | contributors | point_ids),
        'mechanisms': dict(mechanisms),
        'reconsidered_functions': 119,
        'disposition_counts': dict(Counter(d for r in decisions for d in r['dispositions'])),
    }
    return decisions, stats


def report(analyses: dict, stats: dict, decisions: list[dict], metadata: dict) -> None:
    baseline = read(OUTPUT / 'baseline/benchmark_aggregates.json')
    lines = [
        '## Expanded PTF participation',
        '',
        f'The coverage-first E5 second-chance pass reconsidered exactly 119 functions: 64 isolated-pressure, 17 unresolved-adapter and 38 failed-executable entries. The old independent participation was **58 unique catalog functions**; **{stats["newly_participating_functions"]} newly contributing functions** bring full-WRC/Ksat participation to **{stats["final_participating_functions"]}**. Discrete-family members count only if their native prediction actually contributes to a scored measured-pressure value; membership in a registry alone is not participation.',
        '',
        f'The selection roster contains {stats["full_wrc_ksat_candidate_count"]} unique candidates, including {len(stats["new_family_candidates"])} newly scored scientific families. Candidate/family counts differ from underlying function counts. The separate native-pressure benchmark scores {stats["secondary_point_functions"]} functions, of which {stats["secondary_point_only_functions"]} are additional point-only functions. Including this secondary analysis, {stats["all_scored_including_secondary_functions"]} unique catalog functions have scored outputs; point-only results never enter full-WRC ranking or ensembles.',
        '',
        '| Mechanism | Newly scored contributing functions | Newly scored families |',
        '|---|---:|---:|',
    ]
    for mechanism in (
        'Fixed-pressure family reconstruction',
        'Retention-parameter adapters',
        'Predictor recovery',
        'Resolver/implementation fixes',
    ):
        families = sum(
            metadata[f]['mechanism'] == mechanism for f in stats['new_family_candidates']
        )
        lines.append(f'| {mechanism} | {stats["mechanisms"].get(mechanism, 0)} | {families} |')
    lines.extend(
        [
            '',
            '### Atomic selection before and after',
            '',
            '| Target / comparison | Before | After | After RMSE | After samples / observations |',
            '|---|---|---|---:|---:|',
        ]
    )
    for basis in BASES:
        old = baseline['selection']['analyses'][basis]['primary']['ranking'][0]
        new = analyses[basis]['primary']['ranking'][0]
        lines.append(
            f'| {basis}: primary | `{old["function"]}` | `{new["function"]}` | {new["rmse"]:.6f} | {new["samples"]} / {new["observations"]} |'
        )
    old = baseline['selection']['analyses']['ksat']['widest_cohort']['ranking'][0]
    new = analyses['ksat']['widest_cohort']['ranking'][0]
    lines.append(
        f'| Ksat: maximum coverage | `{old["function"]}` | `{new["function"]}` | {new["rmse"]:.6f} | {new["samples"]} / {new["observations"]} |'
    )
    lines.extend(
        [
            '',
            'Primary cohorts changed: the volumetric primary cohort now has 15 samples / 136 observations at approximately 10–50.1 kPa, versus 17 / 495 at 0.0605–257941 kPa before. The gravimetric primary has 10 / 30 versus 8 / 24 before. These RMSEs cannot be interpreted as before/after accuracy gains on identical data. Exact old-primary-cohort rescoring is retained in JSON separately. All maximal supports, compatible intersections, pairwise exact comparisons and wet/intermediate/dry metrics are retained. No global all-model intersection is required.',
            '',
            'The volumetric primary winner remains Varallyai chernozem B. The gravimetric primary winner changes to the Lal 1979 group-I sand discrete family on its stated cohort, while Chakraborty eq4 remains a candidate on other compatible cohorts. Ksat winners and their cohort-specific metrics are unchanged: no new Ksat function obtained valid independent inputs after the second pass. In particular, physical clay <10 µm and its complement do not supply an independent 2–50 µm silt fraction; zero-filled silt, assumed CEC, weather, gravel, conductivity coefficients and fitted WRC parameters were not invented.',
            '',
            '### Enlarged ensembles and robustness',
            '',
            '| Basis | Ensemble | Pooled RMSE | Change vs cohort-best atomic | Passes registered rule? |',
            '|---|---|---:|---:|---|',
        ]
    )
    for basis in BASES[:2]:
        analysis = analyses[basis]
        for name, score in analysis['ensembles'].items():
            conclusion = analysis['ensemble_conclusion'][name]
            lines.append(
                f'| {basis} | {name} | {score["rmse"]:.6f} | {conclusion["relative_rmse_change"]:+.2%} | {"Yes" if conclusion["meaningful_and_robust"] else "No"} |'
            )
    lines.extend(
        [
            '',
            'The previous primary mean RMSEs were 0.039503 (volume) and 0.065109 (mass), and no original ensemble passed robustness. On the enlarged primary volume cohort, top-3 and top-5 equal-weight means now pass: at least 1% pooled improvement and strictly lower RMSE in every required held-out evaluation against both the training-selected and pooled-best atomic comparators. The all-member mean, median and reduced pair do not pass. No mass ensemble passes. This is a changed, cohort-specific exploratory conclusion, not validation over the former full pressure range or evidence of population-level superiority. There are only two volumetric source folds; single-source mass assessment uses whole-sample out-of-bag bootstrap.',
            '',
            'The pooled top-5 mean is the lowest-RMSE passing ensemble on the primary volume cohort. Its membership, held-out reselected memberships, training-only top-N/reduced selection, residual-correlation matrices, effective member counts and selection frequencies are in the expanded selection JSON. Multiple model variants from one publication remain correlated candidates; effective member count is descriptive and does not create independent scientific evidence. All 18 WRC compatible cohorts were assessed separately; no claim is selected by comparing RMSEs across unequal cohorts.',
            '',
            '### Audit, limits and reproducibility',
            '',
            'Discrete families preserve publication, equation set and predictor variant; require at least three valid native pressure coordinates per sample; interpolate water content linearly in log10 pressure between positive endpoints only; never extrapolate. A zero-pressure prediction is used only at exact zero, never as a finite logarithmic anchor. Nonmonotone native family predictions are retained and flagged without smoothing. Secondary measured targets use exact observations or within-sample log-pressure reconstruction, with source observation IDs retained privately.',
            '',
            'Saxton 1986 and Vereecken detailed adapters were registered from encoded specifications. Saxton 2006 wet/dry inversions use independently predicted anchors from its base PTF, but unavailable valid predictors/support prevented additional scoring. Detailed Vereecken remains missing independently defined PSD descriptors and upper-tail fractions. Li 2007 and Wang 2022 WRC conventions require a user decision; zero residual or a specific m constraint is not guessed. Pidgeon AWC and Saxton salinity entries remain audited but are excluded as other physical targets. Weber remains blocked by independent VGM inputs and incomplete encoded Brunswick WRC semantics. Williams Table 5 remains missing the Northcote structure/field-texture group and saturation term.',
            '',
            'Actual same-record bulk density permits explicitly traced water-basis conversion for new predictions; original observations retain their basis. No measured target-water predictor, Rawls full-WRC conditional prediction, unrelated group-4 function or newly fitted PTF was introduced. Historical strict/frozen artifacts and the approximation fits are preserved. The previous final report is archived locally under `local/meta-expanded-benchmark/baseline/`; the sections above this expansion section describe that prior analysis.',
            '',
            'Artifacts: `expanded_selection.json`, `expanded_wrc_registry.json`, `expanded_function_audit.json`, `EXPANDED-FUNCTION-AUDIT.md`, updated `ptf_selection_summary.csv` and `point_target_summary.csv`. Private forecasts, native member predictions, predictor evidence, exact observation keys and failure examples remain under `local/meta-expanded-benchmark/`. PNGs and their updated index are under its `diagnostics/`, packaged as `ptfkit-expanded-diagnostics.zip`; existing approximation PNGs are copied byte for byte. The PPTX is unchanged.',
            '',
            'Reproduce from the repository root using the locked ptfkit-eval environment: run `expanded_participation`, then `expanded_selection`, then `publish_expanded_results`, each as `uv run --project targets/ptfkit-eval --no-sync python -B -m evaluation.experiments.meta_v3_3.<module>`; add `--with matplotlib` before `python` for the publishing module. Input workbook and previous replay forecasts are required. No approximation fitting is rerun.',
            '',
        ]
    )
    volume = analyses['volumetric_water_content']['primary']
    diversity = volume['ensemble_analysis']['diversity']
    matrix = diversity['residual_correlation_matrix']
    members = diversity['members']
    old_names = set(read(OUTPUT / 'scope.json')['previously_scored'])
    old_columns = [i for i, name in enumerate(members) if name in old_names]
    old_effective = len(old_columns) ** 2 / sum(
        matrix[i][j] ** 2 for i in old_columns for j in old_columns
    )
    lines.extend(
        [
            '',
            '### Contribution of new families to ensemble diversity',
            '',
            f'The primary volume pool has {len(members)} nominal models and effective residual member count {diversity["effective_member_count"]:.3f}; its old-model subset has {len(old_columns)} models and effective count {old_effective:.3f} on the same cohort. The two added Lal clay families have residual correlation 0.9866, so they add substantial redundancy rather than two independent error patterns.',
            '',
            'The passing pooled top-5 contains only the five previously scored Clapp/Varallyai models. Neither new Lal family is selected in top-3, top-5 or the reduced pair in either primary source fold. Consequently, this pass does **not** show that adding the new families caused the robust gain: the positive result occurs with an additional top-N strategy on the narrower exact cohort. The all-member mean including Lal is worse there. Detailed matrices and membership frequencies for every compatible cohort remain in JSON.',
            '',
        ]
    )
    original_report = (OUTPUT / 'baseline/FINAL-RESULTS.md').read_text(encoding='utf-8')
    original_report = original_report.replace(
        '# ptfkit benchmark results\n',
        '# ptfkit benchmark results\n\n**Current PTF selection:** see [Expanded PTF participation](#expanded-ptf-participation). Earlier selection sections retain the pre-expansion comparison; the approximation analysis is unchanged.\n',
        1,
    )
    (PUBLIC / 'FINAL-RESULTS.md').write_text(
        original_report.rstrip() + '\n\n' + '\n'.join(lines), encoding='utf-8'
    )
    audit_lines = [
        '# Expanded function audit',
        '',
        'Every one of the 119 functions in the three requested groups is retained below. Point-only scores are secondary; registry membership alone does not count as a full-WRC contribution. Failure counts are failed resolutions/attempts and may overlap; they are not independent sample counts.',
        '',
        '| Function | New dispositions | Reason | Scored candidates |',
        '|---|---|---|---|',
    ]
    audit_lines.extend(
        f'| `{r["function"]}` | {", ".join(r["dispositions"])} | {r["reason"]} | {", ".join(r["scored_candidates"])} |'
        for r in decisions
    )
    audit_lines.extend(
        [
            '',
            'Exact failure counts, previous disposition, point counts and scientific family membership are in `expanded_function_audit.json`. Native evaluation examples, predictor-unit checks and the all-sheet alias re-audit stay in private local storage. Functions outside the three groups and Rawls full-WRC were not reconsidered.',
            '',
        ]
    )
    (PUBLIC / 'EXPANDED-FUNCTION-AUDIT.md').write_text('\n'.join(audit_lines), encoding='utf-8')
    historical = (OUTPUT / 'baseline/NONPARTICIPATING-FUNCTIONS.md').read_text(encoding='utf-8')
    (PUBLIC / 'NONPARTICIPATING-FUNCTIONS.md').write_text(
        '> Historical pre-expansion inventory. Current dispositions for the 119 reconsidered functions are in [EXPANDED-FUNCTION-AUDIT.md](EXPANDED-FUNCTION-AUDIT.md); the current participation counts are in [FINAL-RESULTS.md](FINAL-RESULTS.md#expanded-ptf-participation).\n\n'
        + historical,
        encoding='utf-8',
    )


def point_target_tables(secondary: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for point in secondary:
        groups[point['basis'], point['pressure_kpa'], point['function']].append(point)
    rows = []
    for (basis, pressure, fid), points in sorted(groups.items()):
        rows.append(
            {
                'target': basis,
                'native_pressure_kpa': pressure,
                'function': fid,
                'cohort': 'maximum_function_point_support',
                'route_type': 'point_target',
                **original.scored(points),
            }
        )
    return rows


def update_methodology(analyses: dict) -> None:
    original_text = (OUTPUT / 'baseline/ENSEMBLE-METHODOLOGY.md').read_text(encoding='utf-8-sig')
    # Preserve the user's requested Russian methodology and explicitly label the
    # earlier roster/results instead of silently presenting them as current.
    volume = analyses['volumetric_water_content']['primary']
    mass = analyses['gravimetric_water_content']['primary']
    text = '# Расширенный ансамблевый анализ\n\n'
    text += 'После расширения roster ансамбли пересчитаны на каждой точной совместимой когорте. Полный средний и медианный ансамбли используют всех совместимых участников; top-2, top-3 и top-5 — лучшие модели по обучающей части. Сокращённая пара выбирается по обучающей RMSE и корреляции остатков <0.95 среди первой пятёрки, иначе используются две лучшие модели. Состав заново определяется внутри каждого разбиения; отложенные значения не участвуют в выборе. Для bootstrap ранжирование учитывает кратность обучающих образцов, а корреляции — уникальные обучающие точки.\n\n'
    text += 'Веса во всех средних равны; пропуски исключены через точное пересечение наблюдений. Измеренная влажность как predictor запрещена. Варианты одной публикации могут быть сильно коррелированы: для каждой когорты сохранены матрица корреляций, эффективное число участников `(trace(R))² / sum(R²)` и частоты выбора по разбиениям. Неопределённые корреляции постоянных остатков отдельно отмечены и не считаются нулевой зависимостью.\n\n'
    for basis, cohort in (('Объёмная влажность', volume), ('Массовая влажность', mass)):
        assessment = cohort['ensemble_analysis']
        text += f'**{basis}:** {cohort["samples"]} образцов, {cohort["observations"]} наблюдений; поддержка {cohort["pressure_range_kpa"][0]:.6g}–{cohort["pressure_range_kpa"][1]:.6g} кПа.\n\n'
        text += '| Ансамбль | RMSE | Устойчивое улучшение |\n|---|---:|---|\n'
        for name, score in assessment['ensembles'].items():
            text += f'| {name} | {score["rmse"]:.6f} | {"Да" if assessment["ensemble_conclusion"][name]["meaningful_and_robust"] else "Нет"} |\n'
        text += '\nСоставы на полной когорте:\n\n'
        for name, score in assessment['ensembles'].items():
            text += f'- {name}: ' + ', '.join(f'`{f}`' for f in score['members']) + '.\n'
        text += '\n'
    text += 'Критерий сохранён: минимум 1% снижения pooled RMSE и строго меньшая ошибка во всех доступных отложенных проверках относительно обоих эталонов — лучшей модели на обучении и лучшей модели полной когорты. Top-3 и top-5 теперь проходят критерий на новой основной объёмной когорте; полный mean, median и reduced — нет. Для массовой влажности ни один ансамбль не проходит. Это результат для узкой поддержки примерно 10–50 кПа и двух источников, а не для всей прежней ОГХ. Различные когорты нельзя ранжировать по RMSE напрямую. Новые полные данные reduced и top-N остаются описательными; вложенные held-out результаты и частоты состава сохранены в JSON.\n\n'
    text += 'Прошедший критерий top-5 содержит только прежние пять моделей Clapp/Varallyai. Новые Lal-семейства не выбираются в top-3, top-5 или reduced ни в одном основном source fold. Следовательно, улучшение не доказывает пользу новых семей: оно получено для дополнительной top-N стратегии и более узкой когорты. Корреляция остатков двух новых Lal-семейств здесь составляет 0.9866; семь номинальных моделей дают эффективное число участников 2.272.\n\n'
    text += (
        'Текущая реализация: `expanded_selection.py`. Результаты: `expanded_selection.json`; сравнение с прежними выводами: раздел `Expanded PTF participation` в `FINAL-RESULTS.md`.\n\n---\n\n## Метод и результаты до расширения\n\n'
        + original_text.removeprefix('# Метод построения ансамблей\n').lstrip()
    )
    (PUBLIC / 'ENSEMBLE-METHODOLOGY.md').write_text(text, encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--reuse-images',
        action='store_true',
        help='Refresh reports and packaging while retaining rendered PNGs.',
    )
    args = parser.parse_args()
    analyses = read(OUTPUT / 'analyses.json')
    points = read(OUTPUT / 'predictions.json')
    secondary = read(OUTPUT / 'point-target-predictions.json')
    metadata = read(OUTPUT / 'candidate-metadata.json')
    registered = read(OUTPUT / 'family-adapter-registry.json')
    registered['unresolved'] = routes.UNRESOLVED
    json_write(OUTPUT / 'family-adapter-registry.json', registered)
    json_write(PUBLIC / 'expanded_wrc_registry.json', registered)
    decisions, stats = participation_audit(points, analyses, metadata, registered, secondary)
    baseline = read(OUTPUT / 'baseline/benchmark_aggregates.json')
    old_cohort_comparisons = {}
    for basis in BASES:
        old = read(ROOT / 'local/meta-diagnostic-replay/analyses.json')[basis]['primary']
        keys = set(old['keys'])
        indices = defaultdict(dict)
        for p in points:
            if p['basis'] == basis:
                indices[p['function']][p['id']] = p
        members = sorted(f for f, index in indices.items() if keys <= index.keys())
        old_cohort_comparisons[basis] = {
            'ranking': original.rank(indices, members, sorted(keys), ksat=basis == 'ksat'),
            'samples': old['samples'],
            'observations': old['observations'],
        }
    public = compact_public(
        original.public_summary(
            {
                'analyses': analyses,
                'participation': stats,
                'candidate_metadata': metadata,
                'old_primary_exact_cohort_comparisons': old_cohort_comparisons,
                'policy': {
                    'id': 'expanded_participation_E5_v1',
                    'scope': 'Only the specified 64+17+38 formerly excluded functions; baseline forecasts retained.',
                    'ensembles': ['mean', 'median', 'reduced', 'top_2', 'top_3', 'top_5'],
                    'robustness': original.POLICY['meaningful_ensemble_improvement'],
                    'bootstrap_seed': 20261026,
                    'bootstrap_draws': 500,
                    'no_ksat_ensemble': True,
                },
                'baseline_aggregate_sha256': hashlib.sha256(
                    (OUTPUT / 'baseline/benchmark_aggregates.json').read_bytes()
                ).hexdigest(),
                'implementation_sha256': {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in Path(__file__).parent.glob('*.py')
                },
                'private_analysis_sha256': hashlib.sha256(
                    (OUTPUT / 'analyses.json').read_bytes()
                ).hexdigest(),
            }
        )
    )
    json_write(PUBLIC / 'expanded_selection.json', public)
    json_write(
        PUBLIC / 'expanded_function_audit.json', {'participation': stats, 'functions': decisions}
    )
    # Preserve the historical selection field and approximation section; expose
    # the new result as an explicit separate version within the final aggregates.
    json_write(PUBLIC / 'benchmark_aggregates.json', {**baseline, 'expanded_selection': public})
    selection_rows = []
    for basis in BASES:
        analysis = analyses[basis]
        for cohort in analysis['compatible_cohorts']:
            for score in cohort['ranking']:
                selection_rows.append(
                    {
                        'target': basis,
                        'cohort': cohort['cohort_id'],
                        'kind': 'atomic',
                        'model': score['function'],
                        'route_type': metadata[score['function']]['route_type']
                        if basis != 'ksat'
                        else 'Ksat',
                        'metric_unit': 'log10_ratio'
                        if basis == 'ksat'
                        else 'm3/m3'
                        if basis.startswith('volumetric')
                        else 'kg/kg',
                        'rmse': score['rmse'],
                        'mae': score['mae'],
                        'bias': score['bias'],
                        'samples': score['samples'],
                        'observations': score['observations'],
                        'primary': cohort['cohort_id'] == analysis['primary']['cohort_id'],
                        'pressure_min_kpa': score['pressure_range_kpa'][0]
                        if score['pressure_range_kpa']
                        else None,
                        'pressure_max_kpa': score['pressure_range_kpa'][1]
                        if score['pressure_range_kpa']
                        else None,
                        'within_factor_2': score.get('factor_2'),
                        'within_factor_5': score.get('factor_5'),
                        'within_factor_10': score.get('factor_10'),
                    }
                )
            for kind, score in cohort.get('ensembles', {}).items():
                selection_rows.append(
                    {
                        **selection_rows[-1],
                        'kind': 'ensemble',
                        'model': kind,
                        'route_type': 'equal_weight_ensemble',
                        **{k: score[k] for k in ('rmse', 'mae', 'bias', 'samples', 'observations')},
                    }
                )
    write_csv(PUBLIC / 'ptf_selection_summary.csv', selection_rows)
    point_summary = point_target_tables(secondary)
    # Nested inventory fields remain in JSON; CSV contains the scalar metrics.
    write_csv(
        PUBLIC / 'point_target_summary.csv',
        [{k: v for k, v in r.items() if not isinstance(v, (dict, list))} for r in point_summary],
    )
    point_comparisons = []
    grouped = defaultdict(list)
    for p in secondary:
        grouped[p['basis'], p['pressure_kpa']].append(p)
    for (basis, pressure), group in sorted(grouped.items()):
        indices = defaultdict(dict)
        for p in group:
            indices[p['function']][p['id']] = p
        pairs = []
        from itertools import combinations  # noqa: PLC0415 - Local secondary comparison utility.

        for left, right in combinations(sorted(indices), 2):
            shared = sorted(set(indices[left]) & set(indices[right]))
            if shared:
                pairs.append(
                    {
                        'members': [left, right],
                        'ranking': original.rank(indices, [left, right], shared),
                    }
                )
        point_comparisons.append(
            {
                'basis': basis,
                'pressure_kpa': pressure,
                'maximal_metrics': {
                    f: original.scored(list(i.values())) for f, i in indices.items()
                },
                'pairwise': pairs,
            }
        )
    json_write(
        PUBLIC / 'point_target_selection.json',
        original.public_summary(
            {
                'groups': point_comparisons,
                'summary': point_summary,
                'interpretation': 'Secondary native-pressure comparisons, not full-WRC rankings.',
            }
        ),
    )
    report(analyses, stats, decisions, metadata)
    update_methodology(analyses)
    diagnostics(points, analyses, secondary, metadata, reuse_images=args.reuse_images)
    print(json.dumps(stats, indent=2), flush=True)  # noqa: T201 - Command result.


def compact_public(value: object) -> object:
    """Keep bootstrap draw details private; retain all aggregate selection evidence."""
    if isinstance(value, dict):
        result = {
            k: compact_public(v)
            for k, v in value.items()
            if not (k == 'folds' and value.get('dimension') == 'sample_bootstrap')
        }
        if value.get('dimension') == 'sample_bootstrap' and 'folds' in value:
            result['fold_count'] = len(value['folds'])
            result['fold_details'] = (
                'Private local/meta-expanded-benchmark/analyses.json; frequencies and held-out summaries retained here.'
            )
        return result
    if isinstance(value, list):
        return [compact_public(v) for v in value]
    return value


def diagnostics(
    points: list[dict],
    analyses: dict,
    secondary: list[dict],
    metadata: dict,
    *,
    reuse_images: bool = False,
) -> None:
    destination = OUTPUT / 'diagnostics'
    destination.mkdir(exist_ok=True)
    render.OUTPUT = destination
    if reuse_images:
        with (destination / 'diagnostic_index.csv').open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
    else:
        rows = render.ptf_plots(points, analyses)
        for row in rows:
            row['route_type'] = (
                metadata[row['function_or_family']]['route_type']
                if row['target'] != 'ksat'
                else 'Ksat'
            )
    for (basis, pressure, fid), group in [] if reuse_images else sorted_grouped_points(secondary):
        score = original.scored(group)
        folder, unit, label = render.basis_info(basis)
        cohort = f'native_{pressure:.12g}_kpa_maximum_function_support'
        annotation = (
            textwrap.fill(fid, 42)
            + '\n\nRoute: point_target (secondary)\n'
            + f'Pressure: {pressure:.8g} kPa\nWater basis: {label.lower()}\nSamples: {score["samples"]}\nObservations: {score["observations"]}\nRMSE: {score["rmse"]:.6f}\nMAE: {score["mae"]:.6f}\nBias: {score["bias"]:+.6f}\n\nObserved target: exact or\nwithin-sample log-pressure\nreconstruction; no extrapolation\n\nCohort: '
            + textwrap.fill(cohort, 40)
        )
        fig, ax = render.canvas(
            'Measured vs predicted — secondary point target\n' + fid.removeprefix('calc_ptf_'),
            annotation,
        )
        render.scatter(ax, group, f'water content ({unit})')
        fig.text(
            0.09,
            0.035,
            'Secondary point-target result; compare only identical pressure / basis / sample cohorts.',
            fontsize=8.5,
        )
        path = render.save(
            fig,
            Path('PTF/point_targets')
            / folder
            / f'{fid.removeprefix("calc_ptf_")}_{pressure:.8g}kpa.png',
        )
        rows.append(
            {
                **render.index_row('PTF', basis + '_point_target', fid, cohort, score, path),
                'route_type': 'point_target',
            }
        )
    old = ROOT / 'local/meta-final-benchmark/diagnostics'
    shutil.copytree(old / 'APPROXIMATION', destination / 'APPROXIMATION', dirs_exist_ok=True)
    if not reuse_images:
        with (old / 'diagnostic_index.csv').open(encoding='utf-8', newline='') as stream:
            rows.extend(
                {**r, 'route_type': 'fitted_approximation'}
                for r in csv.DictReader(stream)
                if r['category'] == 'APPROXIMATION'
            )
    write_csv(destination / 'diagnostic_index.csv', rows)
    for name in (
        'ENSEMBLE-METHODOLOGY.md',
        'EXPANDED-FUNCTION-AUDIT.md',
        'expanded_function_audit.json',
        'expanded_wrc_registry.json',
    ):
        shutil.copyfile(PUBLIC / name, destination / name)
    readme = """# Expanded ptfkit diagnostics

`PTF/` contains independent predictions from the enlarged WRC/Ksat roster.
Route types, exact cohort IDs, sample/point counts and metrics appear on each plot.
`PTF/point_targets/` is a separate secondary benchmark at native pressures.
Its measured targets are exact or reconstructed within the same measured curve
by log-pressure interpolation, without extrapolation. It never enters full-WRC
ranking or ensembles. WRC metrics give each sample equal weight. Do not compare
errors across different pressure supports, cohorts or water bases.

Ksat uses m/s on logarithmic axes. Dashed ×2, ×5 and ×10 bands enclose predictions
between measured/factor and measured*factor; fractions and block counts are
annotated. Its error metrics use log10(predicted/measured).

`APPROXIMATION/` is copied byte for byte from the prior package: these parameters
were fitted to the displayed measurements and are not independent PTF predictions.
Overview metrics are medians of sample metrics. Per-sample images have four index
rows sharing one path; dashed curves labelled relaxed only failed strict acceptance.
Zero pressure uses the explicitly annotated display coordinate on logarithmic plots.

`diagnostic_index.csv` covers all PNGs with paths relative to this directory.
See EXPANDED-FUNCTION-AUDIT.md and the expansion section of FINAL-RESULTS.md for
scope, physical ambiguities and changed conclusions. Full model/parameter/source
provenance and individual predictions remain in private local storage. The Russian
ENSEMBLE-METHODOLOGY.md distinguishes current results from the original benchmark.
No conditional Rawls curve, fitted WRC input or unrelated target enters scoring.
"""
    (destination / 'README.md').write_text(readme, encoding='utf-8')
    paths = {r['file_path'] for r in rows}
    if paths != {p.relative_to(destination).as_posix() for p in destination.rglob('*.png')}:
        message = 'Expanded PNG inventory and diagnostic index differ.'
        raise ValueError(message)
    with ZipFile(
        OUTPUT / 'ptfkit-expanded-diagnostics.zip', 'w', compression=ZIP_DEFLATED
    ) as archive:
        for path in sorted(destination.rglob('*')):
            if path.is_file():
                archive.write(
                    path, (Path('diagnostics') / path.relative_to(destination)).as_posix()
                )


def sorted_grouped_points(secondary: list[dict]) -> list[tuple]:
    groups = defaultdict(list)
    for point in secondary:
        groups[point['basis'], point['pressure_kpa'], point['function']].append(point)
    return sorted(groups.items())


if __name__ == '__main__':
    main()
