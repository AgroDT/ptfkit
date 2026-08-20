use std::{collections::BTreeSet, path::PathBuf};

use anyhow::Result;

use crate::{
    documentation::{self as docs},
    model::{CompiledFunction, Output, Parameter},
};

use super::{
    GeneratedFile,
    documentation::{FRONTMATTER_HEADER, HEADER},
    group_by_source,
    native::c_result_name,
};

pub(super) fn render(functions: &[CompiledFunction]) -> Result<Vec<GeneratedFile>> {
    let sources = group_by_source(functions);
    let mut files = vec![file("index.md", index(&sources))];
    files.push(header_file(
        "headers/ptfkit.md",
        "ptfkit",
        umbrella(&sources),
    ));

    let mut index_entries = Vec::new();
    for (slug, functions) in sources {
        files.push(header_file(
            format!("headers/{slug}.md"),
            slug,
            header(slug, &functions)?,
        ));
        for function in functions {
            index_entries.push((slug, function));
        }
    }
    index_entries.sort_by_key(|(_, function)| natural_sort_key(&function.core.name));
    files.push(file("functions.md", functions_index(&index_entries)));
    Ok(files)
}

fn file(path: impl Into<PathBuf>, contents: String) -> GeneratedFile {
    GeneratedFile::new(path.into(), format!("{}\n", contents.trim_end()))
}

fn header_file(path: impl Into<PathBuf>, slug: &str, contents: String) -> GeneratedFile {
    GeneratedFile::new(
        path.into(),
        format!("---\ntitle: \"{slug}.h\"\n---\n\n{}\n", contents.trim_end()),
    )
}

fn index(sources: &std::collections::BTreeMap<&str, Vec<&CompiledFunction>>) -> String {
    let mut text = format!("---\n{FRONTMATTER_HEADER}title: C API reference\n---\n\n");
    text.push_str("# C API reference\n\n");
    text.push_str("ptfkit's C API is organized around installed headers.\n\n");
    text.push_str("## Headers\n\n");
    text.push_str(
        "- [`<ptfkit/ptfkit.h>`](headers/ptfkit.md) — Aggregates every ptfkit source header.\n",
    );
    for (slug, functions) in sources {
        let summary = docs::for_source(
            &functions[0].entry.spec.source,
            &functions[0].entry.spec.scope,
        )
        .summary;
        text.push_str(&format!(
            "- [`<ptfkit/{slug}.h>`](headers/{slug}.md) — {}\n",
            escape_text(summary)
        ));
    }
    text.push_str("\nSee the [function index](functions.md) for all public C functions.\n");
    text
}

fn umbrella(sources: &std::collections::BTreeMap<&str, Vec<&CompiledFunction>>) -> String {
    let mut text = String::from(HEADER);
    text.push_str("# `<ptfkit/ptfkit.h>`\n\n");
    text.push_str("```c\n#include <ptfkit/ptfkit.h>\n```\n\n");
    text.push_str("This umbrella header aggregates every public ptfkit source header. Include an individual header when only one source is needed.\n\n");
    text.push_str("## Included headers\n\n");
    for (slug, functions) in sources {
        text.push_str(&format!(
            "- [`<ptfkit/{slug}.h>`]({slug}.md) — {}\n",
            escape_text(
                docs::for_source(
                    &functions[0].entry.spec.source,
                    &functions[0].entry.spec.scope
                )
                .summary,
            )
        ));
    }
    text
}

fn header(slug: &str, functions: &[&CompiledFunction]) -> Result<String> {
    let first = functions
        .first()
        .expect("compiled source contains at least one function");
    let source = docs::for_source(&first.entry.spec.source, &first.entry.spec.scope);
    let mut text = String::from(HEADER);
    text.push_str(&format!("# `<ptfkit/{slug}.h>`\n\n"));
    text.push_str(&format!("```c\n#include <ptfkit/{slug}.h>\n```\n\n"));
    text.push_str(&format!("{}\n\n", escape_text(source.summary)));
    text.push_str("## Source\n\n");
    text.push_str(&escape_text(source.reference.citation));
    text.push_str("\n\n");
    if let Some(doi) = source.reference.doi {
        text.push_str(&format!(
            "[DOI: {}]({})\n\n",
            escape_text(doi.identifier),
            doi.url
        ));
    }
    if source.territory.is_some() || source.dataset.is_some() {
        text.push_str("## Scope\n\n");
        if let Some(territory) = source.territory {
            text.push_str(&format!("**Territory:** {}\n\n", escape_text(territory)));
        }
        if let Some(dataset) = source.dataset {
            text.push_str(&format!("**Dataset:** {}\n\n", escape_text(dataset)));
        }
    }
    text.push_str(&format!(
        "[PTF catalog page](../../../ptf-catalog/sources/{slug}.md)\n\n"
    ));

    let mut structures = BTreeSet::new();
    for function in functions {
        if let Output::Struct(_) = &function.core.output {
            let spec = spec(function);
            let name = spec
                .result_class()
                .expect("record output has a result class");
            let c_name = c_result_name(name);
            if structures.insert(c_name.clone()) {
                text.push_str(&structure(&c_name, spec.outputs.fields()));
            }
        }
    }
    text.push_str("## Functions\n\n");
    for function in functions {
        text.push_str(&function_documentation(function)?);
    }
    Ok(text)
}

fn structure(name: &str, fields: &[Parameter]) -> String {
    let mut text = format!("## `{name}`\n\n");
    text.push_str("```c\n");
    text.push_str(&format!(
        "typedef struct {{\n{} }} {name};\n",
        fields
            .iter()
            .map(|field| format!("    double {};\n", field.name))
            .collect::<String>()
    ));
    text.push_str("```\n\n| Field | Description |\n| --- | --- |\n");
    for field in fields {
        text.push_str(&format!(
            "| `{}` | {} |\n",
            field.name,
            parameter_details(field)
        ));
    }
    text.push('\n');
    text
}

fn function_documentation(function: &CompiledFunction) -> Result<String> {
    let spec = spec(function);
    let document = docs::for_function(spec);
    let anchor = function_anchor(&function.core.name);
    let mut text = format!("### `{}` {{#{anchor}}}\n\n", function.core.name);
    text.push_str(&format!("{}\n\n", escape_text(document.summary)));
    text.push_str("```c\n");
    text.push_str(&signature(function)?);
    text.push_str(";\n```\n\n");
    text.push_str("#### Parameters\n\n| Name | Direction | Description |\n| --- | --- | --- |\n");
    for parameter in document.parameters {
        text.push_str(&format!(
            "| `{}` | in | {} |\n",
            parameter.name,
            parameter_details(parameter)
        ));
    }
    text.push_str("\n#### Returns\n\n");
    match document.returns {
        docs::Returns::Scalar(field) => text.push_str(&format!("{}\n\n", parameter_details(field))),
        docs::Returns::Record { .. } => {
            let name = spec
                .result_class()
                .expect("record output has a result class");
            text.push_str(&format!("A `{}` value.\n\n", c_result_name(name)));
        }
    }
    for note in document.notes {
        admonition(&mut text, "note", note);
    }
    for warning in document.warnings {
        admonition(&mut text, "warning", warning);
    }
    Ok(text)
}

fn functions_index(functions: &[(&str, &CompiledFunction)]) -> String {
    let mut text = format!("---\n{FRONTMATTER_HEADER}title: C function index\n---\n\n");
    text.push_str("# C function index\n\n| Function | Summary | Header |\n| --- | --- | --- |\n");
    for (slug, function) in functions {
        text.push_str(&format!(
            "| [`{0}`](headers/{1}.md#{2}) | {3} | [`<ptfkit/{1}.h>`](headers/{1}.md) |\n",
            function.core.name,
            slug,
            function_anchor(&function.core.name),
            escape_table(docs::for_function(spec(function)).summary),
        ));
    }
    text
}

fn signature(function: &CompiledFunction) -> Result<String> {
    let spec = spec(function);
    let result = match &function.core.output {
        Output::Scalar => "double".to_owned(),
        Output::Struct(_) => c_result_name(
            spec.result_class()
                .expect("record output has a result class"),
        ),
    };
    Ok(format!(
        "static inline {result} {}({})",
        function.core.name,
        function
            .core
            .inputs
            .iter()
            .map(|input| format!("double {input}"))
            .collect::<Vec<_>>()
            .join(", ")
    ))
}

fn spec(function: &CompiledFunction) -> &crate::model::Function {
    &function.entry.spec.functions[function.function_index]
}

fn function_anchor(name: &str) -> String {
    format!("function-{name}")
}

fn parameter_details(parameter: &Parameter) -> String {
    format!(
        "{} ({})",
        escape_table(&parameter.description),
        escape_table(&parameter.unit)
    )
}

fn admonition(text: &mut String, kind: &str, body: &str) {
    text.push_str(&format!("!!! {kind}\n\n"));
    for line in body.lines() {
        text.push_str(&format!("    {}\n", escape_text(line)));
    }
    text.push('\n');
}

fn escape_text(value: &str) -> String {
    value.replace('\\', "\\\\").replace('`', "\\`")
}

fn escape_table(value: &str) -> String {
    escape_text(value).replace('\n', " ").replace('|', "\\|")
}

fn natural_sort_key(value: &str) -> String {
    super::py::natural_sort_key(value)
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::*;

    fn rendered_files() -> Vec<GeneratedFile> {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .expect("codegen directory has a repository parent");
        let entries = crate::specs::load(root).expect("repository specifications load");
        let compiled =
            super::super::compile::functions(entries).expect("repository specifications compile");
        render(&compiled).expect("C documentation renders")
    }

    fn contents<'a>(files: &'a [GeneratedFile], path: &str) -> &'a str {
        &files
            .iter()
            .find(|file| file.path == Path::new(path))
            .unwrap_or_else(|| panic!("missing generated file {path}"))
            .contents
    }

    #[test]
    fn documents_headers_functions_and_record_fields_from_compiled_sources() {
        let files = rendered_files();
        let index = contents(&files, "index.md");
        let rawls = contents(&files, "headers/rawls1982.md");
        let function_index = contents(&files, "functions.md");

        assert!(index.starts_with(
            "---\n# @generated by ptfkit-codegen; DO NOT EDIT.\n\ntitle: C API reference\n---\n"
        ));
        assert!(rawls.starts_with("---\ntitle: \"rawls1982.h\"\n---\n"));
        assert!(index.contains("[`<ptfkit/ptfkit.h>`](headers/ptfkit.md)"));
        assert!(rawls.contains("## `rawls1982_ptf_result`"));
        assert!(rawls.contains("| `theta_4` | Volumetric water content at -4 kPa. (cm^3/cm^3) |"));
        assert!(rawls.contains(
            "static inline double calc_ptf_rawls1982_theta_1500(double clay, double organic_matter)"
        ));
        assert!(rawls.contains("static inline rawls1982_ptf_result calc_ptf_rawls1982_full_wrc"));
        assert!(rawls.contains("{#function-calc_ptf_rawls1982_theta_1500}"));
        assert!(
            function_index.contains("headers/rawls1982.md#function-calc_ptf_rawls1982_theta_1500")
        );
        assert!(rawls.contains("[PTF catalog page](../../../ptf-catalog/sources/rawls1982.md)"));
    }

    #[test]
    fn umbrella_lists_each_source_header_once_in_natural_order() {
        let files = rendered_files();
        let umbrella = contents(&files, "headers/ptfkit.md");
        let index = contents(&files, "index.md");
        let source_headers = files
            .iter()
            .filter(|file| {
                file.path.starts_with("headers") && file.path != Path::new("headers/ptfkit.md")
            })
            .count();

        assert_eq!(umbrella.matches("- [`<ptfkit/").count(), source_headers);
        assert!(index.find("ptfkit.h").unwrap() < index.find("ahuja1984.h").unwrap());
        assert!(umbrella.find("ahuja1984.h").unwrap() < umbrella.find("aimrun2009.h").unwrap());
    }

    #[test]
    fn escapes_markdown_sensitive_text() {
        assert_eq!(escape_text("a `name` \\ value"), "a \\`name\\` \\\\ value");
        assert_eq!(escape_table("a|b\nc"), "a\\|b c");
    }

    #[test]
    fn function_anchors_are_stable() {
        assert_eq!(
            function_anchor("calc_ptf_rawls1982"),
            "function-calc_ptf_rawls1982"
        );
    }

    #[test]
    fn natural_ordering_handles_numeric_suffixes() {
        assert!(natural_sort_key("calc_2") < natural_sort_key("calc_10"));
    }

    #[test]
    fn renders_notes_and_warnings_as_admonitions() {
        let mut text = String::new();
        admonition(&mut text, "note", "Keep `value` in range.");
        admonition(&mut text, "warning", "Do not use | as a separator.");
        assert_eq!(
            text,
            "!!! note\n\n    Keep \\`value\\` in range.\n\n!!! warning\n\n    Do not use | as a separator.\n\n"
        );
    }
}
