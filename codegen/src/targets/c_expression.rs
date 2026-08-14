use anyhow::Result;

use crate::semantic::{BinaryOp, Expr, MathFunction, Reference, UnaryOp, Variable};

#[derive(Clone, Copy)]
pub(super) enum Dialect {
    C,
    Cpp,
}

pub(super) fn render(
    expression: &Expr,
    inputs: &[String],
    variables: &[Variable],
    dialect: Dialect,
) -> Result<String> {
    Ok(rendered(expression, inputs, variables, dialect)?.text)
}

pub(super) fn float_literal(lexeme: &str) -> String {
    if lexeme.contains(['.', 'e', 'E']) {
        lexeme.to_owned()
    } else {
        format!("{lexeme}.0")
    }
}

pub(super) fn test_float_literal(value: f64) -> String {
    float_literal(&value.to_string())
}

pub(super) fn requires_math(expression: &Expr) -> bool {
    match expression {
        Expr::Number(_) | Expr::Reference(_) => false,
        Expr::Unary { operand, .. } => requires_math(operand),
        Expr::Binary { op, left, right } => {
            matches!(op, BinaryOp::Power) || requires_math(left) || requires_math(right)
        }
        Expr::Call { .. } => true,
    }
}

#[derive(Clone, Copy, Eq, Ord, PartialEq, PartialOrd)]
enum Precedence {
    Sum,
    Product,
    Unary,
    Primary,
}

struct RenderedExpression {
    text: String,
    precedence: Precedence,
}

impl RenderedExpression {
    fn binary_operand(&self, parent: Precedence, is_right: bool) -> String {
        let needs_parentheses = self.precedence < parent || (is_right && self.precedence == parent);
        if needs_parentheses {
            format!("({})", self.text)
        } else {
            self.text.clone()
        }
    }

    fn unary_operand(&self) -> String {
        if self.precedence <= Precedence::Unary {
            format!("({})", self.text)
        } else {
            self.text.clone()
        }
    }
}

fn rendered(
    expression: &Expr,
    inputs: &[String],
    variables: &[Variable],
    dialect: Dialect,
) -> Result<RenderedExpression> {
    Ok(match expression {
        Expr::Number(number) => primary(float_literal(&number.lexeme)),
        Expr::Reference(Reference::Input(index)) => primary(inputs[*index].clone()),
        Expr::Reference(Reference::Variable(index)) => primary(variables[*index].name.clone()),
        Expr::Unary { op, operand } => match op {
            UnaryOp::Plus => rendered(operand, inputs, variables, dialect)?,
            UnaryOp::Minus => {
                let operand = rendered(operand, inputs, variables, dialect)?.unary_operand();
                RenderedExpression {
                    text: format!("-{operand}"),
                    precedence: Precedence::Unary,
                }
            }
        },
        Expr::Binary { op, left, right } => {
            let left = rendered(left, inputs, variables, dialect)?;
            let right = rendered(right, inputs, variables, dialect)?;
            match op {
                BinaryOp::Add => binary(left, right, Precedence::Sum, "+"),
                BinaryOp::Subtract => binary(left, right, Precedence::Sum, "-"),
                BinaryOp::Multiply => binary(left, right, Precedence::Product, "*"),
                BinaryOp::Divide => binary(left, right, Precedence::Product, "/"),
                BinaryOp::Power => primary(format!(
                    "{}({}, {})",
                    math_name("pow", dialect),
                    left.text,
                    right.text
                )),
            }
        }
        Expr::Call { function, args } => {
            let args = args
                .iter()
                .map(|arg| rendered(arg, inputs, variables, dialect))
                .collect::<Result<Vec<_>>>()?;
            let name = match function {
                MathFunction::Sqrt => "sqrt",
                MathFunction::Exp => "exp",
                MathFunction::Ln => "log",
                MathFunction::Log10 => "log10",
                MathFunction::Abs => "fabs",
                MathFunction::Min => "fmin",
                MathFunction::Max => "fmax",
            };
            let name = match (dialect, function) {
                (Dialect::Cpp, MathFunction::Abs) => "std::abs".to_owned(),
                _ => math_name(name, dialect),
            };
            primary(format!(
                "{name}({})",
                args.iter()
                    .map(|argument| argument.text.as_str())
                    .collect::<Vec<_>>()
                    .join(", ")
            ))
        }
    })
}

fn math_name(name: &str, dialect: Dialect) -> String {
    match dialect {
        Dialect::C => name.to_owned(),
        Dialect::Cpp => format!("std::{name}"),
    }
}

fn primary(text: String) -> RenderedExpression {
    RenderedExpression {
        text,
        precedence: Precedence::Primary,
    }
}

fn binary(
    left: RenderedExpression,
    right: RenderedExpression,
    precedence: Precedence,
    operator: &str,
) -> RenderedExpression {
    let left = left.binary_operand(precedence, false);
    let right = right.binary_operand(precedence, true);
    RenderedExpression {
        text: format!("{left} {operator} {right}"),
        precedence,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::semantic::{BinaryOp, Reference};

    #[test]
    fn preserves_precedence_for_c_and_cpp() {
        let inputs = vec!["x".into(), "y".into(), "z".into()];
        let variables = Vec::new();
        let input = |index| Expr::Reference(Reference::Input(index));
        let expression = Expr::Binary {
            op: BinaryOp::Subtract,
            left: Box::new(input(0)),
            right: Box::new(Expr::Binary {
                op: BinaryOp::Subtract,
                left: Box::new(input(1)),
                right: Box::new(input(2)),
            }),
        };

        assert_eq!(
            render(&expression, &inputs, &variables, Dialect::C).unwrap(),
            "x - (y - z)"
        );
        assert_eq!(
            render(&expression, &inputs, &variables, Dialect::Cpp).unwrap(),
            "x - (y - z)"
        );
    }

    #[test]
    fn selects_cpp_math_namespace() {
        let expression = Expr::Call {
            function: MathFunction::Sqrt,
            args: vec![Expr::Reference(Reference::Input(0))],
        };
        let inputs = vec!["x".into()];

        assert_eq!(
            render(&expression, &inputs, &[], Dialect::C).unwrap(),
            "sqrt(x)"
        );
        assert_eq!(
            render(&expression, &inputs, &[], Dialect::Cpp).unwrap(),
            "std::sqrt(x)"
        );
    }
}
