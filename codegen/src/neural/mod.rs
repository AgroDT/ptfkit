//! Experimental local neural-model conversion and independent verification.
//! This path does not register a publication as implemented in the corpus.

pub(crate) mod engine;
mod generate;
pub(crate) mod rosetta;
#[cfg(test)]
mod tests;

pub(crate) use generate::run as generate_local;

use anyhow::{Context, Result};
use serde::Deserialize;
use sha2::{Digest, Sha256};
use std::{fs, path::Path};
use thiserror::Error;

#[derive(Debug, Error)]
pub(crate) enum ModelError {
    #[error("unsupported neural artifact format version {0}")]
    Version(u32),
    #[error("neural artifact SHA-256 mismatch")]
    Integrity,
    #[error("invalid neural topology at network {network}")]
    Topology { network: usize },
    #[error("invalid neural transform at network {network}")]
    Transform { network: usize },
    #[error("neural parameter data is non-finite, truncated, or has trailing values")]
    Data,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Manifest {
    format_version: u32,
    upstream_revision: String,
    artifact: String,
    sha256: String,
    networks: Vec<RawNetwork>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RawNetwork {
    name: String,
    nboot: usize,
    widths: Vec<usize>,
    activations: Vec<String>,
    inputs: Vec<RawScale>,
    outputs: Vec<RawScale>,
    offset: usize,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct RawScale {
    kind: String,
    params: Vec<f64>,
}

pub(crate) struct Model {
    pub(crate) networks: Vec<engine::Network>,
    pub(crate) data: Vec<f64>,
    revision: String,
    contract: serde_json::Value,
}

fn scale_valid(scale: &RawScale) -> bool {
    let count = match scale.kind.as_str() {
        "asis" => 0,
        "division" => 1,
        "logtr" | "affine" | "linear" => 2,
        "minmax" => 3,
        _ => return false,
    };
    scale.params.len() == count
        && scale.params.iter().all(|v| v.is_finite())
        && (!matches!(scale.kind.as_str(), "division" | "logtr") || scale.params[0] != 0.0)
}

impl Model {
    pub(crate) fn load(path: &Path) -> Result<Self> {
        let manifest_bytes = fs::read(path)?;
        let raw: Manifest = serde_json::from_slice(&manifest_bytes)?;
        let contract = serde_json::from_slice(&manifest_bytes)?;
        if raw.format_version != 1 {
            return Err(ModelError::Version(raw.format_version).into());
        }
        // The artifact name is a basename, never a path outside the manifest directory.
        if raw.artifact != "models.bin" {
            return Err(ModelError::Integrity.into());
        }
        let bytes = fs::read(
            path.parent()
                .context("model manifest parent")?
                .join(&raw.artifact),
        )?;
        let actual: String = Sha256::digest(&bytes)
            .iter()
            .map(|b| format!("{b:02x}"))
            .collect();
        if actual != raw.sha256 {
            return Err(ModelError::Integrity.into());
        }
        if !bytes.len().is_multiple_of(8) {
            return Err(ModelError::Data.into());
        }
        let data: Vec<f64> = bytes
            .as_chunks::<8>()
            .0
            .iter()
            .map(|b| f64::from_le_bytes(*b))
            .collect();
        if data.iter().any(|v| !v.is_finite()) {
            return Err(ModelError::Data.into());
        }
        let mut end = 0;
        let mut networks = Vec::new();
        for (index, net) in raw.networks.into_iter().enumerate() {
            if !(2..=17).contains(&net.widths.len())
                || net.widths.iter().any(|w| !(1..=64).contains(w))
                || !(2..=1000).contains(&net.nboot)
                || net.activations.len() + 1 != net.widths.len()
                || net.inputs.len() != net.widths[0]
                || net.outputs.len() != *net.widths.last().unwrap()
                || net.offset != end
                || net.name.is_empty()
            {
                return Err(ModelError::Topology { network: index }.into());
            }
            if net
                .activations
                .iter()
                .any(|a| !matches!(a.as_str(), "linear" | "sigmoid" | "tansig" | "relu"))
                || net
                    .inputs
                    .iter()
                    .chain(&net.outputs)
                    .any(|s| !scale_valid(s))
            {
                return Err(ModelError::Transform { network: index }.into());
            }
            let stride: usize = net.widths.windows(2).map(|w| w[0] * w[1] + w[1]).sum();
            end += stride * net.nboot;
            if end > data.len() {
                return Err(ModelError::Data.into());
            }
            let convert = |s: RawScale| engine::Scale {
                kind: s.kind,
                params: s.params,
            };
            networks.push(engine::Network {
                nboot: net.nboot,
                widths: net.widths,
                activations: net.activations,
                inputs: net.inputs.into_iter().map(convert).collect(),
                outputs: net.outputs.into_iter().map(convert).collect(),
                offset: net.offset,
            });
        }
        if end != data.len() || networks.is_empty() {
            return Err(ModelError::Data.into());
        }
        Ok(Self {
            networks,
            data,
            revision: raw.upstream_revision,
            contract,
        })
    }

    fn check_rosetta(&self) -> Result<()> {
        let pinned: serde_json::Value =
            serde_json::from_str(include_str!("../../../specs/models/rosetta3/network.json"))?;
        if self.contract != pinned {
            return Err(ModelError::Integrity.into());
        }
        if self.networks.len() != 5
            || self.revision != "6b0e3902f8a145805d41b691dc36f8e69e898f2a"
            || self.networks[..4]
                .iter()
                .enumerate()
                .any(|(i, n)| n.widths != [i + 3, 6, 5] || n.nboot != 1000)
            || self.networks[4].widths != [4, 6, 2]
            || self.networks[4].nboot != 100
        {
            return Err(ModelError::Topology { network: 0 }.into());
        }
        Ok(())
    }
}

pub(crate) fn verify(model: &Path, reference: &Path) -> Result<()> {
    let model = Model::load(model)?;
    model.check_rosetta()?;
    let refs: serde_json::Value = serde_json::from_slice(&fs::read(reference)?)?;
    anyhow::ensure!(
        refs["provenance"]["revision"] == model.revision,
        "reference revision differs from model"
    );
    let cases = refs["cases"].as_array().context("reference cases")?;
    anyhow::ensure!(cases.len() == 120, "incomplete reference cases");
    let mut max_abs = 0.0_f64;
    let mut max_rel = 0.0_f64;
    for case in cases {
        let level = case["level"].as_u64().context("level")? as usize;
        let mode = match case["mode"].as_str() {
            Some("arith") => 0,
            Some("log") => 1,
            Some("geo") => 2,
            _ => anyhow::bail!("invalid reference mode"),
        };
        let x: Vec<f64> = serde_json::from_value(case["inputs"].clone())?;
        anyhow::ensure!(rosetta::valid(level, &x), "invalid reference predictors");
        let raw = model.networks[level - 2].predict(&model.data, &x);
        for member in case["raw_members"].as_array().context("raw member cases")? {
            let index = member["index"].as_u64().context("member index")? as usize;
            let expected: Vec<f64> = serde_json::from_value(member["values"].clone())?;
            anyhow::ensure!(
                index < raw.len() && expected.len() == 5,
                "invalid raw member fixture"
            );
            for (actual, expected) in raw[index].iter().zip(expected) {
                anyhow::ensure!(
                    actual.is_finite()
                        && (actual - expected).abs() <= 1e-11_f64.max(1e-12 * expected.abs()),
                    "raw member differs from upstream"
                );
            }
        }
        let actual = rosetta::predict(&model.networks, &model.data, level, mode, &x)
            .context("reference inputs rejected")?;
        let means: Vec<f64> = serde_json::from_value(case["mean"].clone())?;
        let stds: Vec<f64> = serde_json::from_value(case["std"].clone())?;
        anyhow::ensure!(
            means.len() == 7 && stds.len() == 7,
            "incomplete reference outputs"
        );
        for (value, expected) in actual.iter().zip(means.iter().chain(&stds)) {
            let difference = (value - expected).abs();
            max_abs = max_abs.max(difference);
            max_rel = max_rel.max(difference / expected.abs().max(1e-300));
            anyhow::ensure!(
                value.is_finite() && difference <= 1e-11_f64.max(1e-12 * expected.abs()),
                "{}: actual {value}, expected {expected}",
                case["id"]
            );
        }
    }
    let inputs: Vec<Vec<f64>> = serde_json::from_value(refs["conductivity"]["inputs"].clone())?;
    let means: Vec<Vec<f64>> = serde_json::from_value(refs["conductivity"]["mean"].clone())?;
    let stds: Vec<Vec<f64>> = serde_json::from_value(refs["conductivity"]["std"].clone())?;
    anyhow::ensure!(
        inputs.len() == 2 && means.len() == 2 && stds.len() == 2,
        "incomplete conductivity fixture"
    );
    for i in 0..2 {
        anyhow::ensure!(
            inputs[i].len() == 4 && means[i].len() == 2 && stds[i].len() == 2,
            "invalid conductivity fixture"
        );
        let (mean, std) = engine::statistics(&model.networks[4].predict(&model.data, &inputs[i]));
        for (actual, expected) in mean.iter().chain(&std).zip(means[i].iter().chain(&stds[i])) {
            anyhow::ensure!(
                actual.is_finite()
                    && (actual - expected).abs() <= 1e-11_f64.max(1e-12 * expected.abs()),
                "conductivity ensemble differs from upstream"
            );
        }
    }
    println!(
        "{} native Rust cases; max absolute difference {max_abs:e}, max relative difference {max_rel:e}",
        cases.len()
    );
    Ok(())
}
