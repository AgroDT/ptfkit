use std::{collections::BTreeMap, path::PathBuf};

use anyhow::Result;
use proc_macro2::{Literal, Span, TokenStream};
use quote::{format_ident, quote};

use crate::{
    generate::RUST_HEADER,
    model::{CompiledFunction, Output},
    semantic::{self, BinaryOp, Expr, MathFunction, Reference, UnaryOp},
};

pub(crate) fn render(functions: &[CompiledFunction]) -> Result<Vec<(PathBuf, String)>> {
    let mut sources = BTreeMap::<String, Vec<&CompiledFunction>>::new();
    for function in functions {
        sources
            .entry(function.entry.slug.clone())
            .or_default()
            .push(function);
    }

    let mut files = Vec::new();
    let mut modules = Vec::new();
    for (source, functions) in sources {
        modules.push(format_ident!("{source}"));
        files.push((
            PathBuf::from("generated").join(format!("{source}.rs")),
            render_tokens(module_tokens(&functions)?),
        ));
    }
    files.push((
        PathBuf::from("generated/mod.rs"),
        render_tokens(index_tokens(&modules)),
    ));
    Ok(files)
}

fn module_tokens(functions: &[&CompiledFunction]) -> Result<TokenStream> {
    let definitions = functions
        .iter()
        .map(|function| function_tokens(function))
        .collect::<Result<Vec<_>>>()?;
    let registrations = functions
        .iter()
        .map(|function| registration_tokens(function))
        .collect::<Result<Vec<_>>>()?;
    Ok(quote! {
        use std::{ffi::c_void, os::raw::c_char};

        use numpy::npyffi::{objects::PyUFuncGenericFunction, types::{npy_intp, NPY_TYPES}};
        use pyo3::{prelude::*, types::PyModule};

        use super::super::runtime;

        #(#definitions)*

        pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
            let py = module.py();
            #(#registrations)*
            Ok(())
        }
    })
}

fn function_tokens(resolved: &CompiledFunction) -> Result<TokenStream> {
    let function = &resolved.core;
    let loop_name = format_ident!("{}_loop", function.name);
    let upper = function.name.to_uppercase();
    let nin = format_ident!("{upper}_NIN");
    let nout = format_ident!("{upper}_NOUT");
    let nargs = format_ident!("{upper}_NARGS");
    let types = format_ident!("{upper}_TYPES");
    let functions = format_ident!("{upper}_FUNCTIONS");
    let ufunc_name = format_ident!("{upper}_NAME");
    let doc = format_ident!("{upper}_DOC");
    let inputs = function
        .inputs
        .iter()
        .map(|input| format_ident!("{input}"))
        .collect::<Vec<_>>();
    let input_reads = inputs.iter().enumerate().map(|(index, input)| {
        quote! {
            let #input = (pointers[#index] as *const f64).read_unaligned();
        }
    });
    let variables = resolved
        .ir
        .variables
        .iter()
        .map(|variable| {
            let name = format_ident!("{}", variable.name);
            let expression =
                expression_tokens(&variable.expression, &inputs, &resolved.ir.variables)?;
            Ok(quote!(let #name = #expression;))
        })
        .collect::<Result<Vec<_>>>()?;
    let values = output_variable_tokens(&function.output, resolved)?;
    let calculation = quote!(#(#variables)* let values = [#(#values),*];);
    let writes = values.iter().enumerate().map(|(offset, _)| {
        let index = function.inputs.len() + offset;
        quote! { (pointers[#index] as *mut f64).write_unaligned(values[#offset]); }
    });
    let nin_value = function.inputs.len();
    let nout_value = values.len();
    let nargs_value = nin_value + nout_value;
    let nul_terminated_name =
        syn::LitByteStr::new(format!("{}\0", function.name).as_bytes(), Span::call_site());
    Ok(quote! {
        const #nin: usize = #nin_value;
        const #nout: usize = #nout_value;
        const #nargs: usize = #nargs_value;
        static mut #types: [i8; #nargs_value] = [NPY_TYPES::NPY_DOUBLE as i8; #nargs_value];
        static mut #functions: [PyUFuncGenericFunction; 1] = [Some(#loop_name); 1];
        static #ufunc_name: &[u8] = #nul_terminated_name;
        static #doc: &[u8] = #nul_terminated_name;

        unsafe extern "C" fn #loop_name(args: *mut *mut c_char, dimensions: *mut npy_intp, steps: *mut npy_intp, _: *mut c_void) {
            // SAFETY: NumPy invokes this with NARGS valid operand pointers and strides.
            unsafe {
                let count = *dimensions as usize;
                let mut pointers = [std::ptr::null_mut(); #nargs];
                let mut strides = [0isize; #nargs];
                std::ptr::copy_nonoverlapping(args, pointers.as_mut_ptr(), #nargs);
                std::ptr::copy_nonoverlapping(steps, strides.as_mut_ptr(), #nargs);
                for _ in 0..count {
                    #(#input_reads)*
                    #calculation
                    #(#writes)*
                    for index in 0..#nargs { pointers[index] = pointers[index].offset(strides[index]); }
                }
            }
        }
    })
}

fn output_variable_tokens(
    function: &Output,
    resolved: &CompiledFunction,
) -> Result<Vec<TokenStream>> {
    let fields = match function {
        Output::Scalar => &resolved.entry.spec.functions[resolved.function_index]
            .outputs
            .fields()[..1],
        Output::Struct(_) => resolved.entry.spec.functions[resolved.function_index]
            .outputs
            .fields(),
    };
    Ok(fields
        .iter()
        .map(|field| format_ident!("{}", field.name))
        .map(|name| quote!(#name))
        .collect())
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
            let left = expression_tokens(left, inputs, variables)?;
            let right = expression_tokens(right, inputs, variables)?;
            Ok(match op {
                BinaryOp::Add => quote!((#left) + (#right)),
                BinaryOp::Subtract => quote!((#left) - (#right)),
                BinaryOp::Multiply => quote!((#left) * (#right)),
                BinaryOp::Divide => quote!((#left) / (#right)),
                BinaryOp::Power => quote!((#left).powf(#right)),
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

fn registration_tokens(resolved: &CompiledFunction) -> Result<TokenStream> {
    let upper = resolved.core.name.to_uppercase();
    let functions = format_ident!("{upper}_FUNCTIONS");
    let types = format_ident!("{upper}_TYPES");
    let nin = format_ident!("{upper}_NIN");
    let nout = format_ident!("{upper}_NOUT");
    let name = format_ident!("{upper}_NAME");
    let doc = format_ident!("{upper}_DOC");
    let function_name = &resolved.core.name;
    Ok(quote! {
        // SAFETY: the generated function and dtype tables have process-lifetime storage.
        let ufunc = unsafe {
            runtime::create_ufunc(
                py,
                std::ptr::addr_of_mut!(#functions).cast(),
                std::ptr::addr_of_mut!(#types).cast(),
                #nin as i32,
                #nout as i32,
                #name.as_ptr().cast(),
                #doc.as_ptr().cast(),
            )
        }?;
        module.add(#function_name, ufunc)?;
    })
}

fn index_tokens(modules: &[syn::Ident]) -> TokenStream {
    quote! {
        use pyo3::{prelude::*, types::PyModule};

        #(pub mod #modules;)*

        pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
            #( #modules::register(module)?; )*
            Ok(())
        }
    }
}

fn render_tokens(tokens: TokenStream) -> String {
    format!("{RUST_HEADER}{tokens}")
}

#[cfg(test)]
mod tests {
    use quote::{format_ident, quote};

    use super::{expression_tokens, render_tokens};
    use crate::semantic::{BinaryOp, Expr, MathFunction, Reference, Variable};

    #[test]
    fn generated_rust_parses() {
        let generated = render_tokens(quote!(
            pub fn register() {}
        ));
        assert!(syn::parse_file(&generated).is_ok());
    }

    #[test]
    fn renders_scalar_expressions_from_semantic_ir() {
        let inputs = vec![format_ident!("silt"), format_ident!("clay")];
        let variables = vec![Variable {
            name: "log_k_sat".into(),
            expression: Expr::Number(0.0),
        }];
        let expression = Expr::Binary {
            op: BinaryOp::Power,
            left: Box::new(Expr::Number(10.0)),
            right: Box::new(Expr::Binary {
                op: BinaryOp::Add,
                left: Box::new(Expr::Call {
                    function: MathFunction::Log10,
                    args: vec![Expr::Reference(Reference::Input(0))],
                }),
                right: Box::new(Expr::Reference(Reference::Variable(0))),
            }),
        };

        let tokens = expression_tokens(&expression, &inputs, &variables).unwrap();

        assert!(syn::parse2::<syn::Expr>(tokens.clone()).is_ok());
        assert!(tokens.to_string().contains("log10"));
        assert!(tokens.to_string().contains("powf"));
        assert!(tokens.to_string().contains("log_k_sat"));
    }

    #[test]
    fn generated_jabro_ufunc_does_not_call_the_core_kernel() {
        let generated = include_str!("../../../ptfkit-py/src/ufunc/generated/jabro1992.rs");

        assert!(!generated.contains("ptfkit_core::jabro1992"));
    }
}
