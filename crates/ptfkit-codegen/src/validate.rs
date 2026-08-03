use std::{
    collections::{BTreeMap, BTreeSet},
    path::PathBuf,
};

use crate::model::{Entry, Function, Parameter};

pub(crate) fn specifications(entries: &[Entry]) -> Vec<String> {
    let mut errors = Vec::new();
    let mut sources = BTreeMap::new();
    let mut functions = BTreeMap::new();
    let mut public = BTreeMap::new();
    for entry in entries {
        duplicate(
            &mut sources,
            &entry.spec.source.key,
            entry,
            "source.key",
            &mut errors,
        );
        if entry.path.file_stem().and_then(|stem| stem.to_str()) != Some(&entry.spec.source.key) {
            errors.push(diag(
                entry,
                "source.key",
                None,
                "source-oriented filename must match source.key",
            ));
        }
        let expected: Vec<_> = entry
            .spec
            .functions
            .iter()
            .map(|function| function.name.clone())
            .collect();
        if entry.section_functions != expected {
            errors.push(diag(entry, "Markdown sections", None, &format!("declared function sections must appear once and in YAML order; expected {expected:?}, found {:?}", entry.section_functions)));
        }
        for function in &entry.spec.functions {
            duplicate(
                &mut functions,
                &function.name,
                entry,
                "functions[].name",
                &mut errors,
            );
            let public_key = format!("{}::{}", entry.spec.source.key, function.public_api.name);
            duplicate(
                &mut public,
                &public_key,
                entry,
                "functions[].public_api",
                &mut errors,
            );
            duplicate_names(entry, function, &function.inputs, "inputs", &mut errors);
            duplicate_names(entry, function, &function.outputs, "outputs", &mut errors);
            match (
                function.outputs.len(),
                function.public_api.result_class.is_some(),
            ) {
                (1, false) | (2.., true) => {}
                (1, true) => errors.push(diag(
                    entry,
                    "public_api.result_class",
                    Some(&function.name),
                    "must be null for a scalar result",
                )),
                (_, false) => errors.push(diag(
                    entry,
                    "public_api.result_class",
                    Some(&function.name),
                    "must be non-null for a multi-output result",
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
