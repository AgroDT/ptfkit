//! Trusted scientific identities for external EU-PTF v2 QRF objects.
use super::ModelError;
use anyhow::Result;
use serde::Deserialize;
use std::{collections::BTreeSet, fmt::Write as _, path::Path};

#[derive(Deserialize)]
pub(super) struct Collection {
    pub format_version: u32,
    pub format: String,
    pub distribution: String,
    pub models: Vec<Contract>,
}
#[derive(Deserialize)]
pub(super) struct Contract {
    pub id: usize,
    pub name: String,
    pub family: String,
    pub status: String,
    pub features: Vec<String>,
    pub mean_outputs: Vec<String>,
    pub quantile_outputs: Vec<String>,
    pub components: Vec<Component>,
    pub artifact: Artifact,
}
#[derive(Deserialize)]
pub(super) struct Component {
    pub parameter: String,
    pub transform: u32,
}
#[derive(Deserialize)]
pub(super) struct Artifact {
    pub sha256: String,
    pub bytes: usize,
}

pub(super) fn load(root: &Path) -> Result<Collection> {
    let path = root.join("specs/models/euptf2/collection.json");
    let collection: Collection = serde_json::from_slice(&std::fs::read(&path)?)?;
    let mut ids = BTreeSet::new();
    let mut names = BTreeSet::new();
    let valid = collection.format_version == 2
        && collection.format == "PTFKQF02"
        && collection.distribution == "external-only"
        && collection.models.len() == 77
        && collection.models.iter().all(|m| {
            let (parameters, transforms): (Vec<&str>, Vec<u32>) = match m.family.as_str() {
                "VG" => (vec!["THS", "THR", "ALP", "N"], vec![0, 2, 1, 3]),
                "MVG" => (
                    vec!["THS", "THR", "ALP", "N", "K0", "L"],
                    vec![0, 2, 1, 3, 1, 0],
                ),
                "KS" => (vec!["KS"], vec![1]),
                "THS" | "FC" | "FC_2" | "WP" | "AWC" | "AWC_2" => {
                    (vec![m.family.as_str()], vec![0])
                }
                _ => return false,
            };
            let mut means = parameters.clone();
            if parameters.len() > 1 {
                means.push("M");
            }
            ids.insert(m.id)
                && names.insert(&m.name)
                && (1..=77).contains(&m.id)
                && ["implemented", "inventoried", "blocked"].contains(&m.status.as_str())
                && (4..=9).contains(&m.features.len())
                && m.features.iter().collect::<BTreeSet<_>>().len() == m.features.len()
                && m.features.iter().all(|f| {
                    [
                        "USSAND", "USSILT", "USCLAY", "DEPTH_M", "OC", "BD", "CACO3", "PH_H2O",
                        "CEC",
                    ]
                    .contains(&f.as_str())
                })
                && m.components
                    .iter()
                    .map(|c| c.parameter.as_str())
                    .eq(parameters.iter().copied())
                && m.components.iter().map(|c| c.transform).eq(transforms)
                && m.mean_outputs.iter().map(String::as_str).eq(means)
                && m.quantile_outputs.iter().map(String::as_str).eq(parameters)
                && m.artifact.sha256.len() == 64
                && m.artifact
                    .sha256
                    .bytes()
                    .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
                && (20..=64 * 1024 * 1024).contains(&m.artifact.bytes)
        });
    if !valid {
        return Err(ModelError::Artifact { path }.into());
    }
    Ok(collection)
}

pub(super) fn tables(collection: &Collection) -> (String, String, String) {
    let mut rs = String::from("const EUPTF2_MODELS: &[Euptf2Descriptor] = &[\n");
    let mut c = String::new();
    let mut py = String::from("_EUPTF2_CONTRACTS = {\n");
    for m in collection
        .models
        .iter()
        .filter(|m| m.status == "implemented")
    {
        let quoted = |v: &[String]| {
            v.iter()
                .map(|s| format!("{s:?}"))
                .collect::<Vec<_>>()
                .join(",")
        };
        let transforms = m
            .components
            .iter()
            .map(|c| c.transform.to_string())
            .collect::<Vec<_>>()
            .join(",");
        writeln!(rs,"Euptf2Descriptor {{ id:{}, name:{:?}, sha256:{:?}, inputs:&[{}], mean_outputs:&[{}], quantile_outputs:&[{}], transforms:&[{}] }},",
            m.id,m.name,m.artifact.sha256,quoted(&m.features),quoted(&m.mean_outputs),quoted(&m.quantile_outputs),transforms).unwrap();
        writeln!(
            c,
            "{{{},{:?},{:?},{},{},{},{{{}}},{{{}}},{{{}}}}},",
            m.id,
            m.name,
            m.artifact.sha256,
            m.features.len(),
            m.components.len(),
            m.mean_outputs.len(),
            quoted(&m.features),
            quoted(&m.mean_outputs),
            transforms
        )
        .unwrap();
        writeln!(
            py,
            "{:?}: (({},),({},),({},)),",
            m.name,
            quoted(&m.features),
            quoted(&m.mean_outputs),
            quoted(&m.quantile_outputs)
        )
        .unwrap();
    }
    rs.push_str("];\n");
    py.push_str("}\n");
    (rs, c, py)
}
