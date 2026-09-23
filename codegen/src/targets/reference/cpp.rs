use std::{collections::BTreeSet, path::PathBuf};

use crate::targets::{GenerationError, Result};
use convert_case::{Case, Casing};

use crate::{
    documentation::{self as docs},
    model::{CompiledFunction, EnumDefinition, Output, OutputField},
    output::GeneratedFile,
    render::{Writer, markdown},
    targets::{group_by_source, shared_enum_groups},
};

pub(crate) fn render(functions: &[CompiledFunction]) -> Result<Vec<GeneratedFile>> {
    let sources = group_by_source(functions);
    let shared = shared_enum_groups(functions);
    let mut files = vec![markdown::markdown_file("index.md", |writer| {
        render_index(writer, &sources, &shared);
    })];
    files.push(markdown::markdown_file("modules/ptfkit.md", |writer| {
        render_umbrella(writer, &sources, &shared);
    }));

    for (module, definitions) in &shared {
        files.push(markdown::markdown_file(
            format!("modules/{module}.md"),
            |writer| {
                markdown::generated_frontmatter(writer, |writer| {
                    writer.line(format_args!("title: C++ module ptfkit.{module}"));
                    writer.line(format_args!("nav-title: ptfkit.{module}"));
                });
                writer.write(format_args!("# `ptfkit.{module}`\n\n"));
                markdown::code_block(writer, "cpp", |writer| {
                    writer.line(format_args!("import ptfkit.{module};"));
                });
                writer.write(format_args!(
                    "**Exported namespace:** `ptfkit::{module}`\n\n"
                ));
                for definition in definitions {
                    render_enum(writer, definition);
                }
            },
        ));
    }

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
    shared: &std::collections::BTreeMap<&str, Vec<&EnumDefinition>>,
) {
    markdown::generated_frontmatter(writer, |writer| {
        writer.line("title: C++ API reference");
    });
    writer.write("# C++ API reference\n\nptfkit's C++ API is organized around C++23 modules.\n\n## Umbrella module\n\n- [`ptfkit`](modules/ptfkit.md) — Re-exports all public ptfkit modules.\n\n");
    if !shared.is_empty() {
        writer.write("## Shared domain modules\n\n");
        for module in shared.keys() {
            writer.line(format_args!("- [`ptfkit.{module}`](modules/{module}.md)"));
        }
        writer.blank_line();
    }
    writer.write("## Source modules\n\n");
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
    shared: &std::collections::BTreeMap<&str, Vec<&EnumDefinition>>,
) {
    markdown::generated_frontmatter(writer, |writer| {
        writer.line("title: C++ module ptfkit");
        writer.line("nav-title: ptfkit");
    });
    writer.write("# `ptfkit`\n\n");
    markdown::code_block(writer, "cpp", |writer| {
        writer.line("import ptfkit;");
    });
    writer.write(
        "This umbrella module re-exports every public ptfkit module. Import an individual module when only one module is needed.\n\n## Re-exported modules\n\n",
    );
    for module in shared.keys() {
        writer.line(format_args!("- [`ptfkit.{module}`]({module}.md)"));
    }
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
    writer.write(format_args!("# `ptfkit.{slug}`\n\n"));
    markdown::code_block(writer, "cpp", |writer| {
        writer.line(format_args!("import ptfkit.{slug};"));
    });
    writer.write(format_args!(
        "**Exported namespace:** `ptfkit::{slug}`\n\n{}\n\n## Source\n\n{}\n\n",
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

    let shared = functions
        .iter()
        .flat_map(|function| &spec(function).inputs)
        .filter_map(|input| {
            let definition = input.enum_type()?;
            Some((
                definition.shared_document()?,
                definition.enum_type.name.as_str(),
            ))
        })
        .collect::<BTreeSet<_>>();
    if !shared.is_empty() {
        writer.write("## Shared types\n\n");
        for (module, name) in shared {
            writer.line(format_args!(
                "- [`ptfkit::{module}::{name}`]({module}.md#{})",
                name.to_ascii_lowercase()
            ));
        }
        writer.blank_line();
    }

    let mut enums = BTreeSet::new();
    for function in functions {
        for input in &spec(function).inputs {
            if let Some(definition) = input
                .enum_type()
                .filter(|definition| !definition.is_shared())
                && enums.insert(definition.identity().to_owned())
            {
                render_enum(writer, definition);
            }
        }
    }
    let mut structures = BTreeSet::new();
    for function in functions {
        if let Output::Struct(_) = &function.core.output {
            let result = result_class(function)?;
            if structures.insert(result) {
                render_structure(writer, result, spec(function).outputs.fields());
            }
        }
    }
    writer.write("## Functions\n\n");
    for function in functions {
        render_function_documentation(writer, function)?;
    }
    Ok(())
}

fn render_enum(writer: &mut Writer, definition: &EnumDefinition) {
    writer.write(format_args!("## `{}`\n\n", definition.enum_type.name));
    writer.write(format_args!("{}\n\n", escape_text(&definition.description)));
    markdown::code_block(writer, "cpp", |writer| {
        writer.line(format_args!("enum class {} {{", definition.enum_type.name));
        writer.indented(|writer| {
            for member in &definition.values {
                writer.line(format_args!("{},", member.name.to_case(Case::Pascal)));
            }
        });
        writer.line("};");
    });
    writer.line("| Member | Canonical value | Description |");
    writer.line("| --- | --- | --- |");
    for member in &definition.values {
        writer.line(format_args!(
            "| `{}` | `{}` | {} |",
            member.name.to_case(Case::Pascal),
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
    writer.write(format_args!(
        "### `{}` {{#{anchor}}}\n\n{}\n\n",
        function.core.name,
        escape_text(document.summary),
    ));
    let signature = signature(function)?;
    markdown::code_block(writer, "cpp", |writer| {
        writer.line(signature);
    });
    writer.write("#### Parameters\n\n| Name | Description |\n| --- | --- |\n");
    for parameter in document.parameters {
        writer.line(format_args!(
            "| `{}` | {} |",
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
            writer.write(format_args!("A `{}` value.\n\n", result_class(function)?));
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
    writer.write("# C++ function index\n\n| Function | Summary | Module |\n| --- | --- | --- |\n");
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
    let spec = spec(function);
    let result = match &function.core.output {
        Output::Scalar => "double".to_owned(),
        Output::Struct(_) => result_class(function)?.to_owned(),
    };
    Ok(format!(
        "[[nodiscard]]\ninline {result} {}({})",
        function.core.name,
        spec.inputs
            .iter()
            .map(|input| match input.enum_type() {
                Some(definition) => format!(
                    "{} {}",
                    crate::targets::native::cpp_enum_type_name(&definition.enum_type),
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

fn result_class(function: &CompiledFunction) -> Result<&str> {
    spec(function)
        .result_class()
        .ok_or(GenerationError::MissingResultClass)
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
        let mut entries = crate::test_support::entries();
        entries.reverse();
        let compiled = crate::compile::functions(entries).expect("test specifications compile");
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
    fn shared_enum_is_documented_at_its_module_and_linked_from_consumers() {
        let root = crate::test_support::fixture_root("cpp-shared-reference");
        crate::test_support::copy_shared_definition_fixture(&root);
        let entries = crate::load_validated_specifications(&root).unwrap();
        let functions = crate::compile::functions(entries).unwrap();
        let files = render(&functions).unwrap();
        let shared = contents(&files, "modules/soil.md");
        assert!(shared.contains("## `SharedCategory`"));
        assert!(shared.contains("Shared category."));
        let index = contents(&files, "index.md");
        assert!(index.contains("modules/soil.md"));
        assert!(index.find("## Umbrella module") < index.find("## Shared domain modules"));
        assert!(index.find("## Shared domain modules") < index.find("## Source modules"));
        for source in ["first_source", "second_source"] {
            let page = contents(&files, &format!("modules/{source}.md"));
            assert!(page.contains("[`ptfkit::soil::SharedCategory`](soil.md#sharedcategory)"));
            assert_eq!(
                page.contains("## `SharedCategory`"),
                source == "first_source"
            );
        }
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn documents_modules_functions_and_record_fields_from_compiled_sources() {
        let files = rendered_files();
        let index = contents(&files, "index.md");
        let page = contents(&files, "modules/example2.md");
        let function_index = contents(&files, "functions.md");

        snapbox::assert_data_eq!(
            index,
            snapbox::file!["../../fixtures/expected/reference/cpp/index.md"]
        );
        snapbox::assert_data_eq!(
            page,
            snapbox::file!["../../fixtures/expected/reference/cpp/example2.md"]
        );
        snapbox::assert_data_eq!(
            function_index,
            snapbox::file!["../../fixtures/expected/reference/cpp/functions.md"]
        );
    }

    #[test]
    fn umbrella_lists_each_source_module_once_in_slug_order() {
        let files = rendered_files();
        let umbrella = contents(&files, "modules/ptfkit.md");
        assert_eq!(
            umbrella
                .lines()
                .filter(|line| line.starts_with("- [`ptfkit."))
                .collect::<Vec<_>>(),
            [
                "- [`ptfkit.example10`](example10.md) — Synthetic rendering example10.",
                "- [`ptfkit.example2`](example2.md) — Synthetic rendering example2."
            ]
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
            function_anchor("calc_ptf_example2"),
            "function-calc_ptf_example2"
        );
    }

    #[test]
    fn natural_ordering_handles_numeric_suffixes() {
        assert!(natural_sort_key("calc_2") < natural_sort_key("calc_10"));
    }
}
