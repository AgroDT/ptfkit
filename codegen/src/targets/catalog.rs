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

        InputTable {
            title: "Inputs",
            parameters: self.document.parameters,
        }
        .render(writer);
        ParameterTable {
            title: "Outputs",
            parameters: match self.document.returns {
                docs::Returns::Scalar(field) => std::slice::from_ref(field),
                docs::Returns::Record { fields, .. } => fields,
            },
        }
        .render(writer);
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

struct InputTable<'a> {
    title: &'a str,
    parameters: &'a [crate::model::InputParameter],
}

impl Render for InputTable<'_> {
    fn render(&self, writer: &mut Writer) {
        writer.write(format_args!(
            "#### {}\n\n| Name | Type | Unit | Domain | Description |\n| --- | --- | --- | --- | --- |\n",
            self.title
        ));
        for parameter in self.parameters {
            writer.line(format_args!(
                "| `{}` | `{}` | {} | {} | {} |",
                parameter.name,
                parameter.r#type.as_str(),
                escape_table(&parameter.unit),
                parameter
                    .domain
                    .as_deref()
                    .map(escape_table)
                    .unwrap_or_else(|| "\u{2014}".into()),
                escape_table(&parameter.description),
            ));
        }
        writer.blank_line();
    }
}

struct ParameterTable<'a> {
    title: &'a str,
    parameters: &'a [Parameter],
}

impl Render for ParameterTable<'_> {
    fn render(&self, writer: &mut Writer) {
        writer.write(format_args!(
            "#### {}\n\n| Name | Unit | Domain | Description |\n| --- | --- | --- | --- |\n",
            self.title
        ));
        for parameter in self.parameters {
            writer.line(format_args!(
                "| `{}` | {} | {} | {} |",
                parameter.name,
                escape_table(&parameter.unit),
                parameter
                    .domain
                    .as_deref()
                    .map(escape_table)
                    .unwrap_or_else(|| "\u{2014}".into()),
                escape_table(&parameter.description),
            ));
        }
        writer.blank_line();
    }
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
