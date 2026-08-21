use std::fmt::{self, Display, Write as _};

/// Renders a structured value into a [`Writer`].
pub(crate) trait Render {
    fn render(&self, writer: &mut Writer);
}

/// A small, indentation-aware buffer for textual generators.
pub(crate) struct Writer {
    contents: String,
    indentation: usize,
    at_line_start: bool,
}

impl Writer {
    pub(crate) fn new() -> Self {
        Self {
            contents: String::new(),
            indentation: 0,
            at_line_start: true,
        }
    }

    pub(crate) fn write(&mut self, value: impl Display) {
        self.write_fmt(format_args!("{value}"))
            .expect("writing to a String cannot fail");
    }

    pub(crate) fn line(&mut self, value: impl Display) {
        self.write(value);
        self.write("\n");
    }

    pub(crate) fn blank_line(&mut self) {
        if !self.at_line_start {
            self.write("\n");
        }
        self.write("\n");
    }

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
        for part in text.split_inclusive('\n') {
            if self.at_line_start && part != "\n" {
                for _ in 0..self.indentation {
                    self.contents.push_str("    ");
                }
            }
            self.contents.push_str(part);
            self.at_line_start = part.ends_with('\n');
        }
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
