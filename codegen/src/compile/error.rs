use crate::model::{CompiledTolerance, CompiledVerificationCase, Function, OutputField};

#[derive(Debug, thiserror::Error)]
pub(crate) enum CompileError {
    #[error("compiling {function}: implementation is unavailable")]
    MissingImplementation { function: String },
    #[error("verification case `{case_id}` references unknown input `{name}`")]
    UnknownInput { case_id: String, name: String },
    #[error("verification case `{case_id}` is missing input `{name}`")]
    MissingInput { case_id: String, name: String },
    #[error("verification case `{case_id}` references unknown output `{name}`")]
    UnknownOutput { case_id: String, name: String },
    #[error("verification case `{case_id}` is missing expected output `{name}`")]
    MissingOutput { case_id: String, name: String },
    #[error(
        "verification case `{case_id}` input `{input}` references unknown member `{member_name}` of enum `{enum_name}`"
    )]
    UnknownEnumMember {
        case_id: String,
        input: String,
        member_name: String,
        enum_name: String,
    },
    #[error("verification case `{case_id}` input `{input}` must be numeric")]
    NumericInputRequired { case_id: String, input: String },
    #[error(
        "verification case `{case_id}` input `{input}` must name a member of enum `{enum_name}`"
    )]
    EnumInputRequired {
        case_id: String,
        input: String,
        enum_name: String,
    },
    #[error(
        "function `{function}` verification case `{case_id}` output `{output}` has resolved scientific tolerance {resolved} (absolute {absolute}, relative {relative}) greater than or equal to the magnitude of non-zero expected value {magnitude}"
    )]
    NonDiscriminatingTolerance {
        function: String,
        case_id: String,
        output: String,
        resolved: f64,
        absolute: f64,
        relative: f64,
        magnitude: f64,
    },
    #[error("function `{function}` output `{output}` references unknown quantity `{quantity}`")]
    UnknownQuantity {
        function: String,
        output: String,
        quantity: String,
    },
    #[error(
        "function `{function}` output `{output}` quantity `{quantity}` has no registered unit `{unit}`"
    )]
    UnregisteredUnit {
        function: String,
        output: String,
        quantity: String,
        unit: String,
    },
}

impl CompileError {
    pub(crate) fn non_discriminating_tolerance(
        function: &Function,
        case: &CompiledVerificationCase,
        field: &OutputField,
        tolerance: &CompiledTolerance,
        resolved: f64,
        magnitude: f64,
    ) -> Self {
        Self::NonDiscriminatingTolerance {
            function: function.name.clone(),
            case_id: case.id.clone(),
            output: field.name.clone(),
            resolved,
            absolute: tolerance.absolute,
            relative: tolerance.relative,
            magnitude,
        }
    }

    pub(crate) fn unknown_quantity(function: &Function, field: &OutputField) -> Self {
        Self::UnknownQuantity {
            function: function.name.clone(),
            output: field.name.clone(),
            quantity: field.quantity.clone(),
        }
    }

    pub(crate) fn unregistered_unit(function: &Function, field: &OutputField) -> Self {
        Self::UnregisteredUnit {
            function: function.name.clone(),
            output: field.name.clone(),
            quantity: field.quantity.clone(),
            unit: field.unit.clone(),
        }
    }
}
