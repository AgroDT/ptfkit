use std::path::PathBuf;

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Spec {
    pub(crate) source: Source,
    #[serde(default)]
    pub(crate) scope: Scope,
    #[serde(default)]
    pub(crate) python_generation: PythonGeneration,
    pub(crate) functions: Vec<Function>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct Source {
    pub(crate) key: String,
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
    #[serde(default)]
    pub(crate) documentation: Documentation,
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

#[derive(Clone)]
pub(crate) struct Entry {
    pub(crate) path: PathBuf,
    pub(crate) spec: Spec,
    pub(crate) section_functions: Vec<String>,
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

/// Formula data before semantic validation. This deliberately remains separate
/// from the versioned specification model until the frontend is wired to YAML.
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
    reason = "Session 04 constructs raw scalar and record outputs from the versioned specification loader."
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
    fn python_generation_defaults_to_generated() {
        let mut spec = Spec {
            source: Source {
                key: "test".into(),
                summary: "Test (2026), test territory.".into(),
                citation_apa: "Test (2026).".into(),
                doi: None,
            },
            scope: Scope::default(),
            python_generation: PythonGeneration::Generated,
            functions: Vec::new(),
        };

        assert_eq!(spec.python_generation, PythonGeneration::Generated);

        spec.python_generation = PythonGeneration::Manual;
        assert_eq!(spec.python_generation, PythonGeneration::Manual);
    }
}

#[derive(Clone)]
pub(crate) struct Resolved {
    pub(crate) entry: Entry,
    pub(crate) function_index: usize,
    pub(crate) core: CoreFunction,
}
