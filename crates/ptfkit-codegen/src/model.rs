use std::collections::BTreeMap;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Spec {
    pub(crate) source: Source,
    #[serde(default)]
    pub(crate) scope: Scope,
    #[serde(default)]
    pub(crate) generation: Generation,
    pub(crate) functions: Vec<Function>,
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
    pub(crate) outputs: Vec<Parameter>,
    pub(crate) implementation: Option<Implementation>,
    #[serde(default)]
    pub(crate) golden_tests: Vec<GoldenTest>,
    #[serde(default)]
    pub(crate) documentation: Documentation,
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
    pub(crate) output: ImplementationOutput,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct ImplementationVariable {
    pub(crate) name: String,
    pub(crate) expr: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub(crate) enum ImplementationOutput {
    Scalar { expr: String },
    Record { fields: Vec<ImplementationField> },
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct ImplementationField {
    pub(crate) name: String,
    pub(crate) expr: String,
}

#[derive(Clone)]
pub(crate) struct Entry {
    pub(crate) path: PathBuf,
    pub(crate) slug: String,
    pub(crate) spec: Spec,
    #[allow(
        dead_code,
        reason = "Session 05 will make the compiled frontend IR the Rust target input."
    )]
    pub(crate) implementations: Vec<Option<crate::semantic::Function>>,
}

#[derive(Clone)]
pub(crate) struct CoreFunction {
    pub(crate) name: String,
    pub(crate) module: Vec<String>,
    pub(crate) inputs: Vec<String>,
    pub(crate) output: Output,
}

#[derive(Clone)]
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
    pub(crate) output: RawOutput,
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

#[allow(
    dead_code,
    reason = "Session 04 constructs raw scalar and record outputs from the YAML specification loader."
)]
#[derive(Clone, Debug)]
pub(crate) enum RawOutput {
    Scalar(RawExpression),
    Record(Vec<RawField>),
}

#[derive(Clone, Debug)]
pub(crate) struct RawField {
    pub(crate) name: String,
    pub(crate) expression: RawExpression,
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
}

#[derive(Clone)]
pub(crate) struct Resolved {
    pub(crate) entry: Entry,
    pub(crate) function_index: usize,
    pub(crate) core: CoreFunction,
}
