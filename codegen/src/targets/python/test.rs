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
    module.line("import pytest");
    module.blank_line();
    module.import("_helpers", "prepare_vector_case");
    module.import(&format!("ptfkit.{slug}"), imports.join(", "));
    module.blank_line();
    module.blank_line();
    for (index, resolved) in functions.iter().enumerate() {
        if index > 0 {
            module.blank_line();
            module.blank_line();
        }
        let function = &resolved.entry.spec.functions[resolved.function_index];
        function_source(&mut module, function);
    }
    module.into_string()
}

fn function_source(module: &mut Module, function: &Function) {
    let cases_name = format!("CASES_{}", function.public_api.name.to_ascii_uppercase());
    module.assignment(&cases_name, "[");
    module.indented(|writer| {
        for case in &function.golden_tests {
            writer.line(format_args!(
                "({}, {}, {}, {}),",
                dictionary(&case.inputs, function),
                numeric_dictionary(&case.expected),
                float(case.rtol),
                float(case.atol),
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
        "@pytest.mark.parametrize(('inputs', 'expected', 'rtol', 'atol'), {cases_name})"
    ));
    module.line(format_args!(
        "def test_{name}_golden(inputs: dict[str, {input_value_type}], expected: dict[str, float], rtol: float, atol: float):"
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
            "inputs, expected, rtol, atol, _out = prepare_vector_case({cases_name}{result_cls})"
        ));
        writer.line(format_args!("result = {name}(**inputs, out=None)"));
        render_expected_assertion(writer, function, "[0]");
    });
    module.blank_line();
    module.blank_line();
    module.line(format_args!("def test_{name}_out():"));
    module.indented(|writer| {
        writer.line(format_args!(
            "inputs, expected, rtol, atol, out = prepare_vector_case({cases_name}{result_cls})"
        ));
        writer.line(format_args!("result = {name}(**inputs, out=out)"));
        render_out_assertion(writer, function);
        render_expected_assertion(writer, function, "[0]");
    });
}

fn render_expected_assertion(writer: &mut crate::render::Writer, function: &Function, index: &str) {
    match &function.outputs {
        Outputs::Scalar { field } => writer.line(format_args!(
            "assert result{index} == pytest.approx(expected['{}'], rel=rtol, abs=atol)",
            field.name
        )),
        Outputs::Record { fields, .. } => {
            for field in fields {
                writer.line(format_args!(
                    "assert result.{}{index} == pytest.approx(expected['{}'], rel=rtol, abs=atol)",
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

fn numeric_dictionary(values: &BTreeMap<String, f64>) -> String {
    let entries = values
        .iter()
        .map(|(name, value)| format!("'{name}': {}", float(*value)))
        .collect::<Vec<_>>()
        .join(", ");
    format!("{{{entries}}}")
}

fn float(value: f64) -> String {
    format!("{value:?}")
}
