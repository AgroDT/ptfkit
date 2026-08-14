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
    Input(Parameter),
    Output(Outputs),
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
    Inline(Parameter),
    Reference(Reference),
}

#[derive(Clone, Debug, Deserialize)]
#[serde(untagged)]
enum OutputReference {
    Inline(Outputs),
    Reference(Reference),
}

#[derive(Clone, Debug, Deserialize)]
struct Reference {
    #[serde(rename = "$ref")]
    target: String,
}

impl<'de> Deserialize<'de> for Spec {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        let raw = RawSpec::deserialize(deserializer)?;
        let functions = raw
            .functions
            .into_iter()
            .map(|function| {
                let inputs = function
                    .inputs
                    .into_iter()
                    .map(|input| match input {
                        InputReference::Inline(input) => Ok(input),
                        InputReference::Reference(reference) => {
                            let name = definition_name(&reference.target)?;
                            match raw.definitions.get(name) {
                                Some(Definition::Input(input)) => Ok(input.clone()),
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
                let (outputs, output_schema) = match function.outputs {
                    OutputReference::Inline(outputs) => Ok((outputs, None)),
                    OutputReference::Reference(reference) => {
                        let name = definition_name(&reference.target)?;
                        match raw.definitions.get(name) {
                            Some(Definition::Input(_)) => Err(format!(
                                "function {} references input definition `{name}` as an output",
                                function.name
                            )),
                            Some(Definition::Output(outputs)) => Ok((
                                outputs.clone().with_record_name(name),
                                Some(name.to_owned()),
                            )),
                            None => Err(format!(
                                "function {} references unknown definition `{name}`",
                                function.name
                            )),
                        }
                    }
                }?;
                Ok(Function {
                    name: function.name,
                    status: function.status,
                    public_api: function.public_api,
                    scope: function.scope,
                    inputs,
                    outputs,
                    output_schema,
                    implementation: function.implementation,
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

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Function {
    pub(crate) name: String,
    pub(crate) status: String,
    pub(crate) public_api: PublicApi,
    pub(crate) scope: FunctionScope,
    pub(crate) inputs: Vec<Parameter>,
    pub(crate) outputs: Outputs,
    #[serde(skip)]
    pub(crate) output_schema: Option<String>,
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
            Outputs::Record { name, .. } => {
                name.as_deref().or(self.public_api.result_class.as_deref())
            }
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct GoldenTest {
    pub(crate) id: String,
    pub(crate) inputs: BTreeMap<String, f64>,
    pub(crate) expected: BTreeMap<String, f64>,
    pub(crate) rtol: f64,
    pub(crate) atol: f64,
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

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub(crate) enum Outputs {
    Scalar {
        #[serde(flatten)]
        field: Parameter,
    },
    Record {
        #[serde(default)]
        name: Option<String>,
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

    fn with_record_name(mut self, name: &str) -> Self {
        if let Self::Record {
            name: record_name, ..
        } = &mut self
        {
            *record_name = Some(name.to_owned());
        }
        self
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
    #[serde(default)]
    pub(crate) variables: Vec<ImplementationVariable>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct ImplementationVariable {
    pub(crate) name: String,
    pub(crate) expr: String,
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
    pub(crate) inputs: Vec<f64>,
    pub(crate) expected: Vec<f64>,
    pub(crate) rtol: f64,
    pub(crate) atol: f64,
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
}

#[derive(Clone, Debug)]
pub(crate) struct RawVariable {
    pub(crate) name: String,
    pub(crate) expression: RawExpression,
}

#[derive(Clone, Debug)]
pub(crate) struct RawExpression {
    pub(crate) implementation_path: String,
    pub(crate) expression: crate::formula::Expr,
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
    fn resolves_reusable_input_and_output_schemas() {
        let spec: Spec = serde_yaml::from_str(
            r##"
source:
  summary: Test source.
  citation_apa: Test (2026).
  doi: null
$defs:
  x:
    name: x
    symbol: x
    unit: '1'
    domain: null
    description: Test input.
  TestResult:
    type: record
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
  - $ref: "#/$defs/x"
  outputs:
    $ref: "#/$defs/TestResult"
"##,
        )
        .expect("reusable schemas deserialize");

        let function = &spec.functions[0];
        assert_eq!(function.inputs[0].name, "x");
        assert_eq!(function.outputs.fields()[0].name, "value");
        assert_eq!(function.result_class(), Some("TestResult"));
        assert_eq!(function.output_schema.as_deref(), Some("TestResult"));
    }
}
