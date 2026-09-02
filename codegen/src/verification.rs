//! Scientific source intervals and target-independent numerical verification.

use std::collections::BTreeMap;

use anyhow::{Context, Result, bail};
use astro_float::{BigFloat, Consts, Radix, RoundingMode};

use crate::{
    model::{Acceptance, CompiledInput, Outputs, PublishedPrecision, Verification},
    semantic::{
        self, BinaryOp, Expr, MathFunction, Reference, ResultBinding, UnaryOp, VariableValue,
    },
};

/// Precision of the target-independent semantic evaluator.
pub(crate) const ORACLE_PRECISION_BITS: usize = 256;
const ROUNDING: RoundingMode = RoundingMode::ToEven;
const ELEMENTARY_ULPS: usize = 8;
const TRANSCENDENTAL_ULPS: usize = 64;

#[derive(Clone)]
enum Value {
    Number(BigFloat),
    Enum(String),
    Record(BTreeMap<String, BigFloat>),
}

pub(crate) fn oracle_outputs(
    ir: &semantic::Function,
    outputs: &Outputs,
    inputs: &[CompiledInput],
) -> Result<Vec<BigFloat>> {
    let mut constants = Consts::new().context("initializing high-precision constants")?;
    let mut values = inputs
        .iter()
        .map(|input| match input {
            CompiledInput::Number(value) => {
                Value::Number(BigFloat::from_f64(*value, ORACLE_PRECISION_BITS))
            }
            CompiledInput::Enum { member_name, .. } => Value::Enum(member_name.clone()),
        })
        .collect::<Vec<_>>();
    let input_count = values.len();

    for variable in &ir.variables {
        let value = match &variable.value {
            VariableValue::Number(expression) => {
                Value::Number(eval_expr(expression, &values, input_count, &mut constants)?)
            }
            VariableValue::RecordLookup(lookup) => {
                let key = reference(&values, input_count, lookup.key)?;
                let Value::Enum(member) = key else {
                    bail!("high-precision evaluator expected an enum lookup key")
                };
                let case = lookup
                    .cases
                    .iter()
                    .find(|case| case.member == *member)
                    .with_context(|| {
                        format!("high-precision evaluator found no lookup case for `{member}`")
                    })?;
                let fields = lookup
                    .output
                    .fields
                    .iter()
                    .zip(&case.values)
                    .map(|(field, value)| (field.clone(), decimal(&value.lexeme, &mut constants)))
                    .map(|(field, value)| value.map(|value| (field, value)))
                    .collect::<Result<BTreeMap<_, _>>>()?;
                Value::Record(fields)
            }
        };
        values.push(value);
    }

    match ir.result {
        ResultBinding::RecordVariable(index) => {
            let Value::Record(record) = &values[input_count + index] else {
                bail!("high-precision evaluator expected a record result")
            };
            outputs
                .fields()
                .iter()
                .map(|field| {
                    record.get(&field.name).cloned().with_context(|| {
                        format!(
                            "high-precision evaluator is missing output `{}`",
                            field.name
                        )
                    })
                })
                .collect()
        }
        ResultBinding::Fields => outputs
            .fields()
            .iter()
            .map(|field| {
                let value = ir
                    .inputs
                    .iter()
                    .position(|input| input.name == field.name)
                    .map(|index| &values[index])
                    .or_else(|| {
                        ir.variables
                            .iter()
                            .position(|variable| variable.name == field.name)
                            .map(|index| &values[input_count + index])
                    })
                    .with_context(|| {
                        format!(
                            "high-precision evaluator is missing output `{}`",
                            field.name
                        )
                    })?;
                let Value::Number(value) = value else {
                    bail!(
                        "high-precision evaluator output `{}` is not numeric",
                        field.name
                    )
                };
                Ok(value.clone())
            })
            .collect(),
    }
}

pub(crate) fn acceptance(
    verification: &Verification,
    nominal: Option<f64>,
    oracle: &BigFloat,
    ir: &semantic::Function,
) -> Result<Acceptance> {
    match verification {
        Verification::Exact => Ok(Acceptance::Exact(
            nominal.context("exact verification requires an expected value")?,
        )),
        Verification::CalculatedReference => {
            let center = to_f64(oracle)?;
            let acceptance = numeric_interval(center, numeric_ulps(ir));
            if let Some(stored) = nominal
                && !contains(acceptance, stored)
            {
                bail!(
                    "stored calculated reference {stored:?} is inconsistent with the 256-bit semantic result {center:?}"
                );
            }
            Ok(acceptance)
        }
        Verification::PublishedRounded { precision } => {
            let nominal =
                nominal.context("published rounded verification requires an expected value")?;
            let (lower, upper) = rounded_interval(nominal, *precision)?;
            Ok(expand_interval(lower, upper, numeric_ulps(ir)))
        }
        Verification::PublishedInterval { lower, upper } => {
            if !lower.is_finite() || !upper.is_finite() || lower > upper {
                bail!("published interval must have finite bounds with lower <= upper")
            }
            Ok(expand_interval(*lower, *upper, numeric_ulps(ir)))
        }
        Verification::PublishedUncertainty {
            value,
            absolute_uncertainty,
        } => {
            if !value.is_finite()
                || !absolute_uncertainty.is_finite()
                || *absolute_uncertainty <= 0.0
            {
                bail!(
                    "published uncertainty requires a finite value and positive finite absolute_uncertainty"
                )
            }
            Ok(expand_interval(
                value - absolute_uncertainty,
                value + absolute_uncertainty,
                numeric_ulps(ir),
            ))
        }
    }
}

pub(crate) fn rounded_interval(nominal: f64, precision: PublishedPrecision) -> Result<(f64, f64)> {
    if !nominal.is_finite() {
        bail!("published rounded value must be finite")
    }
    let nominal_f64 = nominal;
    let mut constants = Consts::new().context("initializing high-precision constants")?;
    let nominal = BigFloat::from_f64(nominal, ORACLE_PRECISION_BITS);
    let step = match precision {
        PublishedPrecision::DecimalPlaces { decimal_places } => {
            power_of_ten(-(decimal_places as i32), &mut constants)?
        }
        PublishedPrecision::SignificantDigits { significant_digits } => {
            if nominal_f64 == 0.0 {
                bail!(
                    "significant digits are ambiguous for zero; use decimal_places or an explicit interval"
                )
            }
            let exponent = nominal_f64.abs().log10().floor() as i32;
            power_of_ten(exponent - significant_digits as i32 + 1, &mut constants)?
        }
    };
    let two = BigFloat::from_u8(2, ORACLE_PRECISION_BITS);
    let half = step.div(&two, ORACLE_PRECISION_BITS, ROUNDING);
    let lower = to_f64(&nominal.sub(&half, ORACLE_PRECISION_BITS, ROUNDING))?;
    let upper = to_f64(&nominal.add(&half, ORACLE_PRECISION_BITS, ROUNDING))?;
    // Convert decimal boundaries outward; endpoints are included because a publication
    // normally does not document how exact ties were broken.
    Ok((next_down(lower), next_up(upper)))
}

fn eval_expr(
    expression: &Expr,
    values: &[Value],
    input_count: usize,
    constants: &mut Consts,
) -> Result<BigFloat> {
    match expression {
        Expr::Number(number) => decimal(&number.lexeme, constants),
        Expr::Reference(reference_) => {
            number(reference(values, input_count, *reference_)?, "reference")
        }
        Expr::Field { record, field } => {
            let Value::Record(record) = reference(values, input_count, *record)? else {
                bail!("high-precision evaluator expected a record reference")
            };
            record.get(field).cloned().with_context(|| {
                format!("high-precision evaluator found no record field `{field}`")
            })
        }
        Expr::Unary { op, operand } => {
            let value = eval_expr(operand, values, input_count, constants)?;
            Ok(match op {
                UnaryOp::Plus => value,
                UnaryOp::Minus => -value,
            })
        }
        Expr::Binary { op, left, right } => {
            let left = eval_expr(left, values, input_count, constants)?;
            let right = eval_expr(right, values, input_count, constants)?;
            Ok(match op {
                BinaryOp::Add => left.add(&right, ORACLE_PRECISION_BITS, ROUNDING),
                BinaryOp::Subtract => left.sub(&right, ORACLE_PRECISION_BITS, ROUNDING),
                BinaryOp::Multiply => left.mul(&right, ORACLE_PRECISION_BITS, ROUNDING),
                BinaryOp::Divide => left.div(&right, ORACLE_PRECISION_BITS, ROUNDING),
                BinaryOp::Power => {
                    let exponent = to_f64(&right)?;
                    if right.is_int()
                        && exponent.is_finite()
                        && exponent >= isize::MIN as f64
                        && exponent <= isize::MAX as f64
                    {
                        let exponent = exponent as isize;
                        let powered =
                            left.powi(exponent.unsigned_abs(), ORACLE_PRECISION_BITS, ROUNDING);
                        if exponent < 0 {
                            powered.reciprocal(ORACLE_PRECISION_BITS, ROUNDING)
                        } else {
                            powered
                        }
                    } else {
                        left.pow(&right, ORACLE_PRECISION_BITS, ROUNDING, constants)
                    }
                }
            })
        }
        Expr::Call { function, args } => {
            let mut args = args
                .iter()
                .map(|argument| eval_expr(argument, values, input_count, constants))
                .collect::<Result<Vec<_>>>()?;
            let first = args.remove(0);
            Ok(match function {
                MathFunction::Sqrt => first.sqrt(ORACLE_PRECISION_BITS, ROUNDING),
                MathFunction::Exp => first.exp(ORACLE_PRECISION_BITS, ROUNDING, constants),
                MathFunction::Ln => first.ln(ORACLE_PRECISION_BITS, ROUNDING, constants),
                MathFunction::Log10 => first.log10(ORACLE_PRECISION_BITS, ROUNDING, constants),
                MathFunction::Abs => first.abs(),
                MathFunction::Min => first.min(&args[0]),
                MathFunction::Max => first.max(&args[0]),
            })
        }
    }
}

fn reference(values: &[Value], input_count: usize, reference: Reference) -> Result<&Value> {
    let index = match reference {
        Reference::Input(index) => index,
        Reference::Variable(index) => input_count + index,
    };
    values
        .get(index)
        .context("high-precision evaluator found an unresolved reference")
}

fn number(value: &Value, description: &str) -> Result<BigFloat> {
    match value {
        Value::Number(value) => Ok(value.clone()),
        Value::Enum(_) | Value::Record(_) => {
            bail!("high-precision evaluator expected a numeric {description}")
        }
    }
}

fn decimal(lexeme: &str, constants: &mut Consts) -> Result<BigFloat> {
    let value = BigFloat::parse(
        lexeme,
        Radix::Dec,
        ORACLE_PRECISION_BITS,
        ROUNDING,
        constants,
    );
    if value.is_nan() {
        bail!(
            "parsing high-precision decimal `{lexeme}` failed: {:?}",
            value.err()
        )
    }
    Ok(value)
}

fn power_of_ten(exponent: i32, constants: &mut Consts) -> Result<BigFloat> {
    let ten = BigFloat::from_u8(10, ORACLE_PRECISION_BITS);
    let exponent = BigFloat::from_i32(exponent, ORACLE_PRECISION_BITS);
    Ok(ten.pow(&exponent, ORACLE_PRECISION_BITS, ROUNDING, constants))
}

fn to_f64(value: &BigFloat) -> Result<f64> {
    value
        .to_string()
        .parse()
        .with_context(|| format!("converting high-precision result `{value}` to f64"))
}

fn numeric_ulps(ir: &semantic::Function) -> usize {
    if ir.variables.iter().any(|variable| match &variable.value {
        VariableValue::Number(expression) => has_transcendental(expression),
        VariableValue::RecordLookup(_) => false,
    }) {
        TRANSCENDENTAL_ULPS
    } else {
        ELEMENTARY_ULPS
    }
}

fn has_transcendental(expression: &Expr) -> bool {
    match expression {
        Expr::Number(_) | Expr::Reference(_) | Expr::Field { .. } => false,
        Expr::Unary { operand, .. } => has_transcendental(operand),
        Expr::Binary { op, left, right } => {
            matches!(op, BinaryOp::Power) || has_transcendental(left) || has_transcendental(right)
        }
        Expr::Call { function, args } => {
            matches!(
                function,
                MathFunction::Sqrt | MathFunction::Exp | MathFunction::Ln | MathFunction::Log10
            ) || args.iter().any(has_transcendental)
        }
    }
}

fn numeric_interval(center: f64, ulps: usize) -> Acceptance {
    expand_interval(center, center, ulps)
}

fn expand_interval(mut lower: f64, mut upper: f64, ulps: usize) -> Acceptance {
    for _ in 0..ulps {
        lower = next_down(lower);
        upper = next_up(upper);
    }
    Acceptance::Interval { lower, upper }
}

fn contains(acceptance: Acceptance, value: f64) -> bool {
    match acceptance {
        Acceptance::Exact(expected) => value == expected,
        Acceptance::Interval { lower, upper } => value >= lower && value <= upper,
    }
}

fn next_up(value: f64) -> f64 {
    if value.is_nan() || value == f64::INFINITY {
        return value;
    }
    if value == 0.0 {
        return f64::from_bits(1);
    }
    f64::from_bits(if value > 0.0 {
        value.to_bits() + 1
    } else {
        value.to_bits() - 1
    })
}

fn next_down(value: f64) -> f64 {
    if value.is_nan() || value == f64::NEG_INFINITY {
        return value;
    }
    if value == 0.0 {
        return f64::from_bits((1_u64 << 63) | 1);
    }
    f64::from_bits(if value > 0.0 {
        value.to_bits() - 1
    } else {
        value.to_bits() + 1
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn literal(value: &str) -> Expr {
        Expr::Number(semantic::Number {
            value: value.parse().unwrap(),
            lexeme: value.into(),
        })
    }

    fn binary(op: BinaryOp, left: Expr, right: Expr) -> Expr {
        Expr::Binary {
            op,
            left: Box::new(left),
            right: Box::new(right),
        }
    }

    #[test]
    fn decimal_place_intervals_cover_positive_negative_and_zero() {
        let precision = PublishedPrecision::DecimalPlaces { decimal_places: 2 };
        let (lower, upper) = rounded_interval(1.24, precision).unwrap();
        assert!(lower <= 1.235 && upper >= 1.245);
        let (lower, upper) = rounded_interval(
            -2.5,
            PublishedPrecision::DecimalPlaces { decimal_places: 1 },
        )
        .unwrap();
        assert!(lower <= -2.55 && upper >= -2.45);
        let (lower, upper) =
            rounded_interval(0.0, PublishedPrecision::DecimalPlaces { decimal_places: 1 }).unwrap();
        assert!(lower <= -0.05 && upper >= 0.05);
    }

    #[test]
    fn significant_digit_interval_handles_scientific_notation() {
        let (lower, upper) = rounded_interval(
            0.00340,
            PublishedPrecision::SignificantDigits {
                significant_digits: 3,
            },
        )
        .unwrap();
        assert!(lower <= 0.003395 && upper >= 0.003405);
    }

    #[test]
    fn significant_digits_reject_zero() {
        assert!(
            rounded_interval(
                0.0,
                PublishedPrecision::SignificantDigits {
                    significant_digits: 3
                }
            )
            .is_err()
        );
    }

    #[test]
    fn ulp_expansion_is_narrow_and_deterministic() {
        let Acceptance::Interval { lower, upper } = numeric_interval(1.0, 1) else {
            unreachable!()
        };
        assert_eq!(lower, f64::from_bits(1.0_f64.to_bits() - 1));
        assert_eq!(upper, f64::from_bits(1.0_f64.to_bits() + 1));
        assert!(!(2.0 >= lower && 2.0 <= upper));
    }

    #[test]
    fn high_precision_evaluator_covers_arithmetic_power_logarithm_and_exponential() {
        let mut constants = Consts::new().unwrap();
        let arithmetic = binary(
            BinaryOp::Divide,
            binary(
                BinaryOp::Multiply,
                binary(BinaryOp::Add, literal("2"), literal("3")),
                literal("4"),
            ),
            literal("2"),
        );
        assert_eq!(
            to_f64(&eval_expr(&arithmetic, &[], 0, &mut constants).unwrap()).unwrap(),
            10.0
        );

        let power = binary(BinaryOp::Power, literal("2"), literal("8"));
        assert_eq!(
            to_f64(&eval_expr(&power, &[], 0, &mut constants).unwrap()).unwrap(),
            256.0
        );

        let exp = Expr::Call {
            function: MathFunction::Exp,
            args: vec![literal("1")],
        };
        let ln_exp = Expr::Call {
            function: MathFunction::Ln,
            args: vec![exp],
        };
        let result = to_f64(&eval_expr(&ln_exp, &[], 0, &mut constants).unwrap()).unwrap();
        assert!((result - 1.0).abs() < 1e-15);

        let log10 = Expr::Call {
            function: MathFunction::Log10,
            args: vec![literal("1000")],
        };
        assert_eq!(
            to_f64(&eval_expr(&log10, &[], 0, &mut constants).unwrap()).unwrap(),
            3.0
        );
    }

    #[test]
    fn exact_policy_does_not_accept_approximate_values() {
        assert!(contains(Acceptance::Exact(1.0), 1.0));
        assert!(!contains(Acceptance::Exact(1.0), next_up(1.0)));
    }

    #[test]
    fn source_interval_dominates_numeric_expansion() {
        let acceptance = expand_interval(1.20, 1.30, ELEMENTARY_ULPS);
        let Acceptance::Interval { lower, upper } = acceptance else {
            unreachable!()
        };
        assert!(lower < 1.20 && upper > 1.30);
        assert!(upper - lower > 0.099);
    }
}
