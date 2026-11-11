mod error;
pub(crate) use error::CompileError;

type Result<T> = std::result::Result<T, CompileError>;

use crate::model::{
    CompiledFunction, CompiledInput, CompiledTolerance, CompiledVerificationCase, CoreFunction,
    Entry, Function, Output, Outputs, ToleranceSource, VerificationInput,
};

pub(super) fn functions(entries: Vec<Entry>) -> Result<Vec<CompiledFunction>> {
    let mut compiled = Vec::new();
    for entry in entries {
        for (function_index, function) in entry.spec.functions.iter().enumerate() {
            if !matches!(
                function.status.as_str(),
                "implemented" | "ready-for-implementation"
            ) {
                continue;
            }
            let ir = entry.implementations[function_index]
                .clone()
                .ok_or_else(|| CompileError::MissingImplementation {
                    function: function.name.clone(),
                })?;
            let output = match &function.outputs {
                Outputs::Scalar { .. } => Output::Scalar,
                Outputs::Record { fields, .. } => {
                    Output::Struct(fields.iter().map(|field| field.name.clone()).collect())
                }
            };
            let core = CoreFunction {
                name: function.name.clone(),
                inputs: function
                    .inputs
                    .iter()
                    .map(|input| input.name().to_owned())
                    .collect(),
                output,
            };
            let verification_cases = verification_cases(function)?;
            let output_tolerances = output_tolerances(&entry, function)?;
            validate_discriminating_tolerances(function, &verification_cases, &output_tolerances)?;
            compiled.push(CompiledFunction {
                verification_cases,
                output_tolerances,
                core,
                entry: entry.clone(),
                function_index,
                ir,
            });
        }
    }
    Ok(compiled)
}

fn verification_cases(function: &Function) -> Result<Vec<CompiledVerificationCase>> {
    function
        .verification_cases
        .iter()
        .map(|case| {
            for name in case.inputs.keys() {
                if !function.inputs.iter().any(|input| input.name() == name) {
                    return Err(CompileError::UnknownInput {
                        case_id: case.id.clone(),
                        name: name.clone(),
                    });
                }
            }
            let inputs = function
                .inputs
                .iter()
                .map(|input| {
                    let input_name = input.name();
                    let value =
                        case.inputs
                            .get(input_name)
                            .ok_or_else(|| CompileError::MissingInput {
                                case_id: case.id.clone(),
                                name: input_name.to_owned(),
                            })?;
                    match (input.enum_type(), value) {
                        (None, VerificationInput::Number(value)) => {
                            Ok(CompiledInput::Number(*value))
                        }
                        (Some(enum_type), VerificationInput::Enum(member_name)) => {
                            enum_type
                                .values
                                .iter()
                                .find(|member| member.name == *member_name)
                                .ok_or_else(|| CompileError::UnknownEnumMember {
                                    case_id: case.id.clone(),
                                    input: input_name.to_owned(),
                                    member_name: member_name.clone(),
                                    enum_name: enum_type.enum_type.name.clone(),
                                })?;
                            Ok(CompiledInput::Enum {
                                enum_type: enum_type.enum_type.clone(),
                                member_name: member_name.clone(),
                            })
                        }
                        (None, VerificationInput::Enum(_)) => {
                            Err(CompileError::NumericInputRequired {
                                case_id: case.id.clone(),
                                input: input_name.to_owned(),
                            })
                        }
                        (Some(enum_type), VerificationInput::Number(_)) => {
                            Err(CompileError::EnumInputRequired {
                                case_id: case.id.clone(),
                                input: input_name.to_owned(),
                                enum_name: enum_type.enum_type.name.clone(),
                            })
                        }
                    }
                })
                .collect::<Result<Vec<_>>>()?;
            for name in case.expected.keys() {
                if !function
                    .outputs
                    .fields()
                    .iter()
                    .any(|field| field.name == *name)
                {
                    return Err(CompileError::UnknownOutput {
                        case_id: case.id.clone(),
                        name: name.clone(),
                    });
                }
            }
            let expected = function
                .outputs
                .fields()
                .iter()
                .map(|field| {
                    case.expected.get(&field.name).copied().ok_or_else(|| {
                        CompileError::MissingOutput {
                            case_id: case.id.clone(),
                            name: field.name.clone(),
                        }
                    })
                })
                .collect::<Result<Vec<_>>>()?;
            Ok(CompiledVerificationCase {
                id: case.id.clone(),
                inputs,
                expected,
            })
        })
        .collect()
}

fn validate_discriminating_tolerances(
    function: &Function,
    cases: &[CompiledVerificationCase],
    tolerances: &[CompiledTolerance],
) -> Result<()> {
    for case in cases {
        for ((field, expected), tolerance) in function
            .outputs
            .fields()
            .iter()
            .zip(&case.expected)
            .zip(tolerances)
        {
            let magnitude = expected.abs();
            let resolved = tolerance.absolute.max(tolerance.relative * magnitude);
            if *expected != 0.0 && resolved >= magnitude {
                return Err(CompileError::non_discriminating_tolerance(
                    function, case, field, tolerance, resolved, magnitude,
                ));
            }
        }
    }
    Ok(())
}

fn output_tolerances(entry: &Entry, function: &Function) -> Result<Vec<CompiledTolerance>> {
    function
        .outputs
        .fields()
        .iter()
        .map(|field| {
            if let Some(override_) = function.verification_tolerances.get(&field.name) {
                return Ok(CompiledTolerance {
                    absolute: override_.absolute,
                    relative: override_.relative.unwrap_or_default(),
                    quantity: field.quantity.clone(),
                    unit: field.unit.clone(),
                    source: ToleranceSource::SourceOverride(override_.source_location.clone()),
                });
            }
            let quantity = entry
                .quantities
                .quantities
                .get(&field.quantity)
                .ok_or_else(|| CompileError::unknown_quantity(function, field))?;
            let tolerance = quantity
                .units
                .get(&field.unit)
                .ok_or_else(|| CompileError::unregistered_unit(function, field))?;
            Ok(CompiledTolerance {
                absolute: tolerance.absolute,
                relative: tolerance.relative.unwrap_or_default(),
                quantity: field.quantity.clone(),
                unit: field.unit.clone(),
                source: ToleranceSource::Registry,
            })
        })
        .collect()
}
