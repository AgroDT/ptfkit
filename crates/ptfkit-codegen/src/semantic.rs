#![expect(
    dead_code,
    reason = "Session 04 wires semantic compilation into the versioned specification loader."
)]

use std::{collections::BTreeMap, fmt};

use crate::{
    formula::{self, Span},
    model::{RawExpression, RawField, RawFunction, RawOutput},
};

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Function {
    pub(crate) inputs: Vec<Input>,
    pub(crate) variables: Vec<Variable>,
    pub(crate) output: Output,
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
pub(crate) enum Output {
    Scalar(Expr),
    Record(Vec<Field>),
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Field {
    pub(crate) name: String,
    pub(crate) expression: Expr,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum Expr {
    Number(f64),
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

    let output = match &raw.output {
        RawOutput::Scalar(expression) => Output::Scalar(compile_expression(
            raw,
            expression,
            &scope,
            &variable_names,
            raw.variables.len(),
        )?),
        RawOutput::Record(fields) => {
            Output::Record(compile_fields(raw, fields, &scope, &variable_names)?)
        }
    };
    Ok(Function {
        inputs: raw
            .inputs
            .iter()
            .map(|input| Input {
                name: input.name.clone(),
            })
            .collect(),
        variables,
        output,
    })
}

fn compile_fields(
    raw: &RawFunction,
    fields: &[RawField],
    scope: &BTreeMap<String, usize>,
    variable_names: &BTreeMap<&str, usize>,
) -> Result<Vec<Field>, Error> {
    if fields.is_empty() {
        return Err(error(
            raw,
            "output.fields",
            Span { start: 0, end: 0 },
            "record output must contain at least one field",
        ));
    }
    let mut names = BTreeMap::new();
    let mut compiled = Vec::with_capacity(fields.len());
    for field in fields {
        insert_name(
            raw,
            &mut names,
            &field.name,
            "output.fields",
            Span { start: 0, end: 0 },
        )?;
        compiled.push(Field {
            name: field.name.clone(),
            expression: compile_expression(
                raw,
                &field.expression,
                scope,
                variable_names,
                raw.variables.len(),
            )?,
        });
    }
    Ok(compiled)
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
        formula::ExprKind::Number(value) => Ok(Expr::Number(*value)),
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
        model::{RawExpression, RawField, RawFunction, RawInput, RawOutput, RawVariable},
    };

    use super::{BinaryOp, Expr, MathFunction, Output, Reference, compile};

    fn expression(path: &str, source: &str) -> RawExpression {
        RawExpression {
            implementation_path: path.into(),
            expression: parse(path, source).unwrap(),
        }
    }

    fn function(inputs: &[&str], variables: Vec<RawVariable>, output: RawOutput) -> RawFunction {
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
            output,
        }
    }

    #[test]
    fn compiles_scalar_and_record_outputs() {
        let scalar = function(
            &["x"],
            vec![RawVariable {
                name: "twice".into(),
                expression: expression("implementation.variables[0]", "x * 2"),
            }],
            RawOutput::Scalar(expression("implementation.output", "sqrt(twice)")),
        );
        let compiled = compile(&scalar).unwrap();
        assert!(matches!(
            compiled.variables[0].expression,
            Expr::Binary {
                op: BinaryOp::Multiply,
                ..
            }
        ));
        assert!(matches!(
            compiled.output,
            Output::Scalar(Expr::Call {
                function: MathFunction::Sqrt,
                ..
            })
        ));

        let record = function(
            &["x"],
            Vec::new(),
            RawOutput::Record(vec![
                RawField {
                    name: "first".into(),
                    expression: expression("implementation.output.fields[0]", "x"),
                },
                RawField {
                    name: "second".into(),
                    expression: expression("implementation.output.fields[1]", "x + 1"),
                },
            ]),
        );
        let compiled = compile(&record).unwrap();
        let Output::Record(fields) = compiled.output else {
            panic!("expected record output")
        };
        assert_eq!(fields.len(), 2);
        assert!(matches!(
            fields[0].expression,
            Expr::Reference(Reference::Input(0))
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
            RawOutput::Scalar(expression("implementation.output", "second")),
        );
        let compiled = compile(&raw).unwrap();
        assert!(matches!(
            compiled.variables[1].expression,
            Expr::Binary { .. }
        ));
        assert!(matches!(
            compiled.output,
            Output::Scalar(Expr::Reference(Reference::Variable(1)))
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
            let error = compile(&function(
                &[],
                variables,
                RawOutput::Scalar(expression("implementation.output", "1")),
            ))
            .unwrap_err();
            assert!(error.to_string().contains(expected), "{error}");
            assert!(error.to_string().contains(
                "specs/functions/example.md -> function example -> implementation.variables[0]:0.."
            ));
        }
    }

    #[test]
    fn rejects_duplicate_names_and_empty_or_duplicate_record_fields() {
        let duplicate_input = function(
            &["x", "x"],
            Vec::new(),
            RawOutput::Scalar(expression("implementation.output", "x")),
        );
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
            RawOutput::Scalar(expression("implementation.output", "x")),
        );
        assert!(
            compile(&duplicate_variable)
                .unwrap_err()
                .to_string()
                .contains("duplicate name `x`")
        );
        let empty_record = function(&[], Vec::new(), RawOutput::Record(Vec::new()));
        assert!(
            compile(&empty_record)
                .unwrap_err()
                .to_string()
                .contains("at least one field")
        );
        let duplicate_field = function(
            &[],
            Vec::new(),
            RawOutput::Record(vec![
                RawField {
                    name: "x".into(),
                    expression: expression("implementation.output.fields[0]", "1"),
                },
                RawField {
                    name: "x".into(),
                    expression: expression("implementation.output.fields[1]", "2"),
                },
            ]),
        );
        assert!(
            compile(&duplicate_field)
                .unwrap_err()
                .to_string()
                .contains("duplicate name `x`")
        );
    }

    #[test]
    fn rejects_unknown_functions_and_wrong_arities() {
        let unknown = function(
            &["x"],
            Vec::new(),
            RawOutput::Scalar(expression("implementation.output", "nope(x)")),
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
                Vec::new(),
                RawOutput::Scalar(expression("implementation.output", source)),
            );
            assert!(
                compile(&raw).unwrap_err().to_string().contains("expects"),
                "{source}"
            );
        }
    }

    #[test]
    fn validates_final_output_scope() {
        let raw = function(
            &["x"],
            Vec::new(),
            RawOutput::Scalar(expression("implementation.output", "missing + x")),
        );
        let error = compile(&raw).unwrap_err();
        assert!(error.to_string().contains("implementation.output:0..7"));
        assert!(error.to_string().contains("unknown identifier `missing`"));
    }

    #[test]
    fn ir_uses_closed_enums_for_operators_and_functions() {
        let raw = function(
            &["x"],
            Vec::new(),
            RawOutput::Scalar(expression("implementation.output", "max(-x, log10(x))")),
        );
        let compiled = compile(&raw).unwrap();
        let Output::Scalar(Expr::Call { function, args }) = compiled.output else {
            panic!("expected call")
        };
        assert_eq!(function, MathFunction::Max);
        assert_eq!(args.len(), 2);
    }
}
