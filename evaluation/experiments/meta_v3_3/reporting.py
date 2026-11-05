"""Render the workbook benchmark's existing result records as Markdown tables."""

# ruff: noqa: INP001 - Standalone experiment helpers.

from __future__ import annotations

from pathlib import Path


def render_report(summary: dict) -> str:
    """Keep displayed numbers tied to their machine-readable summary fields."""
    sources = [
        f'| {row["source_id"]} | {row.get("reviewed_profile_count", "unresolved")} | '
        f'{row["normalized_samples"]} | {row["normalized_observations"]} | '
        f'{row["review_status"]} | {", ".join(row["blockers"]) or "see evidence"} |'
        for row in summary['sources']
    ]
    functions = []
    for row in summary['functions']:
        reasons = '; '.join(f'{r}: {n}' for r, n in row['reason_counts_by_sample_target'].items())
        functions.append(
            f'| {row["function"]} | {row["eligible_samples"]} | {row["evaluated_samples"]} | '
            f'{row["blocked_samples"]} | {reasons} |'
        )
    performance = []
    for cohort in summary['class_comparison']['cohorts']:
        value = cohort['cohort']['summary']
        metrics = value['metrics']
        performance.append(
            f'| Panina reviewed / {cohort["kind"]} | {cohort["candidate_id"]} | '
            f'{value["sample_count"]} | '
            f'{value["point_count"]} | see candidate coverage | '
            f'{metrics["root_mean_squared_error"]:.9f} | '
            f'{metrics["mean_absolute_error"]:.9f} | {metrics["mean_error"]:.9f} | '
            'insufficient_evidence: one profile |'
        )
    fits = [
        f'| {row["family"]} | {row["fit_attempts"]} | {row["accepted_fits"]} | '
        f'{row["rejected_fits"]} | {row["accepted_rmse_range"]} | '
        f'{row["rejection_reasons"]} |'
        for row in summary['approximations']['families']
    ]
    regions = []
    for row in summary['pressure_diagnostics']['regions']:
        value = row['summary']
        if value is None:
            regions.append(
                f'| {row["region"]} | 0 | 0 | not estimated | not estimated | not estimated |'
            )
        else:
            metrics = value['metrics']
            regions.append(
                f'| {row["region"]} | {value["sample_count"]} | {value["point_count"]} | '
                f'{metrics["root_mean_squared_error"]:.9f} | '
                f'{metrics["mean_absolute_error"]:.9f} | {metrics["mean_error"]:.9f} |'
            )
    blockers = []
    for rank, row in enumerate(summary['remaining_blockers'], 1):
        reasons = ', '.join(row['blockers']) or '; '.join(row['exclusion_reasons'])
        blockers.append(
            f'{rank}. `{row["source_id"]}`: '
            f'{row["excluded_observations"]} excluded rows; {reasons}.'
        )
    result = (
        Path(__file__)
        .with_name('report-template.md')
        .read_text(encoding='utf-8')
        .format(
            sources='\n'.join(sources),
            functions='\n'.join(functions),
            performance='\n'.join(performance),
            fits='\n'.join(fits),
            regions='\n'.join(regions),
            blockers='\n'.join(blockers),
            coverage_counts=str(summary['blocker_impact']['coverage']),
            impact='\n'.join(
                f'| {r["blocker"]} | {r["affected_rows"]} | {r["affected_functions"]} | '
                f'{r["blocked_combinations"]} | <= {r["potential_gain_upper_bound"]}; '
                f'sole gap: {r["sole_blocker_combinations"]} |'
                for r in summary['blocker_impact']['ranked_blockers']
            ),
            source_priority='\n'.join(
                f'| {r["source_id"]} | {r["affected_rows"]} | {r["affected_functions"]} | '
                f'<= {r["potential_combinations_upper_bound"]} |'
                for r in summary['blocker_impact']['ranked_source_reviews']
            ),
            predictor_priority='\n'.join(
                f'| {r["function"]} | {", ".join(r["required_predictors"])} | '
                f'{r["potential_compatible_rows"]} | {r["main_blocker"]} | '
                f'{r["expected_unlock_cost"]}: {r["unresolved_claim_count"]} claim types |'
                for r in summary['function_priorities']
            ),
            priority_audit='\n'.join(
                f'| {r["raw_source"]} | {r["master_row_count"]} | {r["exact_id_count"]} | '
                f'{r["ordered_vector_match_count"]} | {r["released_observation_count"]} | '
                f'{", ".join(r["remaining_claims"])} |'
                for r in summary['priority_source_audit']
            ),
            scope_counts=(
                f'{summary["workbook_scope"]["sheet_count"]} worksheets; '
                f'{summary["workbook_scope"]["populated_row_count"]} populated rows. '
                f'Dispositions: `{summary["workbook_scope"]["status_counts"]}`.'
            ),
            unreviewed_sources='\n'.join(
                f'| {r["raw_source"]} | {r["row_count"]} | unresolved |'
                for r in summary['workbook_scope']['unreviewed_master_sources']
            ),
        )
    )
    if 'function_audit' in summary:
        result += (
            '\n## Catalog coverage and ensemble value\n\n'
            'See [the complete 146-function audit](function-audit.md) for predictor definitions, '
            'scientific and implementation co-blockers, input families and source unlock ceilings. '
            'The audit separates coverage, atomic performance and ensemble value.\n'
        )
    return result
