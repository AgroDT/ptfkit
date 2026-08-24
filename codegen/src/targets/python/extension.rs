use anyhow::Result;

use crate::{
    adapters::{Adapter, Registry},
    model::{CompiledFunction, Output},
    output::GeneratedFile,
    render::{
        Writer,
        c::{self, Dialect},
    },
    targets::group_by_source,
};

use super::C_HEADER;

pub(crate) fn render(
    functions: &[CompiledFunction],
    adapters: &Registry,
) -> Result<Vec<GeneratedFile>> {
    let sources = group_by_source(functions);
    let mut writes = Vec::new();
    for (slug, functions) in &sources {
        let register = format!("ptfkit_register_{slug}");
        let mut source = Writer::new();
        source.write(C_HEADER);
        source.write("#include \"ufunc.h\"\n\n");
        if functions
            .iter()
            .any(|function| !function.ir.derived_inputs.is_empty())
        {
            source.write("#include \"usda_texture_adapter.h\"\n\n");
        }
        for function in functions {
            source.write(ufunc(function)?);
        }
        source.line(format_args!("int {register}(PyObject *module) {{"));
        source.indented(|writer| {
            for function in functions {
                writer.line(format_args!(
                    "if (ptfkit_add_ufunc(module, \"{name}\", {name}_functions, {name}_types, {nin}, {nout}) < 0) return -1;",
                    name = function.core.name,
                    nin = function.core.inputs.len(),
                    nout = output_count(&function.core.output),
                ));
            }
            writer.line("return 0;");
        });
        source.line("}");
        writes.push(GeneratedFile::new(
            format!("src/ptfkit/{slug}.c").into(),
            source.into_string(),
        ));
    }
    let mut entry = Writer::new();
    entry.write(C_HEADER);
    entry.write(
        r#"#define PY_SSIZE_T_CLEAN
#define PY_ARRAY_UNIQUE_SYMBOL PTFKIT_ARRAY_API
#include <Python.h>
#include <numpy/arrayobject.h>
#include <numpy/ufuncobject.h>"#,
    );
    entry.write("\n#include \"usda_texture_parser.h\"\n");
    entry.blank_line();
    for slug in sources.keys() {
        entry.line(format_args!("#include \"{slug}.c\""));
    }
    entry.write("\n\nstatic PyMethodDef ptfkit_methods[] = {\n    {\"_prepare_usda_texture\", ptfkit_prepare_usda_texture, METH_O, NULL},\n    {NULL, NULL, 0, NULL}\n};\n\nstatic struct PyModuleDef module_def = { PyModuleDef_HEAD_INIT, \"_ptfkit\", NULL, -1, ptfkit_methods };\n\nPyMODINIT_FUNC PyInit__ptfkit(void) {\n");
    entry.indented(|writer| {
        writer.line("PyObject *module = PyModule_Create(&module_def);");
        writer.line("if (module == NULL) return NULL;");
        writer.line("import_array();");
        writer.line("import_ufunc();");
        for slug in sources.keys() {
            writer.line(format_args!(
                "if (ptfkit_register_{slug}(module) < 0) {{ Py_DECREF(module); return NULL; }}"
            ));
        }
        writer.line("return module;");
    });
    entry.line("}");
    writes.push(GeneratedFile::new(
        "src/ptfkit/ptfkit.c".into(),
        entry.into_string(),
    ));
    for adapter in adapters.adapters() {
        writes.push(GeneratedFile::new(
            format!("src/ptfkit/{}_adapter.h", adapter.adapter_id).into(),
            adapter_header(adapter),
        ));
    }
    Ok(writes)
}

fn ufunc(function: &CompiledFunction) -> Result<String> {
    let name = &function.core.name;
    let inputs = &function.core.inputs;
    let values = match &function.core.output {
        Output::Scalar => vec![
            function.entry.spec.functions[function.function_index]
                .outputs
                .fields()[0]
                .name
                .clone(),
        ],
        Output::Struct(fields) => fields.clone(),
    };
    let types = inputs
        .iter()
        .map(|input| {
            if input.r#type.is_numeric() {
                "NPY_DOUBLE"
            } else {
                "NPY_UINT8"
            }
        })
        .chain(std::iter::repeat_n("NPY_DOUBLE", values.len()))
        .collect::<Vec<_>>()
        .join(", ");
    let mut writer = Writer::new();
    writer.line(format_args!("static void {name}_loop(char **args, const npy_intp *dimensions, const npy_intp *steps, void *data) {{"));
    writer.indented(|writer| {
        writer.line("npy_intp index;");
        writer.line("for (index = 0; index < dimensions[0]; index++) {");
        writer.indented(|writer| {
            for (index, input) in inputs.iter().enumerate() {
                if input.r#type.is_numeric() {
                    writer.line(format_args!("const double {} = *(const double *)args[{index}];", input.name));
                } else {
                    writer.line(format_args!("const uint8_t {} = *(const uint8_t *)args[{index}];", input.name));
                }
            }
            let mut lowered = std::collections::BTreeSet::new();
            for binding in &function.ir.derived_inputs {
                let source_name = &inputs[binding.source_input].name;
                if lowered.insert((binding.adapter.as_str(), source_name.as_str())) {
                    writer.line(format_args!("const ptfkit_usda_texture_fractions {source_name}_fractions = ptfkit_usda_texture_to_fractions({source_name});"));
                }
                writer.line(format_args!("const double {} = {source_name}_fractions.{};", binding.symbol, binding.component));
            }
            for variable in &function.ir.variables {
                writer.write(format_args!("const double {} = ", variable.name));
                writer.write(c::expression(
                    &variable.expression,
                    inputs,
                    &function.ir.derived_inputs,
                    &function.ir.variables,
                    Dialect::C,
                ));
                writer.line(";");
            }
            for (index, value) in values.iter().enumerate() {
                writer.line(format_args!(
                    "*(double *)args[{}] = {value};",
                    inputs.len() + index
                ));
            }
            writer.line(format_args!(
                "for (int arg = 0; arg < {}; arg++) args[arg] += steps[arg];",
                inputs.len() + values.len()
            ));
        });
        writer.line("}");
    });
    writer.line("}");
    writer.write(format_args!(
        "static PyUFuncGenericFunction {name}_functions[] = {{ {name}_loop }};\nstatic char {name}_types[] = {{ {types} }};\n\n"
    ));
    Ok(writer.into_string())
}

fn adapter_header(adapter: &Adapter) -> String {
    let mut writer = Writer::new();
    writer.write(format_args!("{C_HEADER}\n#ifndef PTFKIT_USDA_TEXTURE_ADAPTER_H\n#define PTFKIT_USDA_TEXTURE_ADAPTER_H\n\n#include <math.h>\n#include <stdint.h>\n\ntypedef struct {{ double sand; double silt; double clay; }} ptfkit_usda_texture_fractions;\n\nstatic inline ptfkit_usda_texture_fractions ptfkit_usda_texture_to_fractions(uint8_t value) {{\n    switch (value) {{\n"));
    writer.indented(|writer| {
        for (code, row) in adapter.representatives.iter().enumerate() {
            writer.line(format_args!(
                "case {code}: return (ptfkit_usda_texture_fractions){{{}, {}, {}}};",
                row.values["sand"], row.values["silt"], row.values["clay"]
            ));
        }
    });
    writer.write(
        "    default: return (ptfkit_usda_texture_fractions){NAN, NAN, NAN};\n    }\n}\n\n#endif\n",
    );
    writer.into_string()
}

fn output_count(output: &Output) -> usize {
    match output {
        Output::Scalar => 1,
        Output::Struct(fields) => fields.len(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn entry_source_initializes_the_private_module() {
        let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .unwrap();
        let adapters = Registry::load(root).unwrap();
        let rendered = render(&[], &adapters).unwrap();
        let entry = &rendered
            .iter()
            .find(|file| file.path == std::path::Path::new("src/ptfkit/ptfkit.c"))
            .unwrap()
            .contents;
        assert!(entry.contains("PyInit__ptfkit"));
        assert!(!entry.contains("#include \"ufunc.h\""));
    }
}
