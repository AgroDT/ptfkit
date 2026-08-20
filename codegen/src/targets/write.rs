use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    process::Command,
    sync::atomic::{AtomicU64, Ordering},
};

use anyhow::{Context, Result, bail};

use super::{Formatter, LAYOUTS, Layout, Output};

struct StagedWrite {
    target: PathBuf,
    temporary: PathBuf,
    layout: &'static Layout,
}

static TEMPORARY_SEQUENCE: AtomicU64 = AtomicU64::new(0);

pub(super) struct GeneratedTree(BTreeMap<PathBuf, Vec<u8>>);

pub(super) fn snapshot_generated(root: &Path) -> Result<GeneratedTree> {
    let mut files = BTreeMap::new();
    for layout in LAYOUTS {
        collect_generated(
            root,
            &root.join(layout.cleanup_directory),
            layout.generated_header,
            &mut files,
        )?;
    }
    Ok(GeneratedTree(files))
}

pub(super) fn assert_unchanged(root: &Path, before: GeneratedTree) -> Result<()> {
    let after = snapshot_generated(root)?;
    if let Some(report) = drift_report(&before.0, &after.0) {
        bail!("generated output drift after regeneration:\n{report}")
    }
    println!("generated output is unchanged");
    Ok(())
}

fn collect_generated(
    root: &Path,
    directory: &Path,
    header: &str,
    files: &mut BTreeMap<PathBuf, Vec<u8>>,
) -> Result<()> {
    if !directory.is_dir() {
        return Ok(());
    }
    for entry in fs::read_dir(directory)? {
        let path = entry?.path();
        if path.is_dir() {
            collect_generated(root, &path, header, files)?;
        } else {
            let contents = fs::read(&path)?;
            if is_generated(&contents, header) {
                let relative = path
                    .strip_prefix(root)
                    .context("finding generated-file path relative to the workspace root")?
                    .to_owned();
                files.insert(relative, contents);
            }
        }
    }
    Ok(())
}

fn drift_report(
    before: &BTreeMap<PathBuf, Vec<u8>>,
    after: &BTreeMap<PathBuf, Vec<u8>>,
) -> Option<String> {
    let added = after
        .keys()
        .filter(|path| !before.contains_key(*path))
        .collect::<Vec<_>>();
    let removed = before
        .keys()
        .filter(|path| !after.contains_key(*path))
        .collect::<Vec<_>>();
    let modified = before
        .iter()
        .filter(|(path, contents)| after.get(*path).is_some_and(|after| after != *contents))
        .map(|(path, _)| path)
        .collect::<Vec<_>>();

    if added.is_empty() && removed.is_empty() && modified.is_empty() {
        return None;
    }

    let mut report = String::new();
    append_paths(&mut report, "added", &added);
    append_paths(&mut report, "removed", &removed);
    append_paths(&mut report, "modified", &modified);
    Some(report.trim_end().to_owned())
}

fn append_paths(report: &mut String, label: &str, paths: &[&PathBuf]) {
    if paths.is_empty() {
        return;
    }
    report.push_str(label);
    report.push_str(":\n");
    for path in paths {
        report.push_str("  ");
        report.push_str(&path.display().to_string());
        report.push('\n');
    }
}

pub(super) fn commit(root: &Path, outputs: &[Output]) -> Result<()> {
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

fn stage(root: &Path, outputs: &[Output]) -> Result<Vec<StagedWrite>> {
    let mut staged = Vec::new();
    for output in outputs {
        for file in &output.files {
            let target = root.join(output.layout.output_directory).join(&file.path);
            if target.exists()
                && fs::read_to_string(&target)? == file.contents
                && output.layout.formatter == Formatter::None
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
                layout: output.layout,
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

fn cleanup(root: &Path, output: &Output) -> Result<()> {
    let expected = output
        .files
        .iter()
        .map(|file| root.join(output.layout.output_directory).join(&file.path))
        .collect::<BTreeSet<_>>();
    remove_obsolete(
        &root.join(output.layout.cleanup_directory),
        &expected,
        output.layout.generated_header,
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
        } else if !expected.contains(&path) && is_generated(&fs::read(&path)?, header) {
            fs::remove_file(path)?;
        }
    }
    Ok(())
}

fn is_generated(contents: &[u8], header: &str) -> bool {
    contents.starts_with(header.as_bytes())
        || (header == super::documentation::HEADER
            && (contents.strip_prefix(b"---\n").is_some_and(|contents| {
                contents.starts_with(super::documentation::FRONTMATTER_HEADER.as_bytes())
            }) || (contents.starts_with(b"---\n")
                && contents
                    .windows(header.len())
                    .any(|window| window == header.as_bytes()))))
}

fn format(root: &Path, staged: &[StagedWrite]) -> Result<()> {
    for layout in LAYOUTS {
        let paths = staged
            .iter()
            .filter(|file| std::ptr::eq(file.layout, layout))
            .map(|file| file.temporary.clone())
            .collect::<Vec<_>>();
        if !paths.is_empty() {
            format_layout(layout.formatter, root, &paths)?;
        }
    }
    Ok(())
}

fn format_layout(formatter: Formatter, root: &Path, paths: &[PathBuf]) -> Result<()> {
    match formatter {
        Formatter::None => Ok(()),
        Formatter::Rust => format_rust(paths),
        Formatter::Python => format_python(root, paths),
        Formatter::C => format_c(paths),
        Formatter::Cpp => format_cpp(paths),
    }
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

#[cfg(test)]
mod tests {
    use std::{collections::BTreeMap, fs, path::Path};

    use super::*;
    use crate::targets::{GeneratedFile, Output, PYTHON_DOCUMENTATION, documentation::HEADER};

    fn temporary_root(label: &str) -> PathBuf {
        std::env::temp_dir().join(format!(
            "ptfkit-codegen-write-{label}-{}",
            std::process::id()
        ))
    }

    #[test]
    fn removes_obsolete_generated_python_reference_pages_only() {
        let root = temporary_root("python-documentation");
        let python_reference = root.join("docs/src/reference/python");
        let c_reference = root.join("docs/src/reference/c");
        fs::create_dir_all(&python_reference).expect("create Python reference directory");
        fs::create_dir_all(&c_reference).expect("create C reference directory");
        fs::write(
            python_reference.join("obsolete.md"),
            format!("{HEADER}# Obsolete\n"),
        )
        .expect("write obsolete Python page");
        fs::write(
            c_reference.join("preserved.md"),
            format!("{HEADER}# Preserved\n"),
        )
        .expect("write C page");

        let output = Output::new(
            &PYTHON_DOCUMENTATION,
            vec![GeneratedFile::new(
                "index.md".into(),
                format!("{HEADER}# Python\n"),
            )],
        );
        commit(&root, &[output]).expect("commit Python documentation");

        assert!(python_reference.join("index.md").is_file());
        assert!(!python_reference.join("obsolete.md").exists());
        assert!(c_reference.join("preserved.md").is_file());

        fs::remove_dir_all(root).expect("remove temporary test directory");
    }

    #[test]
    fn generated_documentation_front_matter_is_recognized_for_cleanup() {
        assert!(is_generated(
            format!("---\ntitle: \"ptfkit.test\"\n---\n\n{HEADER}::: ptfkit.test\n").as_bytes(),
            HEADER,
        ));
        assert!(is_generated(
            format!(
                "---\n{}title: ptfkit.test\n---\n",
                super::super::documentation::FRONTMATTER_HEADER
            )
            .as_bytes(),
            HEADER,
        ));
        assert!(!is_generated(b"# Handwritten page\n", HEADER));
        assert!(Path::new("index.md").is_relative());
    }

    #[test]
    fn generated_output_drift_reports_added_removed_and_modified_files() {
        let before = BTreeMap::from([
            (PathBuf::from("generated/modified"), b"before".to_vec()),
            (PathBuf::from("generated/removed"), b"removed".to_vec()),
        ]);
        let after = BTreeMap::from([
            (PathBuf::from("generated/added"), b"added".to_vec()),
            (PathBuf::from("generated/modified"), b"after".to_vec()),
        ]);

        assert_eq!(
            drift_report(&before, &after),
            Some(
                "added:\n  generated/added\nremoved:\n  generated/removed\nmodified:\n  generated/modified"
                    .to_owned()
            )
        );
    }
}
