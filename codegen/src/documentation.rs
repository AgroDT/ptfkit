//! Semantic documentation assembled from validated specifications.
//!
//! Targets choose their own section ordering and markup. This module only
//! describes the information they have available to render.

use crate::model::{Function, Input, OutputField, Outputs, Parameter, Scope, Source};

#[derive(Clone, Copy, Debug)]
pub(crate) struct SourceDocument<'a> {
    pub(crate) summary: &'a str,
    pub(crate) reference: Reference<'a>,
    pub(crate) territory: Option<&'a str>,
    pub(crate) dataset: Option<&'a str>,
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct Reference<'a> {
    pub(crate) citation: &'a str,
    pub(crate) doi: Option<Doi<'a>>,
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct Doi<'a> {
    pub(crate) identifier: &'a str,
    pub(crate) url: &'a str,
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct FunctionDocument<'a> {
    pub(crate) summary: &'a str,
    pub(crate) parameters: &'a [Input],
    pub(crate) returns: Returns<'a>,
    pub(crate) territory: Option<&'a str>,
    pub(crate) models: Models<'a>,
    pub(crate) remarks: Remarks<'a>,
    pub(crate) notes: &'a [String],
    pub(crate) warnings: &'a [String],
}

#[derive(Clone, Copy, Debug)]
pub(crate) enum Returns<'a> {
    Scalar(&'a OutputField),
    Record {
        name: &'a str,
        fields: &'a [OutputField],
    },
}

#[derive(Clone, Copy, Debug, Default)]
pub(crate) struct Models<'a> {
    pub(crate) h_theta: Option<&'a str>,
    pub(crate) k_h: Option<&'a str>,
}

#[derive(Clone, Copy, Debug)]
pub(crate) struct Remarks<'a> {
    pub(crate) prediction_target: &'a str,
}

pub(crate) fn for_source<'a>(source: &'a Source, scope: &'a Scope) -> SourceDocument<'a> {
    SourceDocument {
        summary: &source.summary,
        reference: Reference {
            citation: &source.citation_apa,
            doi: source.doi.as_ref().map(|doi| Doi {
                identifier: &doi.identifier,
                url: &doi.url,
            }),
        },
        territory: scope.territory.as_deref(),
        dataset: scope.dataset.as_deref(),
    }
}

pub(crate) fn for_function(function: &Function) -> FunctionDocument<'_> {
    FunctionDocument {
        summary: &function.public_api.summary,
        parameters: &function.inputs,
        returns: match &function.outputs {
            Outputs::Scalar { field } => Returns::Scalar(field),
            Outputs::Record { name, fields } => Returns::Record { name, fields },
        },
        territory: function.scope.territory.as_deref(),
        models: Models {
            h_theta: function.scope.models.h_theta.as_deref(),
            k_h: function.scope.models.k_h.as_deref(),
        },
        remarks: Remarks {
            prediction_target: &function.scope.prediction_target,
        },
        notes: &function.documentation.notes,
        warnings: &function.documentation.warnings,
    }
}

pub(crate) trait ParameterMetadata {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn unit(&self) -> Option<&str>;
}

impl ParameterMetadata for Parameter {
    fn name(&self) -> &str {
        &self.name
    }
    fn description(&self) -> &str {
        &self.description
    }
    fn unit(&self) -> Option<&str> {
        Some(&self.unit)
    }
}

impl ParameterMetadata for OutputField {
    fn name(&self) -> &str {
        &self.name
    }
    fn description(&self) -> &str {
        &self.description
    }
    fn unit(&self) -> Option<&str> {
        Some(&self.unit)
    }
}

impl ParameterMetadata for Input {
    fn name(&self) -> &str {
        self.name()
    }
    fn description(&self) -> &str {
        self.description()
    }
    fn unit(&self) -> Option<&str> {
        self.unit()
    }
}

pub(crate) fn parameter_details(parameter: &impl ParameterMetadata) -> String {
    match parameter.unit() {
        Some(unit) => format!("{} ({unit})", parameter.description()),
        None => parameter.description().to_owned(),
    }
}

pub(crate) fn parameter_documentation(parameter: &impl ParameterMetadata) -> String {
    format!("{}: {}", parameter.name(), parameter_details(parameter))
}

#[cfg(test)]
mod tests {
    use crate::model::{
        Documentation, Function, FunctionScope, Input, Models, OutputField, Outputs, Parameter,
        PublicApi,
    };

    use super::{ParameterMetadata, Returns, for_function, parameter_details};

    struct EnumInputMetadata;

    impl ParameterMetadata for EnumInputMetadata {
        fn name(&self) -> &str {
            "soil_texture"
        }

        fn description(&self) -> &str {
            "USDA soil textural class."
        }

        fn unit(&self) -> Option<&str> {
            None
        }
    }

    fn output(name: &str) -> OutputField {
        OutputField {
            name: name.into(),
            quantity: "volumetric_water_content".into(),
            symbol: None,
            unit: "cm^3/cm^3".into(),
            domain: None,
            description: format!("{name} description."),
        }
    }

    fn input(name: &str) -> Input {
        Input::Parameter(Parameter {
            name: name.into(),
            unit: "cm^3/cm^3".into(),
            domain: None,
            description: format!("{name} description."),
        })
    }

    #[test]
    fn omits_a_unit_suffix_for_enum_input_metadata() {
        assert_eq!(
            parameter_details(&EnumInputMetadata),
            "USDA soil textural class."
        );
    }

    #[test]
    fn preserves_empty_optional_documentation_sections() {
        let function = Function {
            name: "calc_ptf_test".into(),
            status: "draft".into(),
            public_api: PublicApi {
                name: "calc_ptf_test".into(),
                result_class: None,
                summary: "Estimate a test property.".into(),
            },
            scope: FunctionScope {
                territory: None,
                prediction_target: "Test property.".into(),
                models: Models::default(),
            },
            inputs: Vec::new(),
            outputs: Outputs::Scalar {
                field: output("result"),
            },
            verification_tolerances: Default::default(),
            documentation: Documentation::default(),
            implementation: None,
            verification_cases: Vec::new(),
            edge_cases: Vec::new(),
        };

        let document = for_function(&function);
        assert!(document.territory.is_none());
        assert!(document.models.h_theta.is_none());
        assert!(document.models.k_h.is_none());
        assert!(document.notes.is_empty());
        assert!(document.warnings.is_empty());
        assert!(matches!(document.returns, Returns::Scalar(_)));
    }

    #[test]
    fn retains_each_record_output_field() {
        let function = Function {
            name: "calc_ptf_test".into(),
            status: "draft".into(),
            public_api: PublicApi {
                name: "calc_ptf_test".into(),
                result_class: Some("TestResult".into()),
                summary: "Estimate test properties.".into(),
            },
            scope: FunctionScope {
                territory: Some("Test territory.".into()),
                prediction_target: "Test properties.".into(),
                models: Models {
                    h_theta: Some("Retention model.".into()),
                    k_h: Some("Conductivity model.".into()),
                },
            },
            inputs: vec![input("sand")],
            outputs: Outputs::Record {
                name: "TestResult".into(),
                fields: vec![output("theta_33"), output("theta_1500")],
            },
            verification_tolerances: Default::default(),
            documentation: Documentation {
                notes: vec!["A note.".into()],
                warnings: vec!["A warning.".into()],
            },
            implementation: None,
            verification_cases: Vec::new(),
            edge_cases: Vec::new(),
        };

        let document = for_function(&function);
        let Returns::Record { name, fields } = document.returns else {
            panic!("record outputs must retain their shape");
        };
        assert_eq!(name, "TestResult");
        assert_eq!(
            fields
                .iter()
                .map(|field| field.name.as_str())
                .collect::<Vec<_>>(),
            ["theta_33", "theta_1500"]
        );
        assert_eq!(document.models.h_theta, Some("Retention model."));
        assert_eq!(document.models.k_h, Some("Conductivity model."));
        assert_eq!(document.remarks.prediction_target, "Test properties.");
    }
}
