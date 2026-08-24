use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
};

use crate::{
    formula::{self, Span},
    model::{RawExpression, RawFunction},
};

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Function {
    pub(crate) inputs: Vec<Input>,
    pub(crate) derived_inputs: Vec<DerivedInput>,
    pub(crate) variables: Vec<Variable>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct Input {
    pub(crate) name: String,
    pub(crate) input_type: String,
    pub(crate) numeric: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct DerivedInput {
    pub(crate) adapter: String,
    pub(crate) source_input: usize,
    pub(crate) component: String,
    pub(crate) symbol: String,
    pub(crate) evidence: String,
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
    NumericInput(usize),
    DerivedInput(usize),
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
    message: String,
}

impl fmt::Display for Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
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
    let mut public_names = BTreeSet::new();
    let mut scope = BTreeMap::new();
    for (index, input) in raw.inputs.iter().enumerate() {
        if !public_names.insert(input.name.clone()) {
            return Err(error(
                raw,
                "inputs",
                Span { start: 0, end: 0 },
                format!("duplicate name `{}`", input.name),
            ));
        }
        if input.r#type.is_numeric() {
            scope.insert(input.name.clone(), Reference::NumericInput(index));
        }
    }
    for (index, derived) in raw.derived_inputs.iter().enumerate() {
        if public_names.contains(&derived.symbol) || scope.contains_key(&derived.symbol) {
            return Err(error(
                raw,
                "derived_inputs",
                Span { start: 0, end: 0 },
                format!("duplicate or colliding derived symbol `{}`", derived.symbol),
            ));
        }
        scope.insert(derived.symbol.clone(), Reference::DerivedInput(index));
    }

    let variable_names: BTreeMap<_, _> = raw
        .variables
        .iter()
        .enumerate()
        .map(|(index, variable)| (variable.name.as_str(), index))
        .collect();
    let mut variables = Vec::with_capacity(raw.variables.len());
    for (index, variable) in raw.variables.iter().enumerate() {
        if public_names.contains(&variable.name) || scope.contains_key(&variable.name) {
            return Err(error(
                raw,
                "variables",
                Span { start: 0, end: 0 },
                format!("duplicate name `{}`", variable.name),
            ));
        }
        let expression =
            compile_expression(raw, &variable.expression, &scope, &variable_names, index)?;
        scope.insert(variable.name.clone(), Reference::Variable(index));
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
                input_type: input.r#type.as_str().to_owned(),
                numeric: input.r#type.is_numeric(),
            })
            .collect(),
        derived_inputs: raw
            .derived_inputs
            .iter()
            .map(|binding| DerivedInput {
                adapter: binding.adapter.clone(),
                source_input: binding.input_index,
                component: binding.component.clone(),
                symbol: binding.symbol.clone(),
                evidence: binding.evidence.clone(),
            })
            .collect(),
        variables,
    })
}

fn compile_expression(
    raw: &RawFunction,
    expression: &RawExpression,
    scope: &BTreeMap<String, Reference>,
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
    scope: &BTreeMap<String, Reference>,
    variable_names: &BTreeMap<&str, usize>,
    variable_index: usize,
) -> Result<Expr, Error> {
    match &expression.kind {
        formula::ExprKind::Number(number) => Ok(Expr::Number(Number {
            value: number.value,
            lexeme: number.lexeme.clone(),
        })),
        formula::ExprKind::Variable(name) => match scope.get(name) {
            Some(reference) => Ok(Expr::Reference(*reference)),
            None => {
                let message = match variable_names.get(name.as_str()) {
                    Some(index) if *index == variable_index => {
                        format!("variable `{name}` cannot reference itself")
                    }
                    Some(index) if *index > variable_index => {
                        format!("variable `{name}` cannot reference a later variable")
                    }
                    _ if raw
                        .inputs
                        .iter()
                        .any(|input| input.name == *name && !input.r#type.is_numeric()) =>
                    {
                        format!(
                            "categorical input `{name}` cannot be used as a numeric formula symbol"
                        )
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
        model::{RawExpression, RawFunction, RawInput, RawVariable},
    };

    use super::{BinaryOp, Expr, compile};

    fn expression(path: &str, source: &str) -> RawExpression {
        RawExpression {
            implementation_path: path.into(),
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
                    r#type: crate::model::InputType::default(),
                })
                .collect(),
            derived_inputs: Vec::new(),
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
