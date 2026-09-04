use std::{collections::BTreeSet, path::PathBuf};

use anyhow::Result;

use crate::render::markdown::HEADER;
use crate::{
    documentation::{self as docs},
    model::{CompiledFunction, EnumDefinition, Output, OutputField},
    output::GeneratedFile,
    render::{Writer, markdown},
    targets::{
        group_by_source,
        native::{c_enum_member, c_enum_name, c_result_name},
    },
};

pub(crate) fn render(functions: &[CompiledFunction]) -> Result<Vec<GeneratedFile>> {
    let sources = group_by_source(functions);
    let mut files = vec![markdown::markdown_file("index.md", |writer| {
        render_index(writer, &sources);
    })];
    files.push(header_file("headers/ptfkit.md", "ptfkit", |writer| {
        render_umbrella(writer, &sources);
        Ok(())
    })?);

    let mut index_entries = Vec::new();
    for (slug, functions) in sources {
        files.push(header_file(format!("headers/{slug}.md"), slug, |writer| {
            render_header(writer, slug, &functions)
        })?);
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

fn header_file(
    path: impl Into<PathBuf>,
    slug: &str,
    render: impl FnOnce(&mut Writer) -> Result<()>,
) -> Result<GeneratedFile> {
    let mut writer = Writer::new();
    markdown::frontmatter(&mut writer, |writer| {
        writer.line(format_args!("title: \"{slug}.h\""));
    });
    render(&mut writer)?;
    Ok(GeneratedFile::new(
        path.into(),
        markdown::markdown_contents(writer),
    ))
}

fn render_index(
    writer: &mut Writer,
    sources: &std::collections::BTreeMap<&str, Vec<&CompiledFunction>>,
) {
    markdown::generated_frontmatter(writer, |writer| {
        writer.line("title: C API reference");
    });
    writer.write(
        "# C API reference\n\nptfkit's C API is organized around installed headers.\n\n## Headers\n\n- [`<ptfkit/ptfkit.h>`](headers/ptfkit.md) — Aggregates every ptfkit source header.\n",
    );
    for (slug, functions) in sources {
        let summary = docs::for_source(
            &functions[0].entry.spec.source,
            &functions[0].entry.spec.scope,
        )
        .summary;
        writer.line(format_args!(
            "- [`<ptfkit/{slug}.h>`](headers/{slug}.md) — {}",
            escape_text(summary)
        ));
    }
    writer.blank_line();
    writer.line("See the [function index](functions.md) for all public C functions.");
}

fn render_umbrella(
    writer: &mut Writer,
    sources: &std::collections::BTreeMap<&str, Vec<&CompiledFunction>>,
) {
    writer.write(HEADER);
    writer.write("# `<ptfkit/ptfkit.h>`\n\n");
    markdown::code_block(writer, "c", |writer| {
        writer.line("#include <ptfkit/ptfkit.h>");
    });
    writer.write(
        "This umbrella header aggregates every public ptfkit source header. Include an individual header when only one source is needed.\n\n## Included headers\n\n",
    );
    for (slug, functions) in sources {
        writer.line(format_args!(
            "- [`<ptfkit/{slug}.h>`]({slug}.md) — {}",
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

fn render_header(writer: &mut Writer, slug: &str, functions: &[&CompiledFunction]) -> Result<()> {
    let first = functions
        .first()
        .expect("compiled source contains at least one function");
    let source = docs::for_source(&first.entry.spec.source, &first.entry.spec.scope);
    writer.write(HEADER);
    writer.write(format_args!("# `<ptfkit/{slug}.h>`\n\n"));
    markdown::code_block(writer, "c", |writer| {
        writer.line(format_args!("#include <ptfkit/{slug}.h>"));
    });
    writer.write(format_args!(
        "{}\n\n## Source\n\n{}\n\n",
        escape_text(source.summary),
        escape_text(source.reference.citation),
    ));
    if let Some(doi) = source.reference.doi {
        writer.write(format_args!(
            "[DOI: {}]({})\n\n",
            escape_text(doi.identifier),
            doi.url
        ));
    }
    if source.territory.is_some() || source.dataset.is_some() {
        writer.write("## Scope\n\n");
        if let Some(territory) = source.territory {
            writer.write(format_args!(
                "**Territory:** {}\n\n",
                escape_text(territory)
            ));
        }
        if let Some(dataset) = source.dataset {
            writer.write(format_args!("**Dataset:** {}\n\n", escape_text(dataset)));
        }
    }
    writer.write(format_args!(
        "[PTF catalog page](../../../ptf-catalog/sources/{slug}.md)\n\n"
    ));

    let mut enums = BTreeSet::new();
    for function in functions {
        for input in &spec(function).inputs {
            if let Some(definition) = input.enum_type()
                && enums.insert(definition.name.clone())
            {
                render_enum(writer, slug, definition, true);
            }
        }
    }
    let mut structures = BTreeSet::new();
    for function in functions {
        if let Output::Struct(_) = &function.core.output {
            let spec = spec(function);
            let name = spec
                .result_class()
                .expect("record output has a result class");
            let c_name = c_result_name(name);
            if structures.insert(c_name.clone()) {
                render_structure(writer, &c_name, spec.outputs.fields());
            }
        }
    }
    writer.write("## Functions\n\n");
    for function in functions {
        render_function_documentation(writer, function)?;
    }
    Ok(())
}

fn render_enum(writer: &mut Writer, module: &str, definition: &EnumDefinition, c: bool) {
    let name = if c {
        c_enum_name(module, &definition.name)
    } else {
        definition.name.clone()
    };
    writer.write(format_args!("## `{name}`\n\n"));
    markdown::code_block(writer, if c { "c" } else { "cpp" }, |writer| {
        writer.line(if c { "typedef enum {" } else { "enum class {" });
        writer.indented(|writer| {
            for member in &definition.values {
                let member_name = if c {
                    c_enum_member(module, &definition.name, &member.name)
                } else {
                    member.name.clone()
                };
                writer.line(format_args!("{member_name},"));
            }
        });
        if c {
            writer.line(format_args!("}} {name};"));
        } else {
            writer.line("};");
        }
    });
    writer.line("| Member | Canonical value | Description |");
    writer.line("| --- | --- | --- |");
    for member in &definition.values {
        let member_name = if c {
            c_enum_member(module, &definition.name, &member.name)
        } else {
            member.name.clone()
        };
        writer.line(format_args!(
            "| `{member_name}` | `{}` | {} |",
            escape_table(&member.value),
            member
                .description
                .as_deref()
                .map(escape_table)
                .unwrap_or_default()
        ));
    }
    writer.blank_line();
}

fn render_structure(writer: &mut Writer, name: &str, fields: &[OutputField]) {
    writer.write(format_args!("## `{name}`\n\n"));
    markdown::code_block(writer, "c", |writer| {
        writer.line("typedef struct {");
        writer.indented(|writer| {
            for field in fields {
                writer.line(format_args!("double {};", field.name));
            }
        });
        writer.line(format_args!(" }} {name};"));
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
    writer.write(format_args!(
        "### `{}` {{#{anchor}}}\n\n{}\n\n",
        function.core.name,
        escape_text(document.summary),
    ));
    let signature = signature(function)?;
    markdown::code_block(writer, "c", |writer| {
        writer.line(format_args!("{signature};"));
    });
    writer.write("#### Parameters\n\n| Name | Direction | Description |\n| --- | --- | --- |\n");
    for parameter in document.parameters {
        writer.line(format_args!(
            "| `{}` | in | {} |",
            parameter.name(),
            parameter_details(parameter)
        ));
    }
    writer.blank_line();
    writer.write("#### Returns\n\n");
    match document.returns {
        docs::Returns::Scalar(field) => {
            writer.write(format_args!("{}\n\n", parameter_details(field)));
        }
        docs::Returns::Record { .. } => {
            let name = spec
                .result_class()
                .expect("record output has a result class");
            writer.write(format_args!("A `{}` value.\n\n", c_result_name(name)));
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
        writer.line("title: C function index");
    });
    writer.write("# C function index\n\n| Function | Summary | Header |\n| --- | --- | --- |\n");
    for (slug, function) in functions {
        writer.line(format_args!(
            "| [`{0}`](headers/{1}.md#{2}) | {3} | [`<ptfkit/{1}.h>`](headers/{1}.md) |",
            function.core.name,
            slug,
            function_anchor(&function.core.name),
            escape_table(docs::for_function(spec(function)).summary),
        ));
    }
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
        spec.inputs
            .iter()
            .map(|input| match input.enum_type() {
                Some(definition) => format!(
                    "{} {}",
                    c_enum_name(&function.entry.slug, &definition.name),
                    input.name()
                ),
                None => format!("double {}", input.name()),
            })
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

fn parameter_details(parameter: &impl docs::ParameterMetadata) -> String {
    escape_table(&docs::parameter_details(parameter))
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
    crate::targets::python::natural_sort_key(value)
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
            crate::compile::functions(entries).expect("repository specifications compile");
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
        let mut writer = Writer::new();
        render_admonition(&mut writer, "note", "Keep `value` in range.");
        render_admonition(&mut writer, "warning", "Do not use | as a separator.");
        assert_eq!(
            writer.into_string(),
            "!!! note\n\n    Keep \\`value\\` in range.\n\n!!! warning\n\n    Do not use | as a separator.\n\n"
        );
    }
}
