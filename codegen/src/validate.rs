use std::{
    collections::{BTreeMap, BTreeSet},
    path::PathBuf,
};

use crate::{
    adapters::Registry,
    model::{Entry, Function, Parameter},
};

pub(crate) fn specifications(entries: &[Entry], adapters: &Registry) -> Vec<String> {
    let mut errors = Vec::new();
    let mut functions = BTreeMap::new();
    let mut public = BTreeMap::new();
    for entry in entries {
        for function in &entry.spec.functions {
            duplicate(
                &mut functions,
                &function.name,
                entry,
                "functions[].name",
                &mut errors,
            );
            let public_key = format!("{}::{}", entry.slug, function.public_api.name);
            duplicate(
                &mut public,
                &public_key,
                entry,
                "functions[].public_api",
                &mut errors,
            );
            duplicate_input_names(entry, function, &mut errors);
            duplicate_names(
                entry,
                function,
                function.outputs.fields(),
                "outputs.fields",
                &mut errors,
            );
            derived_inputs(entry, function, adapters, &mut errors);
            match (
                function.outputs.fields().len(),
                function.result_class().is_some(),
            ) {
                (1, false) | (2.., true) => {}
                (1, true) => errors.push(diag(
                    entry,
                    "outputs",
                    Some(&function.name),
                    "must be scalar when it has one field",
                )),
                (_, false) => errors.push(diag(
                    entry,
                    "outputs",
                    Some(&function.name),
                    "must be a named record when it has multiple fields",
                )),
                (_, true) => errors.push(diag(
                    entry,
                    "outputs",
                    Some(&function.name),
                    "must contain at least one output",
                )),
            }
        }
    }
    errors
}

fn derived_inputs(
    entry: &Entry,
    function: &Function,
    adapters: &Registry,
    errors: &mut Vec<String>,
) {
    for input in &function.inputs {
        if !input.r#type.is_numeric() && adapters.adapter_for_type(input.r#type.as_str()).is_none()
        {
            errors.push(diag(
                entry,
                "inputs[].type",
                Some(&function.name),
                &format!("unknown registered input type `{}`", input.r#type.as_str()),
            ));
        }
    }
    for (index, binding) in function.derived_inputs.iter().enumerate() {
        if binding.evidence.trim().is_empty() {
            errors.push(diag(
                entry,
                &format!("derived_inputs[{index}].evidence"),
                Some(&function.name),
                "must contain source-backed scientific evidence",
            ));
        }
        if let Some(adapter) = adapters.adapter(&binding.adapter) {
            if let Some(input) = function
                .inputs
                .iter()
                .find(|input| input.name == binding.input)
            {
                if input.r#type.as_str() != adapter.input_type.name {
                    errors.push(diag(
                        entry,
                        &format!("derived_inputs[{index}].input"),
                        Some(&function.name),
                        "adapter input type does not match the public input type",
                    ));
                }
            } else {
                errors.push(diag(
                    entry,
                    &format!("derived_inputs[{index}].input"),
                    Some(&function.name),
                    "references an unknown public input",
                ));
            }
            for component in binding.components.keys() {
                if !adapter
                    .outputs
                    .iter()
                    .any(|output| output.name == *component)
                {
                    errors.push(diag(
                        entry,
                        &format!("derived_inputs[{index}].components"),
                        Some(&function.name),
                        &format!("unknown adapter component `{component}`"),
                    ));
                }
            }
        } else {
            errors.push(diag(
                entry,
                &format!("derived_inputs[{index}].adapter"),
                Some(&function.name),
                &format!("unknown adapter `{}`", binding.adapter),
            ));
        }
    }
}

fn duplicate_input_names(entry: &Entry, function: &Function, errors: &mut Vec<String>) {
    let mut seen = BTreeSet::new();
    for value in &function.inputs {
        if !seen.insert(&value.name) {
            errors.push(diag(
                entry,
                "inputs",
                Some(&function.name),
                &format!("duplicate name `{}`", value.name),
            ));
        }
    }
}

fn duplicate<K: Ord + Clone + std::fmt::Display>(
    map: &mut BTreeMap<K, PathBuf>,
    key: &K,
    entry: &Entry,
    path: &str,
    errors: &mut Vec<String>,
) {
    if let Some(previous) = map.insert(key.clone(), entry.path.clone()) {
        errors.push(format!(
            "{}:\n  {path}:\n    duplicate value `{key}`; first declared in {}",
            entry.path.display(),
            previous.display()
        ));
    }
}

fn duplicate_names(
    entry: &Entry,
    function: &Function,
    values: &[Parameter],
    field: &str,
    errors: &mut Vec<String>,
) {
    let mut seen = BTreeSet::new();
    for value in values {
        if !seen.insert(&value.name) {
            errors.push(diag(
                entry,
                field,
                Some(&function.name),
                &format!("duplicate name `{}`", value.name),
            ));
        }
    }
}

pub(crate) fn diag(entry: &Entry, path: &str, function: Option<&str>, message: &str) -> String {
    let function = function
        .map(|name| format!(" ({name})"))
        .unwrap_or_default();
    format!(
        "{}:\n  {path}{function}:\n    {message}",
        entry.path.display()
    )
}
