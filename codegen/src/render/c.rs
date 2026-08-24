use std::fmt;

use crate::semantic::{BinaryOp, Expr, MathFunction, Number, Reference, UnaryOp, Variable};

#[derive(Clone, Copy)]
pub(crate) enum Dialect {
    C,
    Cpp,
}

pub(crate) fn expression<'a>(
    value: &'a Expr,
    inputs: &'a [String],
    variables: &'a [Variable],
    dialect: Dialect,
) -> impl fmt::Display + 'a {
    Expression {
        expression: value,
        inputs,
        variables,
        dialect,
    }
}

pub(crate) fn float_literal(lexeme: &str) -> String {
    if lexeme.contains(['.', 'e', 'E']) {
        lexeme.to_owned()
    } else {
        format!("{lexeme}.0")
    }
}

pub(crate) fn test_float_literal(value: f64) -> String {
    float_literal(&value.to_string())
}

pub(crate) fn requires_math(expression: &Expr) -> bool {
    match expression {
        Expr::Number(_) | Expr::Reference(_) | Expr::Field { .. } => false,
        Expr::Unary { operand, .. } => requires_math(operand),
        Expr::Binary { op, left, right } => {
            (matches!(op, BinaryOp::Power) && small_integer_exponent(right).is_none())
                || requires_math(left)
                || requires_math(right)
        }
        Expr::Call { .. } => true,
    }
}

pub(crate) fn requires_pow4(expression: &Expr) -> bool {
    match expression {
        Expr::Number(_) | Expr::Reference(_) | Expr::Field { .. } => false,
        Expr::Unary { operand, .. } => requires_pow4(operand),
        Expr::Binary { op, left, right } => {
            (matches!(op, BinaryOp::Power) && small_integer_exponent(right) == Some(4))
                || requires_pow4(left)
                || requires_pow4(right)
        }
        Expr::Call { args, .. } => args.iter().any(requires_pow4),
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
            Expr::Field { record, field } => {
                let name = match record {
                    Reference::Input(index) => &self.inputs[*index],
                    Reference::Variable(index) => &self.variables[*index].name,
                };
                write!(formatter, "{name}.{field}")?
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
                    if small_integer_exponent(right) == Some(4) {
                        write!(formatter, "ptfkit_pow4(")?;
                        self.write_expression(formatter, left, None)?;
                        write!(formatter, ")")?;
                    } else if let Some(exponent) = small_integer_exponent(right) {
                        self.write_small_integer_power(formatter, left, exponent)?;
                    } else {
                        write!(formatter, "{}(", self.math_name("pow"))?;
                        self.write_expression(formatter, left, None)?;
                        write!(formatter, ", ")?;
                        self.write_expression(formatter, right, None)?;
                        write!(formatter, ")")?;
                    }
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

    fn write_small_integer_power(
        &self,
        formatter: &mut fmt::Formatter<'_>,
        base: &Expr,
        exponent: usize,
    ) -> fmt::Result {
        for index in 0..exponent {
            if index > 0 {
                write!(formatter, " * ")?;
            }
            self.write_expression(formatter, base, Some((Precedence::Product, index > 0)))?;
        }
        Ok(())
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
        Expr::Binary {
            op: BinaryOp::Power,
            right,
            ..
        } if small_integer_exponent(right).is_some() => Precedence::Product,
        Expr::Number(_)
        | Expr::Reference(_)
        | Expr::Field { .. }
        | Expr::Binary { .. }
        | Expr::Call { .. } => Precedence::Primary,
    }
}

fn small_integer_exponent(expression: &Expr) -> Option<usize> {
    let Expr::Number(Number { value, .. }) = expression else {
        return None;
    };
    match *value {
        2.0 => Some(2),
        3.0 => Some(3),
        4.0 => Some(4),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::semantic::{BinaryOp, Number, Reference};

    fn inputs() -> Vec<String> {
        vec!["x".into(), "y".into(), "z".into()]
    }

    fn input(index: usize) -> Expr {
        Expr::Reference(Reference::Input(index))
    }

    fn number(value: f64) -> Expr {
        Expr::Number(Number {
            value,
            lexeme: value.to_string(),
        })
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
            super::expression(&expression, &inputs(), &[], Dialect::C).to_string(),
            "x - (y - z)"
        );
        assert_eq!(
            super::expression(&expression, &inputs(), &[], Dialect::Cpp).to_string(),
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
            super::expression(&expression, &inputs(), &[], Dialect::C).to_string(),
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
            super::expression(&expression, &inputs(), &[], Dialect::C).to_string(),
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
            super::expression(&expression, &inputs(), &[], Dialect::C).to_string(),
            "fmin(pow(x + y, -z), sqrt(x * y))"
        );
        assert_eq!(
            super::expression(&expression, &inputs(), &[], Dialect::Cpp).to_string(),
            "std::fmin(std::pow(x + y, -z), std::sqrt(x * y))"
        );
    }

    #[test]
    fn renders_small_integer_powers_as_multiplication_for_all_c_dialects() {
        for (exponent, expected) in [(2.0, "x * x"), (3.0, "x * x * x"), (4.0, "ptfkit_pow4(x)")] {
            let expression = Expr::Binary {
                op: BinaryOp::Power,
                left: Box::new(input(0)),
                right: Box::new(number(exponent)),
            };
            assert_eq!(
                super::expression(&expression, &inputs(), &[], Dialect::C).to_string(),
                expected
            );
            assert_eq!(
                super::expression(&expression, &inputs(), &[], Dialect::Cpp).to_string(),
                expected
            );
            assert!(!requires_math(&expression));
            assert_eq!(requires_pow4(&expression), exponent == 4.0);
        }
    }

    #[test]
    fn parenthesizes_small_integer_powers_when_required_by_division() {
        let expression = Expr::Binary {
            op: BinaryOp::Divide,
            left: Box::new(input(0)),
            right: Box::new(Expr::Binary {
                op: BinaryOp::Power,
                left: Box::new(input(1)),
                right: Box::new(number(2.0)),
            }),
        };
        assert_eq!(
            super::expression(&expression, &inputs(), &[], Dialect::C).to_string(),
            "x / (y * y)"
        );
    }

    #[test]
    fn renders_record_field_access_for_native_dialects() {
        let expression = Expr::Field {
            record: Reference::Variable(0),
            field: "b".into(),
        };
        let variables = [Variable {
            name: "parameters".into(),
            value: crate::semantic::VariableValue::Number(Expr::Number(Number {
                value: 0.0,
                lexeme: "0.0".into(),
            })),
        }];

        assert_eq!(
            super::expression(&expression, &[], &variables, Dialect::C).to_string(),
            "parameters.b"
        );
        assert!(!requires_math(&expression));
        assert!(!requires_pow4(&expression));
    }
}
