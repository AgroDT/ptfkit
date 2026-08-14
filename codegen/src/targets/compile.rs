use anyhow::{Context, Result};

use crate::model::{
    CompiledFunction, CompiledGoldenTest, CoreFunction, Entry, Function, Output, Outputs,
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
                    .map(|input| input.name.clone())
                    .collect(),
                output,
            };
            compiled.push(CompiledFunction {
                golden_tests: golden_tests(function, &core)?,
                core,
                entry: entry.clone(),
                function_index,
                ir,
            });
        }
    }
    Ok(compiled)
}

fn golden_tests(function: &Function, core: &CoreFunction) -> Result<Vec<CompiledGoldenTest>> {
    function
        .golden_tests
        .iter()
        .map(|case| {
            let inputs = core
                .inputs
                .iter()
                .map(|name| {
                    case.inputs.get(name).copied().with_context(|| {
                        format!("golden test `{}` is missing input `{name}`", case.id)
                    })
                })
                .collect::<Result<Vec<_>>>()?;
            let expected = function
                .outputs
                .fields()
                .iter()
                .map(|field| {
                    case.expected.get(&field.name).copied().with_context(|| {
                        format!(
                            "golden test `{}` is missing output `{}`",
                            case.id, field.name
                        )
                    })
                })
                .collect::<Result<Vec<_>>>()?;
            Ok(CompiledGoldenTest {
                id: case.id.clone(),
                inputs,
                expected,
                rtol: case.rtol,
                atol: case.atol,
            })
        })
        .collect()
}
