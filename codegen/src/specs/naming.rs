use std::{fmt, path::Path};

use serde_json::Value;

use super::SpecificationError;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum NameStyle {
    Snake,
    Pascal,
}

impl NameStyle {
    fn accepts(self, name: &str) -> bool {
        match self {
            Self::Snake => {
                name.as_bytes().first().is_some_and(u8::is_ascii_lowercase)
                    && name.split('_').all(|part| {
                        !part.is_empty()
                            && part
                                .bytes()
                                .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit())
                    })
            }
            Self::Pascal => {
                name.as_bytes().first().is_some_and(u8::is_ascii_uppercase)
                    && name.bytes().all(|byte| byte.is_ascii_alphanumeric())
            }
        }
    }
}

impl fmt::Display for NameStyle {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Snake => "snake_case",
            Self::Pascal => "PascalCase",
        })
    }
}

pub(super) fn validate(path: &Path, document: &Value) -> Vec<SpecificationError> {
    let mut errors = Vec::new();
    if let Some(definitions) = document["$defs"].as_object() {
        for (key, definition) in definitions {
            let location = format!("$defs.{key}");
            let style = match definition["type"].as_str() {
                Some("enum" | "record") => NameStyle::Pascal,
                _ => NameStyle::Snake,
            };
            check(path, &location, key, style, &mut errors);
            declaration(path, &location, definition, &mut errors);
        }
    }
    if let Some(functions) = document["functions"].as_array() {
        for (index, function) in functions.iter().enumerate() {
            let location = format!("functions.{index}");
            inputs(path, &location, function, &mut errors);
            declaration(
                path,
                &format!("{location}.outputs"),
                &function["outputs"],
                &mut errors,
            );
        }
    }
    errors
}

fn check(
    path: &Path,
    location: &str,
    name: &str,
    style: NameStyle,
    errors: &mut Vec<SpecificationError>,
) {
    if !style.accepts(name) {
        errors.push(SpecificationError::InvalidName {
            path: path.to_owned(),
            location: location.to_owned(),
            name: name.to_owned(),
            style,
        });
    }
}

fn name(
    path: &Path,
    location: &str,
    value: &Value,
    style: NameStyle,
    errors: &mut Vec<SpecificationError>,
) {
    if let Some(name) = value["name"].as_str() {
        check(path, &format!("{location}.name"), name, style, errors);
    }
}

fn inputs(path: &Path, location: &str, value: &Value, errors: &mut Vec<SpecificationError>) {
    if let Some(inputs) = value["inputs"].as_array() {
        for (index, input) in inputs.iter().enumerate() {
            name(
                path,
                &format!("{location}.inputs.{index}"),
                input,
                NameStyle::Snake,
                errors,
            );
        }
    }
}

fn declaration(path: &Path, location: &str, value: &Value, errors: &mut Vec<SpecificationError>) {
    let style = if value["type"] == "record" {
        NameStyle::Pascal
    } else {
        NameStyle::Snake
    };
    name(path, location, value, style, errors);
    let members = if value["type"] == "enum" {
        "values"
    } else {
        "fields"
    };
    if let Some(values) = value[members].as_array() {
        for (index, value) in values.iter().enumerate() {
            name(
                path,
                &format!("{location}.{members}.{index}"),
                value,
                NameStyle::Snake,
                errors,
            );
        }
    }
    if value["type"] == "tree" {
        inputs(path, location, value, errors);
    }
}

#[cfg(test)]
mod tests {
    use std::{fs, path::Path};

    use serde_json::{Value, json};

    use super::NameStyle;
    use crate::{
        diagnostics::{Diagnostic, ValidationReport},
        specs::{SpecificationError, load_all},
        test_support::fixture_root,
    };

    fn document() -> Value {
        let mut document: Value =
            serde_yaml::from_str(include_str!("../fixtures/source.yaml")).unwrap();
        document["$defs"] = json!({
            "input_value": document["functions"][0]["inputs"][0].clone(),
            "scalar_value": document["functions"][0]["outputs"].clone(),
            "Result": document["functions"][1]["outputs"].clone(),
            "Category": {
                "type": "enum", "description": "Test categories.",
                "values": [{"name": "first_class", "value": "First CLASS"}]
            },
            "values_by_category": {
                "type": "lookup", "input": {"$ref": "#/$defs/Category"},
                "output": {"$ref": "#/$defs/Result"},
                "values": [{"key": "first_class", "value": {"first": 1.0, "second": 2.0}}]
            },
            "value_tree": {
                "type": "tree", "inputs": [{"name": "predictor", "type": "number"}],
                "output": {"$ref": "#/$defs/scalar_value"}, "root": {"leaf": 1.0}
            }
        });
        let mut categorical_function = document["functions"][0].clone();
        categorical_function["name"] = json!("calc_ptf_category");
        categorical_function["public_api"]["name"] = json!("calc_ptf_category");
        categorical_function["status"] = json!("draft");
        categorical_function
            .as_object_mut()
            .unwrap()
            .remove("implementation");
        categorical_function
            .as_object_mut()
            .unwrap()
            .remove("verification_cases");
        categorical_function["inputs"] =
            json!([{"name": "soil_class", "$ref": "#/$defs/Category"}]);
        document["functions"]
            .as_array_mut()
            .unwrap()
            .push(categorical_function);
        document
    }

    fn write(path: &Path, document: &Value) {
        fs::write(path, serde_yaml::to_string(document).unwrap()).unwrap();
    }

    fn assert_naming_error(root: &Path, path: &Path, location: &str, name: &str, style: NameStyle) {
        let error = load_all(root)
            .err()
            .expect("invalid naming must fail loading");
        let report = error.downcast_ref::<ValidationReport>().unwrap();
        let [Diagnostic::Specification(error)] = report.diagnostics.as_slice() else {
            panic!("expected exactly one naming diagnostic: {report:?}");
        };
        let SpecificationError::InvalidName {
            path: actual_path,
            location: actual_location,
            name: actual_name,
            style: actual_style,
        } = error.as_ref()
        else {
            panic!("expected a naming error: {error:?}");
        };
        assert_eq!(
            (
                actual_path.as_path(),
                actual_location.as_str(),
                actual_name.as_str(),
                *actual_style
            ),
            (path, location, name, style)
        );
        assert!(
            error
                .to_string()
                .contains(&format!("`{name}` must use {style}"))
        );
    }

    #[test]
    fn validates_every_definition_kind_even_when_unused_by_functions() {
        let root = fixture_root("definition-naming");
        let path = root.join("specs/functions/example.yaml");
        let valid = document();
        write(&path, &valid);
        load_all(&root).expect("all six definition kinds with conforming names must load");

        for (key, invalid, style) in [
            ("input_value", "InputValue", NameStyle::Snake),
            ("scalar_value", "ScalarValue", NameStyle::Snake),
            ("values_by_category", "ValuesByCategory", NameStyle::Snake),
            ("value_tree", "ValueTree", NameStyle::Snake),
            ("Category", "category", NameStyle::Pascal),
            ("Result", "result_record", NameStyle::Pascal),
        ] {
            let mut document = valid.clone();
            let definitions = document["$defs"].as_object_mut().unwrap();
            let definition = definitions.remove(key).unwrap();
            definitions.insert(invalid.to_owned(), definition);
            write(&path, &document);
            assert_naming_error(&root, &path, &format!("$defs.{invalid}"), invalid, style);
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn validates_names_by_role_in_definitions_and_inline_declarations() {
        let root = fixture_root("declaration-naming");
        let path = root.join("specs/functions/example.yaml");
        let valid = document();
        write(&path, &valid);
        load_all(&root).expect("conforming inline and reusable declarations must load");

        for (pointer, invalid, style) in [
            ("/$defs/input_value/name", "InputValue", NameStyle::Snake),
            ("/$defs/scalar_value/name", "ScalarValue", NameStyle::Snake),
            ("/$defs/Result/name", "result_record", NameStyle::Pascal),
            (
                "/$defs/Result/fields/0/name",
                "FirstField",
                NameStyle::Snake,
            ),
            (
                "/$defs/Category/values/0/name",
                "FirstClass",
                NameStyle::Snake,
            ),
            (
                "/$defs/value_tree/inputs/0/name",
                "Predictor",
                NameStyle::Snake,
            ),
            ("/functions/0/inputs/0/name", "InputValue", NameStyle::Snake),
            ("/functions/0/outputs/name", "ScalarValue", NameStyle::Snake),
            (
                "/functions/1/outputs/name",
                "result_record",
                NameStyle::Pascal,
            ),
            (
                "/functions/1/outputs/fields/0/name",
                "FirstField",
                NameStyle::Snake,
            ),
            ("/functions/2/inputs/0/name", "SoilClass", NameStyle::Snake),
        ] {
            let mut document = valid.clone();
            *document.pointer_mut(pointer).unwrap() = json!(invalid);
            write(&path, &document);
            assert_naming_error(
                &root,
                &path,
                &pointer[1..].replace('/', "."),
                invalid,
                style,
            );
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn validates_unused_shared_enum_keys_and_member_names() {
        let root = fixture_root("shared-naming");
        fs::create_dir_all(root.join("specs/definitions")).unwrap();
        let path = root.join("specs/definitions/soil.yaml");
        let valid = json!({"description": "Shared categories.", "$defs": {
            "SoilClass": {"type": "enum", "description": "Soil categories.",
                "values": [{"name": "first_class", "value": "First CLASS"}]}
        }});
        write(&path, &valid);
        load_all(&root).expect("unreferenced shared enum with canonical names must load");
        let invalid_key = json!({"description": "Shared categories.", "$defs": {
            "soil_class": valid["$defs"]["SoilClass"].clone()
        }});
        write(&path, &invalid_key);
        assert_naming_error(
            &root,
            &path,
            "$defs.soil_class",
            "soil_class",
            NameStyle::Pascal,
        );
        for invalid in ["FirstClass", "first__class"] {
            let mut invalid_member = valid.clone();
            invalid_member["$defs"]["SoilClass"]["values"][0]["name"] = json!(invalid);
            write(&path, &invalid_member);
            assert_naming_error(
                &root,
                &path,
                "$defs.SoilClass.values.0.name",
                invalid,
                NameStyle::Snake,
            );
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_malformed_snake_case_keys_without_restricting_acronyms_in_type_names() {
        let root = fixture_root("name-boundaries");
        let path = root.join("specs/functions/example.yaml");
        let mut valid = document();
        valid["$defs"]["Result"]["name"] = json!("PTF2026Result");
        write(&path, &valid);
        load_all(&root).expect("acronyms and digits in PascalCase names must remain valid");
        for invalid in [
            "",
            "_value",
            "value_",
            "value__input",
            "2value",
            "soil-value",
            "válue",
        ] {
            let mut document = valid.clone();
            let definitions = document["$defs"].as_object_mut().unwrap();
            let parameter = definitions.remove("input_value").unwrap();
            definitions.insert(invalid.to_owned(), parameter);
            write(&path, &document);
            assert_naming_error(
                &root,
                &path,
                &format!("$defs.{invalid}"),
                invalid,
                NameStyle::Snake,
            );
        }
        fs::remove_dir_all(root).unwrap();
    }
}
