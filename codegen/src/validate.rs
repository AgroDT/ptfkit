mod error;
pub(crate) use error::{ValidationError, ValidationKind};

use std::{
    collections::{BTreeMap, BTreeSet},
    path::PathBuf,
};

use crate::model::{
    Entry, Function, Input, MeasurementBound, MeasurementDescriptor, MeasurementRole,
    MeasurementStatus, OutputField, QuantityRegistry,
};

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
            validate_measurements(entry, function, &mut errors);
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

fn validate_measurements(entry: &Entry, function: &Function, errors: &mut Vec<ValidationError>) {
    for input in &function.inputs {
        let Input::Parameter(parameter) = input else {
            continue;
        };
        let Some(measurement) = &parameter.measurement else {
            continue;
        };
        if parameter.unit != measurement.reported_unit {
            invalid_measurement(
                entry,
                function,
                &parameter.name,
                format!(
                    "reported_unit `{}` does not match legacy unit `{}`",
                    measurement.reported_unit, parameter.unit
                ),
                errors,
            );
        }
        if measurement.role != MeasurementRole::Predictor
            || measurement.status != MeasurementStatus::Required
        {
            invalid_measurement(
                entry,
                function,
                &parameter.name,
                "must use role `predictor` and status `required`",
                errors,
            );
        }
        validate_measurement(entry, function, &parameter.name, measurement, errors);
    }

    for field in function.outputs.fields() {
        let Some(measurement) = &field.measurement else {
            continue;
        };
        if field.quantity != measurement.quantity
            || field.unit != measurement.unit
            || field.reported_unit != measurement.reported_unit
        {
            invalid_measurement(
                entry,
                function,
                &field.name,
                "does not match the legacy output quantity and unit fields",
                errors,
            );
        }
        if !matches!(
            measurement.role,
            MeasurementRole::Prediction
                | MeasurementRole::ModelParameter
                | MeasurementRole::Uncertainty
        ) || !matches!(
            measurement.status,
            MeasurementStatus::Estimated | MeasurementStatus::Derived
        ) {
            invalid_measurement(
                entry,
                function,
                &field.name,
                "has an invalid output role or status",
                errors,
            );
        }
        validate_measurement(entry, function, &field.name, measurement, errors);
    }
}

fn validate_measurement(
    entry: &Entry,
    function: &Function,
    name: &str,
    measurement: &MeasurementDescriptor,
    errors: &mut Vec<ValidationError>,
) {
    validate_quantity_unit(
        entry,
        function,
        name,
        &measurement.quantity,
        &measurement.unit,
        Some(&measurement.reported_unit),
        errors,
    );
    if let Some(interval) = &measurement.particle_size {
        match entry.quantities.units.get(&interval.unit) {
            None => invalid_measurement(
                entry,
                function,
                name,
                format!(
                    "particle-size interval references unknown unit `{}`",
                    interval.unit
                ),
                errors,
            ),
            Some(unit)
                if unit
                    .conversion
                    .as_ref()
                    .is_none_or(|conversion| conversion.dimension != "length") =>
            {
                invalid_measurement(
                    entry,
                    function,
                    name,
                    format!(
                        "particle-size interval unit `{}` must have length conversion metadata",
                        interval.unit
                    ),
                    errors,
                );
            }
            Some(_) => {}
        }
        validate_interval_bounds(
            entry,
            function,
            name,
            &interval.lower,
            &interval.upper,
            errors,
        );
    }
    if let Some(interval) = &measurement.computational_domain {
        validate_interval_bounds(
            entry,
            function,
            name,
            &interval.lower,
            &interval.upper,
            errors,
        );
    }
    let mut conditions = BTreeSet::new();
    for condition in &measurement.conditions {
        if !conditions.insert(&condition.quantity) {
            invalid_measurement(
                entry,
                function,
                name,
                format!("contains duplicate condition `{}`", condition.quantity),
                errors,
            );
        }
        if !condition.value.is_finite() {
            invalid_measurement(
                entry,
                function,
                name,
                format!("condition `{}` must be finite", condition.quantity),
                errors,
            );
        }
        validate_quantity_unit(
            entry,
            function,
            name,
            &condition.quantity,
            &condition.unit,
            None,
            errors,
        );
    }
    for constraint in &measurement.reported_applicability {
        if let Some(unit) = &constraint.unit
            && !entry.quantities.units.contains_key(unit)
        {
            invalid_measurement(
                entry,
                function,
                name,
                format!("applicability constraint references unknown unit `{unit}`"),
                errors,
            );
        }
    }
}

fn validate_quantity_unit(
    entry: &Entry,
    function: &Function,
    name: &str,
    quantity_id: &str,
    unit_id: &str,
    reported_unit: Option<&str>,
    errors: &mut Vec<ValidationError>,
) {
    let Some(quantity) = entry.quantities.quantities.get(quantity_id) else {
        invalid_measurement(
            entry,
            function,
            name,
            format!("references unknown quantity `{quantity_id}`"),
            errors,
        );
        return;
    };
    let Some(unit) = entry.quantities.units.get(unit_id) else {
        invalid_measurement(
            entry,
            function,
            name,
            format!("references unknown unit `{unit_id}`"),
            errors,
        );
        return;
    };
    if !quantity.units.contains_key(unit_id) {
        invalid_measurement(
            entry,
            function,
            name,
            format!("quantity `{quantity_id}` has no registered unit `{unit_id}`"),
            errors,
        );
    }
    if let Some(reported) = reported_unit
        && reported != unit.preferred_notation
        && !unit.aliases.iter().any(|alias| alias == reported)
    {
        invalid_measurement(
            entry,
            function,
            name,
            format!(
                "reported_unit `{reported}` is not an equivalent notation for unit `{unit_id}`"
            ),
            errors,
        );
    }
}

fn validate_interval_bounds(
    entry: &Entry,
    function: &Function,
    name: &str,
    lower: &Option<MeasurementBound>,
    upper: &Option<MeasurementBound>,
    errors: &mut Vec<ValidationError>,
) {
    if lower.is_none() && upper.is_none() {
        invalid_measurement(
            entry,
            function,
            name,
            "interval requires at least one bound",
            errors,
        );
    }
    for bound in [lower, upper].into_iter().flatten() {
        if !bound.value.is_finite() {
            invalid_measurement(
                entry,
                function,
                name,
                "interval bounds must be finite",
                errors,
            );
        }
    }
    if let (Some(lower), Some(upper)) = (lower, upper)
        && (lower.value > upper.value
            || (lower.value == upper.value && (!lower.inclusive || !upper.inclusive)))
    {
        invalid_measurement(
            entry,
            function,
            name,
            "interval lower bound must precede its upper bound",
            errors,
        );
    }
}

fn invalid_measurement(
    entry: &Entry,
    function: &Function,
    name: &str,
    detail: impl Into<String>,
    errors: &mut Vec<ValidationError>,
) {
    errors.push(
        ValidationKind::invalid_measurement(name, detail).in_function(
            &entry.path,
            &function.name,
            "measurement",
        ),
    );
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
        if let Some(conversion) = &unit.conversion
            && (!valid_identifier(&conversion.dimension)
                || !conversion.scale_to_si.is_finite()
                || conversion.scale_to_si <= 0.0
                || !conversion.offset_to_si.is_finite())
        {
            errors.push(ValidationError::InvalidUnitConversion { id: id.clone() });
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
