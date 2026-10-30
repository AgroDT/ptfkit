//! Local Rosetta3 orchestration over the reusable dense ensemble engine.

use super::engine::{Network, statistics};

/// Fixed-level input validation. Missing predictors never select another level.
pub fn valid(level: usize, x: &[f64]) -> bool {
    (2..=5).contains(&level)
        && x.len() == level + 1
        && x.iter().all(|v| v.is_finite())
        && x[..3].iter().all(|v| *v >= 0.0)
        && (99.0..=101.0).contains(&(x[0] + x[1] + x[2]))
        && (level < 3 || (0.5..=2.0).contains(&x[3]))
        && (level < 4 || (x[4] > 0.0 && x[4] < 1.0))
        && (level < 5 || (x[5] > 0.0 && x[5] < x[4]))
}

/// Seven means followed by seven sample standard deviations.
/// Mode 0: arithmetic, 1: log10, 2: geometric (physical-scale stdev).
pub fn predict(
    networks: &[Network],
    data: &[f64],
    level: usize,
    mode: usize,
    x: &[f64],
) -> Option<[f64; 14]> {
    if !valid(level, x) || mode > 2 {
        return None;
    }
    let raw = networks[level - 2].predict(data, x);
    let mut linear = raw.clone();
    for row in &mut linear {
        for value in &mut row[2..] {
            *value = 10.0_f64.powf(*value);
        }
    }
    let (logmean, logstd) = statistics(&raw);
    let (linmean, linstd) = statistics(&linear);
    let mut geo = logmean.clone();
    for value in &mut geo[2..] {
        *value = 10.0_f64.powf(*value);
    }
    let (mean, std) = match mode {
        0 => (&linmean, &linstd),
        1 => (&logmean, &logstd),
        _ => (&geo, &linstd),
    };
    let vg = if mode == 0 { &linmean[..4] } else { &geo[..4] };
    let mut out = [f64::NAN; 14];
    out[..5].copy_from_slice(mean);
    out[7..12].copy_from_slice(std);
    if !(0.0 <= vg[0] && vg[0] < vg[1] && vg[1] < 1.0 && vg[2] > 0.0 && vg[3] > 1.0) {
        return Some(out);
    }
    let unsat = networks[4].predict(data, vg);
    let mut unsatlin = unsat.clone();
    for row in &mut unsatlin {
        row[0] = 10.0_f64.powf(row[0]);
    }
    let (um, us) = statistics(&unsat);
    let (ulm, uls) = statistics(&unsatlin);
    out[6] = um[1];
    out[13] = us[1];
    out[5] = match mode {
        0 => ulm[0],
        1 => um[0],
        _ => 10.0_f64.powf(um[0]),
    };
    out[12] = if mode == 1 { us[0] } else { uls[0] };
    Some(out)
}
