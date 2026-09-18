mod error;
pub(crate) use error::DefinitionError;
use error::{TreeError, TreeErrorKind};

use std::{
    collections::BTreeMap,
    path::{Path, PathBuf},
    sync::Arc,
};

use serde::{
    Deserialize, Deserializer, Serialize,
    de::{Error as _, MapAccess, Visitor},
};

#[derive(Clone, Debug, Serialize)]
pub(crate) struct Spec {
    pub(crate) source: Source,
    #[serde(default)]
    pub(crate) scope: Scope,
    #[serde(default)]
    pub(crate) generation: Generation,
    #[serde(default)]
    pub(crate) scientific_notes: String,
    pub(crate) functions: Vec<Function>,
}

#[derive(Deserialize)]
struct RawSpec {
    source: Source,
    #[serde(default)]
    scope: Scope,
    #[serde(default)]
    generation: Generation,
    #[serde(default)]
    scientific_notes: String,
    #[serde(default, rename = "$defs")]
    definitions: BTreeMap<String, Definition>,
    functions: Vec<FunctionReference>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(untagged)]
enum Definition {
    Enum(EnumDefinition),
    Lookup(Box<LookupDefinition>),
    Tree(Box<TreeDefinition>),
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
    #[serde(default)]
    verification_tolerances: BTreeMap<String, VerificationToleranceOverride>,
    implementation: Option<Implementation>,
    #[serde(default)]
    verification_cases: Vec<VerificationCase>,
    #[serde(default)]
    edge_cases: Vec<serde_json::Value>,
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
        let tree_definitions = raw
            .definitions
            .iter()
            .filter_map(|(name, definition)| match definition {
                Definition::Tree(definition) => Some(
                    resolve_tree_definition(name, definition, &raw.definitions)
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
                        InputReference::Type(reference) => {
                            resolve_input_type(reference, &raw.definitions, &function.name)
                        }
                        InputReference::Reference(reference) => {
                            let name = definition_name(&reference.target)?;
                            match raw.definitions.get(name) {
                                Some(Definition::Parameter(parameter)) => {
                                    Ok(Input::Parameter(parameter.clone()))
                                }
                                Some(Definition::Enum(_))
                                | Some(Definition::Lookup(_))
                                | Some(Definition::Tree(_)) => {
                                    Err(DefinitionError::MissingInputBinding {
                                        function: function.name.clone(),
                                        name: name.to_owned(),
                                    })
                                }
                                Some(Definition::Output(_)) => {
                                    Err(DefinitionError::OutputAsInput {
                                        function: function.name.clone(),
                                        name: name.to_owned(),
                                    })
                                }
                                None => Err(DefinitionError::UnknownDefinition {
                                    function: function.name.clone(),
                                    name: name.to_owned(),
                                }),
                            }
                        }
                    })
                    .collect::<Result<Vec<_>, _>>()?;
                let outputs = match function.outputs {
                    OutputReference::Inline(outputs) => Ok(outputs),
                    OutputReference::Reference(reference) => {
                        let name = definition_name(&reference.target)?;
                        match raw.definitions.get(name) {
                            Some(Definition::Enum(_))
                            | Some(Definition::Lookup(_))
                            | Some(Definition::Tree(_)) => {
                                Err(DefinitionError::NonOutputAsOutput {
                                    function: function.name.clone(),
                                    name: name.to_owned(),
                                })
                            }
                            Some(Definition::Parameter(_)) => {
                                Err(DefinitionError::ParameterAsOutput {
                                    function: function.name.clone(),
                                    name: name.to_owned(),
                                })
                            }
                            Some(Definition::Output(outputs)) => Ok(outputs.clone()),
                            None => Err(DefinitionError::UnknownDefinition {
                                function: function.name.clone(),
                                name: name.to_owned(),
                            }),
                        }
                    }
                }?;
                let implementation = function
                    .implementation
                    .map(|mut implementation| {
                        for variable in &mut implementation.variables {
                            match variable {
                                ImplementationVariable::Lookup { lookup, .. } => {
                                    let name = definition_name(&lookup.table.target)?;
                                    lookup.definition =
                                        Some(lookup_definitions.get(name).cloned().ok_or_else(
                                            || DefinitionError::UnknownLookup {
                                                function: function.name.clone(),
                                                name: name.to_owned(),
                                            },
                                        )?);
                                }
                                ImplementationVariable::Tree { tree, .. } => {
                                    let name = definition_name(&tree.definition_ref.target)?;
                                    tree.definition =
                                        Some(tree_definitions.get(name).cloned().ok_or_else(
                                            || DefinitionError::UnknownTree {
                                                function: function.name.clone(),
                                                name: name.to_owned(),
                                            },
                                        )?);
                                }
                                ImplementationVariable::Expression { .. } => {}
                            }
                        }
                        Ok::<_, DefinitionError>(implementation)
                    })
                    .transpose()?;
                Ok(Function {
                    name: function.name,
                    status: function.status,
                    public_api: function.public_api,
                    scope: function.scope,
                    inputs,
                    outputs,
                    verification_tolerances: function.verification_tolerances,
                    implementation,
                    verification_cases: function.verification_cases,
                    edge_cases: function.edge_cases,
                    documentation: function.documentation,
                })
            })
            .collect::<Result<Vec<_>, DefinitionError>>()
            .map_err(serde::de::Error::custom)?;
        Ok(Self {
            source: raw.source,
            scope: raw.scope,
            generation: raw.generation,
            scientific_notes: raw.scientific_notes,
            functions,
        })
    }
}

fn resolve_input_type(
    input: NamedReference,
    definitions: &BTreeMap<String, Definition>,
    function: &str,
) -> Result<Input, DefinitionError> {
    let type_name = definition_name(&input.reference.target)?;
    match definitions.get(type_name) {
        Some(Definition::Enum(definition)) => Ok(Input::Enum {
            name: input.name,
            description: input.description,
            definition: resolved_enum_definition(definition, type_name),
        }),
        Some(Definition::Output(_))
        | Some(Definition::Lookup(_))
        | Some(Definition::Tree(_))
        | Some(Definition::Parameter(_)) => Err(DefinitionError::NonEnumInput {
            function: function.to_owned(),
            input: input.name,
            type_name: type_name.to_owned(),
        }),
        None => Err(DefinitionError::UnknownInputEnum {
            function: function.to_owned(),
            input: input.name,
            type_name: type_name.to_owned(),
        }),
    }
}

fn resolved_enum_definition(definition: &EnumDefinition, reference_name: &str) -> EnumDefinition {
    let mut definition = definition.clone();
    definition.enum_type.name = reference_name.to_owned();
    definition
}

fn resolve_lookup_definition(
    name: &str,
    definition: &LookupDefinition,
    definitions: &BTreeMap<String, Definition>,
) -> Result<LookupDefinition, DefinitionError> {
    let input_name = definition_name(&definition.input.target)?;
    let input_type = match definitions.get(input_name) {
        Some(Definition::Enum(definition)) => resolved_enum_definition(definition, input_name),
        Some(_) => {
            return Err(DefinitionError::InputDefinitionType {
                name: name.to_owned(),
            });
        }
        None => {
            return Err(DefinitionError::UnknownInputType {
                name: name.to_owned(),
                input_name: input_name.to_owned(),
            });
        }
    };
    let output_name = definition_name(&definition.output.target)?;
    let output_type = match definitions.get(output_name) {
        Some(Definition::Output(output @ Outputs::Record { .. })) => output.clone(),
        Some(_) => {
            return Err(DefinitionError::OutputDefinitionType {
                name: name.to_owned(),
            });
        }
        None => {
            return Err(DefinitionError::UnknownOutputType {
                name: name.to_owned(),
                output_name: output_name.to_owned(),
            });
        }
    };
    let mut resolved = definition.clone();
    resolved.name = name.to_owned();
    resolved.input_type = Some(input_type);
    resolved.output_type = Some(output_type);
    validate_lookup_values(&resolved)?;
    Ok(resolved)
}

fn validate_lookup_values(lookup: &LookupDefinition) -> Result<(), DefinitionError> {
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
            return Err(DefinitionError::DuplicateLookupKey {
                name: lookup.name.clone(),
                key: row.key.clone(),
                index,
            });
        }
        if !enum_type.values.iter().any(|member| member.name == row.key) {
            return Err(DefinitionError::UnknownLookupMember {
                name: lookup.name.clone(),
                key: row.key.clone(),
                index,
            });
        }
        let row_names = row
            .value
            .keys()
            .map(String::as_str)
            .collect::<std::collections::BTreeSet<_>>();
        if row_names != output_names {
            return Err(DefinitionError::LookupFields {
                name: lookup.name.clone(),
                index,
            });
        }
    }
    let enum_members = enum_type
        .values
        .iter()
        .map(|member| member.name.as_str())
        .collect::<std::collections::BTreeSet<_>>();
    if keys != enum_members {
        return Err(DefinitionError::LookupCoverage {
            name: lookup.name.clone(),
            enum_name: enum_type.enum_type.name.clone(),
        });
    }
    Ok(())
}

fn resolve_tree_definition(
    name: &str,
    definition: &TreeDefinition,
    definitions: &BTreeMap<String, Definition>,
) -> Result<TreeDefinition, DefinitionError> {
    let mut resolved = definition.clone();
    resolved.name = name.to_owned();
    let mut input_names = std::collections::BTreeSet::new();
    for input in &mut resolved.inputs {
        if !input_names.insert(input.name().to_owned()) {
            return Err(TreeError::definition(
                name,
                "inputs",
                TreeErrorKind::DuplicateInput(input.name().to_owned()),
            ));
        }
        if let TreeInput::Enum(input) = input {
            let type_name = definition_name(&input.reference.target)?;
            input.definition = Some(match definitions.get(type_name) {
                Some(Definition::Enum(definition)) => {
                    resolved_enum_definition(definition, type_name)
                }
                Some(_) => {
                    return Err(TreeError::definition(
                        name,
                        "inputs",
                        TreeErrorKind::InputNotEnum(input.name.clone()),
                    ));
                }
                None => {
                    return Err(TreeError::definition(
                        name,
                        "inputs",
                        TreeErrorKind::UnknownInputEnum {
                            input: input.name.clone(),
                            type_name: type_name.to_owned(),
                        },
                    ));
                }
            });
        }
    }
    let output_name = definition_name(&resolved.output.target)?;
    resolved.output_type = Some(match definitions.get(output_name) {
        Some(Definition::Output(output)) => output.clone(),
        Some(_) => {
            return Err(TreeError::definition(
                name,
                "output",
                TreeErrorKind::OutputNotOutput,
            ));
        }
        None => {
            return Err(TreeError::definition(
                name,
                "output",
                TreeErrorKind::UnknownOutputType(output_name.to_owned()),
            ));
        }
    });
    validate_tree_definition(&resolved)?;
    Ok(resolved)
}

fn validate_tree_definition(definition: &TreeDefinition) -> Result<(), DefinitionError> {
    fn validate_node(
        definition: &TreeDefinition,
        node: &DecisionTree,
        path: &str,
    ) -> Result<(), DefinitionError> {
        match node {
            DecisionTree::Leaf(leaf) => {
                let output = definition
                    .output_type
                    .as_ref()
                    .expect("tree output is resolved");
                match (output, &leaf.leaf) {
                    (Outputs::Scalar { .. }, DecisionTreeLeafValue::Number(number)) => {
                        validate_tree_number(definition, path, number)
                    }
                    (Outputs::Scalar { .. }, DecisionTreeLeafValue::Record(_)) => {
                        Err(TreeError::definition(
                            &definition.name,
                            path,
                            TreeErrorKind::NumericLeafRequired,
                        ))
                    }
                    (Outputs::Record { fields, .. }, DecisionTreeLeafValue::Record(values)) => {
                        let expected = fields
                            .iter()
                            .map(|field| field.name.as_str())
                            .collect::<std::collections::BTreeSet<_>>();
                        let actual = values
                            .keys()
                            .map(String::as_str)
                            .collect::<std::collections::BTreeSet<_>>();
                        if actual != expected {
                            return Err(TreeError::definition(
                                &definition.name,
                                path,
                                TreeErrorKind::RecordFields,
                            ));
                        }
                        for number in values.values() {
                            validate_tree_number(definition, path, number)?;
                        }
                        Ok(())
                    }
                    (Outputs::Record { .. }, DecisionTreeLeafValue::Number(_)) => {
                        Err(TreeError::definition(
                            &definition.name,
                            path,
                            TreeErrorKind::RecordLeafRequired,
                        ))
                    }
                }
            }
            DecisionTree::Split(branch) => {
                match &branch.split {
                    DecisionTreeSplit::LessThan(split) => {
                        let input = tree_input(definition, &split.input, path)?;
                        if !matches!(input, TreeInput::Number { .. }) {
                            return Err(TreeError::definition(
                                &definition.name,
                                path,
                                TreeErrorKind::NumericInputRequired(split.input.clone()),
                            ));
                        }
                        validate_tree_number(definition, path, &split.value)?;
                    }
                    DecisionTreeSplit::EnumIn(split) => {
                        let input = tree_input(definition, &split.input, path)?;
                        let TreeInput::Enum(input) = input else {
                            return Err(TreeError::definition(
                                &definition.name,
                                path,
                                TreeErrorKind::EnumInputRequired(split.input.clone()),
                            ));
                        };
                        validate_tree_members(definition, input, &split.values, path)?;
                    }
                }
                validate_node(definition, &branch.yes, &format!("{path}.yes"))?;
                validate_node(definition, &branch.no, &format!("{path}.no"))
            }
            DecisionTree::Match(selection) => {
                let input = tree_input(definition, &selection.match_node.input, path)?;
                let TreeInput::Enum(input) = input else {
                    return Err(TreeError::definition(
                        &definition.name,
                        path,
                        TreeErrorKind::MatchInputNotEnum(selection.match_node.input.clone()),
                    ));
                };
                let enum_definition = input.definition.as_ref().expect("tree enum is resolved");
                let mut covered = std::collections::BTreeSet::new();
                for (index, case) in selection.match_node.cases.iter().enumerate() {
                    validate_tree_members(
                        definition,
                        input,
                        &case.values,
                        &format!("{path}.match.cases[{index}]"),
                    )?;
                    for member in &case.values {
                        if !covered.insert(member.as_str()) {
                            return Err(TreeError::definition(
                                &definition.name,
                                path,
                                TreeErrorKind::OverlappingMember(member.clone()),
                            ));
                        }
                    }
                    validate_node(
                        definition,
                        &case.then,
                        &format!("{path}.match.cases[{index}].then"),
                    )?;
                }
                let expected = enum_definition
                    .values
                    .iter()
                    .map(|member| member.name.as_str())
                    .collect::<std::collections::BTreeSet<_>>();
                if covered != expected {
                    return Err(TreeError::definition(
                        &definition.name,
                        path,
                        TreeErrorKind::IncompleteMatch(enum_definition.enum_type.name.clone()),
                    ));
                }
                Ok(())
            }
        }
    }

    validate_node(definition, &definition.root, "root")
}

fn tree_input<'a>(
    definition: &'a TreeDefinition,
    name: &str,
    path: &str,
) -> Result<&'a TreeInput, DefinitionError> {
    definition
        .inputs
        .iter()
        .find(|input| input.name() == name)
        .ok_or_else(|| {
            TreeError::definition(
                &definition.name,
                path,
                TreeErrorKind::UnknownInput(name.to_owned()),
            )
        })
}

fn validate_tree_members(
    tree: &TreeDefinition,
    input: &TreeEnumInput,
    members: &[String],
    path: &str,
) -> Result<(), DefinitionError> {
    if members.is_empty() {
        return Err(TreeError::definition(
            &tree.name,
            path,
            TreeErrorKind::EmptyMembers,
        ));
    }
    let definition = input.definition.as_ref().expect("tree enum is resolved");
    let mut seen = std::collections::BTreeSet::new();
    for member in members {
        if !seen.insert(member) {
            return Err(TreeError::definition(
                &tree.name,
                path,
                TreeErrorKind::DuplicateMember(member.clone()),
            ));
        }
        if !definition.values.iter().any(|value| value.name == *member) {
            return Err(TreeError::definition(
                &tree.name,
                path,
                TreeErrorKind::UnknownMember {
                    member: member.clone(),
                    enum_name: definition.enum_type.name.clone(),
                },
            ));
        }
    }
    Ok(())
}

fn validate_tree_number(
    definition: &TreeDefinition,
    path: &str,
    number: &serde_json::Number,
) -> Result<(), DefinitionError> {
    if number.as_f64().is_none_or(|value| !value.is_finite()) {
        return Err(TreeError::definition(
            &definition.name,
            path,
            TreeErrorKind::NonFiniteNumber(number.clone()),
        ));
    }
    Ok(())
}

fn definition_name(reference: &str) -> Result<&str, DefinitionError> {
    let Some(name) = reference.strip_prefix("#/$defs/") else {
        return Err(DefinitionError::ReferencePrefix {
            reference: reference.to_owned(),
        });
    };
    if name.is_empty() || name.contains('/') {
        return Err(DefinitionError::ReferenceName {
            reference: reference.to_owned(),
        });
    }
    Ok(name)
}

impl Spec {
    pub(crate) fn set_definition_origins(
        &mut self,
        document: &Path,
        shared: &BTreeMap<String, EnumType>,
    ) {
        let resolve = |definition: &mut EnumDefinition| {
            if let Some(origin) = shared.get(&definition.enum_type.name) {
                definition.enum_type = origin.clone();
            } else {
                definition.enum_type.document = document.to_owned();
            }
        };
        for function in &mut self.functions {
            for input in &mut function.inputs {
                if let Input::Enum { definition, .. } = input {
                    resolve(definition);
                }
            }
            if let Some(implementation) = &mut function.implementation {
                for variable in &mut implementation.variables {
                    match variable {
                        ImplementationVariable::Lookup { lookup, .. } => {
                            if let Some(definition) = lookup
                                .definition
                                .as_mut()
                                .and_then(|lookup| lookup.input_type.as_mut())
                            {
                                resolve(definition);
                            }
                        }
                        ImplementationVariable::Tree { tree, .. } => {
                            if let Some(definition) = tree.definition.as_mut() {
                                for input in &mut definition.inputs {
                                    if let TreeInput::Enum(input) = input
                                        && let Some(definition) = input.definition.as_mut()
                                    {
                                        resolve(definition);
                                    }
                                }
                            }
                        }
                        ImplementationVariable::Expression { .. } => {}
                    }
                }
            }
        }
    }
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
    #[serde(default)]
    pub(crate) verification_tolerances: BTreeMap<String, VerificationToleranceOverride>,
    pub(crate) implementation: Option<Implementation>,
    #[serde(default)]
    pub(crate) verification_cases: Vec<VerificationCase>,
    #[serde(default)]
    pub(crate) edge_cases: Vec<serde_json::Value>,
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
pub(crate) struct VerificationCase {
    pub(crate) id: String,
    pub(crate) kind: VerificationKind,
    pub(crate) inputs: BTreeMap<String, VerificationInput>,
    pub(crate) expected: BTreeMap<String, f64>,
    pub(crate) source_location: Option<String>,
    pub(crate) rationale: Option<String>,
    pub(crate) notes: Option<String>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "lowercase")]
pub(crate) enum VerificationKind {
    Published,
    Calculated,
}

impl VerificationKind {
    pub(crate) const ALL: [Self; 2] = [Self::Published, Self::Calculated];

    pub(crate) const fn label(self) -> &'static str {
        match self {
            Self::Published => "published",
            Self::Calculated => "calculated",
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub(crate) enum VerificationInput {
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

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct OutputField {
    pub(crate) name: String,
    #[serde(default)]
    pub(crate) quantity: String,
    pub(crate) symbol: Option<String>,
    /// Stable identifier in the unit registry.
    pub(crate) unit: String,
    /// Literal source notation; normalization never changes numerical values.
    #[serde(default)]
    pub(crate) reported_unit: String,
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
    pub(crate) enum_type: EnumType,
    #[serde(rename = "type")]
    kind: EnumKind,
    pub(crate) description: String,
    pub(crate) values: Vec<EnumValue>,
}

/// The defining document and member identify a type, independently of its consumers.
#[derive(Clone, Debug, Default, Eq, PartialEq, Ord, PartialOrd)]
pub(crate) struct EnumType {
    pub(crate) document: PathBuf,
    pub(crate) name: String,
    pub(crate) shared_module: Option<String>,
}

impl EnumDefinition {
    pub(crate) fn identity(&self) -> &EnumType {
        &self.enum_type
    }

    pub(crate) fn is_shared(&self) -> bool {
        self.enum_type.shared_module.is_some()
    }

    pub(crate) fn shared_document(&self) -> Option<&str> {
        self.enum_type.shared_module.as_deref()
    }
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
pub(crate) struct TreeDefinition {
    #[serde(skip)]
    pub(crate) name: String,
    #[serde(rename = "type")]
    kind: TreeKind,
    pub(crate) inputs: Vec<TreeInput>,
    pub(crate) output: Reference,
    pub(crate) root: DecisionTree,
    #[serde(skip)]
    pub(crate) output_type: Option<Outputs>,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
enum TreeKind {
    Tree,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub(crate) enum TreeInput {
    Number {
        name: String,
        #[serde(rename = "type")]
        kind: TreeNumberKind,
    },
    Enum(TreeEnumInput),
}

impl TreeInput {
    pub(crate) fn name(&self) -> &str {
        match self {
            Self::Number { name, .. } => name,
            Self::Enum(input) => &input.name,
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
pub(crate) enum TreeNumberKind {
    Number,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct TreeEnumInput {
    pub(crate) name: String,
    #[serde(flatten)]
    pub(crate) reference: Reference,
    #[serde(skip)]
    pub(crate) definition: Option<EnumDefinition>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub(crate) enum Outputs {
    Scalar {
        #[serde(flatten)]
        field: OutputField,
    },
    Record {
        name: String,
        fields: Vec<OutputField>,
    },
}

impl Outputs {
    pub(crate) fn fields(&self) -> &[OutputField] {
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
    Tree {
        name: String,
        tree: Box<TreeInvocation>,
    },
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct TreeInvocation {
    #[serde(rename = "definition")]
    pub(crate) definition_ref: Reference,
    pub(crate) arguments: BTreeMap<String, String>,
    #[serde(skip)]
    pub(crate) definition: Option<TreeDefinition>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct LookupInvocation {
    pub(crate) table: Reference,
    pub(crate) key: String,
    #[serde(skip)]
    pub(crate) definition: Option<LookupDefinition>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub(crate) enum DecisionTree {
    Leaf(DecisionTreeLeaf),
    Split(DecisionTreeBranch),
    Match(DecisionTreeMatch),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct DecisionTreeLeaf {
    pub(crate) leaf: DecisionTreeLeafValue,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub(crate) enum DecisionTreeLeafValue {
    Number(serde_json::Number),
    Record(BTreeMap<String, serde_json::Number>),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct DecisionTreeBranch {
    pub(crate) split: DecisionTreeSplit,
    pub(crate) yes: Box<DecisionTree>,
    pub(crate) no: Box<DecisionTree>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct DecisionTreeMatch {
    #[serde(rename = "match")]
    pub(crate) match_node: DecisionTreeMatchNode,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct DecisionTreeMatchNode {
    pub(crate) input: String,
    pub(crate) cases: Vec<DecisionTreeMatchCase>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct DecisionTreeMatchCase {
    pub(crate) values: Vec<String>,
    pub(crate) then: Box<DecisionTree>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(untagged)]
pub(crate) enum DecisionTreeSplit {
    LessThan(DecisionTreeLessThan),
    EnumIn(DecisionTreeEnumIn),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct DecisionTreeLessThan {
    pub(crate) input: String,
    pub(crate) operator: LessThanOperator,
    pub(crate) value: serde_json::Number,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
pub(crate) enum LessThanOperator {
    #[serde(rename = "lt")]
    LessThan,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct DecisionTreeEnumIn {
    pub(crate) input: String,
    pub(crate) operator: EnumInOperator,
    pub(crate) values: Vec<String>,
}

#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
pub(crate) enum EnumInOperator {
    #[serde(rename = "in")]
    In,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(crate) struct VerificationToleranceOverride {
    pub(crate) absolute: f64,
    #[serde(default)]
    pub(crate) relative: Option<f64>,
    pub(crate) source_location: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct QuantityUnit {
    pub(crate) absolute: f64,
    #[serde(default)]
    pub(crate) relative: Option<f64>,
    pub(crate) rationale: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Quantity {
    pub(crate) description: String,
    #[serde(deserialize_with = "deserialize_unique_units")]
    pub(crate) units: BTreeMap<String, QuantityUnit>,
}

fn deserialize_unique_units<'de, D>(
    deserializer: D,
) -> Result<BTreeMap<String, QuantityUnit>, D::Error>
where
    D: Deserializer<'de>,
{
    struct UniqueUnitsVisitor;

    impl<'de> Visitor<'de> for UniqueUnitsVisitor {
        type Value = BTreeMap<String, QuantityUnit>;

        fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
            formatter.write_str("a map with unique unit keys")
        }

        fn visit_map<A>(self, mut map: A) -> Result<Self::Value, A::Error>
        where
            A: MapAccess<'de>,
        {
            let mut units = BTreeMap::new();
            while let Some((unit, tolerance)) = map.next_entry()? {
                if units.insert(unit, tolerance).is_some() {
                    return Err(A::Error::custom(DefinitionError::DuplicateQuantityUnit));
                }
            }
            Ok(units)
        }
    }

    deserializer.deserialize_map(UniqueUnitsVisitor)
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Unit {
    pub(crate) preferred_notation: String,
    #[serde(default)]
    pub(crate) aliases: Vec<String>,
}

#[derive(Clone, Debug, Default)]
pub(crate) struct QuantityRegistry {
    pub(crate) quantities: BTreeMap<String, Quantity>,
    pub(crate) units: BTreeMap<String, Unit>,
}

#[derive(Clone, Debug)]
pub(crate) struct Entry {
    pub(crate) path: PathBuf,
    pub(crate) slug: String,
    pub(crate) spec: Spec,
    pub(crate) implementations: Vec<Option<crate::semantic::Function>>,
    pub(crate) quantities: Arc<QuantityRegistry>,
}

/// A validated source function paired with its immutable semantic IR.
#[derive(Clone, Debug)]
pub(crate) struct CompiledFunction {
    pub(crate) entry: Entry,
    pub(crate) function_index: usize,
    pub(crate) ir: crate::semantic::Function,
    pub(crate) core: CoreFunction,
    pub(crate) verification_cases: Vec<CompiledVerificationCase>,
    pub(crate) output_tolerances: Vec<CompiledTolerance>,
}

#[derive(Clone, Debug)]
pub(crate) struct CompiledVerificationCase {
    pub(crate) id: String,
    pub(crate) inputs: Vec<CompiledInput>,
    pub(crate) expected: Vec<f64>,
}

#[derive(Clone, Debug)]
pub(crate) struct CompiledTolerance {
    pub(crate) absolute: f64,
    pub(crate) relative: f64,
    pub(crate) quantity: String,
    pub(crate) unit: String,
    pub(crate) source: ToleranceSource,
}

#[derive(Clone, Debug)]
pub(crate) enum ToleranceSource {
    Registry,
    SourceOverride(String),
}

#[derive(Clone, Debug)]
pub(crate) enum CompiledInput {
    Number(f64),
    Enum {
        enum_type: EnumType,
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
    Lookup(Box<RawLookup>),
    Tree(Box<RawTreeInvocation>),
}

#[derive(Clone, Debug)]
pub(crate) struct RawTreeInvocation {
    pub(crate) implementation_path: String,
    pub(crate) arguments: BTreeMap<String, String>,
    pub(crate) definition: TreeDefinition,
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
        let spec: Spec = serde_yaml::from_str(
            "source: {summary: Test source., citation_apa: Test (2026)., doi: null}\nfunctions: []",
        )
        .unwrap();
        assert_eq!(spec.generation.public_python, PythonGeneration::Generated);
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
                .enum_type
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
                enum_type: EnumType {
                    name: "TestCategory".into(),
                    ..Default::default()
                },
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
