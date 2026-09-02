use std::{
    collections::HashMap,
    sync::{Mutex, OnceLock},
};

use anyhow::{Context, Result};

use crate::model::{
    CompiledFunction, CompiledGoldenTest, CompiledInput, CoreFunction, Entry, Function,
    GoldenInput, Output, Outputs, Verification,
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
                golden_tests: golden_tests(function, &ir)?,
                core,
                entry: entry.clone(),
                function_index,
                ir,
            });
        }
    }
    Ok(compiled)
}

fn golden_tests(
    function: &Function,
    ir: &crate::semantic::Function,
) -> Result<Vec<CompiledGoldenTest>> {
    function
        .golden_tests
        .iter()
        .map(|case| {
            let inputs = function
                .inputs
                .iter()
                .map(|input| {
                    let input_name = input.name();
                    let value = case.inputs.get(input_name).with_context(|| {
                        format!(
                            "golden test `{}` is missing input `{}`",
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
                                        "golden test `{}` input `{}` references unknown member `{member_name}` of enum `{}`",
                                        case.id, input_name, enum_type.name
                                    )
                                })?;
                            Ok(CompiledInput::Enum {
                                enum_name: enum_type.name.clone(),
                                member_name: member_name.clone(),
                            })
                        }
                        (None, GoldenInput::Enum(_)) => anyhow::bail!(
                            "golden test `{}` input `{}` must be numeric",
                            case.id,
                            input_name
                        ),
                        (Some(enum_type), GoldenInput::Number(_)) => anyhow::bail!(
                            "golden test `{}` input `{}` must name a member of enum `{}`",
                            case.id,
                            input_name,
                            enum_type.name
                        ),
                    }
                })
                .collect::<Result<Vec<_>>>()?;
            for name in case.expected.keys().chain(case.output_verification.keys()) {
                if !function.outputs.fields().iter().any(|field| field.name == *name) {
                    anyhow::bail!(
                        "golden test `{}` references unknown output `{name}`",
                        case.id
                    );
                }
            }
            static CACHE: OnceLock<Mutex<HashMap<String, Vec<crate::model::Acceptance>>>> = OnceLock::new();
            let cache_key = format!("{ir:?}|{case:?}");
            let mut cache = CACHE
                .get_or_init(|| Mutex::new(HashMap::new()))
                .lock()
                .expect("verification cache lock is not poisoned");
            if let Some(acceptance) = cache.get(&cache_key).cloned() {
                return Ok(CompiledGoldenTest { id: case.id.clone(), inputs, acceptance });
            }
            let oracle = crate::verification::oracle_outputs(ir, &function.outputs, &inputs)
                .with_context(|| format!("evaluating golden test `{}`", case.id))?;
            let acceptance = function
                .outputs
                .fields()
                .iter()
                .zip(&oracle)
                .map(|(field, oracle)| {
                    let verification = case
                        .output_verification
                        .get(&field.name)
                        .unwrap_or(&case.verification);
                    let nominal = case.expected.get(&field.name).copied();
                    if nominal.is_none()
                        && matches!(verification, Verification::Exact | Verification::PublishedRounded { .. })
                    {
                        anyhow::bail!(
                            "golden test `{}` is missing required expected output `{}`",
                            case.id,
                            field.name
                        );
                    }
                    crate::verification::acceptance(verification, nominal, oracle, ir).with_context(
                        || format!("golden test `{}` output `{}`", case.id, field.name),
                    )
                })
                .collect::<Result<Vec<_>>>()?;
            cache.insert(cache_key, acceptance.clone());
            Ok(CompiledGoldenTest {
                id: case.id.clone(),
                inputs,
                acceptance,
            })
        })
        .collect()
}
