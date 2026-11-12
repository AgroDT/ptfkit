#[test]
fn bundled_rosetta_matches_frozen_upstream_case() {
    use ptfkit::zhang_schaap2017::Rosetta3;
    let model = Rosetta3::builtin().unwrap();
    let actual = model
        .calc_ptf_zhang2017_mod2(
            30.0,
            30.0,
            40.0,
            ptfkit::zhang_schaap2017::Estimate::Arithmetic,
        )
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
