use std::fmt;

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
) -> String {
    Expression {
        expression,
        inputs,
        variables,
        dialect,
    }
    .to_string()
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

struct Expression<'a> {
    expression: &'a Expr,
    inputs: &'a [String],
    variables: &'a [Variable],
    dialect: Dialect,
}

impl fmt::Display for Expression<'_> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.write_expression(formatter, self.expression, None)
    }
}

impl Expression<'_> {
    fn write_expression(
        &self,
        formatter: &mut fmt::Formatter<'_>,
        expression: &Expr,
        parent: Option<(Precedence, bool)>,
    ) -> fmt::Result {
        if let Expr::Unary {
            op: UnaryOp::Plus,
            operand,
        } = expression
        {
            return self.write_expression(formatter, operand, parent);
        }

        let precedence = precedence(expression);
        let parenthesize = parent.is_some_and(|(parent, is_right)| {
            precedence < parent || (is_right && precedence == parent)
        });
        if parenthesize {
            write!(formatter, "(")?;
        }

        match expression {
            Expr::Number(number) => write!(formatter, "{}", float_literal(&number.lexeme))?,
            Expr::Reference(Reference::Input(index)) => {
                write!(formatter, "{}", self.inputs[*index])?
            }
            Expr::Reference(Reference::Variable(index)) => {
                write!(formatter, "{}", self.variables[*index].name)?;
            }
            Expr::Unary { op, operand } => match op {
                UnaryOp::Plus => unreachable!("unary plus is handled before parenthesizing"),
                UnaryOp::Minus => {
                    write!(formatter, "-")?;
                    self.write_expression(formatter, operand, Some((Precedence::Unary, true)))?;
                }
            },
            Expr::Binary { op, left, right } => match op {
                BinaryOp::Add => self.write_binary(formatter, left, right, Precedence::Sum, "+")?,
                BinaryOp::Subtract => {
                    self.write_binary(formatter, left, right, Precedence::Sum, "-")?
                }
                BinaryOp::Multiply => {
                    self.write_binary(formatter, left, right, Precedence::Product, "*")?
                }
                BinaryOp::Divide => {
                    self.write_binary(formatter, left, right, Precedence::Product, "/")?
                }
                BinaryOp::Power => {
                    write!(formatter, "{}(", self.math_name("pow"))?;
                    self.write_expression(formatter, left, None)?;
                    write!(formatter, ", ")?;
                    self.write_expression(formatter, right, None)?;
                    write!(formatter, ")")?;
                }
            },
            Expr::Call { function, args } => {
                write!(formatter, "{}(", self.function_name(*function))?;
                for (index, argument) in args.iter().enumerate() {
                    if index > 0 {
                        write!(formatter, ", ")?;
                    }
                    self.write_expression(formatter, argument, None)?;
                }
                write!(formatter, ")")?;
            }
        }

        if parenthesize {
            write!(formatter, ")")?;
        }
        Ok(())
    }

    fn write_binary(
        &self,
        formatter: &mut fmt::Formatter<'_>,
        left: &Expr,
        right: &Expr,
        precedence: Precedence,
        operator: &str,
    ) -> fmt::Result {
        self.write_expression(formatter, left, Some((precedence, false)))?;
        write!(formatter, " {operator} ")?;
        self.write_expression(formatter, right, Some((precedence, true)))
    }

    fn function_name(&self, function: MathFunction) -> &'static str {
        match function {
            MathFunction::Sqrt => self.math_name("sqrt"),
            MathFunction::Exp => self.math_name("exp"),
            MathFunction::Ln => self.math_name("log"),
            MathFunction::Log10 => self.math_name("log10"),
            MathFunction::Abs if matches!(self.dialect, Dialect::Cpp) => "std::abs",
            MathFunction::Abs => self.math_name("fabs"),
            MathFunction::Min => self.math_name("fmin"),
            MathFunction::Max => self.math_name("fmax"),
        }
    }

    fn math_name(&self, name: &'static str) -> &'static str {
        match self.dialect {
            Dialect::C => name,
            Dialect::Cpp => match name {
                "sqrt" => "std::sqrt",
                "exp" => "std::exp",
                "log" => "std::log",
                "log10" => "std::log10",
                "fabs" => "std::fabs",
                "fmin" => "std::fmin",
                "fmax" => "std::fmax",
                "pow" => "std::pow",
                _ => unreachable!("unsupported C/C++ math function"),
            },
        }
    }
}

fn precedence(expression: &Expr) -> Precedence {
    match expression {
        Expr::Binary {
            op: BinaryOp::Add | BinaryOp::Subtract,
            ..
        } => Precedence::Sum,
        Expr::Binary {
            op: BinaryOp::Multiply | BinaryOp::Divide,
            ..
        } => Precedence::Product,
        Expr::Unary {
            op: UnaryOp::Minus, ..
        } => Precedence::Unary,
        Expr::Unary {
            op: UnaryOp::Plus,
            operand,
        } => precedence(operand),
        Expr::Number(_) | Expr::Reference(_) | Expr::Binary { .. } | Expr::Call { .. } => {
            Precedence::Primary
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::semantic::{BinaryOp, Reference};

    fn inputs() -> Vec<String> {
        vec!["x".into(), "y".into(), "z".into()]
    }

    fn input(index: usize) -> Expr {
        Expr::Reference(Reference::Input(index))
    }

    #[test]
    fn preserves_precedence_for_c_and_cpp() {
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
            render(&expression, &inputs(), &[], Dialect::C),
            "x - (y - z)"
        );
        assert_eq!(
            render(&expression, &inputs(), &[], Dialect::Cpp),
            "x - (y - z)"
        );
    }

    #[test]
    fn preserves_parentheses_in_nested_unary_and_binary_expressions() {
        let expression = Expr::Binary {
            op: BinaryOp::Divide,
            left: Box::new(Expr::Unary {
                op: UnaryOp::Minus,
                operand: Box::new(Expr::Binary {
                    op: BinaryOp::Add,
                    left: Box::new(input(0)),
                    right: Box::new(input(1)),
                }),
            }),
            right: Box::new(Expr::Binary {
                op: BinaryOp::Multiply,
                left: Box::new(input(2)),
                right: Box::new(Expr::Binary {
                    op: BinaryOp::Subtract,
                    left: Box::new(input(0)),
                    right: Box::new(input(1)),
                }),
            }),
        };

        assert_eq!(
            render(&expression, &inputs(), &[], Dialect::C),
            "-(x + y) / (z * (x - y))"
        );
    }

    #[test]
    fn unary_plus_preserves_the_operand_precedence() {
        let expression = Expr::Binary {
            op: BinaryOp::Multiply,
            left: Box::new(Expr::Unary {
                op: UnaryOp::Plus,
                operand: Box::new(Expr::Binary {
                    op: BinaryOp::Add,
                    left: Box::new(input(0)),
                    right: Box::new(input(1)),
                }),
            }),
            right: Box::new(input(2)),
        };

        assert_eq!(
            render(&expression, &inputs(), &[], Dialect::C),
            "(x + y) * z"
        );
    }

    #[test]
    fn renders_power_and_calls_with_dialect_local_math_names() {
        let expression = Expr::Call {
            function: MathFunction::Min,
            args: vec![
                Expr::Binary {
                    op: BinaryOp::Power,
                    left: Box::new(Expr::Binary {
                        op: BinaryOp::Add,
                        left: Box::new(input(0)),
                        right: Box::new(input(1)),
                    }),
                    right: Box::new(Expr::Unary {
                        op: UnaryOp::Minus,
                        operand: Box::new(input(2)),
                    }),
                },
                Expr::Call {
                    function: MathFunction::Sqrt,
                    args: vec![Expr::Binary {
                        op: BinaryOp::Multiply,
                        left: Box::new(input(0)),
                        right: Box::new(input(1)),
                    }],
                },
            ],
        };

        assert_eq!(
            render(&expression, &inputs(), &[], Dialect::C),
            "fmin(pow(x + y, -z), sqrt(x * y))"
        );
        assert_eq!(
            render(&expression, &inputs(), &[], Dialect::Cpp),
            "std::fmin(std::pow(x + y, -z), std::sqrt(x * y))"
        );
    }
}
