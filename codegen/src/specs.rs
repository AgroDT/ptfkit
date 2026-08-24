use std::{fs, path::Path};

use anyhow::{Result, bail};
use jsonschema::Draft;
use serde_json::Value;

use crate::{
    adapters::Registry,
    formula,
    model::{
        Entry, Implementation, RawDerivedInput, RawExpression, RawFunction, RawInput, RawVariable,
        Spec, TestValue,
    },
    semantic,
};

#[cfg(test)]
pub(crate) fn load(root: &Path) -> Result<Vec<Entry>> {
    let adapters = Registry::load(root)?;
    load_with_registry(root, &adapters)
}

pub(crate) fn load_with_registry(root: &Path, adapters: &Registry) -> Result<Vec<Entry>> {
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
        let slug = match source_slug(&path) {
            Ok(slug) => slug,
            Err(error) => {
                errors.push(error);
                continue;
            }
        };
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
        for function in &spec.functions {
            if matches!(
                function.status.as_str(),
                "implemented" | "ready-for-implementation"
            ) && function.implementation.is_none()
            {
                errors.push(format!(
                    "{} -> function {} -> implementation: required for status `{}`",
                    path.display(),
                    function.name,
                    function.status
                ));
            }
        }
        let implementations = spec
            .functions
            .iter()
            .map(|function| match &function.implementation {
                Some(implementation) => {
                    compile(&path, function, implementation, adapters).map(Some)
                }
                None => Ok(None),
            })
            .collect::<Result<Vec<_>, _>>();
        match implementations {
            Ok(implementations) => entries.push(Entry {
                path,
                slug,
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

fn source_slug(path: &Path) -> Result<String, String> {
    let Some(stem) = path.file_stem().and_then(|stem| stem.to_str()) else {
        return Err(format!(
            "{}:\n  $:\n    specification filename must have a UTF-8 stem",
            path.display()
        ));
    };
    let valid = stem
        .chars()
        .enumerate()
        .all(|(index, character)| match index {
            0 => character.is_ascii_lowercase(),
            _ => character.is_ascii_lowercase() || character.is_ascii_digit() || character == '_',
        });
    if !stem.is_empty() && valid {
        Ok(stem.to_owned())
    } else {
        Err(format!(
            "{}:\n  $:\n    specification filename stem must be an APA-style slug matching ^[a-z][a-z0-9_]*$",
            path.display()
        ))
    }
}

fn compile(
    path: &Path,
    function: &crate::model::Function,
    implementation: &Implementation,
    adapters: &Registry,
) -> Result<semantic::Function, String> {
    let mut derived_inputs = Vec::new();
    for input in &function.inputs {
        if !input.r#type.is_numeric() && adapters.adapter_for_type(input.r#type.as_str()).is_none()
        {
            return Err(format!(
                "{} -> function {} -> inputs: unknown registered input type `{}`",
                path.display(),
                function.name,
                input.r#type.as_str()
            ));
        }
    }
    let mut bound_sources = std::collections::BTreeSet::new();
    for (binding_index, binding) in function.derived_inputs.iter().enumerate() {
        let adapter = adapters.adapter(&binding.adapter).ok_or_else(|| format!("{} -> function {} -> derived_inputs[{binding_index}].adapter: unknown adapter `{}`", path.display(), function.name, binding.adapter))?;
        let input_index = function.inputs.iter().position(|input| input.name == binding.input).ok_or_else(|| format!("{} -> function {} -> derived_inputs[{binding_index}].input: unknown public input `{}`", path.display(), function.name, binding.input))?;
        let input = &function.inputs[input_index];
        if input.r#type.as_str() != adapter.input_type.name {
            return Err(format!(
                "{} -> function {} -> derived_inputs[{binding_index}].input: input `{}` has type `{}`, expected `{}`",
                path.display(),
                function.name,
                input.name,
                input.r#type.as_str(),
                adapter.input_type.name
            ));
        }
        if binding.evidence.trim().is_empty() {
            return Err(format!(
                "{} -> function {} -> derived_inputs[{binding_index}].evidence: must contain source-backed evidence",
                path.display(),
                function.name
            ));
        }
        for (component, symbol) in &binding.components {
            if !adapter
                .outputs
                .iter()
                .any(|output| output.name == *component)
            {
                return Err(format!(
                    "{} -> function {} -> derived_inputs[{binding_index}].components: unknown adapter component `{component}`",
                    path.display(),
                    function.name
                ));
            }
            if !bound_sources.insert((binding.adapter.clone(), input_index, component.clone())) {
                return Err(format!(
                    "{} -> function {} -> derived_inputs[{binding_index}].components: conflicting duplicate binding for `{component}`",
                    path.display(),
                    function.name
                ));
            }
            derived_inputs.push(RawDerivedInput {
                adapter: binding.adapter.clone(),
                input_index,
                component: component.clone(),
                symbol: symbol.clone(),
                evidence: binding.evidence.clone(),
            });
        }
    }
    let raw = RawFunction {
        specification_path: path.to_owned(),
        name: function.name.clone(),
        inputs: function
            .inputs
            .iter()
            .map(|input| RawInput {
                name: input.name.clone(),
                r#type: input.r#type.clone(),
            })
            .collect(),
        derived_inputs,
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
    };
    validate_output(path, function, &raw)?;
    let semantic = semantic::compile(&raw).map_err(|error| error.to_string())?;
    validate_golden_inputs(path, function, adapters)?;
    Ok(semantic)
}

fn validate_golden_inputs(
    path: &Path,
    function: &crate::model::Function,
    adapters: &Registry,
) -> Result<(), String> {
    for case in &function.golden_tests {
        for input in &function.inputs {
            let value = case.inputs.get(&input.name).ok_or_else(|| {
                format!(
                    "{} -> function {} -> golden test `{}`: missing input `{}`",
                    path.display(),
                    function.name,
                    case.id,
                    input.name
                )
            })?;
            match (input.r#type.is_numeric(), value) {
                (true, TestValue::Number(_)) => {}
                (false, TestValue::Category(category)) => {
                    let adapter = adapters
                        .adapter_for_type(input.r#type.as_str())
                        .expect("input type was resolved");
                    if !adapter.input_type.categories.contains(category) {
                        return Err(format!(
                            "{} -> function {} -> golden test `{}`: invalid `{}` value `{category}`",
                            path.display(),
                            function.name,
                            case.id,
                            input.r#type.as_str()
                        ));
                    }
                }
                (true, _) => {
                    return Err(format!(
                        "{} -> function {} -> golden test `{}`: numeric input `{}` requires a number",
                        path.display(),
                        function.name,
                        case.id,
                        input.name
                    ));
                }
                (false, _) => {
                    return Err(format!(
                        "{} -> function {} -> golden test `{}`: categorical input `{}` requires an exact canonical string",
                        path.display(),
                        function.name,
                        case.id,
                        input.name
                    ));
                }
            }
        }
    }
    Ok(())
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
    raw: &RawFunction,
) -> Result<(), String> {
    let output_names = function
        .outputs
        .fields()
        .iter()
        .map(|output| &output.name)
        .collect::<Vec<_>>();
    let output_sources = raw
        .inputs
        .iter()
        .filter(|input| input.r#type.is_numeric())
        .map(|input| input.name.as_str())
        .chain(raw.derived_inputs.iter().map(|input| input.symbol.as_str()))
        .chain(raw.variables.iter().map(|variable| variable.name.as_str()))
        .collect::<std::collections::BTreeSet<_>>();
    let missing = output_names
        .iter()
        .filter(|name| !output_sources.contains(name.as_str()))
        .collect::<Vec<_>>();
    if missing.is_empty() {
        Ok(())
    } else {
        Err(format!(
            "{} -> function {} -> implementation.variables: missing final output variables {:?}",
            path.display(),
            function.name,
            missing
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
        fs::create_dir_all(root.join("specs/adapters")).unwrap();
        fs::copy(
            Path::new(env!("CARGO_MANIFEST_DIR")).join("../specs/schema/ptf-spec.schema.json"),
            root.join("specs/schema/ptf-spec.schema.json"),
        )
        .unwrap();
        for name in ["usda_texture.yaml", "usda_texture.schema.json"] {
            fs::copy(
                Path::new(env!("CARGO_MANIFEST_DIR"))
                    .join("../specs/adapters")
                    .join(name),
                root.join("specs/adapters").join(name),
            )
            .unwrap();
        }
        root
    }

    fn specification(slug: &str, implementation: &str, generation: &str) -> String {
        format!(
            "source:\n  summary: Test source.\n  citation_apa: Test (2026).\n  doi: null\n{generation}functions:\n  - name: calc_ptf_{slug}\n    status: ready-for-implementation\n    public_api: {{name: calc_ptf_{slug}, result_class: null, summary: Test value.}}\n    scope:\n      prediction_target: Test value.\n      models: {{h_theta: null, k_h: null}}\n    inputs:\n      - {{name: x, symbol: x, unit: '1', domain: null, description: Test input.}}\n    outputs: {{type: scalar, name: value, symbol: y, unit: '1', domain: null, description: Test output.}}\n{implementation}"
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
    fn rejects_a_code_generating_function_without_implementation() {
        let root = fixture_root("mixed");
        write(
            &root,
            "pilot",
            "    implementation:\n      variables: [{name: value, expr: x * 2}]\n",
            "",
        );
        write(&root, "legacy", "", "");

        let error = load(&root).unwrap_err().to_string();
        assert!(error.contains("implementation\" is a required property"));
        assert!(error.contains("required for status `ready-for-implementation`"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn permits_an_output_to_reuse_a_same_named_input() {
        let root = fixture_root("input-output");
        let specification = specification(
            "input_output",
            "    implementation:\n      variables: [{name: intermediate, expr: value}]\n",
            "",
        )
        .replace(
            "{name: x, symbol: x, unit: '1', domain: null, description: Test input.}",
            "{name: value, symbol: x, unit: '1', domain: null, description: Test input.}",
        );
        fs::write(
            root.join("specs/functions/input_output.yaml"),
            specification,
        )
        .unwrap();

        let entries = load(&root).unwrap();
        assert!(entries[0].implementations[0].is_some());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_an_inline_record_without_a_name() {
        let root = fixture_root("unnamed-record");
        let specification = specification(
            "unnamed_record",
            "    implementation:\n      variables: [{name: first, expr: x}, {name: second, expr: x}]\n",
            "",
        )
        .replace(
            "outputs: {type: scalar, name: value, symbol: y, unit: '1', domain: null, description: Test output.}",
            "outputs:\n      type: record\n      fields:\n      - {name: first, symbol: y_1, unit: '1', domain: null, description: First output.}\n      - {name: second, symbol: y_2, unit: '1', domain: null, description: Second output.}",
        );
        fs::write(
            root.join("specs/functions/unnamed_record.yaml"),
            specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("unnamed inline record must fail")
            .to_string();
        assert!(error.contains("functions.0.outputs"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_a_non_pascal_case_record_name() {
        let root = fixture_root("non-pascal-case-record");
        let specification = specification(
            "non_pascal_case_record",
            "    implementation:\n      variables: [{name: first, expr: x}, {name: second, expr: x}]\n",
            "",
        )
        .replace(
            "outputs: {type: scalar, name: value, symbol: y, unit: '1', domain: null, description: Test output.}",
            "outputs:\n      type: record\n      name: result_record\n      fields:\n      - {name: first, symbol: y_1, unit: '1', domain: null, description: First output.}\n      - {name: second, symbol: y_2, unit: '1', domain: null, description: Second output.}",
        );
        fs::write(
            root.join("specs/functions/non_pascal_case_record.yaml"),
            specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("non-PascalCase record name must fail")
            .to_string();
        assert!(error.contains("functions.0.outputs"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_a_record_definition_without_a_name() {
        let root = fixture_root("unnamed-record-definition");
        let specification = specification(
            "unnamed_record_definition",
            "    implementation:\n      variables: [{name: value, expr: x}]\n",
            "",
        )
        .replace(
            "functions:\n",
            "$defs:\n  reusable_result:\n    type: record\n    fields:\n    - {name: value, symbol: y, unit: '1', domain: null, description: Test output.}\nfunctions:\n",
        )
        .replace(
            "outputs: {type: scalar, name: value, symbol: y, unit: '1', domain: null, description: Test output.}",
            "outputs: {$ref: '#/$defs/reusable_result'}",
        );
        fs::write(
            root.join("specs/functions/unnamed_record_definition.yaml"),
            specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("unnamed record definition must fail")
            .to_string();
        assert!(error.contains("$defs.reusable_result"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn reports_schema_formula_and_output_contract_errors() {
        let root = fixture_root("errors");
        write(&root, "schema", "", "unknown: value\n");
        let error = load(&root).expect_err("schema must fail").to_string();
        assert!(error.contains("Additional properties are not allowed"));
        fs::remove_file(root.join("specs/functions/schema.yaml")).unwrap();

        write(
            &root,
            "formula",
            "    implementation:\n      variables: [{name: value, expr: '('}]\n",
            "",
        );
        let error = load(&root).expect_err("formula must fail").to_string();
        assert!(error.contains("implementation.variables[0].expr"));
        fs::remove_file(root.join("specs/functions/formula.yaml")).unwrap();

        write(
            &root,
            "output",
            "    implementation:\n      variables: [{name: other, expr: x}]\n",
            "",
        );
        let error = load(&root)
            .expect_err("output contract must fail")
            .to_string();
        assert!(error.contains("missing final output variables"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn parses_manual_public_python_policy() {
        let root = fixture_root("manual");
        write(
            &root,
            "manual",
            "    implementation:\n      variables: [{name: value, expr: x}]\n",
            "generation:\n  public_python: manual\n",
        );
        let entries = load(&root).unwrap();
        assert_eq!(
            entries[0].spec.generation.public_python,
            PythonGeneration::Manual
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_a_non_slug_specification_filename() {
        let root = fixture_root("invalid-slug");
        write(
            &root,
            "Bad-Slug",
            "    implementation:\n      variables: [{name: value, expr: x * 2}]\n",
            "",
        );

        let error = match load(&root) {
            Ok(_) => panic!("non-slug filename unexpectedly loaded"),
            Err(error) => error.to_string(),
        };

        assert!(error.contains("filename stem must be an APA-style slug"));
    }

    fn adapter_spec(derived: &str, expression: &str) -> String {
        specification("adapter", &format!("    implementation:\n      variables: [{{name: value, expr: {expression}}}]\n"), "")
            .replace("      - {name: x, symbol: x, unit: '1', domain: null, description: Test input.}", "      - {name: texture_class, type: usda_texture_class, symbol: null, unit: USDA texture class, domain: null, description: Test input.}")
            .replace("    outputs:", &format!("{derived}    outputs:"))
    }

    #[test]
    fn resolves_a_registered_categorical_input_and_derived_binding() {
        let root = fixture_root("typed-adapter");
        let derived = "    derived_inputs:\n      - adapter: usda_texture\n        input: texture_class\n        evidence: The source explicitly uses USDA particle-size definitions.\n        components: {sand: sand}\n";
        fs::write(
            root.join("specs/functions/adapter.yaml"),
            adapter_spec(derived, "sand"),
        )
        .unwrap();
        let entries = load(&root).unwrap();
        let ir = entries[0].implementations[0].as_ref().unwrap();
        assert_eq!(ir.inputs[0].input_type, "usda_texture_class");
        assert_eq!(ir.derived_inputs[0].component, "sand");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_invalid_typed_bindings_and_numeric_category_use() {
        for (label, derived, expression, expected) in [
            (
                "unknown-adapter",
                "    derived_inputs:\n      - {adapter: missing, input: texture_class, evidence: Source evidence., components: {sand: sand}}\n",
                "sand",
                "unknown adapter",
            ),
            (
                "missing-input",
                "    derived_inputs:\n      - {adapter: usda_texture, input: missing, evidence: Source evidence., components: {sand: sand}}\n",
                "sand",
                "unknown public input",
            ),
            (
                "unknown-component",
                "    derived_inputs:\n      - {adapter: usda_texture, input: texture_class, evidence: Source evidence., components: {gravel: sand}}\n",
                "sand",
                "unknown adapter component",
            ),
            (
                "empty-evidence",
                "    derived_inputs:\n      - {adapter: usda_texture, input: texture_class, evidence: ' ', components: {sand: sand}}\n",
                "sand",
                "source-backed evidence",
            ),
            (
                "category-as-number",
                "",
                "texture_class",
                "cannot be used as a numeric",
            ),
            ("unbound", "", "sand", "unknown identifier"),
        ] {
            let root = fixture_root(label);
            fs::write(
                root.join("specs/functions/adapter.yaml"),
                adapter_spec(derived, expression),
            )
            .unwrap();
            let error = load(&root).unwrap_err().to_string();
            assert!(error.contains(expected), "{label}: {error}");
            fs::remove_dir_all(root).unwrap();
        }
    }
}
