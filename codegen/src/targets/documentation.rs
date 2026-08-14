use crate::model::Parameter;

pub(super) fn parameter_details(parameter: &Parameter) -> String {
    format!("{} ({})", parameter.description, parameter.unit)
}

pub(super) fn parameter_documentation(parameter: &Parameter) -> String {
    format!("{}: {}", parameter.name, parameter_details(parameter))
}
