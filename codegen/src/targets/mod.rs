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
pub(super) enum Target {
    Documentation,
    CDocumentation,
    CppDocumentation,
    PythonDocumentation,
    Rust,
    PythonExtension,
    PythonWrapper,
    PythonTest,
    NativeC,
    NativeCppModule,
    NativeCppCmake,
    NativeCTest,
    NativeCppTest,
}

impl Target {
    pub(super) const ALL: [Self; 13] = [
        Self::Documentation,
        Self::CDocumentation,
        Self::CppDocumentation,
        Self::PythonDocumentation,
        Self::Rust,
        Self::PythonExtension,
        Self::PythonWrapper,
        Self::PythonTest,
        Self::NativeC,
        Self::NativeCppModule,
        Self::NativeCppCmake,
        Self::NativeCTest,
        Self::NativeCppTest,
    ];

    fn output_path(self, root: &Path, relative: &Path) -> PathBuf {
        match self {
            Self::Documentation => root.join("docs/src/ptf-catalog/sources").join(relative),
            Self::CDocumentation => root.join("docs/src/reference/c").join(relative),
            Self::CppDocumentation => root.join("docs/src/reference/cpp").join(relative),
            Self::PythonDocumentation => root.join("docs/src/reference/python").join(relative),
            Self::Rust => root.join("targets/ptfkit-rs/src").join(relative),
            Self::PythonExtension => root.join("targets/ptfkit-py").join(relative),
            Self::PythonWrapper => root.join("targets/ptfkit-py/src").join(relative),
            Self::PythonTest => root.join("targets/ptfkit-py").join(relative),
            Self::NativeC => root.join("targets/ptfkit-native/include").join(relative),
            Self::NativeCppModule => root.join("targets/ptfkit-native/cpp").join(relative),
            Self::NativeCppCmake => root.join("targets/ptfkit-native/cmake").join(relative),
            Self::NativeCTest => root.join("targets/ptfkit-native/tests/c").join(relative),
            Self::NativeCppTest => root.join("targets/ptfkit-native/tests/cpp").join(relative),
        }
    }

    fn cleanup_directory(self, root: &Path) -> PathBuf {
        match self {
            Self::Documentation => root.join("docs/src/ptf-catalog/sources"),
            Self::CDocumentation => root.join("docs/src/reference/c"),
            Self::CppDocumentation => root.join("docs/src/reference/cpp"),
            Self::PythonDocumentation => root.join("docs/src/reference/python"),
            Self::Rust => root.join("targets/ptfkit-rs/src"),
            Self::PythonExtension | Self::PythonWrapper => {
                root.join("targets/ptfkit-py/src/ptfkit")
            }
            Self::PythonTest => root.join("targets/ptfkit-py/tests"),
            Self::NativeC => root.join("targets/ptfkit-native/include"),
            Self::NativeCppModule => root.join("targets/ptfkit-native/cpp"),
            Self::NativeCppCmake => root.join("targets/ptfkit-native/cmake"),
            Self::NativeCTest => root.join("targets/ptfkit-native/tests/c"),
            Self::NativeCppTest => root.join("targets/ptfkit-native/tests/cpp"),
        }
    }

    fn generated_header(self) -> &'static str {
        match self {
            Self::Documentation => documentation::HEADER,
            Self::CDocumentation => documentation::HEADER,
            Self::CppDocumentation => documentation::HEADER,
            Self::PythonDocumentation => documentation::HEADER,
            Self::Rust => rs::HEADER,
            Self::PythonExtension => py::C_HEADER,
            Self::PythonWrapper => py::WRAPPER_HEADER,
            Self::PythonTest => py::WRAPPER_HEADER,
            Self::NativeC | Self::NativeCppModule | Self::NativeCTest | Self::NativeCppTest => {
                native::HEADER
            }
            Self::NativeCppCmake => native::CMAKE_HEADER,
        }
    }

    fn is_clang_formatted(self) -> bool {
        matches!(
            self,
            Self::PythonExtension
                | Self::NativeC
                | Self::NativeCppModule
                | Self::NativeCTest
                | Self::NativeCppTest
        )
    }

    fn format(self, root: &Path, paths: &[PathBuf]) -> Result<()> {
        match self {
            Self::Documentation
            | Self::CDocumentation
            | Self::CppDocumentation
            | Self::PythonDocumentation => Ok(()),
            Self::Rust => write::format_rust(paths),
            Self::PythonExtension | Self::NativeCTest => write::format_c(paths),
            Self::PythonWrapper => write::format_python(root, paths),
            Self::PythonTest => write::format_python(root, paths),
            Self::NativeC | Self::NativeCppModule | Self::NativeCppTest => write::format_cpp(paths),
            Self::NativeCppCmake => Ok(()),
        }
    }
}

pub(super) struct TargetOutput {
    pub(super) target: Target,
    pub(super) files: Vec<GeneratedFile>,
}

impl TargetOutput {
    fn new(target: Target, files: Vec<GeneratedFile>) -> Self {
        Self { target, files }
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
    let rust = rs::render(&compiled)?
        .into_iter()
        .map(|(path, contents)| GeneratedFile::new(path, contents))
        .collect::<Vec<_>>();
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
            TargetOutput::new(Target::Documentation, documentation),
            TargetOutput::new(Target::CDocumentation, c_documentation),
            TargetOutput::new(Target::CppDocumentation, cpp_documentation),
            TargetOutput::new(Target::PythonDocumentation, python_documentation),
            TargetOutput::new(Target::Rust, rust),
            TargetOutput::new(Target::PythonExtension, c),
            TargetOutput::new(Target::PythonWrapper, wrappers),
            TargetOutput::new(Target::PythonTest, tests),
            TargetOutput::new(Target::NativeC, native.c_headers),
            TargetOutput::new(Target::NativeCppModule, native.cpp_modules),
            TargetOutput::new(Target::NativeCppCmake, native.cpp_cmake),
            TargetOutput::new(Target::NativeCTest, native.c_tests),
            TargetOutput::new(Target::NativeCppTest, native.cpp_tests),
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

    use super::Target;

    #[test]
    fn documentation_targets_use_structured_mkdocs_roots() {
        let root = Path::new("repository");
        let relative = Path::new("index.md");

        for (target, directory) in [
            (Target::Documentation, "docs/src/ptf-catalog/sources"),
            (Target::CDocumentation, "docs/src/reference/c"),
            (Target::CppDocumentation, "docs/src/reference/cpp"),
            (Target::PythonDocumentation, "docs/src/reference/python"),
        ] {
            assert_eq!(
                target.output_path(root, relative),
                root.join(directory).join(relative)
            );
            assert_eq!(target.cleanup_directory(root), root.join(directory));
        }
    }
}
