use anyhow::Result;

use crate::{
    model::{CompiledFunction, Output},
    output::GeneratedFile,
    render::Writer,
    targets::{group_by_source, native::c_result_name},
};

use super::C_HEADER;

pub(crate) fn render(functions: &[CompiledFunction]) -> Result<Vec<GeneratedFile>> {
    let sources = group_by_source(functions);
    let mut writes = Vec::new();
    for (slug, functions) in &sources {
        let register = format!("ptfkit_register_{slug}");
        let mut source = Writer::new();
        source.write(C_HEADER);
        source.write(format_args!(
            "#include <ptfkit/{slug}.h>\n#include \"ufunc.h\"\n\n"
        ));
        for function in functions {
            source.write(ufunc(function)?);
        }
        source.line(format_args!("int {register}(PyObject *module) {{"));
        source.indented(|writer| {
            for function in functions {
                writer.line(format_args!(
                    "if (ptfkit_add_ufunc(module, \"{name}\", {name}_types, {nin}, {nout}, &{name}_spec) < 0) return -1;",
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
#define NPY_TARGET_VERSION NPY_2_0_API_VERSION
#include <Python.h>
#include <numpy/arrayobject.h>
#include <numpy/ufuncobject.h>"#,
    );
    entry.blank_line();
    for slug in sources.keys() {
        entry.line(format_args!("#include \"{slug}.c\""));
    }
    entry.write("\n\nstatic struct PyModuleDef module_def = { PyModuleDef_HEAD_INIT, \"_ptfkit\", NULL, -1, NULL };\n\nPyMODINIT_FUNC PyInit__ptfkit(void) {\n");
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
    Ok(writes)
}

fn ufunc(function: &CompiledFunction) -> Result<String> {
    let name = &function.core.name;
    let inputs = &function.core.inputs;
    let specification = &function.entry.spec.functions[function.function_index];
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
    let mut writer = Writer::new();
    writer.line(format_args!(
        "static const int {name}_types[] = {{{}}};",
        specification
            .inputs
            .iter()
            .map(|input| {
                if input.enum_type().is_some() {
                    "NPY_UINT32"
                } else {
                    "NPY_DOUBLE"
                }
            })
            .chain(std::iter::repeat_n("NPY_DOUBLE", values.len()))
            .collect::<Vec<_>>()
            .join(", "),
    ));
    writer.line(format_args!(
        "static int {name}_contiguous_loop(PyArrayMethod_Context *context, char *const *data, const npy_intp *dimensions, const npy_intp *strides, NpyAuxData *transferdata) {{"
    ));
    writer.indented(|writer| {
        writer.line("(void)context;");
        writer.line("(void)strides;");
        writer.line("(void)transferdata;");
        for (index, input) in inputs.iter().enumerate() {
            let value_type = if specification.inputs[index].enum_type().is_some() {
                "npy_uint32"
            } else {
                "double"
            };
            writer.line(format_args!(
                "const {value_type} *in_{input} = (const {value_type} *)data[{index}];"
            ));
        }
        for (index, value) in values.iter().enumerate() {
            writer.line(format_args!(
                "double *out_{value} = (double *)data[{}];",
                inputs.len() + index
            ));
        }
        writer.line("for (npy_intp index = 0; index < dimensions[0]; index++) {");
        writer.indented(|writer| {
            for input in inputs {
                let input_index = inputs
                    .iter()
                    .position(|item| item == input)
                    .expect("input exists");
                let value_type = if specification.inputs[input_index].enum_type().is_some() {
                    "npy_uint32"
                } else {
                    "double"
                };
                writer.line(format_args!(
                    "const {value_type} {input} = in_{input}[index];"
                ));
            }
            render_kernel_call(writer, function, inputs, &values, Some("[index]"));
        });
        writer.line("}");
        writer.line("return 0;");
    });
    writer.line("}");
    writer.blank_line();
    writer.line(format_args!(
        "static int {name}_strided_loop(PyArrayMethod_Context *context, char *const *data, const npy_intp *dimensions, const npy_intp *strides, NpyAuxData *transferdata) {{"
    ));
    writer.indented(|writer| {
        writer.line("(void)context;");
        writer.line("(void)transferdata;");
        writer.line("for (npy_intp index = 0; index < dimensions[0]; index++) {");
        writer.indented(|writer| {
            for (index, input) in inputs.iter().enumerate() {
                let value_type = if specification.inputs[index].enum_type().is_some() {
                    "npy_uint32"
                } else {
                    "double"
                };
                writer.line(format_args!("const {value_type} {input} = *(const {value_type} *)(data[{index}] + index * strides[{index}]);"));
            }
            render_kernel_call(writer, function, inputs, &values, None);
        });
        writer.line("}");
        writer.line("return 0;");
    });
    writer.line("}");
    writer.write(format_args!(
        "static PyType_Slot {name}_slots[] = {{\n    {{NPY_METH_strided_loop, {name}_strided_loop}},\n    {{NPY_METH_contiguous_loop, {name}_contiguous_loop}},\n    {{0, NULL}},\n}};\nstatic PyArrayMethod_Spec {name}_spec = {{\n    .name = \"{name}\",\n    .nin = {},\n    .nout = {},\n    .casting = NPY_SAME_KIND_CASTING,\n    .slots = {name}_slots,\n}};\n\n",
        inputs.len(),
        values.len(),
    ));
    Ok(writer.into_string())
}

fn render_kernel_call(
    writer: &mut Writer,
    function: &CompiledFunction,
    inputs: &[String],
    values: &[String],
    output_index: Option<&str>,
) {
    let arguments = inputs.join(", ");
    let result = match &function.core.output {
        Output::Scalar => "double".to_owned(),
        Output::Struct(_) => c_result_name(
            function.entry.spec.functions[function.function_index]
                .result_class()
                .expect("record output has a result class"),
        ),
    };
    writer.line(format_args!(
        "const {result} ptfkit_result = {}({arguments});",
        function.core.name
    ));
    for (index, value) in values.iter().enumerate() {
        let result_value = match &function.core.output {
            Output::Scalar => "ptfkit_result".to_owned(),
            Output::Struct(_) => format!("ptfkit_result.{value}"),
        };
        match output_index {
            None => writer.line(format_args!(
                "*(double *)(data[{}] + index * strides[{}]) = {result_value};",
                inputs.len() + index,
                inputs.len() + index
            )),
            Some(output_index) => {
                writer.line(format_args!("out_{value}{output_index} = {result_value};"))
            }
        }
    }
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
