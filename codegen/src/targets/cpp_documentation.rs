use std::{collections::BTreeSet, path::PathBuf};

use anyhow::{Result, anyhow};

use crate::{
    documentation::{self as docs},
    model::{CompiledFunction, Output, Parameter},
    render::Writer,
};

use super::{
    GeneratedFile,
    documentation::{self as markdown},
    group_by_source,
};

pub(super) fn render(functions: &[CompiledFunction]) -> Result<Vec<GeneratedFile>> {
    let sources = group_by_source(functions);
    let mut files = vec![markdown::markdown_file("index.md", |writer| {
        render_index(writer, &sources);
    })];
    files.push(markdown::markdown_file("modules/ptfkit.md", |writer| {
        render_umbrella(writer, &sources);
    }));

    let mut index_entries = Vec::new();
    for (slug, functions) in sources {
        files.push(module_file(slug, &functions)?);
        for function in functions {
            index_entries.push((slug, function));
        }
    }
    index_entries.sort_by_key(|(_, function)| natural_sort_key(&function.core.name));
    files.push(markdown::markdown_file("functions.md", |writer| {
        render_functions_index(writer, &index_entries);
    }));
    Ok(files)
}

fn module_file(slug: &str, functions: &[&CompiledFunction]) -> Result<GeneratedFile> {
    let mut writer = Writer::new();
    render_module(&mut writer, slug, functions)?;
    Ok(GeneratedFile::new(
        PathBuf::from(format!("modules/{slug}.md")),
        markdown::markdown_contents(writer),
    ))
}

fn render_index(
    writer: &mut Writer,
    sources: &std::collections::BTreeMap<&str, Vec<&CompiledFunction>>,
) {
    markdown::generated_frontmatter(writer, |writer| {
        writer.line("title: C++ API reference");
    });
    writer.line("# C++ API reference");
    writer.blank_line();
    writer.line("ptfkit's C++ API is organized around C++20 modules.");
    writer.blank_line();
    writer.line("## Modules");
    writer.blank_line();
    writer.line("- [`ptfkit`](modules/ptfkit.md) — Re-exports every ptfkit source module.");
    for (slug, functions) in sources {
        writer.line(format_args!(
            "- [`ptfkit.{slug}`](modules/{slug}.md) — {}",
            escape_text(
                docs::for_source(
                    &functions[0].entry.spec.source,
                    &functions[0].entry.spec.scope
                )
                .summary,
            )
        ));
    }
    writer.blank_line();
    writer.line("See the [function index](functions.md) for all public C++ functions.");
}

fn render_umbrella(
    writer: &mut Writer,
    sources: &std::collections::BTreeMap<&str, Vec<&CompiledFunction>>,
) {
    markdown::generated_frontmatter(writer, |writer| {
        writer.line("title: C++ module ptfkit");
        writer.line("nav-title: ptfkit");
    });
    writer.line("# `ptfkit`");
    writer.blank_line();
    markdown::code_block(writer, "cpp", |writer| {
        writer.line("import ptfkit;");
    });
    writer.line("This umbrella module re-exports every public ptfkit source module. Import an individual module when only one source is needed.");
    writer.blank_line();
    writer.line("## Re-exported modules");
    writer.blank_line();
    for (slug, functions) in sources {
        writer.line(format_args!(
            "- [`ptfkit.{slug}`]({slug}.md) — {}",
            escape_text(
                docs::for_source(
                    &functions[0].entry.spec.source,
                    &functions[0].entry.spec.scope
                )
                .summary,
            )
        ));
    }
}

fn render_module(writer: &mut Writer, slug: &str, functions: &[&CompiledFunction]) -> Result<()> {
    let first = functions
        .first()
        .expect("compiled source contains at least one function");
    let source = docs::for_source(&first.entry.spec.source, &first.entry.spec.scope);
    markdown::generated_frontmatter(writer, |writer| {
        writer.line(format_args!("title: C++ module ptfkit.{slug}"));
        writer.line(format_args!("nav-title: ptfkit.{slug}"));
    });
    writer.line(format_args!("# `ptfkit.{slug}`"));
    writer.blank_line();
    markdown::code_block(writer, "cpp", |writer| {
        writer.line(format_args!("import ptfkit.{slug};"));
    });
    writer.line(format_args!("**Exported namespace:** `ptfkit::{slug}`"));
    writer.blank_line();
    writer.line(escape_text(source.summary));
    writer.blank_line();
    writer.line("## Source");
    writer.blank_line();
    writer.line(escape_text(source.reference.citation));
    writer.blank_line();
    if let Some(doi) = source.reference.doi {
        writer.line(format_args!(
            "[DOI: {}]({})",
            escape_text(doi.identifier),
            doi.url
        ));
        writer.blank_line();
    }
    if source.territory.is_some() || source.dataset.is_some() {
        writer.line("## Scope");
        writer.blank_line();
        if let Some(territory) = source.territory {
            writer.line(format_args!("**Territory:** {}", escape_text(territory)));
            writer.blank_line();
        }
        if let Some(dataset) = source.dataset {
            writer.line(format_args!("**Dataset:** {}", escape_text(dataset)));
            writer.blank_line();
        }
    }
    writer.line(format_args!(
        "[PTF catalog page](../../../ptf-catalog/sources/{slug}.md)"
    ));
    writer.blank_line();

    let mut structures = BTreeSet::new();
    for function in functions {
        if let Output::Struct(_) = &function.core.output {
            let result = result_class(function)?;
            if structures.insert(result) {
                render_structure(writer, result, spec(function).outputs.fields());
            }
        }
    }
    writer.line("## Functions");
    writer.blank_line();
    for function in functions {
        render_function_documentation(writer, function)?;
    }
    Ok(())
}

fn render_structure(writer: &mut Writer, name: &str, fields: &[Parameter]) {
    writer.line(format_args!("## `{name}`"));
    writer.blank_line();
    markdown::code_block(writer, "cpp", |writer| {
        writer.line(format_args!("struct {name} {{"));
        writer.indented(|writer| {
            for field in fields {
                writer.line(format_args!("double {};", field.name));
            }
        });
        writer.line("};");
    });
    writer.line("| Field | Description |");
    writer.line("| --- | --- |");
    for field in fields {
        writer.line(format_args!(
            "| `{}` | {} |",
            field.name,
            parameter_details(field)
        ));
    }
    writer.blank_line();
}

fn render_function_documentation(writer: &mut Writer, function: &CompiledFunction) -> Result<()> {
    let spec = spec(function);
    let document = docs::for_function(spec);
    let anchor = function_anchor(&function.core.name);
    writer.line(format_args!("### `{}` {{#{anchor}}}", function.core.name));
    writer.blank_line();
    writer.line(escape_text(document.summary));
    writer.blank_line();
    let signature = signature(function)?;
    markdown::code_block(writer, "cpp", |writer| {
        writer.line(signature);
    });
    writer.line("#### Parameters");
    writer.blank_line();
    writer.line("| Name | Description |");
    writer.line("| --- | --- |");
    for parameter in document.parameters {
        writer.line(format_args!(
            "| `{}` | {} |",
            parameter.name,
            parameter_details(parameter)
        ));
    }
    writer.blank_line();
    writer.line("#### Returns");
    writer.blank_line();
    match document.returns {
        docs::Returns::Scalar(field) => {
            writer.line(parameter_details(field));
            writer.blank_line();
        }
        docs::Returns::Record { .. } => {
            writer.line(format_args!("A `{}` value.", result_class(function)?));
            writer.blank_line();
        }
    }
    for note in document.notes {
        render_admonition(writer, "note", note);
    }
    for warning in document.warnings {
        render_admonition(writer, "warning", warning);
    }
    Ok(())
}

fn render_functions_index(writer: &mut Writer, functions: &[(&str, &CompiledFunction)]) {
    markdown::generated_frontmatter(writer, |writer| {
        writer.line("title: C++ function index");
    });
    writer.line("# C++ function index");
    writer.blank_line();
    writer.line("| Function | Summary | Module |");
    writer.line("| --- | --- | --- |");
    for (slug, function) in functions {
        let qualified = format!("ptfkit::{slug}::{}", function.core.name);
        writer.line(format_args!(
            "| [`{qualified}`](modules/{slug}.md#{}) | {} | [`ptfkit.{slug}`](modules/{slug}.md) |",
            function_anchor(&function.core.name),
            escape_table(docs::for_function(spec(function)).summary),
        ));
    }
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

fn render_admonition(writer: &mut Writer, kind: &str, body: &str) {
    markdown::admonition(writer, kind, body, escape_text);
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
        assert!(index.find("[`ptfkit`]( ").is_none());
        assert!(
            index.find("[`ptfkit`](modules/ptfkit.md)").unwrap()
                < index.find("ptfkit.ahuja1984").unwrap()
        );
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
