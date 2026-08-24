//! Render concrete generated products from compiled specifications.

mod catalog;
mod native;
mod python;
mod reference;
mod rust;

use std::{collections::BTreeMap, path::Path};

use anyhow::Result;

use crate::{
    compile,
    model::{CompiledFunction, Entry, Output as FunctionOutput},
    output::{self, Output},
    semantic::VariableValue,
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
        anyhow::bail!("record type `{name}` has conflicting field definitions");
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

pub(crate) fn run(root: &Path, entries: Vec<Entry>) -> Result<()> {
    let catalog = catalog::render(&entries);
    let reference_python = reference::python::render(&entries);
    let compiled = compile::functions(entries)?;
    let reference_c = reference::c::render(&compiled)?;
    let reference_cpp = reference::cpp::render(&compiled)?;
    let rust = rust::render(&compiled)?;
    let python = python::render(&compiled)?;
    let native = native::render(&compiled)?;

    output::commit(
        root,
        &[
            Output::new(&output::CATALOG, catalog),
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
pub(crate) fn check_generated(root: &Path, entries: Vec<Entry>) -> Result<()> {
    let before = output::snapshot_generated(root)?;
    run(root, entries)?;
    output::assert_unchanged(root, before)
}
