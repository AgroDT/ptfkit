use anyhow::{Context, Result};

use crate::model::{CompiledFunction, CoreFunction, Entry, Output, Outputs};

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
            compiled.push(CompiledFunction {
                core: CoreFunction {
                    name: function.name.clone(),
                    inputs: function
                        .inputs
                        .iter()
                        .map(|input| input.name.clone())
                        .collect(),
                    output,
                },
                entry: entry.clone(),
                function_index,
                ir,
            });
        }
    }
    Ok(compiled)
}
