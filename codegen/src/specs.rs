use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::Arc,
};

use anyhow::{Context, Result, bail};
use jsonschema::Draft;
use serde_json::Value;

use crate::{
    formula,
    model::{
        Entry, EnumType, Implementation, ImplementationVariable, Input, Quantity, QuantityRegistry,
        RawDecisionTree, RawExpression, RawFunction, RawInput, RawInputType, RawLookup,
        RawVariable, RawVariableValue, Spec,
    },
    semantic,
};

pub(crate) fn load(root: &Path) -> Result<Vec<Entry>> {
    let quantities = load_quantities(root)?;
    let schema: Value =
        serde_json::from_slice(&fs::read(root.join("specs/schema/ptf-spec.schema.json"))?)?;
    let validator = jsonschema::options()
        .with_draft(Draft::Draft202012)
        .build(&schema)?;
    let definition_schema: Value = serde_json::from_slice(&fs::read(
        root.join("specs/schema/definitions.schema.json"),
    )?)?;
    let registry = jsonschema::Registry::new()
        .add(
            "https://ptfkit.invalid/ptf-spec.schema.json",
            schema.clone(),
        )?
        .prepare()?;
    let definition_validator = jsonschema::options()
        .with_base_uri("https://ptfkit.invalid/definitions.schema.json")
        .with_registry(&registry)
        .build(&definition_schema)?;
    let definitions = load_definitions(root, &definition_validator)?;
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
        let mut value = value;
        let shared = match resolve_external_references(&mut value, &path, &definitions) {
            Ok(shared) => shared,
            Err(error) => {
                errors.push(format!("{}:\n  $:\n    {error}", path.display()));
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
        let mut spec: Spec = match serde_json::from_value(value) {
            Ok(spec) => spec,
            Err(error) => {
                errors.push(format!(
                    "{}:\n  $:\n    metadata cannot be read: {error}",
                    path.display()
                ));
                continue;
            }
        };
        spec.set_definition_origins(&path, &shared);
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
        let expression_locations = match expression_locations(&text, &spec) {
            Ok(locations) => locations,
            Err(error) => {
                errors.push(format!("{}:\n  $:\n    {error}", path.display()));
                continue;
            }
        };
        let mut expression_locations = expression_locations.into_iter();
        let implementations = spec
            .functions
            .iter()
            .map(|function| match &function.implementation {
                Some(implementation) => {
                    compile(&path, function, implementation, &mut expression_locations).map(Some)
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
                quantities: Arc::clone(&quantities),
            }),
            Err(error) => errors.push(error),
        }
    }
    if !errors.is_empty() {
        bail!("validation failed:\n{}", errors.join("\n"))
    }
    Ok(entries)
}

fn load_definitions(
    root: &Path,
    validator: &jsonschema::Validator,
) -> Result<BTreeMap<PathBuf, Value>> {
    let directory = root.join("specs/definitions");
    let mut definitions = BTreeMap::new();
    if !directory.exists() {
        return Ok(definitions);
    }
    for entry in fs::read_dir(directory)? {
        let path = entry?.path();
        if path.extension().is_none_or(|extension| extension != "yaml") {
            continue;
        }
        source_slug(&path).map_err(anyhow::Error::msg)?;
        let text = fs::read_to_string(&path)?;
        let yaml: serde_yaml::Value = serde_yaml::from_str(&text)
            .with_context(|| format!("{}: malformed YAML", path.display()))?;
        let value = serde_json::to_value(yaml)?;
        let errors = validator
            .iter_errors(&value)
            .map(|error| {
                format!(
                    "{}: {}: {error}",
                    path.display(),
                    json_path(error.instance_path())
                )
            })
            .collect::<Vec<_>>();
        if !errors.is_empty() {
            bail!("invalid shared definitions:\n{}", errors.join("\n"));
        }
        definitions.insert(fs::canonicalize(path)?, value);
    }
    Ok(definitions)
}

fn resolve_external_references(
    value: &mut Value,
    document: &Path,
    documents: &BTreeMap<PathBuf, Value>,
) -> Result<BTreeMap<String, EnumType>, String> {
    let mut references = BTreeSet::new();
    collect_external_references(value, &mut references);
    let mut shared = BTreeMap::new();
    for reference in references {
        let (file, name) = reference
            .split_once("#/$defs/")
            .filter(|(file, name)| {
                !file.is_empty() && !name.is_empty() && !name.contains(['/', '#'])
            })
            .ok_or_else(|| {
                format!("unsupported reference `{reference}`: expected `file.yaml#/$defs/Name`")
            })?;
        if file.contains(':') || Path::new(file).is_absolute() {
            return Err(format!(
                "unsupported reference `{reference}`: only relative local files are supported"
            ));
        }
        let target = document
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join(file);
        let target = fs::canonicalize(&target).map_err(|error| {
            format!(
                "reference `{reference}`: cannot read {}: {error}",
                target.display()
            )
        })?;
        let parsed = documents.get(&target)
            .ok_or_else(|| format!("unsupported reference `{reference}`: expected a YAML file directly under specs/definitions"))?;
        let definition = parsed["$defs"].get(name).ok_or_else(|| {
            format!(
                "reference `{reference}`: definition `{name}` is missing in {}",
                target.display()
            )
        })?;
        let defs = value
            .as_object_mut()
            .ok_or_else(|| "specification root must be an object".to_owned())?
            .entry("$defs")
            .or_insert_with(|| Value::Object(serde_json::Map::new()))
            .as_object_mut()
            .ok_or_else(|| "specification `$defs` must be an object".to_owned())?;
        let mut index = defs.len();
        let alias = loop {
            let alias = format!("SharedDefinition{index}");
            if !defs.contains_key(&alias) {
                break alias;
            }
            index += 1;
        };
        defs.insert(alias.clone(), definition.clone());
        shared.insert(
            alias.clone(),
            EnumType {
                document: target.clone(),
                name: name.to_owned(),
                shared_module: Some(source_slug(&target)?),
            },
        );
        replace_reference(value, &reference, &format!("#/$defs/{alias}"));
    }
    Ok(shared)
}

fn collect_external_references(value: &Value, found: &mut BTreeSet<String>) {
    match value {
        Value::Object(object) => {
            if let Some(reference) = object.get("$ref").and_then(Value::as_str)
                && !reference.starts_with("#/$defs/")
            {
                found.insert(reference.to_owned());
            }
            for child in object.values() {
                collect_external_references(child, found);
            }
        }
        Value::Array(array) => array
            .iter()
            .for_each(|child| collect_external_references(child, found)),
        _ => {}
    }
}

fn replace_reference(value: &mut Value, old: &str, new: &str) {
    match value {
        Value::Object(object) => {
            if object.get("$ref").and_then(Value::as_str) == Some(old) {
                object.insert("$ref".to_owned(), Value::String(new.to_owned()));
            }
            for child in object.values_mut() {
                replace_reference(child, old, new);
            }
        }
        Value::Array(array) => array
            .iter_mut()
            .for_each(|child| replace_reference(child, old, new)),
        _ => {}
    }
}

fn load_quantities(root: &Path) -> Result<Arc<QuantityRegistry>> {
    let path = root.join("specs/quantities.yaml");
    let text = fs::read_to_string(&path)
        .with_context(|| format!("reading quantity registry {}", path.display()))?;
    // Parse through Value to reject duplicate keys at every map level.
    let value = serde_yaml::from_str::<serde_yaml::Value>(&text)
        .with_context(|| format!("reading quantity registry {}", path.display()))?;
    let quantities: std::collections::BTreeMap<String, Quantity> = serde_yaml::from_value(value)
        .with_context(|| format!("reading quantity registry {}", path.display()))?;
    let path = root.join("specs/units.yaml");
    let text = fs::read_to_string(&path)
        .with_context(|| format!("reading unit registry {}", path.display()))?;
    let value = serde_yaml::from_str::<serde_yaml::Value>(&text)
        .with_context(|| format!("reading unit registry {}", path.display()))?;
    let units = serde_yaml::from_value(value)
        .with_context(|| format!("reading unit registry {}", path.display()))?;
    Ok(Arc::new(QuantityRegistry { quantities, units }))
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
    expression_locations: &mut impl Iterator<Item = crate::model::SourceLocation>,
) -> Result<semantic::Function, String> {
    let raw = RawFunction {
        specification_path: path.to_owned(),
        name: function.name.clone(),
        inputs: function
            .inputs
            .iter()
            .map(|input| RawInput {
                name: input.name().to_owned(),
                value_type: match input {
                    Input::Parameter(_) => RawInputType::Number,
                    Input::Enum { definition, .. } => RawInputType::Enum(definition.clone()),
                },
            })
            .collect(),
        variables: implementation
            .variables
            .iter()
            .enumerate()
            .map(|(index, variable)| match variable {
                ImplementationVariable::Expression { name, expr } => {
                    let source_location = expression_locations.next().ok_or_else(|| {
                        format!(
                            "{} -> function {} -> implementation.variables[{index}].expr: source location is unavailable",
                            path.display(),
                            function.name
                        )
                    })?;
                    expression(
                        path,
                        &function.name,
                        format!("implementation.variables[{index}].expr"),
                        expr,
                        source_location,
                    )
                }
                .map(|expression| RawVariable {
                    name: name.clone(),
                    value: RawVariableValue::Expression(expression),
                }),
                ImplementationVariable::Lookup { name, lookup } => {
                    let definition = lookup
                        .definition
                        .clone()
                        .expect("lookup invocation is resolved");
                    Ok(RawVariable {
                        name: name.clone(),
                        value: RawVariableValue::Lookup(Box::new(RawLookup {
                            implementation_path: format!(
                                "implementation.variables[{index}].lookup"
                            ),
                            key: lookup.key.clone(),
                            definition,
                        })),
                    })
                }
                ImplementationVariable::DecisionTree {
                    name,
                    decision_tree,
                } => Ok(RawVariable {
                    name: name.clone(),
                    value: RawVariableValue::DecisionTree(Box::new(RawDecisionTree {
                        implementation_path: format!(
                            "implementation.variables[{index}].decision_tree"
                        ),
                        tree: decision_tree.as_ref().clone(),
                    })),
                }),
            })
            .collect::<Result<Vec<_>, _>>()?,
    };
    let mut compiled = semantic::compile(&raw).map_err(|error| error.to_string())?;
    compiled.result = validate_output(path, function, &compiled)?;
    Ok(compiled)
}

fn expression(
    path: &Path,
    function: &str,
    implementation_path: String,
    source: &str,
    source_location: crate::model::SourceLocation,
) -> Result<RawExpression, String> {
    let location = format!(
        "{} -> function {function} -> {implementation_path}",
        path.display()
    );
    formula::parse(location, source)
        .map(|expression| RawExpression {
            implementation_path,
            source_location,
            expression,
        })
        .map_err(|error| error.to_string())
}

fn expression_locations(
    text: &str,
    spec: &Spec,
) -> Result<Vec<crate::model::SourceLocation>, String> {
    let expressions =
        spec.functions
            .iter()
            .filter_map(|function| function.implementation.as_ref())
            .flat_map(|implementation| implementation.variables.iter())
            .filter_map(|variable| match variable {
                ImplementationVariable::Expression { expr, .. } => Some(expr.as_str()),
                ImplementationVariable::Lookup { .. }
                | ImplementationVariable::DecisionTree { .. } => None,
            });
    let mut cursor = 0;
    let mut locations = Vec::new();

    for expression in expressions {
        let Some((offset, next_cursor)) = find_expression(text, cursor, expression) else {
            return Err(format!(
                "could not locate formula expression `{expression}` in YAML source"
            ));
        };
        locations.push(location(text, offset));
        cursor = next_cursor;
    }
    Ok(locations)
}

fn find_expression(text: &str, mut cursor: usize, expression: &str) -> Option<(usize, usize)> {
    while let Some(relative) = text[cursor..].find("expr:") {
        let field = cursor + relative;
        let value_start = field + "expr:".len();
        let value_end = text[value_start..]
            .find("expr:")
            .map_or(text.len(), |next| value_start + next);
        if let Some(relative) = text[value_start..value_end].find(expression) {
            let value = value_start + relative;
            return Some((value, value + expression.len()));
        }
        cursor = field + "expr:".len();
    }
    None
}

fn location(text: &str, offset: usize) -> crate::model::SourceLocation {
    let prefix = &text[..offset];
    crate::model::SourceLocation {
        line: prefix.bytes().filter(|byte| *byte == b'\n').count() + 1,
        column: prefix
            .rsplit_once('\n')
            .map_or(prefix, |(_, line)| line)
            .chars()
            .count()
            + 1,
    }
}

fn validate_output(
    path: &Path,
    function: &crate::model::Function,
    compiled: &semantic::Function,
) -> Result<semantic::ResultBinding, String> {
    if let crate::model::Outputs::Record { name, fields } = &function.outputs {
        let expected = semantic::RecordType {
            name: name.clone(),
            fields: fields.iter().map(|field| field.name.clone()).collect(),
        };
        if let Some((
            index,
            semantic::Variable {
                value: semantic::VariableValue::RecordLookup(lookup),
                ..
            },
        )) = compiled.variables.iter().enumerate().next_back()
        {
            if lookup.output == expected {
                return Ok(semantic::ResultBinding::RecordVariable(index));
            }
            if lookup.output.name == expected.name {
                return Err(format!(
                    "{} -> function {} -> implementation.variables[{index}]: record lookup type `{}` does not exactly match the function output record",
                    path.display(),
                    function.name,
                    lookup.output.name
                ));
            }
        }
    }
    let output_names = function
        .outputs
        .fields()
        .iter()
        .map(|output| &output.name)
        .collect::<Vec<_>>();
    let output_sources = compiled
        .inputs
        .iter()
        .map(|input| input.name.as_str())
        .chain(
            compiled
                .variables
                .iter()
                .filter_map(|variable| match variable.value {
                    semantic::VariableValue::Number(_) => Some(variable.name.as_str()),
                    semantic::VariableValue::DecisionTree(_) => Some(variable.name.as_str()),
                    semantic::VariableValue::RecordLookup(_) => None,
                }),
        )
        .collect::<std::collections::BTreeSet<_>>();
    let missing = output_names
        .iter()
        .filter(|name| !output_sources.contains(name.as_str()))
        .collect::<Vec<_>>();
    if missing.is_empty() {
        Ok(semantic::ResultBinding::Fields)
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
    use std::{fs, path::Path};

    use super::load;
    use crate::model::PythonGeneration;

    use crate::test_support::fixture_root;

    fn specification(slug: &str, implementation: &str, generation: &str) -> String {
        let verification = if implementation.is_empty()
            || implementation.contains("verification_cases:")
        {
            ""
        } else {
            "    verification_cases:\n      - {id: reference, kind: calculated, inputs: {x: 1.0}, expected: {value: 1.0}, rationale: Test fixture.}\n"
        };
        format!(
            "source:\n  summary: Test source.\n  citation_apa: Test (2026).\n  doi: null\n{generation}functions:\n  - name: calc_ptf_{slug}\n    status: ready-for-implementation\n    public_api: {{name: calc_ptf_{slug}, result_class: null, summary: Test value.}}\n    scope:\n      prediction_target: Test value.\n      models: {{h_theta: null, k_h: null}}\n    inputs:\n      - {{name: x, symbol: x, unit: '1', domain: null, description: Test input.}}\n    outputs: {{type: scalar, name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}}\n{implementation}{verification}"
        )
    }

    fn write(root: &Path, key: &str, implementation: &str, generation: &str) {
        fs::write(
            root.join(format!("specs/functions/{key}.yaml")),
            specification(key, implementation, generation),
        )
        .unwrap();
    }

    fn decision_tree_specification() -> &'static str {
        r#"source:
  summary: Test source.
  citation_apa: Test (2026).
  doi: null
$defs:
  Category:
    type: enum
    description: Test category.
    values:
      - {name: coarse, value: Coarse}
      - {name: fine, value: Fine}
functions:
  - name: calc_ptf_decision_tree
    status: ready-for-implementation
    public_api: {name: calc_ptf_decision_tree, result_class: null, summary: Test decision tree.}
    scope:
      prediction_target: Test value.
      models: {h_theta: null, k_h: null}
    inputs:
      - {$ref: '#/$defs/Category', name: category}
      - {name: x, symbol: x, unit: '1', domain: null, description: Test input.}
    outputs: {type: scalar, name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}
    implementation:
      variables:
        - name: value
          decision_tree:
            split: {input: category, operator: in, values: [coarse]}
            yes:
              split: {input: x, operator: lt, value: 2.0}
              yes: {leaf: 1.0}
              no: {leaf: 2.0}
            no: {leaf: 3.0}
    verification_cases:
      - {id: below_boundary, kind: calculated, inputs: {category: coarse, x: 1.0}, expected: {value: 1.0}, rationale: Explicit fixture branch.}
      - {id: at_boundary, kind: calculated, inputs: {category: coarse, x: 2.0}, expected: {value: 2.0}, rationale: Equality takes the No branch.}
      - {id: other_category, kind: calculated, inputs: {category: fine, x: 1.0}, expected: {value: 3.0}, rationale: Explicit fixture branch.}
"#
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
    fn compiles_a_record_lookup_with_additional_inputs_and_later_field_expressions() {
        let root = fixture_root("record-lookup-expression");
        let specification = r#"source:
  summary: Test source.
  citation_apa: Test (2026).
  doi: null
$defs:
  Texture:
    type: enum
    description: Texture class.
    values:
      - {name: sand, value: sand}
      - {name: clay, value: clay}
  Parameters:
    type: record
    name: Parameters
    fields:
      - {name: factor, quantity: volumetric_water_content, symbol: f, unit: volume_fraction, reported_unit: '1', domain: null, description: Test factor.}
  ParametersByTexture:
    type: lookup
    input: {$ref: '#/$defs/Texture'}
    output: {$ref: '#/$defs/Parameters'}
    values:
      - {key: sand, value: {factor: 2.0}}
      - {key: clay, value: {factor: 3.0}}
functions:
  - name: calc_ptf_record_lookup_expression
    status: ready-for-implementation
    public_api: {name: calc_ptf_record_lookup_expression, result_class: null, summary: Test value.}
    scope:
      prediction_target: Test value.
      models: {h_theta: null, k_h: null}
    inputs:
      - {$ref: '#/$defs/Texture', name: texture}
      - {name: x, symbol: x, unit: '1', domain: null, description: Test input.}
    outputs: {type: scalar, name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}
    implementation:
      variables:
        - name: parameters
          lookup:
            table: {$ref: '#/$defs/ParametersByTexture'}
            key: texture
        - {name: value, expr: parameters.factor * x}
    verification_cases:
      - {id: sand, kind: calculated, inputs: {texture: sand, x: 1.0}, expected: {value: 2.0}, rationale: Test fixture.}
"#;
        fs::write(
            root.join("specs/functions/record_lookup_expression.yaml"),
            specification,
        )
        .unwrap();

        let entries = load(&root).unwrap();
        let implementation = entries[0].implementations[0].as_ref().unwrap();
        assert!(matches!(
            implementation.variables[0].value,
            crate::semantic::VariableValue::RecordLookup(_)
        ));
        assert!(matches!(
            implementation.variables[1].value,
            crate::semantic::VariableValue::Number(_)
        ));
        let compiled = crate::compile::functions(entries).unwrap();
        let rust = crate::targets::render_rust_for_test(&compiled).unwrap();
        let rust = &rust
            .iter()
            .find(|file| file.path.ends_with("record_lookup_expression.rs"))
            .unwrap()
            .contents;
        assert!(rust.contains("struct Parameters"), "{rust}");
        assert!(rust.contains("parameters . factor"), "{rust}");
        let (c_headers, cpp_modules) = crate::targets::render_native_for_test(&compiled).unwrap();
        let c = &c_headers
            .iter()
            .find(|file| file.path.ends_with("record_lookup_expression.h"))
            .unwrap()
            .contents;
        assert!(c.contains("} parameters;"), "{c}");
        assert!(c.contains("parameters.factor"), "{c}");
        let cpp = &cpp_modules
            .iter()
            .find(|file| file.path.ends_with("record_lookup_expression.cppm"))
            .unwrap()
            .contents;
        assert!(cpp.contains("struct Parameters"), "{cpp}");
        assert!(cpp.contains("parameters.factor"), "{cpp}");
        let extension = crate::targets::render_python_extension_for_test(&compiled).unwrap();
        let extension = &extension
            .iter()
            .find(|file| file.path.ends_with("record_lookup_expression.c"))
            .unwrap()
            .contents;
        assert!(
            extension.contains("const npy_uint32 texture = in_texture[index];"),
            "{extension}"
        );
        assert!(
            extension.contains("calc_ptf_record_lookup_expression(texture, x)"),
            "{extension}"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn compiles_and_renders_strict_decision_tree_branches() {
        let root = fixture_root("decision-tree");
        fs::write(
            root.join("specs/functions/decision_tree.yaml"),
            decision_tree_specification(),
        )
        .unwrap();

        let entries = load(&root).unwrap();
        assert!(matches!(
            entries[0].implementations[0].as_ref().unwrap().variables[0].value,
            crate::semantic::VariableValue::DecisionTree(_)
        ));
        let compiled = crate::compile::functions(entries).unwrap();
        let rust = crate::targets::render_rust_for_test(&compiled).unwrap();
        let rust = &rust
            .iter()
            .find(|file| file.path.ends_with("decision_tree.rs"))
            .unwrap()
            .contents;
        assert!(
            rust.contains("matches ! (category , Category :: Coarse)"),
            "{rust}"
        );
        assert!(rust.contains("x < 2.0f64"), "{rust}");
        assert!(rust.contains("fn at_boundary"), "{rust}");
        assert!(
            rust.contains("calc_ptf_decision_tree (Category :: Coarse , 2f64)"),
            "{rust}"
        );

        let (c_headers, cpp_modules) = crate::targets::render_native_for_test(&compiled).unwrap();
        let c = &c_headers
            .iter()
            .find(|file| file.path.ends_with("decision_tree.h"))
            .unwrap()
            .contents;
        assert!(
            c.contains("if (category == decision_tree_category_coarse)"),
            "{c}"
        );
        assert!(c.contains("if (x < 2.0)"), "{c}");
        assert!(c.contains("return 1.0;"), "{c}");
        assert!(c.contains("return 2.0;"), "{c}");
        assert!(c.contains("return 3.0;"), "{c}");

        let cpp = &cpp_modules
            .iter()
            .find(|file| file.path.ends_with("decision_tree.cppm"))
            .unwrap()
            .contents;
        assert!(cpp.contains("if (category == Category::Coarse)"), "{cpp}");
        assert!(cpp.contains("if (x < 2.0)"), "{cpp}");

        let extension = crate::targets::render_python_extension_for_test(&compiled).unwrap();
        let extension = &extension
            .iter()
            .find(|file| file.path.ends_with("decision_tree.c"))
            .unwrap()
            .contents;
        assert!(
            extension.contains("calc_ptf_decision_tree(category, x)"),
            "{extension}"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn renders_a_decision_tree_as_an_intermediate_numeric_variable() {
        let root = fixture_root("decision-tree-variable");
        let specification = decision_tree_specification()
            .replace(
                "        - name: value\n          decision_tree:",
                "        - name: branch_value\n          decision_tree:",
            )
            .replace(
                "            no: {leaf: 3.0}\n    verification_cases:",
                "            no: {leaf: 3.0}\n        - {name: value, expr: branch_value * 10}\n    verification_cases:",
            )
            .replace("expected: {value: 1.0}", "expected: {value: 10.0}")
            .replace("expected: {value: 2.0}", "expected: {value: 20.0}")
            .replace("expected: {value: 3.0}", "expected: {value: 30.0}");
        fs::write(
            root.join("specs/functions/decision_tree_variable.yaml"),
            specification,
        )
        .unwrap();

        let compiled = crate::compile::functions(load(&root).unwrap()).unwrap();
        let rust = crate::targets::render_rust_for_test(&compiled).unwrap();
        let rust = &rust
            .iter()
            .find(|file| file.path.ends_with("decision_tree_variable.rs"))
            .unwrap()
            .contents;
        assert!(rust.contains("let branch_value = if"), "{rust}");
        assert!(rust.contains("branch_value * 10.0f64"), "{rust}");

        let (c_headers, cpp_modules) = crate::targets::render_native_for_test(&compiled).unwrap();
        let c = &c_headers
            .iter()
            .find(|file| file.path.ends_with("decision_tree_variable.h"))
            .unwrap()
            .contents;
        assert!(c.contains("const double branch_value ="), "{c}");
        assert!(c.contains("? 1.0 : 2.0"), "{c}");
        assert!(c.contains("branch_value * 10.0"), "{c}");
        let cpp = &cpp_modules
            .iter()
            .find(|file| file.path.ends_with("decision_tree_variable.cppm"))
            .unwrap()
            .contents;
        assert!(cpp.contains("const double branch_value ="), "{cpp}");
        assert!(cpp.contains("branch_value * 10.0"), "{cpp}");

        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_decision_tree_predicates_with_wrong_input_types_or_members() {
        for (label, edit, expected) in [
            (
                "numeric-enum",
                (
                    "split: {input: category, operator: in, values: [coarse]}",
                    "split: {input: category, operator: lt, value: 2.0}",
                ),
                "must be numeric for operator `lt`",
            ),
            (
                "enum-numeric",
                (
                    "split: {input: category, operator: in, values: [coarse]}",
                    "split: {input: x, operator: in, values: [coarse]}",
                ),
                "must be an enum for operator `in`",
            ),
            (
                "unknown-member",
                ("values: [coarse]", "values: [missing]"),
                "unknown member `missing` of enum `Category`",
            ),
            (
                "unknown-input",
                ("input: category", "input: missing"),
                "unknown decision-tree input `missing`",
            ),
        ] {
            let root = fixture_root(label);
            let text = decision_tree_specification().replacen(edit.0, edit.1, 1);
            fs::write(root.join("specs/functions/decision_tree.yaml"), text).unwrap();
            let error = load(&root)
                .expect_err("invalid decision tree must fail")
                .to_string();
            assert!(error.contains(expected), "{error}");
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn validates_unused_lookup_definitions() {
        let root = fixture_root("unused-invalid-lookup");
        let specification = specification(
            "unused_invalid_lookup",
            "    implementation:\n      variables: [{name: value, expr: x}]\n",
            "",
        )
        .replace(
            "functions:\n",
            "$defs:\n  Texture:\n    type: enum\n    description: Texture class.\n    values:\n      - {name: sand, value: sand}\n      - {name: clay, value: clay}\n  Parameters:\n    type: record\n    name: Parameters\n    fields:\n      - {name: factor, quantity: volumetric_water_content, symbol: f, unit: volume_fraction, reported_unit: '1', domain: null, description: Test factor.}\n  InvalidLookup:\n    type: lookup\n    input: {$ref: '#/$defs/Texture'}\n    output: {$ref: '#/$defs/Parameters'}\n    values:\n      - {key: sand, value: {factor: 2.0}}\nfunctions:\n",
        );
        fs::write(
            root.join("specs/functions/unused_invalid_lookup.yaml"),
            specification,
        )
        .unwrap();

        let error = load(&root).unwrap_err().to_string();
        assert!(error.contains("lookup `InvalidLookup` values must cover every member"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn resolves_one_shared_enum_for_independent_sources() {
        let root = fixture_root("shared-definitions");
        crate::test_support::copy_shared_definition_fixture(&root);
        let entries = crate::load_validated_specifications(&root)
            .expect("shared definitions should validate and compile");
        let first = entries[0].spec.functions[0].inputs[0].enum_type().unwrap();
        let second = entries[1].spec.functions[0].inputs[0].enum_type().unwrap();
        assert_eq!(first.identity(), second.identity());
        assert_eq!(first.enum_type.name, "SharedCategory");
        assert_eq!(
            entries[0].spec.functions[0].inputs[0].description(),
            "Usage-specific input."
        );
        let local = entries[0].spec.functions[1].inputs[0].enum_type().unwrap();
        assert_ne!(first.identity(), local.identity());
        assert_eq!(first.enum_type.name, local.enum_type.name);
        assert_eq!(first.description, "Shared category.");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn reports_unsupported_and_missing_external_references() {
        for (label, reference, expected) in [
            (
                "missing-shared-definition",
                "../definitions/missing.yaml#/$defs/Category",
                "cannot read",
            ),
            (
                "missing-shared-member",
                "../definitions/soil.yaml#/$defs/MissingCategory",
                "definition `MissingCategory` is missing",
            ),
            (
                "unsupported-shared-fragment",
                "../definitions/soil.yaml#/$defs/SharedCategory/values",
                "expected `file.yaml#/$defs/Name`",
            ),
            (
                "remote-shared-definition",
                "https://example.test/soil.yaml#/$defs/Category",
                "only relative local files are supported",
            ),
        ] {
            let root = fixture_root(label);
            crate::test_support::copy_shared_definition_fixture(&root);
            fs::write(
                root.join("specs/functions/example.yaml"),
                format!(
                    r#"source: {{summary: Example., citation_apa: Test (2026)., doi: null}}
functions:
  - name: calc_ptf_example
    status: blocked
    public_api: {{name: calc_ptf_example, summary: Result.}}
    scope: {{prediction_target: Result., models: {{h_theta: null, k_h: null}}}}
    inputs: [{{name: category, description: Input., $ref: {reference}}}]
    outputs: {{type: scalar, name: value, quantity: volumetric_water_content, unit: volume_fraction, reported_unit: '1', symbol: null, domain: null, description: Result.}}
"#
                ),
            )
            .unwrap();
            let error = load(&root).expect_err("invalid external reference must fail");
            let diagnostic = error.to_string();
            assert!(diagnostic.contains(expected), "{diagnostic}");
            assert!(diagnostic.contains(reference), "{diagnostic}");
            assert!(diagnostic.contains("example.yaml"), "{diagnostic}");
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn lookup_requires_definition_identity_not_just_its_name() {
        let root = fixture_root("shared-lookup-identity");
        crate::test_support::copy_shared_definition_fixture(&root);
        let path = root.join("specs/functions/first_source.yaml");
        let text = fs::read_to_string(&path).unwrap().replace(
            "input: {$ref: '#/$defs/SharedCategory'}",
            "input: {$ref: '../definitions/soil.yaml#/$defs/SharedCategory'}",
        );
        fs::write(path, text).unwrap();
        let error = load(&root).expect_err("local input cannot key a shared enum lookup");
        let diagnostic = error.to_string();
        assert!(diagnostic.contains("calc_ptf_local"), "{diagnostic}");
        assert!(diagnostic.contains("must have enum type"), "{diagnostic}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn validates_unreferenced_shared_definitions() {
        let root = fixture_root("unused-shared-schema");
        fs::create_dir_all(root.join("specs/definitions")).unwrap();
        let path = root.join("specs/definitions/soil.yaml");
        fs::write(
            &path,
            include_str!("fixtures/shared-definitions/definitions/soil.yaml"),
        )
        .unwrap();
        assert!(load(&root).unwrap().is_empty());
        fs::write(
            &path,
            "$defs: {Broken: {type: enum, description: Broken., values: []}}",
        )
        .unwrap();
        let error = load(&root).expect_err("unused definitions must satisfy the schema");
        let diagnostic = error.to_string();
        assert!(diagnostic.contains("soil.yaml"), "{diagnostic}");
        assert!(diagnostic.contains("values"), "{diagnostic}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_a_record_lookup_that_only_matches_the_output_name() {
        let root = fixture_root("mismatched-record-lookup");
        let specification = r#"source:
  summary: Test source.
  citation_apa: Test (2026).
  doi: null
$defs:
  Texture:
    type: enum
    description: Texture class.
    values:
      - {name: sand, value: sand}
  LookupParameters:
    type: record
    name: Parameters
    fields:
      - {name: factor, quantity: volumetric_water_content, symbol: f, unit: volume_fraction, reported_unit: '1', domain: null, description: Test factor.}
  ParametersByTexture:
    type: lookup
    input: {$ref: '#/$defs/Texture'}
    output: {$ref: '#/$defs/LookupParameters'}
    values:
      - {key: sand, value: {factor: 2.0}}
functions:
  - name: calc_ptf_mismatched_record_lookup
    status: ready-for-implementation
    public_api: {name: calc_ptf_mismatched_record_lookup, result_class: Parameters, summary: Test value.}
    scope:
      prediction_target: Test value.
      models: {h_theta: null, k_h: null}
    inputs:
      - {$ref: '#/$defs/Texture', name: texture}
    outputs:
      type: record
      name: Parameters
      fields:
        - {name: other, quantity: volumetric_water_content, symbol: o, unit: volume_fraction, reported_unit: '1', domain: null, description: Other value.}
    implementation:
      variables:
        - name: parameters
          lookup:
            table: {$ref: '#/$defs/ParametersByTexture'}
            key: texture
"#;
        fs::write(
            root.join("specs/functions/mismatched_record_lookup.yaml"),
            specification,
        )
        .unwrap();

        let error = load(&root).unwrap_err().to_string();
        assert!(
            error.contains("record lookup type `Parameters` does not exactly match"),
            "{error}"
        );
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
        )
        .replace("inputs: {x: 1.0}", "inputs: {value: 1.0}");
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
            "outputs: {type: scalar, name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}",
            "outputs:\n      type: record\n      fields:\n      - {name: first, quantity: volumetric_water_content, symbol: y_1, unit: volume_fraction, reported_unit: '1', domain: null, description: First output.}\n      - {name: second, quantity: volumetric_water_content, symbol: y_2, unit: volume_fraction, reported_unit: '1', domain: null, description: Second output.}",
        );
        fs::write(
            root.join("specs/functions/unnamed_record.yaml"),
            &specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("unnamed inline record must fail")
            .to_string();
        assert!(error.contains("functions.0.outputs"), "{error}");
        fs::write(
            root.join("specs/functions/unnamed_record.yaml"),
            specification.replace(
                "      type: record\n",
                "      type: record\n      name: TestResult\n",
            ),
        )
        .unwrap();
        load(&root).expect("correcting only the record name must make the fixture valid");
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
            "outputs: {type: scalar, name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}",
            "outputs:\n      type: record\n      name: result_record\n      fields:\n      - {name: first, quantity: volumetric_water_content, symbol: y_1, unit: volume_fraction, reported_unit: '1', domain: null, description: First output.}\n      - {name: second, quantity: volumetric_water_content, symbol: y_2, unit: volume_fraction, reported_unit: '1', domain: null, description: Second output.}",
        );
        fs::write(
            root.join("specs/functions/non_pascal_case_record.yaml"),
            &specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("non-PascalCase record name must fail")
            .to_string();
        assert!(error.contains("functions.0.outputs"), "{error}");
        fs::write(
            root.join("specs/functions/non_pascal_case_record.yaml"),
            specification.replace("name: result_record", "name: TestResult"),
        )
        .unwrap();
        load(&root).expect("correcting only the record name must make the fixture valid");
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
            "$defs:\n  reusable_result:\n    type: record\n    fields:\n    - {name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}\nfunctions:\n",
        )
        .replace(
            "outputs: {type: scalar, name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}",
            "outputs: {$ref: '#/$defs/reusable_result'}",
        );
        fs::write(
            root.join("specs/functions/unnamed_record_definition.yaml"),
            &specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("unnamed record definition must fail")
            .to_string();
        assert!(error.contains("$defs.reusable_result"), "{error}");
        fs::write(
            root.join("specs/functions/unnamed_record_definition.yaml"),
            specification.replace(
                "    type: record\n",
                "    type: record\n    name: TestResult\n",
            ),
        )
        .unwrap();
        load(&root).expect("correcting only the record name must make the fixture valid");
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

    fn verification_specification(slug: &str, case: &str) -> String {
        specification(
            slug,
            &format!(
                "    implementation:\n      variables: [{{name: value, expr: x}}]\n    verification_cases:\n      - id: reference\n        inputs: {{x: 1.0}}\n{case}"
            ),
            "",
        )
    }

    #[test]
    fn accepts_both_verification_case_kinds() {
        let cases = [
            (
                "published",
                "        expected: {value: 1.0}\n        kind: published\n        source_location: Table 1, row 1\n        notes: Source lookup.\n",
            ),
            (
                "calculated",
                "        expected: {value: 1.0}\n        kind: calculated\n        source_location: Table 1, input row\n        rationale: Interior representative input.\n",
            ),
        ];
        for (slug, case) in cases {
            let root = fixture_root(slug);
            fs::write(
                root.join(format!("specs/functions/{slug}.yaml")),
                verification_specification(slug, case),
            )
            .unwrap();
            load(&root).unwrap_or_else(|error| panic!("{slug} case failed: {error}"));
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn requires_verification_cases_for_code_generating_statuses() {
        for status in ["ready-for-implementation", "implemented"] {
            let slug = status.replace('-', "_");
            let root = fixture_root(&slug);
            let text = specification(
                &slug,
                "    implementation:\n      variables: [{name: value, expr: x}]\n",
                "",
            )
            .replace(
                "    verification_cases:\n      - {id: reference, kind: calculated, inputs: {x: 1.0}, expected: {value: 1.0}, rationale: Test fixture.}\n",
                "",
            )
            .replace("status: ready-for-implementation", &format!("status: {status}"));
            fs::write(root.join(format!("specs/functions/{slug}.yaml")), text).unwrap();

            let error = load(&root)
                .expect_err("code-generating status without cases must fail")
                .to_string();
            assert!(error.contains("verification_cases"), "{error}");
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn permits_blocked_functions_without_verification_cases() {
        let root = fixture_root("blocked_without_cases");
        let text = specification("blocked_without_cases", "", "")
            .replace("status: ready-for-implementation", "status: blocked");
        fs::write(
            root.join("specs/functions/blocked_without_cases.yaml"),
            text,
        )
        .unwrap();

        load(&root).expect("blocked function may omit cases");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_duplicate_verification_case_ids_within_a_function() {
        let root = fixture_root("duplicate_case_id");
        let text = verification_specification(
            "duplicate_case_id",
            "        expected: {value: 1.0}\n        kind: calculated\n        rationale: First fixture.\n      - {id: reference, kind: calculated, inputs: {x: 2.0}, expected: {value: 2.0}, rationale: Second fixture.}\n",
        );
        fs::write(root.join("specs/functions/duplicate_case_id.yaml"), text).unwrap();

        let error = crate::load_validated_specifications(&root)
            .expect_err("duplicate case IDs must fail")
            .to_string();
        assert!(error.contains("duplicate id `reference`"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_absolute_tolerance_that_masks_a_nonzero_expected_value() {
        let root = fixture_root("nondiscriminating_tolerance");
        let text = specification(
            "nondiscriminating_tolerance",
            "    verification_tolerances:\n      value: {absolute: 1.0, source_location: Test policy}\n    implementation:\n      variables: [{name: value, expr: x}]\n",
            "",
        );
        fs::write(
            root.join("specs/functions/nondiscriminating_tolerance.yaml"),
            text,
        )
        .unwrap();

        let error = crate::load_validated_specifications(&root)
            .and_then(crate::compile::functions)
            .expect_err("non-discriminating tolerance must fail")
            .to_string();
        assert!(
            error.contains("greater than or equal to the magnitude"),
            "{error}"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_relative_tolerance_that_masks_a_nonzero_expected_value() {
        let root = fixture_root("nondiscriminating_relative_tolerance");
        let text = specification(
            "nondiscriminating_relative_tolerance",
            "    verification_tolerances:\n      value: {absolute: 0.001, relative: 1.0, source_location: Test policy}\n    implementation:\n      variables: [{name: value, expr: x}]\n",
            "",
        );
        fs::write(
            root.join("specs/functions/nondiscriminating_relative_tolerance.yaml"),
            text,
        )
        .unwrap();

        let error = crate::load_validated_specifications(&root)
            .and_then(crate::compile::functions)
            .expect_err("non-discriminating relative tolerance must fail")
            .to_string();
        assert!(
            error.contains("greater than or equal to the magnitude"),
            "{error}"
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_invalid_verification_case_provenance() {
        for (slug, valid, invalid) in [
            (
                "unknown_kind",
                "kind: calculated\n        rationale: Test input.",
                "kind: external\n        rationale: Test input.",
            ),
            (
                "published_without_location",
                "kind: published\n        source_location: Table 1",
                "kind: published",
            ),
            (
                "calculated_without_rationale",
                "kind: calculated\n        rationale: Test input.",
                "kind: calculated",
            ),
        ] {
            let root = fixture_root(slug);
            let path = root.join(format!("specs/functions/{slug}.yaml"));
            let text = verification_specification(
                slug,
                &format!("        expected: {{value: 1.0}}\n        {valid}\n"),
            );
            fs::write(&path, &text).unwrap();
            load(&root)
                .expect("provenance control must be valid before removing its required metadata");
            fs::write(&path, text.replace(valid, invalid)).unwrap();
            let error = load(&root)
                .expect_err("invalid provenance must fail")
                .to_string();
            assert!(
                error.contains("functions.0.verification_cases.0"),
                "{error}"
            );
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn rejects_missing_and_unknown_expected_outputs() {
        for (missing, diagnostic) in [
            (true, "missing expected output `first`"),
            (false, "references unknown output `other`"),
        ] {
            let mut entries = crate::test_support::entries();
            let expected = &mut entries[0].spec.functions[1].verification_cases[0].expected;
            if missing {
                expected.remove("first");
            } else {
                expected.insert("other".into(), 3.0);
            }
            let error = crate::compile::functions(entries)
                .expect_err("invalid expected outputs must fail")
                .to_string();
            assert!(error.contains(diagnostic), "{error}");
        }
    }

    #[test]
    fn resolves_registry_defaults_and_replacing_source_overrides() {
        let root = fixture_root("tolerance-resolution");
        let default_spec = specification(
            "default_tolerance",
            "    implementation:\n      variables: [{name: value, expr: x}]\n",
            "",
        );
        fs::write(
            root.join("specs/functions/default_tolerance.yaml"),
            default_spec,
        )
        .unwrap();
        let override_spec = specification(
            "override_tolerance",
            "    verification_tolerances:\n      value:\n        absolute: 0.005\n        relative: 0.01\n        source_location: Table 5\n    implementation:\n      variables: [{name: value, expr: x}]\n",
            "",
        );
        fs::write(
            root.join("specs/functions/override_tolerance.yaml"),
            override_spec,
        )
        .unwrap();

        let compiled = crate::compile::functions(
            crate::load_validated_specifications(&root).expect("fixtures validate"),
        )
        .unwrap();
        let default = &compiled[0].output_tolerances[0];
        assert_eq!(default.absolute, 0.001);
        assert_eq!(default.relative, 0.0);
        assert!(matches!(
            default.source,
            crate::model::ToleranceSource::Registry
        ));
        let override_ = &compiled[1].output_tolerances[0];
        assert_eq!(override_.absolute, 0.005);
        assert_eq!(override_.relative, 0.01);
        assert!(matches!(
            &override_.source,
            crate::model::ToleranceSource::SourceOverride(location) if location == "Table 5"
        ));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_unknown_verification_inputs() {
        let root = fixture_root("unknown-verification-input");
        let text = verification_specification(
            "unknown_verification_input",
            "        expected: {value: 1.0}\n        kind: calculated\n        rationale: Interior input.\n",
        )
        .replace("inputs: {x: 1.0}", "inputs: {x: 1.0, stale: 2.0}");
        fs::write(
            root.join("specs/functions/unknown_verification_input.yaml"),
            text,
        )
        .unwrap();
        let error = crate::load_validated_specifications(&root)
            .and_then(crate::compile::functions)
            .expect_err("unknown input must fail")
            .to_string();
        assert!(error.contains("unknown input `stale`"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_missing_verification_inputs() {
        let root = fixture_root("missing-verification-input");
        let text = verification_specification(
            "missing_verification_input",
            "        expected: {value: 1.0}\n        kind: calculated\n        rationale: Interior input.\n",
        )
        .replace(
            "      - {name: x, symbol: x, unit: '1', domain: null, description: Test input.}",
            "      - {name: x, symbol: x, unit: '1', domain: null, description: Test input.}\n      - {name: y, symbol: y, unit: '1', domain: null, description: Missing test input.}",
        );
        fs::write(
            root.join("specs/functions/missing_verification_input.yaml"),
            text,
        )
        .unwrap();
        let error = crate::load_validated_specifications(&root)
            .and_then(crate::compile::functions)
            .expect_err("missing input must fail")
            .to_string();
        assert!(error.contains("missing input `y`"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn keeps_overrides_function_and_field_local_for_shared_outputs() {
        let root = fixture_root("shared-output-overrides");
        let text = r#"source:
  summary: Test source.
  citation_apa: Test (2026).
  doi: null
$defs:
  SharedResult:
    type: record
    name: SharedResult
    fields:
      - {name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}
      - {name: second, quantity: volumetric_water_content, symbol: z, unit: volume_fraction, reported_unit: '1', domain: null, description: Second test output.}
functions:
  - name: calc_ptf_shared_default
    status: ready-for-implementation
    public_api: {name: calc_ptf_shared_default, result_class: SharedResult, summary: Test value.}
    scope:
      prediction_target: Test value.
      models: {h_theta: null, k_h: null}
    inputs:
      - {name: x, symbol: x, unit: '1', domain: null, description: Test input.}
    outputs: {$ref: '#/$defs/SharedResult'}
    implementation:
      variables: [{name: value, expr: x}, {name: second, expr: x}]
    verification_cases:
      - {id: default, kind: calculated, inputs: {x: 1.0}, expected: {value: 1.0, second: 1.0}, rationale: Test fixture.}
  - name: calc_ptf_shared_override
    status: ready-for-implementation
    public_api: {name: calc_ptf_shared_override, result_class: SharedResult, summary: Test value.}
    scope:
      prediction_target: Test value.
      models: {h_theta: null, k_h: null}
    inputs:
      - {name: x, symbol: x, unit: '1', domain: null, description: Test input.}
    outputs: {$ref: '#/$defs/SharedResult'}
    verification_tolerances:
      value: {absolute: 0.005, source_location: Table 5}
    implementation:
      variables: [{name: value, expr: x}, {name: second, expr: x}]
    verification_cases:
      - {id: override, kind: calculated, inputs: {x: 1.0}, expected: {value: 1.0, second: 1.0}, rationale: Test fixture.}
"#;
        fs::write(
            root.join("specs/functions/shared_output_overrides.yaml"),
            text,
        )
        .unwrap();

        let compiled = crate::load_validated_specifications(&root)
            .and_then(crate::compile::functions)
            .expect("shared output definitions must compile");
        assert_eq!(compiled[0].output_tolerances[0].absolute, 0.001);
        assert_eq!(compiled[1].output_tolerances[0].absolute, 0.005);
        for function in &compiled {
            let second = &function.output_tolerances[1];
            assert_eq!(second.absolute, 0.001);
            assert_eq!(second.relative, 0.0);
            assert!(matches!(
                second.source,
                crate::model::ToleranceSource::Registry
            ));
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_missing_unknown_and_unregistered_output_quantities() {
        for (label, replacement, expected) in [
            (
                "missing-quantity",
                "name: value, symbol: y",
                "not valid under any of the schemas",
            ),
            (
                "unknown-quantity",
                "quantity: unknown_quantity",
                "unknown quantity",
            ),
            (
                "unregistered-unit",
                "unit: 'unregistered'",
                "no registered unit",
            ),
        ] {
            let root = fixture_root(label);
            let mut text = specification(
                &label.replace('-', "_"),
                "    implementation:\n      variables: [{name: value, expr: x}]\n",
                "",
            );
            text = match label {
                "missing-quantity" => text.replace(
                    "name: value, quantity: volumetric_water_content, symbol: y",
                    replacement,
                ),
                "unknown-quantity" => {
                    text.replace("quantity: volumetric_water_content", replacement)
                }
                _ => text.replace("unit: volume_fraction", replacement),
            };
            fs::write(
                root.join(format!("specs/functions/{}.yaml", label.replace('-', "_"))),
                text,
            )
            .unwrap();
            let error = crate::load_validated_specifications(&root)
                .expect_err("invalid quantity contract must fail")
                .to_string();
            assert!(error.contains(expected), "{error}");
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn rejects_invalid_and_unknown_tolerance_overrides() {
        for (label, tolerance, expected) in [
            (
                "missing-location",
                "    verification_tolerances: {value: {absolute: 0.1}}\n",
                "required property",
            ),
            (
                "unknown-output",
                "    verification_tolerances: {other: {absolute: 0.1, source_location: Table 1}}\n",
                "unknown output",
            ),
            (
                "zero-absolute",
                "    verification_tolerances: {value: {absolute: 0.0, source_location: Table 1}}\n",
                "less than or equal to the minimum",
            ),
        ] {
            let root = fixture_root(label);
            let text = specification(
                &label.replace('-', "_"),
                &format!(
                    "{tolerance}    implementation:\n      variables: [{{name: value, expr: x}}]\n"
                ),
                "",
            );
            fs::write(
                root.join(format!("specs/functions/{}.yaml", label.replace('-', "_"))),
                text,
            )
            .unwrap();
            let error = crate::load_validated_specifications(&root)
                .expect_err("invalid override must fail")
                .to_string();
            assert!(error.contains(expected), "{error}");
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn rejects_invalid_registry_tolerances_and_duplicate_identifiers() {
        for (label, edit, expected) in [
            (
                "zero",
                "zero",
                "absolute tolerance must be finite and positive",
            ),
            (
                "negative_relative",
                "negative_relative",
                "relative tolerance must be finite and non-negative",
            ),
            (
                "duplicate_identifier",
                "duplicate_identifier",
                "duplicate entry",
            ),
            ("duplicate_unit", "duplicate_unit", "duplicate entry"),
        ] {
            let root = fixture_root(label);
            write(
                &root,
                label,
                "    implementation:\n      variables: [{name: value, expr: x}]\n",
                "",
            );
            let registry_path = root.join("specs/quantities.yaml");
            let mut registry = fs::read_to_string(&registry_path)
                .unwrap()
                .replace("\r\n", "\n");
            match edit {
                "zero" => {
                    registry = registry.replacen("absolute: 0.001", "absolute: 0.0", 1);
                }
                "negative_relative" => {
                    registry = registry.replacen("relative: 0.01", "relative: -0.01", 1);
                }
                "duplicate_identifier" => registry.push_str(
                    "\nvolumetric_water_content:\n  description: Duplicate.\n  units:\n    '1':\n      absolute: 0.1\n      rationale: Duplicate.\n",
                ),
                _ => registry = registry.replacen(
                    "    volume_fraction:\n      absolute: 0.001",
                    "    volume_fraction:\n      absolute: 0.001\n      rationale: First.\n    volume_fraction:\n      absolute: 0.002",
                    1,
                ),
            }
            fs::write(registry_path, registry).unwrap();
            let error = format!(
                "{:#}",
                crate::load_validated_specifications(&root)
                    .expect_err("invalid registry must fail")
            );
            assert!(error.contains(expected), "{error}");
            fs::remove_dir_all(root).unwrap();
        }
    }
    #[test]
    fn aliases_preserve_values_and_quantity_specific_tolerances() {
        for (unit, notation, tolerance) in [
            ("volume_percent", "vol.%", 0.1),
            ("volume_percent", "% v/v", 0.1),
            ("volume_percent", "% volume/volume", 0.1),
            ("volume_percent", "%", 0.1),
            ("volume_fraction", "cm\u{00b3}/cm\u{00b3}", 0.001),
            ("volume_fraction", "cm^3/cm^3", 0.001),
        ] {
            let root = fixture_root("unit-alias");
            let text = specification("alias", "    implementation:\n      variables: [{name: value, expr: x}]\n    verification_cases:\n      - {id: unchanged, kind: calculated, inputs: {x: 42.0}, expected: {value: 42.0}, rationale: Unchanged source value.}\n", "")
                .replace("unit: volume_fraction, reported_unit: '1'", &format!("unit: {unit}, reported_unit: '{notation}'"));
            fs::write(root.join("specs/functions/alias.yaml"), text).unwrap();
            let entries = crate::load_validated_specifications(&root).unwrap();
            let compiled = crate::compile::functions(entries).unwrap();
            assert_eq!(compiled[0].verification_cases[0].expected, vec![42.0]);
            assert_eq!(compiled[0].output_tolerances[0].absolute, tolerance);
            assert_eq!(compiled[0].output_tolerances[0].unit, unit);
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn rejects_unit_conversion_and_wrong_quantity_context() {
        for (unit, notation, expected) in [
            ("volume_fraction", "% v/v", "not an equivalent notation"),
            ("volume_percent", "m^3/m^3", "not an equivalent notation"),
            ("millimeter_per_hour", "cm/h", "not an equivalent notation"),
            ("kilopascal", "cm H2O", "not an equivalent notation"),
            ("mass_percent", "%", "no registered unit"),
            ("dimensionless", "1", "no registered unit"),
            ("unknown", "1", "unknown unit identifier"),
        ] {
            let root = fixture_root("invalid-unit");
            let text = specification(
                "invalid_unit",
                "    implementation:\n      variables: [{name: value, expr: x}]\n",
                "",
            )
            .replace(
                "unit: volume_fraction, reported_unit: '1'",
                &format!("unit: {unit}, reported_unit: '{notation}'"),
            );
            fs::write(root.join("specs/functions/invalid_unit.yaml"), text).unwrap();
            let error = crate::load_validated_specifications(&root)
                .unwrap_err()
                .to_string();
            assert!(error.contains(expected), "{error}");
            fs::remove_dir_all(root).unwrap();
        }
    }
    #[test]
    fn rejects_invalid_unit_registry_contracts() {
        for (label, extra, expected) in [
            (
                "duplicate",
                "volume_fraction: {preferred_notation: other}\n",
                "duplicate entry",
            ),
            (
                "invalid_id",
                "Bad-id: {preferred_notation: other}\n",
                "invalid unit identifier",
            ),
            (
                "empty",
                "empty: {preferred_notation: ''}\n",
                "empty or duplicate notation",
            ),
            (
                "duplicate_alias",
                "duplicate_alias: {preferred_notation: x, aliases: [x]}\n",
                "empty or duplicate notation",
            ),
            (
                "conversion",
                "conversion: {preferred_notation: x, scale: 100}\n",
                "unknown field",
            ),
            (
                "tolerance",
                "tolerance: {preferred_notation: x, absolute: 0.1}\n",
                "unknown field",
            ),
        ] {
            let root = fixture_root(label);
            write(
                &root,
                label,
                "    implementation:\n      variables: [{name: value, expr: x}]\n",
                "",
            );
            let path = root.join("specs/units.yaml");
            let mut registry = fs::read_to_string(&path).unwrap();
            registry.push_str(extra);
            fs::write(path, registry).unwrap();
            let error = format!(
                "{:#}",
                crate::load_validated_specifications(&root).unwrap_err()
            );
            assert!(error.contains(expected), "{error}");
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn shared_unit_keeps_quantity_specific_tolerances() {
        let root = fixture_root("shared-unit-tolerances");
        let path = root.join("specs/quantities.yaml");
        let mut registry = fs::read_to_string(&path).unwrap();
        registry.push_str("\nother_fraction:\n  description: Test distinct quantity.\n  units:\n    volume_fraction:\n      absolute: 0.25\n      rationale: Test quantity-specific resolution.\n");
        fs::write(path, registry).unwrap();
        for quantity in ["volumetric_water_content", "other_fraction"] {
            let text = specification(
                quantity,
                "    implementation:\n      variables: [{name: value, expr: x}]\n",
                "",
            )
            .replace(
                "quantity: volumetric_water_content",
                &format!("quantity: {quantity}"),
            );
            fs::write(root.join(format!("specs/functions/{quantity}.yaml")), text).unwrap();
        }
        let compiled =
            crate::compile::functions(crate::load_validated_specifications(&root).unwrap())
                .unwrap();
        assert_eq!(compiled[0].output_tolerances[0].absolute, 0.25);
        assert_eq!(compiled[1].output_tolerances[0].absolute, 0.001);
        assert_eq!(
            compiled[0].output_tolerances[0].unit,
            compiled[1].output_tolerances[0].unit
        );
        let path = root.join("specs/quantities.yaml");
        let registry = fs::read_to_string(&path)
            .unwrap()
            .replace("    volume_fraction:", "    missing_unit:");
        fs::write(path, registry).unwrap();
        assert!(
            crate::load_validated_specifications(&root)
                .unwrap_err()
                .to_string()
                .contains("unknown unit identifier")
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_ambiguous_notation_within_a_quantity() {
        let root = fixture_root("ambiguous-notation");
        write(
            &root,
            "ambiguous",
            "    implementation:\n      variables: [{name: value, expr: x}]\n",
            "",
        );
        let path = root.join("specs/units.yaml");
        let registry = fs::read_to_string(&path)
            .unwrap()
            .replace("\"cm^3/cm^3\",", "\"%\", \"cm^3/cm^3\",");
        fs::write(path, registry).unwrap();
        assert!(
            crate::load_validated_specifications(&root)
                .unwrap_err()
                .to_string()
                .contains("ambiguous notation")
        );
        fs::remove_dir_all(root).unwrap();
    }
    #[test]
    fn requires_normalized_and_reported_output_units() {
        for missing in ["unit: volume_fraction, ", "reported_unit: '1', "] {
            let root = fixture_root("missing-unit-metadata");
            let text = specification(
                "missing_unit",
                "    implementation:\n      variables: [{name: value, expr: x}]\n",
                "",
            )
            .replace(missing, "");
            fs::write(root.join("specs/functions/missing_unit.yaml"), text).unwrap();
            assert!(
                load(&root)
                    .unwrap_err()
                    .to_string()
                    .contains("not valid under any of the schemas")
            );
            fs::remove_dir_all(root).unwrap();
        }
    }
}
