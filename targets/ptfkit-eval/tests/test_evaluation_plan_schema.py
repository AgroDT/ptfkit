import json
from importlib.resources import files
from typing import Protocol

import pytest
from jsonschema import Draft202012Validator


class Validator(Protocol):
    def validate(self, instance: object) -> None:
        """Validate an instance or raise a schema error."""

    def is_valid(self, instance: object) -> bool:
        """Return whether an instance conforms to the schema."""


def _candidate() -> dict[str, object]:
    return {
        'id': 'wet_dry_composite',
        'kind': 'range_gated_curve',
        'axis': {
            'quantity': 'matric_potential',
            'unit': 'kilopascal',
            'convention': 'magnitude',
            'transform': 'log10',
        },
        'target': {
            'quantity': 'volumetric_water_content',
            'unit': 'volume_fraction',
            'material_basis': 'fine_earth',
            'denominator_basis': 'bulk_volume',
        },
        'members': [
            {
                'id': 'wet',
                'function': 'calc_ptf_example_wet',
                'prediction': {'kind': 'model_adapter', 'id': 'example_wet_h_theta'},
                'interval': {
                    'lower': {'value': 0.1, 'inclusive': True},
                    'upper': {'value': 33.0, 'inclusive': True},
                },
            },
            {
                'id': 'dry',
                'function': 'calc_ptf_example_dry',
                'prediction': {'kind': 'model_adapter', 'id': 'example_dry_h_theta'},
                'interval': {
                    'lower': {'value': 10.0, 'inclusive': True},
                    'upper': {'value': 1500.0, 'inclusive': True},
                },
            },
        ],
        'routing': {
            'gap': 'reject',
            'extrapolation': 'reject',
            'transitions': [
                {
                    'kind': 'blend',
                    'left_member': 'wet',
                    'right_member': 'dry',
                    'interval': {
                        'lower': {'value': 10.0, 'inclusive': True},
                        'upper': {'value': 33.0, 'inclusive': True},
                    },
                    'weighting': 'smoothstep',
                }
            ],
        },
        'provenance': {'kind': 'fixed', 'source': 'Pre-registered evaluation plan.'},
    }


@pytest.fixture
def validator() -> Validator:
    resource = files('ptfkit_eval').joinpath('schemas/evaluation-plan.schema.json')
    schema = json.loads(resource.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_accepts_a_pre_registered_range_gated_curve(validator: Validator):
    plan = {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [_candidate()],
    }

    validator.validate(plan)


def test_accepts_an_atomic_function_curve_as_a_peer_candidate(validator: Validator):
    plan = {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': 'atomic_retention',
                'kind': 'function_curve',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'log10',
                },
                'target': {
                    'quantity': 'volumetric_water_content',
                    'unit': 'volume_fraction',
                    'material_basis': 'fine_earth',
                    'denominator_basis': 'bulk_volume',
                },
                'function': 'calc_ptf_example',
                'prediction': {'kind': 'model_adapter', 'id': 'example_h_theta'},
            }
        ],
    }

    validator.validate(plan)


def test_leaves_overlap_completeness_to_manifest_aware_validation(validator: Validator):
    candidate = _candidate()
    routing = candidate['routing']
    assert isinstance(routing, dict)
    routing['transitions'] = []
    plan = {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [candidate],
    }

    validator.validate(plan)


def test_learned_routing_requires_a_training_protocol(validator: Validator):
    candidate = _candidate()
    candidate['provenance'] = {'kind': 'learned', 'source': 'Dataset-specific calibration.'}
    plan = {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [candidate],
    }

    assert not validator.is_valid(plan)
