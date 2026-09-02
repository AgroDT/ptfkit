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
            duplicate_verification_case_ids(entry, function, &mut errors);
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

fn valid_identifier(id: &str) -> bool {
    !id.is_empty()
        && id.chars().enumerate().all(|(index, c)| {
            c.is_ascii_lowercase() || (index > 0 && (c.is_ascii_digit() || c == '_'))
        })
}

fn validate_quantity_registry(registry: &QuantityRegistry, errors: &mut Vec<String>) {
    for (id, unit) in &registry.units {
        if !valid_identifier(id) {
            errors.push(format!("specs/units.yaml: invalid unit identifier `{id}`"));
        }
        let mut notations = BTreeSet::new();
        for notation in std::iter::once(&unit.preferred_notation).chain(&unit.aliases) {
            if notation.trim().is_empty() || !notations.insert(notation) {
                errors.push(format!(
                    "specs/units.yaml: unit `{id}` has an empty or duplicate notation"
                ));
            }
        }
    }
    for (id, quantity) in &registry.quantities {
        if !valid_identifier(id) {
            errors.push(format!(
                "specs/quantities.yaml: quantity identifier `{id}` must match ^[a-z][a-z0-9_]*$"
            ));
        }
        if quantity.description.trim().is_empty() {
            errors.push(format!(
                "specs/quantities.yaml:\n  {}:\n    description must not be empty",
                id
            ));
        }
        if quantity.units.is_empty() {
            errors.push(format!(
                "specs/quantities.yaml:\n  {}:\n    at least one unit is required",
                id
            ));
        }
        let mut notations = BTreeMap::new();
        for unit_id in quantity.units.keys() {
            if let Some(unit) = registry.units.get(unit_id) {
                for notation in std::iter::once(&unit.preferred_notation).chain(&unit.aliases) {
                    if let Some(previous) = notations.insert(notation, unit_id) {
                        errors.push(format!("specs/quantities.yaml: quantity `{id}` has ambiguous notation `{notation}` for `{previous}` and `{unit_id}`"));
                    }
                }
            }
        }
        for (unit, tolerance) in &quantity.units {
            if !registry.units.contains_key(unit) {
                errors.push(format!(
                    "specs/quantities.yaml: quantity `{id}` references unknown unit identifier `{unit}`"
                ));
            }
            validate_tolerance(
                "specs/quantities.yaml",
                id,
                unit,
                tolerance.absolute,
                tolerance.relative,
                errors,
            );
            if tolerance.rationale.trim().is_empty() {
                errors.push(format!(
                    "specs/quantities.yaml:\n  {} [{}]:\n    rationale must not be empty",
                    id, unit
                ));
            }
        }
    }
}

fn validate_output_quantities(entry: &Entry, function: &Function, errors: &mut Vec<String>) {
    for field in function.outputs.fields() {
        let Some(quantity) = entry.quantities.quantities.get(&field.quantity) else {
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
        match entry.quantities.units.get(&field.unit) {
            None => errors.push(diag(
                entry,
                "outputs",
                Some(&function.name),
                &format!(
                    "output `{}` references unknown unit identifier `{}`",
                    field.name, field.unit
                ),
            )),
            Some(unit)
                if field.reported_unit != unit.preferred_notation
                    && !unit.aliases.contains(&field.reported_unit) =>
            {
                errors.push(diag(entry, "outputs", Some(&function.name),
                    &format!("output `{}` reported_unit `{}` is not an equivalent notation for unit `{}`; an explicit registry decision is required; values must not be converted", field.name, field.reported_unit, field.unit)));
            }
            Some(_) => {}
        }
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

fn duplicate_verification_case_ids(entry: &Entry, function: &Function, errors: &mut Vec<String>) {
    let mut seen = BTreeSet::new();
    for case in &function.verification_cases {
        if !seen.insert(&case.id) {
            errors.push(diag(
                entry,
                "verification_cases",
                Some(&function.name),
                &format!("duplicate id `{}`", case.id),
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
