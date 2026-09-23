use std::collections::{BTreeMap, BTreeSet};

use crate::{
    model::{CompiledFunction, Entry, EnumDefinition},
    output::GeneratedFile,
    render::{Render, Writer, markdown},
    targets::{python::natural_sort_key, shared_enum_groups},
};

pub(crate) fn render(entries: &[Entry], functions: &[CompiledFunction]) -> Vec<GeneratedFile> {
    let mut entries = entries.iter().collect::<Vec<_>>();
    entries.sort_by_key(|entry| natural_sort_key(&entry.slug));
    let shared = shared_enum_groups(functions);
    let mut source_shared = BTreeMap::<&str, BTreeSet<(&str, &str)>>::new();
    for function in functions {
        for definition in function.entry.spec.functions[function.function_index]
            .inputs
            .iter()
            .filter_map(|input| input.enum_type())
        {
            if let Some(module) = definition.shared_document() {
                source_shared
                    .entry(&function.entry.slug)
                    .or_default()
                    .insert((module, &definition.enum_type.name));
            }
        }
    }

    let mut files = vec![markdown::markdown_file("index.md", |writer| {
        IndexPage {
            entries: &entries,
            shared: &shared,
        }
        .render(writer);
    })];
    for module in shared.keys() {
        files.push(markdown::markdown_file(format!("{module}.md"), |writer| {
            markdown::generated_frontmatter(writer, |writer| {
                writer.line(format_args!("title: Python module ptfkit.{module}"));
                writer.line(format_args!("nav-title: ptfkit.{module}"));
            });
            writer.line(format_args!("::: ptfkit.{module}"));
        }));
    }
    for entry in entries {
        files.push(markdown::markdown_file(
            format!("{}.md", entry.slug),
            |writer| {
                ModulePage {
                    entry,
                    shared: source_shared.get(entry.slug.as_str()),
                }
                .render(writer)
            },
        ));
    }
    files
}

struct IndexPage<'a> {
    entries: &'a [&'a Entry],
    shared: &'a BTreeMap<&'a str, Vec<&'a EnumDefinition>>,
}

impl Render for IndexPage<'_> {
    fn render(&self, writer: &mut Writer) {
        markdown::generated_frontmatter(writer, |writer| {
            writer.line("title: Python API reference");
        });
        writer.write(
            "# Python API reference\n\nptfkit's Python API is organized around public modules.\n\n",
        );
        if !self.shared.is_empty() {
            writer.write("## Shared domain modules\n\n");
            for module in self.shared.keys() {
                writer.line(format_args!("- [`ptfkit.{module}`]({module}.md)"));
            }
            writer.blank_line();
        }
        writer.write("## Source modules\n\n");
        for entry in self.entries {
            ModuleReference { entry }.render(writer);
        }
    }
}

struct ModulePage<'a> {
    entry: &'a Entry,
    shared: Option<&'a BTreeSet<(&'a str, &'a str)>>,
}

impl Render for ModulePage<'_> {
    fn render(&self, writer: &mut Writer) {
        let slug = &self.entry.slug;
        let module = format!("ptfkit.{slug}");
        markdown::generated_frontmatter(writer, |writer| {
            writer.line(format_args!("title: Python module {module}"));
            writer.line(format_args!("nav-title: {module}"));
        });
        if let Some(shared) = self.shared {
            writer.write("Shared types: ");
            for (index, (module, name)) in shared.iter().enumerate() {
                if index > 0 {
                    writer.write(", ");
                }
                writer.write(format_args!(
                    "[`ptfkit.{module}.{name}`]({module}.md#ptfkit.{module}.{name})"
                ));
            }
            writer.write(".\n\n");
        }
        writer.line(format_args!("::: {module}"));
    }
}

struct ModuleReference<'a> {
    entry: &'a Entry,
}

impl Render for ModuleReference<'_> {
    fn render(&self, writer: &mut Writer) {
        let slug = &self.entry.slug;
        let summary = &self.entry.spec.source.summary;
        writer.line(format_args!("- [`ptfkit.{slug}`]({slug}.md) — {summary}"));
    }
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use crate::model::PythonGeneration;

    use super::*;

    fn rendered_files() -> Vec<GeneratedFile> {
        let entries = crate::test_support::entries();
        render(
            &entries,
            &crate::compile::functions(entries.clone()).unwrap(),
        )
    }

    fn contents<'a>(files: &'a [GeneratedFile], path: &str) -> &'a str {
        &files
            .iter()
            .find(|file| file.path == Path::new(path))
            .unwrap_or_else(|| panic!("missing generated file {path}"))
            .contents
    }

    #[test]
    fn shared_module_has_its_own_page_and_consumer_links() {
        let root = crate::test_support::fixture_root("python-shared-reference");
        crate::test_support::copy_shared_definition_fixture(&root);
        let entries = crate::load_validated_specifications(&root).unwrap();
        let functions = crate::compile::functions(entries.clone()).unwrap();
        let files = render(&entries, &functions);
        assert!(contents(&files, "soil.md").contains("::: ptfkit.soil"));
        assert!(contents(&files, "index.md").contains("[`ptfkit.soil`](soil.md)"));
        for source in ["first_source", "second_source"] {
            assert!(
                contents(&files, &format!("{source}.md"))
                    .contains("[`ptfkit.soil.SharedCategory`](soil.md#ptfkit.soil.SharedCategory)")
            );
        }
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn renders_one_page_for_each_source_module() {
        let entries = crate::test_support::entries();
        let files = render(
            &entries,
            &crate::compile::functions(entries.clone()).unwrap(),
        );
        let index = contents(&files, "index.md");

        assert_eq!(files.len(), entries.len() + 1);
        snapbox::assert_data_eq!(
            index,
            snapbox::file!["../../fixtures/expected/reference/python/index.md"]
        );
        snapbox::assert_data_eq!(
            contents(&files, "example10.md"),
            snapbox::str![
                "---\n# @generated by ptfkit-codegen; DO NOT EDIT.\n\ntitle: Python module ptfkit.example10\nnav-title: ptfkit.example10\n---\n\n::: ptfkit.example10\n\n"
            ]
        );
        snapbox::assert_data_eq!(
            contents(&files, "example2.md"),
            snapbox::str![
                "---\n# @generated by ptfkit-codegen; DO NOT EDIT.\n\ntitle: Python module ptfkit.example2\nnav-title: ptfkit.example2\n---\n\n::: ptfkit.example2\n\n"
            ]
        );
    }

    #[test]
    fn includes_intentional_manual_public_modules() {
        let mut entries = crate::test_support::entries();
        let manual = entries
            .iter_mut()
            .find(|entry| entry.slug == "example2")
            .unwrap();
        manual.spec.generation.public_python = PythonGeneration::Manual;
        let files = render(
            &entries,
            &crate::compile::functions(entries.clone()).unwrap(),
        );

        assert!(contents(&files, "example2.md").contains("::: ptfkit.example2"));
    }

    #[test]
    fn excludes_private_implementation_modules() {
        let files = rendered_files();
        let index = contents(&files, "index.md");

        assert!(!index.contains("_ptfkit"));
        assert!(!index.contains("__init__"));
        assert!(files.iter().all(|file| {
            file.path
                .extension()
                .is_some_and(|extension| extension == "md")
        }));
    }
}
