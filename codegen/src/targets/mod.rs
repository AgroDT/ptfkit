mod compile;
mod py;
mod rs;
mod write;

use std::path::{Path, PathBuf};

use anyhow::Result;

use crate::model::{Entry, PythonGeneration};

#[derive(Clone, Copy, PartialEq, Eq)]
pub(super) enum Target {
    Rust,
    PythonExtension,
    PythonWrapper,
}

impl Target {
    pub(super) const ALL: [Self; 3] = [Self::Rust, Self::PythonExtension, Self::PythonWrapper];

    fn output_path(self, root: &Path, relative: &Path) -> PathBuf {
        match self {
            Self::Rust => root.join("targets/ptfkit-rs/src").join(relative),
            Self::PythonExtension => root.join("targets/ptfkit-py").join(relative),
            Self::PythonWrapper => root.join("targets/ptfkit-py/src").join(relative),
        }
    }

    fn cleanup_directory(self, root: &Path) -> PathBuf {
        match self {
            Self::Rust => root.join("targets/ptfkit-rs/src"),
            Self::PythonExtension | Self::PythonWrapper => {
                root.join("targets/ptfkit-py/src/ptfkit")
            }
        }
    }

    fn generated_header(self) -> &'static str {
        match self {
            Self::Rust => rs::HEADER,
            Self::PythonExtension => py::C_HEADER,
            Self::PythonWrapper => py::WRAPPER_HEADER,
        }
    }

    fn format(self, root: &Path, paths: &[PathBuf]) -> Result<()> {
        match self {
            Self::Rust => write::format_rust(paths),
            Self::PythonExtension => Ok(()),
            Self::PythonWrapper => write::format_python(root, paths),
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
    write::commit(
        root,
        [
            TargetOutput::new(Target::Rust, rust),
            TargetOutput::new(Target::PythonExtension, c),
            TargetOutput::new(Target::PythonWrapper, wrappers),
        ],
    )
}
