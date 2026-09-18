#[derive(Debug, thiserror::Error)]
pub(crate) enum DefinitionError {
    #[error(
        "function {function} must bind a name when referencing type definition `{name}` as an input"
    )]
    MissingInputBinding { function: String, name: String },
    #[error("function {function} references output definition `{name}` as an input")]
    OutputAsInput { function: String, name: String },
    #[error("function {function} references non-output definition `{name}` as an output")]
    NonOutputAsOutput { function: String, name: String },
    #[error("function {function} references parameter definition `{name}` as an output")]
    ParameterAsOutput { function: String, name: String },
    #[error("function {function} references unknown definition `{name}`")]
    UnknownDefinition { function: String, name: String },
    #[error("function {function} references unknown lookup definition `{name}`")]
    UnknownLookup { function: String, name: String },
    #[error("function {function} references unknown tree definition `{name}`")]
    UnknownTree { function: String, name: String },
    #[error(
        "function {function} input {input} references non-enum definition `{type_name}` as its type"
    )]
    NonEnumInput {
        function: String,
        input: String,
        type_name: String,
    },
    #[error("function {function} input {input} references unknown enum definition `{type_name}`")]
    UnknownInputEnum {
        function: String,
        input: String,
        type_name: String,
    },
    #[error("lookup `{name}` input must reference an enum definition")]
    InputDefinitionType { name: String },
    #[error("lookup `{name}` references unknown input type `{input_name}`")]
    UnknownInputType { name: String, input_name: String },
    #[error("lookup `{name}` output must reference a record definition")]
    OutputDefinitionType { name: String },
    #[error("lookup `{name}` references unknown output type `{output_name}`")]
    UnknownOutputType { name: String, output_name: String },
    #[error("lookup `{name}` has duplicate key `{key}` at value {index}")]
    DuplicateLookupKey {
        name: String,
        key: String,
        index: usize,
    },
    #[error("lookup `{name}` has unknown enum member `{key}` at value {index}")]
    UnknownLookupMember {
        name: String,
        key: String,
        index: usize,
    },
    #[error("lookup `{name}` value {index} keys must exactly match output fields")]
    LookupFields { name: String, index: usize },
    #[error("lookup `{name}` values must cover every member of enum `{enum_name}` exactly once")]
    LookupCoverage { name: String, enum_name: String },
    #[error("reference `{reference}` must start with `#/$defs/`")]
    ReferencePrefix { reference: String },
    #[error("reference `{reference}` must name exactly one local definition")]
    ReferenceName { reference: String },
    #[error("duplicate entry in quantity units")]
    DuplicateQuantityUnit,
    #[error(transparent)]
    Tree(#[from] TreeError),
}

#[derive(Debug, thiserror::Error)]
#[error("tree `{name}` {path}: {kind}")]
pub(crate) struct TreeError {
    pub(crate) name: String,
    pub(crate) path: String,
    pub(crate) kind: TreeErrorKind,
}

impl TreeError {
    pub(crate) fn definition(name: &str, path: &str, kind: TreeErrorKind) -> DefinitionError {
        DefinitionError::Tree(Self {
            name: name.to_owned(),
            path: path.to_owned(),
            kind,
        })
    }
}

#[derive(Debug, thiserror::Error)]
pub(crate) enum TreeErrorKind {
    #[error("duplicate input `{0}`")]
    DuplicateInput(String),
    #[error("input `{0}` must reference an enum definition")]
    InputNotEnum(String),
    #[error("input `{input}` references unknown enum definition `{type_name}`")]
    UnknownInputEnum { input: String, type_name: String },
    #[error("output must reference an output definition")]
    OutputNotOutput,
    #[error("unknown output type `{0}`")]
    UnknownOutputType(String),
    #[error("must be a numeric leaf")]
    NumericLeafRequired,
    #[error("must be a record leaf")]
    RecordLeafRequired,
    #[error("keys must exactly match output fields")]
    RecordFields,
    #[error("input `{0}` must be numeric for operator `lt`")]
    NumericInputRequired(String),
    #[error("input `{0}` must be an enum for operator `in`")]
    EnumInputRequired(String),
    #[error("match input `{0}` must be an enum")]
    MatchInputNotEnum(String),
    #[error("match cases overlap on enum member `{0}`")]
    OverlappingMember(String),
    #[error("match cases must cover every member of enum `{0}` exactly once")]
    IncompleteMatch(String),
    #[error("unknown input `{0}`")]
    UnknownInput(String),
    #[error("requires at least one enum member")]
    EmptyMembers,
    #[error("repeats enum member `{0}`")]
    DuplicateMember(String),
    #[error("unknown member `{member}` of enum `{enum_name}`")]
    UnknownMember { member: String, enum_name: String },
    #[error("number `{0}` is not a finite f64")]
    NonFiniteNumber(serde_json::Number),
}
