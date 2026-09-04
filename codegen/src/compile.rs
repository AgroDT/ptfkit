use anyhow::{Context, Result};

use crate::model::{
    CompiledFunction, CompiledInput, CompiledVerificationCase, CoreFunction, Entry, Function,
    GoldenInput, Output, Outputs, PublishedPrecision, VerificationKind,
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
            compiled.push(CompiledFunction {
                verification_cases: verification_cases(function)?,
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
                        (None, GoldenInput::Number(value)) => Ok(CompiledInput::Number(*value)),
                        (Some(enum_type), GoldenInput::Enum(member_name)) => {
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
                        (None, GoldenInput::Enum(_)) => anyhow::bail!(
                            "verification case `{}` input `{}` must be numeric",
                            case.id,
                            input_name
                        ),
                        (Some(enum_type), GoldenInput::Number(_)) => anyhow::bail!(
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
            for name in case.precision.keys() {
                if !function.outputs.fields().iter().any(|field| field.name == *name) {
                    anyhow::bail!(
                        "verification case `{}` references unknown precision output `{name}`",
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
            let published_tolerance = function
                .outputs
                .fields()
                .iter()
                .zip(&expected)
                .map(|(field, expected)| {
                    if case.kind != VerificationKind::Published {
                        return 0.0;
                    }
                    case.precision
                        .get(&field.name)
                        .map_or(0.0, |precision| rounding_tolerance(*expected, *precision))
                })
                .collect();
            Ok(CompiledVerificationCase {
                id: case.id.clone(),
                inputs,
                expected,
                published_tolerance,
            })
        })
        .collect()
}

fn rounding_tolerance(expected: f64, precision: PublishedPrecision) -> f64 {
    match precision {
        PublishedPrecision::DecimalPlaces { decimal_places } => {
            0.5 * 10.0_f64.powi(-(decimal_places as i32))
        }
        PublishedPrecision::SignificantDigits { significant_digits } if expected != 0.0 => {
            let exponent = expected.abs().log10().floor() as i32 - significant_digits as i32 + 1;
            0.5 * 10.0_f64.powi(exponent)
        }
        PublishedPrecision::SignificantDigits { .. } => 0.0,
    }
}
