//! Resolve dense ensembles and their summaries in the ordinary implementation scope.
use super::*;
use crate::model::{DenseEnsembleDefinition, NeuralComparison, NeuralVariable, RawNeuralVariable};

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct EnsembleType {
    pub(crate) members: usize,
    pub(crate) fields: Vec<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Condition {
    pub(crate) left: Expr,
    pub(crate) op: NeuralComparison,
    pub(crate) right: Expr,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum Operation {
    Network {
        definition: DenseEnsembleDefinition,
        arguments: Vec<Expr>,
        when: Vec<Condition>,
    },
    Transform {
        source: Reference,
        ensemble: EnsembleType,
        expressions: Vec<Expr>,
    },
    Statistics {
        source: Reference,
        ensemble: EnsembleType,
        output: RecordType,
    },
    Estimate {
        arithmetic: Expr,
        log10: Expr,
        geometric: Expr,
    },
    Require(Vec<Condition>),
}

#[derive(Clone, Debug, Eq, PartialEq, thiserror::Error)]
pub(crate) enum NeuralErrorKind {
    #[error("unknown dense ensemble definition `{name}`")]
    UnknownNetwork { name: String },
    #[error("invalid architecture, channels, scaling, or parameter reference for `{name}`")]
    Definition { name: String },
    #[error("network expects {expected} arguments, found {actual}")]
    Arguments { expected: usize, actual: usize },
    #[error("`{name}` is not an earlier ensemble variable")]
    EnsembleRequired { name: String },
    #[error("unknown ensemble field `{name}`")]
    Field { name: String },
    #[error("sample statistics require ddof=1 and at least two members")]
    Statistics,
    #[error(transparent)]
    Expression(#[from] formula::ParseError),
}

pub(super) fn compile(
    raw: &RawFunction,
    invocation: &RawNeuralVariable,
    scope: &BTreeMap<String, Binding>,
    variable_names: &BTreeMap<&str, usize>,
    index: usize,
) -> Result<(Operation, ValueType), Box<Error>> {
    let error = |kind| {
        Error::in_function(
            raw,
            &invocation.implementation_path,
            Span { start: 0, end: 0 },
            SemanticErrorKind::Neural(kind),
        )
    };
    let expression = |source: &str, suffix: &str| {
        let path = format!("{}.{}", invocation.implementation_path, suffix);
        let parsed =
            formula::parse(&path, source).map_err(|e| error(NeuralErrorKind::Expression(e)))?;
        super::compile_expression(
            raw,
            &RawExpression {
                implementation_path: path,
                source_location: SourceLocation { line: 1, column: 1 },
                expression: parsed,
            },
            scope,
            variable_names,
            index,
        )
    };
    let conditions =
        |conditions: &[crate::model::NeuralCondition]| -> Result<Vec<Condition>, Box<Error>> {
            conditions
                .iter()
                .enumerate()
                .map(|(i, c)| {
                    Ok(Condition {
                        left: expression(&c.left, &format!("conditions[{i}].left"))?,
                        op: c.op,
                        right: expression(&c.right, &format!("conditions[{i}].right"))?,
                    })
                })
                .collect()
        };
    let ensemble = |name: &str| match scope.get(name) {
        Some(Binding {
            reference: Reference::Variable(_),
            value_type: ValueType::Ensemble(ensemble),
        }) => Ok((scope[name].reference, ensemble.clone())),
        _ => Err(error(NeuralErrorKind::EnsembleRequired {
            name: name.into(),
        })),
    };
    match &invocation.operation {
        NeuralVariable::Network { network } => {
            let definition = invocation
                .networks
                .get(&network.definition)
                .ok_or_else(|| {
                    error(NeuralErrorKind::UnknownNetwork {
                        name: network.definition.clone(),
                    })
                })?;
            validate_definition(definition).map_err(|_| {
                error(NeuralErrorKind::Definition {
                    name: network.definition.clone(),
                })
            })?;
            if network.arguments.len() != definition.inputs.len() {
                return Err(error(NeuralErrorKind::Arguments {
                    expected: definition.inputs.len(),
                    actual: network.arguments.len(),
                }));
            }
            let arguments = network
                .arguments
                .iter()
                .enumerate()
                .map(|(i, a)| expression(a, &format!("network.arguments[{i}]")))
                .collect::<Result<Vec<_>, _>>()?;
            Ok((
                Operation::Network {
                    definition: definition.clone(),
                    arguments,
                    when: conditions(&network.when)?,
                },
                ValueType::Ensemble(EnsembleType {
                    members: definition.members,
                    fields: definition.outputs.iter().map(|c| c.name.clone()).collect(),
                }),
            ))
        }
        NeuralVariable::Transform {
            ensemble_transform: transform,
        } => {
            let (source, ensemble) = ensemble(&transform.source)?;
            for field in transform.fields.keys() {
                if !ensemble.fields.contains(field) {
                    return Err(error(NeuralErrorKind::Field {
                        name: field.clone(),
                    }));
                }
            }
            // Member expressions use the existing parser/resolver over named numeric channels.
            let member = RawFunction {
                specification_path: raw.specification_path.clone(),
                name: raw.name.clone(),
                inputs: ensemble
                    .fields
                    .iter()
                    .map(|name| crate::model::RawInput {
                        name: name.clone(),
                        value_type: crate::model::RawInputType::Number,
                    })
                    .collect(),
                variables: ensemble
                    .fields
                    .iter()
                    .map(|field| {
                        let path = format!(
                            "{}.ensemble_transform.fields.{field}",
                            invocation.implementation_path
                        );
                        let parsed =
                            formula::parse(&path, transform.fields.get(field).unwrap_or(field))
                                .map_err(|e| error(NeuralErrorKind::Expression(e)))?;
                        Ok(crate::model::RawVariable {
                            name: format!("transformed_{field}"),
                            value: RawVariableValue::Expression(RawExpression {
                                implementation_path: path,
                                source_location: SourceLocation { line: 1, column: 1 },
                                expression: parsed,
                            }),
                        })
                    })
                    .collect::<Result<Vec<_>, Box<Error>>>()?,
            };
            let expressions = member
                .variables
                .iter()
                .map(|variable| {
                    let single = RawFunction {
                        specification_path: member.specification_path.clone(),
                        name: member.name.clone(),
                        inputs: member.inputs.clone(),
                        variables: vec![variable.clone()],
                    };
                    let compiled = super::compile(&single)?;
                    match compiled.variables.into_iter().next().unwrap().value {
                        VariableValue::Expression(e) => Ok(e),
                        _ => unreachable!(),
                    }
                })
                .collect::<Result<Vec<_>, Box<Error>>>()?;
            Ok((
                Operation::Transform {
                    source,
                    ensemble: ensemble.clone(),
                    expressions,
                },
                ValueType::Ensemble(ensemble),
            ))
        }
        NeuralVariable::Statistics {
            ensemble_statistics: statistics,
        } => {
            let (source, ensemble) = ensemble(&statistics.source)?;
            if statistics.ddof != 1 || ensemble.members < 2 {
                return Err(error(NeuralErrorKind::Statistics));
            }
            let output = RecordType {
                name: format!("NeuralStatistics{index}"),
                fields: ["mean", "std"]
                    .into_iter()
                    .flat_map(|stat| ensemble.fields.iter().map(move |f| format!("{f}_{stat}")))
                    .collect(),
            };
            Ok((
                Operation::Statistics {
                    source,
                    ensemble,
                    output: output.clone(),
                },
                ValueType::Record(output),
            ))
        }
        NeuralVariable::Estimate { estimate } => Ok((
            Operation::Estimate {
                arithmetic: expression(&estimate.arithmetic, "estimate.arithmetic")?,
                log10: expression(&estimate.log10, "estimate.log10")?,
                geometric: expression(&estimate.geometric, "estimate.geometric")?,
            },
            ValueType::Number,
        )),
        NeuralVariable::Require { require } => {
            Ok((Operation::Require(conditions(require)?), ValueType::Effect))
        }
    }
}

pub(crate) fn validate_definition(d: &DenseEnsembleDefinition) -> Result<(), NeuralErrorKind> {
    let valid = (2..=1000).contains(&d.members)
        && (2..=17).contains(&d.widths.len())
        && d.widths.iter().all(|w| (1..=64).contains(w))
        && d.activations.len() + 1 == d.widths.len()
        && d.inputs.len() == d.widths[0]
        && d.outputs.len() == *d.widths.last().unwrap()
        && d.activations
            .iter()
            .all(|a| matches!(a.as_str(), "linear" | "sigmoid" | "tansig" | "relu"))
        && !d.parameters.artifact.path.is_empty();
    let channels_valid = |channels: &[crate::model::NeuralChannel]| {
        let mut names = std::collections::BTreeSet::new();
        channels.iter().all(|c| {
            let count = match c.scale.as_str() {
                "asis" => 0,
                "division" => 1,
                "logtr" | "affine" | "linear" => 2,
                "minmax" => 3,
                _ => return false,
            };
            !c.name.is_empty()
                && c.name
                    .bytes()
                    .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'_')
                && names.insert(&c.name)
                && c.params.len() == count
                && c.params.iter().all(|v| v.is_finite())
                && (!matches!(c.scale.as_str(), "division" | "logtr") || c.params[0] != 0.0)
        })
    };
    if valid && channels_valid(&d.inputs) && channels_valid(&d.outputs) {
        Ok(())
    } else {
        Err(NeuralErrorKind::Definition {
            name: String::new(),
        })
    }
}
