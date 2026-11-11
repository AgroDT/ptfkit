//! Compile a declarative ensemble graph into C and Rust computation.
use super::{Manifest, ModelError};
use serde::Deserialize;
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt::Write as _,
    path::Path,
};

#[cfg(test)]
#[path = "pipeline_tests.rs"]
mod tests;

type Result<T> = std::result::Result<T, ModelError>;

fn require(ok: bool, reason: &'static str) -> Result<()> {
    if ok {
        Ok(())
    } else {
        Err(ModelError::Pipeline { reason })
    }
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct Program {
    format_version: usize,
    network_manifest: String,
    levels: BTreeMap<usize, usize>,
    estimates: usize,
    outputs: usize,
    input_conditions: Vec<Condition>,
    nodes: Vec<Node>,
}

#[derive(Deserialize)]
#[serde(untagged)]
enum Scalar {
    Number(f64),
    Reference(String),
    Sum { sum: Vec<Scalar> },
}

impl Scalar {
    fn evaluate(&self, values: &BTreeMap<String, Vec<Vec<f64>>>) -> f64 {
        match self {
            Self::Number(n) => *n,
            Self::Reference(reference) => {
                let (name, index) = reference
                    .split_once('.')
                    .expect("validated scalar reference");
                values[name][0][index.parse::<usize>().expect("validated scalar index")]
            }
            Self::Sum { sum } => sum.iter().map(|s| s.evaluate(values)).sum(),
        }
    }
}

impl Condition {
    fn evaluate(&self, values: &BTreeMap<String, Vec<Vec<f64>>>) -> bool {
        let left = self.left.evaluate(values);
        let right = self.right.evaluate(values);
        match self.op {
            Comparison::Lt => left < right,
            Comparison::Le => left <= right,
            Comparison::Gt => left > right,
            Comparison::Ge => left >= right,
        }
    }
}

impl Program {
    pub(super) fn valid(&self, level: usize, x: &[f64]) -> bool {
        if self.levels.get(&level) != Some(&x.len()) || x.iter().any(|v| !v.is_finite()) {
            return false;
        }
        let values = BTreeMap::from([("x".into(), vec![x.to_vec()])]);
        self.input_conditions
            .iter()
            .all(|c| level < c.minimum_level || c.evaluate(&values))
    }

    /// Generic interpreter used by the local verification command, never a scientific adapter.
    pub(super) fn evaluate(
        &self,
        networks: &[super::engine::Network],
        data: &[f64],
        level: usize,
        mode: usize,
        x: &[f64],
    ) -> Option<Vec<f64>> {
        if !self.valid(level, x) || mode >= self.estimates {
            return None;
        }
        let mut values = BTreeMap::from([("x".into(), vec![x.to_vec()])]);
        let mut out = vec![f64::NAN; self.outputs];
        for node in &self.nodes {
            let result = match &node.operation {
                Operation::Network {
                    networks: selection,
                    source,
                } => Some(networks[selection[&level]].predict(data, &values[source][0])),
                Operation::Pow10 { source, columns } => {
                    let mut result = values[source].clone();
                    for row in &mut result {
                        for col in columns {
                            row[*col] = 10.0_f64.powf(row[*col]);
                        }
                    }
                    Some(result)
                }
                Operation::Statistics { source, .. } => {
                    let (mean, std) = super::engine::statistics(&values[source]);
                    values.insert(format!("{}_mean", node.id), vec![mean]);
                    values.insert(format!("{}_std", node.id), vec![std]);
                    None
                }
                Operation::Select { choices } => Some(values[&choices[mode]].clone()),
                Operation::Gather { values: scalars } => {
                    Some(vec![scalars.iter().map(|s| s.evaluate(&values)).collect()])
                }
                Operation::Guard { conditions } => {
                    if conditions
                        .iter()
                        .any(|c| level >= c.minimum_level && !c.evaluate(&values))
                    {
                        return Some(out);
                    }
                    None
                }
                Operation::Store {
                    values: scalars,
                    indices,
                } => {
                    for (scalar, index) in scalars.iter().zip(indices) {
                        out[*index] = scalar.evaluate(&values);
                    }
                    None
                }
            };
            if let Some(result) = result {
                values.insert(node.id.clone(), result);
            }
        }
        Some(out)
    }
}

#[derive(Deserialize)]
#[serde(rename_all = "snake_case")]
enum Comparison {
    Lt,
    Le,
    Gt,
    Ge,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Condition {
    left: Scalar,
    op: Comparison,
    right: Scalar,
    minimum_level: usize,
}

fn level_map<'de, D: serde::Deserializer<'de>>(
    deserializer: D,
) -> std::result::Result<BTreeMap<usize, usize>, D::Error> {
    BTreeMap::<String, usize>::deserialize(deserializer)?
        .into_iter()
        .map(|(k, v)| k.parse().map(|k| (k, v)).map_err(serde::de::Error::custom))
        .collect()
}

#[derive(Deserialize)]
struct Node {
    id: String,
    #[serde(flatten)]
    operation: Operation,
}

#[derive(Deserialize)]
#[serde(tag = "op", rename_all = "snake_case", deny_unknown_fields)]
enum Operation {
    Network {
        #[serde(deserialize_with = "level_map")]
        networks: BTreeMap<usize, usize>,
        source: String,
    },
    Pow10 {
        source: String,
        columns: Vec<usize>,
    },
    Statistics {
        source: String,
        ddof: usize,
    },
    Select {
        choices: Vec<String>,
    },
    Gather {
        values: Vec<Scalar>,
    },
    Guard {
        conditions: Vec<Condition>,
    },
    Store {
        values: Vec<Scalar>,
        indices: Vec<usize>,
    },
}

#[derive(Clone, Copy, PartialEq)]
struct Shape {
    rows: usize,
    width: usize,
}

struct Renderer {
    shapes: BTreeMap<String, Shape>,
    c: String,
    rust: String,
}

impl Renderer {
    fn shape(&self, name: &str) -> Result<Shape> {
        self.shapes.get(name).copied().ok_or(ModelError::Pipeline {
            reason: "unknown or forward graph reference",
        })
    }

    fn register(&mut self, name: &str, shape: Shape) -> Result<()> {
        require(
            !name.is_empty() && name.bytes().all(|c| c.is_ascii_lowercase() || c == b'_'),
            "invalid node identifier",
        )?;
        require(
            shape.rows > 0 && shape.width > 0 && shape.rows * shape.width <= 64000,
            "invalid graph shape",
        )?;
        require(
            self.shapes.insert(name.into(), shape).is_none(),
            "duplicate graph identifier",
        )
    }

    fn scalar(&self, value: &Scalar, rust: bool) -> Result<String> {
        match value {
            Scalar::Number(n) => {
                require(n.is_finite(), "non-finite graph constant")?;
                Ok(format!("{n:?}"))
            }
            Scalar::Reference(reference) => {
                let (name, index) = reference.split_once('.').ok_or(ModelError::Pipeline {
                    reason: "invalid scalar reference",
                })?;
                let index: usize = index.parse().map_err(|_| ModelError::Pipeline {
                    reason: "invalid scalar index",
                })?;
                let shape = self.shape(name)?;
                require(
                    shape.rows == 1 && index < shape.width,
                    "scalar reference outside vector",
                )?;
                Ok(if rust && name != "x" {
                    format!("{name}[0][{index}]")
                } else {
                    format!("{name}[{index}]")
                })
            }
            Scalar::Sum { sum } => {
                require(!sum.is_empty(), "empty scalar sum")?;
                Ok(format!(
                    "({})",
                    sum.iter()
                        .map(|s| self.scalar(s, rust))
                        .collect::<Result<Vec<_>>>()?
                        .join(" + ")
                ))
            }
        }
    }

    fn condition(&self, condition: &Condition, rust: bool) -> Result<String> {
        let left = self.scalar(&condition.left, rust)?;
        let right = self.scalar(&condition.right, rust)?;
        if rust {
            let ordering = match condition.op {
                Comparison::Lt => "Some(std::cmp::Ordering::Less)",
                Comparison::Le => "Some(std::cmp::Ordering::Less | std::cmp::Ordering::Equal)",
                Comparison::Gt => "Some(std::cmp::Ordering::Greater)",
                Comparison::Ge => "Some(std::cmp::Ordering::Greater | std::cmp::Ordering::Equal)",
            };
            Ok(format!(
                "matches!(({left}).partial_cmp(&({right})), {ordering})"
            ))
        } else {
            let operator = match condition.op {
                Comparison::Lt => "<",
                Comparison::Le => "<=",
                Comparison::Gt => ">",
                Comparison::Ge => ">=",
            };
            Ok(format!("({left} {operator} {right})"))
        }
    }
}

pub(super) struct Rendered {
    levels: BTreeMap<usize, usize>,
    outputs: usize,
    estimates: usize,
    pub(super) c: String,
    pub(super) rust: String,
}

impl Rendered {
    pub(super) fn check_contract(
        &self,
        level: usize,
        inputs: usize,
        outputs: usize,
        estimates: usize,
    ) -> Result<()> {
        require(
            self.levels.get(&level) == Some(&inputs)
                && self.outputs == outputs
                && self.estimates == estimates,
            "computation and public method contracts differ",
        )
    }
}

pub(super) fn load(path: &Path, container: Option<&[u8]>) -> anyhow::Result<Rendered> {
    let program: Program = serde_json::from_slice(&std::fs::read(path)?)?;
    require(
        program.network_manifest == "network.json",
        "network manifest must be local network.json",
    )?;
    let manifest: Manifest = serde_json::from_slice(&std::fs::read(
        path.with_file_name(&program.network_manifest),
    )?)?;
    if let Some(container) = container {
        // Authenticate architecture and transformations against the actual parameter container.
        let model = super::Model {
            networks: manifest
                .networks
                .iter()
                .map(|n| super::engine::Network {
                    nboot: n.nboot,
                    widths: n.widths.clone(),
                    activations: n.activations.clone(),
                    offset: n.offset,
                    inputs: n
                        .inputs
                        .iter()
                        .map(|s| super::engine::Scale {
                            kind: s.kind.clone(),
                            params: s.params.clone(),
                        })
                        .collect(),
                    outputs: n
                        .outputs
                        .iter()
                        .map(|s| super::engine::Scale {
                            kind: s.kind.clone(),
                            params: s.params.clone(),
                        })
                        .collect(),
                })
                .collect(),
            data: Vec::new(),
            revision: String::new(),
            contract: serde_json::Value::Null,
        };
        require(
            manifest.format_version == 1
                && model.networks.iter().all(|n| {
                    (2..=17).contains(&n.widths.len())
                        && n.widths.iter().all(|w| (1..=64).contains(w))
                        && (2..=1000).contains(&n.nboot)
                        && n.activations.len() + 1 == n.widths.len()
                        && n.inputs.len() == n.widths[0]
                        && n.outputs.len() == *n.widths.last().unwrap()
                        && n.activations
                            .iter()
                            .all(|a| matches!(a.as_str(), "linear" | "sigmoid" | "tansig" | "relu"))
                })
                && manifest
                    .networks
                    .iter()
                    .all(|n| n.inputs.iter().chain(&n.outputs).all(super::scale_valid)),
            "invalid network manifest",
        )?;
        let metadata = super::pack::encode(&model);
        require(
            container.starts_with(&metadata[..metadata.len() - 8]),
            "network manifest differs from parameter container",
        )?;
    }
    Ok(render(&program, &manifest)?)
}

fn render(program: &Program, manifest: &Manifest) -> Result<Rendered> {
    require(
        program.format_version == 1
            && !program.levels.is_empty()
            && program.estimates > 0
            && program.outputs > 0,
        "invalid computation contract",
    )?;
    let mut r = Renderer {
        shapes: BTreeMap::new(),
        c: String::new(),
        rust: String::new(),
    };
    writeln!(r.c, "PTFKIT_MODEL_INLINE int ptfkit_detail_rosetta(const ptfkit_detail_network *networks,const double *data,unsigned level,unsigned mode,const double *x,size_t count,double *out) {{\nif(!out)return 0;\nfor(size_t i=0;i<{};++i)out[i]=NAN;\nif(!x || mode>={})return 0;\nswitch(level){{", program.outputs, program.estimates).unwrap();
    writeln!(r.rust, "use super::engine::{{Network,statistics}};\npub fn predict(networks:&[Network],data:&[f64],level:usize,mode:usize,x:&[f64])->Option<[f64;{}]> {{\nif mode>={} {{return None;}}\nmatch level {{", program.outputs, program.estimates).unwrap();
    for (level, count) in &program.levels {
        writeln!(r.c, "case {level}:if(count!={count})return 0;break;").unwrap();
        writeln!(r.rust, "{level}=>if x.len()!={count} {{return None;}},").unwrap();
    }
    r.c.push_str("default:return 0;}\nfor(size_t i=0;i<count;++i)if(!isfinite(x[i]))return 0;\n");
    r.rust
        .push_str("_=>return None,}\nif x.iter().any(|v|!v.is_finite()) {return None;}\n");
    for condition in &program.input_conditions {
        let width = program
            .levels
            .iter()
            .filter(|(l, _)| **l >= condition.minimum_level)
            .map(|(_, n)| *n)
            .min()
            .ok_or(ModelError::Pipeline {
                reason: "unreachable input condition",
            })?;
        r.shapes.insert("x".into(), Shape { rows: 1, width });
        writeln!(
            r.c,
            "if(level>={} && !{})return 0;",
            condition.minimum_level,
            r.condition(condition, false)?
        )
        .unwrap();
        writeln!(
            r.rust,
            "if level>={} && !{} {{return None;}}",
            condition.minimum_level,
            r.condition(condition, true)?
        )
        .unwrap();
    }
    r.shapes.insert(
        "x".into(),
        Shape {
            rows: 1,
            width: *program.levels.values().min().unwrap(),
        },
    );
    writeln!(r.rust, "let mut out=[f64::NAN;{}];", program.outputs).unwrap();
    let mut assigned = vec![false; program.outputs];
    let mut identifiers = BTreeSet::new();
    for node in &program.nodes {
        let id = &node.id;
        require(identifiers.insert(id), "duplicate graph node")?;
        require(
            !id.is_empty()
                && id.bytes().all(|c| c.is_ascii_lowercase() || c == b'_')
                && !["x", "out", "data", "networks", "level", "mode", "count"]
                    .contains(&id.as_str())
                && !id.ends_with("_index"),
            "invalid or reserved graph identifier",
        )?;
        // Reserve the identifier even for effect-only nodes.
        require(!r.shapes.contains_key(id), "duplicate graph identifier")?;
        match &node.operation {
            Operation::Network { networks, source } => {
                require(
                    networks.keys().eq(program.levels.keys()),
                    "network selection must cover each level",
                )?;
                let mut shape = None;
                for (level, index) in networks {
                    let net = manifest.networks.get(*index).ok_or(ModelError::Pipeline {
                        reason: "network index outside manifest",
                    })?;
                    require(net.widths.len() >= 2, "empty network architecture")?;
                    let width = if source == "x" {
                        program.levels[level]
                    } else {
                        let s = r.shape(source)?;
                        require(s.rows == 1, "network input must be a vector")?;
                        s.width
                    };
                    require(net.widths[0] == width, "network input width mismatch")?;
                    let current = Shape {
                        rows: net.nboot,
                        width: *net.widths.last().unwrap(),
                    };
                    require(
                        shape.is_none_or(|s| s == current),
                        "selected network output shapes differ",
                    )?;
                    shape = Some(current);
                }
                let shape = shape.unwrap();
                r.register(id, shape)?;
                writeln!(r.c, "size_t {id}_index=0;switch(level){{").unwrap();
                writeln!(r.rust, "let {id}_index=match level{{").unwrap();
                for (level, index) in networks {
                    writeln!(r.c, "case {level}:{id}_index={index};break;").unwrap();
                    writeln!(r.rust, "{level}=>{index},").unwrap();
                }
                r.c.push_str("}\n");
                r.rust.push_str("_=>unreachable!(),};\n");
                writeln!(r.c, "double {id}[{}];ptfkit_detail_network_predict(&networks[{id}_index],data,{source},{id});", shape.rows * shape.width).unwrap();
                let input = if source == "x" {
                    "x".into()
                } else {
                    format!("&{source}[0]")
                };
                writeln!(
                    r.rust,
                    "let {id}=networks[{id}_index].predict(data,{input});"
                )
                .unwrap();
            }
            Operation::Pow10 { source, columns } => {
                require(source != "x", "transform requires a graph matrix")?;
                let shape = r.shape(source)?;
                r.register(id, shape)?;
                require(
                    columns.iter().all(|c| *c < shape.width)
                        && columns.iter().collect::<BTreeSet<_>>().len() == columns.len(),
                    "transformation column outside matrix",
                )?;
                writeln!(
                    r.c,
                    "double {id}[{}];for(size_t i=0;i<{};++i){id}[i]={source}[i];",
                    shape.rows * shape.width,
                    shape.rows * shape.width
                )
                .unwrap();
                writeln!(r.rust, "let mut {id}={source}.clone();").unwrap();
                for col in columns {
                    writeln!(
                        r.c,
                        "for(size_t i=0;i<{};++i){id}[i*{}+{col}]=pow(10.0,{source}[i*{}+{col}]);",
                        shape.rows, shape.width, shape.width
                    )
                    .unwrap();
                    writeln!(
                        r.rust,
                        "for row in &mut {id} {{row[{col}]=10.0_f64.powf(row[{col}]);}}"
                    )
                    .unwrap();
                }
            }
            Operation::Statistics { source, ddof } => {
                require(source != "x", "statistics require a graph matrix")?;
                let s = r.shape(source)?;
                require(
                    *ddof == 1 && s.rows > 1,
                    "statistics require sample standard deviation and an ensemble",
                )?;
                r.register(
                    &format!("{id}_mean"),
                    Shape {
                        rows: 1,
                        width: s.width,
                    },
                )?;
                r.register(
                    &format!("{id}_std"),
                    Shape {
                        rows: 1,
                        width: s.width,
                    },
                )?;
                writeln!(r.c,"double {id}_mean[{}],{id}_std[{}];ptfkit_detail_stats({source},{},{},{id}_mean,{id}_std);",s.width,s.width,s.rows,s.width).unwrap();
                writeln!(r.rust,"let ({id}_mean,{id}_std)=statistics(&{source});\nlet {id}_mean=[{id}_mean];let {id}_std=[{id}_std];").unwrap();
            }
            Operation::Select { choices } => {
                require(
                    choices.len() == program.estimates,
                    "estimate selection does not cover every mode",
                )?;
                let s = r.shape(&choices[0])?;
                for choice in choices {
                    require(choice != "x", "estimate selection requires graph matrices")?;
                    require(r.shape(choice)? == s, "estimate selection shape mismatch")?;
                }
                r.register(id, s)?;
                writeln!(r.c, "const double *{id}=NULL;switch(mode){{").unwrap();
                writeln!(r.rust, "let {id}=match mode{{").unwrap();
                for (mode, choice) in choices.iter().enumerate() {
                    writeln!(r.c, "case {mode}:{id}={choice};break;").unwrap();
                    writeln!(r.rust, "{mode}=>&{choice},").unwrap();
                }
                r.c.push_str("}\n");
                r.rust.push_str("_=>unreachable!(),};\n");
            }
            Operation::Gather { values } => {
                let c = values
                    .iter()
                    .map(|v| r.scalar(v, false))
                    .collect::<Result<Vec<_>>>()?
                    .join(",");
                let rs = values
                    .iter()
                    .map(|v| r.scalar(v, true))
                    .collect::<Result<Vec<_>>>()?
                    .join(",");
                r.register(
                    id,
                    Shape {
                        rows: 1,
                        width: values.len(),
                    },
                )?;
                writeln!(r.c, "double {id}[]={{{c}}};").unwrap();
                writeln!(r.rust, "let {id}=[vec![{rs}]];").unwrap();
            }
            Operation::Guard { conditions } => {
                for condition in conditions {
                    writeln!(
                        r.c,
                        "if(level>={} && !{})return 1;",
                        condition.minimum_level,
                        r.condition(condition, false)?
                    )
                    .unwrap();
                    writeln!(
                        r.rust,
                        "if level>={} && !{} {{return Some(out);}}",
                        condition.minimum_level,
                        r.condition(condition, true)?
                    )
                    .unwrap();
                }
            }
            Operation::Store { values, indices } => {
                require(
                    values.len() == indices.len(),
                    "output assignment length mismatch",
                )?;
                for (value, index) in values.iter().zip(indices) {
                    require(
                        *index < program.outputs && !assigned[*index],
                        "duplicate or out of range output assignment",
                    )?;
                    assigned[*index] = true;
                    writeln!(r.c, "out[{index}]={};", r.scalar(value, false)?).unwrap();
                    writeln!(r.rust, "out[{index}]={};", r.scalar(value, true)?).unwrap();
                }
            }
        }
    }
    require(
        assigned.iter().all(|a| *a),
        "unassigned computation outputs",
    )?;
    r.c.push_str("return 1;}\n");
    r.rust.push_str("Some(out)\n}\n");
    Ok(Rendered {
        levels: program.levels.clone(),
        outputs: program.outputs,
        estimates: program.estimates,
        c: r.c,
        rust: r.rust,
    })
}
