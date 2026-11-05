"""Predictor-level contract resolution for registered harmonized evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .eligibility import assess_computational_domain
from .harmonization import EvidenceTier, EvidenceValue, convert_evidence


if TYPE_CHECKING:
    from collections.abc import Mapping


def resolve_harmonized_input(  # noqa: C901 - Independent physical-contract rejection reasons.
    binding: dict,
    evidence: EvidenceValue,
    measurement: dict,
    *,
    manifest: Mapping[str, object] | None = None,
) -> tuple[EvidenceValue | None, tuple[str, ...]]:
    """Resolve one predictor without requiring metadata for unrelated columns.

    Transformations do not authorize a change of material, denominator, method,
    particle boundaries or conditions. A null required method imposes no method
    restriction, matching the existing strict contract convention.
    """
    expected = binding.get('measurement')
    if not expected:
        return None, ('missing_predictor_measurement_contract',)
    reasons = [
        f'predictor_{key}_mismatch'
        for key in ('quantity', 'basis', 'particle_size')
        if measurement.get(key) != expected.get(key)
    ]
    basis = measurement.get('basis') or {}
    if not basis.get('material') or not basis.get('denominator') or 'unspecified' in basis.values():
        reasons.append('unresolved_predictor_basis')
    if expected.get('method') and measurement.get('method') != expected['method']:
        reasons.append('predictor_method_mismatch')
    if measurement.get('conditions', []) != expected.get('conditions', []):
        reasons.append('predictor_conditions_mismatch')
    if evidence.tier == EvidenceTier.UNSUPPORTED:
        reasons.append('unsupported_predictor')
    if not measurement.get('unit'):
        reasons.append('missing_predictor_unit')
    if not isinstance(evidence.value, (int, float)):
        reasons.append('nonnumeric_predictor')
    if reasons:
        return None, tuple(reasons)
    try:
        resolved = convert_evidence(
            evidence, measurement['unit'], expected['unit'], manifest=manifest
        )
    except ValueError:
        return None, ('predictor_unit_mismatch',)
    if not isinstance(resolved.value, (int, float)):
        return None, ('nonnumeric_predictor',)
    domain = assess_computational_domain(resolved.value, expected)
    if not domain.within:
        return None, ('predictor_computational_domain',)
    return resolved, ()
