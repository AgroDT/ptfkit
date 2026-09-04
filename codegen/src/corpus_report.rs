//! Deterministic corpus-level statistics derived from validated specifications.

use std::collections::{BTreeMap, BTreeSet};

use serde::Serialize;

use crate::model::{Entry, Input, Outputs, VerificationKind};

#[derive(Debug, Serialize)]
pub(crate) struct Report {
    pub(crate) sources: Sources,
    pub(crate) functions: Functions,
    pub(crate) verification: Verification,
    pub(crate) quantity_registry: QuantityRegistryReport,
    pub(crate) inputs: Vec<InputFrequency>,
    pub(crate) outputs: OutputsReport,
    pub(crate) scope: ScopeReport,
    pub(crate) blocked_functions: Vec<BlockedFunction>,
}

#[derive(Debug, Serialize)]
pub(crate) struct Sources {
    pub(crate) specification_files: usize,
    pub(crate) represented_publications: usize,
    pub(crate) earliest_publication_year: Option<u16>,
    pub(crate) latest_publication_year: Option<u16>,
    pub(crate) publication_year_derivation: &'static str,
    pub(crate) unresolved_publication_year_count: usize,
    pub(crate) unresolved_publication_years: Vec<String>,
}

#[derive(Debug, Serialize)]
pub(crate) struct Functions {
    pub(crate) total: usize,
    pub(crate) by_status: Vec<Frequency>,
}

#[derive(Debug, Serialize)]
pub(crate) struct Verification {
    pub(crate) cases_total: usize,
    pub(crate) by_kind: BTreeMap<&'static str, usize>,
    pub(crate) published_cases: usize,
    pub(crate) calculated_cases: usize,
    pub(crate) functions_without_cases: usize,
    pub(crate) all_functions: VerificationCoverage,
    pub(crate) implemented_functions: VerificationCoverage,
    pub(crate) ready_for_implementation_functions: VerificationCoverage,
    pub(crate) edge_case_interpretation: &'static str,
}

#[derive(Debug, Default, Serialize)]
pub(crate) struct VerificationCoverage {
    pub(crate) functions: usize,
    pub(crate) verification_cases: usize,
    pub(crate) functions_with_verification_cases: usize,
    pub(crate) functions_with_verification_cases_percentage: f64,
    pub(crate) edge_cases: usize,
    pub(crate) functions_with_edge_cases: usize,
    pub(crate) functions_with_edge_cases_percentage: f64,
}

#[derive(Debug, Serialize)]
pub(crate) struct InputFrequency {
    pub(crate) name: String,
    pub(crate) kind: InputKind,
    pub(crate) functions: usize,
    pub(crate) percentage: f64,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "lowercase")]
pub(crate) enum InputKind {
    Numeric,
    Categorical,
}

#[derive(Debug, Serialize)]
pub(crate) struct OutputsReport {
    pub(crate) scalar_functions: usize,
    pub(crate) record_functions: usize,
    pub(crate) field_names: Vec<Frequency>,
    pub(crate) structured_property_grouping_available: bool,
}

#[derive(Debug, Serialize)]
pub(crate) struct QuantityRegistryReport {
    pub(crate) registered_quantities: usize,
    pub(crate) quantity_unit_combinations_in_use: usize,
    pub(crate) outputs_using_registry_defaults: usize,
    pub(crate) outputs_using_source_specific_overrides: usize,
    pub(crate) unused_quantity_unit_entries: Vec<QuantityUnitEntry>,
    pub(crate) missing_quantity_or_unit_validation_failures: usize,
}

#[derive(Debug, Ord, PartialOrd, Eq, PartialEq, Serialize)]
pub(crate) struct QuantityUnitEntry {
    pub(crate) quantity: String,
    pub(crate) unit: String,
}

#[derive(Debug, Serialize)]
pub(crate) struct ScopeReport {
    pub(crate) prediction_targets: Vec<Frequency>,
    pub(crate) models: ModelsReport,
    pub(crate) calibration_geography: GeographyReport,
}

#[derive(Debug, Serialize)]
pub(crate) struct ModelsReport {
    pub(crate) h_theta: Vec<Frequency>,
    pub(crate) k_h: Vec<Frequency>,
}

#[derive(Debug, Serialize)]
pub(crate) struct GeographyReport {
    pub(crate) source_specifications_with_territory: usize,
    pub(crate) functions_with_territory: usize,
    pub(crate) territories: Vec<TerritoryFrequency>,
    pub(crate) source_specifications_with_dataset: usize,
}

#[derive(Debug, Serialize)]
pub(crate) struct TerritoryFrequency {
    pub(crate) territory: String,
    pub(crate) source_specifications: usize,
    pub(crate) functions: usize,
}

#[derive(Debug, Serialize)]
pub(crate) struct BlockedFunction {
    pub(crate) source_identifier: String,
    pub(crate) function_name: String,
    pub(crate) documentation_notes: Vec<String>,
    pub(crate) documentation_warnings: Vec<String>,
    pub(crate) scientific_notes: Option<String>,
    pub(crate) blocker_classification: Option<String>,
}

#[derive(Debug, Serialize)]
pub(crate) struct Frequency {
    pub(crate) value: String,
    pub(crate) count: usize,
    pub(crate) percentage: f64,
}

impl Report {
    pub(crate) fn from_entries(entries: &[Entry]) -> Self {
        let total_functions = entries.iter().map(|entry| entry.spec.functions.len()).sum();
        let represented_publications = entries
            .iter()
            .map(|entry| entry.spec.source.citation_apa.as_str())
            .collect::<BTreeSet<_>>()
            .len();
        let mut years = Vec::new();
        let mut unresolved_publication_years = Vec::new();
        for entry in entries {
            match publication_year(&entry.slug) {
                Some(year) => years.push(year),
                None => unresolved_publication_years.push(entry.slug.clone()),
            }
        }

        let mut statuses = BTreeMap::new();
        let mut inputs = BTreeMap::new();
        let mut prediction_targets = BTreeMap::new();
        let mut h_theta = BTreeMap::new();
        let mut k_h = BTreeMap::new();
        let mut output_fields = BTreeMap::new();
        let mut scalar_functions = 0;
        let mut record_functions = 0;
        let mut all_verification = VerificationCoverage::default();
        let mut implemented_verification = VerificationCoverage::default();
        let mut ready_verification = VerificationCoverage::default();
        let mut verification_by_kind = VerificationKind::ALL
            .into_iter()
            .map(|kind| (kind.label(), 0))
            .collect::<BTreeMap<_, _>>();
        let mut published_cases = 0;
        let mut calculated_cases = 0;
        let mut function_territories = BTreeMap::new();
        let mut source_territories = BTreeMap::new();
        let mut functions_with_territory = 0;
        let mut blocked_functions = Vec::new();
        let mut used_quantity_units = BTreeSet::new();
        let mut registry_defaults = 0;
        let mut source_overrides = 0;

        for entry in entries {
            if let Some(territory) = &entry.spec.scope.territory {
                increment(&mut source_territories, territory);
            }
            for function in &entry.spec.functions {
                increment(&mut statuses, &function.status);
                increment(&mut prediction_targets, &function.scope.prediction_target);
                if let Some(model) = &function.scope.models.h_theta {
                    increment(&mut h_theta, model);
                }
                if let Some(model) = &function.scope.models.k_h {
                    increment(&mut k_h, model);
                }
                if let Some(territory) = &function.scope.territory {
                    functions_with_territory += 1;
                    increment(&mut function_territories, territory);
                }

                let unique_inputs = function
                    .inputs
                    .iter()
                    .map(|input| {
                        let kind = match input {
                            Input::Parameter(_) => InputKind::Numeric,
                            Input::Enum { .. } => InputKind::Categorical,
                        };
                        (input.name().to_owned(), kind)
                    })
                    .collect::<BTreeSet<_>>();
                for input in unique_inputs {
                    *inputs.entry(input).or_default() += 1;
                }

                match &function.outputs {
                    Outputs::Scalar { .. } => scalar_functions += 1,
                    Outputs::Record { .. } => record_functions += 1,
                }
                for field in function.outputs.fields() {
                    increment(&mut output_fields, &field.name);
                    used_quantity_units.insert((field.quantity.clone(), field.unit.clone()));
                    if function.verification_tolerances.contains_key(&field.name) {
                        source_overrides += 1;
                    } else {
                        registry_defaults += 1;
                    }
                }

                add_verification(&mut all_verification, function);
                for case in &function.verification_cases {
                    *verification_by_kind
                        .get_mut(case.kind.label())
                        .expect("all verification kinds are initialized") += 1;
                    match case.kind {
                        VerificationKind::Published => published_cases += 1,
                        VerificationKind::Calculated => calculated_cases += 1,
                    }
                }
                if function.status == "implemented" {
                    add_verification(&mut implemented_verification, function);
                }
                if function.status == "ready-for-implementation" {
                    add_verification(&mut ready_verification, function);
                }
                if function.status == "blocked" {
                    blocked_functions.push(BlockedFunction {
                        source_identifier: entry.slug.clone(),
                        function_name: function.name.clone(),
                        documentation_notes: function.documentation.notes.clone(),
                        documentation_warnings: function.documentation.warnings.clone(),
                        scientific_notes: (!entry.spec.scientific_notes.is_empty())
                            .then(|| entry.spec.scientific_notes.clone()),
                        blocker_classification: None,
                    });
                }
            }
        }
        finish_verification(&mut all_verification);
        finish_verification(&mut implemented_verification);
        finish_verification(&mut ready_verification);
        blocked_functions.sort_by(|left, right| {
            (&left.source_identifier, &left.function_name)
                .cmp(&(&right.source_identifier, &right.function_name))
        });
        let registry = entries.first().map(|entry| entry.quantities.as_ref());
        let registered_quantity_units = registry
            .into_iter()
            .flat_map(|registry| &registry.quantities)
            .flat_map(|quantity| {
                quantity
                    .units
                    .keys()
                    .map(move |unit| (quantity.id.clone(), unit.clone()))
            })
            .collect::<BTreeSet<_>>();
        let unused_quantity_unit_entries = registered_quantity_units
            .difference(&used_quantity_units)
            .map(|(quantity, unit)| QuantityUnitEntry {
                quantity: quantity.clone(),
                unit: unit.clone(),
            })
            .collect();

        let territory_names = source_territories
            .keys()
            .chain(function_territories.keys())
            .cloned()
            .collect::<BTreeSet<_>>();
        let territories = territory_names
            .into_iter()
            .map(|territory| TerritoryFrequency {
                source_specifications: source_territories
                    .get(&territory)
                    .copied()
                    .unwrap_or_default(),
                functions: function_territories
                    .get(&territory)
                    .copied()
                    .unwrap_or_default(),
                territory,
            })
            .collect();

        Self {
            sources: Sources {
                specification_files: entries.len(),
                represented_publications,
                earliest_publication_year: years.iter().min().copied(),
                latest_publication_year: years.iter().max().copied(),
                publication_year_derivation: "final four characters of the APA-style source slug, when they are four ASCII digits",
                unresolved_publication_year_count: unresolved_publication_years.len(),
                unresolved_publication_years,
            },
            functions: Functions {
                total: total_functions,
                by_status: status_frequencies(statuses, total_functions),
            },
            verification: Verification {
                cases_total: all_verification.verification_cases,
                by_kind: verification_by_kind,
                published_cases,
                calculated_cases,
                functions_without_cases: all_verification.functions
                    - all_verification.functions_with_verification_cases,
                all_functions: all_verification,
                implemented_functions: implemented_verification,
                ready_for_implementation_functions: ready_verification,
                edge_case_interpretation: "declared specification metadata; not a claim that the cases are executable or externally validated",
            },
            quantity_registry: QuantityRegistryReport {
                registered_quantities: registry.map_or(0, |registry| registry.quantities.len()),
                quantity_unit_combinations_in_use: used_quantity_units.len(),
                outputs_using_registry_defaults: registry_defaults,
                outputs_using_source_specific_overrides: source_overrides,
                unused_quantity_unit_entries,
                missing_quantity_or_unit_validation_failures: 0,
            },
            inputs: sorted_inputs(inputs, total_functions),
            outputs: OutputsReport {
                scalar_functions,
                record_functions,
                field_names: frequencies(output_fields, total_functions),
                structured_property_grouping_available: false,
            },
            scope: ScopeReport {
                prediction_targets: frequencies(prediction_targets, total_functions),
                models: ModelsReport {
                    h_theta: frequencies(h_theta, total_functions),
                    k_h: frequencies(k_h, total_functions),
                },
                calibration_geography: GeographyReport {
                    source_specifications_with_territory: entries
                        .iter()
                        .filter(|entry| entry.spec.scope.territory.is_some())
                        .count(),
                    functions_with_territory,
                    territories,
                    source_specifications_with_dataset: entries
                        .iter()
                        .filter(|entry| entry.spec.scope.dataset.is_some())
                        .count(),
                },
            },
            blocked_functions,
        }
    }

    pub(crate) fn to_text(&self) -> String {
        let mut output = String::from("ptfkit corpus report\n\nSources\n-------\n");
        output.push_str(&format!(
            "Specifications: {}\nRepresented publications: {}\n",
            self.sources.specification_files, self.sources.represented_publications
        ));
        match (
            self.sources.earliest_publication_year,
            self.sources.latest_publication_year,
        ) {
            (Some(first), Some(last)) => {
                output.push_str(&format!("Publication years: {first}-{last}\n"));
            }
            _ => output.push_str("Publication years: unavailable\n"),
        }
        if !self.sources.unresolved_publication_years.is_empty() {
            output.push_str(&format!(
                "Unresolved publication years: {}\n",
                self.sources.unresolved_publication_years.join(", ")
            ));
        }

        output.push_str("\nFunctions\n---------\n");
        output.push_str(&format!("Total: {}\n", self.functions.total));
        for status in &self.functions.by_status {
            output.push_str(&format!(
                "{}: {} ({:.1}%)\n",
                status_label(&status.value),
                status.count,
                status.percentage
            ));
        }

        output.push_str("\nVerification\n------------\n");
        output.push_str(&format!(
            "Total verification cases: {}\nPublished cases: {}\nCalculated cases: {}\nFunctions without verification cases: {}\n",
            self.verification.cases_total,
            self.verification.published_cases,
            self.verification.calculated_cases,
            self.verification.functions_without_cases,
        ));
        output.push_str("Cases by provenance:\n");
        for (kind, count) in &self.verification.by_kind {
            output.push_str(&format!("  {kind}: {count}\n"));
        }
        render_verification(
            &mut output,
            "All functions",
            &self.verification.all_functions,
        );

        output.push_str("\nQuantity registry\n-----------------\n");
        output.push_str(&format!(
            "Registered quantities: {}\nQuantity-unit combinations in use: {}\nOutputs using registry defaults: {}\nOutputs using source-specific overrides: {}\nMissing quantity or unit validation failures: {}\n",
            self.quantity_registry.registered_quantities,
            self.quantity_registry.quantity_unit_combinations_in_use,
            self.quantity_registry.outputs_using_registry_defaults,
            self.quantity_registry.outputs_using_source_specific_overrides,
            self.quantity_registry.missing_quantity_or_unit_validation_failures,
        ));
        output.push_str("Unused quantity-unit entries:\n");
        for entry in &self.quantity_registry.unused_quantity_unit_entries {
            output.push_str(&format!("  {} [{}]\n", entry.quantity, entry.unit));
        }
        render_verification(
            &mut output,
            "Implemented functions",
            &self.verification.implemented_functions,
        );
        render_verification(
            &mut output,
            "Ready-for-implementation functions",
            &self.verification.ready_for_implementation_functions,
        );

        output.push_str("\nInputs\n------\n");
        for input in &self.inputs {
            output.push_str(&format!(
                "{} ({}): {} ({:.1}%)\n",
                input.name,
                match input.kind {
                    InputKind::Numeric => "numeric",
                    InputKind::Categorical => "categorical",
                },
                input.functions,
                input.percentage
            ));
        }

        output.push_str("\nOutputs\n-------\n");
        output.push_str(&format!(
            "Scalar functions: {}\nRecord functions: {}\nOutput fields:\n",
            self.outputs.scalar_functions, self.outputs.record_functions
        ));
        for field in &self.outputs.field_names {
            output.push_str(&format!("  {}: {}\n", field.value, field.count));
        }

        output.push_str("\nScope\n-----\nPrediction targets:\n");
        for target in &self.scope.prediction_targets {
            output.push_str(&format!("  {}: {}\n", target.value, target.count));
        }
        output.push_str("h(theta) models:\n");
        render_values(&mut output, &self.scope.models.h_theta);
        output.push_str("K(h) models:\n");
        render_values(&mut output, &self.scope.models.k_h);
        let geography = &self.scope.calibration_geography;
        output.push_str(&format!(
            "Sources with territory: {}\nFunctions with territory: {}\nSources with dataset descriptions: {}\n",
            geography.source_specifications_with_territory,
            geography.functions_with_territory,
            geography.source_specifications_with_dataset
        ));
        for territory in &geography.territories {
            output.push_str(&format!(
                "  {}: {} sources, {} functions\n",
                territory.territory, territory.source_specifications, territory.functions
            ));
        }

        output.push_str("\nBlocked functions\n-----------------\n");
        if self.blocked_functions.is_empty() {
            output.push_str("None\n");
        } else {
            for function in &self.blocked_functions {
                output.push_str(&format!(
                    "{} / {}\n",
                    function.source_identifier, function.function_name
                ));
                for warning in &function.documentation_warnings {
                    output.push_str(&format!("  Warning: {warning}\n"));
                }
                for note in &function.documentation_notes {
                    output.push_str(&format!("  Note: {note}\n"));
                }
                if let Some(notes) = &function.scientific_notes {
                    output.push_str("  Source scientific notes:\n");
                    for line in notes.lines() {
                        output.push_str(&format!("    {line}\n"));
                    }
                }
            }
            output.push_str("Blocker classification: unavailable from the current schema.\n");
        }
        output
    }
}

fn publication_year(slug: &str) -> Option<u16> {
    let suffix = slug.get(slug.len().checked_sub(4)?..)?;
    suffix
        .chars()
        .all(|character| character.is_ascii_digit())
        .then(|| suffix.parse().ok())
        .flatten()
}

fn add_verification(coverage: &mut VerificationCoverage, function: &crate::model::Function) {
    coverage.functions += 1;
    coverage.verification_cases += function.verification_cases.len();
    coverage.edge_cases += function.edge_cases.len();
    coverage.functions_with_verification_cases +=
        usize::from(!function.verification_cases.is_empty());
    coverage.functions_with_edge_cases += usize::from(!function.edge_cases.is_empty());
}

fn finish_verification(coverage: &mut VerificationCoverage) {
    coverage.functions_with_verification_cases_percentage = percentage(
        coverage.functions_with_verification_cases,
        coverage.functions,
    );
    coverage.functions_with_edge_cases_percentage =
        percentage(coverage.functions_with_edge_cases, coverage.functions);
}

fn increment(map: &mut BTreeMap<String, usize>, value: &str) {
    *map.entry(value.to_owned()).or_default() += 1;
}

fn status_frequencies(counts: BTreeMap<String, usize>, total: usize) -> Vec<Frequency> {
    const ORDER: [&str; 4] = [
        "implemented",
        "ready-for-implementation",
        "blocked",
        "draft",
    ];
    ORDER
        .into_iter()
        .map(|status| Frequency {
            value: status.to_owned(),
            count: counts.get(status).copied().unwrap_or_default(),
            percentage: percentage(counts.get(status).copied().unwrap_or_default(), total),
        })
        .collect()
}

fn frequencies(counts: BTreeMap<String, usize>, total: usize) -> Vec<Frequency> {
    let mut values = counts
        .into_iter()
        .map(|(value, count)| Frequency {
            value,
            count,
            percentage: percentage(count, total),
        })
        .collect::<Vec<_>>();
    values.sort_by(|left, right| {
        right
            .count
            .cmp(&left.count)
            .then_with(|| left.value.cmp(&right.value))
    });
    values
}

fn sorted_inputs(
    counts: BTreeMap<(String, InputKind), usize>,
    total: usize,
) -> Vec<InputFrequency> {
    let mut inputs = counts
        .into_iter()
        .map(|((name, kind), functions)| InputFrequency {
            name,
            kind,
            functions,
            percentage: percentage(functions, total),
        })
        .collect::<Vec<_>>();
    inputs.sort_by(|left, right| {
        right
            .functions
            .cmp(&left.functions)
            .then_with(|| left.name.cmp(&right.name))
            .then_with(|| left.kind.cmp(&right.kind))
    });
    inputs
}

fn percentage(count: usize, total: usize) -> f64 {
    if total == 0 {
        0.0
    } else {
        count as f64 * 100.0 / total as f64
    }
}

fn status_label(status: &str) -> String {
    let mut label = status.replace('-', " ");
    if let Some(first) = label.get_mut(0..1) {
        first.make_ascii_uppercase();
    }
    label
}

fn render_verification(output: &mut String, label: &str, coverage: &VerificationCoverage) {
    output.push_str(&format!(
        "{label}:\n  Verification cases: {}\n  Functions with verification cases: {} ({:.1}%)\n  Edge cases: {}\n  Functions with edge cases: {} ({:.1}%)\n",
        coverage.verification_cases,
        coverage.functions_with_verification_cases,
        coverage.functions_with_verification_cases_percentage,
        coverage.edge_cases,
        coverage.functions_with_edge_cases,
        coverage.functions_with_edge_cases_percentage
    ));
}

fn render_values(output: &mut String, values: &[Frequency]) {
    if values.is_empty() {
        output.push_str("  None declared\n");
    } else {
        for value in values {
            output.push_str(&format!("  {}: {}\n", value.value, value.count));
        }
    }
}

#[cfg(test)]
mod tests {
    use std::{
        path::{Path, PathBuf},
        sync::Arc,
    };

    use super::{InputKind, Report};
    use crate::model::{Entry, Spec};

    fn entry(slug: &str, yaml: &str) -> Entry {
        let spec: Spec = serde_yaml::from_str(yaml).expect("fixture specification deserializes");
        let implementations = vec![None; spec.functions.len()];
        Entry {
            path: PathBuf::from(format!("specs/functions/{slug}.yaml")),
            slug: slug.to_owned(),
            spec,
            implementations,
            quantities: Arc::default(),
        }
    }

    fn fixture() -> Entry {
        entry(
            "tester2020",
            r##"
source:
  summary: Test source.
  citation_apa: Tester (2020).
  doi: null
scope: {territory: Test source territory., dataset: Test dataset.}
$defs:
  x:
    name: x
    symbol: x
    unit: '1'
    domain: null
    description: Numeric input.
  Category:
    type: enum
    description: Test category.
    values: [{name: first, value: first}]
  Result:
    type: record
    name: TestResult
    fields:
      - {name: zeta, symbol: z, unit: '1', domain: null, description: Zeta.}
      - {name: alpha, symbol: a, unit: '1', domain: null, description: Alpha.}
scientific_notes: Blocker evidence from source review.
functions:
  - name: calc_ptf_test_implemented
    status: implemented
    public_api: {name: calc_ptf_test_implemented, summary: Test record.}
    scope:
      territory: Test function territory.
      prediction_target: Target B
      models: {h_theta: Model B, k_h: null}
    inputs:
      - {$ref: '#/$defs/x'}
      - {$ref: '#/$defs/x'}
    outputs: {$ref: '#/$defs/Result'}
    verification_cases:
      - {id: one, kind: published, inputs: {x: 1.0}, expected: {alpha: 1.0, zeta: 2.0}, source_location: 'Table 1, row 1'}
      - {id: two, kind: calculated, inputs: {x: 2.0}, expected: {alpha: 2.0, zeta: 3.0}, rationale: Interior input.}
    edge_cases:
      - {id: edge, inputs: {x: 0.0}, expected_behavior: Finite., notes: Metadata only.}
  - name: calc_ptf_test_blocked
    status: blocked
    public_api: {name: calc_ptf_test_blocked, summary: Test scalar.}
    scope:
      prediction_target: Target A
      models: {h_theta: null, k_h: Model K}
    inputs:
      - {$ref: '#/$defs/Category', name: category}
    outputs: {type: scalar, name: beta, symbol: b, unit: '1', domain: null, description: Beta.}
    verification_cases: []
    edge_cases: []
    documentation:
      notes: [Known source limitation.]
      warnings: [Required coefficients are unavailable.]
  - name: calc_ptf_test_ready
    status: ready-for-implementation
    public_api: {name: calc_ptf_test_ready, summary: Test scalar.}
    scope:
      prediction_target: Target A
      models: {h_theta: null, k_h: null}
    inputs: [{$ref: '#/$defs/x'}]
    outputs: {type: scalar, name: gamma, symbol: g, unit: '1', domain: null, description: Gamma.}
  - name: calc_ptf_test_draft
    status: draft
    public_api: {name: calc_ptf_test_draft, summary: Test scalar.}
    scope:
      prediction_target: Target C
      models: {h_theta: null, k_h: null}
    inputs: [{$ref: '#/$defs/x'}]
    outputs: {type: scalar, name: delta, symbol: d, unit: '1', domain: null, description: Delta.}
"##,
        )
    }

    #[test]
    fn aggregates_multi_function_status_and_verification_coverage() {
        let report = Report::from_entries(&[fixture()]);

        assert_eq!(report.functions.total, 4);
        assert!(
            report
                .functions
                .by_status
                .iter()
                .all(|status| status.count == 1)
        );
        assert_eq!(report.verification.all_functions.verification_cases, 2);
        assert_eq!(report.verification.by_kind["published"], 1);
        assert_eq!(report.verification.by_kind["calculated"], 1);
        assert_eq!(report.verification.published_cases, 1);
        assert_eq!(report.verification.calculated_cases, 1);
        assert_eq!(report.verification.all_functions.edge_cases, 1);
        assert_eq!(
            report
                .verification
                .all_functions
                .functions_with_verification_cases,
            1
        );
        assert_eq!(report.verification.implemented_functions.functions, 1);
        assert_eq!(
            report
                .verification
                .implemented_functions
                .functions_with_edge_cases_percentage,
            100.0
        );
    }

    #[test]
    fn uses_resolved_references_and_deduplicates_inputs_per_function() {
        let report = Report::from_entries(&[fixture()]);
        let x = report
            .inputs
            .iter()
            .find(|input| input.name == "x")
            .expect("resolved x input is reported");
        let category = report
            .inputs
            .iter()
            .find(|input| input.name == "category")
            .expect("resolved category input is reported");

        assert_eq!(x.functions, 3);
        assert!(matches!(x.kind, InputKind::Numeric));
        assert!(matches!(category.kind, InputKind::Categorical));
    }

    #[test]
    fn reports_scalar_record_outputs_and_sorted_values() {
        let report = Report::from_entries(&[fixture()]);
        assert_eq!(report.outputs.scalar_functions, 3);
        assert_eq!(report.outputs.record_functions, 1);
        assert_eq!(report.outputs.field_names[0].value, "alpha");
        assert_eq!(report.scope.prediction_targets[0].value, "Target A");
    }

    #[test]
    fn retains_blocked_functions_and_empty_optional_metadata() {
        let mut fixture = fixture();
        fixture.spec.scope.territory = None;
        fixture.spec.scope.dataset = None;
        let report = Report::from_entries(&[fixture]);

        assert_eq!(report.blocked_functions.len(), 1);
        assert_eq!(
            report.blocked_functions[0].documentation_warnings,
            ["Required coefficients are unavailable."]
        );
        assert!(report.blocked_functions[0].scientific_notes.is_some());
        assert_eq!(
            report
                .scope
                .calibration_geography
                .source_specifications_with_dataset,
            0
        );
    }

    #[test]
    fn serializes_deterministically_to_json() {
        let report = Report::from_entries(&[fixture()]);
        let first = serde_json::to_string_pretty(&report).expect("report serializes");
        let second = serde_json::to_string_pretty(&report).expect("report serializes again");

        assert_eq!(first, second);
        assert!(first.contains("\"blocked_functions\""));
        assert!(first.contains("\"implemented_functions\""));
    }

    #[test]
    fn repository_corpus_report_is_complete_and_stable() {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .expect("workspace root exists");
        let entries = crate::specs::load(root).expect("repository specifications load");
        assert!(crate::validate::specifications(&entries).is_empty());
        crate::compile::functions(entries.clone()).expect("repository specifications compile");

        let report = Report::from_entries(&entries);
        assert_eq!(report.verification.cases_total, 137);
        assert_eq!(report.verification.by_kind["calculated"], 126);
        assert_eq!(report.verification.by_kind["published"], 11);
        assert_eq!(report.sources.specification_files, entries.len());
        assert_eq!(
            report.functions.total,
            entries
                .iter()
                .map(|entry| entry.spec.functions.len())
                .sum::<usize>()
        );
        assert_eq!(
            report
                .functions
                .by_status
                .iter()
                .map(|status| status.count)
                .sum::<usize>(),
            report.functions.total
        );
        assert_eq!(
            serde_json::to_string_pretty(&report).unwrap(),
            serde_json::to_string_pretty(&Report::from_entries(&entries)).unwrap()
        );
    }
}
