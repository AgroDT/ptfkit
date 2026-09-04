use std::{
    collections::{BTreeMap, BTreeSet},
    path::PathBuf,
};

use crate::model::{Entry, Function, OutputField, QuantityRegistry};

pub(crate) fn specifications(entries: &[Entry]) -> Vec<String> {
    let mut errors = Vec::new();
    if let Some(entry) = entries.first() {
        validate_quantity_registry(&entry.quantities, &mut errors);
    }
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
            validate_output_quantities(entry, function, &mut errors);
            validate_tolerance_overrides(entry, function, &mut errors);
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

fn validate_quantity_registry(registry: &QuantityRegistry, errors: &mut Vec<String>) {
    let mut identifiers = BTreeSet::new();
    for quantity in &registry.quantities {
        let valid_identifier = !quantity.id.is_empty()
            && quantity.id.chars().enumerate().all(|(index, character)| {
                if index == 0 {
                    character.is_ascii_lowercase()
                } else {
                    character.is_ascii_lowercase() || character.is_ascii_digit() || character == '_'
                }
            });
        if !valid_identifier {
            errors.push(format!(
                "specs/quantities.yaml:\n  {}:\n    quantity identifier must match ^[a-z][a-z0-9_]*$",
                quantity.id
            ));
        }
        if !identifiers.insert(&quantity.id) {
            errors.push(format!(
                "specs/quantities.yaml:\n  {}:\n    duplicate quantity identifier",
                quantity.id
            ));
        }
        if quantity.description.trim().is_empty() {
            errors.push(format!(
                "specs/quantities.yaml:\n  {}:\n    description must not be empty",
                quantity.id
            ));
        }
        if quantity.units.is_empty() {
            errors.push(format!(
                "specs/quantities.yaml:\n  {}:\n    at least one unit is required",
                quantity.id
            ));
        }
        for (unit, tolerance) in &quantity.units {
            if unit.is_empty() {
                errors.push(format!(
                    "specs/quantities.yaml:\n  {}:\n    unit must not be empty",
                    quantity.id
                ));
            }
            validate_tolerance(
                "specs/quantities.yaml",
                &quantity.id,
                unit,
                tolerance.absolute,
                tolerance.relative,
                errors,
            );
            if tolerance.rationale.trim().is_empty() {
                errors.push(format!(
                    "specs/quantities.yaml:\n  {} [{}]:\n    rationale must not be empty",
                    quantity.id, unit
                ));
            }
        }
    }
}

fn validate_output_quantities(entry: &Entry, function: &Function, errors: &mut Vec<String>) {
    for field in function.outputs.fields() {
        let Some(quantity) = entry
            .quantities
            .quantities
            .iter()
            .find(|quantity| quantity.id == field.quantity)
        else {
            errors.push(diag(
                entry,
                "outputs",
                Some(&function.name),
                &format!(
                    "output `{}` references unknown quantity `{}` with unit `{}`",
                    field.name, field.quantity, field.unit
                ),
            ));
            continue;
        };
        if !quantity.units.contains_key(&field.unit) {
            errors.push(diag(
                entry,
                "outputs",
                Some(&function.name),
                &format!(
                    "output `{}` quantity `{}` has no registered unit `{}`",
                    field.name, field.quantity, field.unit
                ),
            ));
        }
    }
}

fn validate_tolerance_overrides(entry: &Entry, function: &Function, errors: &mut Vec<String>) {
    for (name, tolerance) in &function.verification_tolerances {
        let Some(field) = function
            .outputs
            .fields()
            .iter()
            .find(|field| field.name == *name)
        else {
            errors.push(diag(
                entry,
                "verification_tolerances",
                Some(&function.name),
                &format!("override references unknown output `{name}`"),
            ));
            continue;
        };
        validate_tolerance(
            &entry.path.display().to_string(),
            &field.quantity,
            &field.unit,
            tolerance.absolute,
            tolerance.relative,
            errors,
        );
        if tolerance.source_location.trim().is_empty() {
            errors.push(diag(
                entry,
                "verification_tolerances",
                Some(&function.name),
                &format!("override for output `{name}` requires source_location"),
            ));
        }
    }
}

fn validate_tolerance(
    path: &str,
    quantity: &str,
    unit: &str,
    absolute: f64,
    relative: Option<f64>,
    errors: &mut Vec<String>,
) {
    if !absolute.is_finite() || absolute <= 0.0 {
        errors.push(format!(
            "{path}:\n  {quantity} [{unit}]:\n    absolute tolerance must be finite and positive"
        ));
    }
    if relative.is_some_and(|value| !value.is_finite() || value < 0.0) {
        errors.push(format!(
            "{path}:\n  {quantity} [{unit}]:\n    relative tolerance must be finite and non-negative"
        ));
    }
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
    values: &[OutputField],
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
