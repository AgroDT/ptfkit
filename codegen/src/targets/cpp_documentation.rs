use std::{collections::BTreeSet, path::PathBuf};

use anyhow::{Result, anyhow};

use crate::model::{CompiledFunction, Output, Parameter};

use super::{GeneratedFile, documentation::FRONTMATTER_HEADER, group_by_source};

pub(super) fn render(functions: &[CompiledFunction]) -> Result<Vec<GeneratedFile>> {
    let sources = group_by_source(functions);
    let mut files = vec![file("index.md", index(&sources))];
    files.push(GeneratedFile::new(
        "modules/ptfkit.md".into(),
        umbrella(&sources),
    ));

    let mut index_entries = Vec::new();
    for (slug, functions) in sources {
        files.push(GeneratedFile::new(
            format!("modules/{slug}.md").into(),
            module(slug, &functions)?,
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

fn index(sources: &std::collections::BTreeMap<&str, Vec<&CompiledFunction>>) -> String {
    let mut text = format!("---\n{FRONTMATTER_HEADER}title: C++ API reference\n---\n\n");
    text.push_str("# C++ API reference\n\n");
    text.push_str("ptfkit's C++ API is organized around C++20 modules.\n\n");
    text.push_str("## Modules\n\n");
    text.push_str("- [`ptfkit`](modules/ptfkit.md) — Re-exports every ptfkit source module.\n");
    for (slug, functions) in sources {
        text.push_str(&format!(
            "- [`ptfkit.{slug}`](modules/{slug}.md) — {}\n",
            escape_text(&functions[0].entry.spec.source.summary)
        ));
    }
    text.push_str("\nSee the [function index](functions.md) for all public C++ functions.\n");
    text
}

fn umbrella(sources: &std::collections::BTreeMap<&str, Vec<&CompiledFunction>>) -> String {
    let mut text =
        format!("---\n{FRONTMATTER_HEADER}title: C++ module ptfkit\nnav-title: ptfkit\n---\n\n");
    text.push_str("# `ptfkit`\n\n```cpp\nimport ptfkit;\n```\n\n");
    text.push_str("This umbrella module re-exports every public ptfkit source module. Import an individual module when only one source is needed.\n\n");
    text.push_str("## Re-exported modules\n\n");
    for (slug, functions) in sources {
        text.push_str(&format!(
            "- [`ptfkit.{slug}`]({slug}.md) — {}\n",
            escape_text(&functions[0].entry.spec.source.summary)
        ));
    }
    text
}

fn module(slug: &str, functions: &[&CompiledFunction]) -> Result<String> {
    let first = functions
        .first()
        .expect("compiled source contains at least one function");
    let source = &first.entry.spec.source;
    let scope = &first.entry.spec.scope;
    let mut text = format!(
        "---\n{FRONTMATTER_HEADER}title: C++ module ptfkit.{slug}\nnav-title: ptfkit.{slug}\n---\n\n"
    );
    text.push_str(&format!(
        "# `ptfkit.{slug}`\n\n```cpp\nimport ptfkit.{slug};\n```\n\n"
    ));
    text.push_str(&format!("**Exported namespace:** `ptfkit::{slug}`\n\n"));
    text.push_str(&format!("{}\n\n", escape_text(&source.summary)));
    text.push_str("## Source\n\n");
    text.push_str(&escape_text(&source.citation_apa));
    text.push_str("\n\n");
    if let Some(doi) = &source.doi {
        text.push_str(&format!(
            "[DOI: {}]({})\n\n",
            escape_text(&doi.identifier),
            doi.url
        ));
    }
    if scope.territory.is_some() || scope.dataset.is_some() {
        text.push_str("## Scope\n\n");
        if let Some(territory) = &scope.territory {
            text.push_str(&format!("**Territory:** {}\n\n", escape_text(territory)));
        }
        if let Some(dataset) = &scope.dataset {
            text.push_str(&format!("**Dataset:** {}\n\n", escape_text(dataset)));
        }
    }
    text.push_str(&format!(
        "[PTF catalog page](../../../ptf-catalog/sources/{slug}.md)\n\n"
    ));

    let mut structures = BTreeSet::new();
    for function in functions {
        if let Output::Struct(_) = &function.core.output {
            let result = result_class(function)?;
            if structures.insert(result) {
                text.push_str(&structure(result, spec(function).outputs.fields()));
            }
        }
    }
    text.push_str("## Functions\n\n");
    for function in functions {
        text.push_str(&function_documentation(function)?);
    }
    text.pop();
    Ok(text)
}

fn structure(name: &str, fields: &[Parameter]) -> String {
    let mut text = format!("## `{name}`\n\n```cpp\nstruct {name} {{\n");
    for field in fields {
        text.push_str(&format!("    double {};\n", field.name));
    }
    text.push_str("};\n```\n\n| Field | Description |\n| --- | --- |\n");
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
    let anchor = function_anchor(&function.core.name);
    let mut text = format!("### `{}` {{#{anchor}}}\n\n", function.core.name);
    text.push_str(&format!("{}\n\n", escape_text(&spec.public_api.summary)));
    text.push_str("```cpp\n");
    text.push_str(&signature(function)?);
    text.push_str("\n```\n\n");
    text.push_str("#### Parameters\n\n| Name | Description |\n| --- | --- |\n");
    for parameter in &spec.inputs {
        text.push_str(&format!(
            "| `{}` | {} |\n",
            parameter.name,
            parameter_details(parameter)
        ));
    }
    text.push_str("\n#### Returns\n\n");
    match &function.core.output {
        Output::Scalar => text.push_str(&format!(
            "{}\n\n",
            parameter_details(&spec.outputs.fields()[0])
        )),
        Output::Struct(_) => text.push_str(&format!("A `{}` value.\n\n", result_class(function)?)),
    }
    for note in &spec.documentation.notes {
        admonition(&mut text, "note", note);
    }
    for warning in &spec.documentation.warnings {
        admonition(&mut text, "warning", warning);
    }
    Ok(text)
}

fn functions_index(functions: &[(&str, &CompiledFunction)]) -> String {
    let mut text = format!("---\n{FRONTMATTER_HEADER}title: C++ function index\n---\n\n");
    text.push_str("# C++ function index\n\n| Function | Summary | Module |\n| --- | --- | --- |\n");
    for (slug, function) in functions {
        let qualified = format!("ptfkit::{slug}::{}", function.core.name);
        text.push_str(&format!(
            "| [`{qualified}`](modules/{slug}.md#{}) | {} | [`ptfkit.{slug}`](modules/{slug}.md) |\n",
            function_anchor(&function.core.name),
            escape_table(&spec(function).public_api.summary),
        ));
    }
    text
}

fn signature(function: &CompiledFunction) -> Result<String> {
    let result = match &function.core.output {
        Output::Scalar => "double".to_owned(),
        Output::Struct(_) => result_class(function)?.to_owned(),
    };
    Ok(format!(
        "[[nodiscard]]\ninline {result} {}({})",
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

fn result_class(function: &CompiledFunction) -> Result<&str> {
    spec(function)
        .result_class()
        .ok_or_else(|| anyhow!("record output has no result class"))
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
        render(&compiled).expect("C++ documentation renders")
    }

    fn contents<'a>(files: &'a [GeneratedFile], path: &str) -> &'a str {
        &files
            .iter()
            .find(|file| file.path == Path::new(path))
            .unwrap_or_else(|| panic!("missing generated file {path}"))
            .contents
    }

    #[test]
    fn documents_modules_functions_and_record_fields_from_compiled_sources() {
        let files = rendered_files();
        let index = contents(&files, "index.md");
        let rawls = contents(&files, "modules/rawls1982.md");
        let function_index = contents(&files, "functions.md");

        assert!(index.starts_with(
            "---\n# @generated by ptfkit-codegen; DO NOT EDIT.\n\ntitle: C++ API reference\n---\n"
        ));
        assert!(rawls.starts_with(
            "---\n# @generated by ptfkit-codegen; DO NOT EDIT.\n\ntitle: C++ module ptfkit.rawls1982\nnav-title: ptfkit.rawls1982\n---\n"
        ));
        assert!(index.contains("[`ptfkit`](modules/ptfkit.md)"));
        assert!(rawls.contains("import ptfkit.rawls1982;"));
        assert!(rawls.contains("**Exported namespace:** `ptfkit::rawls1982`"));
        assert!(rawls.contains("## `Rawls1982PTFResult`"));
        assert!(rawls.contains("| `theta_4` | Volumetric water content at -4 kPa. (cm^3/cm^3) |"));
        assert!(rawls.contains("[[nodiscard]]\ninline double calc_ptf_rawls1982_theta_1500"));
        assert!(rawls.contains("inline Rawls1982PTFResult calc_ptf_rawls1982_full_wrc"));
        assert!(rawls.contains("{#function-calc_ptf_rawls1982_theta_1500}"));
        assert!(function_index.contains(
            "[`ptfkit::rawls1982::calc_ptf_rawls1982_theta_1500`](modules/rawls1982.md#function-calc_ptf_rawls1982_theta_1500)"
        ));
        assert!(rawls.contains("[PTF catalog page](../../../ptf-catalog/sources/rawls1982.md)"));
    }

    #[test]
    fn umbrella_lists_each_source_module_once_in_natural_order() {
        let files = rendered_files();
        let umbrella = contents(&files, "modules/ptfkit.md");
        let index = contents(&files, "index.md");
        let source_modules = files
            .iter()
            .filter(|file| {
                file.path.starts_with("modules") && file.path != Path::new("modules/ptfkit.md")
            })
            .count();

        assert_eq!(umbrella.matches("- [`ptfkit.").count(), source_modules);
        assert!(index.find("[`ptfkit`](").unwrap() < index.find("ptfkit.ahuja1984").unwrap());
        assert!(
            umbrella.find("ptfkit.ahuja1984").unwrap()
                < umbrella.find("ptfkit.aimrun2009").unwrap()
        );
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
}
