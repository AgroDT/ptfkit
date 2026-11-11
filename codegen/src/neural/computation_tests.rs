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
    let entries = crate::specs::load(&root).unwrap();
    let functions = crate::compile::functions(entries).unwrap();
    (root, functions[0].entry.clone())
}

fn execute(root: &Path, name: &str, source: &str, rust: bool) -> String {
    let path = root.join(format!("{name}.{}", if rust { "rs" } else { "c" }));
    fs::write(&path, source).unwrap();
    let exe = root.join(format!("{name}{}", std::env::consts::EXE_SUFFIX));
    let mut command = if rust {
        let mut c = Command::new("rustc");
        c.args(["--edition", "2024"]);
        c
    } else {
        let mut c = Command::new(std::env::var("CC").unwrap_or_else(|_| "clang".into()));
        c.arg("-std=c11")
            .arg("-I")
            .arg(Path::new(env!("CARGO_MANIFEST_DIR")).join("../targets/ptfkit-native/include"));
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
    let (root, entry) = fixture();
    let ir = entry.implementations[0].as_ref().unwrap();
    let outputs = entry.spec.functions[0]
        .outputs
        .fields()
        .iter()
        .map(|f| f.name.clone())
        .collect::<Vec<_>>();
    // After division by two and output shift by -2, primary members at x=2 are [0,2].
    // Mean(10^[0,2])=50.5, 10^mean([0,2])=10; secondary members are [v,2v].
    let c = format!(
        "#include <ptfkit/models.h>\n{}\n{}",
        render_function(ir, &outputs, 2, false).unwrap(),
        r#"
int main(void){
    ptfkit_detail_network nets[2]={0};
    for(size_t i=0;i<2;++i){nets[i].nboot=2;nets[i].nlayer=1;nets[i].widths[0]=1;nets[i].widths[1]=1;nets[i].offset=i*4;}
    nets[0].inputs[0].kind=1;nets[0].inputs[0].p[0]=2;
    nets[0].outputs[0].kind=5;nets[0].outputs[0].p[0]=1;nets[0].outputs[0].p[1]=-2;
    double data[]={2,0,4,0,1,0,2,0},x=2,out[5];
    for(unsigned mode=0;mode<3;++mode){if(!ptfkit_detail_rosetta_mod2(nets,data,mode,&x,1,out))return 10;
        for(size_t j=0;j<5;++j)printf("%.17g\n",out[j]);}
    x=-0.01;if(ptfkit_detail_rosetta_mod2(nets,data,0,&x,1,out))return 11;
    x=4.01;if(ptfkit_detail_rosetta_mod2(nets,data,0,&x,1,out))return 12;
    x=0;if(!ptfkit_detail_rosetta_mod2(nets,data,0,&x,1,out))return 13;
    x=4;if(!ptfkit_detail_rosetta_mod2(nets,data,0,&x,1,out) || !isfinite(out[0]) || !isnan(out[2]))return 14;
    x=NAN;if(ptfkit_detail_rosetta_mod2(nets,data,0,&x,1,out))return 15;
    return 0;
}"#
    );
    let engine = Path::new(env!("CARGO_MANIFEST_DIR")).join("src/neural/engine.rs");
    let rust = format!(
        "#[path={:?}]mod engine;use engine::{{Network,Scale,statistics}};\n{}\n{}",
        engine.to_string_lossy(),
        render_function(ir, &outputs, 2, true).unwrap(),
        r#"
fn main(){
    let asis=||Scale{kind:"asis".into(),params:vec![]};
    let net=|offset|Network{nboot:2,widths:vec![1,1],activations:vec!["linear".into()],inputs:vec![asis()],outputs:vec![asis()],offset};
    let mut nets=[net(0),net(4)];
    nets[0].inputs[0]=Scale{kind:"division".into(),params:vec![2.0]};
    nets[0].outputs[0]=Scale{kind:"linear".into(),params:vec![1.0,-2.0]};
    let data=[2.,0.,4.,0.,1.,0.,2.,0.];
    for mode in 0..3{for value in mod2(&nets,&data,mode,&[2.]).unwrap(){println!("{value:.17e}");}}
    assert!(mod2(&nets,&data,0,&[-0.01]).is_none());assert!(mod2(&nets,&data,0,&[4.01]).is_none());
    assert!(mod2(&nets,&data,0,&[0.]).is_some());let guarded=mod2(&nets,&data,0,&[4.]).unwrap();
    assert!(guarded[0].is_finite());assert!(guarded[2].is_nan());assert!(mod2(&nets,&data,0,&[f64::NAN]).is_none());
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
        let actual = execute(&root, name, &source, is_rust)
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
        revision: String::new(),
        contract: serde_json::Value::Null,
    };
    let (c, rust) = super::parameters::render(&model, &"0".repeat(64));
    let c = c
        + "\nint main(void){for(size_t i=0;i<6;++i){uint64_t bits;memcpy(&bits,&weights[i],8);printf(\"%016llx\\n\",(unsigned long long)bits);}return 0;}\n";
    let engine = Path::new(env!("CARGO_MANIFEST_DIR")).join("src/neural/engine.rs");
    let rust = format!(
        "mod models{{#[path={:?}]pub mod engine;pub struct Model;impl Model{{pub(crate) fn from_bundled(_:Vec<engine::Network>,_:&[f64],_:[u8;32])->Self{{Self}}}}}}\nmod prepared{{{rust}\npub(super) fn print_bits(){{for value in WEIGHTS{{println!(\"{{:016x}}\",value.to_bits());}}}}}}\nfn main(){{prepared::print_bits();}}",
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
