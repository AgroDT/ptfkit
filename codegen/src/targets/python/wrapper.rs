use std::{collections::BTreeMap, path::PathBuf};

use anyhow::{Result, bail};

use crate::{
    documentation::{self as docs, FunctionDocument},
    model::{CompiledFunction, Function, Parameter, PythonGeneration, Scope, Source},
    output::GeneratedFile,
    render::Writer,
};

use super::{WRAPPER_HEADER, natural_sort_key, syntax::Module};

const LINE_WIDTH: usize = 100;

struct PythonFunction<'a> {
    name: &'a str,
    rust_name: &'a str,
    result_class: Option<&'a str>,
    scalar_inputs: Vec<String>,
    array_inputs: Vec<String>,
    keyword_inputs: Vec<String>,
    parameters: String,
    docstring: PythonDocstring,
}

#[derive(PartialEq, Eq)]
struct PythonDocstring {
    summary: String,
    sections: Vec<(&'static str, Vec<String>)>,
}

struct PythonResultClass {
    name: String,
    field_definitions: String,
    docstring: PythonDocstring,
}

pub(crate) fn render(functions: &[CompiledFunction]) -> Result<Vec<GeneratedFile>> {
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
                        .map(|output| format!("{}: T", output.name))
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
        generated.push(GeneratedFile::new(
            PathBuf::from(module.replace('.', "/")).with_extension("py"),
            text,
        ));
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
    let mut module = Module::new(WRAPPER_HEADER);
    if functions.len() > 1 {
        let has_long_import = functions.iter().any(|function| {
            format!(
                "    {rust_name} as _{rust_name},",
                rust_name = function.rust_name
            )
            .chars()
            .count()
                > LINE_WIDTH
        });
        module.blank_line();
        module.line(if has_long_import {
            "# ruff: noqa: E501, I001"
        } else {
            "# ruff: noqa: I001"
        });
    }
    module.blank_line();
    render_module_docstring(&mut module, source, scope);
    module.write(format_args!(
        "from __future__ import annotations\n\nfrom typing import {typing_imports}\n\n"
    ));
    module.block(
        "from ptfkit._ptfkit import (",
        |writer| {
            for function in functions {
                writer.line(format_args!(
                    "{rust_name} as _{rust_name},",
                    rust_name = function.rust_name
                ));
            }
        },
        ")",
    );
    module.line("\n\nif TYPE_CHECKING:");
    module.indented(|writer| {
        writer.line("from numpy import floating");
        writer.line("from numpy.typing import ArrayLike, NDArray");
    });
    if !classes.is_empty() {
        module.blank_line();
        module.assignment("T", "TypeVar('T')");
        for class in classes {
            module.blank_line();
            module.line(format_args!(
                "class {}(NamedTuple, Generic[T]):",
                class.name
            ));
            module.indented(|writer| {
                render_docstring(writer, &class.docstring, 4);
                for line in class.field_definitions.lines() {
                    writer.line(line);
                }
            });
        }
    }
    module.blank_line();
    module.assignment(
        "__all__",
        format_args!(
            "[{}]",
            exports
                .iter()
                .map(|export| format!("'{export}'"))
                .collect::<Vec<_>>()
                .join(", ")
        ),
    );
    for function in functions {
        module.blank_line();
        module.blank_line();
        render_function(&mut module, function);
    }
    module.line("");
    module.into_string()
}

fn render_function(module: &mut Module, function: &PythonFunction<'_>) {
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
    module.line("@overload");
    module.line(format_args!(
        "def {}(*, {}) -> {scalar_result}: ...",
        function.name,
        function.scalar_inputs.join(", "),
    ));
    module.blank_line();
    module.line("@overload");
    module.line(format_args!(
        "def {}(*, {},",
        function.name,
        function.array_inputs.join(", "),
    ));
    module.indented(|writer| {
        writer.line(format_args!("out: {array_result} | None = None,"));
    });
    module.line(format_args!(") -> {array_result}: ..."));
    module.blank_line();
    module.line(format_args!("def {}(*,", function.name));
    module.indented(|writer| {
        for input in &function.keyword_inputs {
            writer.line(input);
        }
        writer.line(format_args!("out: {array_result} | None = None,"));
    });
    module.line(format_args!(") -> {scalar_result} | {array_result}:"));
    module.indented(|writer| {
        render_docstring(writer, &function.docstring, 4);
        writer.line("if out is None:");
        writer.indented(|writer| {
            writer.line(format_args!(
                "values = _{}({})",
                function.rust_name, function.parameters
            ));
        });
        writer.line("else:");
        writer.indented(|writer| {
            writer.line(format_args!(
                "values = _{}({}, out={out})",
                function.rust_name, function.parameters
            ));
        });
        writer.blank_line();
        writer.line(result);
    });
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
            .map(|input| format!("{}: float | ArrayLike,", input.name))
            .collect(),
        parameters: names.join(", "),
        docstring: function_docstring(function),
    }
}

fn render_module_docstring(module: &mut Module, source: &Source, scope: &Scope) {
    let document = docs::for_source(source, scope);
    module.line(format_args!("r\"\"\"{}", document.summary));
    module.blank_line();
    module.line("Reference:");
    render_markdown_block(module, document.reference.citation, "    ");
    if let Some(doi) = document.reference.doi {
        render_markdown_block(
            module,
            &format!("[DOI: {}]({})", doi.identifier, doi.url),
            "    ",
        );
    }
    if let Some(territory) = document.territory {
        render_definition_list_block(module, "Territory", territory);
    }
    if let Some(dataset) = document.dataset {
        render_definition_list_block(module, "Dataset", dataset);
    }
    module.blank_line();
    module.line("\"\"\"");
}

fn function_docstring(function: &Function) -> PythonDocstring {
    let document = docs::for_function(function);
    function_docstring_from_document(document, function.result_class())
}

fn function_docstring_from_document(
    document: FunctionDocument<'_>,
    result_class: Option<&str>,
) -> PythonDocstring {
    let mut arguments = document
        .parameters
        .iter()
        .map(parameter_documentation)
        .collect::<Vec<_>>();
    arguments.push("out: Optional output arrays for in-place calculation.".into());
    let returns = if let Some(result_class) = result_class {
        vec![format!(
            "{result_class}: Results grouped by result attributes."
        )]
    } else {
        match document.returns {
            docs::Returns::Scalar(field) => vec![parameter_documentation(field)],
            docs::Returns::Record { fields, .. } => {
                fields.iter().map(parameter_documentation).collect()
            }
        }
    };
    let mut sections = vec![("Arguments", arguments), ("Returns", returns)];
    if let Some(territory) = document.territory {
        sections.push(("Territory", vec![territory.into()]));
    }
    let models = [
        document
            .models
            .h_theta
            .map(|model| format!("$h(\\theta)$: {model}")),
        document.models.k_h.map(|model| format!("$k(h)$: {model}")),
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
            document.remarks.prediction_target
        ))
        .chain(document.notes.iter().cloned())
        .collect(),
    ));
    if !document.warnings.is_empty() {
        sections.push(("Warning", document.warnings.to_vec()));
    }
    PythonDocstring {
        summary: document.summary.to_owned(),
        sections,
    }
}

fn result_class_docstring(function: &Function) -> PythonDocstring {
    PythonDocstring {
        summary: "Results returned by the matching PTF.".into(),
        sections: vec![(
            "Attributes",
            function
                .outputs
                .fields()
                .iter()
                .map(parameter_documentation)
                .collect(),
        )],
    }
}

fn parameter_documentation(parameter: &Parameter) -> String {
    docs::parameter_documentation(parameter)
}

fn render_definition_list_block(module: &mut Module, name: &str, text: &str) {
    module.blank_line();
    module.line(name);
    module.blank_line();
    render_markdown_block(module, text, ":   ");
}

fn render_markdown_block(module: &mut Module, text: &str, first_prefix: &str) {
    let first_width = LINE_WIDTH - first_prefix.len();
    let wrapped = wrap_doc_line(text, first_width, 96);
    module.line(format_args!("{first_prefix}{}", wrapped[0]));
    for line in wrapped.iter().skip(1) {
        module.line(format_args!("    {line}"));
    }
}

fn with_terminal_punctuation(text: &str) -> String {
    if matches!(text.chars().last(), Some('.' | '?' | '!')) {
        text.into()
    } else {
        format!("{text}.")
    }
}

fn render_docstring(writer: &mut Writer, docstring: &PythonDocstring, indent_width: usize) {
    let left_width = LINE_WIDTH - indent_width;
    let raw = docstring.summary.contains('\\')
        || docstring
            .sections
            .iter()
            .flat_map(|(title, entries)| {
                std::iter::once(*title).chain(entries.iter().map(String::as_str))
            })
            .any(|text| text.contains('\\'));
    let opening = if raw { "r\"\"\"" } else { "\"\"\"" };
    let summary = with_terminal_punctuation(&docstring.summary);
    let first_line_width = left_width - 3;
    let (summary, description) = if summary.len() <= first_line_width {
        (summary, None)
    } else {
        (
            "Calculate the pedotransfer function.".into(),
            Some(wrap_doc_line(&summary, left_width, left_width)),
        )
    };
    writer.line(format_args!("{opening}{summary}"));
    writer.blank_line();
    if let Some(description) = description {
        for line in description {
            writer.line(line);
        }
        writer.blank_line();
    }
    for (section_index, (title, entries)) in docstring.sections.iter().enumerate() {
        if !title.is_empty() {
            writer.line(format_args!("{title}:"));
        }
        for entry in entries {
            let wrapped = wrap_doc_line(entry, left_width - 4, left_width - 8);
            writer.line(format_args!("    {}", wrapped[0]));
            for line in wrapped.iter().skip(1) {
                writer.line(format_args!("        {line}"));
            }
        }
        if section_index + 1 != docstring.sections.len() {
            writer.blank_line();
        }
    }
    writer.blank_line();
    writer.line("\"\"\"");
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
    use super::{function_docstring, render_module_docstring};
    use crate::{
        model::{Documentation, Function, FunctionScope, Models, PublicApi, Scope, Source},
        targets::python::syntax::Module,
    };

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
            input_adapters: None,
            inputs: Vec::new(),
            outputs: crate::model::Outputs::Record {
                name: "TestResult".into(),
                fields: Vec::new(),
            },
            documentation: Documentation::default(),
            implementation: None,
            golden_tests: Vec::new(),
        }
    }

    #[test]
    fn function_territory_is_rendered_only_when_declared() {
        let with_territory = function_docstring(&function(Some("Narrow test region.")));
        assert_eq!(
            with_territory
                .sections
                .iter()
                .find(|(title, _)| *title == "Territory")
                .map(|(_, entries)| entries),
            Some(&vec!["Narrow test region.".into()])
        );
        let without_territory = function_docstring(&function(None));
        assert!(
            without_territory
                .sections
                .iter()
                .all(|(title, _)| *title != "Territory")
        );
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

        let mut module = Module::new("");
        render_module_docstring(&mut module, &source, &scope);
        let docstring = module.into_string();
        assert_eq!(
            docstring.lines().next(),
            Some("r\"\"\"Test et al. (2026), short territory.")
        );
        assert!(docstring.contains("[DOI: 10.1234/test](https://example.test/doi/10.1234/test)"));
    }
}
