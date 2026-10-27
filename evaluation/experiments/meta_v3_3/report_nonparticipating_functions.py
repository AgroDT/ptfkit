"""Describe catalog functions absent from independent final PTF scoring."""

# ruff: noqa: INP001, E501, C901, RUF001 - Standalone scientific audit tables.

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


OUTPUT = Path(__file__).parent / 'final_results'


def main() -> None:
    selection = json.loads((OUTPUT / 'benchmark_aggregates.json').read_bytes())['selection']
    bases = ('volumetric_water_content', 'gravimetric_water_content', 'ksat')
    included = set().union(*(set(selection['analyses'][b]['coverage']) for b in bases))
    catalog = selection['catalog']
    groups = defaultdict(list)
    for record in catalog:
        if record['function'] in included:
            continue
        if record['executions']:
            group = 'conditional'
        elif record['wrc_targets'] or record['ksat_targets']:
            group = 'blocked'
        else:
            group = record['wrc_disposition']
        groups[group].append(record)
    excluded = {r['function'] for records in groups.values() for r in records}
    if len(excluded) + len(included) != len(catalog) or excluded & included:
        message = 'Excluded and included rosters must partition the catalog.'
        raise ValueError(message)
    lines = [
        '# Functions not included in independent final PTF scoring',
        '',
        'This inventory documents the existing final benchmark without rerunning selection or changing its conclusions. “Not included” means absent from all three independent scored coverage rosters: volumetric WRC, gravimetric WRC and Ksat. It does not mean scientifically inferior, unimplemented, or absent from ptfkit.',
        '',
        f'The audit examined **{len(catalog)} catalog functions**. **{len(included)} distinct functions participated**, representing 59 function/target combinations (13 volumetric WRC, 3 gravimetric WRC and 43 Ksat); one function appears under two targets. **{len(excluded)} functions did not participate** in independent scoring. Functions scored on smaller compatible cohorts still count as participants, even when absent from the primary cohort or final recommendations.',
        '',
        '| Reason group | Functions |',
        '|---|---:|',
        f'| Isolated pressure outputs without an eligible full-WRC route | {len(groups["isolated_pressure_outputs_not_full_WRC"])} |',
        f'| No operational WRC/Ksat target in this benchmark | {len(groups["not_WRC_output"])} |',
        f'| WRC definition or adapter unresolved, without an executable alternative | {len(groups["curve_definition_or_adapter_unresolved"])} |',
        f'| Executable target available, but no valid predictions obtained | {len(groups["blocked"])} |',
        f'| Measured-water inputs required; conditional analysis only | {len(groups["conditional"])} |',
        '',
        'The scope is the executable catalog recorded in `selection.catalog`, not every function mentioned in publications or blocked YAML specifications. Reasons below are recorded implementation dispositions and execution failures, not a new scientific applicability review.',
        '',
        '## Measured-water-conditioned predictions',
        '',
        '`calc_ptf_rawls1982_full_wrc` produced 24 volumetric predictions, but required water-content predictors (`theta_33` and `theta_1500`) reconstructed from the same sample’s measured retention data. These were kept in the separate `volumetric_water_content_water_conditioned` analysis, whose status is `no_comparable_multi_pressure_cohort`. They were not mixed with independent PTF predictions or included in their diagnostic figures. This is not an execution failure.',
        '',
        '## Executable targets without valid predictions',
        '',
        'Each row lists **all recorded failure codes and counts**. `missing_predictor:X` means that the existing resolver could not supply an admissible value of X from that sample’s evidence; it does not assert that X is absent everywhere in the workbook. Counts refer to failed resolutions or rejected attempted coordinates. Several reasons can apply to one coordinate, and early checks can prevent later checks; counts must not be summed as independent sample or observation totals.',
        '',
        '`different_water_basis` rejects incompatible mass/volume targets without silently converting them. `computational_domain:X` rejects an input outside the executable contract. `pressure_outside_declared_domain` rejects unsupported pressure inputs. `native_domain_or_curve_support_failure` records a caught native evaluation/domain or curve-support error; the stored audit does not resolve it further. `nonpositive_or_nonfinite_prediction` rejects nonfinite outputs and nonpositive Ksat values required for log scoring.',
        '',
        '| Function | Eligible target route | Recorded failures (count) |',
        '|---|---|---|',
    ]
    for record in sorted(groups['blocked'], key=lambda r: r['function']):
        targets = []
        if record['wrc_targets']:
            targets.append(
                'WRC: ' + ', '.join(sorted({t['quantity'] for t in record['wrc_targets']}))
            )
        if record['ksat_targets']:
            targets.append('Ksat')
        failures = '; '.join(
            f'`{code}` ({count})' for code, count in sorted(record['failure_counts'].items())
        )
        lines.append(
            f'| `{record["function"]}` | {"; ".join(targets)} | {failures or "No recorded failure detail"} |'
        )
    for group, title, explanation in (
        (
            'isolated_pressure_outputs_not_full_WRC',
            'Isolated pressure outputs',
            'The final WRC benchmark required a continuous curve adapter or at least three distinct registered fixed-pressure outputs, with linear interpolation in log10 pressure only between positive supported endpoints and no extrapolation. These functions had the recorded disposition `isolated_pressure_outputs_not_full_WRC` and no executable Ksat alternative. This scope decision does not invalidate isolated FC/PWP/AWC predictions for their own targets.',
        ),
        (
            'curve_definition_or_adapter_unresolved',
            'Unresolved WRC definitions or adapters',
            'These functions were classified as full-WRC or retention-parameter candidates, but the final registry exposed no executable observed-pressure WRC route and no alternative Ksat route. The code `curve_definition_or_adapter_unresolved` does not distinguish an unresolved model convention from a missing implementation adapter; no more specific cause is inferred.',
        ),
        (
            'not_WRC_output',
            'No operational WRC or Ksat target',
            'The target registry exposed neither an eligible WRC comparison nor a Ksat comparison for these functions. Their recorded WRC disposition is `not_WRC_output`. Declared scientific output families below show what the functions do provide; “no target” refers to this benchmark, not to the absence of a valid output.',
        ),
    ):
        lines.extend(
            [
                '',
                f'## {title}',
                '',
                explanation,
                '',
                '| Function | Declared output families |',
                '|---|---|',
            ]
        )
        for record in sorted(groups[group], key=lambda r: r['function']):
            families = '; '.join(record['declared_families']) or 'Not classified in the audit'
            lines.append(f'| `{record["function"]}` | {families} |')
    lines.extend(
        [
            '',
            '## Evidence and reproduction',
            '',
            'Source: [`benchmark_aggregates.json`](benchmark_aggregates.json), `selection.catalog` and the independent `selection.analyses.*.coverage` rosters. The diagnostic replay’s complete decisions matched this catalog exactly, and its forecasts reproduced all published selection analyses exactly. Candidate gating and execution reasons are implemented in [`model_selection.py`](../model_selection.py), particularly `candidate_targets`, `predict` and `analyze`.',
            '',
            'Regenerate from the repository root with `uv run --project targets/ptfkit-eval --no-sync python -B -m evaluation.experiments.meta_v3_3.report_nonparticipating_functions`. No private sample identifiers are included.',
            '',
        ]
    )
    (OUTPUT / 'NONPARTICIPATING-FUNCTIONS.md').write_text('\n'.join(lines), encoding='utf-8')
    print(  # noqa: T201 - Command result.
        f'Documented {len(excluded)} excluded functions; {len(included)} participating functions.',
        flush=True,
    )


if __name__ == '__main__':
    main()
