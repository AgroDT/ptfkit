use std::{fs, path::Path};

use anyhow::{Result, bail};
use jsonschema::Draft;
use serde_json::Value;

use crate::{
    formula,
    model::{
        Entry, Implementation, ImplementationOutput, RawExpression, RawField, RawFunction,
        RawInput, RawOutput, RawVariable, Spec,
    },
    semantic,
};

/// Temporary frontend compatibility boundary. Remove the `None` branch when
/// every source specification provides an implementation.
pub(crate) fn load(root: &Path) -> Result<Vec<Entry>> {
    let schema: Value =
        serde_json::from_slice(&fs::read(root.join("specs/schema/ptf-spec.schema.json"))?)?;
    let validator = jsonschema::options()
        .with_draft(Draft::Draft202012)
        .build(&schema)?;
    let mut paths =
        fs::read_dir(root.join("specs/functions"))?.collect::<std::result::Result<Vec<_>, _>>()?;
    paths.sort_by_key(|entry| entry.path());

    let mut entries = Vec::new();
    let mut errors = Vec::new();
    for path in paths.into_iter().map(|entry| entry.path()).filter(|path| {
        path.extension()
            .is_some_and(|extension| extension == "yaml")
    }) {
        let text = fs::read_to_string(&path)?;
        let yaml_value: serde_yaml::Value = match serde_yaml::from_str(&text) {
            Ok(value) => value,
            Err(error) => {
                errors.push(format!(
                    "{}:\n  $:\n    malformed YAML: {error}",
                    path.display()
                ));
                continue;
            }
        };
        let value = match serde_json::to_value(yaml_value) {
            Ok(value) => value,
            Err(error) => {
                errors.push(format!(
                    "{}:\n  $:\n    YAML cannot be represented as JSON: {error}",
                    path.display()
                ));
                continue;
            }
        };
        for error in validator.iter_errors(&value) {
            errors.push(format!(
                "{}:\n  {}:\n    {}",
                path.display(),
                json_path(error.instance_path()),
                error
            ));
        }
        let spec: Spec = match serde_json::from_value(value) {
            Ok(spec) => spec,
            Err(error) => {
                errors.push(format!(
                    "{}:\n  $:\n    metadata cannot be read: {error}",
                    path.display()
                ));
                continue;
            }
        };
        let implementations = spec
            .functions
            .iter()
            .map(|function| match &function.implementation {
                Some(implementation) => compile(&path, function, implementation).map(Some),
                None => Ok(None),
            })
            .collect::<Result<Vec<_>, _>>();
        match implementations {
            Ok(implementations) => entries.push(Entry {
                path,
                spec,
                implementations,
            }),
            Err(error) => errors.push(error),
        }
    }
    if !errors.is_empty() {
        bail!("validation failed:\n{}", errors.join("\n"))
    }
    Ok(entries)
}

fn compile(
    path: &Path,
    function: &crate::model::Function,
    implementation: &Implementation,
) -> Result<semantic::Function, String> {
    let raw = RawFunction {
        specification_path: path.to_owned(),
        name: function.name.clone(),
        inputs: function
            .inputs
            .iter()
            .map(|input| RawInput {
                name: input.name.clone(),
            })
            .collect(),
        variables: implementation
            .variables
            .iter()
            .enumerate()
            .map(|(index, variable)| {
                expression(
                    path,
                    &function.name,
                    format!("implementation.variables[{index}].expr"),
                    &variable.expr,
                )
                .map(|expression| RawVariable {
                    name: variable.name.clone(),
                    expression,
                })
            })
            .collect::<Result<Vec<_>, _>>()?,
        output: match &implementation.output {
            ImplementationOutput::Scalar { expr } => RawOutput::Scalar(expression(
                path,
                &function.name,
                "implementation.output.expr".into(),
                expr,
            )?),
            ImplementationOutput::Record { fields } => RawOutput::Record(
                fields
                    .iter()
                    .enumerate()
                    .map(|(index, field)| {
                        expression(
                            path,
                            &function.name,
                            format!("implementation.output.fields[{index}].expr"),
                            &field.expr,
                        )
                        .map(|expression| RawField {
                            name: field.name.clone(),
                            expression,
                        })
                    })
                    .collect::<Result<Vec<_>, _>>()?,
            ),
        },
    };
    validate_output(path, function, &raw.output)?;
    semantic::compile(&raw).map_err(|error| error.to_string())
}

fn expression(
    path: &Path,
    function: &str,
    implementation_path: String,
    source: &str,
) -> Result<RawExpression, String> {
    let location = format!(
        "{} -> function {function} -> {implementation_path}",
        path.display()
    );
    formula::parse(location, source)
        .map(|expression| RawExpression {
            implementation_path,
            expression,
        })
        .map_err(|error| error.to_string())
}

fn validate_output(
    path: &Path,
    function: &crate::model::Function,
    output: &RawOutput,
) -> Result<(), String> {
    let expected = function
        .outputs
        .iter()
        .map(|output| &output.name)
        .collect::<Vec<_>>();
    let actual: Vec<_> = match output {
        RawOutput::Scalar(_) => {
            if expected.len() == 1 {
                return Ok(());
            }
            return Err(format!(
                "{} -> function {} -> implementation.output: scalar implementation requires exactly one output, found {}",
                path.display(),
                function.name,
                expected.len()
            ));
        }
        RawOutput::Record(fields) => fields.iter().map(|field| &field.name).collect(),
    };
    if actual == expected {
        Ok(())
    } else {
        Err(format!(
            "{} -> function {} -> implementation.output.fields: field names {:?} do not match outputs {:?}",
            path.display(),
            function.name,
            actual,
            expected
        ))
    }
}

fn json_path(path: &impl std::fmt::Display) -> String {
    let path = path.to_string();
    if path.is_empty() {
        "$".into()
    } else {
        path.trim_start_matches('/').replace('/', ".")
    }
}

#[cfg(test)]
mod tests {
    use std::{
        fs,
        path::{Path, PathBuf},
    };

    use super::load;
    use crate::model::PythonGeneration;

    fn fixture_root(label: &str) -> PathBuf {
        let root = std::env::temp_dir().join(format!(
            "ptfkit-codegen-specs-{label}-{}-{}",
            std::process::id(),
            line!()
        ));
        fs::create_dir_all(root.join("specs/functions")).unwrap();
        fs::create_dir_all(root.join("specs/schema")).unwrap();
        fs::copy(
            Path::new(env!("CARGO_MANIFEST_DIR")).join("../../specs/schema/ptf-spec.schema.json"),
            root.join("specs/schema/ptf-spec.schema.json"),
        )
        .unwrap();
        root
    }

    fn specification(key: &str, implementation: &str, generation: &str) -> String {
        format!(
            "source:\n  key: {key}\n  summary: Test source.\n  citation_apa: Test (2026).\n  doi: null\n{generation}functions:\n  - name: calc_ptf_{key}\n    status: ready-for-implementation\n    public_api: {{name: calc_ptf_{key}, result_class: null, summary: Test value.}}\n    scope:\n      prediction_target: Test value.\n      models: {{h_theta: null, k_h: null}}\n    inputs:\n      - {{name: x, symbol: x, unit: '1', domain: null, description: Test input.}}\n    outputs:\n      - {{name: value, symbol: y, unit: '1', domain: null, description: Test output.}}\n{implementation}"
        )
    }

    fn write(root: &Path, key: &str, implementation: &str, generation: &str) {
        fs::write(
            root.join(format!("specs/functions/{key}.yaml")),
            specification(key, implementation, generation),
        )
        .unwrap();
    }

    #[test]
    fn loads_standalone_yaml_with_pilot_and_legacy_functions() {
        let root = fixture_root("mixed");
        write(
            &root,
            "pilot",
            "    implementation:\n      output: {type: scalar, expr: x * 2}\n",
            "",
        );
        write(&root, "legacy", "", "");

        let entries = load(&root).unwrap();
        assert_eq!(entries.len(), 2);
        assert!(entries[1].implementations[0].is_some());
        assert!(entries[0].implementations[0].is_none());
        assert_eq!(
            entries[0].spec.generation.public_python,
            PythonGeneration::Generated
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn reports_schema_formula_and_output_contract_errors() {
        let root = fixture_root("errors");
        write(&root, "schema", "", "unknown: value\n");
        let error = load(&root).err().expect("schema must fail").to_string();
        assert!(error.contains("Additional properties are not allowed"));
        fs::remove_file(root.join("specs/functions/schema.yaml")).unwrap();

        write(
            &root,
            "formula",
            "    implementation:\n      output: {type: scalar, expr: '('}\n",
            "",
        );
        let error = load(&root).err().expect("formula must fail").to_string();
        assert!(error.contains("implementation.output.expr"));
        fs::remove_file(root.join("specs/functions/formula.yaml")).unwrap();

        write(
            &root,
            "output",
            "    implementation:\n      output:\n        type: record\n        fields: [{name: other, expr: x}]\n",
            "",
        );
        let error = load(&root)
            .err()
            .expect("output contract must fail")
            .to_string();
        assert!(error.contains("field names"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn parses_manual_public_python_policy() {
        let root = fixture_root("manual");
        write(
            &root,
            "manual",
            "    implementation:\n      output: {type: scalar, expr: x}\n",
            "generation:\n  public_python: manual\n",
        );
        let entries = load(&root).unwrap();
        assert_eq!(
            entries[0].spec.generation.public_python,
            PythonGeneration::Manual
        );
        fs::remove_dir_all(root).unwrap();
    }
}
