use std::{collections::BTreeMap, path::PathBuf};

use anyhow::Result;
use proc_macro2::{Span, TokenStream};
use quote::{format_ident, quote};

use crate::{
    generate::RUST_HEADER,
    model::{Output, Resolved},
};

pub(crate) fn render(functions: &[Resolved]) -> Result<Vec<(PathBuf, String)>> {
    let mut sources = BTreeMap::<String, Vec<&Resolved>>::new();
    for function in functions {
        sources
            .entry(function.entry.spec.source.key.clone())
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

fn module_tokens(functions: &[&Resolved]) -> Result<TokenStream> {
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

fn function_tokens(resolved: &Resolved) -> Result<TokenStream> {
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
    let core_path = syn::parse_str::<syn::Path>(&format!(
        "ptfkit_core::{}::{}",
        function.module.join("::"),
        function.name
    ))?;
    let values = match &function.output {
        Output::Scalar => vec![quote!(result)],
        Output::Struct(fields) => fields
            .iter()
            .map(|field| {
                let field = format_ident!("{field}");
                quote!(result.#field)
            })
            .collect(),
    };
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
                    let result = #core_path(#(#inputs),*);
                    let values = [#(#values),*];
                    #(#writes)*
                    for index in 0..#nargs { pointers[index] = pointers[index].offset(strides[index]); }
                }
            }
        }
    })
}

fn registration_tokens(resolved: &Resolved) -> Result<TokenStream> {
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
    use quote::quote;

    use super::render_tokens;

    #[test]
    fn generated_rust_parses() {
        let generated = render_tokens(quote!(
            pub fn register() {}
        ));
        assert!(syn::parse_file(&generated).is_ok());
    }
}
