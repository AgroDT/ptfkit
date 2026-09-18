use std::{fmt, path::PathBuf, process::ExitStatus};

#[derive(Debug, thiserror::Error)]
pub(crate) struct GeneratedDrift {
    pub(crate) added: Vec<PathBuf>,
    pub(crate) removed: Vec<PathBuf>,
    pub(crate) modified: Vec<PathBuf>,
}

impl fmt::Display for GeneratedDrift {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("generated output drift after regeneration:")?;
        for (label, paths) in [
            ("added", &self.added),
            ("removed", &self.removed),
            ("modified", &self.modified),
        ] {
            if !paths.is_empty() {
                write!(formatter, "\n{label}:")?;
                for path in paths {
                    write!(formatter, "\n  {}", path.display())?;
                }
            }
        }
        Ok(())
    }
}

#[derive(Debug, thiserror::Error)]
#[error("{program} failed ({status}):\n{stderr}", stderr = .stderr.trim())]
pub(crate) struct FormatterFailure {
    pub(crate) program: String,
    pub(crate) status: ExitStatus,
    pub(crate) stderr: String,
}

impl FormatterFailure {
    pub(crate) fn from_output(program: impl Into<String>, output: std::process::Output) -> Self {
        Self {
            program: program.into(),
            status: output.status,
            stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
        }
    }
}
