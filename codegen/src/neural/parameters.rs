//! Authenticate the canonical container and prepare uncommitted typed arrays.
use super::{
    Model, ModelError,
    engine::{Network, Scale},
};
use crate::model::{DenseEnsembleDefinition, Entry, NeuralChannel};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fmt::Write as _, path::Path};

const HEADER: &str = "// @prepared by ptfkit-codegen; DO NOT COMMIT.\n";

fn declarations(entry: &Entry) -> anyhow::Result<BTreeMap<usize, DenseEnsembleDefinition>> {
    let mut networks = BTreeMap::new();
    for implementation in entry
        .spec
        .functions
        .iter()
        .filter_map(|f| f.implementation.as_ref())
    {
        for definition in implementation.networks.values() {
            crate::semantic::neural::validate_definition(definition)?;
            if let Some(previous) =
                networks.insert(definition.parameters.network, definition.clone())
                && previous != *definition
            {
                return Err(ModelError::ParameterDefinition {
                    network: definition.parameters.network,
                }
                .into());
            }
        }
    }
    if networks.is_empty() || networks.keys().copied().ne(0..networks.len()) {
        return Err(ModelError::Data.into());
    }
    Ok(networks)
}

pub(super) fn decode(entry: &Entry, bytes: &[u8]) -> anyhow::Result<Model> {
    let declarations = declarations(entry)?;
    let scale = |c: &NeuralChannel| Scale {
        kind: c.scale.clone(),
        params: c.params.clone(),
    };
    let networks = declarations
        .values()
        .map(|n| Network {
            nboot: n.members,
            widths: n.widths.clone(),
            activations: n.activations.clone(),
            offset: n.parameters.offset,
            inputs: n.inputs.iter().map(scale).collect(),
            outputs: n.outputs.iter().map(scale).collect(),
        })
        .collect::<Vec<_>>();
    let mut values = 0;
    for (index, n) in networks.iter().enumerate() {
        if n.offset != values {
            return Err(ModelError::ParameterDefinition { network: index }.into());
        }
        values += n.nboot
            * n.widths
                .windows(2)
                .map(|w| w[0] * w[1] + w[1])
                .sum::<usize>();
    }
    let mut model = Model {
        networks,
        data: Vec::new(),
        revision: String::new(),
        contract: serde_json::Value::Null,
    };
    let mut metadata = super::pack::encode(&model);
    metadata.truncate(metadata.len() - 8);
    metadata.extend_from_slice(&(values as u64).to_le_bytes());
    if !bytes.starts_with(&metadata) || bytes.len() != metadata.len() + values * 8 {
        return Err(ModelError::Data.into());
    }
    model.data = bytes[metadata.len()..]
        .as_chunks::<8>()
        .0
        .iter()
        .map(|b| f64::from_le_bytes(*b))
        .collect();
    if model.data.iter().any(|v| !v.is_finite()) {
        return Err(ModelError::Data.into());
    }
    Ok(model)
}

fn c_float(value: f64) -> String {
    let bits = value.to_bits();
    let sign = if bits >> 63 != 0 { "-" } else { "" };
    let exponent = ((bits >> 52) & 0x7ff) as i32;
    let fraction = bits & 0x000f_ffff_ffff_ffff;
    if exponent == 0 {
        format!("{sign}0x0.{fraction:013x}p-1022")
    } else {
        format!("{sign}0x1.{fraction:013x}p{}", exponent - 1023)
    }
}

fn c_scales(scales: &[Scale]) -> String {
    let mut text = String::from("{");
    for scale in scales {
        let kind = match scale.kind.as_str() {
            "asis" => 0,
            "division" => 1,
            "logtr" => 2,
            "affine" => 3,
            "minmax" => 4,
            "linear" => 5,
            _ => unreachable!(),
        };
        let params = (0..3)
            .map(|i| c_float(scale.params.get(i).copied().unwrap_or(0.0)))
            .collect::<Vec<_>>()
            .join(",");
        write!(text, "{{{kind},{{{params}}}}},").unwrap();
    }
    text.push('}');
    text
}

pub(super) fn render(model: &Model, sha: &str) -> (String, String) {
    let mut c = format!(
        "{HEADER}/* Exact binary64 hexadecimal literals; CC0 model parameters. */\n#include <ptfkit/zhang_schaap2017.h>\nstatic const double weights[]={{\n"
    );
    let mut rust = format!(
        "{HEADER}use crate::models::{{Model,engine::{{Network,Scale}}}};\nstatic WEIGHTS:[f64;{}]=[\n",
        model.data.len()
    );
    for values in model.data.chunks(8) {
        for value in values {
            write!(c, "{},", c_float(*value)).unwrap();
            write!(rust, "{value:?},").unwrap();
        }
        c.push('\n');
        rust.push('\n');
    }
    c.push_str("};\nstatic const ptfkit_detail_network networks[]={\n");
    rust.push_str("];\npub(super) fn builtin()->Model {let networks=vec![\n");
    for n in &model.networks {
        let widths = n
            .widths
            .iter()
            .map(usize::to_string)
            .collect::<Vec<_>>()
            .join(",");
        let activations = n
            .activations
            .iter()
            .map(|a| match a.as_str() {
                "linear" => "0",
                "sigmoid" => "1",
                "tansig" => "2",
                _ => "3",
            })
            .collect::<Vec<_>>()
            .join(",");
        writeln!(
            c,
            "{{{},{},{{{widths}}},{},{{{activations}}},{},{}}},",
            n.nboot,
            n.activations.len(),
            n.offset,
            c_scales(&n.inputs),
            c_scales(&n.outputs)
        )
        .unwrap();
        let rs_scales = |scales: &[Scale]| {
            scales
                .iter()
                .map(|s| {
                    format!(
                        "Scale{{kind:{:?}.into(),params:vec![{}]}}",
                        s.kind,
                        s.params
                            .iter()
                            .map(|v| format!("f64::from_bits(0x{:016x})", v.to_bits()))
                            .collect::<Vec<_>>()
                            .join(",")
                    )
                })
                .collect::<Vec<_>>()
                .join(",")
        };
        writeln!(rust,"Network{{nboot:{},widths:vec![{widths}],activations:vec![{}],inputs:vec![{}],outputs:vec![{}],offset:{}}},",n.nboot,n.activations.iter().map(|a|format!("{a:?}.into()")).collect::<Vec<_>>().join(","),rs_scales(&n.inputs),rs_scales(&n.outputs),n.offset).unwrap();
    }
    let digest = (0..32)
        .map(|i| format!("0x{}", &sha[i * 2..i * 2 + 2]))
        .collect::<Vec<_>>()
        .join(",");
    c.push_str("};\n");
    writeln!(c,"ptfkit_model_status ptfkit_detail_rosetta3_builtin(ptfkit_model **out){{static const unsigned char digest[32]={{{digest}}};return ptfkit_detail_model_from_arrays(networks,{},weights,{},digest,out);}}",model.networks.len(),model.data.len()).unwrap();
    writeln!(
        rust,
        "];Model::from_bundled(networks,&WEIGHTS,[{digest}])}}"
    )
    .unwrap();
    (c, rust)
}

pub(crate) fn prepare(root: &Path, entries: &[Entry]) -> anyhow::Result<()> {
    for entry in entries.iter().filter(|e| e.slug == "zhang_schaap2017") {
        let declarations = declarations(entry)?;
        let artifacts = declarations
            .values()
            .map(|d| d.parameters.artifact.as_str())
            .collect::<std::collections::BTreeSet<_>>();
        if artifacts.len() != 1 {
            return Err(ModelError::Data.into());
        }
        let path = entry
            .path
            .parent()
            .unwrap()
            .join(artifacts.first().unwrap());
        let metadata: serde_json::Value = serde_json::from_slice(&std::fs::read(&path)?)?;
        let sha = metadata["sha256"].as_str().ok_or(ModelError::Integrity)?;
        let bytes = std::fs::read(path.with_file_name("rosetta3.ptfm"))?;
        let actual = Sha256::digest(&bytes)
            .iter()
            .map(|v| format!("{v:02x}"))
            .collect::<String>();
        if sha != actual || metadata["bytes"].as_u64() != Some(bytes.len() as u64) {
            return Err(ModelError::Integrity.into());
        }
        let model = decode(entry, &bytes)?;
        let (c, rust) = render(&model, sha);
        let c_path = root.join("targets/ptfkit-native/prepared/rosetta3_data.c");
        let rs_path = root.join("targets/ptfkit-rs/src/prepared/rosetta3.rs");
        std::fs::create_dir_all(c_path.parent().unwrap())?;
        std::fs::create_dir_all(rs_path.parent().unwrap())?;
        std::fs::write(c_path, c)?;
        std::fs::write(rs_path, rust)?;
    }
    Ok(())
}
