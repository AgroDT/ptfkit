//! Render concrete generated products from compiled specifications.

mod catalog;
mod native;
mod python;
mod reference;
mod rust;

use std::{collections::BTreeMap, path::Path};

mod error;
pub(crate) use error::GenerationError;
type Result<T> = std::result::Result<T, GenerationError>;

use crate::{
    compile,
    model::{CompiledFunction, Output as FunctionOutput},
    output::{self, Output},
    semantic::VariableValue,
    specs::LoadedSpecifications,
};

pub(super) fn record_types(
    functions: &[&CompiledFunction],
) -> Result<BTreeMap<String, Vec<String>>> {
    let mut records = BTreeMap::new();
    for function in functions {
        if let FunctionOutput::Struct(fields) = &function.core.output {
            let name = function.entry.spec.functions[function.function_index]
                .result_class()
                .expect("record output has a result class");
            insert_record_type(&mut records, name, fields)?;
        }
        for lookup in function.ir.variables.iter().filter_map(|variable| {
            if let VariableValue::RecordLookup(lookup) = &variable.value {
                Some(lookup)
            } else {
                None
            }
        }) {
            insert_record_type(&mut records, &lookup.output.name, &lookup.output.fields)?;
        }
        for tree in function.ir.variables.iter().filter_map(|variable| {
            if let VariableValue::Tree(tree) = &variable.value {
                Some(tree)
            } else {
                None
            }
        }) {
            if let crate::semantic::ValueType::Record(record) = &tree.definition.output {
                insert_record_type(&mut records, &record.name, &record.fields)?;
            }
        }
    }
    Ok(records)
}

fn insert_record_type(
    records: &mut BTreeMap<String, Vec<String>>,
    name: &str,
    fields: &[String],
) -> Result<()> {
    if let Some(previous) = records.get(name)
        && previous != fields
    {
        return Err(GenerationError::ConflictingRecordFields {
            name: name.to_owned(),
        });
    }
    records.insert(name.to_owned(), fields.to_vec());
    Ok(())
}

#[cfg(test)]
pub(crate) fn render_rust_for_test(
    functions: &[CompiledFunction],
) -> Result<Vec<output::GeneratedFile>> {
    rust::render(functions)
}

#[cfg(test)]
pub(crate) fn render_native_for_test(
    functions: &[CompiledFunction],
) -> Result<(Vec<output::GeneratedFile>, Vec<output::GeneratedFile>)> {
    let rendered = native::render(functions)?;
    Ok((rendered.c_headers, rendered.cpp_modules))
}

#[cfg(test)]
pub(crate) fn render_python_extension_for_test(
    functions: &[CompiledFunction],
) -> Result<Vec<output::GeneratedFile>> {
    Ok(python::render(functions)?.extension)
}

pub(super) fn group_by_source(
    functions: &[CompiledFunction],
) -> BTreeMap<&str, Vec<&CompiledFunction>> {
    let mut sources: BTreeMap<&str, Vec<&CompiledFunction>> = BTreeMap::new();
    for function in functions {
        sources
            .entry(function.entry.slug.as_str())
            .or_default()
            .push(function);
    }
    sources
}

pub(super) fn shared_enum_groups<'a>(
    functions: impl IntoIterator<Item = &'a CompiledFunction>,
) -> BTreeMap<&'a str, Vec<&'a crate::model::EnumDefinition>> {
    let mut groups = BTreeMap::<_, Vec<_>>::new();
    let mut seen = std::collections::BTreeSet::new();
    for definition in functions.into_iter().flat_map(|function| {
        function.entry.spec.functions[function.function_index]
            .inputs
            .iter()
            .filter_map(|input| input.enum_type())
    }) {
        if let Some(module) = definition.shared_document()
            && seen.insert(definition.identity())
        {
            groups.entry(module).or_default().push(definition);
        }
    }
    groups
}

pub(crate) fn run(root: &Path, loaded: LoadedSpecifications) -> anyhow::Result<()> {
    let LoadedSpecifications {
        entries,
        definitions,
    } = loaded;
    let catalog = catalog::render(&entries, &definitions);
    let compiled = compile::functions(entries.clone())?;
    let reference_python = reference::python::render(&entries, &compiled);
    let reference_c = reference::c::render(&compiled)?;
    let reference_cpp = reference::cpp::render(&compiled)?;
    let rust = rust::render_with_definitions(&compiled, &definitions)?;
    let python = python::render_with_definitions(&compiled, &definitions)?;
    let native = native::render_with_definitions(&compiled, &definitions)?;

    output::commit(
        root,
        &[
            Output::new(&output::CATALOG, catalog.sources),
            Output::new(&output::CATALOG_DEFINITIONS, catalog.definitions),
            Output::new(&output::REFERENCE_C, reference_c),
            Output::new(&output::REFERENCE_CPP, reference_cpp),
            Output::new(&output::REFERENCE_PYTHON, reference_python),
            Output::new(&output::RUST, rust),
            Output::new(&output::PYTHON_EXTENSION, python.extension),
            Output::new(&output::PYTHON_WRAPPER, python.wrappers),
            Output::new(&output::PYTHON_TEST, python.tests),
            Output::new(&output::NATIVE_C, native.c_headers),
            Output::new(&output::NATIVE_CPP_MODULE, native.cpp_modules),
            Output::new(&output::NATIVE_C_TEST, native.c_tests),
            Output::new(&output::NATIVE_CPP_TEST, native.cpp_tests),
        ],
    )
}

/// Regenerate every target and fail when that changes a codegen-owned file.
pub(crate) fn check_generated(root: &Path, loaded: LoadedSpecifications) -> anyhow::Result<()> {
    let before = output::snapshot_generated(root)?;
    run(root, loaded)?;
    output::assert_unchanged(root, before)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shared_document_description_reaches_catalog_and_generated_modules() {
        let root = crate::test_support::fixture_root("shared-document-description");
        crate::test_support::copy_shared_definition_fixture(&root);
        let loaded = crate::specs::load_all(&root).unwrap();
        let catalog = catalog::render(&loaded.entries, &loaded.definitions);
        let page = catalog
            .definitions
            .iter()
            .find(|file| file.path == Path::new("soil.md"))
            .unwrap();
        assert!(
            page.contents
                .contains("Shared soil categories for test sources.")
        );
        assert!(page.contents.contains("### `SharedCategory`"));

        let functions = compile::functions(loaded.entries).unwrap();
        let rust = rust::render_with_definitions(&functions, &loaded.definitions).unwrap();
        let python = python::render_with_definitions(&functions, &loaded.definitions).unwrap();
        let native = native::render_with_definitions(&functions, &loaded.definitions).unwrap();
        let expected = "Shared soil categories for test sources.";
        assert!(
            rust.iter()
                .find(|file| file.path == Path::new("soil.rs"))
                .unwrap()
                .contents
                .contains(expected)
        );
        assert!(
            python
                .wrappers
                .iter()
                .find(|file| file.path == Path::new("ptfkit/soil.py"))
                .unwrap()
                .contents
                .contains(&format!("\"\"\"{expected}\"\"\""))
        );
        assert!(
            native
                .c_headers
                .iter()
                .find(|file| file.path == Path::new("ptfkit/soil.h"))
                .unwrap()
                .contents
                .contains(expected)
        );
        assert!(
            native
                .cpp_modules
                .iter()
                .find(|file| file.path == Path::new("soil.cppm"))
                .unwrap()
                .contents
                .contains(expected)
        );
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn unreferenced_definition_document_still_has_a_catalog_page() {
        let root = crate::test_support::fixture_root("unused-definition-catalog");
        crate::test_support::copy_shared_definition_fixture(&root);
        let soil = std::fs::read_to_string(root.join("specs/definitions/soil.yaml")).unwrap();
        std::fs::write(
            root.join("specs/definitions/unused.yaml"),
            soil.replace(
                "Shared soil categories for test sources.",
                "Unused example categories.",
            ),
        )
        .unwrap();
        let loaded = crate::specs::load_all(&root).unwrap();
        let catalog = catalog::render(&loaded.entries, &loaded.definitions);
        let page = catalog
            .definitions
            .iter()
            .find(|file| file.path == Path::new("unused.md"))
            .unwrap();
        assert!(page.contents.contains("Unused example categories."));
        assert!(
            catalog
                .definitions
                .iter()
                .any(|file| file.path == Path::new("index.md")
                    && file.contents.contains("unused.md"))
        );
        let functions = compile::functions(loaded.entries).unwrap();
        assert!(
            !rust::render_with_definitions(&functions, &loaded.definitions)
                .unwrap()
                .iter()
                .any(|file| file.path == Path::new("unused.rs"))
        );
        std::fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn shared_enum_declarations_and_references_preserve_the_defining_module() {
        let root = crate::test_support::fixture_root("shared-rendering");
        crate::test_support::copy_shared_definition_fixture(&root);
        let entries = crate::load_validated_specifications(&root).unwrap();
        let functions = compile::functions(entries).unwrap();
        let native = native::render(&functions).unwrap();
        for (files, shared_path, first_path, second_path, declaration, reference) in [
            (
                rust::render(&functions).unwrap(),
                "soil.rs",
                "first_source.rs",
                "second_source.rs",
                "pubenumSharedCategory",
                "crate::soil::SharedCategory",
            ),
            (
                native.c_headers,
                "ptfkit/soil.h",
                "ptfkit/first_source.h",
                "ptfkit/second_source.h",
                "}ptfkit_soil_shared_category;",
                "ptfkit_soil_shared_categorycategory",
            ),
            (
                native.cpp_modules,
                "soil.cppm",
                "first_source.cppm",
                "second_source.cppm",
                "exportenumclassSharedCategory",
                "ptfkit::soil::SharedCategorycategory",
            ),
            (
                python::render(&functions).unwrap().wrappers,
                "ptfkit/soil.py",
                "ptfkit/first_source.py",
                "ptfkit/second_source.py",
                "classSharedCategory(Enum):",
                "_soil.SharedCategory",
            ),
        ] {
            let text = |path: &str| {
                let matches = files
                    .iter()
                    .filter(|file| file.path == Path::new(path))
                    .collect::<Vec<_>>();
                assert_eq!(matches.len(), 1, "expected one generated {path}");
                matches[0].contents.split_whitespace().collect::<String>()
            };
            assert_eq!(
                text(shared_path).matches(declaration).count(),
                1,
                "{shared_path}"
            );
            for path in [first_path, second_path] {
                assert!(
                    text(path).contains(reference),
                    "{path} must reference its shared type"
                );
            }
            assert!(
                !text(second_path).contains(declaration),
                "{second_path} must not redeclare the shared type"
            );
        }
        let python = python::render(&functions).unwrap().wrappers;
        let generated = |path: &str| {
            &python
                .iter()
                .find(|file| file.path == Path::new(path))
                .unwrap()
                .contents
        };
        assert!(
            generated("ptfkit/soil.py")
                .contains("from typing import TYPE_CHECKING\n\nfrom ptfkit.enums import EnumArray")
        );
        assert!(
            generated("ptfkit/first_source.py")
                .contains("message = 'expected SharedCategory or EnumArray[SharedCategory]'")
        );
        std::fs::remove_dir_all(root).unwrap();
    }
}
