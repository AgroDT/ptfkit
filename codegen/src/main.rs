//! Specification validation and deterministic binding generation for ptfkit.

use std::{path::Path, process::ExitCode};

use anyhow::{Context, Result, bail};
use clap::{Parser, Subcommand};

mod formula;
mod model;
mod semantic;
mod specs;
mod targets;
mod validate;
mod version;

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
    Version { version: String },
}

impl Cli {
    fn run(self) -> Result<()> {
        let root = Path::new(env!("CARGO_MANIFEST_DIR"))
            .parent()
            .context("finding the ptfkit workspace root")?;

        match self.command {
            Command::Validate => {
                let entries = load_validated_specifications(root)?;
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
            Command::Generate => {
                let entries = load_validated_specifications(root)?;
                targets::run(root, entries)
            }
            Command::Version { version } => version::run(root, &version),
        }
    }
}

fn load_validated_specifications(root: &Path) -> Result<Vec<model::Entry>> {
    let entries = specs::load(root)?;
    let errors = validate::specifications(&entries);
    if !errors.is_empty() {
        bail!("validation failed:\n{}", errors.join("\n"))
    }
    Ok(entries)
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
