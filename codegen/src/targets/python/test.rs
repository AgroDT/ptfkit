use std::collections::BTreeMap;

use crate::{
    model::{CompiledFunction, Function, Outputs, PythonGeneration},
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
    }
    imports.sort_by_key(|name| natural_sort_key(name));
    imports.dedup();
    let mut module = Module::new(WRAPPER_HEADER);
    module.write("\nfrom __future__ import annotations\n\nimport pytest\n\n");
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
    for case in &function.golden_tests {
        module.line(format_args!(
            "    ({}, {}, {}, {}),",
            dictionary(&case.inputs),
            dictionary(&case.expected),
            float(case.rtol),
            float(case.atol),
        ));
    }
    module.write("]\n\n\n");
    let name = &function.public_api.name;
    module.line(format_args!(
        "@pytest.mark.parametrize(('inputs', 'expected', 'rtol', 'atol'), {cases_name})"
    ));
    module.line(format_args!(
        "def test_{name}_golden(inputs: dict[str, float], expected: dict[str, float], rtol: float, atol: float):"
    ));
    module.write(format_args!("    result = {name}(**inputs)\n\n"));
    module.line(expected_assertion(function, "    ", ""));
    if !function.golden_tests.is_empty() {
        vector_test_source(module, function, &cases_name);
    }
}

fn vector_test_source(module: &mut Module, function: &Function, cases_name: &str) {
    let array_assertion = expected_assertion(function, "    ", "[0]");
    let out_assertion = match &function.outputs {
        Outputs::Scalar { .. } => "    assert result is out",
        Outputs::Record { .. } => {
            "    for actual, expected_out in zip(result, out, strict=True):\n        assert actual is expected_out"
        }
    };
    let result_cls = function
        .result_class()
        .map(|result_class| format!(", {result_class}"))
        .unwrap_or_default();
    let name = &function.public_api.name;
    module.blank_line();
    module.blank_line();
    module.line(format_args!("def test_{name}_array():"));
    module.write(format_args!(
        "    inputs, expected, rtol, atol, _out = prepare_vector_case({cases_name}{result_cls})\n    result = {name}(**inputs, out=None)\n{array_assertion}\n\n\n"
    ));
    module.line(format_args!("def test_{name}_out():"));
    module.line(format_args!(
        "    inputs, expected, rtol, atol, out = prepare_vector_case({cases_name}{result_cls})"
    ));
    module.line(format_args!("    result = {name}(**inputs, out=out)"));
    module.line(out_assertion);
    module.line(array_assertion);
}

fn expected_assertion(function: &Function, indent: &str, index: &str) -> String {
    match &function.outputs {
        Outputs::Scalar { field } => format!(
            "{indent}assert result{index} == pytest.approx(expected['{}'], rel=rtol, abs=atol)",
            field.name
        ),
        Outputs::Record { fields, .. } => fields
            .iter()
            .map(|field| {
                format!(
                    "{indent}assert result.{}{index} == pytest.approx(expected['{}'], rel=rtol, abs=atol)",
                    field.name, field.name
                )
            })
            .collect::<Vec<_>>()
            .join("\n"),
    }
}

fn dictionary(values: &BTreeMap<String, f64>) -> String {
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
