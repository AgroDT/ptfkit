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
from .quality import diagnose_retention_run


if TYPE_CHECKING:
    from .runner import RetentionRunResult


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
    {'curve-quality.json', 'selection.json', 'approximations.json', 'prediction-intervals.json'}
)


def artifact_value(value: object) -> object:
    """Serialize immutable domain records without deepcopying read-only mappings."""
    if is_dataclass(value) and not isinstance(value, type):
        record = {field.name: artifact_value(getattr(value, field.name)) for field in fields(value)}
        for name in ('status', 'eligible'):
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
    if result.selection is not None:
        payloads['selection.json'] = canonical_json(artifact_value(result.selection))
    if result.approximations:
        payloads['approximations.json'] = canonical_json(artifact_value(result.approximations))
    if result.prediction_intervals:
        payloads['prediction-intervals.json'] = canonical_json(
            artifact_value(result.prediction_intervals)
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
