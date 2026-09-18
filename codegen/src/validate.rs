mod error;
pub(crate) use error::{ValidationError, ValidationKind};

use std::{
    collections::{BTreeMap, BTreeSet},
    path::PathBuf,
};

use crate::model::{Entry, Function, OutputField, QuantityRegistry};

pub(crate) fn specifications(entries: &[Entry]) -> Vec<ValidationError> {
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
                (1, true) => errors.push(ValidationKind::ScalarRequired.in_function(
                    &entry.path,
                    &function.name,
                    "outputs",
                )),
                (_, false) => errors.push(ValidationKind::RecordRequired.in_function(
                    &entry.path,
                    &function.name,
                    "outputs",
                )),
                (_, true) => errors.push(ValidationKind::EmptyOutputs.in_function(
                    &entry.path,
                    &function.name,
                    "outputs",
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

fn validate_quantity_registry(registry: &QuantityRegistry, errors: &mut Vec<ValidationError>) {
    for (id, unit) in &registry.units {
        if !valid_identifier(id) {
            errors.push(ValidationError::InvalidUnitIdentifier { id: id.clone() });
        }
        let mut notations = BTreeSet::new();
        for notation in std::iter::once(&unit.preferred_notation).chain(&unit.aliases) {
            if notation.trim().is_empty() || !notations.insert(notation) {
                errors.push(ValidationError::InvalidUnitNotation { id: id.clone() });
            }
        }
    }
    for (id, quantity) in &registry.quantities {
        if !valid_identifier(id) {
            errors.push(ValidationError::InvalidQuantityIdentifier { id: id.clone() });
        }
        if quantity.description.trim().is_empty() {
            errors.push(ValidationError::EmptyQuantityDescription { id: id.clone() });
        }
        if quantity.units.is_empty() {
            errors.push(ValidationError::EmptyQuantityUnits { id: id.clone() });
        }
        let mut notations = BTreeMap::new();
        for unit_id in quantity.units.keys() {
            if let Some(unit) = registry.units.get(unit_id) {
                for notation in std::iter::once(&unit.preferred_notation).chain(&unit.aliases) {
                    if let Some(previous) = notations.insert(notation, unit_id) {
                        errors.push(ValidationError::AmbiguousNotation {
                            id: id.clone(),
                            notation: notation.clone(),
                            previous: previous.clone(),
                            unit_id: unit_id.clone(),
                        });
                    }
                }
            }
        }
        for (unit, tolerance) in &quantity.units {
            if !registry.units.contains_key(unit) {
                errors.push(ValidationError::UnknownQuantityUnit {
                    id: id.clone(),
                    unit: unit.clone(),
                });
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
                errors.push(ValidationError::EmptyToleranceRationale {
                    id: id.clone(),
                    unit: unit.clone(),
                });
            }
        }
    }
}

fn validate_output_quantities(
    entry: &Entry,
    function: &Function,
    errors: &mut Vec<ValidationError>,
) {
    for field in function.outputs.fields() {
        let Some(quantity) = entry.quantities.quantities.get(&field.quantity) else {
            errors.push(ValidationKind::unknown_output_quantity(field).in_function(
                &entry.path,
                &function.name,
                "outputs",
            ));
            continue;
        };
        match entry.quantities.units.get(&field.unit) {
            None => errors.push(ValidationKind::unknown_output_unit(field).in_function(
                &entry.path,
                &function.name,
                "outputs",
            )),
            Some(unit)
                if field.reported_unit != unit.preferred_notation
                    && !unit.aliases.contains(&field.reported_unit) =>
            {
                errors.push(ValidationKind::non_equivalent_unit(field).in_function(
                    &entry.path,
                    &function.name,
                    "outputs",
                ));
            }
            Some(_) => {}
        }
        if !quantity.units.contains_key(&field.unit) {
            errors.push(ValidationKind::unregistered_output_unit(field).in_function(
                &entry.path,
                &function.name,
                "outputs",
            ));
        }
    }
}

fn validate_tolerance_overrides(
    entry: &Entry,
    function: &Function,
    errors: &mut Vec<ValidationError>,
) {
    for (name, tolerance) in &function.verification_tolerances {
        let Some(field) = function
            .outputs
            .fields()
            .iter()
            .find(|field| field.name == *name)
        else {
            errors.push(ValidationKind::unknown_override_output(name).in_function(
                &entry.path,
                &function.name,
                "verification_tolerances",
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
            errors.push(ValidationKind::missing_override_source(name).in_function(
                &entry.path,
                &function.name,
                "verification_tolerances",
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
    errors: &mut Vec<ValidationError>,
) {
    if !absolute.is_finite() || absolute <= 0.0 {
        errors.push(ValidationError::AbsoluteTolerance {
            path: path.to_owned(),
            quantity: quantity.to_owned(),
            unit: unit.to_owned(),
            value: absolute,
        });
    }
    if let Some(value) = relative
        && (!value.is_finite() || value < 0.0)
    {
        errors.push(ValidationError::RelativeTolerance {
            path: path.to_owned(),
            quantity: quantity.to_owned(),
            unit: unit.to_owned(),
            value,
        });
    }
}

fn duplicate_input_names(entry: &Entry, function: &Function, errors: &mut Vec<ValidationError>) {
    let mut seen = BTreeSet::new();
    for value in &function.inputs {
        if !seen.insert(value.name()) {
            errors.push(ValidationKind::duplicate_name(value.name()).in_function(
                &entry.path,
                &function.name,
                "inputs",
            ));
        }
    }
}

fn duplicate_verification_case_ids(
    entry: &Entry,
    function: &Function,
    errors: &mut Vec<ValidationError>,
) {
    let mut seen = BTreeSet::new();
    for case in &function.verification_cases {
        if !seen.insert(&case.id) {
            errors.push(ValidationKind::duplicate_case(&case.id).in_function(
                &entry.path,
                &function.name,
                "verification_cases",
            ));
        }
    }
}

fn validate_enums(entry: &Entry, function: &Function, errors: &mut Vec<ValidationError>) {
    let mut validated = BTreeSet::new();
    for input in &function.inputs {
        let Some(enum_type) = input.enum_type() else {
            continue;
        };
        if !validated.insert(enum_type.identity()) {
            continue;
        }
        let mut names = BTreeSet::new();
        let mut values = BTreeSet::new();
        for member in &enum_type.values {
            if !names.insert(&member.name) {
                errors.push(
                    ValidationKind::duplicate_enum_name(&enum_type.enum_type.name, &member.name)
                        .in_function(&entry.path, &function.name, "$defs"),
                );
            }
            if !values.insert(&member.value) {
                errors.push(
                    ValidationKind::duplicate_enum_value(&enum_type.enum_type.name, &member.value)
                        .in_function(&entry.path, &function.name, "$defs"),
                );
            }
        }
        if enum_type.values.len() > u32::MAX as usize {
            errors.push(
                ValidationKind::enum_capacity(&enum_type.enum_type.name).in_function(
                    &entry.path,
                    &function.name,
                    "$defs",
                ),
            );
        }
    }
}

fn duplicate<K: Ord + Clone + std::fmt::Display>(
    map: &mut BTreeMap<K, PathBuf>,
    key: &K,
    entry: &Entry,
    path: &str,
    errors: &mut Vec<ValidationError>,
) {
    if let Some(previous) = map.insert(key.clone(), entry.path.clone()) {
        errors.push(ValidationError::DuplicateValue {
            document: entry.path.clone(),
            path: path.to_owned(),
            key: key.to_string(),
            previous,
        });
    }
}

fn duplicate_names(
    entry: &Entry,
    function: &Function,
    values: &[OutputField],
    field: &str,
    errors: &mut Vec<ValidationError>,
) {
    let mut seen = BTreeSet::new();
    for value in values {
        if !seen.insert(&value.name) {
            errors.push(ValidationKind::duplicate_name(&value.name).in_function(
                &entry.path,
                &function.name,
                field,
            ));
        }
    }
}
