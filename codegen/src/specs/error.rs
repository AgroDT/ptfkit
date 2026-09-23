use std::path::{Path, PathBuf};

use crate::model::Function;

#[derive(Debug, thiserror::Error)]
pub(crate) enum SpecificationError {
    #[error("shared definition module `{module}` in {path} uses a reserved target module name", path = .path.display())]
    ReservedModule { module: String, path: PathBuf },
    #[error("shared definition module `{module}` in {definition} conflicts with source module {path}", definition = .definition.display(), path = .path.display())]
    ModuleCollision {
        module: String,
        definition: PathBuf,
        path: PathBuf,
    },
    #[error("{path}:\n  $:\n    {kind}", path = .path.display())]
    Document {
        path: PathBuf,
        #[source]
        kind: DocumentError,
    },
    #[error("{path}:\n  {location}:\n    {source}", path = .path.display())]
    Schema {
        path: PathBuf,
        location: String,
        #[source]
        source: jsonschema::ValidationError<'static>,
    },
    #[error("{path}:\n  $:\n    specification filename must have a UTF-8 stem", path = .path.display())]
    NonUtf8Slug { path: PathBuf },
    #[error("{path}:\n  $:\n    specification filename stem must be an APA-style slug matching ^[a-z][a-z0-9_]*$", path = .path.display())]
    InvalidSlug { path: PathBuf },
    #[error("{path} -> function {function} -> implementation: required for status `{status}`", path = .path.display())]
    MissingImplementation {
        path: PathBuf,
        function: String,
        status: String,
    },
    #[error("{path} -> function {function} -> implementation.variables[{index}].expr: source location is unavailable", path = .path.display())]
    MissingSourceLocation {
        path: PathBuf,
        function: String,
        index: usize,
    },
    #[error("{path} -> function {function} -> implementation.variables[{index}]: record value type `{record}` does not exactly match the function output record", path = .path.display())]
    RecordOutputMismatch {
        path: PathBuf,
        function: String,
        index: usize,
        record: String,
    },
    #[error("{path} -> function {function} -> implementation.variables: missing final output variables {names:?}", path = .path.display())]
    MissingOutputs {
        path: PathBuf,
        function: String,
        names: Vec<String>,
    },
}

#[derive(Debug, thiserror::Error)]
pub(crate) enum DocumentError {
    #[error("malformed YAML: {0}")]
    Yaml(#[source] serde_yaml::Error),
    #[error("YAML cannot be represented as JSON: {0}")]
    Json(#[source] serde_json::Error),
    #[error("metadata cannot be read: {0}")]
    Metadata(#[source] serde_json::Error),
    #[error(transparent)]
    Reference(#[from] ReferenceError),
    #[error("could not locate formula expression `{expression}` in YAML source")]
    ExpressionNotFound { expression: String },
}

#[derive(Debug, thiserror::Error)]
pub(crate) enum ReferenceError {
    #[error("unsupported reference `{reference}`: expected `file.yaml#/$defs/Name`")]
    InvalidFormat { reference: String },
    #[error("unsupported reference `{reference}`: only relative local files are supported")]
    NonLocal { reference: String },
    #[error("reference `{reference}`: cannot read {path}: {source}", path = .path.display())]
    Read {
        reference: String,
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },
    #[error(
        "unsupported reference `{reference}`: expected a YAML file directly under specs/definitions"
    )]
    OutsideDefinitions { reference: String },
    #[error("reference `{reference}`: definition `{name}` is missing in {path}", path = .path.display())]
    MissingDefinition {
        reference: String,
        name: String,
        path: PathBuf,
    },
    #[error("specification root must be an object")]
    InvalidRoot,
    #[error("specification `$defs` must be an object")]
    InvalidDefinitions,
    #[error(transparent)]
    SourceSlug(#[from] Box<SpecificationError>),
}

impl DocumentError {
    pub(crate) fn at(self, path: impl Into<PathBuf>) -> SpecificationError {
        SpecificationError::Document {
            path: path.into(),
            kind: self,
        }
    }
}

impl SpecificationError {
    pub(crate) fn schema(
        path: impl Into<PathBuf>,
        source: jsonschema::ValidationError<'_>,
    ) -> Self {
        let location = source.instance_path().to_string();
        let location = if location.is_empty() {
            "$".to_owned()
        } else {
            location.trim_start_matches('/').replace('/', ".")
        };
        Self::Schema {
            path: path.into(),
            location,
            source: source.to_owned(),
        }
    }

    pub(crate) fn missing_implementation(path: &Path, function: &Function) -> Self {
        Self::MissingImplementation {
            path: path.to_owned(),
            function: function.name.clone(),
            status: function.status.clone(),
        }
    }

    pub(crate) fn missing_source_location(path: &Path, function: &Function, index: usize) -> Self {
        Self::MissingSourceLocation {
            path: path.to_owned(),
            function: function.name.clone(),
            index,
        }
    }

    pub(crate) fn record_output_mismatch(
        path: &Path,
        function: &Function,
        index: usize,
        record: &str,
    ) -> Self {
        Self::RecordOutputMismatch {
            path: path.to_owned(),
            function: function.name.clone(),
            index,
            record: record.to_owned(),
        }
    }

    pub(crate) fn missing_outputs(
        path: &Path,
        function: &Function,
        names: impl IntoIterator<Item = impl Into<String>>,
    ) -> Self {
        Self::MissingOutputs {
            path: path.to_owned(),
            function: function.name.clone(),
            names: names.into_iter().map(Into::into).collect(),
        }
    }
}

impl From<SpecificationError> for ReferenceError {
    fn from(error: SpecificationError) -> Self {
        Self::SourceSlug(Box::new(error))
    }
}
