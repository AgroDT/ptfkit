use std::collections::BTreeMap;

use anyhow::Result;

use crate::{
    model::{CompiledFunction, Output},
    semantic::{BinaryOp, Expr, MathFunction, Reference, UnaryOp},
};

use super::C_HEADER;

pub(crate) fn render(functions: &[CompiledFunction]) -> Result<Vec<(String, String)>> {
    let mut sources = BTreeMap::<String, Vec<&CompiledFunction>>::new();
    for function in functions {
        sources
            .entry(function.entry.slug.clone())
            .or_default()
            .push(function);
    }
    let mut includes = String::new();
    let mut registers = Vec::new();
    let mut writes = Vec::new();
    for (slug, functions) in sources {
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
            expression(&variable.expression, inputs, &function.ir.variables)?.text
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

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
enum Precedence {
    Sum,
    Product,
    Unary,
    Primary,
}

struct RenderedExpression {
    text: String,
    precedence: Precedence,
}

impl RenderedExpression {
    fn binary_operand(&self, parent: Precedence, is_right: bool) -> String {
        let needs_parentheses = self.precedence < parent || (is_right && self.precedence == parent);
        match needs_parentheses {
            true => format!("({})", self.text),
            false => self.text.clone(),
        }
    }

    fn unary_operand(&self) -> String {
        match self.precedence <= Precedence::Unary {
            true => format!("({})", self.text),
            false => self.text.clone(),
        }
    }
}

fn expression(
    expr: &Expr,
    inputs: &[String],
    variables: &[crate::semantic::Variable],
) -> Result<RenderedExpression> {
    Ok(match expr {
        Expr::Number(number) => primary(c_float_literal(&number.lexeme)),
        Expr::Reference(Reference::Input(index)) => primary(inputs[*index].clone()),
        Expr::Reference(Reference::Variable(index)) => primary(variables[*index].name.clone()),
        Expr::Unary { op, operand } => match op {
            UnaryOp::Plus => expression(operand, inputs, variables)?,
            UnaryOp::Minus => {
                let operand = expression(operand, inputs, variables)?.unary_operand();
                RenderedExpression {
                    text: format!("-{operand}"),
                    precedence: Precedence::Unary,
                }
            }
        },
        Expr::Binary { op, left, right } => {
            let left = expression(left, inputs, variables)?;
            let right = expression(right, inputs, variables)?;
            match op {
                BinaryOp::Add => binary(left, right, Precedence::Sum, "+"),
                BinaryOp::Subtract => binary(left, right, Precedence::Sum, "-"),
                BinaryOp::Multiply => binary(left, right, Precedence::Product, "*"),
                BinaryOp::Divide => binary(left, right, Precedence::Product, "/"),
                BinaryOp::Power => primary(format!("pow({}, {})", left.text, right.text)),
            }
        }
        Expr::Call { function, args } => {
            let args = args
                .iter()
                .map(|arg| expression(arg, inputs, variables))
                .collect::<Result<Vec<_>>>()?;
            match function {
                MathFunction::Sqrt => primary(format!("sqrt({})", args[0].text)),
                MathFunction::Exp => primary(format!("exp({})", args[0].text)),
                MathFunction::Ln => primary(format!("log({})", args[0].text)),
                MathFunction::Log10 => primary(format!("log10({})", args[0].text)),
                MathFunction::Abs => primary(format!("fabs({})", args[0].text)),
                MathFunction::Min => primary(format!("fmin({}, {})", args[0].text, args[1].text)),
                MathFunction::Max => primary(format!("fmax({}, {})", args[0].text, args[1].text)),
            }
        }
    })
}

fn c_float_literal(lexeme: &str) -> String {
    match lexeme.contains(['.', 'e', 'E']) {
        true => lexeme.to_owned(),
        false => format!("{lexeme}.0"),
    }
}

fn primary(text: String) -> RenderedExpression {
    RenderedExpression {
        text,
        precedence: Precedence::Primary,
    }
}

fn binary(
    left: RenderedExpression,
    right: RenderedExpression,
    precedence: Precedence,
    operator: &str,
) -> RenderedExpression {
    let left = left.binary_operand(precedence, false);
    let right = right.binary_operand(precedence, true);
    RenderedExpression {
        text: format!("{left} {operator} {right}"),
        precedence,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::semantic::{BinaryOp, Reference};

    #[test]
    fn entry_source_initializes_the_private_module() {
        let rendered = render(&[]).unwrap();
        let entry = rendered.last().unwrap().1.as_str();
        assert!(entry.contains("PyInit__ptfkit"));
        assert!(!entry.contains("#include \"ufunc.h\""));
    }

    #[test]
    fn omits_parentheses_when_precedence_preserves_the_expression() {
        let inputs = vec!["x".into(), "y".into(), "z".into()];
        let variables = Vec::new();
        let input = |index| Expr::Reference(Reference::Input(index));
        let binary = |op, left, right| Expr::Binary {
            op,
            left: Box::new(left),
            right: Box::new(right),
        };
        let cases = [
            (
                binary(
                    BinaryOp::Add,
                    input(0),
                    binary(BinaryOp::Multiply, input(1), input(2)),
                ),
                "x + y * z",
            ),
            (
                binary(
                    BinaryOp::Multiply,
                    binary(BinaryOp::Add, input(0), input(1)),
                    input(2),
                ),
                "(x + y) * z",
            ),
            (
                binary(
                    BinaryOp::Subtract,
                    input(0),
                    binary(BinaryOp::Subtract, input(1), input(2)),
                ),
                "x - (y - z)",
            ),
            (
                binary(
                    BinaryOp::Power,
                    binary(BinaryOp::Add, input(0), input(1)),
                    input(2),
                ),
                "pow(x + y, z)",
            ),
        ];
        for (expr, expected) in cases {
            assert_eq!(
                expression(&expr, &inputs, &variables).unwrap().text,
                expected
            );
        }
    }

    #[test]
    fn preserves_number_lexemes_in_c_literals() {
        assert_eq!(c_float_literal("1"), "1.0");
        assert_eq!(c_float_literal("1.00"), "1.00");
        assert_eq!(c_float_literal(".5e1"), ".5e1");
    }
}
