use anyhow::Result;

use crate::model::{CompiledFunction, Output};
use crate::render::Writer;

use super::{
    super::{
        GeneratedFile,
        c_expression::{self, Dialect},
        group_by_source,
    },
    C_HEADER,
};

pub(crate) fn render(functions: &[CompiledFunction]) -> Result<Vec<GeneratedFile>> {
    let mut includes = Writer::new();
    let mut registers = Vec::new();
    let mut writes = Vec::new();
    for (slug, functions) in group_by_source(functions) {
        let register = format!("ptfkit_register_{slug}");
        registers.push(register.clone());
        let mut definitions = Writer::new();
        let mut calls = Writer::new();
        for function in functions {
            definitions.write(ufunc(function)?);
            calls.line(format_args!(
                "if (ptfkit_add_ufunc(module, \"{name}\", {name}_functions, {name}_types, {nin}, {nout}) < 0) return -1;",
                name = function.core.name,
                nin = function.core.inputs.len(),
                nout = output_count(&function.core.output),
            ));
        }
        includes.line(format_args!("#include \"{slug}.c\""));
        let mut source = Writer::new();
        source.write(C_HEADER);
        source.line("#include \"ufunc.h\"");
        source.blank_line();
        source.write(definitions.into_string());
        source.line(format_args!("int {register}(PyObject *module) {{"));
        source.indented(|writer| {
            writer.write(calls.into_string());
            writer.line("return 0;");
        });
        source.line("}");
        writes.push(GeneratedFile::new(
            format!("src/ptfkit/{slug}.c").into(),
            source.into_string(),
        ));
    }
    let mut calls = Writer::new();
    for register in &registers {
        calls.line(format_args!(
            "if ({register}(module) < 0) {{ Py_DECREF(module); return NULL; }}"
        ));
    }
    let mut entry = Writer::new();
    entry.write(C_HEADER);
    entry.line("#define PY_SSIZE_T_CLEAN");
    entry.line("#define PY_ARRAY_UNIQUE_SYMBOL PTFKIT_ARRAY_API");
    entry.line("#include <Python.h>");
    entry.line("#include <numpy/arrayobject.h>");
    entry.line("#include <numpy/ufuncobject.h>");
    entry.blank_line();
    entry.write(includes.into_string());
    entry.blank_line();
    entry.line("static struct PyModuleDef module_def = { PyModuleDef_HEAD_INIT, \"_ptfkit\", NULL, -1, NULL };");
    entry.blank_line();
    entry.line("PyMODINIT_FUNC PyInit__ptfkit(void) {");
    entry.indented(|writer| {
        writer.line("PyObject *module = PyModule_Create(&module_def);");
        writer.line("if (module == NULL) return NULL;");
        writer.line("import_array();");
        writer.line("import_ufunc();");
        writer.write(calls.into_string());
        writer.line("return module;");
    });
    entry.line("}");
    writes.push(GeneratedFile::new(
        "src/ptfkit/ptfkit.c".into(),
        entry.into_string(),
    ));
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
    let types = std::iter::repeat_n("NPY_DOUBLE", inputs.len() + values.len())
        .collect::<Vec<_>>()
        .join(", ");
    let mut writer = Writer::new();
    writer.line(format_args!("static void {name}_loop(char **args, const npy_intp *dimensions, const npy_intp *steps, void *data) {{"));
    writer.indented(|writer| {
        writer.line("npy_intp index;");
        writer.line("for (index = 0; index < dimensions[0]; index++) {");
        writer.indented(|writer| {
            for (index, input) in inputs.iter().enumerate() {
                writer.line(format_args!(
                    "const double {input} = *(const double *)args[{index}];"
                ));
            }
            for variable in &function.ir.variables {
                writer.write(format_args!("const double {} = ", variable.name));
                writer.write(c_expression::expression(
                    &variable.expression,
                    inputs,
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
    writer.line(format_args!(
        "static PyUFuncGenericFunction {name}_functions[] = {{ {name}_loop }};"
    ));
    writer.line(format_args!("static char {name}_types[] = {{ {types} }};"));
    writer.blank_line();
    Ok(writer.into_string())
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
        let rendered = render(&[]).unwrap();
        let entry = &rendered.last().unwrap().contents;
        assert!(entry.contains("PyInit__ptfkit"));
        assert!(!entry.contains("#include \"ufunc.h\""));
    }
}
