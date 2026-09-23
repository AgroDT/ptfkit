mod error;
pub(crate) use error::{DocumentError, ReferenceError, SpecificationError};

use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
    sync::Arc,
};

use anyhow::{Context, Result};
use jsonschema::Draft;
use serde_json::Value;

use crate::{
    diagnostics::{Diagnostic, ValidationReport},
    formula,
    model::{
        Entry, EnumDefinition, EnumType, Implementation, ImplementationVariable, Input, Quantity,
        QuantityRegistry, RawExpression, RawFunction, RawInput, RawInputType, RawLookup,
        RawTreeInvocation, RawVariable, RawVariableValue, Spec,
    },
    semantic,
};

pub(crate) struct DefinitionDocument {
    pub(crate) module: String,
    pub(crate) description: String,
    pub(crate) definitions: Vec<EnumDefinition>,
}

pub(crate) struct LoadedSpecifications {
    pub(crate) entries: Vec<Entry>,
    pub(crate) definitions: Vec<DefinitionDocument>,
}

#[cfg(test)]
pub(crate) fn load(root: &Path) -> Result<Vec<Entry>> {
    Ok(load_all(root)?.entries)
}

pub(crate) fn load_all(root: &Path) -> Result<LoadedSpecifications> {
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
                errors.push(error.into());
                continue;
            }
        };
        if let Some(definition) = definitions
            .keys()
            .find(|definition| definition.file_stem() == path.file_stem())
        {
            errors.push(
                SpecificationError::ModuleCollision {
                    module: slug,
                    definition: definition.clone(),
                    path,
                }
                .into(),
            );
            continue;
        }
        let text = fs::read_to_string(&path)?;
        let yaml_value: serde_yaml::Value = match serde_yaml::from_str(&text) {
            Ok(value) => value,
            Err(error) => {
                errors.push(DocumentError::Yaml(error).at(&path).into());
                continue;
            }
        };
        let mut value = match serde_json::to_value(yaml_value) {
            Ok(value) => value,
            Err(error) => {
                errors.push(DocumentError::Json(error).at(&path).into());
                continue;
            }
        };
        let shared = match resolve_external_references(&mut value, &path, &definitions) {
            Ok(shared) => shared,
            Err(error) => {
                errors.push(DocumentError::Reference(error).at(&path).into());
                continue;
            }
        };
        errors.extend(
            validator
                .iter_errors(&value)
                .map(|error| SpecificationError::schema(&path, error).into()),
        );
        let mut spec: Spec = match serde_json::from_value(value) {
            Ok(spec) => spec,
            Err(error) => {
                errors.push(DocumentError::Metadata(error).at(&path).into());
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
                errors.push(SpecificationError::missing_implementation(&path, function).into());
            }
        }
        let expression_locations = match expression_locations(&text, &spec) {
            Ok(locations) => locations,
            Err(error) => {
                errors.push(error.at(&path).into());
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
        return Err(ValidationReport::specifications(errors).into());
    }
    let definition_documents = definitions
        .into_iter()
        .map(|(path, value)| {
            let module = source_slug(&path).expect("validated definition filename");
            let description = value["description"]
                .as_str()
                .expect("validated description")
                .to_owned();
            let members = value["$defs"].as_object().expect("validated definitions");
            let definitions = members
                .iter()
                .map(|(name, value)| {
                    let mut definition: EnumDefinition = serde_json::from_value(value.clone())?;
                    definition.enum_type = EnumType {
                        document: path.clone(),
                        name: name.clone(),
                        shared_module: Some(module.clone()),
                    };
                    Ok(definition)
                })
                .collect::<Result<Vec<_>>>()?;
            Ok(DefinitionDocument {
                module,
                description,
                definitions,
            })
        })
        .collect::<Result<Vec<_>>>()?;
    Ok(LoadedSpecifications {
        entries,
        definitions: definition_documents,
    })
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
        let module = source_slug(&path)?;
        if matches!(
            module.as_str(),
            "enums" | "lib" | "mod" | "ptfkit" | "test_support"
        ) {
            return Err(SpecificationError::ReservedModule { module, path }.into());
        }
        let text = fs::read_to_string(&path)?;
        let yaml: serde_yaml::Value =
            serde_yaml::from_str(&text).map_err(|error| DocumentError::Yaml(error).at(&path))?;
        let value =
            serde_json::to_value(yaml).map_err(|error| DocumentError::Json(error).at(&path))?;
        let errors = validator
            .iter_errors(&value)
            .map(|error| SpecificationError::schema(&path, error).into())
            .collect::<Vec<_>>();
        if !errors.is_empty() {
            return Err(ValidationReport::shared_definitions(errors).into());
        }
        definitions.insert(fs::canonicalize(path)?, value);
    }
    Ok(definitions)
}

fn resolve_external_references(
    value: &mut Value,
    document: &Path,
    documents: &BTreeMap<PathBuf, Value>,
) -> Result<BTreeMap<String, EnumType>, ReferenceError> {
    let mut references = BTreeSet::new();
    collect_external_references(value, &mut references);
    let mut shared = BTreeMap::new();
    for reference in references {
        let (file, name) = reference
            .split_once("#/$defs/")
            .filter(|(file, name)| {
                !file.is_empty() && !name.is_empty() && !name.contains(['/', '#'])
            })
            .ok_or_else(|| ReferenceError::InvalidFormat {
                reference: reference.clone(),
            })?;
        if file.contains(':') || Path::new(file).is_absolute() {
            return Err(ReferenceError::NonLocal {
                reference: reference.clone(),
            });
        }
        let target = document
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join(file);
        let target = fs::canonicalize(&target).map_err(|error| ReferenceError::Read {
            reference: reference.clone(),
            path: target.clone(),
            source: error,
        })?;
        let parsed = documents
            .get(&target)
            .ok_or_else(|| ReferenceError::OutsideDefinitions {
                reference: reference.clone(),
            })?;
        let definition =
            parsed["$defs"]
                .get(name)
                .ok_or_else(|| ReferenceError::MissingDefinition {
                    reference: reference.clone(),
                    name: name.to_owned(),
                    path: target.clone(),
                })?;
        let defs = value
            .as_object_mut()
            .ok_or(ReferenceError::InvalidRoot)?
            .entry("$defs")
            .or_insert_with(|| Value::Object(serde_json::Map::new()))
            .as_object_mut()
            .ok_or(ReferenceError::InvalidDefinitions)?;
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

fn source_slug(path: &Path) -> Result<String, SpecificationError> {
    let Some(stem) = path.file_stem().and_then(|stem| stem.to_str()) else {
        return Err(SpecificationError::NonUtf8Slug {
            path: path.to_owned(),
        });
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
        Err(SpecificationError::InvalidSlug {
            path: path.to_owned(),
        })
    }
}

fn compile(
    path: &Path,
    function: &crate::model::Function,
    implementation: &Implementation,
    expression_locations: &mut impl Iterator<Item = crate::model::SourceLocation>,
) -> Result<semantic::Function, Diagnostic> {
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
                        SpecificationError::missing_source_location(path, function, index)
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
                ImplementationVariable::Tree { name, tree } => {
                    let definition = tree
                        .definition
                        .clone()
                        .expect("tree invocation is resolved");
                    Ok(RawVariable {
                        name: name.clone(),
                        value: RawVariableValue::Tree(Box::new(RawTreeInvocation {
                            implementation_path: format!("implementation.variables[{index}].tree"),
                            arguments: tree.arguments.clone(),
                            definition,
                        })),
                    })
                }
            })
            .collect::<Result<Vec<_>, _>>()?,
    };
    let mut compiled = semantic::compile(&raw)?;
    compiled.result = validate_output(path, function, &compiled)?;
    Ok(compiled)
}

fn expression(
    path: &Path,
    function: &str,
    implementation_path: String,
    source: &str,
    source_location: crate::model::SourceLocation,
) -> Result<RawExpression, Diagnostic> {
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
        .map_err(Diagnostic::from)
}

fn expression_locations(
    text: &str,
    spec: &Spec,
) -> Result<Vec<crate::model::SourceLocation>, DocumentError> {
    let expressions = spec
        .functions
        .iter()
        .filter_map(|function| function.implementation.as_ref())
        .flat_map(|implementation| implementation.variables.iter())
        .filter_map(|variable| match variable {
            ImplementationVariable::Expression { expr, .. } => Some(expr.as_str()),
            ImplementationVariable::Lookup { .. } | ImplementationVariable::Tree { .. } => None,
        });
    let mut cursor = 0;
    let mut locations = Vec::new();

    for expression in expressions {
        let Some((offset, next_cursor)) = find_expression(text, cursor, expression) else {
            return Err(DocumentError::ExpressionNotFound {
                expression: expression.to_owned(),
            });
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
) -> Result<semantic::ResultBinding, SpecificationError> {
    if let crate::model::Outputs::Record { name, fields } = &function.outputs {
        let expected = semantic::RecordType {
            name: name.clone(),
            fields: fields.iter().map(|field| field.name.clone()).collect(),
        };
        if let Some((index, variable)) = compiled.variables.iter().enumerate().next_back() {
            let actual = match &variable.value {
                semantic::VariableValue::RecordLookup(lookup) => Some(&lookup.output),
                semantic::VariableValue::Tree(tree) => match &tree.definition.output {
                    semantic::ValueType::Record(record) => Some(record),
                    semantic::ValueType::Number | semantic::ValueType::Enum(_) => None,
                },
                semantic::VariableValue::Expression(_) => None,
            };
            if actual == Some(&expected) {
                return Ok(semantic::ResultBinding::RecordVariable(index));
            }
            if actual.is_some_and(|actual| actual.name == expected.name) {
                return Err(SpecificationError::record_output_mismatch(
                    path,
                    function,
                    index,
                    &expected.name,
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
                    semantic::VariableValue::Expression(_) => Some(variable.name.as_str()),
                    semantic::VariableValue::Tree(ref tree)
                        if tree.definition.output == semantic::ValueType::Number =>
                    {
                        Some(variable.name.as_str())
                    }
                    semantic::VariableValue::Tree(_) => None,
                    semantic::VariableValue::RecordLookup(_) => None,
                }),
        )
        .collect::<std::collections::BTreeSet<_>>();
    let missing = output_names
        .into_iter()
        .filter(|name| !output_sources.contains(name.as_str()))
        .collect::<Vec<_>>();
    if missing.is_empty() {
        Ok(semantic::ResultBinding::Fields)
    } else {
        Err(SpecificationError::missing_outputs(path, function, missing))
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

    fn scalar_tree_specification() -> &'static str {
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
  ScalarValue:
    {type: scalar, name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}
  ScalarTree:
    type: tree
    inputs:
      - {name: category, $ref: '#/$defs/Category'}
      - {name: predictor, type: number}
    output: {$ref: '#/$defs/ScalarValue'}
    root:
      split: {input: category, operator: in, values: [coarse]}
      yes:
        split: {input: predictor, operator: lt, value: 2.0}
        yes: {leaf: 1.0}
        no: {leaf: 2.0}
      no: {leaf: 3.0}
functions:
  - name: calc_ptf_tree_branch
    status: ready-for-implementation
    public_api: {name: calc_ptf_tree_branch, result_class: null, summary: Test named tree.}
    scope:
      prediction_target: Test value.
      models: {h_theta: null, k_h: null}
    inputs:
      - {$ref: '#/$defs/Category', name: category}
      - {name: x, symbol: x, unit: '1', domain: null, description: Test input.}
    outputs: {$ref: '#/$defs/ScalarValue'}
    implementation:
      variables:
        - {name: value, tree: {definition: {$ref: '#/$defs/ScalarTree'}, arguments: {category: category, predictor: x}}}
    verification_cases:
      - {id: below_boundary, kind: calculated, inputs: {category: coarse, x: 1.0}, expected: {value: 1.0}, rationale: Explicit fixture branch.}
      - {id: at_boundary, kind: calculated, inputs: {category: coarse, x: 2.0}, expected: {value: 2.0}, rationale: Equality takes the No branch.}
      - {id: other_category, kind: calculated, inputs: {category: fine, x: 1.0}, expected: {value: 3.0}, rationale: Explicit fixture branch.}
"#
    }

    fn named_tree_specification() -> &'static str {
        r#"source:
  summary: Named tree test source.
  citation_apa: Test (2026).
  doi: null
$defs:
  Category:
    type: enum
    description: Test category.
    values:
      - {name: coarse, value: Coarse}
      - {name: fine, value: Fine}
  ScalarValue:
    {type: scalar, name: value, quantity: volumetric_water_content, symbol: y, unit: volume_fraction, reported_unit: '1', domain: null, description: Test output.}
  Pair:
    type: record
    name: Pair
    fields:
      - {name: low, quantity: volumetric_water_content, symbol: lo, unit: volume_fraction, reported_unit: '1', domain: null, description: Low value.}
      - {name: high, quantity: volumetric_water_content, symbol: hi, unit: volume_fraction, reported_unit: '1', domain: null, description: High value.}
  ScalarTree:
    type: tree
    inputs:
      - {name: category, $ref: '#/$defs/Category'}
      - {name: predictor, type: number}
    output: {$ref: '#/$defs/ScalarValue'}
    root:
      match:
        input: category
        cases:
          - values: [coarse]
            then:
              split: {input: predictor, operator: lt, value: 2.0}
              yes: {leaf: 1.0}
              no: {leaf: 2.0}
          - values: [fine]
            then: {leaf: 3.0}
  RecordTree:
    type: tree
    inputs:
      - {name: category, $ref: '#/$defs/Category'}
    output: {$ref: '#/$defs/Pair'}
    root:
      match:
        input: category
        cases:
          - {values: [coarse], then: {leaf: {low: 1.0, high: 2.0}}}
          - {values: [fine], then: {leaf: {low: 3.0, high: 5.0}}}
functions:
  - name: calc_ptf_tree_scaled
    status: ready-for-implementation
    public_api: {name: calc_ptf_tree_scaled, result_class: null, summary: Scale a tree result.}
    scope: {prediction_target: Test value., models: {h_theta: null, k_h: null}}
    inputs:
      - {name: category, $ref: '#/$defs/Category'}
      - {name: x, symbol: x, unit: '1', domain: null, description: First input.}
      - {name: y, symbol: y, unit: '1', domain: null, description: Second input.}
    outputs: {$ref: '#/$defs/ScalarValue'}
    implementation:
      variables:
        - {name: selected, tree: {definition: {$ref: '#/$defs/ScalarTree'}, arguments: {category: category, predictor: x}}}
        - {name: value, expr: 'selected * 10'}
    verification_cases:
      - {id: strict_boundary, kind: calculated, inputs: {category: coarse, x: 2.0, y: 9.0}, expected: {value: 20.0}, rationale: Equality takes the no branch before scaling.}
      - {id: enum_group, kind: calculated, inputs: {category: fine, x: 1.0, y: 9.0}, expected: {value: 30.0}, rationale: Fine selects its explicit match arm.}
  - name: calc_ptf_tree_rebound
    status: ready-for-implementation
    public_api: {name: calc_ptf_tree_rebound, result_class: null, summary: Rebind a shared tree.}
    scope: {prediction_target: Test value., models: {h_theta: null, k_h: null}}
    inputs:
      - {name: category, $ref: '#/$defs/Category'}
      - {name: x, symbol: x, unit: '1', domain: null, description: First input.}
      - {name: y, symbol: y, unit: '1', domain: null, description: Second input.}
    outputs: {$ref: '#/$defs/ScalarValue'}
    implementation:
      variables:
        - {name: value, tree: {definition: {$ref: '#/$defs/ScalarTree'}, arguments: {category: category, predictor: y}}}
    verification_cases:
      - {id: rebound_argument, kind: calculated, inputs: {category: coarse, x: 9.0, y: 1.0}, expected: {value: 1.0}, rationale: The formal predictor is bound to y rather than x.}
  - name: calc_ptf_tree_fields
    status: ready-for-implementation
    public_api: {name: calc_ptf_tree_fields, result_class: null, summary: Use record tree fields.}
    scope: {prediction_target: Test value., models: {h_theta: null, k_h: null}}
    inputs:
      - {name: category, $ref: '#/$defs/Category'}
    outputs: {$ref: '#/$defs/ScalarValue'}
    implementation:
      variables:
        - {name: pair, tree: {definition: {$ref: '#/$defs/RecordTree'}, arguments: {category: category}}}
        - {name: value, expr: 'pair.low + pair.high'}
    verification_cases:
      - {id: record_fields, kind: calculated, inputs: {category: fine}, expected: {value: 8.0}, rationale: Both fields from the fine record leaf contribute.}
  - name: calc_ptf_tree_record
    status: ready-for-implementation
    public_api: {name: calc_ptf_tree_record, result_class: Pair, summary: Return a tree record.}
    scope: {prediction_target: Test pair., models: {h_theta: null, k_h: null}}
    inputs:
      - {name: category, $ref: '#/$defs/Category'}
    outputs: {$ref: '#/$defs/Pair'}
    implementation:
      variables:
        - {name: result, tree: {definition: {$ref: '#/$defs/RecordTree'}, arguments: {category: category}}}
    verification_cases:
      - {id: record_result, kind: calculated, inputs: {category: coarse}, expected: {low: 1.0, high: 2.0}, rationale: The complete record leaf is returned.}
"#
    }

    #[test]
    fn preserves_typed_diagnostics_and_report_order() {
        use crate::{
            diagnostics::{Diagnostic, ValidationReport},
            formula::Span,
            semantic::SemanticErrorKind,
        };

        let root = fixture_root("typed-diagnostics");
        // Creation order differs from the loader's filename order.
        for (slug, expression) in [("c_semantic", "missing"), ("b_parse", "1e999")] {
            write(
                &root,
                slug,
                &format!(
                    "    implementation:\n      variables: [{{name: value, expr: '{expression}'}}]\n"
                ),
                "",
            );
        }
        fs::write(root.join("specs/functions/a_invalid.yaml"), "[").unwrap();

        let error = crate::load_validated_specifications(&root).unwrap_err();
        let report = error.downcast_ref::<ValidationReport>().unwrap();
        let [
            Diagnostic::Specification(specification),
            Diagnostic::Parse(parse),
            Diagnostic::Semantic(semantic),
        ] = report.diagnostics.as_slice()
        else {
            panic!("expected specification, parser, and semantic diagnostics: {report:?}");
        };
        let super::SpecificationError::Document {
            path,
            kind: super::DocumentError::Yaml(_),
        } = specification.as_ref()
        else {
            panic!("expected malformed YAML diagnostic: {specification:?}");
        };
        assert_eq!(path, &root.join("specs/functions/a_invalid.yaml"));
        let parse_location = format!(
            "{} -> function calc_ptf_b_parse -> implementation.variables[0].expr",
            root.join("specs/functions/b_parse.yaml").display()
        );
        assert_eq!(parse.location, parse_location);
        assert_eq!(parse.span, Span { start: 0, end: 5 });
        assert_eq!(
            semantic.kind,
            SemanticErrorKind::UnknownIdentifier {
                name: "missing".into()
            }
        );
        assert_eq!(semantic.function, "calc_ptf_c_semantic");
        assert_eq!(
            semantic.implementation_path,
            "implementation.variables[0].expr"
        );
        assert_eq!(semantic.span, Span { start: 0, end: 7 });
        assert_eq!(
            std::error::Error::source(semantic.as_ref())
                .unwrap()
                .downcast_ref::<SemanticErrorKind>(),
            Some(&SemanticErrorKind::UnknownIdentifier {
                name: "missing".into()
            })
        );
        fs::remove_dir_all(root).unwrap();
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
            crate::semantic::VariableValue::Expression(_)
        ));
        let compiled = crate::compile::functions(entries).unwrap();
        let rust = crate::targets::render_rust_for_test(&compiled).unwrap();
        let rust = &rust
            .iter()
            .find(|file| file.path.ends_with("record_lookup_expression.rs"))
            .unwrap()
            .contents;
        snapbox::assert_data_eq!(
            rust,
            snapbox::file!["fixtures/expected/record_lookup/source.rs"]
        );
        let (c_headers, cpp_modules) = crate::targets::render_native_for_test(&compiled).unwrap();
        let c = &c_headers
            .iter()
            .find(|file| file.path.ends_with("record_lookup_expression.h"))
            .unwrap()
            .contents;
        snapbox::assert_data_eq!(
            c,
            snapbox::file!["fixtures/expected/record_lookup/source.h"]
        );
        let cpp = &cpp_modules
            .iter()
            .find(|file| file.path.ends_with("record_lookup_expression.cppm"))
            .unwrap()
            .contents;
        assert!(cpp.contains("namespace ptfkit::record_lookup_expression {"));
        assert!(!cpp.contains("export namespace ptfkit::record_lookup_expression"));
        assert!(cpp.contains("export enum class Texture"));
        assert!(cpp.contains("struct Parameters"));
        assert!(!cpp.contains("export struct Parameters"));
        assert!(!cpp.contains("export [[nodiscard]] inline Parameters parameters_from_texture"));
        assert!(
            cpp.contains(
                "export [[nodiscard]]\n    inline double calc_ptf_record_lookup_expression"
            )
        );
        snapbox::assert_data_eq!(
            format!("{}\n", cpp.trim_end_matches('\n')),
            snapbox::file!["fixtures/expected/record_lookup/source.cppm"]
        );
        let extension = crate::targets::render_python_extension_for_test(&compiled).unwrap();
        let extension = &extension
            .iter()
            .find(|file| file.path.ends_with("record_lookup_expression.c"))
            .unwrap()
            .contents;
        snapbox::assert_data_eq!(
            extension,
            snapbox::file!["fixtures/expected/record_lookup/extension.c"]
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn compiles_and_renders_strict_named_tree_branches() {
        let root = fixture_root("tree-branch");
        fs::write(
            root.join("specs/functions/tree_branch.yaml"),
            scalar_tree_specification(),
        )
        .unwrap();

        let entries = load(&root).unwrap();
        assert!(matches!(
            entries[0].implementations[0].as_ref().unwrap().variables[0].value,
            crate::semantic::VariableValue::Tree(_)
        ));
        let compiled = crate::compile::functions(entries).unwrap();
        let rust = crate::targets::render_rust_for_test(&compiled).unwrap();
        let rust = &rust
            .iter()
            .find(|file| file.path.ends_with("tree_branch.rs"))
            .unwrap()
            .contents;
        assert!(
            rust.contains("matches ! (category , Category :: Coarse)"),
            "{rust}"
        );
        assert!(rust.contains("predictor < 2.0f64"), "{rust}");
        assert!(rust.contains("fn at_boundary"), "{rust}");
        assert!(
            rust.contains("calc_ptf_tree_branch (Category :: Coarse , 2f64)"),
            "{rust}"
        );
        snapbox::assert_data_eq!(rust, snapbox::file!["fixtures/expected/tree/branch.rs"]);

        let (c_headers, cpp_modules) = crate::targets::render_native_for_test(&compiled).unwrap();
        let c = &c_headers
            .iter()
            .find(|file| file.path.ends_with("tree_branch.h"))
            .unwrap()
            .contents;
        assert!(
            c.contains("if (category == tree_branch_category_coarse)"),
            "{c}"
        );
        assert!(c.contains("if (predictor < 2.0)"), "{c}");
        assert!(c.contains("return 1.0;"), "{c}");
        assert!(c.contains("return 2.0;"), "{c}");
        assert!(c.contains("return 3.0;"), "{c}");
        snapbox::assert_data_eq!(c, snapbox::file!["fixtures/expected/tree/branch.h"]);

        let cpp = &cpp_modules
            .iter()
            .find(|file| file.path.ends_with("tree_branch.cppm"))
            .unwrap()
            .contents;
        assert!(cpp.contains("if (category == Category::Coarse)"), "{cpp}");
        assert!(cpp.contains("if (predictor < 2.0)"), "{cpp}");
        assert_eq!(cpp.matches("namespace ptfkit::tree_branch {").count(), 1);
        snapbox::assert_data_eq!(cpp, snapbox::file!["fixtures/expected/tree/branch.cppm"]);

        let extension = crate::targets::render_python_extension_for_test(&compiled).unwrap();
        let extension = &extension
            .iter()
            .find(|file| file.path.ends_with("tree_branch.c"))
            .unwrap()
            .contents;
        assert!(
            extension.contains("calc_ptf_tree_branch(category, x)"),
            "{extension}"
        );
        snapbox::assert_data_eq!(extension, snapbox::file!["fixtures/expected/tree/branch.c"]);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn renders_a_named_tree_call_as_an_intermediate_numeric_variable() {
        let root = fixture_root("tree-variable");
        let specification = scalar_tree_specification()
            .replace(
                "        - {name: value, tree:",
                "        - {name: branch_value, tree:",
            )
            .replace(
                "arguments: {category: category, predictor: x}}}\n    verification_cases:",
                "arguments: {category: category, predictor: x}}}\n        - {name: value, expr: branch_value * 10}\n    verification_cases:",
            )
            .replace("expected: {value: 1.0}", "expected: {value: 10.0}")
            .replace("expected: {value: 2.0}", "expected: {value: 20.0}")
            .replace("expected: {value: 3.0}", "expected: {value: 30.0}");
        fs::write(
            root.join("specs/functions/tree_variable.yaml"),
            specification,
        )
        .unwrap();

        let compiled = crate::compile::functions(load(&root).unwrap()).unwrap();
        let rust = crate::targets::render_rust_for_test(&compiled).unwrap();
        let rust = &rust
            .iter()
            .find(|file| file.path.ends_with("tree_variable.rs"))
            .unwrap()
            .contents;
        assert!(rust.contains("let branch_value = scalar_tree"), "{rust}");
        assert!(rust.contains("branch_value * 10.0f64"), "{rust}");
        snapbox::assert_data_eq!(rust, snapbox::file!["fixtures/expected/tree/variable.rs"]);

        let (c_headers, cpp_modules) = crate::targets::render_native_for_test(&compiled).unwrap();
        let c = &c_headers
            .iter()
            .find(|file| file.path.ends_with("tree_variable.h"))
            .unwrap()
            .contents;
        assert!(c.contains("const double branch_value ="), "{c}");
        assert!(c.contains("tree_variable_scalar_tree"), "{c}");
        assert!(!c.contains(" ? "), "{c}");
        assert!(c.contains("branch_value * 10.0"), "{c}");
        snapbox::assert_data_eq!(c, snapbox::file!["fixtures/expected/tree/variable.h"]);
        let cpp = &cpp_modules
            .iter()
            .find(|file| file.path.ends_with("tree_variable.cppm"))
            .unwrap()
            .contents;
        assert!(cpp.contains("const double branch_value ="), "{cpp}");
        assert!(cpp.contains("branch_value * 10.0"), "{cpp}");
        snapbox::assert_data_eq!(cpp, snapbox::file!["fixtures/expected/tree/variable.cppm"]);

        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_invalid_named_tree_arguments_leaves_and_match_groups() {
        for (label, edit, expected) in [
            (
                "tree-missing-argument",
                (
                    "arguments: {category: category, predictor: x}",
                    "arguments: {category: category}",
                ),
                "missing [\"predictor\"]",
            ),
            (
                "tree-unknown-argument",
                (
                    "arguments: {category: category, predictor: x}",
                    "arguments: {category: category, predictor: x, other: y}",
                ),
                "unknown [\"other\"]",
            ),
            (
                "tree-wrong-argument-type",
                (
                    "arguments: {category: category, predictor: x}",
                    "arguments: {category: x, predictor: x}",
                ),
                "input `category` requires enum `Category`",
            ),
            (
                "tree-later-argument",
                (
                    "arguments: {category: category, predictor: x}",
                    "arguments: {category: category, predictor: value}",
                ),
                "cannot reference a later variable",
            ),
            (
                "tree-record-leaf-shape",
                ("{leaf: {low: 1.0, high: 2.0}}", "{leaf: {low: 1.0}}"),
                "keys must exactly match output fields",
            ),
            (
                "tree-overlapping-match",
                (
                    "- values: [fine]\n            then: {leaf: 3.0}",
                    "- values: [coarse, fine]\n            then: {leaf: 3.0}",
                ),
                "match cases overlap on enum member `coarse`",
            ),
            (
                "tree-incomplete-match",
                (
                    "          - values: [fine]\n            then: {leaf: 3.0}\n  RecordTree:",
                    "  RecordTree:",
                ),
                "match cases must cover every member",
            ),
        ] {
            let root = fixture_root(label);
            let specification = named_tree_specification().replacen(edit.0, edit.1, 1);
            fs::write(root.join("specs/functions/named_tree.yaml"), specification).unwrap();
            let failure = load(&root).expect_err("invalid named tree must fail");
            if label == "tree-missing-argument" {
                let report = failure
                    .downcast_ref::<crate::diagnostics::ValidationReport>()
                    .unwrap();
                assert!(report.diagnostics.iter().any(|diagnostic| matches!(
                    diagnostic,
                    crate::diagnostics::Diagnostic::Semantic(error)
                        if matches!(&error.kind, crate::semantic::SemanticErrorKind::TreeArguments { tree, missing, unknown }
                            if tree == "ScalarTree" && missing == &["predictor"] && unknown.is_empty())
                )));
            }
            let error = failure.to_string();
            assert!(error.contains(expected), "{error}");
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn rejects_named_tree_predicates_with_wrong_input_types_or_members() {
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
                    "split: {input: predictor, operator: in, values: [coarse]}",
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
                "unknown input `missing`",
            ),
        ] {
            let root = fixture_root(label);
            let text = scalar_tree_specification().replacen(edit.0, edit.1, 1);
            fs::write(root.join("specs/functions/tree_branch.yaml"), text).unwrap();
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
    fn rejects_shared_modules_that_shadow_target_infrastructure() {
        for module in ["enums", "lib", "mod", "ptfkit", "test_support"] {
            let root = fixture_root(&format!("reserved-shared-module-{module}"));
            crate::test_support::copy_shared_definition_fixture(&root);
            let path = root.join(format!("specs/definitions/{module}.yaml"));
            fs::rename(root.join("specs/definitions/soil.yaml"), &path).unwrap();
            let error = load(&root).unwrap_err();
            let super::SpecificationError::ReservedModule {
                module: actual,
                path: actual_path,
            } = error.downcast_ref::<super::SpecificationError>().unwrap()
            else {
                panic!("expected a reserved module error: {error:?}");
            };
            assert_eq!(actual, module);
            assert_eq!(actual_path, &path);
            fs::remove_dir_all(root).unwrap();
        }
    }

    #[test]
    fn shared_document_requires_a_general_description() {
        let root = fixture_root("shared-description-required");
        crate::test_support::copy_shared_definition_fixture(&root);
        let path = root.join("specs/definitions/soil.yaml");
        let yaml = fs::read_to_string(&path).unwrap();
        fs::write(
            &path,
            yaml.replace(
                "description: Shared soil categories for test sources.\n",
                "",
            ),
        )
        .unwrap();
        let error = load(&root).unwrap_err();
        assert!(error.to_string().contains("invalid shared definitions"));
        assert!(error.to_string().contains("description"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_shared_and_source_module_collisions() {
        use crate::{
            diagnostics::{Diagnostic, ValidationReport},
            specs::SpecificationError,
        };

        let root = fixture_root("shared-module-collision");
        crate::test_support::copy_shared_definition_fixture(&root);
        let path = root.join("specs/functions/soil.yaml");
        fs::rename(root.join("specs/functions/first_source.yaml"), &path).unwrap();
        let error = crate::load_validated_specifications(&root).unwrap_err();
        let report = error.downcast_ref::<ValidationReport>().unwrap();
        let [Diagnostic::Specification(error)] = report.diagnostics.as_slice() else {
            panic!("expected one module collision: {report:?}");
        };
        let SpecificationError::ModuleCollision {
            module,
            definition,
            path: actual,
        } = error.as_ref()
        else {
            panic!("expected a module collision: {error:?}");
        };
        assert_eq!(module, "soil");
        assert_eq!(
            definition,
            &fs::canonicalize(root.join("specs/definitions/soil.yaml")).unwrap()
        );
        assert_eq!(actual, &path);
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
        for (label, reference) in [
            (
                "missing-shared-definition",
                "../definitions/missing.yaml#/$defs/Category",
            ),
            (
                "missing-shared-member",
                "../definitions/soil.yaml#/$defs/MissingCategory",
            ),
            (
                "unsupported-shared-fragment",
                "../definitions/soil.yaml#/$defs/SharedCategory/values",
            ),
            (
                "remote-shared-definition",
                "https://example.test/soil.yaml#/$defs/Category",
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
            let report = error
                .downcast_ref::<crate::diagnostics::ValidationReport>()
                .unwrap();
            let [crate::diagnostics::Diagnostic::Specification(error)] =
                report.diagnostics.as_slice()
            else {
                panic!("expected one specification error: {report:?}");
            };
            let super::SpecificationError::Document {
                path,
                kind: super::DocumentError::Reference(error),
            } = error.as_ref()
            else {
                panic!("expected reference error: {error:?}");
            };
            assert_eq!(path, &root.join("specs/functions/example.yaml"));
            match (label, error) {
                (
                    "missing-shared-definition",
                    super::ReferenceError::Read {
                        reference: actual,
                        path,
                        source,
                    },
                ) => {
                    assert_eq!(actual, reference);
                    assert_eq!(
                        path,
                        &root.join("specs/functions/../definitions/missing.yaml")
                    );
                    assert_eq!(source.kind(), std::io::ErrorKind::NotFound);
                }
                (
                    "missing-shared-member",
                    super::ReferenceError::MissingDefinition {
                        reference: actual,
                        name,
                        path,
                    },
                ) => {
                    assert_eq!(actual, reference);
                    assert_eq!(name, "MissingCategory");
                    assert_eq!(
                        path,
                        &fs::canonicalize(root.join("specs/definitions/soil.yaml")).unwrap()
                    );
                }
                (
                    "unsupported-shared-fragment",
                    super::ReferenceError::InvalidFormat { reference: actual },
                )
                | (
                    "remote-shared-definition",
                    super::ReferenceError::NonLocal { reference: actual },
                ) => {
                    assert_eq!(actual, reference);
                }
                _ => panic!("unexpected reference error for {label}: {error:?}"),
            }
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
            error.contains("record value type `Parameters` does not exactly match"),
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

        let error =
            crate::load_validated_specifications(&root).expect_err("duplicate case IDs must fail");
        let report = error
            .downcast_ref::<crate::diagnostics::ValidationReport>()
            .unwrap();
        let [crate::diagnostics::Diagnostic::Validation(error)] = report.diagnostics.as_slice()
        else {
            panic!("expected one validation error: {report:?}");
        };
        let crate::validate::ValidationError::Function {
            document,
            path,
            function,
            kind: crate::validate::ValidationKind::DuplicateCaseId { id },
        } = error.as_ref()
        else {
            panic!("expected duplicate verification case ID: {error:?}");
        };
        assert_eq!(
            document,
            &root.join("specs/functions/duplicate_case_id.yaml")
        );
        assert_eq!(path, "verification_cases");
        assert_eq!(function.as_deref(), Some("calc_ptf_duplicate_case_id"));
        assert_eq!(id, "reference");
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

        let entries = crate::load_validated_specifications(&root).unwrap();
        let error =
            crate::compile::functions(entries).expect_err("non-discriminating tolerance must fail");
        let crate::compile::CompileError::NonDiscriminatingTolerance {
            function,
            case_id,
            output,
            resolved,
            absolute,
            relative,
            magnitude,
        } = error
        else {
            panic!("unexpected error: {error:?}");
        };
        assert_eq!(function, "calc_ptf_nondiscriminating_tolerance");
        assert_eq!(case_id, "reference");
        assert_eq!(output, "value");
        assert_eq!(
            (resolved, absolute, relative, magnitude),
            (1.0, 1.0, 0.0, 1.0)
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

        let entries = crate::load_validated_specifications(&root).unwrap();
        let error = crate::compile::functions(entries)
            .expect_err("non-discriminating relative tolerance must fail");
        let crate::compile::CompileError::NonDiscriminatingTolerance {
            function,
            case_id,
            output,
            resolved,
            absolute,
            relative,
            magnitude,
        } = error
        else {
            panic!("unexpected error: {error:?}");
        };
        assert_eq!(function, "calc_ptf_nondiscriminating_relative_tolerance");
        assert_eq!(case_id, "reference");
        assert_eq!(output, "value");
        assert_eq!(
            (resolved, absolute, relative, magnitude),
            (1.0, 0.001, 1.0, 1.0)
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
        let entries = crate::load_validated_specifications(&root).unwrap();
        let error = crate::compile::functions(entries).expect_err("unknown input must fail");
        assert!(
            matches!(error, crate::compile::CompileError::UnknownInput { case_id, name } if case_id == "reference" && name == "stale")
        );
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
        let entries = crate::load_validated_specifications(&root).unwrap();
        let error = crate::compile::functions(entries).expect_err("missing input must fail");
        assert!(
            matches!(error, crate::compile::CompileError::MissingInput { case_id, name } if case_id == "reference" && name == "y")
        );
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

        let entries = crate::load_validated_specifications(&root).unwrap();
        let compiled =
            crate::compile::functions(entries).expect("shared output definitions must compile");
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
