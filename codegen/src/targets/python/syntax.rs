use std::fmt::Display;

use crate::render::Writer;

/// Small Python-specific rendering helpers for the declarations emitted by the
/// public wrapper and its generated tests. This deliberately models only the
/// constructs the generator owns, not Python's complete syntax.
pub(super) struct Module {
    writer: Writer,
}

impl Module {
    pub(super) fn new(header: &str) -> Self {
        let mut writer = Writer::new();
        writer.write(header.trim_end());
        Self { writer }
    }

    pub(super) fn blank_line(&mut self) {
        self.writer.blank_line();
    }

    pub(super) fn line(&mut self, value: impl Display) {
        self.writer.line(value);
    }

    pub(super) fn write(&mut self, value: impl Display) {
        self.writer.write(value);
    }

    pub(super) fn import(&mut self, module: &str, names: impl Display) {
        self.line(format_args!("from {module} import {names}"));
    }

    pub(super) fn assignment(&mut self, name: &str, value: impl Display) {
        self.line(format_args!("{name} = {value}"));
    }

    pub(super) fn block(
        &mut self,
        opening: impl Display,
        render: impl FnOnce(&mut Writer),
        closing: impl Display,
    ) {
        self.writer.line(opening);
        self.writer.indented(render);
        self.writer.line(closing);
    }

    pub(super) fn indented(&mut self, render: impl FnOnce(&mut Writer)) {
        self.writer.indented(render);
    }

    pub(super) fn into_string(self) -> String {
        self.writer.into_string()
    }
}
