use crate::model::{MeasurementDescriptor, MeasurementStatus, QuantityRegistry};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Compatibility {
    Exact,
    UnitConverted,
    ExactlyDerived,
    Estimated,
    Incompatible,
}

fn classify(
    required: &MeasurementDescriptor,
    available: &MeasurementDescriptor,
    registry: &QuantityRegistry,
) -> Compatibility {
    if required.quantity != available.quantity
        || required.basis != available.basis
        || required.particle_size != available.particle_size
        || required.conditions != available.conditions
        || required.method.is_some() && required.method != available.method
    {
        return Compatibility::Incompatible;
    }

    let unit_relation = if required.unit == available.unit {
        Compatibility::Exact
    } else if convertible(
        &required.quantity,
        &required.unit,
        &available.unit,
        registry,
    ) {
        Compatibility::UnitConverted
    } else {
        return Compatibility::Incompatible;
    };

    match available.status {
        MeasurementStatus::Observed | MeasurementStatus::Required => unit_relation,
        MeasurementStatus::Converted => Compatibility::UnitConverted,
        MeasurementStatus::Derived => Compatibility::ExactlyDerived,
        MeasurementStatus::Estimated | MeasurementStatus::Imputed => Compatibility::Estimated,
    }
}

fn convertible(quantity: &str, left: &str, right: &str, registry: &QuantityRegistry) -> bool {
    let Some(quantity) = registry.quantities.get(quantity) else {
        return false;
    };
    if !quantity.units.contains_key(left) || !quantity.units.contains_key(right) {
        return false;
    }
    let Some(left) = registry
        .units
        .get(left)
        .and_then(|unit| unit.conversion.as_ref())
    else {
        return false;
    };
    let Some(right) = registry
        .units
        .get(right)
        .and_then(|unit| unit.conversion.as_ref())
    else {
        return false;
    };
    left.dimension == right.dimension
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;

    use crate::model::{
        MeasurementDescriptor, MeasurementStatus, Quantity, QuantityRegistry, Unit,
    };

    use super::{Compatibility, classify};

    fn registry() -> QuantityRegistry {
        let quantities: BTreeMap<String, Quantity> = serde_yaml::from_str(
            r#"
saturated_hydraulic_conductivity:
  description: Conductivity.
  units:
    millimeter_per_hour: {absolute: 0.1, rationale: Test.}
    meter_per_second: {absolute: 1.0e-10, rationale: Test.}
particle_mass_fraction:
  description: Particle fraction.
  units:
    mass_percent: {absolute: 0.1, rationale: Test.}
"#,
        )
        .unwrap();
        let units: BTreeMap<String, Unit> = serde_yaml::from_str(
            r#"
millimeter_per_hour:
  preferred_notation: mm/h
  conversion: {dimension: length_per_time, scale_to_si: 2.7777777777777776e-7}
meter_per_second:
  preferred_notation: m/s
  conversion: {dimension: length_per_time, scale_to_si: 1.0}
mass_percent:
  preferred_notation: "% w/w"
  aliases: ["%"]
micrometer:
  preferred_notation: um
  conversion: {dimension: length, scale_to_si: 1.0e-6}
"#,
        )
        .unwrap();
        QuantityRegistry { quantities, units }
    }

    fn conductivity() -> MeasurementDescriptor {
        serde_yaml::from_str(
            r#"
quantity: saturated_hydraulic_conductivity
unit: millimeter_per_hour
reported_unit: mm/h
basis: {material: fine_earth, denominator: not_applicable}
status: required
role: observation
"#,
        )
        .unwrap()
    }

    fn clay() -> MeasurementDescriptor {
        serde_yaml::from_str(
            r#"
quantity: particle_mass_fraction
unit: mass_percent
reported_unit: "% w/w"
basis: {material: fine_earth, denominator: dry_mass}
particle_size:
  unit: micrometer
  lower: null
  upper: {value: 2, inclusive: false}
status: required
role: predictor
"#,
        )
        .unwrap()
    }

    #[test]
    fn distinguishes_the_five_compatibility_outcomes() {
        let registry = registry();
        let required = conductivity();

        let mut available = required.clone();
        available.status = MeasurementStatus::Observed;
        assert_eq!(
            classify(&required, &available, &registry),
            Compatibility::Exact
        );

        available.unit = "meter_per_second".into();
        available.reported_unit = "m/s".into();
        assert_eq!(
            classify(&required, &available, &registry),
            Compatibility::UnitConverted
        );

        available.unit = required.unit.clone();
        available.status = MeasurementStatus::Derived;
        assert_eq!(
            classify(&required, &available, &registry),
            Compatibility::ExactlyDerived
        );

        available.status = MeasurementStatus::Estimated;
        assert_eq!(
            classify(&required, &available, &registry),
            Compatibility::Estimated
        );

        available.quantity = "volumetric_water_content".into();
        assert_eq!(
            classify(&required, &available, &registry),
            Compatibility::Incompatible
        );
    }

    #[test]
    fn does_not_interchange_one_and_two_micrometer_particle_fractions() {
        let registry = registry();
        let required = clay();
        let mut available = required.clone();
        available.status = MeasurementStatus::Observed;
        available
            .particle_size
            .as_mut()
            .unwrap()
            .upper
            .as_mut()
            .unwrap()
            .value = 1.0;

        assert_eq!(
            classify(&required, &available, &registry),
            Compatibility::Incompatible
        );
    }
}
