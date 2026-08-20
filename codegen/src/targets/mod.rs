mod c_documentation;
mod c_expression;
mod compile;
mod cpp_documentation;
mod documentation;
mod native;
mod py;
mod python_documentation;
mod rs;
mod write;

use std::{
    collections::BTreeMap,
    path::{Path, PathBuf},
};

use anyhow::Result;

use crate::model::{CompiledFunction, Entry, PythonGeneration};

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

#[derive(Clone, Copy, PartialEq, Eq)]
pub(super) enum Formatter {
    None,
    Rust,
    Python,
    C,
    Cpp,
}

pub(super) struct Layout {
    pub(super) output_directory: &'static str,
    pub(super) cleanup_directory: &'static str,
    pub(super) generated_header: &'static str,
    pub(super) formatter: Formatter,
}

macro_rules! layout {
    (
        $name:ident,
        $output_directory:literal,
        $cleanup_directory:literal,
        $generated_header:path,
        $formatter:path,
    ) => {
        pub(super) static $name: Layout = Layout {
            output_directory: $output_directory,
            cleanup_directory: $cleanup_directory,
            generated_header: $generated_header,
            formatter: $formatter,
        };
    };
}

layout!(
    DOCUMENTATION,
    "docs/src/ptf-catalog/sources",
    "docs/src/ptf-catalog/sources",
    documentation::HEADER,
    Formatter::None,
);
layout!(
    C_DOCUMENTATION,
    "docs/src/reference/c",
    "docs/src/reference/c",
    documentation::HEADER,
    Formatter::None,
);
layout!(
    CPP_DOCUMENTATION,
    "docs/src/reference/cpp",
    "docs/src/reference/cpp",
    documentation::HEADER,
    Formatter::None,
);
layout!(
    PYTHON_DOCUMENTATION,
    "docs/src/reference/python",
    "docs/src/reference/python",
    documentation::HEADER,
    Formatter::None,
);
layout!(
    RUST,
    "targets/ptfkit-rs/src",
    "targets/ptfkit-rs/src",
    rs::HEADER,
    Formatter::Rust,
);
layout!(
    PYTHON_EXTENSION,
    "targets/ptfkit-py",
    "targets/ptfkit-py/src/ptfkit",
    py::C_HEADER,
    Formatter::C,
);
layout!(
    PYTHON_WRAPPER,
    "targets/ptfkit-py/src",
    "targets/ptfkit-py/src/ptfkit",
    py::WRAPPER_HEADER,
    Formatter::Python,
);
layout!(
    PYTHON_TEST,
    "targets/ptfkit-py",
    "targets/ptfkit-py/tests",
    py::WRAPPER_HEADER,
    Formatter::Python,
);
layout!(
    NATIVE_C,
    "targets/ptfkit-native/include",
    "targets/ptfkit-native/include",
    native::HEADER,
    Formatter::Cpp,
);
layout!(
    NATIVE_CPP_MODULE,
    "targets/ptfkit-native/cpp",
    "targets/ptfkit-native/cpp",
    native::HEADER,
    Formatter::Cpp,
);
layout!(
    NATIVE_CPP_CMAKE,
    "targets/ptfkit-native/cmake",
    "targets/ptfkit-native/cmake",
    native::CMAKE_HEADER,
    Formatter::None,
);
layout!(
    NATIVE_C_TEST,
    "targets/ptfkit-native/tests/c",
    "targets/ptfkit-native/tests/c",
    native::HEADER,
    Formatter::C,
);
layout!(
    NATIVE_CPP_TEST,
    "targets/ptfkit-native/tests/cpp",
    "targets/ptfkit-native/tests/cpp",
    native::HEADER,
    Formatter::Cpp,
);

pub(super) const LAYOUTS: [&Layout; 13] = [
    &DOCUMENTATION,
    &C_DOCUMENTATION,
    &CPP_DOCUMENTATION,
    &PYTHON_DOCUMENTATION,
    &RUST,
    &PYTHON_EXTENSION,
    &PYTHON_WRAPPER,
    &PYTHON_TEST,
    &NATIVE_C,
    &NATIVE_CPP_MODULE,
    &NATIVE_CPP_CMAKE,
    &NATIVE_C_TEST,
    &NATIVE_CPP_TEST,
];

pub(super) struct Output {
    pub(super) layout: &'static Layout,
    pub(super) files: Vec<GeneratedFile>,
}

impl Output {
    fn new(layout: &'static Layout, files: Vec<GeneratedFile>) -> Self {
        Self { layout, files }
    }
}

pub(super) struct GeneratedFile {
    path: PathBuf,
    contents: String,
}

impl GeneratedFile {
    fn new(path: PathBuf, contents: String) -> Self {
        Self { path, contents }
    }
}

pub(crate) fn run(root: &Path, entries: Vec<Entry>) -> Result<()> {
    let documentation = documentation::render(&entries);
    let python_documentation = python_documentation::render(&entries);
    let compiled = compile::functions(entries)?;
    let rust = rs::render(&compiled)?;
    let py = py::render(&compiled)?;
    let native = native::render(&compiled)?;
    let c_documentation = c_documentation::render(&compiled)?;
    let cpp_documentation = cpp_documentation::render(&compiled)?;
    let c = py
        .c_sources
        .into_iter()
        .map(|(path, contents)| GeneratedFile::new(path.into(), contents))
        .collect::<Vec<_>>();
    let mut wrappers = py
        .wrappers
        .into_iter()
        .filter_map(|(module, mode, contents)| {
            (mode == PythonGeneration::Generated).then_some(GeneratedFile::new(
                PathBuf::from(module.replace('.', "/")).with_extension("py"),
                contents,
            ))
        })
        .collect::<Vec<_>>();
    wrappers.push(GeneratedFile::new("ptfkit/_ptfkit.pyi".into(), py.stub));
    let tests = py
        .tests
        .into_iter()
        .filter_map(|(slug, mode, contents)| {
            (mode == PythonGeneration::Generated).then_some(GeneratedFile::new(
                format!("tests/test_{slug}.py").into(),
                contents,
            ))
        })
        .collect::<Vec<_>>();
    write::commit(
        root,
        &[
            Output::new(&DOCUMENTATION, documentation),
            Output::new(&C_DOCUMENTATION, c_documentation),
            Output::new(&CPP_DOCUMENTATION, cpp_documentation),
            Output::new(&PYTHON_DOCUMENTATION, python_documentation),
            Output::new(&RUST, rust),
            Output::new(&PYTHON_EXTENSION, c),
            Output::new(&PYTHON_WRAPPER, wrappers),
            Output::new(&PYTHON_TEST, tests),
            Output::new(&NATIVE_C, native.c_headers),
            Output::new(&NATIVE_CPP_MODULE, native.cpp_modules),
            Output::new(&NATIVE_CPP_CMAKE, native.cpp_cmake),
            Output::new(&NATIVE_C_TEST, native.c_tests),
            Output::new(&NATIVE_CPP_TEST, native.cpp_tests),
        ],
    )
}

/// Regenerate every target and fail when that changes a codegen-owned file.
pub(crate) fn check_generated(root: &Path, entries: Vec<Entry>) -> Result<()> {
    let before = write::snapshot_generated(root)?;
    run(root, entries)?;
    write::assert_unchanged(root, before)
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::{
        C_DOCUMENTATION, CPP_DOCUMENTATION, DOCUMENTATION, PYTHON_DOCUMENTATION, PYTHON_EXTENSION,
        PYTHON_WRAPPER,
    };

    #[test]
    fn documentation_targets_use_structured_mkdocs_roots() {
        let root = Path::new("repository");
        let relative = Path::new("index.md");

        for (layout, directory) in [
            (&DOCUMENTATION, "docs/src/ptf-catalog/sources"),
            (&C_DOCUMENTATION, "docs/src/reference/c"),
            (&CPP_DOCUMENTATION, "docs/src/reference/cpp"),
            (&PYTHON_DOCUMENTATION, "docs/src/reference/python"),
        ] {
            assert_eq!(
                root.join(layout.output_directory).join(relative),
                root.join(directory).join(relative)
            );
            assert_eq!(root.join(layout.cleanup_directory), root.join(directory));
        }
    }

    #[test]
    fn python_layouts_keep_extension_cleanup_scoped_to_its_package() {
        assert_eq!(PYTHON_EXTENSION.output_directory, "targets/ptfkit-py");
        assert_eq!(
            PYTHON_EXTENSION.cleanup_directory,
            "targets/ptfkit-py/src/ptfkit"
        );
        assert_eq!(PYTHON_WRAPPER.output_directory, "targets/ptfkit-py/src");
        assert_eq!(
            PYTHON_WRAPPER.cleanup_directory,
            "targets/ptfkit-py/src/ptfkit"
        );
    }
}
