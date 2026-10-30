use super::{
    engine::{Network, Scale, statistics},
    rosetta,
};

fn scale(kind: &str, params: &[f64]) -> Scale {
    Scale {
        kind: kind.to_owned(),
        params: params.to_vec(),
    }
}

#[test]
fn dense_members_preserve_weight_orientation_bias_and_output_scaling() {
    // Hand calculation: scaled inputs [2,3]; hidden [3,2] / [3,3];
    // logits 3 / 0; output 2*sigmoid(logit)-1. Asymmetric matrices
    // distinguish transposed weights and biases added inside dot products.
    let network = Network {
        nboot: 2,
        widths: vec![2, 2, 1],
        activations: vec!["linear".into(), "sigmoid".into()],
        inputs: vec![scale("division", &[2.0]), scale("affine", &[1.0, 2.0])],
        outputs: vec![scale("linear", &[2.0, -1.0])],
        offset: 1,
    };
    let data = [
        999.0, 1.0, 2.0, 0.0, 1.0, -5.0, -1.0, 2.0, -1.0, -1.0, 0.0, 1.0, 2.0, 0.0, 0.0, -1.0, 1.0,
        1.0, -6.0,
    ];
    let actual = network.predict(&data, &[4.0, 1.0]);
    assert!((actual[0][0] - 0.9051482536448667).abs() < 1e-15);
    assert_eq!(actual[1][0], 0.0);
}

#[test]
fn uncertainty_is_sample_standard_deviation_in_each_reported_scale() {
    // Two values 1 and 3 have mean 2 and sample SD sqrt(2),
    // distinguishing ddof=0 and standard error from the required contract.
    let (mean, std) = statistics(&[vec![1.0, 10.0], vec![3.0, 14.0]]);
    assert_eq!(mean, [2.0, 12.0]);
    assert!((std[0] - 2.0_f64.sqrt()).abs() < 1e-15);
    assert!((std[1] - 8.0_f64.sqrt()).abs() < 1e-15);
}

#[test]
fn fixed_level_validation_never_downgrades_or_invents_predictors() {
    assert!(rosetta::valid(2, &[39.0, 40.0, 20.0]));
    assert!(rosetta::valid(2, &[41.0, 40.0, 20.0]));
    assert!(!rosetta::valid(2, &[38.99, 40.0, 20.0]));
    assert!(!rosetta::valid(2, &[41.01, 40.0, 20.0]));
    assert!(rosetta::valid(3, &[40.0, 40.0, 20.0, 0.5]));
    assert!(rosetta::valid(3, &[40.0, 40.0, 20.0, 2.0]));
    assert!(!rosetta::valid(3, &[40.0, 40.0, 20.0, 2.01]));
    assert!(!rosetta::valid(5, &[40.0, 40.0, 20.0, 1.4, 0.3, 0.3]));
    assert!(!rosetta::valid(4, &[40.0, 40.0, 20.0, 1.4]));
    for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
        assert!(!rosetta::valid(2, &[value, 40.0, 20.0]));
    }
    assert!(!rosetta::valid(0, &[]));
}

#[test]
fn importer_rejects_corrupted_bytes_and_incompatible_metadata() {
    use super::{Model, ModelError};
    use sha2::{Digest, Sha256};
    use std::fs;
    let root = crate::test_support::fixture_root("neural-integrity");
    let path = root.join("models.json");
    let bytes: Vec<u8> = [2.0_f64, 1.0, 4.0, -1.0]
        .into_iter()
        .flat_map(f64::to_le_bytes)
        .collect();
    let hash: String = Sha256::digest(&bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    let manifest = serde_json::json!({
        "format_version": 1, "upstream_revision": "synthetic", "artifact": "models.bin", "sha256": hash,
        "networks": [{"name": "synthetic", "nboot": 2, "widths": [1,1], "offset": 0,
            "activations": ["linear"], "inputs": [{"kind":"asis", "params":[]}],
            "outputs": [{"kind":"asis", "params":[]}]}]
    });
    fs::write(&path, serde_json::to_vec(&manifest).unwrap()).unwrap();
    fs::write(root.join("models.bin"), &bytes).unwrap();
    let model = Model::load(&path).unwrap();
    // Independent affine arithmetic: 2*3+1=7 and 4*3-1=11.
    assert_eq!(
        model.networks[0].predict(&model.data, &[3.0]),
        [vec![7.0], vec![11.0]]
    );
    let mut corrupted = bytes.clone();
    corrupted[0] ^= 1;
    fs::write(root.join("models.bin"), &corrupted).unwrap();
    assert!(matches!(
        Model::load(&path)
            .err()
            .unwrap()
            .downcast_ref::<ModelError>(),
        Some(ModelError::Integrity)
    ));
    fs::write(root.join("models.bin"), &bytes).unwrap();
    let mut invalid = manifest.clone();
    invalid["networks"][0]["widths"] = serde_json::json!([2, 1]);
    fs::write(&path, serde_json::to_vec(&invalid).unwrap()).unwrap();
    assert!(matches!(
        Model::load(&path)
            .err()
            .unwrap()
            .downcast_ref::<ModelError>(),
        Some(ModelError::Topology { network: 0 })
    ));
    let mut invalid = manifest;
    invalid["networks"][0]["inputs"][0] = serde_json::json!({"kind":"division","params":[0.0]});
    fs::write(&path, serde_json::to_vec(&invalid).unwrap()).unwrap();
    assert!(matches!(
        Model::load(&path)
            .err()
            .unwrap()
            .downcast_ref::<ModelError>(),
        Some(ModelError::Transform { network: 0 })
    ));
    fs::remove_dir_all(root).unwrap();
}
