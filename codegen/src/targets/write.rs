use std::{
    collections::BTreeSet,
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    process::Command,
    sync::atomic::{AtomicU64, Ordering},
};

use anyhow::{Context, Result, bail};

use super::{Target, TargetOutput};

struct StagedWrite {
    target: PathBuf,
    temporary: PathBuf,
    output_target: Target,
}

static TEMPORARY_SEQUENCE: AtomicU64 = AtomicU64::new(0);

pub(super) fn commit(root: &Path, outputs: &[TargetOutput]) -> Result<()> {
    let staged = stage(root, outputs)?;
    if let Err(error) = format(root, &staged) {
        remove_temporary(&staged);
        return Err(error);
    }
    for (index, write) in staged.iter().enumerate() {
        if let Err(error) = fs::rename(&write.temporary, &write.target) {
            remove_temporary(&staged[index..]);
            return Err(error).with_context(|| format!("replacing {}", write.target.display()));
        }
    }
    for output in outputs {
        cleanup(root, output)?;
    }
    Ok(())
}

fn stage(root: &Path, outputs: &[TargetOutput]) -> Result<Vec<StagedWrite>> {
    let mut staged = Vec::new();
    for output in outputs {
        for file in &output.files {
            let target = output.target.output_path(root, &file.path);
            if target.exists()
                && fs::read_to_string(&target)? == file.contents
                && !output.target.is_clang_formatted()
            {
                continue;
            }
            let parent = target.parent().context("finding generated-file parent")?;
            fs::create_dir_all(parent)?;
            let temporary = temporary_path(&target);
            if let Err(error) = write_temporary(&temporary, &file.contents) {
                let _ = fs::remove_file(&temporary);
                remove_temporary(&staged);
                return Err(error);
            }
            staged.push(StagedWrite {
                target,
                temporary,
                output_target: output.target,
            });
        }
    }
    Ok(staged)
}

fn temporary_path(target: &Path) -> PathBuf {
    let extension = target
        .extension()
        .and_then(|extension| extension.to_str())
        .unwrap_or("generated");
    let sequence = TEMPORARY_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    target.with_extension(format!(
        "{extension}.{}.{}.tmp",
        std::process::id(),
        sequence
    ))
}

fn write_temporary(path: &Path, contents: &str) -> Result<()> {
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .with_context(|| format!("creating temporary generated file {}", path.display()))?;
    file.write_all(contents.as_bytes())
        .with_context(|| format!("writing temporary generated file {}", path.display()))
}

fn cleanup(root: &Path, output: &TargetOutput) -> Result<()> {
    let expected = output
        .files
        .iter()
        .map(|file| output.target.output_path(root, &file.path))
        .collect::<BTreeSet<_>>();
    remove_obsolete(
        &output.target.cleanup_directory(root),
        &expected,
        output.target.generated_header(),
    )
}

fn remove_obsolete(directory: &Path, expected: &BTreeSet<PathBuf>, header: &str) -> Result<()> {
    if !directory.is_dir() {
        return Ok(());
    }
    for entry in fs::read_dir(directory)? {
        let path = entry?.path();
        if path.is_dir() {
            remove_obsolete(&path, expected, header)?;
        } else if !expected.contains(&path) && fs::read(&path)?.starts_with(header.as_bytes()) {
            fs::remove_file(path)?;
        }
    }
    Ok(())
}

fn format(root: &Path, staged: &[StagedWrite]) -> Result<()> {
    for target in Target::ALL {
        let paths = staged
            .iter()
            .filter(|file| file.output_target == target)
            .map(|file| file.temporary.clone())
            .collect::<Vec<_>>();
        if !paths.is_empty() {
            target.format(root, &paths)?;
        }
    }
    Ok(())
}

pub(super) fn format_rust(paths: &[PathBuf]) -> Result<()> {
    run("rustfmt", &["--edition", "2024"], paths, None)
}

pub(super) fn format_python(root: &Path, paths: &[PathBuf]) -> Result<()> {
    run(
        "uv",
        &["run", "--no-sync", "ruff", "format"],
        paths,
        Some(&root.join("targets/ptfkit-py")),
    )
}

pub(super) fn format_c(paths: &[PathBuf]) -> Result<()> {
    run(
        "clang-format",
        &["--style=file", "--assume-filename=generated.c", "-i"],
        paths,
        None,
    )
}

pub(super) fn format_cpp(paths: &[PathBuf]) -> Result<()> {
    run(
        "clang-format",
        &["--style=file", "--assume-filename=generated.cpp", "-i"],
        paths,
        None,
    )
}

fn run(
    program: &str,
    arguments: &[&str],
    paths: &[PathBuf],
    current_dir: Option<&Path>,
) -> Result<()> {
    let mut command = Command::new(program);
    command.args(arguments).args(paths);
    if let Some(current_dir) = current_dir {
        command.current_dir(current_dir);
    }
    let output = command
        .output()
        .with_context(|| format!("running {program}"))?;
    if output.status.success() {
        Ok(())
    } else {
        bail!(
            "{program} failed:\n{}",
            String::from_utf8_lossy(&output.stderr).trim()
        )
    }
}

fn remove_temporary(staged: &[StagedWrite]) {
    for write in staged {
        let _ = fs::remove_file(&write.temporary);
    }
}
