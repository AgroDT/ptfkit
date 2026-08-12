use std::{
    collections::BTreeSet,
    fs,
    path::{Path, PathBuf},
    process::Command,
};

use anyhow::{Context, Result, bail};

use super::{Target, TargetOutput};

struct StagedWrite {
    target: PathBuf,
    temporary: PathBuf,
    output_target: Target,
}

pub(super) fn commit(root: &Path, outputs: [TargetOutput; 3]) -> Result<()> {
    for output in &outputs {
        cleanup(root, output)?;
    }
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
    Ok(())
}

fn stage(root: &Path, outputs: [TargetOutput; 3]) -> Result<Vec<StagedWrite>> {
    let mut staged = Vec::new();
    for output in outputs {
        for file in output.files {
            let target = output.target.output_path(root, &file.path);
            let contents = file.contents.replace("\r\n", "\n");
            if target.exists() && fs::read_to_string(&target)? == contents {
                continue;
            }
            let parent = target.parent().context("finding generated-file parent")?;
            fs::create_dir_all(parent)?;
            let temporary = target.with_extension(format!(
                "{}.tmp",
                target
                    .extension()
                    .and_then(|extension| extension.to_str())
                    .unwrap_or("generated")
            ));
            fs::write(&temporary, contents)?;
            staged.push(StagedWrite {
                target,
                temporary,
                output_target: output.target,
            });
        }
    }
    Ok(staged)
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
