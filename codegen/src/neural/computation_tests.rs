use super::computation::*;
use crate::model::Entry;
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};

fn fixture() -> (PathBuf, Entry) {
    let root = crate::test_support::fixture_root("neural-computation");
    fs::write(
        root.join("specs/functions/example2026.yaml"),
        include_str!("../fixtures/neural.yaml"),
    )
    .unwrap();
    fs::write(
        root.join("specs/functions/controlled.ptfm"),
        include_bytes!("../fixtures/controlled.ptfm"),
    )
    .unwrap();
    let entries = crate::specs::load(&root).unwrap();
    let functions = crate::compile::functions(entries).unwrap();
    (root, functions[0].entry.clone())
}

fn execute(root: &Path, name: &str, source: &str, rust: bool) -> String {
    execute_with_include(root, name, source, rust, None)
}
fn execute_with_include(
    root: &Path,
    name: &str,
    source: &str,
    rust: bool,
    include: Option<&Path>,
) -> String {
    let path = root.join(format!("{name}.{}", if rust { "rs" } else { "c" }));
    fs::write(&path, source).unwrap();
    let exe = root.join(format!("{name}{}", std::env::consts::EXE_SUFFIX));
    let mut command = if rust {
        let mut c = Command::new("rustc");
        c.args(["--edition", "2024"]);
        c
    } else {
        let mut c = Command::new(std::env::var("CC").unwrap_or_else(|_| "clang".into()));
        c.arg("-std=c11").arg("-I");
        if let Some(include) = include {
            c.arg(include);
        } else {
            c.arg(Path::new(env!("CARGO_MANIFEST_DIR")).join("../targets/ptfkit-native/include"));
        }
        c
    };
    command.arg(&path).arg("-o").arg(&exe);
    if !rust && !cfg!(windows) {
        command.arg("-lm");
    }
    let output = command.output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let output = Command::new(exe).output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    String::from_utf8(output.stdout).unwrap()
}

#[test]
fn emits_neural_operations_resolved_by_the_shared_semantic_pipeline() {
    let (_, entry) = fixture();
    let ir = entry.implementations[0].as_ref().unwrap();
    let outputs = entry.spec.functions[0]
        .outputs
        .fields()
        .iter()
        .map(|f| f.name.clone())
        .collect::<Vec<_>>();
    snapbox::assert_data_eq!(
        render_function(ir, &outputs, 2, false).unwrap(),
        snapbox::file!("../fixtures/expected/neural_computation.c")
    );
    snapbox::assert_data_eq!(
        render_function(ir, &outputs, 2, true).unwrap(),
        snapbox::file!("../fixtures/expected/neural_computation.rs")
    );
}

#[test]
fn generated_c_and_rust_execute_independent_composition_and_uncertainty_example() {
    let (root, _) = fixture();
    fs::write(
        root.join("specs/functions/other2026.yaml"),
        include_str!("../fixtures/neural.yaml")
            .replace("calc_ptf_example2026", "calc_ptf_other2026")
            .replace("DenseModel", "OtherModel")
            .replace("DenseStatistics", "OtherStatistics"),
    )
    .unwrap();
    let loaded = crate::specs::load_all(&root).unwrap();
    let entries = loaded.entries.clone();
    fs::create_dir_all(root.join("targets/ptfkit-py")).unwrap();
    fs::write(
        root.join("targets/ptfkit-py/ruff.toml"),
        include_str!("../../../ruff.toml"),
    )
    .unwrap();
    crate::targets::run(&root, loaded).unwrap();
    super::parameters::prepare(&root, &entries).unwrap();
    let include = root.join("targets/ptfkit-native/include");
    let prepared = root.join("targets/ptfkit-native/prepared/example2026_data.c");
    let c = format!(
        "#include <ptfkit/ptfkit.h>\n#include {:?}\n{}",
        prepared.to_string_lossy(),
        r#"
int main(void){
    ptfkit_model *model=NULL;
    if(ptfkit_densemodel_builtin(&model)!=PTFKIT_MODEL_OK)return 1;
    ptfkit_densemodel_statistics result;
    if(calc_ptf_example2026(model,2,&result)!=PTFKIT_MODEL_OK || result.mean!=50.5 || result.shifted!=82.75)return 2;
    double x=2;
    for(unsigned mode=0;mode<3;++mode){if(calc_ptf_example2026_estimate(model,2,(ptfkit_estimate)mode,&result)!=PTFKIT_MODEL_OK)return 10;
        double out[]={result.mean,result.std,result.secondary_mean,result.secondary_std,result.shifted};
        for(size_t j=0;j<5;++j)printf("%.17g\n",out[j]);}
    x=-0.01;if(calc_ptf_example2026(model,x,&result)!=PTFKIT_MODEL_INPUT)return 11;
    x=4.01;if(calc_ptf_example2026(model,x,&result)!=PTFKIT_MODEL_INPUT)return 12;
    x=0;if(calc_ptf_example2026(model,x,&result)!=PTFKIT_MODEL_OK)return 13;
    x=4;if(calc_ptf_example2026(model,x,&result)!=PTFKIT_MODEL_OK || !isfinite(result.mean) || !isnan(result.secondary_mean))return 14;
    x=NAN;if(calc_ptf_example2026(model,x,&result)!=PTFKIT_MODEL_INPUT)return 15;
    ptfkit_model *other=NULL;if(ptfkit_densemodel_builtin(&other)!=PTFKIT_MODEL_OK)return 16;
    if(model->detail_data!=other->detail_data || model->detail_networks!=other->detail_networks)return 17;
    ptfkit_densemodel_free(model);ptfkit_densemodel_free(other);return 0;
}"#
    );
    let rust_src = root.join("targets/ptfkit-rs/src");
    let rust = format!(
        "#[path={:?}]mod models;#[path={:?}]mod example2026;\n{}",
        rust_src.join("models.rs").to_string_lossy(),
        rust_src.join("example2026.rs").to_string_lossy(),
        r#"
fn main(){
    use example2026::{DenseModel,Estimate};
    let model=DenseModel::builtin().unwrap();
    for mode in [Estimate::Arithmetic,Estimate::Log10,Estimate::Geometric]{
        let v=model.calc_ptf_example2026(2.,mode).unwrap();
        for value in [v.mean,v.std,v.secondary_mean,v.secondary_std,v.shifted]{println!("{value:.17e}");}
    }
    assert!(model.calc_ptf_example2026(-0.01,Estimate::Arithmetic).is_err());
    assert!(model.calc_ptf_example2026(4.01,Estimate::Arithmetic).is_err());
    assert!(model.calc_ptf_example2026(0.,Estimate::Arithmetic).is_ok());
    let guarded=model.calc_ptf_example2026(4.,Estimate::Arithmetic).unwrap();
    assert!(guarded.mean.is_finite());assert!(guarded.secondary_mean.is_nan());
    assert!(model.calc_ptf_example2026(f64::NAN,Estimate::Arithmetic).is_err());

}"#
    );
    let expected = [
        50.5,
        99.0 / 2.0_f64.sqrt(),
        75.75,
        50.5 / 2.0_f64.sqrt(),
        82.75,
        1.0,
        2.0_f64.sqrt(),
        15.0,
        10.0 / 2.0_f64.sqrt(),
        22.0,
        10.0,
        99.0 / 2.0_f64.sqrt(),
        15.0,
        10.0 / 2.0_f64.sqrt(),
        22.0,
    ];
    for (name, source, is_rust) in [("neural_c", c, false), ("neural_rs", rust, true)] {
        let actual = execute_with_include(&root, name, &source, is_rust, Some(&include))
            .split_whitespace()
            .map(|s| s.parse::<f64>().unwrap())
            .collect::<Vec<_>>();
        assert_eq!(actual.len(), expected.len());
        for (actual, expected) in actual.iter().zip(expected) {
            assert!(
                (actual - expected).abs() < 1e-12,
                "{name}: {actual} != {expected}"
            );
        }
    }
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn semantic_resolution_rejects_invalid_neural_references_dimensions_and_modes() {
    for change in 0..5 {
        let root = crate::test_support::fixture_root("invalid-neural");
        let source = include_str!("../fixtures/neural.yaml");
        let changed = match change {
            0 => source.replace("definition: primary", "definition: unknown"),
            1 => source.replace("source: raw", "source: physical"),
            2 => source.replace("value: 10 ^ value", "missing: 10 ^ value"),
            3 => source.replace("members: 2", "members: 1"),
            _ => source.replace("log10: logs.value_mean", "log10: raw.value"),
        };
        assert_ne!(
            changed, source,
            "mutation {change} did not reach the fixture"
        );
        fs::write(root.join("specs/functions/example2026.yaml"), changed).unwrap();
        let error = crate::specs::load(&root).expect_err("invalid neural implementation accepted");
        let report = error
            .downcast_ref::<crate::diagnostics::ValidationReport>()
            .unwrap();
        use crate::{
            diagnostics::Diagnostic,
            semantic::{SemanticErrorKind, neural::NeuralErrorKind},
        };
        if change == 3 {
            assert!(
                report
                    .diagnostics
                    .iter()
                    .any(|d| matches!(d, Diagnostic::Specification(_))),
                "{report:?}"
            );
            assert!(report.diagnostics.iter().any(|d|matches!(d,Diagnostic::Semantic(e) if matches!(&e.kind,SemanticErrorKind::Neural(NeuralErrorKind::Definition{name}) if name=="primary"))),"{report:?}");
            fs::remove_dir_all(root).unwrap();
            continue;
        }
        assert_eq!(report.diagnostics.len(), 1);
        match &report.diagnostics[0] {
            Diagnostic::Semantic(error) => {
                assert_eq!(error.function, "calc_ptf_example2026");
                assert!(
                    error
                        .implementation_path
                        .starts_with("implementation.variables[")
                );
                match (change, &error.kind) {
                    (0, SemanticErrorKind::Neural(NeuralErrorKind::UnknownNetwork { name })) => {
                        assert_eq!(name, "unknown")
                    }
                    (1, SemanticErrorKind::Neural(NeuralErrorKind::EnsembleRequired { name })) => {
                        assert_eq!(name, "physical")
                    }
                    (2, SemanticErrorKind::Neural(NeuralErrorKind::Field { name })) => {
                        assert_eq!(name, "missing")
                    }
                    (4, SemanticErrorKind::NotARecord { name }) => assert_eq!(name, "raw"),
                    _ => panic!("unexpected semantic rejection: {:?}", error.kind),
                }
            }
            Diagnostic::Specification(_) if change == 3 => {}
            other => panic!("unexpected rejection: {other:?}"),
        }
        fs::remove_dir_all(root).unwrap();
    }
}

#[test]
fn compiled_prepared_c_and_rust_arrays_preserve_binary64_bits() {
    use crate::neural::{
        Model,
        engine::{Network, Scale},
    };
    let bits = [
        0x0000000000000001_u64,
        0x8000000000000000,
        0x0000000000000000,
        0x3fb999999999999a,
        0x7fefffffffffffff,
        0x3ff0000000000001,
    ];
    let scale = || Scale {
        kind: "asis".into(),
        params: vec![],
    };
    let model = Model {
        networks: vec![Network {
            nboot: 2,
            widths: vec![2, 1],
            activations: vec!["linear".into()],
            inputs: vec![scale(), scale()],
            outputs: vec![scale()],
            offset: 0,
        }],
        data: bits.iter().copied().map(f64::from_bits).collect(),
    };
    let (c, rust) = super::parameters::render(&model, "example2026");
    let c = c
        + "\nint main(void){for(size_t i=0;i<6;++i){uint64_t bits;memcpy(&bits,&weights[i],8);printf(\"%016llx\\n\",(unsigned long long)bits);}return 0;}\n";
    let engine = Path::new(env!("CARGO_MANIFEST_DIR")).join("src/neural/engine.rs");
    let rust = format!(
        "mod models{{#[path={:?}]pub mod engine;pub struct Model;impl Model{{pub(crate) fn from_bundled(_:Vec<engine::Network>,_:&'static [f64])->Self{{Self}}}}}}\nmod prepared{{{rust}\npub(super) fn print_bits(){{for value in WEIGHTS{{println!(\"{{:016x}}\",value.to_bits());}}}}}}\nfn main(){{prepared::print_bits();}}",
        engine.to_string_lossy()
    );
    let root = crate::test_support::fixture_root("prepared-bits");
    for (name, source, is_rust) in [("bits_c", c, false), ("bits_rs", rust, true)] {
        let actual = execute(&root, name, &source, is_rust)
            .split_whitespace()
            .map(|s| u64::from_str_radix(s, 16).unwrap())
            .collect::<Vec<_>>();
        assert_eq!(actual, bits, "{name} changed binary64 parameter bits");
    }
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn preparation_rejects_corruption_and_inconsistent_parameter_artifacts() {
    let (root, entry) = fixture();
    let path = root.join("specs/functions/controlled.ptfm");
    let original = fs::read(&path).unwrap();
    let mut corrupt = original.clone();
    *corrupt.last_mut().unwrap() ^= 1;
    fs::write(&path, &corrupt).unwrap();
    let error = super::parameters::prepare(&root, std::slice::from_ref(&entry)).unwrap_err();
    assert!(matches!(
        error.downcast_ref::<super::ModelError>(),
        Some(super::ModelError::Integrity)
    ));
    fs::write(&path, &original).unwrap();
    let mut inconsistent = entry.clone();
    inconsistent.spec.functions[0]
        .implementation
        .as_mut()
        .unwrap()
        .networks
        .get_mut("secondary")
        .unwrap()
        .parameters
        .artifact
        .path = "other.ptfm".into();
    let error = super::parameters::prepare(&root, &[inconsistent]).unwrap_err();
    assert!(matches!(
        error.downcast_ref::<super::ModelError>(),
        Some(super::ModelError::Data)
    ));
    let mut truncated = original.clone();
    truncated.pop();
    let error = super::parameters::decode(&entry, &truncated).err().unwrap();
    assert!(matches!(
        error.downcast_ref::<super::ModelError>(),
        Some(super::ModelError::Data)
    ));
    let mut blocked = entry;
    blocked.spec.functions[0].status = "blocked".into();
    fs::remove_file(path).unwrap();
    super::parameters::prepare(&root, std::slice::from_ref(&blocked)).unwrap();
    assert!(super::public::render(&root, &[blocked]).unwrap().is_none());
    fs::remove_dir_all(root).unwrap();
}
