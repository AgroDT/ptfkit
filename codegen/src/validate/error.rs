use std::path::{Path, PathBuf};

use crate::model::OutputField;

#[derive(Debug, thiserror::Error)]
pub(crate) enum ValidationError {
    #[error("specs/units.yaml: invalid unit identifier `{id}`")]
    InvalidUnitIdentifier { id: String },
    #[error("specs/units.yaml: unit `{id}` has an empty or duplicate notation")]
    InvalidUnitNotation { id: String },
    #[error("specs/quantities.yaml: quantity identifier `{id}` must match ^[a-z][a-z0-9_]*$")]
    InvalidQuantityIdentifier { id: String },
    #[error("specs/quantities.yaml:\n  {id}:\n    description must not be empty")]
    EmptyQuantityDescription { id: String },
    #[error("specs/quantities.yaml:\n  {id}:\n    at least one unit is required")]
    EmptyQuantityUnits { id: String },
    #[error(
        "specs/quantities.yaml: quantity `{id}` has ambiguous notation `{notation}` for `{previous}` and `{unit_id}`"
    )]
    AmbiguousNotation {
        id: String,
        notation: String,
        previous: String,
        unit_id: String,
    },
    #[error("specs/quantities.yaml: quantity `{id}` references unknown unit identifier `{unit}`")]
    UnknownQuantityUnit { id: String, unit: String },
    #[error("specs/quantities.yaml:\n  {id} [{unit}]:\n    rationale must not be empty")]
    EmptyToleranceRationale { id: String, unit: String },
    #[error("{path}:\n  {quantity} [{unit}]:\n    absolute tolerance must be finite and positive")]
    AbsoluteTolerance {
        path: String,
        quantity: String,
        unit: String,
        value: f64,
    },
    #[error(
        "{path}:\n  {quantity} [{unit}]:\n    relative tolerance must be finite and non-negative"
    )]
    RelativeTolerance {
        path: String,
        quantity: String,
        unit: String,
        value: f64,
    },
    #[error("{document}:\n  {path}:\n    duplicate value `{key}`; first declared in {previous}", document = .document.display(), previous = .previous.display())]
    DuplicateValue {
        document: PathBuf,
        path: String,
        key: String,
        previous: PathBuf,
    },
    #[error("{document}:\n  {path}{function}:\n    {kind}", document = .document.display(), function = .function.as_ref().map(|name| format!(" ({name})")).unwrap_or_default())]
    Function {
        document: PathBuf,
        path: String,
        function: Option<String>,
        #[source]
        kind: ValidationKind,
    },
}

#[derive(Debug, thiserror::Error)]
pub(crate) enum ValidationKind {
    #[error("must be scalar when it has one field")]
    ScalarRequired,
    #[error("must be a named record when it has multiple fields")]
    RecordRequired,
    #[error("must contain at least one output")]
    EmptyOutputs,
    #[error("output `{output}` references unknown quantity `{quantity}` with unit `{unit}`")]
    UnknownOutputQuantity {
        output: String,
        quantity: String,
        unit: String,
    },
    #[error("output `{output}` references unknown unit identifier `{unit}`")]
    UnknownOutputUnit { output: String, unit: String },
    #[error(
        "output `{output}` reported_unit `{reported}` is not an equivalent notation for unit `{unit}`; an explicit registry decision is required; values must not be converted"
    )]
    NonEquivalentUnit {
        output: String,
        reported: String,
        unit: String,
    },
    #[error("output `{output}` quantity `{quantity}` has no registered unit `{unit}`")]
    UnregisteredOutputUnit {
        output: String,
        quantity: String,
        unit: String,
    },
    #[error("override references unknown output `{name}`")]
    UnknownOverrideOutput { name: String },
    #[error("override for output `{name}` requires source_location")]
    MissingOverrideSource { name: String },
    #[error("duplicate name `{name}`")]
    DuplicateName { name: String },
    #[error("duplicate id `{id}`")]
    DuplicateCaseId { id: String },
    #[error("enum `{enum_name}` contains duplicate member name `{member}`")]
    DuplicateEnumName { enum_name: String, member: String },
    #[error("enum `{enum_name}` contains duplicate canonical value `{member}`")]
    DuplicateEnumValue { enum_name: String, member: String },
    #[error("enum `{enum_name}` exceeds the target ordinal capacity")]
    EnumCapacity { enum_name: String },
}

impl ValidationKind {
    pub(crate) fn in_function(
        self,
        document: &Path,
        function: &str,
        path: &str,
    ) -> ValidationError {
        ValidationError::Function {
            document: document.to_owned(),
            path: path.to_owned(),
            function: Some(function.to_owned()),
            kind: self,
        }
    }

    pub(crate) fn unknown_output_quantity(field: &OutputField) -> Self {
        Self::UnknownOutputQuantity {
            output: field.name.clone(),
            quantity: field.quantity.clone(),
            unit: field.unit.clone(),
        }
    }

    pub(crate) fn unknown_output_unit(field: &OutputField) -> Self {
        Self::UnknownOutputUnit {
            output: field.name.clone(),
            unit: field.unit.clone(),
        }
    }

    pub(crate) fn non_equivalent_unit(field: &OutputField) -> Self {
        Self::NonEquivalentUnit {
            output: field.name.clone(),
            reported: field.reported_unit.clone(),
            unit: field.unit.clone(),
        }
    }

    pub(crate) fn unregistered_output_unit(field: &OutputField) -> Self {
        Self::UnregisteredOutputUnit {
            output: field.name.clone(),
            quantity: field.quantity.clone(),
            unit: field.unit.clone(),
        }
    }

    pub(crate) fn unknown_override_output(name: impl Into<String>) -> Self {
        Self::UnknownOverrideOutput { name: name.into() }
    }

    pub(crate) fn missing_override_source(name: impl Into<String>) -> Self {
        Self::MissingOverrideSource { name: name.into() }
    }

    pub(crate) fn duplicate_name(name: impl Into<String>) -> Self {
        Self::DuplicateName { name: name.into() }
    }

    pub(crate) fn duplicate_case(id: impl Into<String>) -> Self {
        Self::DuplicateCaseId { id: id.into() }
    }

    pub(crate) fn duplicate_enum_name(
        enum_name: impl Into<String>,
        member: impl Into<String>,
    ) -> Self {
        Self::DuplicateEnumName {
            enum_name: enum_name.into(),
            member: member.into(),
        }
    }

    pub(crate) fn duplicate_enum_value(
        enum_name: impl Into<String>,
        member: impl Into<String>,
    ) -> Self {
        Self::DuplicateEnumValue {
            enum_name: enum_name.into(),
            member: member.into(),
        }
    }

    pub(crate) fn enum_capacity(enum_name: impl Into<String>) -> Self {
        Self::EnumCapacity {
            enum_name: enum_name.into(),
        }
    }
}
