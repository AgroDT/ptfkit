use std::path::PathBuf;

use anyhow::{Result, bail};
use proc_macro2::{Literal, TokenStream};
use quote::{format_ident, quote};

use crate::{
    generate::RUST_HEADER,
    model::{Function, Output, Parameter, Resolved, Scope, Source},
    semantic::{self, BinaryOp, Expr, MathFunction, Reference, UnaryOp},
};

pub(crate) fn render(functions: &[Resolved]) -> Result<Vec<(PathBuf, String)>> {
    functions
        .iter()
        .filter_map(|resolved| {
            resolved.entry.implementations[resolved.function_index]
                .as_ref()
                .map(|ir| (resolved, ir))
        })
        .map(|(resolved, ir)| {
            let module_docs =
                module_doc_tokens(&resolved.entry.spec.source, &resolved.entry.spec.scope);
            Ok((
                PathBuf::from(format!("{}.rs", resolved.entry.slug)),
                render_tokens(module_docs, module_tokens(resolved, ir)?),
            ))
        })
        .collect()
}

fn module_tokens(resolved: &Resolved, ir: &semantic::Function) -> Result<TokenStream> {
    let function = &resolved.core;
    let specification = &resolved.entry.spec.functions[resolved.function_index];
    let function_docs = function_doc_tokens(specification);
    let name = format_ident!("{}", function.name);
    let inputs = function
        .inputs
        .iter()
        .map(|name| format_ident!("{name}"))
        .collect::<Vec<_>>();
    let variables = ir
        .variables
        .iter()
        .map(|variable| {
            let name = format_ident!("{}", variable.name);
            let expression = expression_tokens(&variable.expression, &inputs, &ir.variables)?;
            Ok(quote!(let #name = #expression;))
        })
        .collect::<Result<Vec<_>>>()?;
    let OutputTokens {
        definition,
        return_type,
        expression,
    } = output_tokens(resolved, ir, &inputs)?;
    let tests = golden_test_tokens(resolved)?;
    Ok(quote! {
        #definition

        #function_docs
        #[must_use]
        pub fn #name(#(#inputs: f64),*) -> #return_type {
            #(#variables)*
            #expression
        }

        #tests
    })
}

struct OutputTokens {
    definition: TokenStream,
    return_type: TokenStream,
    expression: TokenStream,
}

fn output_tokens(
    resolved: &Resolved,
    ir: &semantic::Function,
    inputs: &[syn::Ident],
) -> Result<OutputTokens> {
    match (&resolved.core.output, &ir.output) {
        (Output::Scalar, semantic::Output::Scalar(expression)) => {
            let expression = expression_tokens(expression, inputs, &ir.variables)?;
            Ok(OutputTokens {
                definition: TokenStream::new(),
                return_type: quote!(f64),
                expression: quote!(#expression),
            })
        }
        (Output::Struct(fields), semantic::Output::Record(expressions)) => {
            let specification = &resolved.entry.spec.functions[resolved.function_index];
            let result = specification
                .public_api
                .result_class
                .as_deref()
                .ok_or_else(|| anyhow::anyhow!("record output has no result class"))?;
            let result = format_ident!("{result}");
            let definitions = fields.iter().map(|field| {
                let field = format_ident!("{field}");
                let parameter = specification
                    .outputs
                    .iter()
                    .find(|parameter| field == parameter.name)
                    .expect("core output field matches specification");
                let docs = doc_tokens([parameter_doc(parameter)]);
                quote!(#docs pub #field: f64)
            });
            let values = expressions
                .iter()
                .map(|field| {
                    let name = format_ident!("{}", field.name);
                    let expression = expression_tokens(&field.expression, inputs, &ir.variables)?;
                    Ok(quote!(#name: #expression))
                })
                .collect::<Result<Vec<_>>>()?;
            Ok(OutputTokens {
                definition: {
                    let mut lines = vec![
                        "Results returned by the matching PTF.".into(),
                        String::new(),
                        "# Fields".into(),
                        String::new(),
                    ];
                    lines.extend(specification.outputs.iter().map(parameter_doc));
                    let docs = doc_tokens(lines);
                    quote!(#docs #[derive(Clone, Copy, Debug, PartialEq)] pub struct #result { #(#definitions),* })
                },
                return_type: quote!(#result),
                expression: quote!(#result { #(#values),* }),
            })
        }
        _ => bail!("semantic output does not match public core output"),
    }
}

fn module_doc_tokens(source: &Source, scope: &Scope) -> TokenStream {
    let mut lines = vec![
        source.summary.clone(),
        String::new(),
        "# Reference".into(),
        String::new(),
        source.citation_apa.clone(),
    ];
    if let Some(doi) = &source.doi {
        lines.push(format!("DOI: {} ({})", doi.identifier, doi.url));
    }
    if let Some(territory) = &scope.territory {
        lines.extend([
            String::new(),
            "# Territory".into(),
            String::new(),
            territory.clone(),
        ]);
    }
    if let Some(dataset) = &scope.dataset {
        lines.extend([
            String::new(),
            "# Dataset".into(),
            String::new(),
            dataset.clone(),
        ]);
    }
    inner_doc_tokens(lines)
}

fn function_doc_tokens(function: &Function) -> TokenStream {
    let mut lines = vec![
        function.public_api.summary.clone(),
        String::new(),
        "# Arguments".into(),
        String::new(),
    ];
    lines.extend(
        function
            .inputs
            .iter()
            .map(|parameter| format!("* {}", parameter_doc(parameter))),
    );
    lines.extend([String::new(), "# Returns".into(), String::new()]);
    lines.extend(
        function
            .outputs
            .iter()
            .map(|parameter| format!("* {}", parameter_doc(parameter))),
    );
    if let Some(territory) = &function.scope.territory {
        lines.extend([
            String::new(),
            "# Territory".into(),
            String::new(),
            territory.clone(),
        ]);
    }
    let models = [
        function
            .scope
            .models
            .h_theta
            .as_ref()
            .map(|model| format!("h(theta): {model}")),
        function
            .scope
            .models
            .k_h
            .as_ref()
            .map(|model| format!("k(h): {model}")),
    ]
    .into_iter()
    .flatten()
    .collect::<Vec<_>>();
    if !models.is_empty() {
        lines.extend([String::new(), "# Models".into(), String::new()]);
        lines.extend(models.into_iter().map(|model| format!("* {model}")));
    }
    lines.extend([
        String::new(),
        "# Notes".into(),
        String::new(),
        format!("Prediction target: {}", function.scope.prediction_target),
    ]);
    lines.extend(function.documentation.notes.iter().cloned());
    if !function.documentation.warnings.is_empty() {
        lines.extend([String::new(), "# Warnings".into(), String::new()]);
        lines.extend(function.documentation.warnings.iter().cloned());
    }
    doc_tokens(lines)
}

fn parameter_doc(parameter: &Parameter) -> String {
    format!(
        "{}: {} ({})",
        parameter.name, parameter.description, parameter.unit
    )
}

fn doc_tokens(lines: impl IntoIterator<Item = String>) -> TokenStream {
    let documentation = raw_doc_literal(wrap_doc_lines(lines).join("\n"));
    quote!(#[doc = #documentation])
}

fn inner_doc_tokens(lines: impl IntoIterator<Item = String>) -> TokenStream {
    let documentation = raw_doc_literal(wrap_doc_lines(lines).join("\n"));
    quote!(#![doc = #documentation])
}

fn wrap_doc_lines(lines: impl IntoIterator<Item = String>) -> Vec<String> {
    lines
        .into_iter()
        .flat_map(|line| {
            if line.is_empty() || line.starts_with('#') {
                return vec![line];
            }
            let (first_prefix, continuation_prefix, text) = match line.strip_prefix("* ") {
                Some(text) => ("  * ", "    ", text),
                None => ("", "", line.as_str()),
            };
            wrap_doc_line(text, first_prefix, continuation_prefix)
        })
        .collect()
}

fn wrap_doc_line(text: &str, first_prefix: &str, continuation_prefix: &str) -> Vec<String> {
    const WIDTH: usize = 96;
    let mut lines = Vec::new();
    let mut line = first_prefix.to_owned();
    for word in text.split_whitespace() {
        let separator = usize::from(line.len() > first_prefix.len());
        if line.len() + separator + word.len() > WIDTH && line.len() > first_prefix.len() {
            lines.push(line);
            line = continuation_prefix.to_owned();
        }
        if line.len()
            > if lines.is_empty() {
                first_prefix.len()
            } else {
                continuation_prefix.len()
            }
        {
            line.push(' ');
        }
        line.push_str(word);
    }
    if !line.is_empty() {
        lines.push(line);
    }
    lines
}

fn raw_doc_literal(documentation: String) -> syn::LitStr {
    for hashes in 0.. {
        let delimiter = "#".repeat(hashes);
        let source = format!("r{delimiter}\"{documentation}\"{delimiter}");
        if let Ok(literal) = syn::parse_str(&source) {
            return literal;
        }
    }
    unreachable!("a raw string delimiter is always available")
}

fn expression_tokens(
    expression: &Expr,
    inputs: &[syn::Ident],
    variables: &[semantic::Variable],
) -> Result<TokenStream> {
    match expression {
        Expr::Number(value) => {
            let value = Literal::f64_suffixed(*value);
            Ok(quote!(#value))
        }
        Expr::Reference(Reference::Input(index)) => {
            let input = &inputs[*index];
            Ok(quote!(#input))
        }
        Expr::Reference(Reference::Variable(index)) => {
            let name = format_ident!("{}", variables[*index].name);
            Ok(quote!(#name))
        }
        Expr::Unary { op, operand } => {
            let operand = expression_tokens(operand, inputs, variables)?;
            Ok(match op {
                UnaryOp::Plus => quote!(#operand),
                UnaryOp::Minus => quote!(-(#operand)),
            })
        }
        Expr::Binary { op, left, right } => {
            let exponent_is_i32 = matches!(op, BinaryOp::Power)
                && matches!(right.as_ref(), Expr::Number(value) if value.fract() == 0.0 && *value >= i32::MIN as f64 && *value <= i32::MAX as f64);
            let exponent_value = match right.as_ref() {
                Expr::Number(value) => Some(*value as i32),
                _ => None,
            };
            let left = expression_tokens(left, inputs, variables)?;
            let right = expression_tokens(right, inputs, variables)?;
            Ok(match op {
                BinaryOp::Add => quote!((#left) + (#right)),
                BinaryOp::Subtract => quote!((#left) - (#right)),
                BinaryOp::Multiply => quote!((#left) * (#right)),
                BinaryOp::Divide => quote!((#left) / (#right)),
                BinaryOp::Power if exponent_is_i32 => power_tokens(left, right, exponent_value),
                BinaryOp::Power => power_tokens(left, right, None),
            })
        }
        Expr::Call { function, args } => {
            let args = args
                .iter()
                .map(|arg| expression_tokens(arg, inputs, variables))
                .collect::<Result<Vec<_>>>()?;
            let first = &args[0];
            Ok(match function {
                MathFunction::Sqrt => quote!((#first).sqrt()),
                MathFunction::Exp => quote!((#first).exp()),
                MathFunction::Ln => quote!((#first).ln()),
                MathFunction::Log10 => quote!((#first).log10()),
                MathFunction::Abs => quote!((#first).abs()),
                MathFunction::Min => {
                    let second = &args[1];
                    quote!((#first).min(#second))
                }
                MathFunction::Max => {
                    let second = &args[1];
                    quote!((#first).max(#second))
                }
            })
        }
    }
}

fn power_tokens(
    base: TokenStream,
    exponent: TokenStream,
    integer_exponent: Option<i32>,
) -> TokenStream {
    if let Some(value) = integer_exponent {
        let exponent = Literal::i32_unsuffixed(value);
        quote!((#base).powi(#exponent))
    } else {
        quote!((#base).powf(#exponent))
    }
}

fn golden_test_tokens(resolved: &Resolved) -> Result<TokenStream> {
    let function = format_ident!("{}", resolved.core.name);
    let tests = resolved.entry.spec.functions[resolved.function_index]
        .golden_tests
        .iter()
        .map(|case| {
            let name = format_ident!("{}", case.id);
            let values = resolved
                .core
                .inputs
                .iter()
                .map(|input| {
                    case.inputs
                        .get(input)
                        .map(|value| Literal::f64_suffixed(*value))
                        .ok_or_else(|| {
                            anyhow::anyhow!("golden test `{}` is missing input `{input}`", case.id)
                        })
                })
                .collect::<Result<Vec<_>>>()?;
            let expected = resolved.entry.spec.functions[resolved.function_index]
                .outputs
                .iter()
                .map(|field| {
                    case.expected
                        .get(&field.name)
                        .map(|value| Literal::f64_suffixed(*value))
                        .ok_or_else(|| {
                            anyhow::anyhow!(
                                "golden test `{}` is missing output `{}`",
                                case.id,
                                field.name
                            )
                        })
                })
                .collect::<Result<Vec<_>>>()?;
            let atol = Literal::f64_suffixed(case.atol);
            let rtol = Literal::f64_suffixed(case.rtol);
            let assertions = match &resolved.core.output {
                Output::Scalar => {
                    let expected = &expected[0];
                    quote!(assert_close(result, #expected, #atol, #rtol);)
                }
                Output::Struct(fields) => {
                    let assertions = fields.iter().zip(&expected).map(|(field, expected)| {
                        let field = format_ident!("{field}");
                        quote!(assert_close(result.#field, #expected, #atol, #rtol);)
                    });
                    quote!(#(#assertions)*)
                }
            };
            Ok(quote!(#[test] fn #name() { let result = #function(#(#values),*); #assertions }))
        })
        .collect::<Result<Vec<_>>>()?;
    Ok(
        quote! { #[cfg(test)] mod tests { use super::*; fn assert_close(actual: f64, expected: f64, atol: f64, rtol: f64) { assert!((actual - expected).abs() <= atol + rtol * expected.abs(), "actual {actual} != expected {expected}"); } #(#tests)* } },
    )
}

fn render_tokens(module_docs: TokenStream, tokens: TokenStream) -> String {
    format!("{RUST_HEADER}\n{module_docs}\n\n{tokens}")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::semantic::{BinaryOp, Expr, MathFunction, Reference};
    #[test]
    fn renders_every_operator_and_function() {
        let inputs = vec![format_ident!("x"), format_ident!("y")];
        let vars = Vec::new();
        let binary = [
            BinaryOp::Add,
            BinaryOp::Subtract,
            BinaryOp::Multiply,
            BinaryOp::Divide,
            BinaryOp::Power,
        ];
        for op in binary {
            assert!(
                syn::parse2::<syn::Expr>(
                    expression_tokens(
                        &Expr::Binary {
                            op,
                            left: Box::new(Expr::Reference(Reference::Input(0))),
                            right: Box::new(Expr::Number(2.0))
                        },
                        &inputs,
                        &vars
                    )
                    .unwrap()
                )
                .is_ok()
            );
        }
        for function in [
            MathFunction::Sqrt,
            MathFunction::Exp,
            MathFunction::Ln,
            MathFunction::Log10,
            MathFunction::Abs,
            MathFunction::Min,
            MathFunction::Max,
        ] {
            let args = if matches!(function, MathFunction::Min | MathFunction::Max) {
                vec![Expr::Number(1.0), Expr::Number(2.0)]
            } else {
                vec![Expr::Number(1.0)]
            };
            assert!(
                syn::parse2::<syn::Expr>(
                    expression_tokens(&Expr::Call { function, args }, &inputs, &vars).unwrap()
                )
                .is_ok()
            );
        }
    }

    #[test]
    fn renders_outer_and_inner_rustdoc_attributes() {
        let module_docs = inner_doc_tokens(["Source summary.".into(), "# Reference".into()]);
        let function_docs = doc_tokens(["Function summary.".into(), "# Arguments".into()]);
        let generated = quote!(#module_docs #function_docs pub fn calculate() {});
        assert!(syn::parse_file(&generated.to_string()).is_ok());
        assert!(generated.to_string().contains("r\"Source summary."));
        assert!(generated.to_string().contains("r\"Function summary."));
    }
}
