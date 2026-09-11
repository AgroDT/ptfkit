fn resolved_tolerance(expected: f64, absolute: f64, relative: f64) -> f64 {
    absolute.max(relative * expected.abs()).max(1e-14)
}

pub(crate) fn assert_close(
    actual: f64,
    expected: f64,
    absolute: f64,
    relative: f64,
    quantity: &str,
    unit: &str,
    source: &str,
) {
    let difference = (actual - expected).abs();
    let tolerance = resolved_tolerance(expected, absolute, relative);
    assert!(
        difference <= tolerance,
        "actual={actual}, expected={expected}, difference={difference}, tolerance={tolerance}, quantity={quantity}, unit={unit}, source={source}"
    );
}

mod comparator_tests {
    use super::*;

    #[test]
    fn checks_independent_tolerances_and_boundaries() {
        let cases = [
            ("absolute", 4.0, 0.5, 0.0625, 0.5, 4.25, 4.5, 5.0),
            ("relative", 4.0, 0.125, 0.25, 1.0, 4.5, 5.0, 6.0),
            ("negative", -4.0, 0.125, 0.25, 1.0, -4.5, -5.0, -6.0),
            ("zero", 0.0, 0.125, 0.25, 0.125, 0.0625, 0.125, 0.25),
            ("guard", 0.0, 0.0, 0.0, 1e-14, 5e-15, 1e-14, 2e-14),
        ];
        for (name, expected, absolute, relative, tolerance, below, boundary, above) in cases {
            assert_eq!(
                resolved_tolerance(expected, absolute, relative),
                tolerance,
                "{name}"
            );
            for actual in [below, boundary] {
                assert_close(actual, expected, absolute, relative, name, "1", "registry");
            }
            assert!(
                std::panic::catch_unwind(|| {
                    assert_close(above, expected, absolute, relative, name, "1", "registry");
                })
                .is_err(),
                "{name}: above-threshold value must panic"
            );
        }
    }
}
