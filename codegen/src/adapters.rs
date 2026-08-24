use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::Path,
};

use anyhow::{Context, Result, bail};
use jsonschema::Draft;
use serde::Deserialize;
use serde_json::Value;

#[derive(Clone, Debug)]
pub(crate) struct Registry {
    adapters: BTreeMap<String, Adapter>,
    input_types: BTreeMap<String, String>,
}

#[derive(Clone, Debug, Deserialize)]
pub(crate) struct Adapter {
    pub(crate) adapter_id: String,
    pub(crate) input_type: CategoricalInputType,
    pub(crate) outputs: Vec<AdapterOutput>,
    pub(crate) representatives: Vec<Representative>,
    pub(crate) sum_constraint: SumConstraint,
    pub(crate) provenance: Provenance,
}

#[derive(Clone, Debug, Deserialize)]
pub(crate) struct CategoricalInputType {
    pub(crate) name: String,
    pub(crate) description: String,
    pub(crate) categories: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
pub(crate) struct AdapterOutput {
    pub(crate) name: String,
    pub(crate) unit: String,
    pub(crate) domain: [f64; 2],
    pub(crate) description: String,
}

#[derive(Clone, Debug, Deserialize)]
pub(crate) struct Representative {
    pub(crate) category: String,
    pub(crate) values: BTreeMap<String, f64>,
}

#[derive(Clone, Debug, Deserialize)]
pub(crate) struct SumConstraint {
    pub(crate) target: f64,
    pub(crate) tolerance: f64,
}

#[derive(Clone, Debug, Deserialize)]
#[allow(dead_code)]
pub(crate) struct Provenance {
    pub(crate) organization: String,
    pub(crate) title: String,
    pub(crate) artifact: String,
    pub(crate) retrieved: String,
    pub(crate) url: String,
    pub(crate) sha256: String,
    pub(crate) value_rule: String,
}

impl Registry {
    pub(crate) fn load(root: &Path) -> Result<Self> {
        let directory = root.join("specs/adapters");
        let mut yaml_paths = fs::read_dir(&directory)?
            .collect::<std::result::Result<Vec<_>, _>>()?
            .into_iter()
            .map(|entry| entry.path())
            .filter(|path| {
                path.extension()
                    .is_some_and(|extension| extension == "yaml")
            })
            .collect::<Vec<_>>();
        yaml_paths.sort();

        let mut adapters = BTreeMap::new();
        let mut input_types = BTreeMap::new();
        let mut errors = Vec::new();
        for path in yaml_paths {
            let stem = path
                .file_stem()
                .and_then(|stem| stem.to_str())
                .context("adapter filename must be UTF-8")?;
            let schema_path = directory.join(format!("{stem}.schema.json"));
            if !schema_path.is_file() {
                errors.push(format!(
                    "{}: missing paired schema {}",
                    path.display(),
                    schema_path.display()
                ));
                continue;
            }
            match load_adapter(&path, &schema_path) {
                Ok(adapter) => {
                    validate_adapter(&path, &adapter, &mut errors);
                    if let Some(previous) =
                        adapters.insert(adapter.adapter_id.clone(), adapter.clone())
                    {
                        errors.push(format!(
                            "{}: duplicate adapter ID `{}` (also declared by `{}`)",
                            path.display(),
                            adapter.adapter_id,
                            previous.adapter_id
                        ));
                    }
                    if let Some(previous) = input_types
                        .insert(adapter.input_type.name.clone(), adapter.adapter_id.clone())
                    {
                        errors.push(format!("{}: duplicate registered input type `{}` (adapters `{previous}` and `{}`)", path.display(), adapter.input_type.name, adapter.adapter_id));
                    }
                }
                Err(error) => errors.push(format!("{}: {error:#}", path.display())),
            }
        }
        if adapters.is_empty() {
            errors.push(format!(
                "{}: adapter registry contains no YAML specifications",
                directory.display()
            ));
        }
        if errors.is_empty() {
            Ok(Self {
                adapters,
                input_types,
            })
        } else {
            bail!("adapter registry validation failed:\n{}", errors.join("\n"))
        }
    }

    pub(crate) fn adapter(&self, id: &str) -> Option<&Adapter> {
        self.adapters.get(id)
    }
    pub(crate) fn adapter_for_type(&self, input_type: &str) -> Option<&Adapter> {
        self.input_types
            .get(input_type)
            .and_then(|id| self.adapters.get(id))
    }
    pub(crate) fn adapters(&self) -> impl Iterator<Item = &Adapter> {
        self.adapters.values()
    }
}

fn load_adapter(path: &Path, schema_path: &Path) -> Result<Adapter> {
    let schema: Value = serde_json::from_slice(&fs::read(schema_path)?)?;
    let validator = jsonschema::options()
        .with_draft(Draft::Draft202012)
        .build(&schema)?;
    let yaml: serde_yaml::Value = serde_yaml::from_str(&fs::read_to_string(path)?)?;
    let value = serde_json::to_value(yaml)?;
    let schema_errors = validator
        .iter_errors(&value)
        .map(|error| format!("{}: {error}", error.instance_path()))
        .collect::<Vec<_>>();
    if !schema_errors.is_empty() {
        bail!("schema validation failed:\n{}", schema_errors.join("\n"));
    }
    Ok(serde_json::from_value(value)?)
}

fn validate_adapter(path: &Path, adapter: &Adapter, errors: &mut Vec<String>) {
    let identifier = |value: &str| {
        !value.is_empty()
            && value.chars().enumerate().all(|(index, c)| {
                if index == 0 {
                    c.is_ascii_lowercase()
                } else {
                    c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_'
                }
            })
    };
    if !identifier(&adapter.adapter_id) || !identifier(&adapter.input_type.name) {
        errors.push(format!(
            "{}: adapter ID and input type must be lowercase identifiers",
            path.display()
        ));
    }
    if adapter.input_type.description.trim().is_empty()
        || adapter.provenance.organization.trim().is_empty()
        || adapter.provenance.title.trim().is_empty()
        || adapter.provenance.value_rule.trim().is_empty()
    {
        errors.push(format!(
            "{}: input metadata and provenance must be non-empty",
            path.display()
        ));
    }
    let categories = adapter
        .input_type
        .categories
        .iter()
        .collect::<BTreeSet<_>>();
    if categories.len() != adapter.input_type.categories.len()
        || adapter.input_type.categories.iter().any(|category| {
            category.trim() != category
                || category.is_empty()
                || category
                    .chars()
                    .any(|c| !(c.is_ascii_lowercase() || c == ' '))
        })
    {
        errors.push(format!("{}: categories must be unique exact lowercase values with deterministic array ordering", path.display()));
    }
    let outputs = adapter
        .outputs
        .iter()
        .map(|output| output.name.as_str())
        .collect::<BTreeSet<_>>();
    if outputs.len() != adapter.outputs.len() || adapter.outputs.is_empty() {
        errors.push(format!(
            "{}: adapter outputs must be non-empty and unique",
            path.display()
        ));
    }
    for output in &adapter.outputs {
        if !identifier(&output.name)
            || output.unit.trim().is_empty()
            || output.description.trim().is_empty()
            || output.domain.iter().any(|value| !value.is_finite())
            || output.domain[0] > output.domain[1]
        {
            errors.push(format!(
                "{}: output `{}` has invalid metadata or domain",
                path.display(),
                output.name
            ));
        }
    }
    if adapter.representatives.len() != adapter.input_type.categories.len()
        || adapter
            .representatives
            .iter()
            .map(|row| &row.category)
            .collect::<Vec<_>>()
            != adapter.input_type.categories.iter().collect::<Vec<_>>()
    {
        errors.push(format!(
            "{}: representative mappings must appear exactly once in category order",
            path.display()
        ));
    }
    for row in &adapter.representatives {
        if !categories.contains(&row.category)
            || row
                .values
                .keys()
                .map(String::as_str)
                .collect::<BTreeSet<_>>()
                != outputs
        {
            errors.push(format!(
                "{}: category `{}` has an invalid or incomplete output mapping",
                path.display(),
                row.category
            ));
            continue;
        }
        let mut sum = 0.0;
        for output in &adapter.outputs {
            let value = row.values[&output.name];
            if !value.is_finite() || !(output.domain[0]..=output.domain[1]).contains(&value) {
                errors.push(format!(
                    "{}: category `{}` component `{}` is outside its domain",
                    path.display(),
                    row.category,
                    output.name
                ));
            }
            sum += value;
        }
        if (sum - adapter.sum_constraint.target).abs() > adapter.sum_constraint.tolerance {
            errors.push(format!(
                "{}: category `{}` sums to {sum}, outside tolerance {}",
                path.display(),
                row.category,
                adapter.sum_constraint.tolerance
            ));
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn repository_registry_is_valid_and_preserves_usda_values() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap();
        let registry = Registry::load(root).unwrap();
        let adapter = registry.adapter("usda_texture").unwrap();
        assert_eq!(adapter.input_type.categories.len(), 12);
        assert_eq!(adapter.input_type.categories[3], "loam");
        assert_eq!(adapter.representatives[3].values["sand"], 41.0);
        assert_eq!(adapter.representatives[3].values["silt"], 42.0);
        assert_eq!(adapter.representatives[3].values["clay"], 17.0);
    }
}
