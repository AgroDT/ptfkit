#[derive(Debug, thiserror::Error)]
pub(crate) enum GenerationError {
    #[error("record output has no result class")]
    MissingResultClass,
    #[error("record type `{name}` has conflicting field definitions")]
    ConflictingRecordFields { name: String },
    #[error("Python result class `{name}` is reused with conflicting fields")]
    ConflictingPythonClass { name: String },
}
