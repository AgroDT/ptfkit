use std::fmt;

use pest::{Parser, error::ErrorVariant, iterators::Pair};
use pest_derive::Parser;

#[derive(Parser)]
#[grammar = "formula.pest"]
struct FormulaParser;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct Span {
    pub(crate) start: usize,
    pub(crate) end: usize,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Expr {
    pub(crate) kind: ExprKind,
    pub(crate) span: Span,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) struct Number {
    pub(crate) value: f64,
    pub(crate) lexeme: String,
}

#[derive(Clone, Debug, PartialEq)]
pub(crate) enum ExprKind {
    Number(Number),
    Variable(String),
    Field {
        base: String,
        field: String,
    },
    Unary {
        op: UnaryOp,
        operand: Box<Expr>,
    },
    Binary {
        op: BinaryOp,
        left: Box<Expr>,
        right: Box<Expr>,
    },
    Call {
        name: String,
        args: Vec<Expr>,
    },
    Grouped(Box<Expr>),
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub(crate) enum UnaryOp {
    Plus,
    Minus,
}

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub(crate) enum BinaryOp {
    Add,
    Subtract,
    Multiply,
    Divide,
    Power,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct ParseError {
    pub(crate) location: String,
    pub(crate) span: Span,
    expected: Vec<&'static str>,
}

impl fmt::Display for ParseError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "{}:{}..{}: expected {}",
            self.location,
            self.span.start,
            self.span.end,
            self.expected.join(" or ")
        )
    }
}

impl std::error::Error for ParseError {}

pub(crate) fn parse(location: impl Into<String>, source: &str) -> Result<Expr, ParseError> {
    let location = location.into();
    let mut pairs = FormulaParser::parse(Rule::program, source)
        .map_err(|error| parse_error(location.clone(), source, error))?;
    let program = pairs.next().expect("program parser returns one pair");
    let expression = program
        .into_inner()
        .find(|pair| pair.as_rule() == Rule::expression)
        .expect("program contains an expression");
    build_expression(expression, &location)
}

fn parse_error(location: String, source: &str, error: pest::error::Error<Rule>) -> ParseError {
    let offset = match error.location {
        pest::error::InputLocation::Pos(position) => position,
        pest::error::InputLocation::Span((start, _)) => start,
    };
    let expected = match error.variant {
        ErrorVariant::ParsingError { positives, .. } => positives
            .iter()
            .filter_map(expected_token)
            .collect::<Vec<_>>(),
        ErrorVariant::CustomError { .. } => Vec::new(),
    };
    ParseError {
        location,
        span: Span {
            start: offset,
            end: source[offset..]
                .chars()
                .next()
                .map_or(offset, |character| offset + character.len_utf8()),
        },
        expected: if expected.is_empty() {
            vec!["valid expression syntax"]
        } else {
            expected
        },
    }
}

fn expected_token(rule: &Rule) -> Option<&'static str> {
    match rule {
        Rule::number => Some("a finite number"),
        Rule::identifier => Some("an identifier"),
        Rule::lparen => Some("`(`"),
        Rule::rparen => Some("`)`"),
        Rule::comma => Some("`,`"),
        Rule::dot => Some("`.`"),
        Rule::plus => Some("`+`"),
        Rule::minus => Some("`-`"),
        Rule::times => Some("`*`"),
        Rule::divide => Some("`/`"),
        Rule::power_operator => Some("`^`"),
        Rule::EOI => Some("end of expression"),
        _ => None,
    }
}

fn build_expression(pair: Pair<'_, Rule>, location: &str) -> Result<Expr, ParseError> {
    match pair.as_rule() {
        Rule::expression => build_expression(
            pair.into_inner().next().expect("expression has addition"),
            location,
        ),
        Rule::addition => build_left_associative(pair, binary_operator, location),
        Rule::multiplication => build_left_associative(pair, binary_operator, location),
        Rule::unary => build_unary(pair, location),
        Rule::power => build_power(pair, location),
        Rule::primary => build_expression(
            pair.into_inner().next().expect("primary has a child"),
            location,
        ),
        Rule::number => {
            let span = span(&pair);
            let lexeme = pair.as_str().to_owned();
            let value = lexeme.parse::<f64>().map_err(|_| ParseError {
                location: location.to_owned(),
                span,
                expected: vec!["a finite number"],
            })?;
            if !value.is_finite() {
                return Err(ParseError {
                    location: location.to_owned(),
                    span,
                    expected: vec!["a finite number"],
                });
            }
            Ok(Expr {
                kind: ExprKind::Number(Number { value, lexeme }),
                span,
            })
        }
        Rule::identifier => Ok(Expr {
            kind: ExprKind::Variable(pair.as_str().to_owned()),
            span: span(&pair),
        }),
        Rule::field => {
            let expression_span = span(&pair);
            let mut identifiers = pair
                .into_inner()
                .filter(|child| child.as_rule() == Rule::identifier);
            Ok(Expr {
                kind: ExprKind::Field {
                    base: identifiers
                        .next()
                        .expect("field has a base")
                        .as_str()
                        .to_owned(),
                    field: identifiers
                        .next()
                        .expect("field has a member")
                        .as_str()
                        .to_owned(),
                },
                span: expression_span,
            })
        }
        Rule::call => build_call(pair, location),
        Rule::parenthesized => {
            let span = span(&pair);
            let expression = pair
                .into_inner()
                .find(|child| child.as_rule() == Rule::expression)
                .expect("parenthesized expression has a child");
            Ok(Expr {
                kind: ExprKind::Grouped(Box::new(build_expression(expression, location)?)),
                span,
            })
        }
        _ => unreachable!("unexpected grammar rule in AST: {:?}", pair.as_rule()),
    }
}

fn build_left_associative(
    pair: Pair<'_, Rule>,
    operator: fn(Rule) -> Option<BinaryOp>,
    location: &str,
) -> Result<Expr, ParseError> {
    let mut children = pair.into_inner();
    let mut expression = build_expression(
        children.next().expect("binary expression has left operand"),
        location,
    )?;
    while let Some(operator_pair) = children.next() {
        let operation = operator(operator_pair.as_rule()).expect("binary operator rule");
        let right = build_expression(
            children.next().expect("operator has right operand"),
            location,
        )?;
        let expression_span = Span {
            start: expression.span.start,
            end: right.span.end,
        };
        expression = Expr {
            kind: ExprKind::Binary {
                op: operation,
                left: Box::new(expression),
                right: Box::new(right),
            },
            span: expression_span,
        };
    }
    Ok(expression)
}

fn build_unary(pair: Pair<'_, Rule>, location: &str) -> Result<Expr, ParseError> {
    let children = pair.into_inner().collect::<Vec<_>>();
    let (operators, operand) = children.split_at(children.len() - 1);
    let mut expression = build_expression(operand[0].clone(), location)?;
    for operator in operators.iter().rev() {
        let op = match operator.as_rule() {
            Rule::plus => UnaryOp::Plus,
            Rule::minus => UnaryOp::Minus,
            _ => unreachable!("unary operator rule"),
        };
        let expression_span = Span {
            start: operator.as_span().start(),
            end: expression.span.end,
        };
        expression = Expr {
            kind: ExprKind::Unary {
                op,
                operand: Box::new(expression),
            },
            span: expression_span,
        };
    }
    Ok(expression)
}

fn build_power(pair: Pair<'_, Rule>, location: &str) -> Result<Expr, ParseError> {
    let span = span(&pair);
    let mut children = pair.into_inner();
    let left = build_expression(children.next().expect("power has left operand"), location)?;
    let Some(operator) = children.next() else {
        return Ok(left);
    };
    debug_assert_eq!(operator.as_rule(), Rule::power_operator);
    let right = build_expression(
        children.next().expect("power operator has right operand"),
        location,
    )?;
    Ok(Expr {
        kind: ExprKind::Binary {
            op: BinaryOp::Power,
            left: Box::new(left),
            right: Box::new(right),
        },
        span,
    })
}

fn build_call(pair: Pair<'_, Rule>, location: &str) -> Result<Expr, ParseError> {
    let span = span(&pair);
    let mut children = pair.into_inner();
    let name = children
        .next()
        .expect("call has a name")
        .as_str()
        .to_owned();
    let args = children
        .filter(|child| child.as_rule() == Rule::expression)
        .map(|argument| build_expression(argument, location))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(Expr {
        kind: ExprKind::Call { name, args },
        span,
    })
}

fn binary_operator(rule: Rule) -> Option<BinaryOp> {
    match rule {
        Rule::plus => Some(BinaryOp::Add),
        Rule::minus => Some(BinaryOp::Subtract),
        Rule::times => Some(BinaryOp::Multiply),
        Rule::divide => Some(BinaryOp::Divide),
        _ => None,
    }
}

fn span(pair: &Pair<'_, Rule>) -> Span {
    let span = pair.as_span();
    Span {
        start: span.start(),
        end: span.end(),
    }
}

#[cfg(test)]
mod tests {
    use super::{BinaryOp, Expr, ExprKind, UnaryOp, parse};

    fn shape(expression: &Expr) -> String {
        match &expression.kind {
            ExprKind::Number(number) => format!("{}", number.value),
            ExprKind::Variable(name) => name.clone(),
            ExprKind::Field { base, field } => format!("{base}.{field}"),
            ExprKind::Unary { op, operand } => match op {
                UnaryOp::Plus => format!("(+ {})", shape(operand)),
                UnaryOp::Minus => format!("(- {})", shape(operand)),
            },
            ExprKind::Binary { op, left, right } => {
                let op = match op {
                    BinaryOp::Add => "+",
                    BinaryOp::Subtract => "-",
                    BinaryOp::Multiply => "*",
                    BinaryOp::Divide => "/",
                    BinaryOp::Power => "^",
                };
                format!("({op} {} {})", shape(left), shape(right))
            }
            ExprKind::Call { name, args } => format!(
                "{name}({})",
                args.iter().map(shape).collect::<Vec<_>>().join(", ")
            ),
            ExprKind::Grouped(expression) => format!("(group {})", shape(expression)),
        }
    }

    #[test]
    fn parses_operator_precedence_and_associativity() {
        let cases = [
            ("a + b", "(+ a b)"),
            ("a - b - c", "(- (- a b) c)"),
            ("a * b / c", "(/ (* a b) c)"),
            ("a + b * c", "(+ a (* b c))"),
            ("-x ^ y", "(- (^ x y))"),
            ("(-x) ^ y", "(^ (group (- x)) y)"),
            ("a ^ b ^ c", "(^ a (^ b c))"),
            ("a ^ -b", "(^ a (- b))"),
            ("a / b ^ c", "(/ a (^ b c))"),
        ];

        for (source, expected) in cases {
            assert_eq!(
                shape(&parse("formula", source).unwrap()),
                expected,
                "{source}"
            );
        }
    }

    #[test]
    fn parses_numbers_whitespace_and_nested_calls() {
        let expression = parse("spec.yaml:12", "\n  max(.5e1, sqrt(x + 2.))\n").unwrap();
        assert_eq!(shape(&expression), "max(5, sqrt((+ x 2)))");
        assert_eq!(expression.span.start, 3);
        assert_eq!(expression.span.end, 26);
    }

    #[test]
    fn preserves_number_lexemes() {
        let expression = parse("formula", "1.00 + .5e1 + 2.").unwrap();
        let ExprKind::Binary { left, right, .. } = expression.kind else {
            panic!("expected addition");
        };
        let ExprKind::Binary {
            left,
            right: middle,
            ..
        } = left.kind
        else {
            panic!("expected addition");
        };
        let ExprKind::Number(first) = left.kind else {
            panic!("expected number");
        };
        let ExprKind::Number(middle) = middle.kind else {
            panic!("expected number");
        };
        let ExprKind::Number(last) = right.kind else {
            panic!("expected number");
        };
        assert_eq!(
            [first.lexeme, middle.lexeme, last.lexeme],
            ["1.00", ".5e1", "2."]
        );
    }

    #[test]
    fn assigns_each_operator_node_its_own_source_span() {
        let expression = parse("formula", "a + b + c").unwrap();
        let ExprKind::Binary { left, .. } = expression.kind else {
            panic!("expected addition");
        };
        assert_eq!(left.span.start, 0);
        assert_eq!(left.span.end, 5);

        let expression = parse("formula", "--x").unwrap();
        let ExprKind::Unary { operand, .. } = expression.kind else {
            panic!("expected unary expression");
        };
        assert_eq!(expression.span.start, 0);
        assert_eq!(expression.span.end, 3);
        assert_eq!(operand.span.start, 1);
        assert_eq!(operand.span.end, 3);
    }

    #[test]
    fn preserves_all_initial_function_spellings_without_semantic_validation() {
        for name in ["sqrt", "exp", "ln", "log10", "abs", "min", "max"] {
            let expression = parse("formula", &format!("{name}(x)")).unwrap();
            assert_eq!(shape(&expression), format!("{name}(x)"));
        }
        assert_eq!(
            shape(&parse("formula", "unknown(x, y, z)").unwrap()),
            "unknown(x, y, z)"
        );
    }

    #[test]
    fn rejects_non_canonical_and_malformed_syntax() {
        for source in [
            "2x", "x**2", "√x", "sqrt x", "f(,x)", "f(x,)", "1e", "1.2.3", ".", "1e9999",
        ] {
            assert!(parse("spec.yaml:9", source).is_err(), "{source}");
        }
    }

    #[test]
    fn finite_number_errors_preserve_the_expression_location() {
        let error = parse("specs/example.yaml:18", "1e9999").unwrap_err();
        assert_eq!(error.location, "specs/example.yaml:18");
        assert_eq!(error.span.start, 0);
        assert_eq!(error.span.end, 6);
        assert!(error.to_string().contains("a finite number"));
    }

    #[test]
    fn diagnostics_include_location_span_and_expected_tokens() {
        let error = parse("specs/example.yaml:17", "x + )").unwrap_err();
        assert_eq!(error.location, "specs/example.yaml:17");
        assert_eq!(error.span.start, 4);
        assert!(error.span.end > error.span.start);
        assert!(error.to_string().contains("specs/example.yaml:17:4..5"));
        assert!(error.to_string().contains("expected"));
    }
}
