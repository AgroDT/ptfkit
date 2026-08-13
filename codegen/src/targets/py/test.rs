use std::collections::BTreeMap;

use crate::model::{CompiledFunction, Function, Outputs, PythonGeneration};

use super::{WRAPPER_HEADER, natural_sort_key};

pub(super) fn render(functions: &[CompiledFunction]) -> Vec<(String, PythonGeneration, String)> {
    let mut modules: BTreeMap<String, Vec<&CompiledFunction>> = BTreeMap::new();
    for function in functions {
        modules
            .entry(function.entry.slug.clone())
            .or_default()
            .push(function);
    }

    modules
        .into_iter()
        .map(|(slug, functions)| {
            let mode = functions[0].entry.spec.generation.public_python;
            let source = if mode == PythonGeneration::Generated {
                module_source(&slug, &functions)
            } else {
                String::new()
            };
            (slug, mode, source)
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
    let imports = imports.join(", ");
    let tests = functions
        .iter()
        .map(|resolved| {
            let function = &resolved.entry.spec.functions[resolved.function_index];
            function_source(function)
        })
        .collect::<Vec<_>>()
        .join("\n\n\n");

    format!(
        "{header}\nfrom __future__ import annotations\n\nimport pytest\n\nfrom _helpers import prepare_vector_case\nfrom ptfkit.{slug} import {imports}\n\n\n{tests}\n",
        header = WRAPPER_HEADER.trim_end(),
    )
}

fn function_source(function: &Function) -> String {
    let cases_name = format!("CASES_{}", function.public_api.name.to_ascii_uppercase());
    let cases = function
        .golden_tests
        .iter()
        .map(|case| {
            format!(
                "    ({inputs}, {expected}, {rtol}, {atol}),",
                inputs = dictionary(&case.inputs),
                expected = dictionary(&case.expected),
                rtol = float(case.rtol),
                atol = float(case.atol),
            )
        })
        .collect::<Vec<_>>()
        .join("\n");
    let assertion = expected_assertion(function, "    ", "");
    let vector_tests = if !function.golden_tests.is_empty() {
        vector_test_source(function, &cases_name)
    } else {
        Default::default()
    };
    format!(
        "{cases_name} = [\n{cases}\n]\n\n\n@pytest.mark.parametrize(('inputs', 'expected', 'rtol', 'atol'), {cases_name})\ndef test_{name}_golden(inputs: dict[str, float], expected: dict[str, float], rtol: float, atol: float):\n    result = {name}(**inputs)\n\n{assertion}{vector_tests}",
        cases_name = cases_name,
        name = function.public_api.name,
        assertion = assertion,
        vector_tests = vector_tests,
    )
}

fn vector_test_source(function: &Function, cases_name: &str) -> String {
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
    format!(
        r#"


def test_{name}_array():
    inputs, expected, rtol, atol, _out = prepare_vector_case({cases_name}{result_cls})
    result = {name}(**inputs, out=None)
{array_assertion}


def test_{name}_out():
    inputs, expected, rtol, atol, out = prepare_vector_case({cases_name}{result_cls})
    result = {name}(**inputs, out=out)
{out_assertion}
{array_assertion}"#,
        name = function.public_api.name,
        cases_name = cases_name,
        result_cls = result_cls,
        array_assertion = array_assertion,
        out_assertion = out_assertion,
    )
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
