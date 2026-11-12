//! Specification types for the dense ensembles used by neural PTFs.
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub(crate) struct DenseEnsembleDefinition {
    pub(crate) parameters: NeuralParameters,
    pub(crate) members: usize,
    pub(crate) widths: Vec<usize>,
    pub(crate) activations: Vec<String>,
    pub(crate) inputs: Vec<NeuralChannel>,
    pub(crate) outputs: Vec<NeuralChannel>,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub(crate) struct NeuralParameters {
    pub(crate) artifact: NeuralArtifact,
    pub(crate) network: usize,
    pub(crate) offset: usize,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub(crate) struct NeuralChannel {
    pub(crate) name: String,
    pub(crate) scale: String,
    pub(crate) params: Vec<f64>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(untagged, deny_unknown_fields)]
pub(crate) enum NeuralVariable {
    Network {
        network: NetworkInvocation,
    },
    Transform {
        ensemble_transform: EnsembleTransform,
    },
    Statistics {
        ensemble_statistics: EnsembleStatistics,
    },
    Estimate {
        estimate: EstimateExpressions,
    },
    Require {
        require: Vec<NeuralCondition>,
    },
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct NetworkInvocation {
    pub(crate) definition: String,
    pub(crate) arguments: Vec<String>,
    #[serde(default)]
    pub(crate) when: Vec<NeuralCondition>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct EnsembleTransform {
    pub(crate) source: String,
    pub(crate) fields: BTreeMap<String, String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct EnsembleStatistics {
    pub(crate) source: String,
    pub(crate) ddof: usize,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct EstimateExpressions {
    pub(crate) arithmetic: String,
    pub(crate) log10: String,
    pub(crate) geometric: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct NeuralCondition {
    pub(crate) left: String,
    pub(crate) op: NeuralComparison,
    pub(crate) right: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub(crate) enum NeuralComparison {
    Lt,
    Le,
    Gt,
    Ge,
}

#[derive(Clone, Debug)]
pub(crate) struct RawNeuralVariable {
    pub(crate) implementation_path: String,
    pub(crate) operation: NeuralVariable,
    pub(crate) networks: BTreeMap<String, DenseEnsembleDefinition>,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub(crate) struct NeuralArtifact {
    pub(crate) path: String,
    pub(crate) sha256: String,
    pub(crate) bytes: usize,
    pub(crate) license: String,
}
