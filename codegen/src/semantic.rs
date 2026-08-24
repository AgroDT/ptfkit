use std::{
    collections::{BTreeMap, HashMap},
    fmt,
};

use crate::{
    formula::{self, Span},
    model::{RawExpression, RawFunction, SourceLocation},
};

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Function {
    pub(crate) inputs: Vec<Input>,
    pub(crate) variables: Vec<Variable>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct Input {
    pub(crate) name: String,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Variable {
    pub(crate) name: String,
    pub(crate) expression: Expr,
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
    let mut inputs = BTreeMap::new();
    for (index, input) in raw.inputs.iter().enumerate() {
        insert_name(
            raw,
            &mut inputs,
            &input.name,
            "inputs",
            Span { start: 0, end: 0 },
        )?;
        debug_assert_eq!(inputs[&input.name], index);
    }

    validate_repeated_expressions(raw)?;

    let variable_names: BTreeMap<_, _> = raw
        .variables
        .iter()
        .enumerate()
        .map(|(index, variable)| (variable.name.as_str(), index))
        .collect();
    let mut variables = Vec::with_capacity(raw.variables.len());
    let mut scope = inputs;
    for (index, variable) in raw.variables.iter().enumerate() {
        if scope.contains_key(&variable.name) {
            return Err(error(
                raw,
                "variables",
                Span { start: 0, end: 0 },
                format!("duplicate name `{}`", variable.name),
            ));
        }
        let expression =
            compile_expression(raw, &variable.expression, &scope, &variable_names, index)?;
        scope.insert(variable.name.clone(), raw.inputs.len() + index);
        variables.push(Variable {
            name: variable.name.clone(),
            expression,
        });
    }

    Ok(Function {
        inputs: raw
            .inputs
            .iter()
            .map(|input| Input {
                name: input.name.clone(),
            })
            .collect(),
        variables,
    })
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
enum StructuralExpr {
    Number(String),
    Variable(String),
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
        let expression = &variable.expression;
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
        formula::ExprKind::Number(_) | formula::ExprKind::Variable(_) => None,
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
        formula::ExprKind::Number(_) | formula::ExprKind::Variable(_) => false,
    }
}

fn arithmetic_operation_count(expression: &formula::Expr) -> usize {
    match &expression.kind {
        formula::ExprKind::Number(_) | formula::ExprKind::Variable(_) => 0,
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

fn insert_name(
    raw: &RawFunction,
    names: &mut BTreeMap<String, usize>,
    name: &str,
    path: &str,
    span: Span,
) -> Result<(), Error> {
    if names.insert(name.to_owned(), names.len()).is_some() {
        return Err(error(raw, path, span, format!("duplicate name `{name}`")));
    }
    Ok(())
}

fn compile_expression(
    raw: &RawFunction,
    expression: &RawExpression,
    scope: &BTreeMap<String, usize>,
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
    scope: &BTreeMap<String, usize>,
    variable_names: &BTreeMap<&str, usize>,
    variable_index: usize,
) -> Result<Expr, Error> {
    match &expression.kind {
        formula::ExprKind::Number(number) => Ok(Expr::Number(Number {
            value: number.value,
            lexeme: number.lexeme.clone(),
        })),
        formula::ExprKind::Variable(name) => match scope.get(name) {
            Some(index) if *index < raw.inputs.len() => {
                Ok(Expr::Reference(Reference::Input(*index)))
            }
            Some(index) => Ok(Expr::Reference(Reference::Variable(
                *index - raw.inputs.len(),
            ))),
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
        model::{RawExpression, RawFunction, RawInput, RawVariable, SourceLocation},
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
                })
                .collect(),
            variables,
        }
    }

    #[test]
    fn compiles_variables() {
        let raw = function(
            &["x"],
            vec![RawVariable {
                name: "twice".into(),
                expression: expression("implementation.variables[0]", "x * 2"),
            }],
        );
        let compiled = compile(&raw).unwrap();
        assert!(matches!(
            compiled.variables[0].expression,
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
                RawVariable {
                    name: "first".into(),
                    expression: expression("implementation.variables[0]", "x + 1"),
                },
                RawVariable {
                    name: "second".into(),
                    expression: expression("implementation.variables[1]", "first * first"),
                },
            ],
        );
        let compiled = compile(&raw).unwrap();
        assert!(matches!(
            compiled.variables[1].expression,
            Expr::Binary { .. }
        ));
    }

    #[test]
    fn permits_repeated_simple_multiplication() {
        let raw = function(
            &["x", "y"],
            vec![
                RawVariable {
                    name: "first".into(),
                    expression: expression("implementation.variables[0].expr", "x * y"),
                },
                RawVariable {
                    name: "second".into(),
                    expression: expression("implementation.variables[1].expr", "x * y"),
                },
            ],
        );

        assert!(compile(&raw).is_ok());
    }

    #[test]
    fn rejects_repeated_power_with_both_expression_locations() {
        let mut raw = function(
            &["x"],
            vec![
                RawVariable {
                    name: "first".into(),
                    expression: expression("implementation.variables[0].expr", "x ^ 2"),
                },
                RawVariable {
                    name: "second".into(),
                    expression: expression("implementation.variables[1].expr", "x ^ 2"),
                },
            ],
        );
        raw.variables[1].expression.source_location = SourceLocation { line: 2, column: 3 };

        let error = compile(&raw).unwrap_err().to_string();
        assert!(
            error.contains("specs/functions/example.md:1:1..6"),
            "{error}"
        );
        assert!(
            error.contains("specs/functions/example.md:2:3..8"),
            "{error}"
        );
        assert!(
            error.contains("must be extracted into an earlier implementation variable"),
            "{error}"
        );
    }

    #[test]
    fn rejects_repeated_math_function_calls() {
        let raw = function(
            &["x"],
            vec![
                RawVariable {
                    name: "first".into(),
                    expression: expression("implementation.variables[0].expr", "sqrt(x)"),
                },
                RawVariable {
                    name: "second".into(),
                    expression: expression("implementation.variables[1].expr", "sqrt(x)"),
                },
            ],
        );

        assert!(
            compile(&raw)
                .unwrap_err()
                .to_string()
                .contains("must be extracted into an earlier implementation variable")
        );
    }

    #[test]
    fn rejects_repeated_compound_arithmetic_expressions() {
        let raw = function(
            &["x", "y", "z"],
            vec![
                RawVariable {
                    name: "first".into(),
                    expression: expression("implementation.variables[0].expr", "x + y * z"),
                },
                RawVariable {
                    name: "second".into(),
                    expression: expression("implementation.variables[1].expr", "x + y * z"),
                },
            ],
        );

        assert!(
            compile(&raw)
                .unwrap_err()
                .to_string()
                .contains("must be extracted into an earlier implementation variable")
        );
    }

    #[test]
    fn distinguishes_operand_order() {
        let raw = function(
            &["x", "y"],
            vec![
                RawVariable {
                    name: "first".into(),
                    expression: expression("implementation.variables[0].expr", "x / y"),
                },
                RawVariable {
                    name: "second".into(),
                    expression: expression("implementation.variables[1].expr", "y / x"),
                },
            ],
        );

        assert!(compile(&raw).is_ok());
    }

    #[test]
    fn permits_references_to_an_earlier_extracted_expression() {
        let raw = function(
            &["x"],
            vec![
                RawVariable {
                    name: "x_squared".into(),
                    expression: expression("implementation.variables[0].expr", "x ^ 2"),
                },
                RawVariable {
                    name: "first".into(),
                    expression: expression("implementation.variables[1].expr", "x_squared + 1"),
                },
                RawVariable {
                    name: "second".into(),
                    expression: expression("implementation.variables[2].expr", "x_squared + 2"),
                },
            ],
        );

        assert!(compile(&raw).is_ok());
    }

    #[test]
    fn rejects_unknown_forward_and_self_references_with_expression_paths() {
        for (source, expected) in [
            ("missing", "unknown identifier `missing`"),
            ("later", "cannot reference a later variable"),
            ("current", "cannot reference itself"),
        ] {
            let variables = vec![
                RawVariable {
                    name: "current".into(),
                    expression: expression("implementation.variables[0]", source),
                },
                RawVariable {
                    name: "later".into(),
                    expression: expression("implementation.variables[1]", "1"),
                },
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
                RawVariable {
                    name: "x".into(),
                    expression: expression("implementation.variables[0]", "1"),
                },
                RawVariable {
                    name: "x".into(),
                    expression: expression("implementation.variables[1]", "1"),
                },
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
            vec![RawVariable {
                name: "value".into(),
                expression: expression("implementation.variables[0]", "nope(x)"),
            }],
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
                vec![RawVariable {
                    name: "value".into(),
                    expression: expression("implementation.variables[0]", source),
                }],
            );
            assert!(
                compile(&raw).unwrap_err().to_string().contains("expects"),
                "{source}"
            );
        }
    }
}
