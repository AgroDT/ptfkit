use std::{fs, path::Path};

use anyhow::{Result, bail};
use jsonschema::Draft;
use serde_json::Value;

use crate::{
    formula,
    model::{Entry, Implementation, RawExpression, RawFunction, RawInput, RawVariable, Spec},
    semantic,
};

pub(crate) fn load(root: &Path) -> Result<Vec<Entry>> {
    let schema: Value =
        serde_json::from_slice(&fs::read(root.join("specs/schema/ptf-spec.schema.json"))?)?;
    let validator = jsonschema::options()
        .with_draft(Draft::Draft202012)
        .build(&schema)?;
    let mut paths =
        fs::read_dir(root.join("specs/functions"))?.collect::<std::result::Result<Vec<_>, _>>()?;
    paths.sort_by_key(|entry| entry.path());

    let mut entries = Vec::new();
    let mut errors = Vec::new();
    for path in paths.into_iter().map(|entry| entry.path()).filter(|path| {
        path.extension()
            .is_some_and(|extension| extension == "yaml")
    }) {
        let slug = match source_slug(&path) {
            Ok(slug) => slug,
            Err(error) => {
                errors.push(error);
                continue;
            }
        };
        let text = fs::read_to_string(&path)?;
        let yaml_value: serde_yaml::Value = match serde_yaml::from_str(&text) {
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
        for function in &spec.functions {
            if matches!(
                function.status.as_str(),
                "implemented" | "ready-for-implementation"
            ) && function.implementation.is_none()
            {
                errors.push(format!(
                    "{} -> function {} -> implementation: required for status `{}`",
                    path.display(),
                    function.name,
                    function.status
                ));
            }
        }
        let expression_locations = match expression_locations(&text, &spec) {
            Ok(locations) => locations,
            Err(error) => {
                errors.push(format!("{}:\n  $:\n    {error}", path.display()));
                continue;
            }
        };
        let mut expression_locations = expression_locations.into_iter();
        let implementations = spec
            .functions
            .iter()
            .map(|function| match &function.implementation {
                Some(implementation) => {
                    compile(&path, function, implementation, &mut expression_locations).map(Some)
                }
                None => Ok(None),
            })
            .collect::<Result<Vec<_>, _>>();
        match implementations {
            Ok(implementations) => entries.push(Entry {
                path,
                slug,
                spec,
                implementations,
            }),
            Err(error) => errors.push(error),
        }
    }
    if !errors.is_empty() {
        bail!("validation failed:\n{}", errors.join("\n"))
    }
    Ok(entries)
}

fn source_slug(path: &Path) -> Result<String, String> {
    let Some(stem) = path.file_stem().and_then(|stem| stem.to_str()) else {
        return Err(format!(
            "{}:\n  $:\n    specification filename must have a UTF-8 stem",
            path.display()
        ));
    };
    let valid = stem
        .chars()
        .enumerate()
        .all(|(index, character)| match index {
            0 => character.is_ascii_lowercase(),
            _ => character.is_ascii_lowercase() || character.is_ascii_digit() || character == '_',
        });
    if !stem.is_empty() && valid {
        Ok(stem.to_owned())
    } else {
        Err(format!(
            "{}:\n  $:\n    specification filename stem must be an APA-style slug matching ^[a-z][a-z0-9_]*$",
            path.display()
        ))
    }
}

fn compile(
    path: &Path,
    function: &crate::model::Function,
    implementation: &Implementation,
    expression_locations: &mut impl Iterator<Item = crate::model::SourceLocation>,
) -> Result<semantic::Function, String> {
    let raw = RawFunction {
        specification_path: path.to_owned(),
        name: function.name.clone(),
        inputs: function
            .inputs
            .iter()
            .map(|input| RawInput {
                name: input.name.clone(),
            })
            .collect(),
        variables: implementation
            .variables
            .iter()
            .enumerate()
            .map(|(index, variable)| {
                let source_location = expression_locations.next().ok_or_else(|| {
                    format!(
                        "{} -> function {} -> implementation.variables[{index}].expr: source location is unavailable",
                        path.display(),
                        function.name
                    )
                })?;
                expression(
                    path,
                    &function.name,
                    format!("implementation.variables[{index}].expr"),
                    &variable.expr,
                    source_location,
                )
                .map(|expression| RawVariable {
                    name: variable.name.clone(),
                    expression,
                })
            })
            .collect::<Result<Vec<_>, _>>()?,
    };
    validate_output(path, function, &raw)?;
    semantic::compile(&raw).map_err(|error| error.to_string())
}

fn expression(
    path: &Path,
    function: &str,
    implementation_path: String,
    source: &str,
    source_location: crate::model::SourceLocation,
) -> Result<RawExpression, String> {
    let location = format!(
        "{} -> function {function} -> {implementation_path}",
        path.display()
    );
    formula::parse(location, source)
        .map(|expression| RawExpression {
            implementation_path,
            source_location,
            expression,
        })
        .map_err(|error| error.to_string())
}

fn expression_locations(
    text: &str,
    spec: &Spec,
) -> Result<Vec<crate::model::SourceLocation>, String> {
    let expressions = spec
        .functions
        .iter()
        .filter_map(|function| function.implementation.as_ref())
        .flat_map(|implementation| implementation.variables.iter())
        .map(|variable| variable.expr.as_str());
    let mut cursor = 0;
    let mut locations = Vec::new();

    for expression in expressions {
        let Some((offset, next_cursor)) = find_expression(text, cursor, expression) else {
            return Err(format!(
                "could not locate formula expression `{expression}` in YAML source"
            ));
        };
        locations.push(location(text, offset));
        cursor = next_cursor;
    }
    Ok(locations)
}

fn find_expression(text: &str, mut cursor: usize, expression: &str) -> Option<(usize, usize)> {
    while let Some(relative) = text[cursor..].find("expr:") {
        let field = cursor + relative;
        let value_start = field + "expr:".len();
        let value_end = text[value_start..]
            .find("expr:")
            .map_or(text.len(), |next| value_start + next);
        if let Some(relative) = text[value_start..value_end].find(expression) {
            let value = value_start + relative;
            return Some((value, value + expression.len()));
        }
        cursor = field + "expr:".len();
    }
    None
}

fn location(text: &str, offset: usize) -> crate::model::SourceLocation {
    let prefix = &text[..offset];
    crate::model::SourceLocation {
        line: prefix.bytes().filter(|byte| *byte == b'\n').count() + 1,
        column: prefix
            .rsplit_once('\n')
            .map_or(prefix, |(_, line)| line)
            .chars()
            .count()
            + 1,
    }
}

fn validate_output(
    path: &Path,
    function: &crate::model::Function,
    raw: &RawFunction,
) -> Result<(), String> {
    let output_names = function
        .outputs
        .fields()
        .iter()
        .map(|output| &output.name)
        .collect::<Vec<_>>();
    let output_sources = raw
        .inputs
        .iter()
        .map(|input| input.name.as_str())
        .chain(raw.variables.iter().map(|variable| variable.name.as_str()))
        .collect::<std::collections::BTreeSet<_>>();
    let missing = output_names
        .iter()
        .filter(|name| !output_sources.contains(name.as_str()))
        .collect::<Vec<_>>();
    if missing.is_empty() {
        Ok(())
    } else {
        Err(format!(
            "{} -> function {} -> implementation.variables: missing final output variables {:?}",
            path.display(),
            function.name,
            missing
        ))
    }
}

fn json_path(path: &impl std::fmt::Display) -> String {
    let path = path.to_string();
    if path.is_empty() {
        "$".into()
    } else {
        path.trim_start_matches('/').replace('/', ".")
    }
}

#[cfg(test)]
mod tests {
    use std::{
        fs,
        path::{Path, PathBuf},
    };

    use super::{find_expression, load, location};
    use crate::model::PythonGeneration;

    fn fixture_root(label: &str) -> PathBuf {
        let root = std::env::temp_dir().join(format!(
            "ptfkit-codegen-specs-{label}-{}-{}",
            std::process::id(),
            line!()
        ));
        fs::create_dir_all(root.join("specs/functions")).unwrap();
        fs::create_dir_all(root.join("specs/schema")).unwrap();
        fs::copy(
            Path::new(env!("CARGO_MANIFEST_DIR")).join("../specs/schema/ptf-spec.schema.json"),
            root.join("specs/schema/ptf-spec.schema.json"),
        )
        .unwrap();
        root
    }

    fn specification(slug: &str, implementation: &str, generation: &str) -> String {
        format!(
            "source:\n  summary: Test source.\n  citation_apa: Test (2026).\n  doi: null\n{generation}functions:\n  - name: calc_ptf_{slug}\n    status: ready-for-implementation\n    public_api: {{name: calc_ptf_{slug}, result_class: null, summary: Test value.}}\n    scope:\n      prediction_target: Test value.\n      models: {{h_theta: null, k_h: null}}\n    inputs:\n      - {{name: x, symbol: x, unit: '1', domain: null, description: Test input.}}\n    outputs: {{type: scalar, name: value, symbol: y, unit: '1', domain: null, description: Test output.}}\n{implementation}"
        )
    }

    fn write(root: &Path, key: &str, implementation: &str, generation: &str) {
        fs::write(
            root.join(format!("specs/functions/{key}.yaml")),
            specification(key, implementation, generation),
        )
        .unwrap();
    }

    #[test]
    fn rejects_a_code_generating_function_without_implementation() {
        let root = fixture_root("mixed");
        write(
            &root,
            "pilot",
            "    implementation:\n      variables: [{name: value, expr: x * 2}]\n",
            "",
        );
        write(&root, "legacy", "", "");

        let error = load(&root).unwrap_err().to_string();
        assert!(error.contains("implementation\" is a required property"));
        assert!(error.contains("required for status `ready-for-implementation`"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn permits_an_output_to_reuse_a_same_named_input() {
        let root = fixture_root("input-output");
        let specification = specification(
            "input_output",
            "    implementation:\n      variables: [{name: intermediate, expr: value}]\n",
            "",
        )
        .replace(
            "{name: x, symbol: x, unit: '1', domain: null, description: Test input.}",
            "{name: value, symbol: x, unit: '1', domain: null, description: Test input.}",
        );
        fs::write(
            root.join("specs/functions/input_output.yaml"),
            specification,
        )
        .unwrap();

        let entries = load(&root).unwrap();
        assert!(entries[0].implementations[0].is_some());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_an_inline_record_without_a_name() {
        let root = fixture_root("unnamed-record");
        let specification = specification(
            "unnamed_record",
            "    implementation:\n      variables: [{name: first, expr: x}, {name: second, expr: x}]\n",
            "",
        )
        .replace(
            "outputs: {type: scalar, name: value, symbol: y, unit: '1', domain: null, description: Test output.}",
            "outputs:\n      type: record\n      fields:\n      - {name: first, symbol: y_1, unit: '1', domain: null, description: First output.}\n      - {name: second, symbol: y_2, unit: '1', domain: null, description: Second output.}",
        );
        fs::write(
            root.join("specs/functions/unnamed_record.yaml"),
            specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("unnamed inline record must fail")
            .to_string();
        assert!(error.contains("functions.0.outputs"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_a_non_pascal_case_record_name() {
        let root = fixture_root("non-pascal-case-record");
        let specification = specification(
            "non_pascal_case_record",
            "    implementation:\n      variables: [{name: first, expr: x}, {name: second, expr: x}]\n",
            "",
        )
        .replace(
            "outputs: {type: scalar, name: value, symbol: y, unit: '1', domain: null, description: Test output.}",
            "outputs:\n      type: record\n      name: result_record\n      fields:\n      - {name: first, symbol: y_1, unit: '1', domain: null, description: First output.}\n      - {name: second, symbol: y_2, unit: '1', domain: null, description: Second output.}",
        );
        fs::write(
            root.join("specs/functions/non_pascal_case_record.yaml"),
            specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("non-PascalCase record name must fail")
            .to_string();
        assert!(error.contains("functions.0.outputs"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_a_record_definition_without_a_name() {
        let root = fixture_root("unnamed-record-definition");
        let specification = specification(
            "unnamed_record_definition",
            "    implementation:\n      variables: [{name: value, expr: x}]\n",
            "",
        )
        .replace(
            "functions:\n",
            "$defs:\n  reusable_result:\n    type: record\n    fields:\n    - {name: value, symbol: y, unit: '1', domain: null, description: Test output.}\nfunctions:\n",
        )
        .replace(
            "outputs: {type: scalar, name: value, symbol: y, unit: '1', domain: null, description: Test output.}",
            "outputs: {$ref: '#/$defs/reusable_result'}",
        );
        fs::write(
            root.join("specs/functions/unnamed_record_definition.yaml"),
            specification,
        )
        .unwrap();

        let error = load(&root)
            .expect_err("unnamed record definition must fail")
            .to_string();
        assert!(error.contains("$defs.reusable_result"), "{error}");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn reports_schema_formula_and_output_contract_errors() {
        let root = fixture_root("errors");
        write(&root, "schema", "", "unknown: value\n");
        let error = load(&root).expect_err("schema must fail").to_string();
        assert!(error.contains("Additional properties are not allowed"));
        fs::remove_file(root.join("specs/functions/schema.yaml")).unwrap();

        write(
            &root,
            "formula",
            "    implementation:\n      variables: [{name: value, expr: '('}]\n",
            "",
        );
        let error = load(&root).expect_err("formula must fail").to_string();
        assert!(error.contains("implementation.variables[0].expr"));
        fs::remove_file(root.join("specs/functions/formula.yaml")).unwrap();

        write(
            &root,
            "output",
            "    implementation:\n      variables: [{name: other, expr: x}]\n",
            "",
        );
        let error = load(&root)
            .expect_err("output contract must fail")
            .to_string();
        assert!(error.contains("missing final output variables"));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn parses_manual_public_python_policy() {
        let root = fixture_root("manual");
        write(
            &root,
            "manual",
            "    implementation:\n      variables: [{name: value, expr: x}]\n",
            "generation:\n  public_python: manual\n",
        );
        let entries = load(&root).unwrap();
        assert_eq!(
            entries[0].spec.generation.public_python,
            PythonGeneration::Manual
        );
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_a_non_slug_specification_filename() {
        let root = fixture_root("invalid-slug");
        write(
            &root,
            "Bad-Slug",
            "    implementation:\n      variables: [{name: value, expr: x * 2}]\n",
            "",
        );

        let error = match load(&root) {
            Ok(_) => panic!("non-slug filename unexpectedly loaded"),
            Err(error) => error.to_string(),
        };

        assert!(error.contains("filename stem must be an APA-style slug"));
    }

    #[test]
    fn locates_block_and_quoted_formula_values_in_yaml_source() {
        let source = "variables:\n  - expr: >-\n      x ^ 2\n  - {expr: 'sqrt(x)'}\n";
        let (power, cursor) = find_expression(source, 0, "x ^ 2").unwrap();
        let (call, _) = find_expression(source, cursor, "sqrt(x)").unwrap();

        assert_eq!(location(source, power).line, 3);
        assert_eq!(location(source, power).column, 7);
        assert_eq!(location(source, call).line, 4);
        assert_eq!(location(source, call).column, 13);
    }
}
