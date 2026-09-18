use std::{
    collections::{BTreeMap, HashMap},
    fmt,
};

use crate::{
    formula::{self, Span},
    model::{
        DecisionTree as RawDecisionTreeNode, DecisionTreeLeafValue,
        DecisionTreeSplit as RawDecisionTreeSplit, Outputs, RawExpression, RawFunction,
        RawInputType, RawLookup, RawTreeInvocation, RawVariableValue, SourceLocation,
        TreeDefinition as RawTreeDefinition, TreeInput as RawTreeInput,
    },
};

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Function {
    pub(crate) inputs: Vec<Input>,
    pub(crate) variables: Vec<Variable>,
    pub(crate) result: ResultBinding,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ResultBinding {
    Fields,
    RecordVariable(usize),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct Input {
    pub(crate) name: String,
    pub(crate) value_type: ValueType,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Variable {
    pub(crate) name: String,
    pub(crate) value: VariableValue,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum ValueType {
    Number,
    Enum(crate::model::EnumType),
    Record(RecordType),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct RecordType {
    pub(crate) name: String,
    pub(crate) fields: Vec<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum VariableValue {
    Expression(Expr),
    RecordLookup(RecordLookup),
    Tree(TreeCall),
}

impl VariableValue {
    pub(crate) fn as_expression(&self) -> Option<&Expr> {
        match self {
            Self::Expression(expression) => Some(expression),
            Self::RecordLookup(_) | Self::Tree(_) => None,
        }
    }

    pub(crate) fn is_number(&self) -> bool {
        matches!(self, Self::Expression(_))
            || matches!(self, Self::Tree(tree) if tree.definition.output == ValueType::Number)
    }
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum DecisionTree {
    Leaf(DecisionTreeLeaf),
    Split {
        predicate: DecisionTreePredicate,
        yes: Box<Self>,
        no: Box<Self>,
    },
    Match {
        input: Reference,
        enum_type: crate::model::EnumType,
        cases: Vec<DecisionTreeMatchCase>,
    },
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum DecisionTreeLeaf {
    Number(Number),
    Record(Vec<Number>),
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct DecisionTreeMatchCase {
    pub(crate) members: Vec<String>,
    pub(crate) then: DecisionTree,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum DecisionTreePredicate {
    LessThan {
        input: Reference,
        value: Number,
    },
    EnumIn {
        input: Reference,
        enum_type: crate::model::EnumType,
        members: Vec<String>,
    },
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct RecordLookup {
    pub(crate) key: Reference,
    pub(crate) enum_type: crate::model::EnumType,
    pub(crate) output: RecordType,
    pub(crate) cases: Vec<RecordLookupCase>,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct RecordLookupCase {
    pub(crate) member: String,
    pub(crate) values: Vec<Number>,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct TreeCall {
    pub(crate) definition: TreeDefinition,
    pub(crate) arguments: Vec<Reference>,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct TreeDefinition {
    pub(crate) name: String,
    pub(crate) inputs: Vec<Input>,
    pub(crate) output: ValueType,
    pub(crate) root: DecisionTree,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Number {
    pub(crate) value: f64,
    pub(crate) lexeme: String,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum Expr {
    Number(Number),
    Reference(Reference),
    Field {
        record: Reference,
        field: String,
    },
    Unary {
        op: UnaryOp,
        operand: Box<Self>,
    },
    Binary {
        op: BinaryOp,
        left: Box<Self>,
        right: Box<Self>,
    },
    Call {
        function: MathFunction,
        args: Vec<Self>,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum Reference {
    Input(usize),
    Variable(usize),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum UnaryOp {
    Plus,
    Minus,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum BinaryOp {
    Add,
    Subtract,
    Multiply,
    Divide,
    Power,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum MathFunction {
    Sqrt,
    Exp,
    Ln,
    Log10,
    Abs,
    Min,
    Max,
}

impl MathFunction {
    fn parse(name: &str) -> Option<Self> {
        let func = match name {
            "sqrt" => Self::Sqrt,
            "exp" => Self::Exp,
            "ln" => Self::Ln,
            "log10" => Self::Log10,
            "abs" => Self::Abs,
            "min" => Self::Min,
            "max" => Self::Max,
            _ => return None,
        };
        Some(func)
    }

    fn arity(self) -> usize {
        match self {
            Self::Sqrt | Self::Exp | Self::Ln | Self::Log10 | Self::Abs => 1,
            Self::Min | Self::Max => 2,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, thiserror::Error)]
pub(crate) enum SemanticErrorKind {
    #[error("duplicate name `{name}`")]
    DuplicateName { name: String },
    #[error("unknown identifier `{name}`")]
    UnknownIdentifier { name: String },
    #[error("identifier `{name}` is not numeric")]
    NonNumericIdentifier { name: String },
    #[error("variable `{name}` cannot reference itself")]
    SelfReference { name: String },
    #[error("variable `{name}` cannot reference a later variable")]
    ForwardReference { name: String },
    #[error("record `{record}` has no field `{field}`")]
    UnknownRecordField { record: String, field: String },
    #[error("`{name}` is not a record")]
    NotARecord { name: String },
    #[error("unsupported function `{name}`")]
    UnsupportedFunction { name: String },
    #[error("function `{name}` expects {expected} argument(s), found {actual}")]
    WrongArity {
        name: String,
        expected: usize,
        actual: usize,
    },
    #[error("unknown lookup key `{key}`")]
    UnknownLookupKey { key: String },
    #[error("lookup key `{key}` must have enum type `{expected}`")]
    LookupKeyType { key: String, expected: String },
    #[error(
        "tree `{tree}` argument names do not match its inputs; missing {missing:?}, unknown {unknown:?}"
    )]
    TreeArguments {
        tree: String,
        missing: Vec<String>,
        unknown: Vec<String>,
    },
    #[error("tree argument `{name}` cannot reference itself")]
    TreeSelfReference { name: String },
    #[error("tree argument `{name}` cannot reference a later variable")]
    TreeForwardReference { name: String },
    #[error("tree argument references unknown value `{name}`")]
    UnknownTreeArgument { name: String },
    #[error("tree argument `{name}` has type {actual}, but input `{input}` requires {expected}")]
    TreeArgumentType {
        name: String,
        actual: String,
        input: String,
        expected: String,
    },
    #[error("expression is repeated at {path}:{line}:{start}..{end}; it must be extracted into an earlier implementation variable",
        path = .specification_path.display(), line = .location.line,
        start = .location.column + .span.start, end = .location.column + .span.end)]
    RepeatedExpression {
        specification_path: std::path::PathBuf,
        location: SourceLocation,
        span: Span,
    },
}

#[derive(Clone, Debug, Eq, PartialEq, thiserror::Error)]
pub(crate) struct Error {
    pub(crate) specification_path: String,
    pub(crate) function: String,
    pub(crate) implementation_path: String,
    pub(crate) span: Span,
    source_location: Option<Box<SourceLocation>>,
    #[source]
    pub(crate) kind: SemanticErrorKind,
}

impl Error {
    fn in_function(
        raw: &RawFunction,
        implementation_path: &str,
        span: Span,
        kind: SemanticErrorKind,
    ) -> Box<Self> {
        Box::new(Self {
            specification_path: raw.specification_path.display().to_string(),
            function: raw.name.clone(),
            implementation_path: implementation_path.to_owned(),
            span,
            source_location: None,
            kind,
        })
    }

    fn at_source(
        raw: &RawFunction,
        source_location: SourceLocation,
        span: Span,
        kind: SemanticErrorKind,
    ) -> Box<Self> {
        Box::new(Self {
            specification_path: raw.specification_path.display().to_string(),
            function: raw.name.clone(),
            implementation_path: String::new(),
            span,
            source_location: Some(Box::new(source_location)),
            kind,
        })
    }

    fn in_expression(
        raw: &RawFunction,
        expression: &RawExpression,
        span: Span,
        kind: SemanticErrorKind,
    ) -> Box<Self> {
        Self::in_function(raw, &expression.implementation_path, span, kind)
    }
}

impl fmt::Display for Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        if let Some(source_location) = self.source_location.as_deref() {
            return write!(
                formatter,
                "{}:{}:{}..{}: {}",
                self.specification_path,
                source_location.line,
                source_location.column + self.span.start,
                source_location.column + self.span.end,
                self.kind,
            );
        }
        write!(
            formatter,
            "{} -> function {} -> {}:{}..{}: {}",
            self.specification_path,
            self.function,
            self.implementation_path,
            self.span.start,
            self.span.end,
            self.kind,
        )
    }
}

pub(crate) fn compile(raw: &RawFunction) -> Result<Function, Box<Error>> {
    let mut scope = BTreeMap::new();
    for (index, input) in raw.inputs.iter().enumerate() {
        let value_type = match &input.value_type {
            RawInputType::Number => ValueType::Number,
            RawInputType::Enum(definition) => ValueType::Enum(definition.enum_type.clone()),
        };
        if scope
            .insert(
                input.name.clone(),
                Binding {
                    reference: Reference::Input(index),
                    value_type,
                },
            )
            .is_some()
        {
            return Err(Error::in_function(
                raw,
                "inputs",
                Span { start: 0, end: 0 },
                SemanticErrorKind::DuplicateName {
                    name: input.name.clone(),
                },
            ));
        }
    }

    validate_repeated_expressions(raw)?;

    let variable_names: BTreeMap<_, _> = raw
        .variables
        .iter()
        .enumerate()
        .map(|(index, variable)| (variable.name.as_str(), index))
        .collect();
    let mut variables = Vec::with_capacity(raw.variables.len());
    for (index, variable) in raw.variables.iter().enumerate() {
        if scope.contains_key(&variable.name) {
            return Err(Error::in_function(
                raw,
                "variables",
                Span { start: 0, end: 0 },
                SemanticErrorKind::DuplicateName {
                    name: variable.name.clone(),
                },
            ));
        }
        let (value, value_type) = match &variable.value {
            RawVariableValue::Expression(expression) => (
                VariableValue::Expression(compile_expression(
                    raw,
                    expression,
                    &scope,
                    &variable_names,
                    index,
                )?),
                ValueType::Number,
            ),
            RawVariableValue::Lookup(lookup) => {
                let (lookup, record_type) = compile_lookup(raw, lookup, &scope)?;
                (
                    VariableValue::RecordLookup(lookup),
                    ValueType::Record(record_type),
                )
            }
            RawVariableValue::Tree(tree) => {
                let (tree, value_type) =
                    compile_tree_call(raw, tree, &scope, &variable_names, index)?;
                (VariableValue::Tree(tree), value_type)
            }
        };
        scope.insert(
            variable.name.clone(),
            Binding {
                reference: Reference::Variable(index),
                value_type,
            },
        );
        variables.push(Variable {
            name: variable.name.clone(),
            value,
        });
    }

    Ok(Function {
        inputs: raw
            .inputs
            .iter()
            .map(|input| Input {
                name: input.name.clone(),
                value_type: match &input.value_type {
                    RawInputType::Number => ValueType::Number,
                    RawInputType::Enum(definition) => ValueType::Enum(definition.enum_type.clone()),
                },
            })
            .collect(),
        variables,
        result: ResultBinding::Fields,
    })
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
enum StructuralExpr {
    Number(String),
    Variable(String),
    Field {
        base: String,
        field: String,
    },
    Unary {
        op: formula::UnaryOp,
        operand: Box<Self>,
    },
    Binary {
        op: formula::BinaryOp,
        left: Box<Self>,
        right: Box<Self>,
    },
    Call {
        name: String,
        args: Vec<Self>,
    },
    Grouped(Box<Self>),
}

#[derive(Clone, Debug)]
struct Occurrence {
    source_location: SourceLocation,
    span: Span,
}

fn validate_repeated_expressions(raw: &RawFunction) -> Result<(), Box<Error>> {
    let mut occurrences = HashMap::new();
    for variable in &raw.variables {
        let RawVariableValue::Expression(expression) = &variable.value else {
            continue;
        };
        if let Some((first, later)) = find_repeated_expression(
            &expression.expression,
            expression.source_location,
            &mut occurrences,
        ) {
            return Err(Error::at_source(
                raw,
                first.source_location,
                first.span,
                SemanticErrorKind::RepeatedExpression {
                    specification_path: raw.specification_path.clone(),
                    location: later.source_location,
                    span: later.span,
                },
            ));
        }
    }
    Ok(())
}

fn find_repeated_expression(
    expression: &formula::Expr,
    source_location: SourceLocation,
    occurrences: &mut HashMap<StructuralExpr, Occurrence>,
) -> Option<(Occurrence, Occurrence)> {
    if requires_extraction(expression) {
        let structural = structural_expr(expression);
        let occurrence = Occurrence {
            source_location,
            span: expression.span,
        };
        if let Some(first) = occurrences.get(&structural) {
            return Some((first.clone(), occurrence));
        }
        occurrences.insert(structural, occurrence);
    }
    match &expression.kind {
        formula::ExprKind::Unary { operand, .. } | formula::ExprKind::Grouped(operand) => {
            find_repeated_expression(operand, source_location, occurrences)
        }
        formula::ExprKind::Binary { left, right, .. } => {
            find_repeated_expression(left, source_location, occurrences)
                .or_else(|| find_repeated_expression(right, source_location, occurrences))
        }
        formula::ExprKind::Call { args, .. } => args
            .iter()
            .find_map(|argument| find_repeated_expression(argument, source_location, occurrences)),
        formula::ExprKind::Number(_)
        | formula::ExprKind::Variable(_)
        | formula::ExprKind::Field { .. } => None,
    }
}

fn requires_extraction(expression: &formula::Expr) -> bool {
    match &expression.kind {
        formula::ExprKind::Call { .. } => true,
        formula::ExprKind::Binary {
            op: formula::BinaryOp::Divide | formula::BinaryOp::Power,
            ..
        } => true,
        formula::ExprKind::Binary { .. } => arithmetic_operation_count(expression) > 1,
        formula::ExprKind::Unary { operand, .. } | formula::ExprKind::Grouped(operand) => {
            arithmetic_operation_count(expression) > 1 || requires_extraction(operand)
        }
        formula::ExprKind::Number(_)
        | formula::ExprKind::Variable(_)
        | formula::ExprKind::Field { .. } => false,
    }
}

fn arithmetic_operation_count(expression: &formula::Expr) -> usize {
    match &expression.kind {
        formula::ExprKind::Number(_)
        | formula::ExprKind::Variable(_)
        | formula::ExprKind::Field { .. } => 0,
        formula::ExprKind::Call { args, .. } => args.iter().map(arithmetic_operation_count).sum(),
        formula::ExprKind::Grouped(operand) => arithmetic_operation_count(operand),
        formula::ExprKind::Unary { operand, .. } => 1 + arithmetic_operation_count(operand),
        formula::ExprKind::Binary { left, right, .. } => {
            1 + arithmetic_operation_count(left) + arithmetic_operation_count(right)
        }
    }
}

fn structural_expr(expression: &formula::Expr) -> StructuralExpr {
    match &expression.kind {
        formula::ExprKind::Number(number) => StructuralExpr::Number(number.lexeme.clone()),
        formula::ExprKind::Variable(name) => StructuralExpr::Variable(name.clone()),
        formula::ExprKind::Field { base, field } => StructuralExpr::Field {
            base: base.clone(),
            field: field.clone(),
        },
        formula::ExprKind::Unary { op, operand } => StructuralExpr::Unary {
            op: *op,
            operand: Box::new(structural_expr(operand)),
        },
        formula::ExprKind::Binary { op, left, right } => StructuralExpr::Binary {
            op: *op,
            left: Box::new(structural_expr(left)),
            right: Box::new(structural_expr(right)),
        },
        formula::ExprKind::Call { name, args } => StructuralExpr::Call {
            name: name.clone(),
            args: args.iter().map(structural_expr).collect(),
        },
        formula::ExprKind::Grouped(operand) => {
            StructuralExpr::Grouped(Box::new(structural_expr(operand)))
        }
    }
}

#[derive(Clone)]
struct Binding {
    reference: Reference,
    value_type: ValueType,
}

fn compile_lookup(
    raw: &RawFunction,
    lookup: &RawLookup,
    scope: &BTreeMap<String, Binding>,
) -> Result<(RecordLookup, RecordType), Box<Error>> {
    let binding = scope.get(&lookup.key).ok_or_else(|| {
        Error::in_function(
            raw,
            &lookup.implementation_path,
            Span { start: 0, end: 0 },
            SemanticErrorKind::UnknownLookupKey {
                key: lookup.key.clone(),
            },
        )
    })?;
    let enum_type = lookup
        .definition
        .input_type
        .as_ref()
        .expect("lookup input type is resolved");
    if binding.value_type != ValueType::Enum(enum_type.enum_type.clone()) {
        return Err(Error::in_function(
            raw,
            &lookup.implementation_path,
            Span { start: 0, end: 0 },
            SemanticErrorKind::LookupKeyType {
                key: lookup.key.clone(),
                expected: enum_type.enum_type.name.clone(),
            },
        ));
    }
    let output = lookup
        .definition
        .output_type
        .as_ref()
        .expect("lookup output type is resolved");
    let crate::model::Outputs::Record { name, fields } = output else {
        unreachable!("lookup outputs are validated as records")
    };
    let record_type = RecordType {
        name: name.clone(),
        fields: fields.iter().map(|field| field.name.clone()).collect(),
    };
    let cases = enum_type
        .values
        .iter()
        .map(|member| {
            let case = lookup
                .definition
                .values
                .iter()
                .find(|case| case.key == member.name)
                .expect("validated lookup covers every enum member exactly once");
            RecordLookupCase {
                member: member.name.clone(),
                values: fields
                    .iter()
                    .map(|field| {
                        let value = case.value[&field.name];
                        Number {
                            value,
                            lexeme: format!("{value:?}"),
                        }
                    })
                    .collect(),
            }
        })
        .collect();
    Ok((
        RecordLookup {
            key: binding.reference,
            enum_type: enum_type.enum_type.clone(),
            output: record_type.clone(),
            cases,
        },
        record_type,
    ))
}

fn compile_tree_call(
    raw: &RawFunction,
    call: &RawTreeInvocation,
    scope: &BTreeMap<String, Binding>,
    variable_names: &BTreeMap<&str, usize>,
    variable_index: usize,
) -> Result<(TreeCall, ValueType), Box<Error>> {
    let definition = compile_tree_definition(&call.definition);
    let expected = definition
        .inputs
        .iter()
        .map(|input| input.name.as_str())
        .collect::<std::collections::BTreeSet<_>>();
    let actual = call
        .arguments
        .keys()
        .map(String::as_str)
        .collect::<std::collections::BTreeSet<_>>();
    if expected != actual {
        let missing = expected
            .difference(&actual)
            .map(|name| (*name).to_owned())
            .collect();
        let unknown = actual
            .difference(&expected)
            .map(|name| (*name).to_owned())
            .collect();
        return Err(Error::in_function(
            raw,
            &call.implementation_path,
            Span { start: 0, end: 0 },
            SemanticErrorKind::TreeArguments {
                tree: definition.name.clone(),
                missing,
                unknown,
            },
        ));
    }
    let mut arguments = Vec::with_capacity(definition.inputs.len());
    for formal in &definition.inputs {
        let actual = &call.arguments[&formal.name];
        let Some(binding) = scope.get(actual) else {
            let kind = match variable_names.get(actual.as_str()) {
                Some(index) if *index == variable_index => SemanticErrorKind::TreeSelfReference {
                    name: actual.clone(),
                },
                Some(index) if *index > variable_index => SemanticErrorKind::TreeForwardReference {
                    name: actual.clone(),
                },
                _ => SemanticErrorKind::UnknownTreeArgument {
                    name: actual.clone(),
                },
            };
            return Err(Error::in_function(
                raw,
                &call.implementation_path,
                Span { start: 0, end: 0 },
                kind,
            ));
        };
        if binding.value_type != formal.value_type {
            return Err(Error::in_function(
                raw,
                &call.implementation_path,
                Span { start: 0, end: 0 },
                SemanticErrorKind::TreeArgumentType {
                    name: actual.clone(),
                    actual: value_type_name(&binding.value_type),
                    input: formal.name.clone(),
                    expected: value_type_name(&formal.value_type),
                },
            ));
        }
        arguments.push(binding.reference);
    }
    let output = definition.output.clone();
    Ok((
        TreeCall {
            definition,
            arguments,
        },
        output,
    ))
}

fn value_type_name(value_type: &ValueType) -> String {
    match value_type {
        ValueType::Number => "number".to_owned(),
        ValueType::Enum(enum_type) => format!("enum `{}`", enum_type.name),
        ValueType::Record(record) => format!("record `{}`", record.name),
    }
}

fn compile_tree_definition(raw: &RawTreeDefinition) -> TreeDefinition {
    let inputs = raw
        .inputs
        .iter()
        .map(|input| Input {
            name: input.name().to_owned(),
            value_type: match input {
                RawTreeInput::Number { .. } => ValueType::Number,
                RawTreeInput::Enum(input) => ValueType::Enum(
                    input
                        .definition
                        .as_ref()
                        .expect("tree enum input is resolved")
                        .enum_type
                        .clone(),
                ),
            },
        })
        .collect::<Vec<_>>();
    let output = match raw.output_type.as_ref().expect("tree output is resolved") {
        Outputs::Scalar { .. } => ValueType::Number,
        Outputs::Record { name, fields } => ValueType::Record(RecordType {
            name: name.clone(),
            fields: fields.iter().map(|field| field.name.clone()).collect(),
        }),
    };
    TreeDefinition {
        name: raw.name.clone(),
        root: compile_named_tree_node(raw, &raw.root),
        inputs,
        output,
    }
}

fn compile_named_tree_node(
    definition: &RawTreeDefinition,
    node: &RawDecisionTreeNode,
) -> DecisionTree {
    let input = |name: &str| {
        Reference::Input(
            definition
                .inputs
                .iter()
                .position(|input| input.name() == name)
                .expect("tree inputs are validated"),
        )
    };
    let number = |number: &serde_json::Number| Number {
        value: number.as_f64().expect("tree numbers are validated"),
        lexeme: number.to_string(),
    };
    match node {
        RawDecisionTreeNode::Leaf(leaf) => DecisionTree::Leaf(match &leaf.leaf {
            DecisionTreeLeafValue::Number(value) => DecisionTreeLeaf::Number(number(value)),
            DecisionTreeLeafValue::Record(values) => {
                let Outputs::Record { fields, .. } = definition
                    .output_type
                    .as_ref()
                    .expect("tree output is resolved")
                else {
                    unreachable!("tree leaf shape is validated")
                };
                DecisionTreeLeaf::Record(
                    fields
                        .iter()
                        .map(|field| number(&values[&field.name]))
                        .collect(),
                )
            }
        }),
        RawDecisionTreeNode::Split(branch) => {
            let predicate = match &branch.split {
                RawDecisionTreeSplit::LessThan(split) => DecisionTreePredicate::LessThan {
                    input: input(&split.input),
                    value: number(&split.value),
                },
                RawDecisionTreeSplit::EnumIn(split) => {
                    let RawTreeInput::Enum(formal) = definition
                        .inputs
                        .iter()
                        .find(|formal| formal.name() == split.input)
                        .expect("tree input is validated")
                    else {
                        unreachable!("tree predicate type is validated")
                    };
                    DecisionTreePredicate::EnumIn {
                        input: input(&split.input),
                        enum_type: formal
                            .definition
                            .as_ref()
                            .expect("tree enum is resolved")
                            .enum_type
                            .clone(),
                        members: split.values.clone(),
                    }
                }
            };
            DecisionTree::Split {
                predicate,
                yes: Box::new(compile_named_tree_node(definition, &branch.yes)),
                no: Box::new(compile_named_tree_node(definition, &branch.no)),
            }
        }
        RawDecisionTreeNode::Match(selection) => {
            let formal = definition
                .inputs
                .iter()
                .find(|formal| formal.name() == selection.match_node.input)
                .expect("tree match input is validated");
            let RawTreeInput::Enum(formal) = formal else {
                unreachable!("tree match input type is validated")
            };
            DecisionTree::Match {
                input: input(&selection.match_node.input),
                enum_type: formal
                    .definition
                    .as_ref()
                    .expect("tree enum is resolved")
                    .enum_type
                    .clone(),
                cases: selection
                    .match_node
                    .cases
                    .iter()
                    .map(|case| DecisionTreeMatchCase {
                        members: case.values.clone(),
                        then: compile_named_tree_node(definition, &case.then),
                    })
                    .collect(),
            }
        }
    }
}

fn compile_expression(
    raw: &RawFunction,
    expression: &RawExpression,
    scope: &BTreeMap<String, Binding>,
    variable_names: &BTreeMap<&str, usize>,
    variable_index: usize,
) -> Result<Expr, Box<Error>> {
    compile_expr(
        raw,
        expression,
        &expression.expression,
        scope,
        variable_names,
        variable_index,
    )
}

fn compile_expr(
    raw: &RawFunction,
    source: &RawExpression,
    expression: &formula::Expr,
    scope: &BTreeMap<String, Binding>,
    variable_names: &BTreeMap<&str, usize>,
    variable_index: usize,
) -> Result<Expr, Box<Error>> {
    match &expression.kind {
        formula::ExprKind::Number(number) => Ok(Expr::Number(Number {
            value: number.value,
            lexeme: number.lexeme.clone(),
        })),
        formula::ExprKind::Variable(name) => match scope.get(name) {
            Some(binding) if binding.value_type == ValueType::Number => {
                Ok(Expr::Reference(binding.reference))
            }
            Some(_) => Err(Error::in_expression(
                raw,
                source,
                expression.span,
                SemanticErrorKind::NonNumericIdentifier { name: name.clone() },
            )),
            None => {
                let kind = match variable_names.get(name.as_str()) {
                    Some(index) if *index == variable_index => {
                        SemanticErrorKind::SelfReference { name: name.clone() }
                    }
                    Some(index) if *index > variable_index => {
                        SemanticErrorKind::ForwardReference { name: name.clone() }
                    }
                    _ => SemanticErrorKind::UnknownIdentifier { name: name.clone() },
                };
                Err(Error::in_expression(raw, source, expression.span, kind))
            }
        },
        formula::ExprKind::Field { base, field } => match scope.get(base) {
            Some(Binding {
                reference,
                value_type: ValueType::Record(record),
            }) if record.fields.contains(field) => Ok(Expr::Field {
                record: *reference,
                field: field.clone(),
            }),
            Some(Binding {
                value_type: ValueType::Record(record),
                ..
            }) => Err(Error::in_expression(
                raw,
                source,
                expression.span,
                SemanticErrorKind::UnknownRecordField {
                    record: record.name.clone(),
                    field: field.clone(),
                },
            )),
            Some(_) => Err(Error::in_expression(
                raw,
                source,
                expression.span,
                SemanticErrorKind::NotARecord { name: base.clone() },
            )),
            None => Err(Error::in_expression(
                raw,
                source,
                expression.span,
                SemanticErrorKind::UnknownIdentifier { name: base.clone() },
            )),
        },
        formula::ExprKind::Unary { op, operand } => Ok(Expr::Unary {
            op: match op {
                formula::UnaryOp::Plus => UnaryOp::Plus,
                formula::UnaryOp::Minus => UnaryOp::Minus,
            },
            operand: Box::new(compile_expr(
                raw,
                source,
                operand,
                scope,
                variable_names,
                variable_index,
            )?),
        }),
        formula::ExprKind::Binary { op, left, right } => Ok(Expr::Binary {
            op: match op {
                formula::BinaryOp::Add => BinaryOp::Add,
                formula::BinaryOp::Subtract => BinaryOp::Subtract,
                formula::BinaryOp::Multiply => BinaryOp::Multiply,
                formula::BinaryOp::Divide => BinaryOp::Divide,
                formula::BinaryOp::Power => BinaryOp::Power,
            },
            left: Box::new(compile_expr(
                raw,
                source,
                left,
                scope,
                variable_names,
                variable_index,
            )?),
            right: Box::new(compile_expr(
                raw,
                source,
                right,
                scope,
                variable_names,
                variable_index,
            )?),
        }),
        formula::ExprKind::Call { name, args } => {
            let function = MathFunction::parse(name).ok_or_else(|| {
                Error::in_expression(
                    raw,
                    source,
                    expression.span,
                    SemanticErrorKind::UnsupportedFunction { name: name.clone() },
                )
            })?;
            if args.len() != function.arity() {
                return Err(Error::in_expression(
                    raw,
                    source,
                    expression.span,
                    SemanticErrorKind::WrongArity {
                        name: name.clone(),
                        expected: function.arity(),
                        actual: args.len(),
                    },
                ));
            }
            Ok(Expr::Call {
                function,
                args: args
                    .iter()
                    .map(|argument| {
                        compile_expr(raw, source, argument, scope, variable_names, variable_index)
                    })
                    .collect::<Result<_, _>>()?,
            })
        }
        formula::ExprKind::Grouped(expression) => compile_expr(
            raw,
            source,
            expression,
            scope,
            variable_names,
            variable_index,
        ),
    }
}

#[cfg(test)]
mod tests {
    use std::path::PathBuf;

    use crate::{
        formula::parse,
        model::{
            EnumDefinition, LookupDefinition, OutputField, Outputs, RawExpression, RawFunction,
            RawInput, RawInputType, RawLookup, RawVariable, RawVariableValue, SourceLocation,
        },
    };

    use super::{BinaryOp, Expr, SemanticErrorKind, VariableValue, compile};

    fn expression(path: &str, source: &str) -> RawExpression {
        RawExpression {
            implementation_path: path.into(),
            source_location: SourceLocation { line: 1, column: 1 },
            expression: parse(path, source).unwrap(),
        }
    }

    fn function(inputs: &[&str], variables: Vec<RawVariable>) -> RawFunction {
        RawFunction {
            specification_path: PathBuf::from("specs/functions/example.md"),
            name: "example".into(),
            inputs: inputs
                .iter()
                .map(|name| RawInput {
                    name: (*name).into(),
                    value_type: RawInputType::Number,
                })
                .collect(),
            variables,
        }
    }

    fn variable(name: &str, path: &str, source: &str) -> RawVariable {
        RawVariable {
            name: name.into(),
            value: RawVariableValue::Expression(expression(path, source)),
        }
    }

    #[test]
    fn resolves_ordered_variables_and_reuses_prior_values() {
        let raw = function(
            &["x", "y"],
            vec![
                variable("first", "implementation.variables[0]", "y + 1"),
                variable("second", "implementation.variables[1]", "first * x"),
                variable("third", "implementation.variables[2]", "second - first"),
            ],
        );
        let compiled = compile(&raw).unwrap();
        use super::{Number, Reference};
        let expected = [
            Expr::Binary {
                op: BinaryOp::Add,
                left: Box::new(Expr::Reference(Reference::Input(1))),
                right: Box::new(Expr::Number(Number {
                    value: 1.0,
                    lexeme: "1".into(),
                })),
            },
            Expr::Binary {
                op: BinaryOp::Multiply,
                left: Box::new(Expr::Reference(Reference::Variable(0))),
                right: Box::new(Expr::Reference(Reference::Input(0))),
            },
            Expr::Binary {
                op: BinaryOp::Subtract,
                left: Box::new(Expr::Reference(Reference::Variable(1))),
                right: Box::new(Expr::Reference(Reference::Variable(0))),
            },
        ];
        assert_eq!(
            compiled
                .variables
                .iter()
                .map(|variable| variable.name.as_str())
                .collect::<Vec<_>>(),
            ["first", "second", "third"]
        );
        assert_eq!(
            compiled
                .variables
                .iter()
                .map(|variable| variable.value.as_expression().unwrap())
                .collect::<Vec<_>>(),
            expected.iter().collect::<Vec<_>>()
        );
    }

    #[test]
    fn lookup_cases_follow_enum_order() {
        let mut enum_type: EnumDefinition = serde_yaml::from_str(
            r#"
            type: enum
            description: Example enum.
            values:
              - name: first
                value: first
              - name: second
                value: second
            "#,
        )
        .unwrap();
        enum_type.enum_type.name = "ExampleEnum".into();

        let mut lookup_definition: LookupDefinition = serde_yaml::from_str(
            r##"
            type: lookup
            input:
              $ref: "#/$defs/ExampleEnum"
            output:
              $ref: "#/$defs/ExampleRecord"
            values:
              - key: second
                value:
                  value: 2.0
              - key: first
                value:
                  value: 1.0
            "##,
        )
        .unwrap();
        lookup_definition.name = "ExampleLookup".into();
        lookup_definition.input_type = Some(enum_type.clone());
        lookup_definition.output_type = Some(Outputs::Record {
            name: "ExampleRecord".into(),
            fields: vec![OutputField {
                name: "value".into(),
                quantity: String::new(),
                symbol: None,
                unit: "dimensionless".into(),
                reported_unit: "1".into(),
                domain: None,
                description: "Example value.".into(),
            }],
        });

        let raw = RawFunction {
            specification_path: PathBuf::from("specs/functions/example.md"),
            name: "example".into(),
            inputs: vec![RawInput {
                name: "kind".into(),
                value_type: RawInputType::Enum(enum_type),
            }],
            variables: vec![RawVariable {
                name: "row".into(),
                value: RawVariableValue::Lookup(Box::new(RawLookup {
                    implementation_path: "implementation.variables[0].lookup".into(),
                    key: "kind".into(),
                    definition: lookup_definition,
                })),
            }],
        };
        let compiled = compile(&raw).unwrap();
        let VariableValue::RecordLookup(lookup) = &compiled.variables[0].value else {
            panic!("expected record lookup");
        };
        assert_eq!(
            lookup
                .cases
                .iter()
                .map(|case| case.member.as_str())
                .collect::<Vec<_>>(),
            ["first", "second"]
        );
        assert_eq!(
            lookup
                .cases
                .iter()
                .map(|case| case.values[0].value)
                .collect::<Vec<_>>(),
            [1.0, 2.0]
        );
    }

    #[test]
    fn rejects_unknown_forward_and_self_references_with_expression_paths() {
        for (source, kind) in [
            (
                "missing",
                SemanticErrorKind::UnknownIdentifier {
                    name: "missing".into(),
                },
            ),
            (
                "later",
                SemanticErrorKind::ForwardReference {
                    name: "later".into(),
                },
            ),
            (
                "current",
                SemanticErrorKind::SelfReference {
                    name: "current".into(),
                },
            ),
        ] {
            let variables = vec![
                variable("current", "implementation.variables[0]", source),
                variable("later", "implementation.variables[1]", "1"),
            ];
            let error = compile(&function(&[], variables)).unwrap_err();
            assert_eq!(error.kind, kind);
            assert_eq!(error.specification_path, "specs/functions/example.md");
            assert_eq!(error.function, "example");
            assert_eq!(error.implementation_path, "implementation.variables[0]");
            assert_eq!(
                error.span,
                crate::formula::Span {
                    start: 0,
                    end: source.len()
                }
            );
        }
    }

    #[test]
    fn repeated_expression_retains_both_source_locations() {
        use crate::formula::Span;

        let mut first = expression("implementation.variables[0].expr", "sqrt(x)");
        first.source_location = SourceLocation {
            line: 10,
            column: 4,
        };
        let mut later = expression("implementation.variables[1].expr", "1 + sqrt(x)");
        later.source_location = SourceLocation {
            line: 20,
            column: 6,
        };
        let raw = function(
            &["x"],
            vec![
                RawVariable {
                    name: "first".into(),
                    value: RawVariableValue::Expression(first),
                },
                RawVariable {
                    name: "later".into(),
                    value: RawVariableValue::Expression(later),
                },
            ],
        );
        let error = compile(&raw).unwrap_err();
        assert_eq!(
            error.source_location.as_deref(),
            Some(&SourceLocation {
                line: 10,
                column: 4
            })
        );
        assert_eq!(error.span, Span { start: 0, end: 7 });
        assert_eq!(
            error.kind,
            SemanticErrorKind::RepeatedExpression {
                specification_path: PathBuf::from("specs/functions/example.md"),
                location: SourceLocation {
                    line: 20,
                    column: 6
                },
                span: Span { start: 4, end: 11 },
            }
        );
    }

    #[test]
    fn rejects_duplicate_names() {
        let duplicate_input = function(&["x", "x"], Vec::new());
        assert!(
            compile(&duplicate_input)
                .unwrap_err()
                .to_string()
                .contains("duplicate name `x`")
        );
        let duplicate_variable = function(
            &[],
            vec![
                variable("x", "implementation.variables[0]", "1"),
                variable("x", "implementation.variables[1]", "1"),
            ],
        );
        assert!(
            compile(&duplicate_variable)
                .unwrap_err()
                .to_string()
                .contains("duplicate name `x`")
        );
    }

    #[test]
    fn rejects_unknown_functions_and_wrong_arities() {
        let unknown = function(
            &["x"],
            vec![variable("value", "implementation.variables[0]", "nope(x)")],
        );
        assert!(
            compile(&unknown)
                .unwrap_err()
                .to_string()
                .contains("unsupported function `nope`")
        );
        for source in [
            "sqrt(x, x)",
            "exp()",
            "ln(x, x)",
            "log10()",
            "abs(x, x)",
            "min(x)",
            "max(x, x, x)",
        ] {
            let raw = function(
                &["x"],
                vec![variable("value", "implementation.variables[0]", source)],
            );
            assert!(
                compile(&raw).unwrap_err().to_string().contains("expects"),
                "{source}"
            );
        }
    }
}
