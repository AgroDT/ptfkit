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
    model::{CompiledFunction, Entry},
    output::{self, Output},
};

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
            Output::new(&output::NATIVE_CPP_CMAKE, native.cpp_cmake),
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
