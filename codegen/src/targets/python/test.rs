use std::collections::BTreeMap;

use crate::{
    model::{Acceptance, CompiledFunction, Function, GoldenInput, Outputs, PythonGeneration},
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

    modules
        .into_iter()
        .filter_map(|(slug, functions)| {
            (functions[0].entry.spec.generation.public_python == PythonGeneration::Generated).then(
                || {
                    GeneratedFile::new(
                        format!("tests/test_{slug}.py").into(),
                        module_source(&slug, &functions),
                    )
                },
            )
        })
        .collect()
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
    module.line("from typing import Any, cast");
    module.blank_line();
    module.line("import pytest");
    module.blank_line();
    module.import("_helpers", "prepare_vector_case");
    module.import(&format!("ptfkit.{slug}"), imports.join(", "));
    module.blank_line();
    module.blank_line();
    module.line("def assert_accepted(actual: object, acceptance: tuple[float, float, bool]):");
    module.indented(|writer| {
        writer.line("actual_float = float(cast(\"Any\", actual))");
        writer.line("lower, upper, exact = acceptance");
        writer.line("assert actual_float == lower if exact else lower <= actual_float <= upper");
    });
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
        for (case, compiled) in function.golden_tests.iter().zip(&resolved.golden_tests) {
            writer.line(format_args!(
                "({}, {}),",
                dictionary(&case.inputs, function),
                acceptance_dictionary(function, &compiled.acceptance),
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
        "@pytest.mark.parametrize(('inputs', 'acceptance'), {cases_name})"
    ));
    module.line(format_args!(
        "def test_{name}_golden(inputs: dict[str, {input_value_type}], acceptance: dict[str, tuple[float, float, bool]]):"
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
        render_expected_assertion(writer, function, "");
    });
    if !function.golden_tests.is_empty() {
        vector_test_source(module, function, &cases_name);
    }
}

fn vector_test_source(module: &mut Module, function: &Function, cases_name: &str) {
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
            "inputs, acceptance, _out = prepare_vector_case({cases_name}{result_cls})"
        ));
        writer.line(format_args!("result = {name}(**inputs, out=None)"));
        render_expected_assertion(writer, function, "[0]");
    });
    module.blank_line();
    module.blank_line();
    module.line(format_args!("def test_{name}_out():"));
    module.indented(|writer| {
        writer.line(format_args!(
            "inputs, acceptance, out = prepare_vector_case({cases_name}{result_cls})"
        ));
        writer.line(format_args!("result = {name}(**inputs, out=out)"));
        render_out_assertion(writer, function);
        render_expected_assertion(writer, function, "[0]");
    });
}

fn render_expected_assertion(writer: &mut crate::render::Writer, function: &Function, index: &str) {
    match &function.outputs {
        Outputs::Scalar { field } => writer.line(format_args!(
            "assert_accepted(result{index}, acceptance['{}'])",
            field.name
        )),
        Outputs::Record { fields, .. } => {
            for field in fields {
                writer.line(format_args!(
                    "assert_accepted(result.{}{index}, acceptance['{}'])",
                    field.name, field.name
                ));
            }
        }
    }
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

fn acceptance_dictionary(function: &Function, values: &[Acceptance]) -> String {
    let entries = function
        .outputs
        .fields()
        .iter()
        .zip(values)
        .map(|(field, acceptance)| {
            let value = match acceptance {
                Acceptance::Exact(value) => format!("({}, {}, True)", float(*value), float(*value)),
                Acceptance::Interval { lower, upper } => {
                    format!("({}, {}, False)", float(*lower), float(*upper))
                }
            };
            format!("'{}': {value}", field.name)
        })
        .collect::<Vec<_>>()
        .join(", ");
    format!("{{{entries}}}")
}

fn float(value: f64) -> String {
    format!("{value:?}")
}
