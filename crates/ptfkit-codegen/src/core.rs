use std::{collections::BTreeMap, fs, path::Path};

use anyhow::{Context, Result, bail};
use syn::{FnArg, Item, ItemFn, ItemMod, ItemStruct, ReturnType, Type, Visibility};

use crate::model::{CoreFunction, Output};

pub(crate) fn discover(lib: &Path) -> Result<Vec<CoreFunction>> {
    let mut modules = BTreeMap::new();
    parse_module(lib, &[], &mut modules)?;
    let mut structs = BTreeMap::new();
    for (module, file) in &modules {
        for item in &file.items {
            if let Item::Struct(structure) = item {
                structs.insert(
                    (module.clone(), structure.ident.to_string()),
                    structure.clone(),
                );
            }
        }
    }
    let mut functions = Vec::new();
    for (module, file) in &modules {
        for item in &file.items {
            if let Item::Fn(function) = item
                && matches!(function.vis, Visibility::Public(_))
                && function.sig.ident.to_string().starts_with("calc_ptf_")
            {
                functions.push(parse_function(function, module, &structs)?);
            }
        }
    }
    functions.sort_by_key(|function| (function.module.clone(), function.name.clone()));
    Ok(functions)
}

fn parse_module(
    path: &Path,
    module: &[String],
    modules: &mut BTreeMap<Vec<String>, syn::File>,
) -> Result<()> {
    let file = syn::parse_file(
        &fs::read_to_string(path).with_context(|| format!("reading {}", path.display()))?,
    )?;
    let parent = path.parent().expect("Rust module path has a parent");
    for item in &file.items {
        if let Item::Mod(ItemMod {
            ident,
            content: None,
            ..
        }) = item
        {
            let name = ident.to_string();
            let direct = parent.join(format!("{name}.rs"));
            let nested = parent.join(&name).join("mod.rs");
            let child = if direct.exists() {
                direct
            } else if nested.exists() {
                nested
            } else {
                bail!("cannot resolve module `{name}` from {}", path.display())
            };
            let mut next = module.to_vec();
            next.push(name);
            parse_module(&child, &next, modules)?;
        }
    }
    modules.insert(module.to_vec(), file);
    Ok(())
}

fn parse_function(
    function: &ItemFn,
    module: &[String],
    structs: &BTreeMap<(Vec<String>, String), ItemStruct>,
) -> Result<CoreFunction> {
    if !function.sig.generics.params.is_empty()
        || function.sig.variadic.is_some()
        || function.sig.asyncness.is_some()
    {
        bail!(
            "unsupported signature for `{}`: generics, variadic, async, and unsafe are not supported",
            function.sig.ident
        );
    }
    let mut inputs = Vec::new();
    for argument in &function.sig.inputs {
        let FnArg::Typed(argument) = argument else {
            bail!("unsupported receiver on `{}`", function.sig.ident)
        };
        if !is_f64(&argument.ty) {
            bail!(
                "unsupported parameter type on `{}`: every argument must be f64",
                function.sig.ident
            )
        }
        let syn::Pat::Ident(name) = &*argument.pat else {
            bail!("unsupported argument pattern on `{}`", function.sig.ident)
        };
        inputs.push(name.ident.to_string());
    }
    let output = match &function.sig.output {
        ReturnType::Default => bail!("unsupported return type on `{}`", function.sig.ident),
        ReturnType::Type(_, ty) if is_f64(ty) => Output::Scalar,
        ReturnType::Type(_, ty) if matches!(ty.as_ref(), Type::Path(_)) => {
            let Type::Path(path) = ty.as_ref() else {
                unreachable!()
            };
            let ident = path
                .path
                .segments
                .last()
                .expect("type path has a segment")
                .ident
                .to_string();
            let structure = structs
                .get(&(module.to_vec(), ident.clone()))
                .or_else(|| {
                    structs
                        .iter()
                        .find_map(|((_, name), structure)| (name == &ident).then_some(structure))
                })
                .with_context(|| {
                    format!(
                        "unsupported return type `{ident}` on `{}`",
                        function.sig.ident
                    )
                })?;
            parse_struct(structure)?
        }
        ReturnType::Type(_, _) => bail!("unsupported return type on `{}`", function.sig.ident),
    };
    Ok(CoreFunction {
        name: function.sig.ident.to_string(),
        module: module.to_vec(),
        inputs,
        output,
    })
}

fn is_f64(ty: &Type) -> bool {
    matches!(ty, Type::Path(path) if path.qself.is_none() && path.path.is_ident("f64"))
}

fn parse_struct(structure: &ItemStruct) -> Result<Output> {
    if !structure.generics.params.is_empty() {
        bail!(
            "result structure `{}` cannot have generics",
            structure.ident
        )
    }
    let syn::Fields::Named(fields) = &structure.fields else {
        bail!(
            "result structure `{}` must have named fields",
            structure.ident
        )
    };
    if fields.named.is_empty() {
        bail!("result structure `{}` must have fields", structure.ident)
    }
    let mut names = Vec::new();
    for field in &fields.named {
        if !matches!(field.vis, Visibility::Public(_)) {
            bail!("result structure `{}` has a private field", structure.ident)
        }
        if !is_f64(&field.ty) {
            bail!("result structure `{}` has a non-f64 field", structure.ident)
        }
        names.push(
            field
                .ident
                .as_ref()
                .expect("named field has an identifier")
                .to_string(),
        );
    }
    Ok(Output::Struct(names))
}
