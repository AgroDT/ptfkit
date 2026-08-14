mod c_expression;
mod compile;
mod documentation;
mod native;
mod py;
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
    pub(super) const ALL: [Self; 9] = [
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
    let compiled = compile::functions(entries)?;
    let rust = rs::render(&compiled)?
        .into_iter()
        .map(|(path, contents)| GeneratedFile::new(path, contents))
        .collect::<Vec<_>>();
    let py = py::render(&compiled)?;
    let native = native::render(&compiled)?;
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
