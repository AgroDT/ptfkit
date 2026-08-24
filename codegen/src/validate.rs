use std::{
    collections::{BTreeMap, BTreeSet},
    path::PathBuf,
};

use crate::model::{Entry, Function, Parameter};

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
            duplicate_input_names(entry, function, &mut errors);
            validate_enums(entry, function, &mut errors);
            duplicate_names(
                entry,
                function,
                function.outputs.fields(),
                "outputs.fields",
                &mut errors,
            );
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

fn duplicate_input_names(entry: &Entry, function: &Function, errors: &mut Vec<String>) {
    let mut seen = BTreeSet::new();
    for value in &function.inputs {
        if !seen.insert(value.name()) {
            errors.push(diag(
                entry,
                "inputs",
                Some(&function.name),
                &format!("duplicate name `{}`", value.name()),
            ));
        }
    }
}

fn validate_enums(entry: &Entry, function: &Function, errors: &mut Vec<String>) {
    let mut validated = BTreeSet::new();
    for input in &function.inputs {
        let Some(enum_type) = input.enum_type() else {
            continue;
        };
        if !validated.insert(&enum_type.name) {
            continue;
        }
        let mut names = BTreeSet::new();
        let mut values = BTreeSet::new();
        for member in &enum_type.values {
            if !names.insert(&member.name) {
                errors.push(diag(
                    entry,
                    "$defs",
                    Some(&function.name),
                    &format!(
                        "enum `{}` contains duplicate member name `{}`",
                        enum_type.name, member.name
                    ),
                ));
            }
            if !values.insert(&member.value) {
                errors.push(diag(
                    entry,
                    "$defs",
                    Some(&function.name),
                    &format!(
                        "enum `{}` contains duplicate canonical value `{}`",
                        enum_type.name, member.value
                    ),
                ));
            }
        }
        if enum_type.values.len() > u32::MAX as usize {
            errors.push(diag(
                entry,
                "$defs",
                Some(&function.name),
                &format!(
                    "enum `{}` exceeds the target ordinal capacity",
                    enum_type.name
                ),
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
