use std::collections::BTreeMap;

use crate::{
    model::{CompiledFunction, Function, GoldenInput, Outputs, PythonGeneration},
    output::GeneratedFile,
};

use super::{WRAPPER_HEADER, natural_sort_key, syntax::Module};

pub(super) fn render(functions: &[CompiledFunction]) -> Vec<GeneratedFile> {
    let mut modules: BTreeMap<String, Vec<&CompiledFunction>> = BTreeMap::new();
    for function in functions {
        modules
            .entry(function.entry.slug.clone())
            .or_default()
            .push(function);
    }

    let mut files = vec![
        GeneratedFile::new("tests/_helpers.py".into(), helper_source()),
        GeneratedFile::new("tests/test_comparator.py".into(), comparator_test_source()),
    ];
    files.extend(
        modules
            .into_iter()
            .filter_map(|(slug, functions)| {
                (functions[0].entry.spec.generation.public_python == PythonGeneration::Generated)
                    .then(|| {
                        GeneratedFile::new(
                            format!("tests/test_{slug}.py").into(),
                            module_source(&slug, &functions),
                        )
                    })
            })
            .collect::<Vec<_>>(),
    );
    files
}

fn comparator_test_source() -> String {
    format!(
        r#"{WRAPPER_HEADER}
import pytest

from _helpers import assert_close, resolved_tolerance


@pytest.mark.parametrize('expected', [0.0, 2.0, -2.0])
def test_accepts_below_and_rejects_above_tolerance(expected: float):
    absolute = 0.001
    relative = 0.01
    tolerance = resolved_tolerance(expected, absolute, relative)
    metadata = {{
        'absolute': absolute,
        'relative': relative,
        'quantity': 'test_quantity',
        'unit': '1',
        'source': 'registry',
    }}
    assert_close(expected + tolerance * 0.5, expected, **metadata)
    with pytest.raises(AssertionError):
        assert_close(expected + tolerance * 2.0, expected, **metadata)
"#
    )
}

fn helper_source() -> String {
    format!(
        r#"{WRAPPER_HEADER}
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, TypeVar, overload

import numpy as np

from ptfkit.enums import EnumArray


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

    R = TypeVar('R', bound=NamedTuple)
    Expected = dict[str, float]
    VerificationCase = tuple[Mapping[str, Any], Expected]
    VectorCasePart = tuple[dict[str, Any], Expected]
    VectorCaseScalar = tuple[*VectorCasePart, np.ndarray]
    VectorCaseTuple = tuple[*VectorCasePart, R]


@overload
def prepare_vector_case(cases: Sequence[VerificationCase]) -> VectorCaseScalar: ...


@overload
def prepare_vector_case(
    cases: Sequence[VerificationCase], result_type: type[R]
) -> VectorCaseTuple: ...


def prepare_vector_case(
    cases: Sequence[VerificationCase],
    result_cls: type[R] | None = None,
) -> VectorCaseScalar | VectorCaseTuple:
    inputs, expected = cases[0]
    vector_inputs = {{
        name: (
            EnumArray._from_members(type(value), [value])  # noqa: SLF001
            if isinstance(value, Enum)
            else np.array([value])
        )
        for name, value in inputs.items()
    }}
    out: np.ndarray | R
    if result_cls is None:
        out = np.empty(1, dtype=float)
    else:
        field_count = len(result_cls._fields)
        out = result_cls(*(np.empty(1, dtype=float) for _ in range(field_count)))
    return vector_inputs, expected, out


def assert_close(
    actual: object,
    expected: float,
    *,
    absolute: float,
    relative: float,
    quantity: str,
    unit: str,
    source: str,
) -> None:
    actual_float = float(actual)  # ty: ignore[invalid-argument-type]
    tolerance = resolved_tolerance(expected, absolute, relative)
    difference = abs(actual_float - expected)
    assert difference <= tolerance, (
        f'actual={{actual_float}}, expected={{expected}}, difference={{difference}}, '
        f'tolerance={{tolerance}}, quantity={{quantity!r}}, unit={{unit!r}}, source={{source}}'
    )


def resolved_tolerance(expected: float, absolute: float, relative: float) -> float:
    scientific_tolerance = max(absolute, relative * abs(expected))
    return max(scientific_tolerance, {:?})
"#,
        crate::compile::FLOATING_POINT_GUARD
    )
}

fn module_source(slug: &str, functions: &[&CompiledFunction]) -> String {
    let mut imports = Vec::new();
    for resolved in functions {
        let function = &resolved.entry.spec.functions[resolved.function_index];
        imports.push(function.public_api.name.as_str());
        if let Some(result_class) = function.result_class() {
            imports.push(result_class);
        }
        for input in &function.inputs {
            if let Some(enum_type) = input.enum_type() {
                imports.push(&enum_type.name);
            }
        }
    }
    imports.sort_by_key(|name| natural_sort_key(name));
    imports.dedup();
    let mut module = Module::new(WRAPPER_HEADER);
    module.line("\nfrom __future__ import annotations");
    module.blank_line();
    module.line("import pytest");
    module.blank_line();
    module.import("_helpers", "assert_close, prepare_vector_case");
    module.import(&format!("ptfkit.{slug}"), imports.join(", "));
    module.blank_line();
    module.blank_line();
    for (index, resolved) in functions.iter().enumerate() {
        if index > 0 {
            module.blank_line();
            module.blank_line();
        }
        function_source(&mut module, resolved);
    }
    module.into_string()
}

fn function_source(module: &mut Module, resolved: &CompiledFunction) {
    let function = &resolved.entry.spec.functions[resolved.function_index];
    let cases_name = format!("CASES_{}", function.public_api.name.to_ascii_uppercase());
    module.assignment(&cases_name, "[");
    module.indented(|writer| {
        for (case, compiled) in function
            .verification_cases
            .iter()
            .zip(&resolved.verification_cases)
        {
            writer.line(format_args!(
                "({}, {}),",
                dictionary(&case.inputs, function),
                expected_dictionary(function, &compiled.expected),
            ));
        }
    });
    module.line("]");
    module.blank_line();
    module.blank_line();
    let name = &function.public_api.name;
    let input_value_type = if function
        .inputs
        .iter()
        .any(|input| input.enum_type().is_some())
    {
        "object"
    } else {
        "float"
    };
    module.line(format_args!(
        "@pytest.mark.parametrize(('inputs', 'expected'), {cases_name})"
    ));
    module.line(format_args!(
        "def test_{name}_verification(inputs: dict[str, {input_value_type}], expected: dict[str, float]):"
    ));
    module.indented(|writer| {
        if function
            .inputs
            .iter()
            .any(|input| input.enum_type().is_some())
        {
            writer.line(format_args!(
                "result = {name}(**inputs)  # ty: ignore[no-matching-overload]"
            ));
        } else {
            writer.line(format_args!("result = {name}(**inputs)"));
        }
        writer.blank_line();
        render_expected_assertion(writer, resolved, "");
    });
    if !function.verification_cases.is_empty() {
        vector_test_source(module, resolved, &cases_name);
    }
}

fn vector_test_source(module: &mut Module, resolved: &CompiledFunction, cases_name: &str) {
    let function = &resolved.entry.spec.functions[resolved.function_index];
    let result_cls = function
        .result_class()
        .map(|result_class| format!(", {result_class}"))
        .unwrap_or_default();
    let name = &function.public_api.name;
    module.blank_line();
    module.blank_line();
    module.line(format_args!("def test_{name}_array():"));
    module.indented(|writer| {
        writer.line(format_args!(
            "inputs, expected, _out = prepare_vector_case({cases_name}{result_cls})"
        ));
        writer.line(format_args!("result = {name}(**inputs, out=None)"));
        render_expected_assertion(writer, resolved, "[0]");
    });
    module.blank_line();
    module.blank_line();
    module.line(format_args!("def test_{name}_out():"));
    module.indented(|writer| {
        writer.line(format_args!(
            "inputs, expected, out = prepare_vector_case({cases_name}{result_cls})"
        ));
        writer.line(format_args!("result = {name}(**inputs, out=out)"));
        render_out_assertion(writer, function);
        render_expected_assertion(writer, resolved, "[0]");
    });
}

fn render_expected_assertion(
    writer: &mut crate::render::Writer,
    resolved: &CompiledFunction,
    index: &str,
) {
    let function = &resolved.entry.spec.functions[resolved.function_index];
    match &function.outputs {
        Outputs::Scalar { field } => writer.line(assertion(
            &format!("result{index}"),
            field.name.as_str(),
            &resolved.output_tolerances[0],
        )),
        Outputs::Record { fields, .. } => {
            for (field, tolerance) in fields.iter().zip(&resolved.output_tolerances) {
                writer.line(assertion(
                    &format!("result.{}{index}", field.name),
                    field.name.as_str(),
                    tolerance,
                ));
            }
        }
    }
}

fn assertion(actual: &str, field: &str, tolerance: &crate::model::CompiledTolerance) -> String {
    let source = match &tolerance.source {
        crate::model::ToleranceSource::Registry => "registry".to_owned(),
        crate::model::ToleranceSource::SourceOverride(location) => {
            format!("source override: {location}")
        }
    };
    format!(
        "assert_close({actual}, expected['{field}'], absolute={}, relative={}, quantity={:?}, unit={:?}, source={:?})",
        float(tolerance.absolute),
        float(tolerance.relative),
        tolerance.quantity,
        tolerance.unit,
        source,
    )
}

fn render_out_assertion(writer: &mut crate::render::Writer, function: &Function) {
    match &function.outputs {
        Outputs::Scalar { .. } => writer.line("assert result is out"),
        Outputs::Record { .. } => {
            writer.line("for actual, expected_out in zip(result, out, strict=True):");
            writer.indented(|writer| writer.line("assert actual is expected_out"));
        }
    }
}

fn dictionary(values: &BTreeMap<String, GoldenInput>, function: &Function) -> String {
    let entries = values
        .iter()
        .map(|(name, value)| {
            let value = match value {
                GoldenInput::Number(value) => float(*value),
                GoldenInput::Enum(member) => {
                    let enum_name = function
                        .inputs
                        .iter()
                        .find(|input| input.name() == name)
                        .and_then(|input| input.enum_type())
                        .expect("enum golden input has a resolved enum type")
                        .name
                        .as_str();
                    format!("{enum_name}.{}", member.to_ascii_uppercase())
                }
            };
            format!("'{name}': {value}")
        })
        .collect::<Vec<_>>()
        .join(", ");
    format!("{{{entries}}}")
}

fn expected_dictionary(function: &Function, values: &[f64]) -> String {
    let entries = function
        .outputs
        .fields()
        .iter()
        .zip(values)
        .map(|(field, value)| format!("'{}': {}", field.name, float(*value)))
        .collect::<Vec<_>>()
        .join(", ");
    format!("{{{entries}}}")
}

fn float(value: f64) -> String {
    format!("{value:?}")
}
