use std::{fs, path::Path};

use anyhow::{Context, Result, bail};
use jsonschema::Draft;
use serde_json::Value;

use crate::model::{Entry, Spec};

pub(crate) fn load(root: &Path) -> Result<Vec<Entry>> {
    let schema: Value = serde_json::from_slice(&fs::read(
        root.join("specs/schema/ptf-spec-v1.schema.json"),
    )?)?;
    let validator = jsonschema::options()
        .with_draft(Draft::Draft202012)
        .build(&schema)?;
    let mut paths =
        fs::read_dir(root.join("specs/functions"))?.collect::<std::result::Result<Vec<_>, _>>()?;
    paths.sort_by_key(|entry| entry.path());

    let mut entries = Vec::new();
    let mut errors = Vec::new();
    for path in paths
        .into_iter()
        .map(|entry| entry.path())
        .filter(|path| path.extension().is_some_and(|extension| extension == "md"))
    {
        let text = fs::read_to_string(&path)?;
        let yaml = frontmatter(&text)
            .with_context(|| format!("{}: missing YAML front matter", path.display()))?;
        let yaml_value: serde_yaml::Value = match serde_yaml::from_str(yaml) {
            Ok(value) => value,
            Err(error) => {
                errors.push(format!(
                    "{}:\n  $:\n    malformed YAML: {error}",
                    path.display()
                ));
                continue;
            }
        };
        let value = match serde_json::to_value(yaml_value) {
            Ok(value) => value,
            Err(error) => {
                errors.push(format!(
                    "{}:\n  $:\n    YAML cannot be represented as JSON: {error}",
                    path.display()
                ));
                continue;
            }
        };
        for error in validator.iter_errors(&value) {
            errors.push(format!(
                "{}:\n  {}:\n    {}",
                path.display(),
                json_path(error.instance_path()),
                error
            ));
        }
        let spec: Spec = match serde_json::from_value(value) {
            Ok(spec) => spec,
            Err(error) => {
                errors.push(format!(
                    "{}:\n  $:\n    metadata cannot be read: {error}",
                    path.display()
                ));
                continue;
            }
        };
        entries.push(Entry {
            path,
            spec,
            section_functions: markdown_functions(&text),
        });
    }
    if !errors.is_empty() {
        bail!("validation failed:\n{}", errors.join("\n"))
    }
    Ok(entries)
}

fn frontmatter(text: &str) -> Option<&str> {
    text.strip_prefix("---\n")?
        .split_once("\n---")
        .map(|(front, _)| front)
}

fn json_path(path: &impl std::fmt::Display) -> String {
    let path = path.to_string();
    if path.is_empty() {
        "$".into()
    } else {
        path.trim_start_matches('/').replace('/', ".")
    }
}

fn markdown_functions(text: &str) -> Vec<String> {
    text.lines()
        .filter_map(|line| {
            line.strip_prefix("## `")
                .and_then(|name| name.strip_suffix('`'))
        })
        .filter(|name| name.starts_with("calc_ptf_"))
        .map(str::to_owned)
        .collect()
}
