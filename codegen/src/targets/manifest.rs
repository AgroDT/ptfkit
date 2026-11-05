use std::{collections::BTreeMap, path::PathBuf};

use serde::Serialize;
use serde_json::Value;

use crate::{
    model::{
        Entry, EnumDefinition, EnumValue, Function, Input, MeasurementDescriptor, Models, Quantity,
        Unit,
    },
    output::GeneratedFile,
};

use super::Result;

const GENERATED_BY: &str = "ptfkit-codegen; DO NOT EDIT.";

#[derive(Serialize)]
struct Manifest<'a> {
    #[serde(rename = "_generated")]
    generated: &'static str,
    schema_version: u8,
    ptfkit_version: &'a str,
    coverage: Coverage,
    units: &'a BTreeMap<String, Unit>,
    quantities: BTreeMap<&'a str, ManifestQuantity<'a>>,
    functions: Vec<ManifestFunction<'a>>,
}

#[derive(Serialize)]
struct Coverage {
    implemented_functions: usize,
    manifest_functions: usize,
    omitted_functions: Vec<OmittedFunction>,
}

#[derive(Serialize)]
struct OmittedFunction {
    id: String,
    reason: &'static str,
}

#[derive(Serialize)]
struct ManifestQuantity<'a> {
    description: &'a str,
    units: Vec<&'a str>,
}

#[derive(Serialize)]
struct ManifestFunction<'a> {
    id: &'a str,
    source: &'a str,
    module: String,
    callable: &'a str,
    status: &'a str,
    models: &'a Models,
    warnings: &'a [String],
    inputs: Vec<Binding<'a>>,
    outputs: Vec<Binding<'a>>,
}

#[derive(Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum Binding<'a> {
    Numeric {
        name: &'a str,
        measurement: &'a MeasurementDescriptor,
    },
    Categorical {
        name: &'a str,
        #[serde(rename = "enum")]
        enumeration: ManifestEnum<'a>,
    },
}

#[derive(Serialize)]
struct ManifestEnum<'a> {
    id: String,
    description: &'a str,
    values: &'a [EnumValue],
}

pub(super) fn render(entries: &[Entry], version: &str) -> Result<Vec<GeneratedFile>> {
    let registry = entries.first().map(|entry| entry.quantities.as_ref());
    let empty_units = BTreeMap::new();
    let units = registry.map_or(&empty_units, |registry| &registry.units);
    let quantities = registry.map_or_else(BTreeMap::new, |registry| {
        registry
            .quantities
            .iter()
            .map(|(id, quantity)| (id.as_str(), manifest_quantity(quantity)))
            .collect()
    });

    let mut implemented_functions = 0;
    let mut functions = Vec::new();
    let mut omitted_functions = Vec::new();
    for entry in entries {
        for function in &entry.spec.functions {
            if function.status != "implemented" {
                continue;
            }
            implemented_functions += 1;
            if complete(function) {
                functions.push(manifest_function(entry, function));
            } else {
                omitted_functions.push(OmittedFunction {
                    id: function.name.clone(),
                    reason: "incomplete_measurement_contract",
                });
            }
        }
    }
    functions.sort_by_key(|function| function.id);
    omitted_functions.sort_by(|left, right| left.id.cmp(&right.id));

    let manifest = Manifest {
        generated: GENERATED_BY,
        schema_version: 1,
        ptfkit_version: version,
        coverage: Coverage {
            implemented_functions,
            manifest_functions: functions.len(),
            omitted_functions,
        },
        units,
        quantities,
        functions,
    };
    let value = serde_json::to_value(&manifest)?;
    validate(&value)?;
    let mut contents = serde_json::to_string_pretty(&value)?;
    contents.push('\n');
    Ok(vec![GeneratedFile::new(
        PathBuf::from("ptfkit/_manifest.json"),
        contents,
    )])
}

fn validate(value: &Value) -> Result<()> {
    let measurement: Value = serde_json::from_str(include_str!(
        "../../../specs/schema/measurement.schema.json"
    ))
    .expect("committed measurement schema is valid JSON");
    let schema: Value = serde_json::from_str(include_str!(
        "../../../specs/schema/ptf-manifest.schema.json"
    ))
    .expect("committed manifest schema is valid JSON");
    let registry = jsonschema::Registry::new()
        .add(
            "https://ptfkit.invalid/measurement.schema.json",
            measurement,
        )
        .expect("committed measurement schema has a valid identifier")
        .prepare()
        .expect("committed measurement schema references resolve");
    let validator = jsonschema::options()
        .with_draft(jsonschema::Draft::Draft202012)
        .with_registry(&registry)
        .build(&schema)
        .expect("committed manifest schema references resolve");
    let diagnostics = validator
        .iter_errors(value)
        .map(|error| format!("{}: {error}", error.instance_path()))
        .collect::<Vec<_>>();
    if diagnostics.is_empty() {
        Ok(())
    } else {
        Err(super::GenerationError::InvalidManifest {
            diagnostics: diagnostics.join("\n"),
        })
    }
}

fn manifest_quantity(quantity: &Quantity) -> ManifestQuantity<'_> {
    ManifestQuantity {
        description: &quantity.description,
        units: quantity.units.keys().map(String::as_str).collect(),
    }
}

fn complete(function: &Function) -> bool {
    function.inputs.iter().all(|input| match input {
        Input::Parameter(parameter) => parameter.measurement.is_some(),
        Input::Enum { .. } => true,
    }) && function
        .outputs
        .fields()
        .iter()
        .all(|field| field.measurement.is_some())
}

fn manifest_function<'a>(entry: &'a Entry, function: &'a Function) -> ManifestFunction<'a> {
    ManifestFunction {
        id: &function.name,
        source: &entry.slug,
        module: format!("ptfkit.{}", entry.slug),
        callable: &function.public_api.name,
        status: &function.status,
        models: &function.scope.models,
        warnings: &function.documentation.warnings,
        inputs: function
            .inputs
            .iter()
            .map(|input| manifest_input(&entry.slug, input))
            .collect(),
        outputs: function
            .outputs
            .fields()
            .iter()
            .map(|field| Binding::Numeric {
                name: &field.name,
                measurement: field
                    .measurement
                    .as_deref()
                    .expect("complete function has described outputs"),
            })
            .collect(),
    }
}

fn manifest_input<'a>(source: &str, input: &'a Input) -> Binding<'a> {
    match input {
        Input::Parameter(parameter) => Binding::Numeric {
            name: &parameter.name,
            measurement: parameter
                .measurement
                .as_deref()
                .expect("complete function has described numeric inputs"),
        },
        Input::Enum {
            name, definition, ..
        } => Binding::Categorical {
            name,
            enumeration: manifest_enum(source, definition),
        },
    }
}

fn manifest_enum<'a>(source: &str, definition: &'a EnumDefinition) -> ManifestEnum<'a> {
    let enum_type = definition.identity();
    let module = enum_type.shared_module.as_deref().unwrap_or(source);
    ManifestEnum {
        id: format!("{module}.{}", enum_type.name),
        description: &definition.description,
        values: &definition.values,
    }
}

#[cfg(test)]
mod tests {
    use std::{fs, path::Path};

    use super::render;

    #[test]
    fn emits_only_complete_functions_and_preserves_binding_order() {
        let root = crate::test_support::fixture_root("manifest-coverage");
        let descriptor = |status: &str, role: &str| {
            format!(
                "measurement: {{quantity: volumetric_water_content, unit: volume_fraction, reported_unit: '1', basis: {{material: fine_earth, denominator: bulk_volume}}, particle_size: null, conditions: [], status: {status}, method: null, role: {role}, computational_domain: {{lower: {{value: 0, inclusive: true}}, upper: {{value: 1, inclusive: true}}}}, reported_applicability: []}}"
            )
        };
        let mut source = include_str!("../fixtures/source.yaml").to_owned();
        source = source.replace(
            "- {name: x, unit: '1', symbol: null, domain: null, description: Input value.}",
            &format!(
                "- {{name: x, unit: '1', symbol: null, {}, domain: null, description: Input value.}}",
                descriptor("required", "predictor")
            ),
        );
        for name in ["first", "second"] {
            source = source.replace(
                &format!("name: {name}, quantity:"),
                &format!(
                    "name: {name}, {}, quantity:",
                    descriptor("estimated", "prediction")
                ),
            );
        }
        fs::write(root.join("specs/functions/example.yaml"), source).unwrap();

        let entries = crate::load_validated_specifications(&root).unwrap();
        let files = render(&entries, "9.8.7").unwrap();
        let mut reversed = entries.clone();
        for entry in &mut reversed {
            entry.spec.functions.reverse();
        }
        let reversed_files = render(&reversed, "9.8.7").unwrap();
        assert_eq!(files[0].contents, reversed_files[0].contents);
        let manifest: serde_json::Value = serde_json::from_str(&files[0].contents).unwrap();
        assert_eq!(manifest["coverage"]["implemented_functions"], 2);
        assert_eq!(manifest["coverage"]["manifest_functions"], 1);
        assert_eq!(
            manifest["coverage"]["omitted_functions"][0]["id"],
            "calc_ptf_example_scalar"
        );
        assert_eq!(
            manifest["functions"][0]["callable"],
            "calc_ptf_example_record"
        );
        assert_eq!(
            manifest["functions"][0]["outputs"]
                .as_array()
                .unwrap()
                .iter()
                .map(|output| output["name"].as_str().unwrap())
                .collect::<Vec<_>>(),
            ["first", "second"]
        );
        assert_eq!(manifest["ptfkit_version"], "9.8.7");
        assert_eq!(files[0].path, Path::new("ptfkit/_manifest.json"));
        fs::remove_dir_all(root).unwrap();
    }
}
