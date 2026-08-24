use std::{
    collections::{BTreeMap, HashMap},
    fmt,
};

use crate::{
    formula::{self, Span},
    model::{
        RawExpression, RawFunction, RawInputType, RawLookup, RawVariableValue, SourceLocation,
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
    Enum(String),
    Record(RecordType),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct RecordType {
    pub(crate) name: String,
    pub(crate) fields: Vec<String>,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum VariableValue {
    Number(Expr),
    RecordLookup(RecordLookup),
}

impl VariableValue {
    pub(crate) fn as_number(&self) -> Option<&Expr> {
        match self {
            Self::Number(expression) => Some(expression),
            Self::RecordLookup(_) => None,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct RecordLookup {
    pub(crate) key: Reference,
    pub(crate) enum_name: String,
    pub(crate) output: RecordType,
    pub(crate) cases: Vec<RecordLookupCase>,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct RecordLookupCase {
    pub(crate) member: String,
    pub(crate) values: Vec<Number>,
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

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct Error {
    pub(crate) specification_path: String,
    pub(crate) function: String,
    pub(crate) implementation_path: String,
    pub(crate) span: Span,
    source_location: Option<Box<SourceLocation>>,
    message: String,
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
                self.message,
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
            self.message,
        )
    }
}

impl std::error::Error for Error {}

pub(crate) fn compile(raw: &RawFunction) -> Result<Function, Error> {
    let mut scope = BTreeMap::new();
    for (index, input) in raw.inputs.iter().enumerate() {
        let value_type = match &input.value_type {
            RawInputType::Number => ValueType::Number,
            RawInputType::Enum(definition) => ValueType::Enum(definition.name.clone()),
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
            return Err(error(
                raw,
                "inputs",
                Span { start: 0, end: 0 },
                format!("duplicate name `{}`", input.name),
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
            return Err(error(
                raw,
                "variables",
                Span { start: 0, end: 0 },
                format!("duplicate name `{}`", variable.name),
            ));
        }
        let (value, value_type) = match &variable.value {
            RawVariableValue::Expression(expression) => (
                VariableValue::Number(compile_expression(
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
                    RawInputType::Enum(definition) => ValueType::Enum(definition.name.clone()),
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

fn validate_repeated_expressions(raw: &RawFunction) -> Result<(), Error> {
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
            return Err(source_error(
                raw,
                first.source_location,
                first.span,
                format!(
                    "expression is repeated at {}:{}:{}..{}; it must be extracted into an earlier implementation variable",
                    raw.specification_path.display(),
                    later.source_location.line,
                    later.source_location.column + later.span.start,
                    later.source_location.column + later.span.end,
                ),
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
) -> Result<(RecordLookup, RecordType), Error> {
    let binding = scope.get(&lookup.key).ok_or_else(|| {
        error(
            raw,
            &lookup.implementation_path,
            Span { start: 0, end: 0 },
            format!("unknown lookup key `{}`", lookup.key),
        )
    })?;
    let enum_type = lookup
        .definition
        .input_type
        .as_ref()
        .expect("lookup input type is resolved");
    if binding.value_type != ValueType::Enum(enum_type.name.clone()) {
        return Err(error(
            raw,
            &lookup.implementation_path,
            Span { start: 0, end: 0 },
            format!(
                "lookup key `{}` must have enum type `{}`",
                lookup.key, enum_type.name
            ),
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
    let cases = lookup
        .definition
        .values
        .iter()
        .map(|case| RecordLookupCase {
            member: case.key.clone(),
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
        })
        .collect();
    Ok((
        RecordLookup {
            key: binding.reference,
            enum_name: enum_type.name.clone(),
            output: record_type.clone(),
            cases,
        },
        record_type,
    ))
}

fn compile_expression(
    raw: &RawFunction,
    expression: &RawExpression,
    scope: &BTreeMap<String, Binding>,
    variable_names: &BTreeMap<&str, usize>,
    variable_index: usize,
) -> Result<Expr, Error> {
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
) -> Result<Expr, Error> {
    match &expression.kind {
        formula::ExprKind::Number(number) => Ok(Expr::Number(Number {
            value: number.value,
            lexeme: number.lexeme.clone(),
        })),
        formula::ExprKind::Variable(name) => match scope.get(name) {
            Some(binding) if binding.value_type == ValueType::Number => {
                Ok(Expr::Reference(binding.reference))
            }
            Some(_) => Err(expression_error(
                raw,
                source,
                expression.span,
                format!("identifier `{name}` is not numeric"),
            )),
            None => {
                let message = match variable_names.get(name.as_str()) {
                    Some(index) if *index == variable_index => {
                        format!("variable `{name}` cannot reference itself")
                    }
                    Some(index) if *index > variable_index => {
                        format!("variable `{name}` cannot reference a later variable")
                    }
                    _ => format!("unknown identifier `{name}`"),
                };
                Err(expression_error(raw, source, expression.span, message))
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
            }) => Err(expression_error(
                raw,
                source,
                expression.span,
                format!("record `{}` has no field `{field}`", record.name),
            )),
            Some(_) => Err(expression_error(
                raw,
                source,
                expression.span,
                format!("`{base}` is not a record"),
            )),
            None => Err(expression_error(
                raw,
                source,
                expression.span,
                format!("unknown identifier `{base}`"),
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
                expression_error(
                    raw,
                    source,
                    expression.span,
                    format!("unsupported function `{name}`"),
                )
            })?;
            if args.len() != function.arity() {
                return Err(expression_error(
                    raw,
                    source,
                    expression.span,
                    format!(
                        "function `{name}` expects {} argument(s), found {}",
                        function.arity(),
                        args.len()
                    ),
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

fn error(
    raw: &RawFunction,
    implementation_path: &str,
    span: Span,
    message: impl Into<String>,
) -> Error {
    Error {
        specification_path: raw.specification_path.display().to_string(),
        function: raw.name.clone(),
        implementation_path: implementation_path.to_owned(),
        span,
        source_location: None,
        message: message.into(),
    }
}

fn source_error(
    raw: &RawFunction,
    source_location: SourceLocation,
    span: Span,
    message: impl Into<String>,
) -> Error {
    Error {
        specification_path: raw.specification_path.display().to_string(),
        function: raw.name.clone(),
        implementation_path: String::new(),
        span,
        source_location: Some(Box::new(source_location)),
        message: message.into(),
    }
}

fn expression_error(
    raw: &RawFunction,
    expression: &RawExpression,
    span: Span,
    message: impl Into<String>,
) -> Error {
    error(raw, &expression.implementation_path, span, message)
}

#[cfg(test)]
mod tests {
    use std::path::PathBuf;

    use crate::{
        formula::parse,
        model::{
            RawExpression, RawFunction, RawInput, RawInputType, RawVariable, RawVariableValue,
            SourceLocation,
        },
    };

    use super::{BinaryOp, Expr, compile};

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
    fn compiles_variables() {
        let raw = function(
            &["x"],
            vec![variable("twice", "implementation.variables[0]", "x * 2")],
        );
        let compiled = compile(&raw).unwrap();
        assert!(matches!(
            compiled.variables[0].value.as_number().unwrap(),
            Expr::Binary {
                op: BinaryOp::Multiply,
                ..
            }
        ));
    }

    #[test]
    fn resolves_ordered_variables_and_reuses_prior_values() {
        let raw = function(
            &["x"],
            vec![
                variable("first", "implementation.variables[0]", "x + 1"),
                variable("second", "implementation.variables[1]", "first * first"),
            ],
        );
        let compiled = compile(&raw).unwrap();
        assert!(matches!(
            compiled.variables[1].value.as_number().unwrap(),
            Expr::Binary { .. }
        ));
    }

    #[test]
    fn rejects_unknown_forward_and_self_references_with_expression_paths() {
        for (source, expected) in [
            ("missing", "unknown identifier `missing`"),
            ("later", "cannot reference a later variable"),
            ("current", "cannot reference itself"),
        ] {
            let variables = vec![
                variable("current", "implementation.variables[0]", source),
                variable("later", "implementation.variables[1]", "1"),
            ];
            let error = compile(&function(&[], variables)).unwrap_err();
            assert!(error.to_string().contains(expected), "{error}");
            assert!(error.to_string().contains(
                "specs/functions/example.md -> function example -> implementation.variables[0]:0.."
            ));
        }
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
