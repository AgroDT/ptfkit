//! Semantic documentation assembled from validated specifications.
//!
//! Targets choose their own section ordering and markup. This module only
//! describes the information they have available to render.

use crate::model::{Function, Outputs, Parameter, Scope, Source};

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
    pub(crate) parameters: &'a [Parameter],
    pub(crate) returns: Returns<'a>,
    pub(crate) territory: Option<&'a str>,
    pub(crate) models: Models<'a>,
    pub(crate) remarks: Remarks<'a>,
    pub(crate) notes: &'a [String],
    pub(crate) warnings: &'a [String],
}

#[derive(Clone, Copy, Debug)]
pub(crate) enum Returns<'a> {
    Scalar(&'a Parameter),
    Record {
        name: &'a str,
        fields: &'a [Parameter],
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

#[cfg(test)]
mod tests {
    use crate::model::{
        Documentation, Function, FunctionScope, Models, Outputs, Parameter, PublicApi,
    };

    use super::{Returns, for_function};

    fn parameter(name: &str) -> Parameter {
        Parameter {
            name: name.into(),
            unit: "cm^3/cm^3".into(),
            domain: None,
            description: format!("{name} description."),
        }
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
                field: parameter("result"),
            },
            documentation: Documentation::default(),
            implementation: None,
            golden_tests: Vec::new(),
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
            inputs: vec![parameter("sand")],
            outputs: Outputs::Record {
                name: "TestResult".into(),
                fields: vec![parameter("theta_33"), parameter("theta_1500")],
            },
            documentation: Documentation {
                notes: vec!["A note.".into()],
                warnings: vec!["A warning.".into()],
            },
            implementation: None,
            golden_tests: Vec::new(),
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
