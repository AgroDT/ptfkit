// Hand-specified PTFKNN01 affine ensemble: x=[3,4] -> members [21,9].
const AFFINE: &[u8] = &[
    80, 84, 70, 75, 78, 78, 48, 49, 1, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0, 240, 191, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0, 240, 63, 0, 0, 0, 0, 0,
    0, 240, 63, 0, 0, 0, 0, 0, 0, 240, 191, 0, 0, 0, 0, 0, 0, 0, 64, 0, 0, 0, 0, 0, 0, 0, 0,
];
const SHA: &str = "7b160f19c85818a5995d9154563a44a8edd8e63f44d961542a4ca5d3b3a0e5ec";

use ptfkit::models::{Model, ModelError};
use sha2::{Digest, Sha256};
fn digest(bytes: &[u8]) -> String {
    Sha256::digest(bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect()
}
#[test]
fn authenticated_owned_affine_ensemble() {
    let mut bytes = AFFINE.to_vec();
    let model = Model::from_bytes(&bytes, SHA).unwrap();
    bytes.fill(0);
    assert_eq!(model.sha256(), SHA);
    assert_eq!(model.network_count(), 1);
    assert_eq!(model.network_shape(0).unwrap(), (2, 1, 2));
    assert_eq!(
        model.predict_network(0, &[3.0, 4.0]).unwrap(),
        [vec![21.0], vec![9.0]]
    );
    assert!(matches!(
        model.predict_network(1, &[3.0, 4.0]),
        Err(ModelError::Input)
    ));
    assert!(matches!(
        model.predict_network(0, &[3.0]),
        Err(ModelError::Input)
    ));
    assert!(matches!(
        model.predict_network(0, &[f64::NAN, 4.0]),
        Err(ModelError::Input)
    ));
    assert!(matches!(
        ptfkit::zhang_schaap2017::Rosetta3::from_model(model),
        Err(ModelError::Integrity)
    ));
}
#[test]
fn corruption_and_authenticated_malformed_containers_are_rejected() {
    let mut changed = AFFINE.to_vec();
    changed[179] ^= 1;
    assert!(matches!(
        Model::from_bytes(&changed, SHA),
        Err(ModelError::Integrity)
    ));
    for size in 0..AFFINE.len() {
        let data = &AFFINE[..size];
        assert!(
            matches!(
                Model::from_bytes(data, &digest(data)),
                Err(ModelError::Format)
            ),
            "prefix {size}"
        );
    }
    for offset in [0, 8, 12, 16, 20, 24, 28, 32, 116, 124] {
        let mut data = AFFINE.to_vec();
        data[offset] = 255;
        assert!(
            matches!(
                Model::from_bytes(&data, &digest(&data)),
                Err(ModelError::Format)
            ),
            "offset {offset}"
        );
    }
    let mut data = AFFINE.to_vec();
    data.push(0);
    assert!(matches!(
        Model::from_bytes(&data, &digest(&data)),
        Err(ModelError::Format)
    ));
    assert!(matches!(
        Model::from_bytes(AFFINE, "not a digest"),
        Err(ModelError::Format)
    ));
}

#[test]
fn bundled_rosetta_matches_frozen_upstream_case() {
    use ptfkit::zhang_schaap2017::{Estimate, Rosetta3};
    let model = Rosetta3::builtin().unwrap();
    let actual = model
        .predict(2, Estimate::Arithmetic, &[30.0, 30.0, 40.0])
        .unwrap();
    // Frozen upstream case mod2_arith_clay_loam; no external file is loaded.
    let expected = [
        0.11921313412479762,
        0.4348486578079577,
        0.009109686083606867,
        1.3094213646469939,
        8.74047181417013,
        1.3099307799553759,
        -1.009187960743742,
        0.009022699466985867,
        0.010140469075525323,
        0.0022509742698824248,
        0.0366504620061113,
        2.930411333703784,
        0.843530623042398,
        1.547848314232419,
    ];
    for (a, e) in actual
        .mean()
        .into_iter()
        .chain(actual.stddev())
        .zip(expected)
    {
        assert!((a - e).abs() <= 1e-11_f64.max(1e-12 * e.abs()));
    }
}
