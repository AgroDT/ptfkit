use crate::{
    documentation::{self as docs, FunctionDocument},
    model::{Entry, Parameter},
    output::GeneratedFile,
    render::{Render, Writer, markdown},
};

pub(super) fn render(entries: &[Entry]) -> Vec<GeneratedFile> {
    let mut files = vec![markdown::markdown_file("index.md", |writer| {
        IndexPage { entries }.render(writer);
    })];
    for entry in entries {
        files.push(markdown::markdown_file(
            format!("{}.md", entry.slug),
            |writer| {
                SourcePage { entry }.render(writer);
            },
        ));
    }
    files
}

struct IndexPage<'a> {
    entries: &'a [Entry],
}

impl Render for IndexPage<'_> {
    fn render(&self, writer: &mut Writer) {
        markdown::generated_frontmatter(writer, |writer| writer.line("title: PTF Sources"));
        writer.write(
            "# PTF Sources\n\
\n\
Each page describes the source, scope, inputs, outputs, status, and limitations of the functions defined by one specification.\n\
\n\
| Source | Territory | Functions |\n\
| --- | --- | ---: |\n",
        );
        for entry in self.entries {
            let source = docs::for_source(&entry.spec.source, &entry.spec.scope);
            let territory = source.territory.unwrap_or("\u{2014}");
            writer.line(format_args!(
                "| [{}](./{}.md) | {} | {} |",
                escape_table(source.summary),
                entry.slug,
                escape_table(territory),
                entry.spec.functions.len(),
            ));
        }
    }
}

struct SourcePage<'a> {
    entry: &'a Entry,
}

impl Render for SourcePage<'_> {
    fn render(&self, writer: &mut Writer) {
        let spec = &self.entry.spec;
        let source = docs::for_source(&spec.source, &spec.scope);
        markdown::generated_frontmatter(writer, |writer| {
            writer.line(format_args!("title: PTF source {}", self.entry.slug));
            writer.line(format_args!("nav-title: {}", self.entry.slug));
        });
        writer.write(format_args!(
            "# {}\n\n## Source\n\n{}\n\n",
            source.summary, source.reference.citation
        ));
        if let Some(doi) = source.reference.doi {
            writer.write(format_args!("[DOI: {}]({})\n\n", doi.identifier, doi.url));
        }
        if source.territory.is_some() || source.dataset.is_some() {
            writer.write("## Scope\n\n");
            if let Some(territory) = source.territory {
                writer.write(format_args!("**Territory:** {territory}\n\n"));
            }
            if let Some(dataset) = source.dataset {
                writer.write(format_args!("**Dataset:** {dataset}\n\n"));
            }
        }
        writer.write("## Functions\n\n");
        for function in &spec.functions {
            FunctionSection {
                document: docs::for_function(function),
                name: &function.public_api.name,
                status: &function.status,
            }
            .render(writer);
        }
    }
}

struct FunctionSection<'a> {
    document: FunctionDocument<'a>,
    name: &'a str,
    status: &'a str,
}

impl Render for FunctionSection<'_> {
    fn render(&self, writer: &mut Writer) {
        writer.write(format_args!(
            "### `{}`\n\n{}\n\n**Status:** `{}`\n\n**Prediction target:** {}\n\n",
            self.name, self.document.summary, self.status, self.document.remarks.prediction_target,
        ));

        if self.document.models.h_theta.is_some() || self.document.models.k_h.is_some() {
            writer.write("**Models:** ");
            if let Some(model) = self.document.models.h_theta {
                writer.write(format_args!("$h(\\theta)$ \u{2014} {model}"));
                if self.document.models.k_h.is_some() {
                    writer.write("; ");
                }
            }
            if let Some(model) = self.document.models.k_h {
                writer.write(format_args!("$k(h)$ \u{2014} {model}"));
            }
            writer.blank_line();
        }

        render_input_table(writer, self.document.parameters);
        render_parameter_table(
            writer,
            "Outputs",
            match self.document.returns {
                docs::Returns::Scalar(field) => std::slice::from_ref(field),
                docs::Returns::Record { fields, .. } => fields,
            },
        );
        for note in self.document.notes {
            Admonition {
                kind: "note",
                body: note,
            }
            .render(writer);
        }
        for warning in self.document.warnings {
            Admonition {
                kind: "warning",
                body: warning,
            }
            .render(writer);
        }
    }
}

trait CatalogParameter {
    fn name(&self) -> &str;
    fn unit(&self) -> &str;
    fn domain(&self) -> Option<&str>;
    fn description(&self) -> &str;
}

impl CatalogParameter for Parameter {
    fn name(&self) -> &str {
        &self.name
    }
    fn unit(&self) -> &str {
        &self.unit
    }
    fn domain(&self) -> Option<&str> {
        self.domain.as_deref()
    }
    fn description(&self) -> &str {
        &self.description
    }
}

fn render_input_table(writer: &mut Writer, inputs: &[crate::model::Input]) {
    writer.write(
        "#### Inputs\n\n| Name | Type | Unit | Domain | Description |\n| --- | --- | --- | --- | --- |\n",
    );
    for input in inputs {
        let value_type = input
            .enum_type()
            .map(|definition| format!("`{}`", definition.name))
            .unwrap_or_else(|| "`number`".to_owned());
        writer.line(format_args!(
            "| `{}` | {} | {} | {} | {} |",
            input.name(),
            value_type,
            input
                .unit()
                .map(escape_table)
                .unwrap_or_else(|| "\u{2014}".into()),
            input
                .domain()
                .map(escape_table)
                .unwrap_or_else(|| "\u{2014}".into()),
            escape_table(input.description()),
        ));
    }
    writer.blank_line();
}

fn render_parameter_table(writer: &mut Writer, title: &str, parameters: &[impl CatalogParameter]) {
    writer.write(format_args!(
        "#### {title}\n\n| Name | Unit | Domain | Description |\n| --- | --- | --- | --- |\n"
    ));
    for parameter in parameters {
        writer.line(format_args!(
            "| `{}` | {} | {} | {} |",
            parameter.name(),
            escape_table(parameter.unit()),
            parameter
                .domain()
                .map(escape_table)
                .unwrap_or_else(|| "\u{2014}".into()),
            escape_table(parameter.description()),
        ));
    }
    writer.blank_line();
}

struct Admonition<'a> {
    kind: &'a str,
    body: &'a str,
}

impl Render for Admonition<'_> {
    fn render(&self, writer: &mut Writer) {
        markdown::admonition(writer, self.kind, self.body, str::to_owned);
    }
}

fn escape_table(value: &str) -> String {
    value.replace('\n', " ").replace('|', "\\|")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn renders_admonitions_with_writer_indentation() {
        let mut writer = Writer::new();
        Admonition {
            kind: "note",
            body: "first\nsecond",
        }
        .render(&mut writer);

        assert_eq!(
            writer.into_string(),
            "!!! note\n\n    first\n    second\n\n"
        );
    }

    #[test]
    fn renders_generated_frontmatter_with_the_existing_spacing() {
        let file = markdown::markdown_file("test.md", |writer| {
            markdown::generated_frontmatter(writer, |writer| writer.line("title: Test"));
            writer.line("# Test");
        });

        assert_eq!(
            file.contents,
            "---\n# @generated by ptfkit-codegen; DO NOT EDIT.\n\ntitle: Test\n---\n\n# Test\n"
        );
    }
}
