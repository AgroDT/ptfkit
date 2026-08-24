use std::{collections::BTreeMap, path::PathBuf};

use serde::{Deserialize, Deserializer, Serialize};

#[derive(Clone, Debug, Serialize)]
pub(crate) struct Spec {
    pub(crate) source: Source,
    #[serde(default)]
    pub(crate) scope: Scope,
    #[serde(default)]
    pub(crate) generation: Generation,
    pub(crate) functions: Vec<Function>,
}

#[derive(Deserialize)]
struct RawSpec {
    source: Source,
    #[serde(default)]
    scope: Scope,
    #[serde(default)]
    generation: Generation,
    #[serde(default, rename = "$defs")]
    definitions: BTreeMap<String, Definition>,
    functions: Vec<FunctionReference>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(untagged)]
enum Definition {
    Enum(EnumDefinition),
    Lookup(LookupDefinition),
    Output(Outputs),
    Parameter(Parameter),
}

#[derive(Clone, Debug, Deserialize)]
struct FunctionReference {
    name: String,
    status: String,
    public_api: PublicApi,
    scope: FunctionScope,
    inputs: Vec<InputReference>,
    outputs: OutputReference,
    implementation: Option<Implementation>,
    #[serde(default)]
    golden_tests: Vec<GoldenTest>,
    #[serde(default)]
    documentation: Documentation,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(untagged)]
enum InputReference {
    Parameter(Parameter),
    Type(NamedReference),
    Reference(Reference),
}

#[derive(Clone, Debug, Deserialize)]
struct NamedReference {
    name: String,
    description: Option<String>,
    #[serde(flatten)]
    reference: Reference,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(untagged)]
enum OutputReference {
    Inline(Outputs),
    Reference(Reference),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Reference {
    #[serde(rename = "$ref")]
    target: String,
}

impl<'de> Deserialize<'de> for Spec {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let raw = RawSpec::deserialize(deserializer)?;
        let lookup_definitions = raw
            .definitions
            .iter()
            .filter_map(|(name, definition)| match definition {
                Definition::Lookup(definition) => Some(
                    resolve_lookup_definition(name, definition, &raw.definitions)
                        .map(|definition| (name.clone(), definition)),
                ),
                _ => None,
            })
            .collect::<Result<BTreeMap<_, _>, _>>()
            .map_err(serde::de::Error::custom)?;
        let functions = raw
            .functions
            .into_iter()
            .map(|function| {
                let inputs = function
                    .inputs
                    .into_iter()
                    .map(|input| match input {
                        InputReference::Parameter(parameter) => Ok(Input::Parameter(parameter)),
                        InputReference::Type(reference) => resolve_input_type(
                            reference,
                            &raw.definitions,
                            &function.name,
                        ),
                        InputReference::Reference(reference) => {
                            let name = definition_name(&reference.target)?;
                            match raw.definitions.get(name) {
                                Some(Definition::Parameter(parameter)) => {
                                    Ok(Input::Parameter(parameter.clone()))
                                }
                                Some(Definition::Enum(_)) | Some(Definition::Lookup(_)) => {
                                    Err(format!(
                                        "function {} must bind a name when referencing type definition `{name}` as an input",
                                        function.name
                                    ))
                                }
                                Some(Definition::Output(_)) => Err(format!(
                                    "function {} references output definition `{name}` as an input",
                                    function.name
                                )),
                                None => Err(format!(
                                    "function {} references unknown definition `{name}`",
                                    function.name
                                )),
                            }
                        }
                    })
                    .collect::<Result<Vec<_>, _>>()?;
                let outputs = match function.outputs {
                    OutputReference::Inline(outputs) => Ok(outputs),
                    OutputReference::Reference(reference) => {
                        let name = definition_name(&reference.target)?;
                        match raw.definitions.get(name) {
                            Some(Definition::Enum(_)) | Some(Definition::Lookup(_)) => Err(format!(
                                "function {} references non-output definition `{name}` as an output",
                                function.name
                            )),
                            Some(Definition::Parameter(_)) => Err(format!(
                                "function {} references parameter definition `{name}` as an output",
                                function.name
                            )),
                            Some(Definition::Output(outputs)) => Ok(outputs.clone()),
                            None => Err(format!(
                                "function {} references unknown definition `{name}`",
                                function.name
                            )),
                        }
                    }
                }?;
                let implementation = function
                    .implementation
                    .map(|mut implementation| {
                        for variable in &mut implementation.variables {
                            if let ImplementationVariable::Lookup { lookup, .. } = variable {
                                let name = definition_name(&lookup.table.target)?;
                                lookup.definition = Some(
                                    lookup_definitions.get(name).cloned().ok_or_else(|| {
                                        format!(
                                            "function {} references unknown lookup definition `{name}`",
                                            function.name
                                        )
                                    })?,
                                );
                            }
                        }
                        Ok::<_, String>(implementation)
                    })
                    .transpose()?;
                Ok(Function {
                    name: function.name,
                    status: function.status,
                    public_api: function.public_api,
                    scope: function.scope,
                    inputs,
                    outputs,
                    implementation,
                    golden_tests: function.golden_tests,
                    documentation: function.documentation,
                })
            })
            .collect::<Result<Vec<_>, String>>()
            .map_err(serde::de::Error::custom)?;
        Ok(Self {
            source: raw.source,
            scope: raw.scope,
            generation: raw.generation,
            functions,
        })
    }
}

fn resolve_input_type(
    input: NamedReference,
    definitions: &BTreeMap<String, Definition>,
    function: &str,
) -> Result<Input, String> {
    let type_name = definition_name(&input.reference.target)?;
    match definitions.get(type_name) {
        Some(Definition::Enum(definition)) => {
            let mut definition = definition.clone();
            definition.name = type_name.to_owned();
            Ok(Input::Enum {
                name: input.name,
                description: input.description,
                definition,
            })
        }
        Some(Definition::Output(_))
        | Some(Definition::Lookup(_))
        | Some(Definition::Parameter(_)) => Err(format!(
            "function {function} input {} references non-enum definition `{type_name}` as its type",
            input.name
        )),
        None => Err(format!(
            "function {function} input {} references unknown enum definition `{type_name}`",
            input.name
        )),
    }
}

fn resolve_lookup_definition(
    name: &str,
    definition: &LookupDefinition,
    definitions: &BTreeMap<String, Definition>,
) -> Result<LookupDefinition, String> {
    let input_name = definition_name(&definition.input.target)?;
    let input_type = match definitions.get(input_name) {
        Some(Definition::Enum(definition)) => {
            let mut definition = definition.clone();
            definition.name = input_name.to_owned();
            definition
        }
        Some(_) => {
            return Err(format!(
                "lookup `{name}` input must reference an enum definition"
            ));
        }
        None => {
            return Err(format!(
                "lookup `{name}` references unknown input type `{input_name}`"
            ));
        }
    };
    let output_name = definition_name(&definition.output.target)?;
    let output_type = match definitions.get(output_name) {
        Some(Definition::Output(output @ Outputs::Record { .. })) => output.clone(),
        Some(_) => {
            return Err(format!(
                "lookup `{name}` output must reference a record definition"
            ));
        }
        None => {
            return Err(format!(
                "lookup `{name}` references unknown output type `{output_name}`"
            ));
        }
    };
    let mut resolved = definition.clone();
    resolved.name = name.to_owned();
    resolved.input_type = Some(input_type);
    resolved.output_type = Some(output_type);
    validate_lookup_values(&resolved)?;
    Ok(resolved)
}

fn validate_lookup_values(lookup: &LookupDefinition) -> Result<(), String> {
    let enum_type = lookup
        .input_type
        .as_ref()
        .expect("lookup input type is resolved");
    let output = lookup
        .output_type
        .as_ref()
        .expect("lookup output type is resolved");
    let output_names = output
        .fields()
        .iter()
        .map(|field| field.name.as_str())
        .collect::<std::collections::BTreeSet<_>>();
    let mut keys = std::collections::BTreeSet::new();
    for (index, row) in lookup.values.iter().enumerate() {
        if !keys.insert(row.key.as_str()) {
            return Err(format!(
                "lookup `{}` has duplicate key `{}` at value {index}",
                lookup.name, row.key
            ));
        }
        if !enum_type.values.iter().any(|member| member.name == row.key) {
            return Err(format!(
                "lookup `{}` has unknown enum member `{}` at value {index}",
                lookup.name, row.key
            ));
        }
        let row_names = row
            .value
            .keys()
            .map(String::as_str)
            .collect::<std::collections::BTreeSet<_>>();
        if row_names != output_names {
            return Err(format!(
                "lookup `{}` value {index} keys must exactly match output fields",
                lookup.name
            ));
        }
    }
    let enum_members = enum_type
        .values
        .iter()
        .map(|member| member.name.as_str())
        .collect::<std::collections::BTreeSet<_>>();
    if keys != enum_members {
        return Err(format!(
            "lookup `{}` values must cover every member of enum `{}` exactly once",
            lookup.name, enum_type.name
        ));
    }
    Ok(())
}

fn definition_name(reference: &str) -> Result<&str, String> {
    let Some(name) = reference.strip_prefix("#/$defs/") else {
        return Err(format!(
            "reference `{reference}` must start with `#/$defs/`"
        ));
    };
    if name.is_empty() || name.contains('/') {
        return Err(format!(
            "reference `{reference}` must name exactly one local definition"
        ));
    }
    Ok(name)
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Source {
    pub(crate) summary: String,
    pub(crate) citation_apa: String,
    pub(crate) doi: Option<Doi>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Doi {
    pub(crate) identifier: String,
    pub(crate) url: String,
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub(crate) struct Scope {
    pub(crate) territory: Option<String>,
    pub(crate) dataset: Option<String>,
}

#[derive(Clone, Debug, Serialize)]
pub(crate) struct Function {
    pub(crate) name: String,
    pub(crate) status: String,
    pub(crate) public_api: PublicApi,
    pub(crate) scope: FunctionScope,
    pub(crate) inputs: Vec<Input>,
    pub(crate) outputs: Outputs,
    pub(crate) implementation: Option<Implementation>,
    #[serde(default)]
    pub(crate) golden_tests: Vec<GoldenTest>,
    #[serde(default)]
    pub(crate) documentation: Documentation,
}

impl Function {
    pub(crate) fn result_class(&self) -> Option<&str> {
        match &self.outputs {
            Outputs::Scalar { .. } => None,
            Outputs::Record { name, .. } => Some(name),
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct GoldenTest {
    pub(crate) id: String,
    pub(crate) inputs: BTreeMap<String, GoldenInput>,
    pub(crate) expected: BTreeMap<String, f64>,
    pub(crate) rtol: f64,
    pub(crate) atol: f64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub(crate) enum GoldenInput {
    Number(f64),
    Enum(String),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct PublicApi {
    pub(crate) name: String,
    pub(crate) result_class: Option<String>,
    pub(crate) summary: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct FunctionScope {
    pub(crate) territory: Option<String>,
    pub(crate) prediction_target: String,
    #[allow(dead_code)]
    #[serde(default)]
    pub(crate) models: Models,
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub(crate) struct Models {
    #[allow(dead_code)]
    pub(crate) h_theta: Option<String>,
    #[allow(dead_code)]
    pub(crate) k_h: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Parameter {
    pub(crate) name: String,
    pub(crate) unit: String,
    #[allow(dead_code)]
    pub(crate) domain: Option<String>,
    pub(crate) description: String,
}

#[derive(Clone, Debug, Serialize)]
#[serde(untagged)]
pub(crate) enum Input {
    Parameter(Parameter),
    Enum {
        name: String,
        description: Option<String>,
        #[serde(skip)]
        definition: EnumDefinition,
    },
}

impl Input {
    pub(crate) fn name(&self) -> &str {
        match self {
            Self::Parameter(parameter) => &parameter.name,
            Self::Enum { name, .. } => name,
        }
    }

    pub(crate) fn description(&self) -> &str {
        match self {
            Self::Parameter(parameter) => &parameter.description,
            Self::Enum { description, .. } => description.as_deref().unwrap_or_default(),
        }
    }

    pub(crate) fn unit(&self) -> Option<&str> {
        match self {
            Self::Parameter(parameter) => Some(&parameter.unit),
            Self::Enum { .. } => None,
        }
    }

    pub(crate) fn domain(&self) -> Option<&str> {
        match self {
            Self::Parameter(parameter) => parameter.domain.as_deref(),
            Self::Enum { .. } => None,
        }
    }

    pub(crate) fn enum_type(&self) -> Option<&EnumDefinition> {
        match self {
            Self::Parameter(_) => None,
            Self::Enum { definition, .. } => Some(definition),
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub(crate) struct EnumDefinition {
    #[serde(skip)]
    pub(crate) name: String,
    #[serde(rename = "type")]
    kind: EnumKind,
    pub(crate) description: String,
    pub(crate) values: Vec<EnumValue>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
enum EnumKind {
    Enum,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub(crate) struct EnumValue {
    pub(crate) name: String,
    pub(crate) value: String,
    pub(crate) description: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct LookupDefinition {
    #[serde(skip)]
    pub(crate) name: String,
    #[serde(rename = "type")]
    kind: LookupKind,
    pub(crate) input: Reference,
    pub(crate) output: Reference,
    pub(crate) values: Vec<LookupValue>,
    #[serde(skip)]
    pub(crate) input_type: Option<EnumDefinition>,
    #[serde(skip)]
    pub(crate) output_type: Option<Outputs>,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
enum LookupKind {
    Lookup,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct LookupValue {
    pub(crate) key: String,
    pub(crate) value: BTreeMap<String, f64>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub(crate) enum Outputs {
    Scalar {
        #[serde(flatten)]
        field: Parameter,
    },
    Record {
        name: String,
        fields: Vec<Parameter>,
    },
}

impl Outputs {
    pub(crate) fn fields(&self) -> &[Parameter] {
        match self {
            Self::Scalar { field } => std::slice::from_ref(field),
            Self::Record { fields, .. } => fields,
        }
    }
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub(crate) struct Documentation {
    #[serde(default)]
    pub(crate) notes: Vec<String>,
    #[serde(default)]
    pub(crate) warnings: Vec<String>,
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
pub(crate) enum PythonGeneration {
    #[default]
    Generated,
    Manual,
}

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
pub(crate) struct Generation {
    #[serde(default)]
    pub(crate) public_python: PythonGeneration,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Implementation {
    pub(crate) variables: Vec<ImplementationVariable>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub(crate) enum ImplementationVariable {
    Expression {
        name: String,
        expr: String,
    },
    Lookup {
        name: String,
        lookup: Box<LookupInvocation>,
    },
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct LookupInvocation {
    pub(crate) table: Reference,
    pub(crate) key: String,
    #[serde(skip)]
    pub(crate) definition: Option<LookupDefinition>,
}

#[derive(Clone, Debug)]
pub(crate) struct Entry {
    pub(crate) path: PathBuf,
    pub(crate) slug: String,
    pub(crate) spec: Spec,
    pub(crate) implementations: Vec<Option<crate::semantic::Function>>,
}

/// A validated source function paired with its immutable semantic IR.
#[derive(Clone, Debug)]
pub(crate) struct CompiledFunction {
    pub(crate) entry: Entry,
    pub(crate) function_index: usize,
    pub(crate) ir: crate::semantic::Function,
    pub(crate) core: CoreFunction,
    pub(crate) golden_tests: Vec<CompiledGoldenTest>,
}

#[derive(Clone, Debug)]
pub(crate) struct CompiledGoldenTest {
    pub(crate) id: String,
    pub(crate) inputs: Vec<CompiledInput>,
    pub(crate) expected: Vec<f64>,
    pub(crate) rtol: f64,
    pub(crate) atol: f64,
}

#[derive(Clone, Debug)]
pub(crate) enum CompiledInput {
    Number(f64),
    Enum {
        enum_name: String,
        member_name: String,
    },
}

#[derive(Clone, Debug)]
pub(crate) struct CoreFunction {
    pub(crate) name: String,
    pub(crate) inputs: Vec<String>,
    pub(crate) output: Output,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum Output {
    Scalar,
    Struct(Vec<String>),
}

/// Formula data passed from the YAML specification frontend to semantic validation.
#[derive(Clone, Debug)]
pub(crate) struct RawFunction {
    pub(crate) specification_path: PathBuf,
    pub(crate) name: String,
    pub(crate) inputs: Vec<RawInput>,
    pub(crate) variables: Vec<RawVariable>,
}

#[derive(Clone, Debug)]
pub(crate) struct RawInput {
    pub(crate) name: String,
    pub(crate) value_type: RawInputType,
}

#[derive(Clone, Debug)]
pub(crate) enum RawInputType {
    Number,
    Enum(EnumDefinition),
}

#[derive(Clone, Debug)]
pub(crate) struct RawVariable {
    pub(crate) name: String,
    pub(crate) value: RawVariableValue,
}

#[derive(Clone, Debug)]
pub(crate) enum RawVariableValue {
    Expression(RawExpression),
    Lookup(RawLookup),
}

#[derive(Clone, Debug)]
pub(crate) struct RawLookup {
    pub(crate) implementation_path: String,
    pub(crate) key: String,
    pub(crate) definition: LookupDefinition,
}

#[derive(Clone, Debug)]
pub(crate) struct RawExpression {
    pub(crate) implementation_path: String,
    pub(crate) source_location: SourceLocation,
    pub(crate) expression: crate::formula::Expr,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct SourceLocation {
    pub(crate) line: usize,
    pub(crate) column: usize,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn public_python_generation_defaults_to_generated() {
        let mut spec = Spec {
            source: Source {
                summary: "Test (2026), test territory.".into(),
                citation_apa: "Test (2026).".into(),
                doi: None,
            },
            scope: Scope::default(),
            generation: Generation::default(),
            functions: Vec::new(),
        };

        assert_eq!(spec.generation.public_python, PythonGeneration::Generated);

        spec.generation.public_python = PythonGeneration::Manual;
        assert_eq!(spec.generation.public_python, PythonGeneration::Manual);
    }

    #[test]
    fn resolves_named_enum_input_and_reusable_output() {
        let spec: Spec = serde_yaml::from_str(
            r##"
source:
  summary: Test source.
  citation_apa: Test (2026).
  doi: null
$defs:
  TestCategory:
    type: enum
    description: Test category type.
    values:
    - name: first
      value: first
  reusable_result:
    type: record
    name: TestResult
    fields:
    - name: value
      symbol: y
      unit: '1'
      domain: null
      description: Test output.
functions:
- name: calc_ptf_test
  status: ready-for-implementation
  public_api:
    name: calc_ptf_test
    summary: Test result.
  scope:
    prediction_target: Test result.
    models: {h_theta: null, k_h: null}
  inputs:
  - $ref: "#/$defs/TestCategory"
    name: x
    description: Test input category.
  outputs:
    $ref: "#/$defs/reusable_result"
"##,
        )
        .expect("reusable schemas deserialize");

        let function = &spec.functions[0];
        assert_eq!(function.inputs[0].name(), "x");
        assert_eq!(function.inputs[0].description(), "Test input category.");
        assert_eq!(
            function.inputs[0]
                .enum_type()
                .expect("enum input is resolved")
                .name,
            "TestCategory"
        );
        assert_eq!(function.outputs.fields()[0].name, "value");
        assert_eq!(function.result_class(), Some("TestResult"));
    }

    #[test]
    fn does_not_use_an_enum_type_description_for_an_undocumented_binding() {
        let input = Input::Enum {
            name: "topsoil_texture".into(),
            description: None,
            definition: EnumDefinition {
                name: "TestCategory".into(),
                kind: EnumKind::Enum,
                description: "Test category type.".into(),
                values: Vec::new(),
            },
        };

        assert_eq!(input.description(), "");
        assert_eq!(
            input
                .enum_type()
                .expect("enum input retains its type")
                .description,
            "Test category type."
        );
    }
}
