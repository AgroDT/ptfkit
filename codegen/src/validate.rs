use std::{
    collections::{BTreeMap, BTreeSet},
    path::PathBuf,
};

use crate::model::{AdapterStatus, Entry, Function, Parameter};

pub(crate) fn specifications(entries: &[Entry]) -> Vec<String> {
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
            duplicate_names(entry, function, &function.inputs, "inputs", &mut errors);
            duplicate_names(
                entry,
                function,
                function.outputs.fields(),
                "outputs.fields",
                &mut errors,
            );
            input_adapters(entry, function, &mut errors);
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

fn input_adapters(entry: &Entry, function: &Function, errors: &mut Vec<String>) {
    let Some(adapter) = function
        .input_adapters
        .as_ref()
        .and_then(|adapters| adapters.usda_texture.as_ref())
    else {
        return;
    };
    if adapter.evidence.trim().is_empty() {
        errors.push(diag(
            entry,
            "input_adapters.usda_texture.evidence",
            Some(&function.name),
            "must contain scientific compatibility evidence",
        ));
    }

    let declared = function
        .inputs
        .iter()
        .map(|input| input.name.as_str())
        .collect::<BTreeSet<_>>();
    let mut mapped = BTreeSet::new();
    if let Some(mapping) = &adapter.inputs {
        for (role, name) in mapping.roles() {
            let Some(name) = name else { continue };
            if !declared.contains(name) {
                errors.push(diag(
                    entry,
                    &format!("input_adapters.usda_texture.inputs.{role}"),
                    Some(&function.name),
                    &format!("mapped input `{name}` is not declared by the function"),
                ));
            }
            if !mapped.insert(name) {
                errors.push(diag(
                    entry,
                    "input_adapters.usda_texture.inputs",
                    Some(&function.name),
                    &format!("input `{name}` is mapped to multiple texture roles"),
                ));
            }
        }
    }
    if matches!(adapter.status, AdapterStatus::Supported) && mapped.is_empty() {
        errors.push(diag(
            entry,
            "input_adapters.usda_texture.inputs",
            Some(&function.name),
            "supported compatibility must map at least one texture role",
        ));
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
