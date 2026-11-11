//! Emit dense-model calculation functions from the shared semantic IR.
use crate::{
    model::{Entry, ExternalModel},
    semantic::{
        self, Expr, Reference, VariableValue,
        neural::{Condition, Operation},
    },
};
use std::fmt::Write as _;

pub(super) struct Rendered {
    pub(super) c: String,
    pub(super) rust: String,
}

fn reference(reference: Reference, ir: &semantic::Function) -> &str {
    match reference {
        Reference::Input(i) => &ir.inputs[i].name,
        Reference::Variable(i) => &ir.variables[i].name,
    }
}

fn expression(
    expr: &Expr,
    inputs: &[String],
    ir: &semantic::Function,
    rust: bool,
) -> anyhow::Result<String> {
    if rust {
        Ok(crate::targets::rust::render_expression(
            expr,
            inputs,
            &ir.variables,
        )?)
    } else {
        Ok(
            crate::render::c::expression(expr, inputs, &ir.variables, crate::render::c::Dialect::C)
                .to_string(),
        )
    }
}

fn condition(
    c: &Condition,
    inputs: &[String],
    ir: &semantic::Function,
    rust: bool,
) -> anyhow::Result<String> {
    let left = expression(&c.left, inputs, ir, rust)?;
    let right = expression(&c.right, inputs, ir, rust)?;
    use crate::model::NeuralComparison::*;
    Ok(if rust {
        let order = match c.op {
            Lt => "Some(std::cmp::Ordering::Less)",
            Le => "Some(std::cmp::Ordering::Less | std::cmp::Ordering::Equal)",
            Gt => "Some(std::cmp::Ordering::Greater)",
            Ge => "Some(std::cmp::Ordering::Greater | std::cmp::Ordering::Equal)",
        };
        format!("matches!(({left}).partial_cmp(&({right})),{order})")
    } else {
        let op = match c.op {
            Lt => "<",
            Le => "<=",
            Gt => ">",
            Ge => ">=",
        };
        format!("({left} {op} {right})")
    })
}

pub(super) fn render_function(
    ir: &semantic::Function,
    outputs: &[String],
    level: usize,
    rust: bool,
) -> anyhow::Result<String> {
    let inputs = ir.inputs.iter().map(|i| i.name.clone()).collect::<Vec<_>>();
    let count = inputs.len();
    let size = outputs.len();
    let mut text = if rust {
        format!(
            "fn mod{level}(_ptfkit_networks:&[Network],_ptfkit_data:&[f64],_ptfkit_mode:usize,_ptfkit_inputs:&[f64])->Option<[f64;{size}]>{{\nif _ptfkit_mode>2 || _ptfkit_inputs.len()!={count} || _ptfkit_inputs.iter().any(|v|!v.is_finite()) {{return None;}}\n"
        )
    } else {
        format!(
            "PTFKIT_MODEL_INLINE int ptfkit_detail_rosetta_mod{level}(const ptfkit_detail_network *_ptfkit_networks,const double *_ptfkit_data,unsigned _ptfkit_mode,const double *_ptfkit_inputs,size_t _ptfkit_count,double *_ptfkit_out){{\nif(!_ptfkit_inputs || !_ptfkit_out)return 0;\nfor(size_t i=0;i<{size};++i)_ptfkit_out[i]=NAN;\nif(_ptfkit_mode>2 || _ptfkit_count!={count})return 0;\nfor(size_t i=0;i<_ptfkit_count;++i)if(!isfinite(_ptfkit_inputs[i]))return 0;\n"
        )
    };
    for (i, name) in inputs.iter().enumerate() {
        if rust {
            writeln!(text, "let {name}:f64=_ptfkit_inputs[{i}];")?;
        } else {
            writeln!(text, "const double {name}=_ptfkit_inputs[{i}];")?;
        }
    }
    for (index, variable) in ir.variables.iter().enumerate() {
        let name = &variable.name;
        match &variable.value {
            VariableValue::Expression(e) => {
                let value = expression(e, &inputs, ir, rust)?;
                if rust {
                    writeln!(text, "let {name}:f64={value};")?;
                } else {
                    writeln!(text, "const double {name}={value};")?;
                }
            }
            VariableValue::Neural(op) => match op.as_ref() {
                Operation::Network {
                    definition,
                    arguments,
                    when,
                } => {
                    let width = definition.outputs.len();
                    let members = definition.members;
                    let net = definition.parameters.network;
                    let args = arguments
                        .iter()
                        .map(|a| expression(a, &inputs, ir, rust))
                        .collect::<anyhow::Result<Vec<_>>>()?
                        .join(",");
                    let conditions = when
                        .iter()
                        .map(|c| condition(c, &inputs, ir, rust))
                        .collect::<anyhow::Result<Vec<_>>>()?
                        .join(" && ");
                    if rust {
                        let prediction =
                            format!("_ptfkit_networks[{net}].predict(_ptfkit_data,&[{args}])");
                        if when.is_empty() {
                            writeln!(text, "let {name}={prediction};")?;
                        } else {
                            writeln!(
                                text,
                                "let {name}=if {conditions} {{{prediction}}}else{{vec![vec![f64::NAN;{width}];{members}]}};"
                            )?;
                        }
                    } else {
                        writeln!(text, "double {name}[{}];", members * width)?;
                        if !when.is_empty() {
                            writeln!(
                                text,
                                "for(size_t i=0;i<{};++i){name}[i]=NAN;\nif({conditions}){{",
                                members * width
                            )?;
                        }
                        writeln!(
                            text,
                            "const double _ptfkit_{name}_inputs[]={{{args}}};\nptfkit_detail_network_predict(&_ptfkit_networks[{net}],_ptfkit_data,_ptfkit_{name}_inputs,{name});"
                        )?;
                        if !when.is_empty() {
                            text.push_str("}\n");
                        }
                    }
                }
                Operation::Transform {
                    source,
                    ensemble,
                    expressions,
                } => {
                    let source = reference(*source, ir);
                    let width = ensemble.fields.len();
                    let members = ensemble.members;
                    let aliases = ensemble
                        .fields
                        .iter()
                        .map(|f| format!("member_{f}"))
                        .collect::<Vec<_>>();
                    if rust {
                        writeln!(text, "let {name}={source}.iter().map(|row|{{")?;
                    } else {
                        writeln!(
                            text,
                            "double {name}[{}];\nfor(size_t member=0;member<{members};++member){{",
                            members * width
                        )?;
                    }
                    for (i, alias) in aliases.iter().enumerate() {
                        if rust {
                            writeln!(text, "let {alias}:f64=row[{i}];")?;
                        } else {
                            writeln!(text, "const double {alias}={source}[member*{width}+{i}];")?;
                        }
                    }
                    let values = expressions
                        .iter()
                        .map(|e| expression(e, &aliases, ir, rust))
                        .collect::<anyhow::Result<Vec<_>>>()?;
                    if rust {
                        writeln!(
                            text,
                            "vec![{}]}}).collect::<Vec<Vec<f64>>>();",
                            values.join(",")
                        )?;
                    } else {
                        for (i, value) in values.iter().enumerate() {
                            writeln!(text, "{name}[member*{width}+{i}]={value};")?;
                        }
                        text.push_str("}\n");
                    }
                }
                Operation::Statistics {
                    source,
                    ensemble,
                    output,
                } => {
                    let source = reference(*source, ir);
                    let width = ensemble.fields.len();
                    let members = ensemble.members;
                    if rust {
                        writeln!(text, "#[allow(dead_code)]\nstruct Statistics{index}{{")?;
                        for field in &output.fields {
                            writeln!(text, "{field}:f64,")?;
                        }
                        writeln!(
                            text,
                            "}}\nlet ({name}_mean,{name}_std)=statistics(&{source});\nlet {name}=Statistics{index}{{"
                        )?;
                        for (i, field) in output.fields.iter().enumerate() {
                            let stat = if i < width { "mean" } else { "std" };
                            writeln!(text, "{field}:{name}_{stat}[{}],", i % width)?;
                        }
                        text.push_str("};\n");
                    } else {
                        text.push_str("struct{\n");
                        for field in &output.fields {
                            writeln!(text, "double {field};")?;
                        }
                        writeln!(
                            text,
                            "}}{name};\ndouble {name}_mean[{width}],{name}_std[{width}];\nptfkit_detail_stats({source},{members},{width},{name}_mean,{name}_std);"
                        )?;
                        for (i, field) in output.fields.iter().enumerate() {
                            let stat = if i < width { "mean" } else { "std" };
                            writeln!(text, "{name}.{field}={name}_{stat}[{}];", i % width)?;
                        }
                    }
                }
                Operation::Estimate {
                    arithmetic,
                    log10,
                    geometric,
                } => {
                    let a = expression(arithmetic, &inputs, ir, rust)?;
                    let l = expression(log10, &inputs, ir, rust)?;
                    let g = expression(geometric, &inputs, ir, rust)?;
                    if rust {
                        writeln!(
                            text,
                            "let {name}:f64=match _ptfkit_mode{{0=>{a},1=>{l},_=>{g}}};"
                        )?;
                    } else {
                        writeln!(
                            text,
                            "const double {name}=_ptfkit_mode==0 ? {a} : _ptfkit_mode==1 ? {l} : {g};"
                        )?;
                    }
                }
                Operation::Require(conditions) => {
                    for c in conditions {
                        let valid = condition(c, &inputs, ir, rust)?;
                        if rust {
                            writeln!(text, "if !{valid} {{return None;}}")?;
                        } else {
                            writeln!(text, "if(!{valid})return 0;")?;
                        }
                    }
                }
            },
            _ => anyhow::bail!("dense backend received a non-neural structural operation"),
        }
    }
    if rust {
        writeln!(text, "Some([{}])\n}}", outputs.join(","))?;
    } else {
        for (i, name) in outputs.iter().enumerate() {
            writeln!(text, "_ptfkit_out[{i}]={name};")?;
        }
        text.push_str("return 1;}\n");
    }
    Ok(text)
}

pub(super) fn render(entry: &Entry) -> anyhow::Result<Rendered> {
    let mut c = String::new();
    let mut rust = String::from("use super::engine::{Network,statistics};\n");
    let mut levels = Vec::new();
    for (index, function) in entry
        .spec
        .functions
        .iter()
        .enumerate()
        .filter(|(_, f)| super::public::enabled(f))
    {
        let ExternalModel { level, .. } = function
            .implementation
            .as_ref()
            .unwrap()
            .external_model
            .as_ref()
            .unwrap();
        let ir = entry.implementations[index]
            .as_ref()
            .expect("neural implementations are compiled with the source");
        let outputs = function
            .outputs
            .fields()
            .iter()
            .map(|f| f.name.clone())
            .collect::<Vec<_>>();
        c.push_str(&render_function(ir, &outputs, *level, false)?);
        rust.push_str(&render_function(ir, &outputs, *level, true)?);
        levels.push(*level);
    }
    c.push_str("PTFKIT_MODEL_INLINE int ptfkit_detail_rosetta(const ptfkit_detail_network *networks,const double *data,unsigned level,unsigned mode,const double *x,size_t count,double *out){switch(level){\n");
    rust.push_str("pub(super) fn predict(networks:&[Network],data:&[f64],level:usize,mode:usize,x:&[f64])->Option<[f64;14]>{match level{\n");
    for level in levels {
        writeln!(
            c,
            "case {level}:return ptfkit_detail_rosetta_mod{level}(networks,data,mode,x,count,out);"
        )?;
        writeln!(rust, "{level}=>mod{level}(networks,data,mode,x),")?;
    }
    c.push_str("default:return 0;}}\n");
    rust.push_str("_=>None,}}\n");
    Ok(Rendered { c, rust })
}
