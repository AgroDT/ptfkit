use anyhow::{Context, Result};

use crate::model::{
    CompiledFunction, CompiledInput, CompiledTolerance, CompiledVerificationCase, CoreFunction,
    Entry, Function, Output, Outputs, ToleranceSource, VerificationInput,
};

pub(crate) const FLOATING_POINT_GUARD: f64 = 1e-14;

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
                .with_context(|| format!("compiling {}", function.name))?;
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
                    anyhow::bail!(
                        "verification case `{}` references unknown input `{name}`",
                        case.id
                    );
                }
            }
            let inputs = function
                .inputs
                .iter()
                .map(|input| {
                    let input_name = input.name();
                    let value = case.inputs.get(input_name).with_context(|| {
                        format!(
                            "verification case `{}` is missing input `{}`",
                            case.id, input_name
                        )
                    })?;
                    match (input.enum_type(), value) {
                        (None, VerificationInput::Number(value)) => Ok(CompiledInput::Number(*value)),
                        (Some(enum_type), VerificationInput::Enum(member_name)) => {
                            enum_type
                                .values
                                .iter()
                                .find(|member| member.name == *member_name)
                                .with_context(|| {
                                    format!(
                                        "verification case `{}` input `{}` references unknown member `{member_name}` of enum `{}`",
                                        case.id, input_name, enum_type.name
                                    )
                                })?;
                            Ok(CompiledInput::Enum {
                                enum_name: enum_type.name.clone(),
                                member_name: member_name.clone(),
                            })
                        }
                        (None, VerificationInput::Enum(_)) => anyhow::bail!(
                            "verification case `{}` input `{}` must be numeric",
                            case.id,
                            input_name
                        ),
                        (Some(enum_type), VerificationInput::Number(_)) => anyhow::bail!(
                            "verification case `{}` input `{}` must name a member of enum `{}`",
                            case.id,
                            input_name,
                            enum_type.name
                        ),
                    }
                })
                .collect::<Result<Vec<_>>>()?;
            for name in case.expected.keys() {
                if !function.outputs.fields().iter().any(|field| field.name == *name) {
                    anyhow::bail!(
                        "verification case `{}` references unknown output `{name}`",
                        case.id
                    );
                }
            }
            let expected = function
                .outputs
                .fields()
                .iter()
                .map(|field| {
                    case.expected.get(&field.name).copied().with_context(|| {
                        format!(
                            "verification case `{}` is missing expected output `{}`",
                            case.id, field.name
                        )
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
                anyhow::bail!(
                    "function `{}` verification case `{}` output `{}` has resolved scientific tolerance {} (absolute {}, relative {}) greater than or equal to the magnitude of non-zero expected value {}",
                    function.name,
                    case.id,
                    field.name,
                    resolved,
                    tolerance.absolute,
                    tolerance.relative,
                    magnitude,
                );
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
                .with_context(|| {
                    format!(
                        "function `{}` output `{}` references unknown quantity `{}`",
                        function.name, field.name, field.quantity
                    )
                })?;
            let tolerance = quantity.units.get(&field.unit).with_context(|| {
                format!(
                    "function `{}` output `{}` quantity `{}` has no registered unit `{}`",
                    function.name, field.name, field.quantity, field.unit
                )
            })?;
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
