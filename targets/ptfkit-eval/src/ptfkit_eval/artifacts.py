"""Deterministic, integrity-checked artifacts for fixed retention evaluation runs."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
from collections import Counter
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from importlib import import_module
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from .documents import EvaluationDocumentError, canonical_json, document_hash, object_mapping, plain
from .hard_switch import HardSwitchGridFit
from .quality import diagnose_retention_run


if TYPE_CHECKING:
    from .nested_applicability import NestedApplicabilityResult
    from .runner import RetentionRunResult
    from .strategy_assessment import OuterStrategySummary


_RUN_FILES = frozenset(
    {
        'run-plan.json',
        'source-run-plan.json',
        'evaluation-plan.json',
        'dataset.json',
        'ptfkit-manifest.json',
        'point-decisions.json',
        'sample-eligibility.json',
        'cohorts.json',
        'coverage.json',
        'report.md',
    }
)
_OPTIONAL_RUN_FILES = frozenset(
    {
        'curve-quality.json',
        'selection.json',
        'approximations.json',
        'prediction-intervals.json',
        'empirical-domains.json',
        'composite-seams.json',
        'nested-applicability.json',
        'paired-comparisons.json',
        'learned-selection.json',
        'learned-applicability.json',
        'learned-seams.json',
        'selection-curve-quality.json',
        'strategy-assessment.json',
        'selection-resampling.json',
        'conditional-outer-risk.json',
    }
)


def artifact_value(value: object) -> object:
    """Serialize immutable domain records without deepcopying read-only mappings."""
    if is_dataclass(value) and not isinstance(value, type):
        record = {field.name: artifact_value(getattr(value, field.name)) for field in fields(value)}
        for name in (
            'status',
            'eligible',
            'partition',
            'total_sample_count',
            'eligible_loss_sample_count',
            'complete_replicate_count',
        ):
            if hasattr(value, name):
                record[name] = artifact_value(getattr(value, name))
        return record
    if isinstance(value, Mapping):
        return {key: artifact_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [artifact_value(item) for item in value]
    return plain(value)


def write_retention_run(result: RetentionRunResult, destination: str | Path) -> Path:
    """Publish a complete run directory without overwriting an existing run."""
    target = Path(destination)
    if target.exists() or target.is_symlink():
        message = f'Run output already exists: {target}.'
        raise FileExistsError(message)
    payloads = _payloads(result)
    environment = {
        'python': platform.python_version(),
        'packages': {
            name: version(name)
            for name in (
                'ptfkit-eval',
                'ptfkit',
                'numpy',
                'scipy',
                'jsonschema',
                'openpyxl',
                'pyyaml',
            )
        },
        'git': _git_state(),
        'evaluator_source_sha256': _source_hash(),
        'ptfkit_package_sha256': _source_hash(Path(import_module('ptfkit').__file__).parent),
    }
    manifest = {
        'schema_version': 1,
        'run_kind': 'synthetic_validation'
        if result.plan.dataset.document['kind'] == 'synthetic'
        else 'external_validation',
        'dataset_id': result.plan.dataset.dataset_id,
        'protocol_id': object_mapping(result.plan.document['protocol'])['id'],
        'input_hashes': result.plan.input_hashes,
        'environment': environment,
        'files': {
            name: {'sha256': hashlib.sha256(contents).hexdigest(), 'bytes': len(contents)}
            for name, contents in sorted(payloads.items())
        },
    }
    manifest['run_id'] = document_hash(manifest)
    payloads['run-manifest.json'] = canonical_json(manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=f'.{target.name}.', dir=target.parent) as temporary:
        staging = Path(temporary) / 'run'
        staging.mkdir()
        for name, contents in payloads.items():
            (staging / name).write_bytes(contents)
        if target.exists() or target.is_symlink():
            message = f'Run output appeared during publication: {target}.'
            raise FileExistsError(message)
        staging.rename(target)
    return target


def read_retention_run_report(source: str | Path) -> str:
    """Verify every retained artifact before returning a persisted report."""
    directory = Path(source)
    try:
        manifest = object_mapping(json.loads((directory / 'run-manifest.json').read_text('utf-8')))
        if manifest.get('schema_version') != 1:
            message = 'Unsupported retention run artifact version.'
            raise EvaluationDocumentError(message)
        files = object_mapping(manifest['files'])
        if not set(files) >= _RUN_FILES or set(files) - _RUN_FILES - _OPTIONAL_RUN_FILES:
            message = 'Run manifest does not list the exact required artifact set.'
            raise EvaluationDocumentError(message)
        unsigned = {key: value for key, value in manifest.items() if key != 'run_id'}
        if manifest['run_id'] != document_hash(unsigned):
            message = 'Run manifest content hash does not match its run identifier.'
            raise EvaluationDocumentError(message)
        for name, metadata in files.items():
            path = directory / name
            if path.is_symlink():
                message = 'Run artifacts must be regular files, not symbolic links.'
                raise EvaluationDocumentError(message)
            contents = path.read_bytes()
            expected = object_mapping(metadata)
            if (
                hashlib.sha256(contents).hexdigest() != expected['sha256']
                or len(contents) != expected['bytes']
            ):
                message = f'Run artifact checksum mismatch: {name}.'
                raise EvaluationDocumentError(message)
        return (directory / 'report.md').read_text('utf-8')
    except (OSError, UnicodeError, ValueError, KeyError) as error:
        if isinstance(error, EvaluationDocumentError):
            raise
        message = f'Cannot verify retention run directory {directory}.'
        raise EvaluationDocumentError(message) from error


def _payloads(result: RetentionRunResult) -> dict[str, bytes]:
    documents = {
        'source-run-plan.json': result.plan.document,
        'evaluation-plan.json': result.plan.evaluation_document,
        'dataset.json': result.plan.dataset.document,
        'ptfkit-manifest.json': result.plan.manifest,
        'point-decisions.json': artifact_value(result.points),
        'sample-eligibility.json': artifact_value(result.sample_eligibility),
        'cohorts.json': artifact_value(result.cohorts),
        'coverage.json': _coverage(result),
        'curve-quality.json': artifact_value(diagnose_retention_run(result)),
    }
    payloads = {name: canonical_json(document) for name, document in documents.items()}
    optional = {
        'selection.json': result.selection,
        'approximations.json': result.approximations,
        'prediction-intervals.json': result.prediction_intervals,
        'empirical-domains.json': result.empirical_domains,
        'composite-seams.json': result.seam_diagnostics,
        'nested-applicability.json': result.nested_applicability,
        'paired-comparisons.json': result.paired_comparisons,
        'learned-selection.json': result.learned_selection,
        'learned-applicability.json': result.learned_applicability,
        'learned-seams.json': result.learned_seams,
        'selection-curve-quality.json': result.selection_quality,
        'strategy-assessment.json': result.strategy_assessments,
        'selection-resampling.json': result.selection_resampling,
        'conditional-outer-risk.json': result.conditional_outer_risk,
    }
    payloads.update(
        {name: canonical_json(artifact_value(value)) for name, value in optional.items() if value}
    )
    portable = dict(result.plan.document)
    for field, name in (('evaluation_plan', 'evaluation-plan.json'), ('dataset', 'dataset.json')):
        portable[field] = {'path': name, 'sha256': hashlib.sha256(payloads[name]).hexdigest()}
    payloads['run-plan.json'] = canonical_json(portable)
    payloads['report.md'] = _report(result).encode('utf-8')
    return payloads


def _coverage(result: RetentionRunResult) -> dict[str, object]:
    candidates = []
    for candidate in sorted(result.plan.evaluation.candidates, key=lambda item: item.id):
        points = [point for point in result.points if point.candidate_id == candidate.id]
        samples = [
            sample for sample in result.sample_eligibility if sample.candidate_id == candidate.id
        ]
        reasons = Counter(reason for point in points for reason in point.reasons)
        candidates.append(
            {
                'candidate_id': candidate.id,
                'candidate_sample_count': len(samples),
                'eligible_sample_count': sum(sample.eligible_point_count > 0 for sample in samples),
                'observation_count': len(points),
                'eligible_point_count': sum(point.eligible for point in points),
                'excluded_point_count': sum(not point.eligible for point in points),
                'exclusion_reason_counts': dict(sorted(reasons.items())),
            }
        )
    findings = Counter(
        f'{curve.kind}.{diagnostic.code}'
        for curve in diagnose_retention_run(result)
        for diagnostic in curve.quality.diagnostics
    )
    return {
        'schema_version': 1,
        'candidates': candidates,
        'curve_quality_finding_counts': dict(sorted(findings.items())),
    }


def _report(result: RetentionRunResult) -> str:
    synthetic = result.plan.dataset.document['kind'] == 'synthetic'
    lines = [
        '# ptfkit-eval retention evaluation',
        '',
        f'Dataset: `{result.plan.dataset.dataset_id}`.',
        f'Protocol: `{object_mapping(result.plan.document["protocol"])["id"]}`.',
        '',
        'Synthetic validation; these results are not external predictive accuracy evidence.'
        if synthetic
        else 'Fixed-candidate external validation under the declared eligibility protocol.',
        '',
        (
            'Errors use prediction minus observation, volume fractions, '
            'and equal total weight per sample.'
        ),
        'Intervals are cluster-percentile confidence intervals for aggregate metrics.',
        'Optional uncertainty protocols report their own assumptions and evidence status.',
        '',
        '| Candidate | Cohort | Samples | Points | ME | MAE | RMSE | Median AE | CI status |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |',
    ]
    interval_lines: list[str] = []
    for item in result.cohorts:
        cohort = item.cohort
        summary = cohort.summary
        values = (
            ['n/a'] * 4
            if summary is None
            else [
                f'{value:.8g}'
                for value in (
                    summary.metrics.mean_error,
                    summary.metrics.mean_absolute_error,
                    summary.metrics.root_mean_squared_error,
                    summary.metrics.median_absolute_error,
                )
            ]
        )
        samples, points = (0, 0) if summary is None else (summary.sample_count, summary.point_count)
        status = item.confidence.reason or item.confidence.status
        lines.append(
            f'| {cohort.candidate_id} | {cohort.kind} | {samples} | {points} | '
            + ' | '.join(values)
            + f' | {status} |'
        )
        if item.confidence.intervals is not None:
            interval_lines.extend(
                [
                    '',
                    (
                        f'{cohort.candidate_id}, {cohort.kind}: '
                        f'{result.plan.bootstrap.confidence_level:.1%} metric confidence intervals '
                        f'({item.confidence.effective_grouping}, '
                        f'{item.confidence.group_count} groups).'
                    ),
                ]
            )
            for name in (
                'mean_error',
                'mean_absolute_error',
                'root_mean_squared_error',
                'median_absolute_error',
            ):
                interval = getattr(item.confidence.intervals, name)
                interval_lines.append(f'- {name}: [{interval.lower:.8g}, {interval.upper:.8g}]')
            interval_lines.append('')
    lines.extend(interval_lines)
    lines.extend(_input_diagnostics_report(result))
    lines.extend(
        _nested_applicability_report(
            result.nested_applicability, title='Nested input-domain diagnostics'
        )
    )
    lines.extend(
        _nested_applicability_report(
            result.learned_applicability, title='Learned selection input-domain diagnostics'
        )
    )
    lines.extend(_paired_comparison_report(result))
    lines.extend(_learned_selection_report(result))
    lines.extend(_learned_seam_report(result))
    lines.extend(_selection_quality_report(result))
    lines.extend(_strategy_assessment_report(result))
    lines.extend(_selection_resampling_report(result))
    lines.extend(_conditional_risk_report(result))
    if result.prediction_intervals:
        lines.extend(
            [
                '',
                '## PTF prediction intervals',
                '',
                'Whole-group split-conformal calibration uses disjoint registered roles.',
                'Coverage interpretation assumes exchangeable whole groups and a fixed grid/rule.',
                ('These prediction intervals differ from aggregate-metric confidence intervals.'),
                '',
            ]
        )
        lines.extend(
            f'- {item.calibration.plan.candidate_id}: {item.status}; '
            f'calibration={item.calibration.reason or item.calibration.status}; '
            f'groups={len(item.calibration.scores)}; '
            f'test forecasts={len(item.forecasts)}.'
            for item in result.prediction_intervals
        )
    if result.approximations:
        lines.extend(
            [
                '',
                '## Reference approximation fits',
                '',
                (
                    'Approximation error and conditional fit uncertainty '
                    'are separate from PTF prediction error.'
                ),
                (
                    'Parameter and curve intervals assume local linearity '
                    'and iid homoscedastic residuals.'
                ),
                (
                    'Conditional prediction intervals concern future observations '
                    'under the fitted family.'
                ),
                '',
                '| Family | Accepted | Failed |',
                '| --- | ---: | ---: |',
            ]
        )
        family_ids = sorted({item.fit.plan.family_id for item in result.approximations})
        for family in family_ids:
            family_fits = [
                item.fit for item in result.approximations if item.fit.plan.family_id == family
            ]
            accepted = sum(fit.status == 'fitted' for fit in family_fits)
            lines.append(f'| {family} | {accepted} | {len(family_fits) - accepted} |')
    if result.selection is not None:
        lines.extend(
            [
                '',
                '## Nested fixed-candidate selection',
                '',
                'Choices use inner validation only; outer errors assess locked strategies.',
                'No final function is chosen by sorting outer test errors.',
                '',
            ]
        )
        if not result.selection.protocols:
            lines.append(f'Insufficient evidence: {result.selection.splits.reason}.')
        lines.extend(
            f'- {assessment.kind}: {assessment.status}; '
            f'outer loss={assessment.mean_outer_loss}; '
            f'coverage={assessment.eligible_sample_count}/{assessment.total_sample_count}; '
            f'selections={assessment.selected_counts}.'
            for assessment in result.selection.protocols
        )
    lines.extend(
        [
            '',
            '## Coverage and exclusions',
            '',
            '```json',
            canonical_json(_coverage(result)).decode('utf-8').rstrip(),
            '```',
            '',
        ]
    )
    return '\n'.join(lines)


def _source_hash(root: Path | None = None) -> str:
    root = Path(__file__).parent if root is None else root
    digest = hashlib.sha256()
    paths = [
        path
        for path in root.rglob('*')
        if path.is_file() and path.suffix in ('.py', '.json', '.pyd', '.so', '.dll')
    ]
    for path in sorted(paths):
        digest.update(path.relative_to(root).as_posix().encode('utf-8'))
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


def _git_state() -> dict[str, object]:
    executable = shutil.which('git')
    if executable is None:
        return {'revision': None, 'dirty': None}
    try:
        revision = _run_git(executable, ['rev-parse', 'HEAD']).strip()
        status = _run_git(executable, ['status', '--porcelain', '--untracked-files=normal'])
    except (OSError, subprocess.SubprocessError):
        return {'revision': None, 'dirty': None}
    return {'revision': revision, 'dirty': bool(status)}


def _run_git(executable: str, arguments: list[str]) -> str:
    return subprocess.run(  # noqa: S603 - Fixed read-only Git commands; no shell interpolation.
        [executable, *arguments],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    ).stdout


def _input_diagnostics_report(result: RetentionRunResult) -> list[str]:
    lines: list[str] = []
    if result.empirical_domains:
        lines.extend(
            [
                '',
                '## Empirical input domains',
                '',
                'Envelopes use complete training inputs only, with inclusive numeric bounds.',
                'Inside means marginal input support, not joint support or predictive accuracy.',
                'These diagnostics do not alter scoring or nested selection.',
                '',
            ]
        )
        for domain in result.empirical_domains:
            for member in domain.members:
                counts = dict(
                    sorted(Counter(sample.status for sample in member.test_samples).items())
                )
                lines.append(
                    f'- {domain.plan.candidate_id}/{member.member_id}: '
                    f'{member.reason or member.status}; '
                    f'training groups={member.training_group_count}; '
                    f'test inputs={counts}.'
                )
    if result.seam_diagnostics:
        lines.extend(
            [
                '',
                '## Composite transition diagnostics',
                '',
                'Exact right-minus-left member contrasts use predictors only.',
                'Hard-switch contrasts imply jumps only for members continuous at the switch.',
                'Blend endpoint contrasts describe member disagreement, not blended-curve jumps.',
                '',
                '| Candidate | Source/sample | Boundary | kPa | Right minus left | Status |',
                '| --- | --- | --- | ---: | ---: | --- |',
            ]
        )
        lines.extend(
            f'| {item.candidate_id} | {item.source_id}/{item.sample_id} | {item.kind} | '
            f'{item.suction_kpa:.8g} | {item.right_minus_left} | {item.status} |'
            for item in result.seam_diagnostics
        )
    return lines


def _nested_applicability_report(
    assessment: NestedApplicabilityResult | None, *, title: str
) -> list[str]:
    if assessment is None:
        return []
    lines = [
        '',
        f'## {title}',
        '',
        'Each envelope uses only the corresponding inner/outer training predictors.',
        'Sample labels require support from all registered composite members.',
        'Error strata use the selection roster common cohort; labels never choose candidates.',
        'Metric confidence intervals condition on the retained folds and envelopes.',
        'They do not repeat training or selection. Registered loss means have no intervals here.',
        '',
    ]
    if assessment.reason is not None:
        return [*lines, f'Insufficient evidence: {assessment.reason}.', '']
    lines.extend(
        [
            (
                '| Outer | Inner | Candidate | Stratum | Samples | Loss eligible | '
                'Mean log-pressure loss | RMSE | Metric CI |'
            ),
            '| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- |',
        ]
    )
    for fold in assessment.folds:
        for stratum in fold.strata:
            if not stratum.samples:
                continue
            summary = stratum.confidence.summary
            rmse = 'n/a' if summary is None else f'{summary.metrics.root_mean_squared_error:.8g}'
            inner = 'outer test' if fold.inner_fold_id is None else str(fold.inner_fold_id)
            lines.append(
                f'| {fold.outer_fold_id} | {inner} | {fold.domain.plan.candidate_id} | '
                f'{stratum.status} | {stratum.total_sample_count} | '
                f'{stratum.eligible_loss_sample_count} | {stratum.mean_log_pressure_loss} | '
                f'{rmse} | {stratum.confidence.reason or stratum.confidence.status} |'
            )
    return [*lines, '']


def _paired_comparison_report(result: RetentionRunResult) -> list[str]:
    if not result.paired_comparisons:
        return []
    lines = [
        '',
        '## Paired candidate differences',
        '',
        'Every difference is left minus right on the exact run-wide common cohort.',
        'Both candidates use the same whole-cluster bootstrap draws.',
        'Intervals are unadjusted descriptive comparisons, not a selection procedure.',
        'Negative MAE/RMSE/median differences favor the left candidate on this cohort.',
        'Signed mean-error differences are bias contrasts, not an accuracy ordering.',
        '',
        '| Left | Right | Metric | Difference | Confidence interval | Status |',
        '| --- | --- | --- | ---: | --- | --- |',
    ]
    for comparison in result.paired_comparisons:
        for metric in (
            'mean_error',
            'mean_absolute_error',
            'root_mean_squared_error',
            'median_absolute_error',
        ):
            difference = (
                getattr(comparison.differences, metric)
                if comparison.differences is not None
                else 'n/a'
            )
            interval = (
                getattr(comparison.intervals, metric) if comparison.intervals is not None else None
            )
            bounds = f'[{interval.lower:.8g}, {interval.upper:.8g}]' if interval else 'n/a'
            lines.append(
                f'| {comparison.left.candidate_id} | {comparison.right.candidate_id} | {metric} | '
                f'{difference} | {bounds} | {comparison.reason or comparison.status} |'
            )
    return [*lines, '']


def _learned_selection_report(result: RetentionRunResult) -> list[str]:
    selection = result.learned_selection
    if selection is None:
        return []
    lines = [
        '',
        (
            '## Nested convex ensemble selection'
            if selection.plan.method == 'nested_convex_pair_selection_v1'
            else '## Nested two-curve ensemble selection'
        ),
        '',
        'Each inner fit uses training groups only; inner validation locks the candidate.',
        'The selected ensemble is refitted on all outer training groups before outer testing.',
        'Learned parameters follow the registered constant-weight or finite-grid switch protocol.',
        'Weight/boundary uncertainty and full selection-process intervals are not estimated.',
        'Outer errors do not choose a final function or ensemble.',
        '',
    ]
    if selection.splits.reason is not None:
        return [*lines, f'Insufficient evidence: {selection.splits.reason}.', '']
    lines.extend(
        f'- {item.kind}: {item.status}; mean outer loss={item.mean_outer_loss}; '
        f'coverage={item.eligible_sample_count}/{item.total_sample_count}; '
        f'selections={item.selected_counts}.'
        for item in selection.protocols
    )
    for fold in selection.folds:
        ensemble = fold.ensemble
        if ensemble.outer_fit is not None:
            fitted_parameter = (
                f'switch kPa={ensemble.outer_fit.switch_suction_kpa}'
                if isinstance(ensemble.outer_fit, HardSwitchGridFit)
                else f'left weight={ensemble.outer_fit.left_weight}'
            )
            lines.append(
                f'- Outer fold {fold.fold_id}, {ensemble.candidate_id}: '
                f'{fitted_parameter}; '
                f'refit={ensemble.outer_fit.reason or ensemble.outer_fit.status}.'
            )
    return [*lines, '']


def _learned_seam_report(result: RetentionRunResult) -> list[str]:
    if not result.learned_seams:
        return []
    lines = [
        '',
        '## Fitted hard-switch diagnostics',
        '',
        'Member contrasts use only test predictors at the already locked outer-training seam.',
        'A contrast implies a jump only for member curves continuous at the boundary.',
        'These diagnostics do not refit boundaries or change candidate selection.',
        '',
        '| Outer | Candidate | Source/sample | kPa | Right minus left | Status |',
        '| ---: | --- | --- | ---: | ---: | --- |',
    ]
    lines.extend(
        f'| {seam.outer_fold_id} | {seam.candidate_id} | '
        f'{seam.left.source_id}/{seam.left.sample_id} | {seam.suction_kpa:.8g} | '
        f'{seam.right_minus_left} | {seam.status} |'
        for seam in result.learned_seams
    )
    return [*lines, '']


def _selection_quality_report(result: RetentionRunResult) -> list[str]:
    if not result.selection_quality:
        return []
    lines = [
        '',
        '## Held-out curve physical diagnostics',
        '',
        'Bounds and monotonicity findings never repair predictions or change selection.',
        (
            'Counts describe frame/sample records; '
            'repeated inner holdouts are not independent replicates.'
        ),
        'No-prediction records remain separate from diagnosed curves without findings.',
        '',
        '| Protocol | Partition | Strategy | Diagnosed | No predictions | Bounds | Increases |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: |',
    ]
    scopes = sorted(
        {(item.protocol, item.partition, item.strategy) for item in result.selection_quality}
    )
    for protocol, partition, strategy in scopes:
        curves = [
            item
            for item in result.selection_quality
            if (item.protocol, item.partition, item.strategy) == (protocol, partition, strategy)
        ]
        findings = Counter(
            finding.code for curve in curves for finding in curve.quality.diagnostics
        )
        lines.append(
            f'| {protocol} | {partition} | {strategy} | '
            f'{sum(curve.status == "diagnosed" for curve in curves)} | '
            f'{sum(curve.status == "no_predictions" for curve in curves)} | '
            f'{findings["water_outside_physical_bounds"]} | '
            f'{findings["increasing_water_with_suction"]} |'
        )
    return [*lines, '']


def _strategy_assessment_report(result: RetentionRunResult) -> list[str]:
    if not result.strategy_assessments:
        return []
    lines = [
        '',
        '## Locked outer strategy descriptive assessment',
        '',
        (
            'Only untouched outer predictions inside the registered selection-loss domain '
            'enter these metrics.'
        ),
        (
            'Strategies may choose different candidates in different folds; '
            'no final model is selected here.'
        ),
        'Partial rows remain descriptive; failed folds prevent a complete strategy result.',
        (
            'Confidence intervals are not estimated because overlapping training sets '
            'and selection are not resampled.'
        ),
        '',
        (
            '| Protocol | Strategy | Cohort | Samples | Points | '
            'ME | MAE | RMSE | Median AE | Status |'
        ),
        '| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |',
    ]
    for assessment in result.strategy_assessments:
        summaries: dict[str, OuterStrategySummary] = {
            item.strategy: item for item in assessment.strategies
        }
        for cohort in (*assessment.cohorts.maximal, *assessment.cohorts.common):
            summary = cohort.summary
            values = (
                ['n/a'] * 4
                if summary is None
                else [
                    f'{value:.8g}'
                    for value in (
                        summary.metrics.mean_error,
                        summary.metrics.mean_absolute_error,
                        summary.metrics.root_mean_squared_error,
                        summary.metrics.median_absolute_error,
                    )
                ]
            )
            strategy = summaries[cohort.candidate_id]
            samples, points = (
                (0, 0) if summary is None else (summary.sample_count, summary.point_count)
            )
            lines.append(
                f'| {assessment.protocol} | {cohort.candidate_id} | {cohort.kind} | '
                f'{samples} | {points} | '
                + ' | '.join(values)
                + f' | {strategy.reason or strategy.status} |'
            )
        lines.append(
            f'{assessment.protocol}: {assessment.reason or assessment.status}; '
            f'uncertainty={assessment.uncertainty_status}.'
        )
        lines.extend(
            f'- {assessment.protocol}.{strategy.strategy}: loss coverage='
            f'{strategy.eligible_loss_sample_count}/{strategy.total_sample_count}; '
            f'failed folds={strategy.failed_fold_count}; '
            f'outside-domain rows={strategy.excluded_pressure_point_count}; '
            f'selections={strategy.selected_counts}.'
            for strategy in assessment.strategies
        )
        difference = assessment.atomic_minus_ensemble
        if difference is not None:
            lines.append(
                f'{assessment.protocol}, common cohort, atomic minus ensemble: '
                f'MAE={difference.mean_absolute_error:.8g}, '
                f'RMSE={difference.root_mean_squared_error:.8g}; descriptive, no interval.'
            )
    return [*lines, '']


def _selection_resampling_report(result: RetentionRunResult) -> list[str]:
    if not result.selection_resampling:
        return []
    lines = [
        '',
        '## Whole-group selection retraining sensitivity',
        '',
        'Original source/profile identities keep every copy of a group in the same fold.',
        (
            'Every draw repeats selection and ensemble fitting; '
            'failed draws are retained, not retried.'
        ),
        'These trajectories are sensitivity evidence, not confidence or prediction intervals.',
        '',
    ]
    lines.extend(
        f'- {item.plan.protocol}: {item.reason or item.status}; grouping={item.grouping}; '
        f'original groups={len(item.original_groups)}; requested draws={item.plan.n_resamples}; '
        f'accounted draws={len(item.replicates)}; complete draws={item.complete_replicate_count}; '
        f'uncertainty={item.uncertainty_status}.'
        for item in result.selection_resampling
    )
    return [*lines, '']


def _conditional_risk_report(result: RetentionRunResult) -> list[str]:
    if not result.conditional_outer_risk:
        return []
    lines = [
        '',
        '## Conditional outer-rule risk bounds',
        '',
        'Target: equal-fold mean conditional sample risk of locked outer rules.',
        (
            'These are not intervals for observed CV error, '
            'training-law average risk or a final all-data model.'
        ),
        (
            'Coverage assumes the declared IID population, '
            'value-independent partition and prior bounds.'
        ),
        (
            'Failed policies remain in the simultaneous family; '
            'no success-conditioned reallocation applies.'
        ),
        '',
    ]
    for item in result.conditional_outer_risk:
        plan = item.policy.bounds
        interval = item.bound.equal_fold_mean_risk_interval if item.bound is not None else None
        limits = (
            f'[{interval.lower:.6g}, {interval.upper:.6g}]'
            if interval is not None
            else 'unavailable'
        )
        lines.append(
            f'- {item.policy.protocol}/{item.policy.strategy}: {item.reason or item.status}; '
            f'interval={limits}; family confidence={plan.confidence_level!r}; '
            f'family size={item.family_size}; '
            f'allocated error={item.allocated_error_probability:.6g}; '
            f'population={plan.population_id}; grouping={plan.grouping}; '
            f'group size=[{plan.minimum_group_size}, {plan.maximum_group_size}]; '
            f'loss bound={plan.maximum_sample_loss:.6g}; '
            f'loss domain=[{plan.loss.lower_suction_kpa:g}, '
            f'{plan.loss.upper_suction_kpa:g}] kPa.'
        )
        lines.extend(
            f'  - Outer fold {failure.fold_id}: {failure.reason}.' for failure in item.fold_failures
        )
    return [*lines, '']
