use anyhow::Result;

use crate::model::{CompiledFunction, Output};

use super::{
    super::{
        c_expression::{self, Dialect},
        group_by_source,
    },
    C_HEADER,
};

pub(crate) fn render(functions: &[CompiledFunction]) -> Result<Vec<(String, String)>> {
    let mut includes = String::new();
    let mut registers = Vec::new();
    let mut writes = Vec::new();
    for (slug, functions) in group_by_source(functions) {
        let register = format!("ptfkit_register_{slug}");
        registers.push(register.clone());
        let mut definitions = String::new();
        let mut calls = String::new();
        for function in functions {
            definitions.push_str(&ufunc(function)?);
            calls.push_str(&format!(
                "    if (ptfkit_add_ufunc(module, \"{name}\", {name}_functions, {name}_types, {nin}, {nout}) < 0) return -1;\n",
                name = function.core.name,
                nin = function.core.inputs.len(),
                nout = output_count(&function.core.output),
            ));
        }
        includes.push_str(&format!("#include \"{slug}.c\"\n"));
        writes.push((
            format!("src/ptfkit/{slug}.c"),
            format!(
                "{C_HEADER}#include \"ufunc.h\"\n\n{definitions}int {register}(PyObject *module) {{\n{calls}    return 0;\n}}\n"
            ),
        ));
    }
    let calls = registers
        .iter()
        .map(|register| {
            format!("    if ({register}(module) < 0) {{ Py_DECREF(module); return NULL; }}\n")
        })
        .collect::<String>();
    writes.push((
        "src/ptfkit/ptfkit.c".into(),
        format!(
            "{C_HEADER}#define PY_SSIZE_T_CLEAN\n#define PY_ARRAY_UNIQUE_SYMBOL PTFKIT_ARRAY_API\n#include <Python.h>\n#include <numpy/arrayobject.h>\n#include <numpy/ufuncobject.h>\n\n{includes}\nstatic struct PyModuleDef module_def = {{ PyModuleDef_HEAD_INIT, \"_ptfkit\", NULL, -1, NULL }};\n\nPyMODINIT_FUNC PyInit__ptfkit(void) {{\n    PyObject *module = PyModule_Create(&module_def);\n    if (module == NULL) return NULL;\n    import_array();\n    import_ufunc();\n{calls}    return module;\n}}\n"
        ),
    ));
    Ok(writes)
}

fn ufunc(function: &CompiledFunction) -> Result<String> {
    let name = &function.core.name;
    let inputs = &function.core.inputs;
    let mut locals = String::new();
    for (index, input) in inputs.iter().enumerate() {
        locals.push_str(&format!(
            "        const double {input} = *(const double *)args[{index}];\n"
        ));
    }
    for variable in &function.ir.variables {
        locals.push_str(&format!(
            "        const double {} = {};\n",
            variable.name,
            c_expression::render(
                &variable.expression,
                inputs,
                &function.ir.variables,
                Dialect::C,
            )
        ));
    }
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
    let writes = values
        .iter()
        .enumerate()
        .map(|(index, value)| {
            format!(
                "        *(double *)args[{}] = {value};\n",
                inputs.len() + index
            )
        })
        .collect::<String>();
    let types = std::iter::repeat_n("NPY_DOUBLE", inputs.len() + values.len())
        .collect::<Vec<_>>()
        .join(", ");
    Ok(format!(
        "static void {name}_loop(char **args, const npy_intp *dimensions, const npy_intp *steps, void *data) {{\n    npy_intp index;\n    for (index = 0; index < dimensions[0]; index++) {{\n{locals}{writes}        for (int arg = 0; arg < {}; arg++) args[arg] += steps[arg];\n    }}\n}}\nstatic PyUFuncGenericFunction {name}_functions[] = {{ {name}_loop }};\nstatic char {name}_types[] = {{ {types} }};\n\n",
        inputs.len() + values.len()
    ))
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
        let entry = rendered.last().unwrap().1.as_str();
        assert!(entry.contains("PyInit__ptfkit"));
        assert!(!entry.contains("#include \"ufunc.h\""));
    }
}
