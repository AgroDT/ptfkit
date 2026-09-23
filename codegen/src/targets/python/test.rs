use std::collections::BTreeMap;

use crate::{
    model::{CompiledFunction, Function, Outputs, PythonGeneration, VerificationInput},
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
            if let Some(enum_type) = input.enum_type()
                && !enum_type.is_shared()
            {
                imports.push(&enum_type.enum_type.name);
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
    let shared = functions
        .iter()
        .flat_map(|resolved| &resolved.entry.spec.functions[resolved.function_index].inputs)
        .filter_map(|input| {
            input
                .enum_type()
                .and_then(|definition| definition.shared_document())
        })
        .collect::<std::collections::BTreeSet<_>>();
    for document in shared {
        module.import("ptfkit", format!("{document} as _{document}"));
    }
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
    let case_ids_name = format!("{cases_name}_IDS");
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
    module.assignment(&case_ids_name, "[");
    module.indented(|writer| {
        for case in &function.verification_cases {
            writer.line(format_args!("{:?},", case.id));
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
        "@pytest.mark.parametrize(('inputs', 'expected'), {cases_name}, ids={case_ids_name})"
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

fn dictionary(values: &BTreeMap<String, VerificationInput>, function: &Function) -> String {
    let entries = values
        .iter()
        .map(|(name, value)| {
            let value = match value {
                VerificationInput::Number(value) => float(*value),
                VerificationInput::Enum(member) => {
                    let definition = function
                        .inputs
                        .iter()
                        .find(|input| input.name() == name)
                        .and_then(|input| input.enum_type())
                        .expect("enum verification input has a resolved enum type");
                    let enum_name = super::wrapper::enum_type_name(&definition.enum_type);
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
