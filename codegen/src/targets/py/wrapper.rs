use std::collections::BTreeMap;

use anyhow::{Result, bail};

use crate::model::{CompiledFunction, Function, Parameter, PythonGeneration, Scope, Source};

use super::{super::documentation, WRAPPER_HEADER, natural_sort_key};

struct PythonFunction<'a> {
    name: &'a str,
    rust_name: &'a str,
    result_class: Option<&'a str>,
    scalar_inputs: Vec<String>,
    array_inputs: Vec<String>,
    keyword_inputs: Vec<String>,
    parameters: String,
    docstring: String,
}

struct PythonResultClass {
    name: String,
    field_definitions: String,
    docstring: String,
}

pub(crate) fn render(
    functions: &[CompiledFunction],
) -> Result<Vec<(String, PythonGeneration, String)>> {
    let mut modules: BTreeMap<String, Vec<&CompiledFunction>> = BTreeMap::new();
    for function in functions {
        modules
            .entry(format!("ptfkit.{}", function.entry.slug))
            .or_default()
            .push(function);
    }

    let mut generated = Vec::new();
    for (module, functions) in modules {
        let mode = functions[0].entry.spec.generation.public_python;
        if mode == PythonGeneration::Manual {
            generated.push((module, mode, String::new()));
            continue;
        }
        let source = &functions[0].entry.spec.source;
        let scope = &functions[0].entry.spec.scope;
        let mut classes = BTreeMap::<String, PythonResultClass>::new();
        for resolved in &functions {
            let function = &resolved.entry.spec.functions[resolved.function_index];
            if let Some(class_name) = function.result_class() {
                let result_class = PythonResultClass {
                    name: class_name.to_owned(),
                    field_definitions: function
                        .outputs
                        .fields()
                        .iter()
                        .map(|output| format!("    {}: T", output.name))
                        .collect::<Vec<_>>()
                        .join("\n"),
                    docstring: result_class_docstring(function),
                };
                if let Some(previous) = classes.get(class_name)
                    && (previous.field_definitions != result_class.field_definitions
                        || previous.docstring != result_class.docstring)
                {
                    bail!("Python result class `{class_name}` is reused with conflicting fields")
                }
                classes.insert(class_name.to_owned(), result_class);
            }
        }
        let functions = functions
            .iter()
            .map(|resolved| view(resolved))
            .collect::<Vec<_>>();
        let mut exports = classes
            .keys()
            .cloned()
            .chain(functions.iter().map(|function| function.name.to_owned()))
            .collect::<Vec<_>>();
        exports.sort_by_key(|export| natural_sort_key(export));
        let classes = classes.into_values().collect::<Vec<_>>();
        let typing_imports = if classes.is_empty() {
            "TYPE_CHECKING, overload"
        } else {
            "TYPE_CHECKING, Generic, NamedTuple, TypeVar, overload"
        };
        let text = module_source(
            source,
            scope,
            typing_imports,
            &classes,
            &functions,
            &exports,
        );
        generated.push((module, mode, text));
    }
    Ok(generated)
}

fn module_source(
    source: &Source,
    scope: &Scope,
    typing_imports: &str,
    classes: &[PythonResultClass],
    functions: &[PythonFunction<'_>],
    exports: &[String],
) -> String {
    let mut sections = vec![WRAPPER_HEADER.trim_end().into()];
    if functions.len() > 1 {
        let has_long_import = functions.iter().any(|function| {
            format!(
                "    {rust_name} as _{rust_name},",
                rust_name = function.rust_name
            )
            .chars()
            .count()
                > 100
        });
        sections.push(if has_long_import {
            "# ruff: noqa: E501, I001".into()
        } else {
            "# ruff: noqa: I001".into()
        });
    }
    sections.extend([
        module_docstring(source, scope),
        "from __future__ import annotations".into(),
        format!("from typing import {typing_imports}"),
        "from ptfkit._ptfkit import (".into(),
    ]);
    sections.extend(functions.iter().map(|function| {
        format!(
            "    {rust_name} as _{rust_name},",
            rust_name = function.rust_name
        )
    }));
    sections.extend([
        ")\n".into(),
        "if TYPE_CHECKING:\n    from numpy import floating\n    from numpy.typing import ArrayLike, NDArray"
            .into(),
    ]);
    if !classes.is_empty() {
        sections.push("T = TypeVar('T')".into());
        sections.extend(classes.iter().map(|class| {
            format!(
                "class {}(NamedTuple, Generic[T]):\n{}\n{}",
                class.name, class.docstring, class.field_definitions
            )
        }));
    }
    sections.push(format!(
        "__all__ = [{}]",
        exports
            .iter()
            .map(|export| format!("'{export}'"))
            .collect::<Vec<_>>()
            .join(", ")
    ));
    sections.extend(functions.iter().map(function_source));
    format!("{}\n", sections.join("\n\n"))
}

fn function_source(function: &PythonFunction<'_>) -> String {
    let scalar_result = function
        .result_class
        .map(|class| format!("{class}[floating]"))
        .unwrap_or_else(|| "floating".into());
    let array_result = function
        .result_class
        .map(|class| format!("{class}[NDArray[floating]]"))
        .unwrap_or_else(|| "NDArray[floating]".into());
    let out = if function.result_class.is_some() {
        "tuple(out)"
    } else {
        "out"
    };
    let result = if let Some(result_class) = function.result_class {
        format!("return {result_class}(*values)")
    } else {
        "return values".into()
    };
    let calculation = format!(
        "    if out is None:\n        values = _{}({})\n    else:\n        values = _{}({}, out={out})",
        function.rust_name, function.parameters, function.rust_name, function.parameters
    );
    format!(
        "@overload\ndef {}(*, {}) -> {scalar_result}: ...\n\n@overload\ndef {}(*, {},\n    out: {array_result} | None = None,\n) -> {array_result}: ...\n\ndef {}(*,\n{}\n    out: {array_result} | None = None,\n) -> {scalar_result} | {array_result}:\n{}\n{calculation}\n\n    {result}",
        function.name,
        function.scalar_inputs.join(", "),
        function.name,
        function.array_inputs.join(", "),
        function.name,
        function.keyword_inputs.join("\n"),
        function.docstring,
    )
}

fn view(resolved: &CompiledFunction) -> PythonFunction<'_> {
    let function = &resolved.entry.spec.functions[resolved.function_index];
    let names = function
        .inputs
        .iter()
        .map(|input| input.name.clone())
        .collect::<Vec<_>>();
    PythonFunction {
        name: &function.public_api.name,
        rust_name: &resolved.core.name,
        result_class: function.result_class(),
        scalar_inputs: names.iter().map(|name| format!("{name}: float")).collect(),
        array_inputs: names
            .iter()
            .map(|name| format!("{name}: ArrayLike"))
            .collect(),
        keyword_inputs: function
            .inputs
            .iter()
            .map(|input| format!("    {}: float | ArrayLike,", input.name))
            .collect(),
        parameters: names.join(", "),
        docstring: function_docstring(function),
    }
}

fn module_docstring(source: &Source, scope: &Scope) -> String {
    let mut lines = vec![
        format!("r\"\"\"{}", source.summary),
        String::new(),
        "Reference:".into(),
    ];
    lines.extend(wrap_markdown_block(&source.citation_apa, "    "));
    if let Some(doi) = &source.doi {
        lines.extend(wrap_markdown_block(
            &format!("[DOI: {}]({})", doi.identifier, doi.url),
            "    ",
        ));
    }
    if let Some(territory) = &scope.territory {
        definition_list_block(&mut lines, "Territory", territory);
    }
    if let Some(dataset) = &scope.dataset {
        definition_list_block(&mut lines, "Dataset", dataset);
    }
    lines.push(String::new());
    lines.push("\"\"\"".into());
    lines.join("\n")
}

fn function_docstring(function: &Function) -> String {
    let mut arguments = function
        .inputs
        .iter()
        .map(parameter_documentation)
        .collect::<Vec<_>>();
    arguments.push("out: Optional output arrays for in-place calculation.".into());
    let returns = if let Some(result_class) = function.result_class() {
        vec![format!(
            "{result_class}: Results grouped by result attributes."
        )]
    } else {
        function
            .outputs
            .fields()
            .iter()
            .map(parameter_documentation)
            .collect()
    };
    let mut sections = vec![("Arguments", arguments), ("Returns", returns)];
    if let Some(territory) = &function.scope.territory {
        sections.push(("Territory", vec![territory.clone()]));
    }
    let models = [
        function
            .scope
            .models
            .h_theta
            .as_ref()
            .map(|model| format!("$h(\\theta)$: {model}")),
        function
            .scope
            .models
            .k_h
            .as_ref()
            .map(|model| format!("$k(h)$: {model}")),
    ]
    .into_iter()
    .flatten()
    .collect::<Vec<_>>();
    if !models.is_empty() {
        sections.push(("Models", models));
    }
    sections.push((
        "Notes",
        std::iter::once(format!(
            "Prediction target: {}",
            function.scope.prediction_target
        ))
        .chain(function.documentation.notes.iter().cloned())
        .collect(),
    ));
    if !function.documentation.warnings.is_empty() {
        sections.push(("Warnings", function.documentation.warnings.clone()));
    }
    render_docstring("    ", &function.public_api.summary, &sections, 4)
}

fn result_class_docstring(function: &Function) -> String {
    render_docstring(
        "    ",
        "Results returned by the matching PTF.",
        &[(
            "Attributes",
            function
                .outputs
                .fields()
                .iter()
                .map(parameter_documentation)
                .collect(),
        )],
        4,
    )
}

fn parameter_documentation(parameter: &Parameter) -> String {
    documentation::parameter_documentation(parameter)
}

fn definition_list_block(lines: &mut Vec<String>, name: &str, text: &str) {
    lines.push(String::new());
    lines.push(name.into());
    lines.push(String::new());
    let wrapped = wrap_markdown_block(text, ":   ");
    lines.extend(wrapped);
}

fn wrap_markdown_block(text: &str, first_prefix: &str) -> Vec<String> {
    let first_width = 100 - first_prefix.len();
    let wrapped = wrap_doc_line(text, first_width, 96);
    let mut lines = vec![format!("{first_prefix}{}", wrapped[0])];
    lines.extend(wrapped.iter().skip(1).map(|line| format!("    {line}")));
    lines
}

fn with_terminal_punctuation(text: &str) -> String {
    if matches!(text.chars().last(), Some('.' | '?' | '!')) {
        text.into()
    } else {
        format!("{text}.")
    }
}

fn render_docstring(
    indent: &str,
    summary: &str,
    sections: &[(&str, Vec<String>)],
    indent_width: usize,
) -> String {
    let raw = summary.contains('\\')
        || sections
            .iter()
            .flat_map(|(title, entries)| {
                std::iter::once(*title).chain(entries.iter().map(String::as_str))
            })
            .any(|text| text.contains('\\'));
    let opening = if raw { "r\"\"\"" } else { "\"\"\"" };
    let summary = with_terminal_punctuation(summary);
    let first_line_width = 100 - indent_width - 3;
    let (summary, description) = if summary.len() <= first_line_width {
        (summary, None)
    } else {
        (
            "Calculate the pedotransfer function.".into(),
            Some(wrap_doc_line(
                &summary,
                100 - indent_width,
                100 - indent_width,
            )),
        )
    };
    let mut lines = vec![format!("{indent}{opening}{summary}"), String::new()];
    if let Some(description) = description {
        lines.extend(
            description
                .into_iter()
                .map(|line| format!("{indent}{line}")),
        );
        lines.push(String::new());
    }
    for (section_index, (title, entries)) in sections.iter().enumerate() {
        if !title.is_empty() {
            lines.push(format!("{indent}{title}:"));
        }
        for entry in entries {
            let wrapped = wrap_doc_line(entry, 100 - indent_width - 4, 100 - indent_width - 8);
            lines.push(format!("{indent}    {}", wrapped[0]));
            lines.extend(
                wrapped
                    .iter()
                    .skip(1)
                    .map(|line| format!("{indent}        {line}")),
            );
        }
        if section_index + 1 != sections.len() {
            lines.push(String::new());
        }
    }
    lines.push(String::new());
    lines.push(format!("{indent}\"\"\""));
    lines.join("\n")
}

fn wrap_doc_line(text: &str, first_width: usize, continuation_width: usize) -> Vec<String> {
    let mut lines = Vec::new();
    let mut line = String::new();
    let mut width = first_width;
    for word in text.split_whitespace() {
        if !line.is_empty() && line.len() + 1 + word.len() > width {
            lines.push(line);
            line = String::new();
            width = continuation_width;
        }
        if !line.is_empty() {
            line.push(' ');
        }
        line.push_str(word);
    }
    if !line.is_empty() {
        lines.push(line);
    }
    lines
}

#[cfg(test)]
mod tests {
    use super::{function_docstring, module_docstring};
    use crate::model::{Documentation, Function, FunctionScope, Models, PublicApi, Scope, Source};

    fn function(territory: Option<&str>) -> Function {
        Function {
            name: "calc_ptf_test".into(),
            status: "draft".into(),
            public_api: PublicApi {
                name: "calc_ptf_test".into(),
                result_class: None,
                summary: "Estimate a test property".into(),
            },
            scope: FunctionScope {
                territory: territory.map(str::to_owned),
                prediction_target: "Test property.".into(),
                models: Models::default(),
            },
            inputs: Vec::new(),
            outputs: crate::model::Outputs::Record {
                name: None,
                fields: Vec::new(),
            },
            output_schema: None,
            documentation: Documentation::default(),
            implementation: None,
            golden_tests: Vec::new(),
        }
    }

    #[test]
    fn function_territory_is_rendered_only_when_declared() {
        assert!(
            function_docstring(&function(Some("Narrow test region.")))
                .contains("Territory:\n        Narrow test region.")
        );
        assert!(!function_docstring(&function(None)).contains("Territory:"));
    }

    #[test]
    fn module_summary_and_doi_url_come_from_source() {
        let source = Source {
            summary: "Test et al. (2026), short territory.".into(),
            citation_apa: "Test et al. (2026). Test reference.".into(),
            doi: Some(crate::model::Doi {
                identifier: "10.1234/test".into(),
                url: "https://example.test/doi/10.1234/test".into(),
            }),
        };
        let scope = Scope {
            territory: Some("A much longer territory description.".into()),
            dataset: None,
        };

        let docstring = module_docstring(&source, &scope);
        assert_eq!(
            docstring.lines().next(),
            Some("r\"\"\"Test et al. (2026), short territory.")
        );
        assert!(docstring.contains("[DOI: 10.1234/test](https://example.test/doi/10.1234/test)"));
    }
}
