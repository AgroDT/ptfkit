//! Specification validation and deterministic binding generation for ptfkit.

use std::{path::Path, process::ExitCode};

use anyhow::{Context, Result, bail};
use clap::{Parser, Subcommand};

mod core;
mod formula;
mod generate;
mod model;
mod semantic;
mod specs;
mod validate;

#[derive(Parser)]
#[command(about = "Validate ptfkit specifications and generate bindings")]
pub(crate) struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    Validate,
    Generate,
}

impl Cli {
    fn run(self) -> Result<()> {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("../../")
            .canonicalize()
            .context("finding the ptfkit workspace root")?;
        let entries = specs::load(&root)?;
        let errors = validate::specifications(&entries);
        if !errors.is_empty() {
            bail!("validation failed:\n{}", errors.join("\n"))
        }

        match self.command {
            Command::Validate => {
                println!(
                    "validated {} PTF specification files containing {} functions",
                    entries.len(),
                    entries
                        .iter()
                        .map(|entry| entry.spec.functions.len())
                        .sum::<usize>()
                );
                Ok(())
            }
            Command::Generate => generate::run(&root, entries),
        }
    }
}

fn main() -> ExitCode {
    match Cli::parse().run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprint!("{error:#}");
            ExitCode::FAILURE
        }
    }
}
