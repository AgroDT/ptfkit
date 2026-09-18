use std::fmt;

use crate::{formula, semantic, specs::SpecificationError, validate::ValidationError};

#[derive(Debug, thiserror::Error)]
pub(crate) enum Diagnostic {
    #[error(transparent)]
    Parse(#[from] formula::ParseError),
    #[error(transparent)]
    Semantic(#[from] Box<semantic::Error>),
    #[error(transparent)]
    Specification(Box<SpecificationError>),
    #[error(transparent)]
    Validation(Box<ValidationError>),
}

impl From<SpecificationError> for Diagnostic {
    fn from(error: SpecificationError) -> Self {
        Self::Specification(Box::new(error))
    }
}

impl From<ValidationError> for Diagnostic {
    fn from(error: ValidationError) -> Self {
        Self::Validation(Box::new(error))
    }
}

#[derive(Debug)]
enum ReportScope {
    Specifications,
    SharedDefinitions,
}

#[derive(Debug, thiserror::Error)]
pub(crate) struct ValidationReport {
    scope: ReportScope,
    pub(crate) diagnostics: Vec<Diagnostic>,
}

impl ValidationReport {
    pub(crate) fn specifications(diagnostics: Vec<Diagnostic>) -> Self {
        Self {
            scope: ReportScope::Specifications,
            diagnostics,
        }
    }

    pub(crate) fn shared_definitions(diagnostics: Vec<Diagnostic>) -> Self {
        Self {
            scope: ReportScope::SharedDefinitions,
            diagnostics,
        }
    }
}

impl fmt::Display for ValidationReport {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self.scope {
            ReportScope::Specifications => "validation failed:",
            ReportScope::SharedDefinitions => "invalid shared definitions:",
        })?;
        for diagnostic in &self.diagnostics {
            write!(formatter, "\n{diagnostic}")?;
        }
        Ok(())
    }
}
