use std::fmt::{self, Display, Write as _};

pub(crate) mod c;
pub(crate) mod markdown;

const DEFAULT_CAPACITY: usize = 16 * 1024;

/// Renders a structured value into a [`Writer`].
pub(crate) trait Render {
    fn render(&self, writer: &mut Writer);
}

/// A small, indentation-aware buffer for textual generators.
pub(crate) struct Writer {
    contents: String,
    indentation: usize,
    indent: &'static str,
    at_line_start: bool,
}

impl Writer {
    pub(crate) fn new() -> Self {
        Self::with_capacity(DEFAULT_CAPACITY)
    }

    /// Creates a writer with space reserved for at least `capacity` bytes.
    pub(crate) fn with_capacity(capacity: usize) -> Self {
        Self {
            contents: String::with_capacity(capacity),
            indentation: 0,
            indent: "    ",
            at_line_start: true,
        }
    }

    #[allow(dead_code)]
    pub(crate) fn with_indent(mut self, indent: &'static str) -> Self {
        self.indent = indent;
        self
    }

    /// Writes one text fragment, adding indentation only at its start.
    ///
    /// Keep large static templates as single fragments outside an indented
    /// block. Within [`Self::indented`], write each line separately with
    /// [`Self::line`] or [`Self::blank_line`]; this method does not inspect
    /// embedded newlines.
    pub(crate) fn write(&mut self, value: impl Display) {
        self.write_fmt(format_args!("{value}"))
            .expect("writing to a String cannot fail");
    }

    pub(crate) fn line(&mut self, value: impl Display) {
        self.write_fmt(format_args!("{value}\n"))
            .expect("writing to a String cannot fail");
    }

    pub(crate) fn blank_line(&mut self) {
        let res = if self.at_line_start {
            self.write_char('\n')
        } else {
            self.write_str("\n\n")
        };
        res.expect("writing to a String cannot fail");
    }

    /// Renders a nested block with one additional indentation level.
    pub(crate) fn indented(&mut self, render: impl FnOnce(&mut Self)) {
        self.indentation += 1;
        render(self);
        self.indentation -= 1;
    }

    pub(crate) fn into_string(self) -> String {
        self.contents
    }
}

impl fmt::Write for Writer {
    fn write_str(&mut self, text: &str) -> fmt::Result {
        debug_assert!(
            self.indentation == 0 || !text.contains('\n') || text == "\n",
            "write each indented line separately"
        );
        if self.at_line_start && !text.is_empty() && !text.starts_with('\n') {
            for _ in 0..self.indentation {
                self.contents.push_str(self.indent);
            }
        }
        self.contents.push_str(text);
        self.at_line_start = text.ends_with('\n');
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::{Render, Writer};

    struct Paragraph(&'static str);

    impl Render for Paragraph {
        fn render(&self, writer: &mut Writer) {
            writer.line(self.0);
        }
    }

    #[test]
    fn writes_display_values_and_blank_lines() {
        let mut writer = Writer::new();
        writer.write("value: ");
        writer.line(42);
        writer.blank_line();
        writer.line("next");

        assert_eq!(writer.into_string(), "value: 42\n\nnext\n");
    }

    #[test]
    fn composes_render_values() {
        let mut writer = Writer::new();
        Paragraph("first").render(&mut writer);
        Paragraph("second").render(&mut writer);

        assert_eq!(writer.into_string(), "first\nsecond\n");
    }
}
