//! Small, controlled inputs for codegen tests; independent of the publication corpus.

use std::{
    fs,
    path::{Path, PathBuf},
};

static NEXT_ROOT: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);

pub(crate) fn fixture_root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "ptfkit-codegen-specs-{label}-{}-{}",
        std::process::id(),
        NEXT_ROOT.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
    ));
    fs::create_dir_all(root.join("specs/functions")).unwrap();
    fs::create_dir_all(root.join("specs/schema")).unwrap();
    fs::copy(
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../specs/schema/ptf-spec.schema.json"),
        root.join("specs/schema/ptf-spec.schema.json"),
    )
    .unwrap();
    fs::write(
        root.join("specs/quantities.yaml"),
        include_str!("fixtures/quantities.yaml"),
    )
    .unwrap();
    fs::write(
        root.join("specs/units.yaml"),
        include_str!("fixtures/units.yaml"),
    )
    .unwrap();
    root
}

pub(crate) fn entries() -> Vec<crate::model::Entry> {
    let root = fixture_root("renderers");
    for slug in ["example10", "example2"] {
        fs::write(
            root.join(format!("specs/functions/{slug}.yaml")),
            include_str!("fixtures/source.yaml").replace("example", slug),
        )
        .unwrap();
    }
    let entries =
        crate::load_validated_specifications(&root).expect("test specifications validate");
    fs::remove_dir_all(root).unwrap();
    entries
}

pub(crate) fn functions() -> Vec<crate::model::CompiledFunction> {
    crate::compile::functions(entries()).expect("test specifications compile")
}
